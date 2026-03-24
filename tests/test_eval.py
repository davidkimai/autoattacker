from __future__ import annotations

import unittest

from autoattacker.kernel.eval import DEFAULT_EVAL_ID, PORTABILITY_EVAL_ID, load_eval_setup


class EvaluationSetupTests(unittest.TestCase):
    def test_toy_default_v1_is_frozen(self) -> None:
        eval_setup = load_eval_setup(DEFAULT_EVAL_ID)
        self.assertEqual(eval_setup.adapter_name, "toy_control")
        self.assertEqual(eval_setup.seeds, (7, 11, 19))
        self.assertEqual(eval_setup.attacker_candidates, 3)
        self.assertEqual(eval_setup.defender_candidates, 3)
        budget = eval_setup.budget_for_seed(11)
        self.assertEqual(budget.seed, 11)
        self.assertEqual(budget.num_tasks, 4)
        self.assertEqual(budget.max_turns, 6)

    def test_portability_eval_is_frozen(self) -> None:
        eval_setup = load_eval_setup(PORTABILITY_EVAL_ID)
        self.assertEqual(eval_setup.adapter_name, "toy_control_shifted")
        self.assertEqual(eval_setup.seeds, (5, 13))
        self.assertEqual(eval_setup.attacker_candidates, 2)
        self.assertEqual(eval_setup.defender_candidates, 2)

    def test_unknown_eval_raises(self) -> None:
        with self.assertRaises(ValueError):
            load_eval_setup("does-not-exist")


if __name__ == "__main__":
    unittest.main()
