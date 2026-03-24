from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoattacker.kernel.baseline import load_baseline_attacker, load_baseline_defender
from autoattacker.kernel.candidates import AttackerCandidate, CandidateLineage
from autoattacker.kernel.portfolio import (
    build_frontier_state,
    frontier_incumbent,
    frontier_state_candidates,
    load_frontier_state,
    persist_frontier_state,
    update_frontier_state,
)
from autoattacker.kernel.score import ScoreBreakdown


class FrontierStateTests(unittest.TestCase):
    def test_frontier_state_persists_and_updates(self) -> None:
        attacker = load_baseline_attacker()
        defender = load_baseline_defender()
        baseline_score = ScoreBreakdown(
            attacker_fitness=-0.5,
            defender_fitness=-0.3,
            system_report={"attack_success": 0.1, "defender_success": 0.8},
            weights={},
        )
        state = build_frontier_state(
            regime_id="toy_default_v1",
            updated_at="2026-03-24T00:00:00+00:00",
            comparator={"rule": "fixed"},
            attacker=attacker,
            attacker_score=baseline_score,
            attacker_artifact_ref="runs/c0/system.json",
            attacker_batch_ids=["batch-1"],
            defender=defender,
            defender_score=baseline_score,
            defender_artifact_ref="runs/c0/system.json",
            defender_batch_ids=["batch-1"],
        )
        challenger = AttackerCandidate(
            candidate_id="attacker-promoted",
            name="Promoted Attacker",
            description="Improved attacker",
            parameters={"aggression": 0.66, "stealth": 0.52, "persistence": 0.61},
            lineage=CandidateLineage(parent_id=attacker.candidate_id, generation=1, mutation_note="mutate aggression"),
            tags=["mutated"],
        )
        challenger_score = ScoreBreakdown(
            attacker_fitness=-0.2,
            defender_fitness=-0.35,
            system_report={"attack_success": 0.3, "defender_success": 0.6},
            weights={},
        )
        update_frontier_state(
            state,
            role="attacker",
            candidate=challenger,
            score=challenger_score,
            artifact_ref="runs/c1/attacker-promoted.json",
            batch_ids=["batch-2", "batch-3"],
            updated_at="2026-03-24T01:00:00+00:00",
            max_size=3,
        )
        self.assertEqual(frontier_incumbent(state, "attacker").candidate_id, challenger.candidate_id)
        self.assertEqual(len(frontier_state_candidates(state, "attacker")), 2)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "frontier.json"
            persist_frontier_state(path, state)
            loaded = load_frontier_state(path)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.regime_id, "toy_default_v1")
            self.assertEqual(frontier_incumbent(loaded, "attacker").candidate_id, challenger.candidate_id)


if __name__ == "__main__":
    unittest.main()
