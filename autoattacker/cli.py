from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from autoattacker.adapters.base import Adapter
from autoattacker.adapters.toy_control.adapter import ToyControlAdapter, ToyControlShiftedAdapter
from autoattacker.kernel.archive import (
    append_campaign_result_row,
    append_research_ledger,
    build_batch_artifact,
    build_campaign_summary,
    build_run_artifact,
    persist_batch_artifact,
    persist_run_artifact,
    write_campaign_comparison_artifact,
    write_campaign_summary,
)
from autoattacker.kernel.baseline import default_budget, load_baseline_attacker, load_baseline_defender
from autoattacker.kernel.candidates import AttackerCandidate, DefenderCandidate, EvaluatedCandidate, PromotionDecision
from autoattacker.kernel.match import evaluate_match
from autoattacker.kernel.mutate import generate_attacker_candidates, generate_defender_candidates
from autoattacker.kernel.derived import write_machine_derived_summaries
from autoattacker.kernel.portfolio import (
    FrontierState,
    build_frontier_state,
    frontier_candidates,
    frontier_incumbent,
    frontier_state_candidates,
    load_frontier_state,
    persist_frontier_state,
    seed_frontier,
    update_frontier,
    update_frontier_state,
)
from autoattacker.kernel.regime import DEFAULT_REGIME_ID, CampaignRegime, load_regime
from autoattacker.kernel.score import ScoreBreakdown, aggregate_score_breakdowns, score_match
from autoattacker.kernel.select import decide_promotion, role_score, settle_iteration_promotions
from autoattacker.utils.reproducibility import capture_reproducibility
from autoattacker.utils.seeds import derive_seed, short_hash


