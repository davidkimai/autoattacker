from __future__ import annotations

from autoattacker.kernel.baseline import default_budget
from autoattacker.kernel.candidates import MatchBudget


def make_budget(seed: int, num_tasks: int, max_turns: int) -> MatchBudget:
    return default_budget(seed=seed, num_tasks=num_tasks, max_turns=max_turns)


def budget_ratio(used: float, max_units: float) -> float:
    return 0.0 if max_units <= 0 else round(min(1.0, used / max_units), 6)
