from __future__ import annotations

from autoattacker.kernel.candidates import (
    AttackerCandidate,
    CandidateLineage,
    DefenderCandidate,
    MatchBudget,
)


def load_baseline_attacker() -> AttackerCandidate:
    return AttackerCandidate(
        candidate_id="attacker-baseline",
        name="Baseline Attacker",
        description="Balanced baseline attacker for the toy control adapter.",
        parameters={
            "aggression": 0.58,
            "stealth": 0.47,
            "persistence": 0.55,
        },
        lineage=CandidateLineage(mutation_note="baseline", generation=0),
        tags=["baseline", "toy_control"],
    )


def load_baseline_defender() -> DefenderCandidate:
    return DefenderCandidate(
        candidate_id="defender-baseline",
        name="Baseline Defender",
        description="Balanced baseline defender for the toy control adapter.",
        parameters={
            "sensitivity": 0.56,
            "hardening": 0.50,
            "response_speed": 0.54,
        },
        lineage=CandidateLineage(mutation_note="baseline", generation=0),
        tags=["baseline", "toy_control"],
    )


def default_budget(seed: int, num_tasks: int = 4, max_turns: int = 6) -> MatchBudget:
    return MatchBudget(
        seed=seed,
        num_tasks=num_tasks,
        max_turns=max_turns,
        max_actions_per_turn=1,
        max_cost_units=float(num_tasks * max_turns),
    )