def get_adapter(name: str) -> Adapter:
    if name == "toy_control":
        return ToyControlAdapter()
    if name == "toy_control_shifted":
        return ToyControlShiftedAdapter()
    raise ValueError(f"unknown adapter {name}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _baseline_decision(candidate_id: str, comparator_id: str, fitness: float) -> PromotionDecision:
    return PromotionDecision(
        role="system",
        candidate_id=candidate_id,
        comparator_id=comparator_id,
        candidate_score=fitness,
        comparator_score=fitness,
        novelty_score=0.0,
        status="promoted",
        reason="baseline comparator seeded for the frontier",
    )


def _comparison_decision_label(status: str) -> str:
    mapping = {
        "promoted": "promote",
        "archived": "archive_interesting",
        "discarded": "discard",
    }
    return mapping[status]


def _campaign_id(regime_id: str) -> str:
    return f"campaign-{short_hash(regime_id, time.time_ns())}"


def _iteration_batch_id(campaign_id: str, iteration: int, seed: int) -> str:
    return f"{campaign_id}-i{iteration:03d}-s{seed:03d}"


def _frontier_pool(
    frontier_state: FrontierState | None,
    role: str,
    incumbent: AttackerCandidate | DefenderCandidate,
) -> list[AttackerCandidate | DefenderCandidate]:
    if frontier_state is None:
        return [incumbent]
    candidates = frontier_state_candidates(frontier_state, role)
    return candidates or [incumbent]


def _lineage_text(candidate: AttackerCandidate | DefenderCandidate) -> str:
    return json.dumps(candidate.lineage.to_dict(), sort_keys=True, separators=(",", ":"))


def run_single(args: argparse.Namespace) -> int:
    adapter = get_adapter(args.adapter)
    output_root = Path(args.output_root)
    docs_root = Path(args.docs_root)
    attacker = load_baseline_attacker()
    defender = load_baseline_defender()
    budget = default_budget(seed=args.seed, num_tasks=args.tasks, max_turns=args.turns)
    batch_id = f"single-{short_hash(args.adapter, args.seed, args.tasks, args.turns)}"
    reproducibility = capture_reproducibility(cwd=Path.cwd(), argv=list(args.raw_argv), seed=args.seed)

    outcome = evaluate_match(
        adapter=adapter,
        attacker=attacker,
        defender=defender,
        budget=budget,
        batch_id=batch_id,
        label="baseline",
    )
    breakdown = score_match(outcome)
    decision = _baseline_decision(attacker.candidate_id, attacker.candidate_id, breakdown.attacker_fitness)
    evaluated = EvaluatedCandidate(
        role="system",
        candidate_id=attacker.candidate_id,
        opponent_id=defender.candidate_id,
        outcome=outcome,
        score=breakdown.to_dict(),
        decision=decision,
    )
    artifact = build_run_artifact(
        batch_id=batch_id,
        candidate=attacker,
        opponent=defender,
        evaluated=evaluated,
        reproducibility=reproducibility,
    )
    path = persist_run_artifact(output_root, artifact)
    evaluated.artifact_path = str(path)

    batch_artifact = build_batch_artifact(
        batch_id=batch_id,
        adapter_name=adapter.name,
        budget=budget,
        frontier=seed_frontier(attacker, defender, breakdown),
        evaluations=[evaluated],
        reproducibility=reproducibility,
    )
    persist_batch_artifact(output_root, batch_artifact)
    if args.update_ledger:
        append_research_ledger(docs_root, batch_artifact)

    print(f"run_id={outcome.run_id}")
    print(f"attack_success={outcome.attack_success:.3f}")
    print(f"stealth_score={outcome.stealth_score:.3f}")
    print(f"defender_success={outcome.defender_success:.3f}")
    print(f"artifact={path}")
    return 0


def run_batch(args: argparse.Namespace) -> int:
    adapter = get_adapter(args.adapter)
    output_root = Path(args.output_root)
    docs_root = Path(args.docs_root)
    attacker_baseline = load_baseline_attacker()
    defender_baseline = load_baseline_defender()
    budget = default_budget(seed=args.seed, num_tasks=args.tasks, max_turns=args.turns)
    batch_id = f"batch-{short_hash(args.adapter, args.seed, args.attacker_candidates, args.defender_candidates, args.tasks, args.turns)}"
    reproducibility = capture_reproducibility(cwd=Path.cwd(), argv=list(args.raw_argv), seed=args.seed)

    lookup = {
        attacker_baseline.candidate_id: attacker_baseline,
        defender_baseline.candidate_id: defender_baseline,
    }
    evaluations: list[EvaluatedCandidate] = []

    baseline_outcome = evaluate_match(
        adapter=adapter,
        attacker=attacker_baseline,
        defender=defender_baseline,
        budget=budget,
        batch_id=batch_id,
        label="baseline",
    )
    baseline_breakdown = score_match(baseline_outcome)
    frontier = seed_frontier(attacker_baseline, defender_baseline, baseline_breakdown)
    baseline_decision = _baseline_decision(attacker_baseline.candidate_id, attacker_baseline.candidate_id, baseline_breakdown.attacker_fitness)
    baseline_eval = EvaluatedCandidate(
        role="system",
        candidate_id=attacker_baseline.candidate_id,
        opponent_id=defender_baseline.candidate_id,
        outcome=baseline_outcome,
        score=baseline_breakdown.to_dict(),
        decision=baseline_decision,
    )
    baseline_artifact = build_run_artifact(
        batch_id=batch_id,
        candidate=attacker_baseline,
        opponent=defender_baseline,
        evaluated=baseline_eval,
        reproducibility=reproducibility,
    )
    baseline_path = persist_run_artifact(output_root, baseline_artifact)
    baseline_eval.artifact_path = str(baseline_path)
    evaluations.append(baseline_eval)

    attacker_candidates = generate_attacker_candidates(
        attacker_baseline,
        args.attacker_candidates,
        args.seed,
        batch_id,
        defender=defender_baseline,
        ledger_path=output_root / "campaign_results.tsv",
    )
    defender_candidates = generate_defender_candidates(
        defender_baseline,
        args.defender_candidates,
        args.seed,
        batch_id,
        attacker=attacker_baseline,
        ledger_path=output_root / "campaign_results.tsv",
    )
    for candidate in attacker_candidates + defender_candidates:
        lookup[candidate.candidate_id] = candidate

    current_attacker = attacker_baseline
    current_attacker_score = baseline_breakdown
    for index, candidate in enumerate(attacker_candidates):
        outcome = evaluate_match(
            adapter=adapter,
            attacker=candidate,
            defender=defender_baseline,
            budget=budget,
            batch_id=batch_id,
            label=f"attacker-{index}",
        )
        breakdown = score_match(outcome)
        frontier_pool = frontier_candidates(frontier, "attacker", lookup)
        decision = decide_promotion(
            role="attacker",
            candidate=candidate,
            candidate_score=breakdown,
            comparator=current_attacker,
            comparator_score=current_attacker_score,
            frontier=frontier_pool,
        )
        evaluation = EvaluatedCandidate(
            role="attacker",
            candidate_id=candidate.candidate_id,
            opponent_id=defender_baseline.candidate_id,
            outcome=outcome,
            score=breakdown.to_dict(),
            decision=decision,
        )
        artifact = build_run_artifact(
            batch_id=batch_id,
            candidate=candidate,
            opponent=defender_baseline,
            evaluated=evaluation,
            reproducibility=reproducibility,
        )
        path = persist_run_artifact(output_root, artifact)
        evaluation.artifact_path = str(path)
        evaluations.append(evaluation)
        if decision.status == "promoted":
            update_frontier(frontier, role="attacker", candidate=candidate, score=breakdown)
            current_attacker = candidate
            current_attacker_score = breakdown

    current_defender = defender_baseline
    current_defender_score = baseline_breakdown
    for index, candidate in enumerate(defender_candidates):
        outcome = evaluate_match(
            adapter=adapter,
            attacker=attacker_baseline,
            defender=candidate,
            budget=budget,
            batch_id=batch_id,
            label=f"defender-{index}",
        )
        breakdown = score_match(outcome)
        frontier_pool = frontier_candidates(frontier, "defender", lookup)
        decision = decide_promotion(
            role="defender",
            candidate=candidate,
            candidate_score=breakdown,
            comparator=current_defender,
            comparator_score=current_defender_score,
            frontier=frontier_pool,
        )
        evaluation = EvaluatedCandidate(
            role="defender",
            candidate_id=candidate.candidate_id,
            opponent_id=attacker_baseline.candidate_id,
            outcome=outcome,
            score=breakdown.to_dict(),
            decision=decision,
        )
        artifact = build_run_artifact(
            batch_id=batch_id,
            candidate=candidate,
            opponent=attacker_baseline,
            evaluated=evaluation,
            reproducibility=reproducibility,
        )
        path = persist_run_artifact(output_root, artifact)
        evaluation.artifact_path = str(path)
        evaluations.append(evaluation)
        if decision.status == "promoted":
            update_frontier(frontier, role="defender", candidate=candidate, score=breakdown)
            current_defender = candidate
            current_defender_score = breakdown

    batch_artifact = build_batch_artifact(
        batch_id=batch_id,
        adapter_name=adapter.name,
        budget=budget,
        frontier=frontier,
        evaluations=evaluations,
        reproducibility=reproducibility,
    )
    batch_json, summary_md = persist_batch_artifact(output_root, batch_artifact)
    if args.update_ledger:
        append_research_ledger(docs_root, batch_artifact)

    print(f"batch_id={batch_id}")
    print(f"evaluations={len(evaluations)}")
    print(f"promoted={len(batch_artifact.promoted)}")
    print(f"batch_json={batch_json}")
    print(f"summary_md={summary_md}")
    return 0


def _execute_campaign_iteration(
    *,
    args: argparse.Namespace,
    campaign_id: str,
    iteration: int,
    regime: CampaignRegime,
    adapter: Adapter,
    output_root: Path,
    frontier_state: FrontierState | None,
) -> tuple[FrontierState, list[dict[str, object]]]:
    current_attacker = frontier_incumbent(frontier_state, "attacker") if frontier_state else load_baseline_attacker()
    current_defender = frontier_incumbent(frontier_state, "defender") if frontier_state else load_baseline_defender()
    iteration_tag = f"{campaign_id}-i{iteration:03d}"

    attacker_candidates = generate_attacker_candidates(
        current_attacker,
        regime.attacker_candidates,
        derive_seed(regime.regime_id, campaign_id, iteration, "attacker"),
        iteration_tag,
        defender=current_defender,
        ledger_path=output_root / "campaign_results.tsv",
    )
    defender_candidates = generate_defender_candidates(
        current_defender,
        regime.defender_candidates,
        derive_seed(regime.regime_id, campaign_id, iteration, "defender"),
        iteration_tag,
        attacker=current_attacker,
        ledger_path=output_root / "campaign_results.tsv",
    )

    baseline_by_seed: dict[int, dict[str, Any]] = {}
    attacker_records: dict[str, dict[str, Any]] = {
        candidate.candidate_id: {"candidate": candidate, "seed_records": [], "error": None}
        for candidate in attacker_candidates
    }
    defender_records: dict[str, dict[str, Any]] = {
        candidate.candidate_id: {"candidate": candidate, "seed_records": [], "error": None}
        for candidate in defender_candidates
    }

    for seed in regime.seeds:
        budget = regime.budget_for_seed(seed)
        batch_id = _iteration_batch_id(campaign_id, iteration, seed)
        reproducibility = capture_reproducibility(cwd=Path.cwd(), argv=list(args.raw_argv), seed=seed)

        baseline_outcome = evaluate_match(
            adapter=adapter,
            attacker=current_attacker,
            defender=current_defender,
            budget=budget,
            batch_id=batch_id,
            label="baseline",
        )
        baseline_breakdown = score_match(baseline_outcome)
        baseline_by_seed[seed] = {
            "seed": seed,
            "budget": budget,
            "batch_id": batch_id,
            "outcome": baseline_outcome,
            "breakdown": baseline_breakdown,
            "reproducibility": reproducibility,
        }

        for index, candidate in enumerate(attacker_candidates):
            record = attacker_records[candidate.candidate_id]
            if record["error"] is not None:
                continue
            try:
                outcome = evaluate_match(
                    adapter=adapter,
                    attacker=candidate,
                    defender=current_defender,
                    budget=budget,
                    batch_id=batch_id,
                    label=f"attacker-{index}",
                )
            except Exception as exc:  # pragma: no cover - exercised by failure handling if adapter breaks
                record["error"] = f"{type(exc).__name__}: {exc}"
                continue
            record["seed_records"].append(
                {
                    "seed": seed,
                    "batch_id": batch_id,
                    "outcome": outcome,
                    "breakdown": score_match(outcome),
                    "reproducibility": reproducibility,
                }
            )

        for index, candidate in enumerate(defender_candidates):
            record = defender_records[candidate.candidate_id]
            if record["error"] is not None:
                continue
            try:
                outcome = evaluate_match(
                    adapter=adapter,
                    attacker=current_attacker,
                    defender=candidate,
                    budget=budget,
                    batch_id=batch_id,
                    label=f"defender-{index}",
                )
            except Exception as exc:  # pragma: no cover - exercised by failure handling if adapter breaks
                record["error"] = f"{type(exc).__name__}: {exc}"
                continue
            record["seed_records"].append(
                {
                    "seed": seed,
                    "batch_id": batch_id,
                    "outcome": outcome,
                    "breakdown": score_match(outcome),
                    "reproducibility": reproducibility,
                }
            )

    baseline_aggregate = aggregate_score_breakdowns(
        [baseline_by_seed[seed]["breakdown"] for seed in regime.seeds]
    )
    attacker_frontier = _frontier_pool(frontier_state, "attacker", current_attacker)
    defender_frontier = _frontier_pool(frontier_state, "defender", current_defender)

    attacker_scores: dict[str, ScoreBreakdown] = {}
    attacker_decisions: dict[str, PromotionDecision] = {}
    for candidate in attacker_candidates:
        record = attacker_records[candidate.candidate_id]
        if record["error"] is not None:
            continue
        aggregate = aggregate_score_breakdowns([item["breakdown"] for item in record["seed_records"]])
        attacker_scores[candidate.candidate_id] = aggregate
        attacker_decisions[candidate.candidate_id] = decide_promotion(
            role="attacker",
            candidate=candidate,
            candidate_score=aggregate,
            comparator=current_attacker,
            comparator_score=baseline_aggregate,
            frontier=attacker_frontier,
            improvement_floor=regime.improvement_floor,
            novelty_floor=regime.novelty_floor,
        )
    attacker_decisions = settle_iteration_promotions(
        role="attacker",
        candidate_scores=attacker_scores,
        decisions=attacker_decisions,
    )

    defender_scores: dict[str, ScoreBreakdown] = {}
    defender_decisions: dict[str, PromotionDecision] = {}
    for candidate in defender_candidates:
        record = defender_records[candidate.candidate_id]
        if record["error"] is not None:
            continue
        aggregate = aggregate_score_breakdowns([item["breakdown"] for item in record["seed_records"]])
        defender_scores[candidate.candidate_id] = aggregate
        defender_decisions[candidate.candidate_id] = decide_promotion(
            role="defender",
            candidate=candidate,
            candidate_score=aggregate,
            comparator=current_defender,
            comparator_score=baseline_aggregate,
            frontier=defender_frontier,
            improvement_floor=regime.improvement_floor,
            novelty_floor=regime.novelty_floor,
        )
    defender_decisions = settle_iteration_promotions(
        role="defender",
        candidate_scores=defender_scores,
        decisions=defender_decisions,
    )

    for seed in regime.seeds:
        seed_context = baseline_by_seed[seed]
        evaluations: list[EvaluatedCandidate] = []
        frontier_snapshot = seed_frontier(current_attacker, current_defender, seed_context["breakdown"])
        system_eval = EvaluatedCandidate(
            role="system",
            candidate_id=current_attacker.candidate_id,
            opponent_id=current_defender.candidate_id,
            outcome=seed_context["outcome"],
            score=seed_context["breakdown"].to_dict(),
            decision=_baseline_decision(
                current_attacker.candidate_id,
                current_attacker.candidate_id,
                seed_context["breakdown"].attacker_fitness,
            ),
        )
        system_artifact = build_run_artifact(
            batch_id=seed_context["batch_id"],
            candidate=current_attacker,
            opponent=current_defender,
            evaluated=system_eval,
            reproducibility=seed_context["reproducibility"],
        )
        system_path = persist_run_artifact(output_root, system_artifact)
        system_eval.artifact_path = str(system_path)
        seed_context["artifact_path"] = str(system_path)
        evaluations.append(system_eval)

        for candidate in attacker_candidates:
            record = attacker_records[candidate.candidate_id]
            seed_record = next((item for item in record["seed_records"] if item["seed"] == seed), None)
            if seed_record is None:
                continue
            decision = attacker_decisions[candidate.candidate_id]
            evaluation = EvaluatedCandidate(
                role="attacker",
                candidate_id=candidate.candidate_id,
                opponent_id=current_defender.candidate_id,
                outcome=seed_record["outcome"],
                score=seed_record["breakdown"].to_dict(),
                decision=decision,
            )
            artifact = build_run_artifact(
                batch_id=seed_context["batch_id"],
                candidate=candidate,
                opponent=current_defender,
                evaluated=evaluation,
                reproducibility=seed_record["reproducibility"],
            )
            path = persist_run_artifact(output_root, artifact)
            evaluation.artifact_path = str(path)
            seed_record["artifact_path"] = str(path)
            evaluations.append(evaluation)
            if decision.status == "promoted":
                update_frontier(frontier_snapshot, role="attacker", candidate=candidate, score=seed_record["breakdown"])

        for candidate in defender_candidates:
            record = defender_records[candidate.candidate_id]
            seed_record = next((item for item in record["seed_records"] if item["seed"] == seed), None)
            if seed_record is None:
                continue
            decision = defender_decisions[candidate.candidate_id]
            evaluation = EvaluatedCandidate(
                role="defender",
                candidate_id=candidate.candidate_id,
                opponent_id=current_attacker.candidate_id,
                outcome=seed_record["outcome"],
                score=seed_record["breakdown"].to_dict(),
                decision=decision,
            )
            artifact = build_run_artifact(
                batch_id=seed_context["batch_id"],
                candidate=candidate,
                opponent=current_attacker,
                evaluated=evaluation,
                reproducibility=seed_record["reproducibility"],
            )
            path = persist_run_artifact(output_root, artifact)
            evaluation.artifact_path = str(path)
            seed_record["artifact_path"] = str(path)
            evaluations.append(evaluation)
            if decision.status == "promoted":
                update_frontier(frontier_snapshot, role="defender", candidate=candidate, score=seed_record["breakdown"])

        batch_artifact = build_batch_artifact(
            batch_id=seed_context["batch_id"],
            adapter_name=adapter.name,
            budget=seed_context["budget"],
            frontier=frontier_snapshot,
            evaluations=evaluations,
            reproducibility=seed_context["reproducibility"],
        )
        batch_json, summary_md = persist_batch_artifact(output_root, batch_artifact)
        seed_context["batch_json"] = str(batch_json)
        seed_context["summary_md"] = str(summary_md)

    system_artifact_path = write_campaign_comparison_artifact(
        output_root=output_root,
        campaign_id=campaign_id,
        iteration=iteration,
        role="system",
        candidate_id=f"{current_attacker.candidate_id}-{current_defender.candidate_id}",
        payload={
            "campaign_id": campaign_id,
            "iteration": iteration,
            "regime": regime.to_dict(),
            "role": "system",
            "attacker": current_attacker.to_dict(),
            "defender": current_defender.to_dict(),
            "aggregate_score": baseline_aggregate.to_dict(),
            "seed_results": [
                {
                    "seed": seed,
                    "batch_id": baseline_by_seed[seed]["batch_id"],
                    "batch_summary": baseline_by_seed[seed]["batch_json"],
                    "run_artifact": baseline_by_seed[seed]["artifact_path"],
                    "score": baseline_by_seed[seed]["breakdown"].to_dict(),
                    "metrics": baseline_by_seed[seed]["outcome"].metrics,
                }
                for seed in regime.seeds
            ],
        },
    )

    if frontier_state is None:
        baseline_batch_ids = [baseline_by_seed[seed]["batch_id"] for seed in regime.seeds]
        frontier_state = build_frontier_state(
            regime_id=regime.regime_id,
            updated_at=_utc_now(),
            comparator={
                "rule": regime.comparator_rule,
                "promotion_rule": regime.promotion_rule,
                "seeds": list(regime.seeds),
                "num_tasks": regime.num_tasks,
                "max_turns": regime.max_turns,
                "last_campaign_id": campaign_id,
                "last_iteration": iteration,
            },
            attacker=current_attacker,
            attacker_score=baseline_aggregate,
            attacker_artifact_ref=str(system_artifact_path),
            attacker_batch_ids=baseline_batch_ids,
            defender=current_defender,
            defender_score=baseline_aggregate,
            defender_artifact_ref=str(system_artifact_path),
            defender_batch_ids=baseline_batch_ids,
        )

    rows: list[dict[str, object]] = []
    promoted_updates: list[dict[str, object]] = []
    role_contexts = [
        ("attacker", current_attacker, attacker_candidates, attacker_records, attacker_scores, attacker_decisions),
        ("defender", current_defender, defender_candidates, defender_records, defender_scores, defender_decisions),
    ]
    for role, incumbent, candidates, records, scores, decisions in role_contexts:
        for candidate in candidates:
            record = records[candidate.candidate_id]
            if record["error"] is not None:
                comparison_path = write_campaign_comparison_artifact(
                    output_root=output_root,
                    campaign_id=campaign_id,
                    iteration=iteration,
                    role=role,
                    candidate_id=candidate.candidate_id,
                    payload={
                        "campaign_id": campaign_id,
                        "iteration": iteration,
                        "regime": regime.to_dict(),
                        "role": role,
                        "incumbent": incumbent.to_dict(),
                        "challenger": candidate.to_dict(),
                        "decision": "crash",
                        "error": record["error"],
                        "seed_results": [
                            {
                                "seed": item["seed"],
                                "batch_id": item["batch_id"],
                                "run_artifact": item.get("artifact_path"),
                                "score": item["breakdown"].to_dict(),
                            }
                            for item in record["seed_records"]
                        ],
                    },
                )
                row = {
                    "campaign_id": campaign_id,
                    "iteration": iteration,
                    "regime_id": regime.regime_id,
                    "role": role,
                    "incumbent_id": incumbent.candidate_id,
                    "challenger_id": candidate.candidate_id,
                    "challenger_lineage": _lineage_text(candidate),
                    "scalar_fitness": "nan",
                    "delta_vs_incumbent": "nan",
                    "decision": "crash",
                    "novelty_score": "0.000000",
                    "artifact_path": str(comparison_path),
                    "status_note": record["error"],
                }
                append_campaign_result_row(output_root, row)
                rows.append(row)
                continue

            aggregate = scores[candidate.candidate_id]
            decision = decisions[candidate.candidate_id]
            scalar_fitness = role_score(aggregate, role)
            delta = scalar_fitness - role_score(baseline_aggregate, role)
            comparison_path = write_campaign_comparison_artifact(
                output_root=output_root,
                campaign_id=campaign_id,
                iteration=iteration,
                role=role,
                candidate_id=candidate.candidate_id,
                payload={
                    "campaign_id": campaign_id,
                    "iteration": iteration,
                    "regime": regime.to_dict(),
                    "role": role,
                    "incumbent": incumbent.to_dict(),
                    "challenger": candidate.to_dict(),
                    "aggregate_score": aggregate.to_dict(),
                    "incumbent_score": baseline_aggregate.to_dict(),
                    "delta_vs_incumbent": round(delta, 6),
                    "decision": decision.to_dict(),
                    "seed_results": [
                        {
                            "seed": item["seed"],
                            "batch_id": item["batch_id"],
                            "run_artifact": item["artifact_path"],
                            "score": item["breakdown"].to_dict(),
                            "metrics": item["outcome"].metrics,
                        }
                        for item in record["seed_records"]
                    ],
                },
            )
            row = {
                "campaign_id": campaign_id,
                "iteration": iteration,
                "regime_id": regime.regime_id,
                "role": role,
                "incumbent_id": incumbent.candidate_id,
                "challenger_id": candidate.candidate_id,
                "challenger_lineage": _lineage_text(candidate),
                "scalar_fitness": f"{scalar_fitness:.6f}",
                "delta_vs_incumbent": f"{delta:.6f}",
                "decision": _comparison_decision_label(decision.status),
                "novelty_score": f"{decision.novelty_score:.6f}",
                "artifact_path": str(comparison_path),
                "status_note": decision.reason,
            }
            append_campaign_result_row(output_root, row)
            rows.append(row)
            if decision.status == "promoted":
                promoted_updates.append(
                    {
                        "role": role,
                        "candidate": candidate,
                        "score": aggregate,
                        "artifact_path": str(comparison_path),
                        "batch_ids": [item["batch_id"] for item in record["seed_records"]],
                    }
                )

    updated_at = _utc_now()
    for update in promoted_updates:
        update_frontier_state(
            frontier_state,
            role=update["role"],
            candidate=update["candidate"],
            score=update["score"],
            artifact_ref=update["artifact_path"],
            batch_ids=update["batch_ids"],
            updated_at=updated_at,
            max_size=regime.max_frontier_entries,
        )
    frontier_state.comparator = {
        "rule": regime.comparator_rule,
        "promotion_rule": regime.promotion_rule,
        "seeds": list(regime.seeds),
        "num_tasks": regime.num_tasks,
        "max_turns": regime.max_turns,
        "last_campaign_id": campaign_id,
        "last_iteration": iteration,
        "comparison_attacker": current_attacker.candidate_id,
        "comparison_defender": current_defender.candidate_id,
        "frontier_after": {
            "attacker": frontier_state.attackers[0].candidate_id,
            "defender": frontier_state.defenders[0].candidate_id,
        },
        "system_report": {key: round(value, 6) for key, value in baseline_aggregate.system_report.items()},
        "system_artifact": str(system_artifact_path),
    }
    frontier_state.updated_at = updated_at
    return frontier_state, rows


def run_campaign(args: argparse.Namespace) -> int:
    regime = load_regime(args.regime)
    adapter = get_adapter(regime.adapter_name)
    output_root = Path(args.output_root)
    docs_root = Path(args.docs_root)
    frontier_path = output_root / "frontier.json"
    campaign_id = _campaign_id(regime.regime_id)
    frontier_state = load_frontier_state(frontier_path)
    if frontier_state is not None and frontier_state.regime_id != regime.regime_id:
        raise ValueError(
            f"frontier at {frontier_path} is pinned to regime {frontier_state.regime_id}, not {regime.regime_id}"
        )

    all_rows: list[dict[str, object]] = []
    for iteration in range(1, args.iterations + 1):
        frontier_state, rows = _execute_campaign_iteration(
            args=args,
            campaign_id=campaign_id,
            iteration=iteration,
            regime=regime,
            adapter=adapter,
            output_root=output_root,
            frontier_state=frontier_state,
        )
        persist_frontier_state(frontier_path, frontier_state)
        all_rows.extend(rows)

    summary = build_campaign_summary(
        campaign_id=campaign_id,
        regime_id=regime.regime_id,
        iterations=args.iterations,
        frontier_path=frontier_path,
        rows=all_rows,
    )
    summary_path = write_campaign_summary(output_root, campaign_id, summary)
    derived_paths: dict[str, Path] = {}
    if regime.regime_id == DEFAULT_REGIME_ID:
        derived_paths = write_machine_derived_summaries(output_root, docs_root)

    print(f"campaign_id={campaign_id}")
    print(f"regime_id={regime.regime_id}")
    print(f"iterations={args.iterations}")
    print(f"frontier={frontier_path}")
    print(f"ledger={output_root / 'campaign_results.tsv'}")
    print(f"summary={summary_path}")
    for label, path in derived_paths.items():
        print(f"{label}={path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AUTOATTACKER CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_flags(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--adapter", default="toy_control")
        subparser.add_argument("--seed", type=int, default=7)
        subparser.add_argument("--tasks", type=int, default=4)
        subparser.add_argument("--turns", type=int, default=6)
        subparser.add_argument("--output-root", default="runs")
        subparser.add_argument("--docs-root", default="docs")
        subparser.add_argument("--update-ledger", action="store_true")

    run_parser = subparsers.add_parser("run", help="Run one baseline match")
    add_common_flags(run_parser)
    run_parser.set_defaults(handler=run_single)

    batch_parser = subparsers.add_parser("batch", help="Run a bounded baseline plus mutation batch")
    add_common_flags(batch_parser)
    batch_parser.add_argument("--attacker-candidates", type=int, default=3)
    batch_parser.add_argument("--defender-candidates", type=int, default=3)
    batch_parser.set_defaults(handler=run_batch)

    campaign_parser = subparsers.add_parser("campaign", help="Run the canonical autonomous campaign loop")
    campaign_parser.add_argument("--regime", default=DEFAULT_REGIME_ID)
    campaign_parser.add_argument("--iterations", type=int, default=1)
    campaign_parser.add_argument("--output-root", default="runs")
    campaign_parser.add_argument("--docs-root", default="docs")
    campaign_parser.add_argument("--update-ledger", action="store_true")
    campaign_parser.set_defaults(handler=run_campaign)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    args = parser.parse_args(raw_argv)
    args.raw_argv = raw_argv
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
