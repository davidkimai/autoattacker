from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from autoattacker.kernel.candidates import (
    AttackerCandidate,
    DefenderCandidate,
    MatchBudget,
    MatchOutcome,
)


@dataclass(slots=True)
class MatchSpec:
    run_id: str
    adapter_name: str
    attacker: AttackerCandidate
    defender: DefenderCandidate
    budget: MatchBudget
    tasks: list[Any]
    config: dict[str, Any] = field(default_factory=dict)


class Adapter(ABC):
    name: str

    @abstractmethod
    def load_tasks(self, seed: int, limit: int) -> list[Any]:
        raise NotImplementedError

    @abstractmethod
    def instantiate_match(
        self,
        attacker: AttackerCandidate,
        defender: DefenderCandidate,
        budget: MatchBudget,
        tasks: list[Any],
        run_id: str,
    ) -> MatchSpec:
        raise NotImplementedError

    @abstractmethod
    def run_match(self, match_spec: MatchSpec) -> MatchOutcome:
        raise NotImplementedError

    @abstractmethod
    def summarize_outcome(self, outcome: MatchOutcome) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def score_components(self, outcome: MatchOutcome) -> dict[str, float]:
        raise NotImplementedError
