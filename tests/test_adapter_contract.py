from __future__ import annotations

import unittest

from autoattacker.adapters.toy_control.adapter import ToyControlAdapter, ToyControlShiftedAdapter
from autoattacker.kernel.baseline import default_budget, load_baseline_attacker, load_baseline_defender


class AdapterContractTests(unittest.TestCase):
    def test_toy_adapter_contract(self) -> None:
        adapter = ToyControlAdapter()
        attacker = load_baseline_attacker()
        defender = load_baseline_defender()
        budget = default_budget(seed=7, num_tasks=3, max_turns=4)
        tasks = adapter.load_tasks(seed=7, limit=3)
        self.assertEqual(len(tasks), 3)
        goals = [task.goal_threshold for task in tasks]
        self.assertGreater(max(goals) - min(goals), 0.1)
        match_spec = adapter.instantiate_match(attacker, defender, budget, tasks, run_id="demo-run")
        outcome = adapter.run_match(match_spec)
        summary = adapter.summarize_outcome(outcome)
        components = adapter.score_components(outcome)
        self.assertEqual(outcome.adapter_name, "toy_control")
        self.assertEqual(len(outcome.traces), 3)
        self.assertIn("attack_success", summary)
        self.assertIn("attack_progress", summary)
        self.assertIn("stealth_score", components)
        self.assertIn("attack_progress", components)
        self.assertGreaterEqual(outcome.cost_penalty, 0.0)
        self.assertLessEqual(outcome.cost_penalty, 1.0)

    def test_shifted_adapter_contract(self) -> None:
        adapter = ToyControlShiftedAdapter()
        attacker = load_baseline_attacker()
        defender = load_baseline_defender()
        budget = default_budget(seed=5, num_tasks=3, max_turns=4)
        tasks = adapter.load_tasks(seed=5, limit=3)
        self.assertTrue(all(task.task_id.startswith("shifted-task-") for task in tasks))
        match_spec = adapter.instantiate_match(attacker, defender, budget, tasks, run_id="shifted-run")
        outcome = adapter.run_match(match_spec)
        self.assertEqual(outcome.adapter_name, "toy_control_shifted")
        self.assertEqual(len(outcome.traces), 3)
        self.assertIn("attack_progress", outcome.metrics)

    def test_toy_adapter_is_stable_under_same_seed_pairing(self) -> None:
        adapter = ToyControlAdapter()
        attacker = load_baseline_attacker()
        defender = load_baseline_defender()
        budget = default_budget(seed=11, num_tasks=4, max_turns=6)
        tasks = adapter.load_tasks(seed=11, limit=4)
        left = adapter.run_match(adapter.instantiate_match(attacker, defender, budget, tasks, run_id="left-run"))
        right = adapter.run_match(adapter.instantiate_match(attacker, defender, budget, tasks, run_id="right-run"))
        self.assertEqual(left.metrics, right.metrics)
        self.assertEqual(
            [trace.to_dict() for trace in left.traces],
            [trace.to_dict() for trace in right.traces],
        )


if __name__ == "__main__":
    unittest.main()
