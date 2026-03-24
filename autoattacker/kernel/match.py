from __future__ import annotations

from autoattacker.adapters.base import Adapter
from autoattacker.kernel.candidates import AttackerCandidate, DefenderCandidate, MatchBudget, MatchOutcome
from autoattacker.utils.seeds import short_hash


def evaluate_match(
    *,
    adapter: Adapter,
    attacker: AttackerCandidate,
    defender: DefenderCandidate,
    budget: MatchBudget,
    batch_id: str,
    label: str,
) -> MatchOutcome:
    run_id = f"run-{short_hash(batch_id, label, attacker.candidate_id, defender.candidate_id, budget.seed)}"
    tasks = adapter.load_tasks(seed=budget.seed, limit=budget.num_tasks)
    match_spec = adapter.instantiate_match(
        attacker=attacker,
        defender=defender,
        budget=budget,
        tasks=tasks,
        run_id=run_id,
    )
    match_spec.config["label"] = label
    return adapter.run_match(match_spec)
