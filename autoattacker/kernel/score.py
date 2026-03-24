from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean

from autoattacker.kernel.candidates import MatchOutcome


@dataclass(slots=True)
class ScoreWeights:
    attack_success: float = 1.0
    stealth_score: float = 1.0
    attacker_cost_penalty: float = 1.0
    defender_success: float = 1.0
    false_positive_penalty: float = 1.0
    defender_cost_penalty: float = 1.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(slots=True)
class ScoreBreakdown:
    attacker_fitness: float
    defender_fitness: float
    system_report: dict[str, float]
    weights: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return {
            "attacker_fitness": round(self.attacker_fitness, 6),
            "defender_fitness": round(self.defender_fitness, 6),
            "system_report": {key: round(value, 6) for key, value in self.system_report.items()},
            "weights": self.weights,
        }


def score_match(outcome: MatchOutcome, weights: ScoreWeights | None = None) -> ScoreBreakdown:
    score_weights = weights or ScoreWeights()
    attacker_fitness = (
        score_weights.attack_success * outcome.attack_success
        + score_weights.stealth_score * outcome.stealth_score
        - score_weights.attacker_cost_penalty * outcome.cost_penalty
    )
    defender_fitness = (
        score_weights.defender_success * outcome.defender_success
        - score_weights.false_positive_penalty * outcome.false_positive_penalty
        - score_weights.defender_cost_penalty * outcome.cost_penalty
    )
    system_report = {
        "attack_success": outcome.attack_success,
        "attack_progress": outcome.metrics.get("attack_progress", outcome.attack_success),
        "stealth_score": outcome.stealth_score,
        "defender_success": outcome.defender_success,
        "false_positive_penalty": outcome.false_positive_penalty,
        "cost_penalty": outcome.cost_penalty,
        "budget_used": outcome.budget_used,
        "stability": outcome.stability,
    }
    return ScoreBreakdown(
        attacker_fitness=round(attacker_fitness, 6),
        defender_fitness=round(defender_fitness, 6),
        system_report=system_report,
        weights=score_weights.to_dict(),
    )


def aggregate_score_breakdowns(breakdowns: list[ScoreBreakdown]) -> ScoreBreakdown:
    if not breakdowns:
        raise ValueError("cannot aggregate empty score list")
    report_keys = sorted({key for breakdown in breakdowns for key in breakdown.system_report})
    system_report = {
        key: round(mean(breakdown.system_report.get(key, 0.0) for breakdown in breakdowns), 6)
        for key in report_keys
    }
    return ScoreBreakdown(
        attacker_fitness=round(mean(breakdown.attacker_fitness for breakdown in breakdowns), 6),
        defender_fitness=round(mean(breakdown.defender_fitness for breakdown in breakdowns), 6),
        system_report=system_report,
        weights=dict(breakdowns[0].weights),
    )
