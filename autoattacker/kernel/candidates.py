from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

DecisionStatus = Literal["promoted", "archived", "discarded"]
Role = Literal["attacker", "defender", "system"]

ATTACKER_KEYS = ("aggression", "stealth", "persistence")
DEFENDER_KEYS = ("sensitivity", "hardening", "response_speed")


@dataclass(slots=True)
class CandidateLineage:
    parent_id: str | None = None
    generation: int = 0
    mutation_note: str = "baseline"
    batch_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class CandidateBase:
    candidate_id: str
    name: str
    description: str
    parameters: dict[str, float]
    lineage: CandidateLineage = field(default_factory=CandidateLineage)
    notes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    role: str = field(init=False, default="candidate")

    def validate(self, required_keys: tuple[str, ...]) -> None:
        missing = [key for key in required_keys if key not in self.parameters]
        if missing:
            raise ValueError(f"missing parameters for {self.role}: {missing}")
        for key in required_keys:
            value = self.parameters[key]
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"parameter {key} must be within [0, 1], got {value}")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class AttackerCandidate(CandidateBase):
    role: str = field(init=False, default="attacker")

    def __post_init__(self) -> None:
        self.validate(ATTACKER_KEYS)


@dataclass(slots=True)
class DefenderCandidate(CandidateBase):
    role: str = field(init=False, default="defender")

    def __post_init__(self) -> None:
        self.validate(DEFENDER_KEYS)


@dataclass(slots=True)
class MatchBudget:
    seed: int
    num_tasks: int = 4
    max_turns: int = 6
    max_actions_per_turn: int = 1
    max_cost_units: float = 24.0

    def __post_init__(self) -> None:
        if self.num_tasks <= 0:
            raise ValueError("num_tasks must be positive")
        if self.max_turns <= 0:
            raise ValueError("max_turns must be positive")
        if self.max_actions_per_turn <= 0:
            raise ValueError("max_actions_per_turn must be positive")
        if self.max_cost_units <= 0:
            raise ValueError("max_cost_units must be positive")

    @property
    def total_action_budget(self) -> int:
        return self.num_tasks * self.max_turns * self.max_actions_per_turn

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class TaskTrace:
    task_id: str
    actions: list[str]
    success: bool
    progress: float
    hidden_objective_score: float
    anomaly_peak: float
    alerts: int
    false_positives: int
    turns_used: int
    cost_used: float
    notes: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class MatchOutcome:
    run_id: str
    attacker_id: str
    defender_id: str
    adapter_name: str
    task_ids: list[str]
    budget: MatchBudget
    attack_success: float
    stealth_score: float
    defender_success: float
    false_positive_penalty: float
    cost_penalty: float
    budget_used: float
    stability: float
    metrics: dict[str, float]
    traces: list[TaskTrace]
    notes: str
    trace_pointer: str | None = "embedded"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["budget"] = self.budget.to_dict()
        payload["traces"] = [trace.to_dict() for trace in self.traces]
        return payload


@dataclass(slots=True)
class PromotionDecision:
    role: Role
    candidate_id: str
    comparator_id: str
    candidate_score: float
    comparator_score: float
    novelty_score: float
    status: DecisionStatus
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class EvaluatedCandidate:
    role: Literal["attacker", "defender", "system"]
    candidate_id: str
    opponent_id: str
    outcome: MatchOutcome
    score: dict[str, object]
    decision: PromotionDecision
    artifact_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "candidate_id": self.candidate_id,
            "opponent_id": self.opponent_id,
            "outcome": self.outcome.to_dict(),
            "score": self.score,
            "decision": self.decision.to_dict(),
            "artifact_path": self.artifact_path,
        }


def candidate_distance(left: CandidateBase, right: CandidateBase) -> float:
    keys = tuple(sorted(set(left.parameters) | set(right.parameters)))
    total = 0.0
    for key in keys:
        total += abs(left.parameters.get(key, 0.0) - right.parameters.get(key, 0.0))
    return total / max(1, len(keys))
