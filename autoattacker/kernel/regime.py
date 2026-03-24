from __future__ import annotations

from dataclasses import asdict, dataclass

from autoattacker.kernel.candidates import MatchBudget

DEFAULT_REGIME_ID = "toy_default_v1"
PORTABILITY_REGIME_ID = "toy_shifted_smoke_v1"


@dataclass(slots=True, frozen=True)
class CampaignRegime:
    regime_id: str
    adapter_name: str
    seeds: tuple[int, ...]
    num_tasks: int
    max_turns: int
    attacker_candidates: int
    defender_candidates: int
    improvement_floor: float
    novelty_floor: float
    max_frontier_entries: int = 3
    task_mix: str = "toy_control_calibrated_4slot_v1"
    comparator_rule: str = "mean_role_fitness_over_frozen_seed_set"
    promotion_rule: str = "promote_only_on_positive_incumbent_delta_with_artifact_backing"

    def budget_for_seed(self, seed: int) -> MatchBudget:
        return MatchBudget(
            seed=seed,
            num_tasks=self.num_tasks,
            max_turns=self.max_turns,
            max_actions_per_turn=1,
            max_cost_units=float(self.num_tasks * self.max_turns),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


REGIMES: dict[str, CampaignRegime] = {
    DEFAULT_REGIME_ID: CampaignRegime(
        regime_id=DEFAULT_REGIME_ID,
        adapter_name="toy_control",
        seeds=(7, 11, 19),
        num_tasks=4,
        max_turns=6,
        attacker_candidates=3,
        defender_candidates=3,
        improvement_floor=0.025,
        novelty_floor=0.05,
    ),
    PORTABILITY_REGIME_ID: CampaignRegime(
        regime_id=PORTABILITY_REGIME_ID,
        adapter_name="toy_control_shifted",
        seeds=(5, 13),
        num_tasks=4,
        max_turns=6,
        attacker_candidates=2,
        defender_candidates=2,
        improvement_floor=0.025,
        novelty_floor=0.05,
        task_mix="toy_control_shifted_4slot_v1",
    ),
}


def load_regime(regime_id: str) -> CampaignRegime:
    try:
        return REGIMES[regime_id]
    except KeyError as exc:
        known = ", ".join(sorted(REGIMES))
        raise ValueError(f"unknown regime {regime_id}; known regimes: {known}") from exc
