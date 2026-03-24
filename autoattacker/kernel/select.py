from __future__ import annotations

from autoattacker.kernel.candidates import (
    AttackerCandidate,
    CandidateBase,
    DefenderCandidate,
    PromotionDecision,
    candidate_distance,
)
from autoattacker.kernel.score import ScoreBreakdown


def role_score(score: ScoreBreakdown, role: str) -> float:
    if role == "attacker":
        return score.attacker_fitness
    if role == "defender":
        return score.defender_fitness
    raise ValueError(f"unsupported role {role}")


def _novelty(candidate: CandidateBase, frontier: list[CandidateBase]) -> float:
    if not frontier:
        return 1.0
    return round(min(candidate_distance(candidate, incumbent) for incumbent in frontier), 6)


def decide_promotion(
    *,
    role: str,
    candidate: AttackerCandidate | DefenderCandidate,
    candidate_score: ScoreBreakdown,
    comparator: AttackerCandidate | DefenderCandidate,
    comparator_score: ScoreBreakdown,
    frontier: list[CandidateBase],
    improvement_floor: float = 0.025,
    novelty_floor: float = 0.05,
) -> PromotionDecision:
    candidate_value = role_score(candidate_score, role)
    comparator_value = role_score(comparator_score, role)
    delta = candidate_value - comparator_value
    novelty = _novelty(candidate, frontier)

    if delta >= improvement_floor and (novelty >= novelty_floor or delta >= improvement_floor * 2):
        status = "promoted"
        reason = f"beats comparator by {delta:.3f} with novelty {novelty:.3f}"
    elif delta >= -0.01 or novelty >= novelty_floor * 1.5:
        status = "archived"
        reason = f"informative result: delta {delta:.3f}, novelty {novelty:.3f}"
    else:
        status = "discarded"
        reason = f"loses comparator by {-delta:.3f} without compensating novelty"

    return PromotionDecision(
        role=role,
        candidate_id=candidate.candidate_id,
        comparator_id=comparator.candidate_id,
        candidate_score=round(candidate_value, 6),
        comparator_score=round(comparator_value, 6),
        novelty_score=novelty,
        status=status,
        reason=reason,
    )


def settle_iteration_promotions(
    *,
    role: str,
    candidate_scores: dict[str, ScoreBreakdown],
    decisions: dict[str, PromotionDecision],
) -> dict[str, PromotionDecision]:
    promoted_ids = [
        candidate_id
        for candidate_id, decision in decisions.items()
        if decision.status == "promoted"
    ]
    if len(promoted_ids) <= 1:
        return decisions

    winner_id = max(promoted_ids, key=lambda candidate_id: role_score(candidate_scores[candidate_id], role))
    settled: dict[str, PromotionDecision] = {}
    for candidate_id, decision in decisions.items():
        if candidate_id == winner_id or decision.status != "promoted":
            settled[candidate_id] = decision
            continue
        settled[candidate_id] = PromotionDecision(
            role=decision.role,
            candidate_id=decision.candidate_id,
            comparator_id=decision.comparator_id,
            candidate_score=decision.candidate_score,
            comparator_score=decision.comparator_score,
            novelty_score=decision.novelty_score,
            status="archived",
            reason=(
                f"beats incumbent but loses same-iteration comparison to {winner_id} "
                f"({decision.candidate_score:.3f} vs {decisions[winner_id].candidate_score:.3f})"
            ),
        )
    return settled
