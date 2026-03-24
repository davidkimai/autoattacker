from __future__ import annotations

import unittest

from autoattacker.kernel.baseline import default_budget, load_baseline_attacker, load_baseline_defender
from autoattacker.kernel.candidates import AttackerCandidate


class CandidateSchemaTests(unittest.TestCase):
    def test_baselines_validate(self) -> None:
        attacker = load_baseline_attacker()
        defender = load_baseline_defender()
        self.assertEqual(attacker.role, "attacker")
        self.assertEqual(defender.role, "defender")
        self.assertEqual(attacker.lineage.mutation_note, "baseline")
        self.assertIn("aggression", attacker.parameters)
        self.assertIn("sensitivity", defender.parameters)

    def test_invalid_candidate_raises(self) -> None:
        with self.assertRaises(ValueError):
            AttackerCandidate(
                candidate_id="bad-attacker",
                name="Bad",
                description="invalid",
                parameters={"aggression": 1.2, "stealth": 0.5, "persistence": 0.4},
            )

    def test_budget_has_comparable_action_surface(self) -> None:
        budget = default_budget(seed=7, num_tasks=3, max_turns=5)
        self.assertEqual(budget.total_action_budget, 15)
        self.assertEqual(budget.max_cost_units, 15.0)


if __name__ == "__main__":
    unittest.main()
