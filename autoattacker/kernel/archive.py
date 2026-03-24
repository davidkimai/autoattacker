from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autoattacker.artifacts.leaderboard import build_leaderboard
from autoattacker.artifacts.schema import BatchArtifact, RunArtifact, SCHEMA_VERSION
from autoattacker.artifacts.writer import write_batch_artifact, write_batch_summary, write_run_artifact
from autoattacker.kernel.candidates import CandidateBase, EvaluatedCandidate, MatchBudget, PromotionDecision
from autoattacker.kernel.portfolio import Frontier
from autoattacker.kernel.score import ScoreBreakdown
from autoattacker.utils.io import append_text, ensure_dir, write_json, write_text

CAMPAIGN_LEDGER_HEADER = [
    "campaign_id",
    "iteration",
    "regime_id",
    "role",
    "incumbent_id",
    "challenger_id",
    "challenger_lineage",
    "scalar_fitness",
    "delta_vs_incumbent",
    "decision",
    "novelty_score",
    "artifact_path",
    "status_note",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_run_artifact(
    *,
    batch_id: str,
    candidate: CandidateBase,
    opponent: CandidateBase,
    evaluated: EvaluatedCandidate,
    reproducibility: dict[str, Any],
) -> RunArtifact:
    outcome = evaluated.outcome
    return RunArtifact(
        schema_version=SCHEMA_VERSION,
        created_at=_utc_now(),
        batch_id=batch_id,
        run_id=outcome.run_id,
        attacker_id=outcome.attacker_id,
        defender_id=outcome.defender_id,
        attacker_lineage=(candidate.lineage.to_dict() if candidate.role == "attacker" else opponent.lineage.to_dict()),
        defender_lineage=(candidate.lineage.to_dict() if candidate.role == "defender" else opponent.lineage.to_dict()),
        adapter_name=outcome.adapter_name,
        task_ids=outcome.task_ids,
        config={"evaluation_role": evaluated.role},
        budget=outcome.budget.to_dict(),
        metrics=outcome.metrics,
        outcome=outcome.to_dict(),
        score=evaluated.score,
        promotion_decision=evaluated.decision.to_dict(),
        trace_refs=[outcome.trace_pointer or "embedded"],
        reproducibility=reproducibility,
    )


def persist_run_artifact(output_root: Path, artifact: RunArtifact) -> Path:
    return write_run_artifact(output_root=output_root, artifact=artifact)


def build_batch_artifact(
    *,
    batch_id: str,
    adapter_name: str,
    budget: MatchBudget,
    frontier: Frontier,
    evaluations: list[EvaluatedCandidate],
    reproducibility: dict[str, Any],
) -> BatchArtifact:
    leaderboard = build_leaderboard(evaluations)
    promoted = [record.to_dict() for record in evaluations if record.decision.status == "promoted"]
    archived = [record.to_dict() for record in evaluations if record.decision.status == "archived"]
    discarded = [record.to_dict() for record in evaluations if record.decision.status == "discarded"]
    return BatchArtifact(
        schema_version=SCHEMA_VERSION,
        created_at=_utc_now(),
        batch_id=batch_id,
        adapter_name=adapter_name,
        budget=budget.to_dict(),
        frontier=frontier.to_dict(),
        evaluations=[record.to_dict() for record in evaluations],
        promoted=promoted,
        archived=archived,
        discarded=discarded,
        leaderboard=leaderboard,
        reproducibility=reproducibility,
    )


def persist_batch_artifact(output_root: Path, artifact: BatchArtifact) -> tuple[Path, Path]:
    batch_json = write_batch_artifact(output_root=output_root, artifact=artifact)
    summary_md = write_batch_summary(output_root=output_root, artifact=artifact)
    return batch_json, summary_md


def append_research_ledger(docs_root: Path, batch_artifact: BatchArtifact) -> None:
    ledger_path = docs_root / "RESEARCH_LEDGER.md"
    promoted = [record for record in batch_artifact.promoted if record["role"] != "system"]
    discarded = [record for record in batch_artifact.discarded if record["role"] != "system"]
    lines = [
        "",
        f"## Batch {batch_artifact.batch_id}",
        "",
        "### Promoted Frontier",
    ]
    if promoted:
        for record in promoted:
            lines.append(
                f"- {record['candidate_id']} ({record['role']}) promoted over {record['decision']['comparator_id']}"
            )
    else:
        lines.append("- None in this batch.")
    lines.extend(["", "### Discarded Branches"])
    if discarded:
        for record in discarded:
            lines.append(
                f"- {record['candidate_id']} ({record['role']}) discarded: {record['decision']['reason']}"
            )
    else:
        lines.append("- None in this batch.")
    lines.extend(["", "### Winning Candidates"])
    if promoted:
        for record in promoted:
            lines.append(
                f"- {record['candidate_id']}: score {record['decision']['candidate_score']:.3f}"
            )
    else:
        lines.append("- Baseline remained the comparator frontier.")
    lines.extend(["", "### Why They Won"])
    if promoted:
        for record in promoted:
            lines.append(f"- {record['decision']['reason']}")
    else:
        lines.append("- No challenger cleared the promotion bar in this batch.")
    lines.extend(["", "### What Should Be Tried Next"])
    lines.append("- Re-run on a different seed to test stability.")
    lines.append("- Add one stronger mutation operator or a second adapter only if the current loop stays stable.")
    append_text(ledger_path, "\n".join(lines) + "\n")


def append_campaign_result_row(output_root: Path, row: dict[str, object]) -> Path:
    ledger_path = output_root / "campaign_results.tsv"
    if not ledger_path.exists():
        append_text(ledger_path, "\t".join(CAMPAIGN_LEDGER_HEADER) + "\n")
    values = [_sanitize_tsv_value(row.get(column, "")) for column in CAMPAIGN_LEDGER_HEADER]
    append_text(ledger_path, "\t".join(values) + "\n")
    return ledger_path


def write_campaign_comparison_artifact(
    *,
    output_root: Path,
    campaign_id: str,
    iteration: int,
    role: str,
    candidate_id: str,
    payload: dict[str, Any],
) -> Path:
    comparison_dir = ensure_dir(output_root / campaign_id / "comparisons" / f"iter-{iteration:03d}")
    artifact_path = comparison_dir / f"{role}-{candidate_id}.json"
    write_json(artifact_path, payload)
    return artifact_path


def write_campaign_summary(output_root: Path, campaign_id: str, content: str) -> Path:
    summary_dir = ensure_dir(output_root / campaign_id)
    summary_path = summary_dir / "campaign_summary.md"
    write_text(summary_path, content)
    return summary_path


def build_campaign_summary(
    *,
    campaign_id: str,
    regime_id: str,
    iterations: int,
    frontier_path: Path,
    rows: list[dict[str, object]],
) -> str:
    promoted = [row for row in rows if row["decision"] == "promote"]
    archived = [row for row in rows if row["decision"] == "archive_interesting"]
    crashes = [row for row in rows if row["decision"] == "crash"]
    strongest_next = _strongest_next_branch(archived)
    lines = [
        f"# Campaign {campaign_id}",
        "",
        f"- Regime: {regime_id}",
        f"- Iterations: {iterations}",
        f"- Frontier state: {frontier_path}",
        f"- Promotions: {len(promoted)}",
        f"- Archived: {len(archived)}",
        f"- Crashes: {len(crashes)}",
        "",
        "## What Was Tried",
    ]
    if rows:
        for row in rows:
            lines.append(
                f"- iter {row['iteration']} {row['role']} {row['challenger_id']} vs {row['incumbent_id']}: {row['decision']} ({row['status_note']})"
            )
    else:
        lines.append("- No challenger rows were recorded.")
    lines.extend(["", "## Frontier Delta"])
    if promoted:
        for row in promoted:
            lines.append(
                f"- {row['role']} frontier advanced: {row['incumbent_id']} -> {row['challenger_id']} (delta {row['delta_vs_incumbent']})"
            )
    else:
        lines.append("- No frontier promotions in this campaign.")
    lines.extend(["", "## Strongest Next Branch"])
    lines.append(f"- {strongest_next}")
    return "\n".join(lines) + "\n"


def _strongest_next_branch(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "No archived branch beat the incumbent closely enough to prioritize over current operator tuning."
    best = max(rows, key=lambda row: float(row.get("delta_vs_incumbent", -999.0)))
    return (
        f"Revisit {best['role']} challenger {best['challenger_id']} first; it archived with delta "
        f"{best['delta_vs_incumbent']} and novelty {best['novelty_score']}."
    )


def _sanitize_tsv_value(value: object) -> str:
    return str(value).replace("\t", " ").replace("\n", " ")
