from __future__ import annotations

import unittest

from autoattacker.kernel.regime import DEFAULT_REGIME_ID, PORTABILITY_REGIME_ID, load_regime


class RegimeTests(unittest.TestCase):
    def test_toy_default_v1_is_frozen(self) -> None:
        regime = load_regime(DEFAULT_REGIME_ID)
        self.assertEqual(regime.adapter_name, "toy_control")
        self.assertEqual(regime.seeds, (7, 11, 19))
        self.assertEqual(regime.attacker_candidates, 3)
        self.assertEqual(regime.defender_candidates, 3)
        budget = regime.budget_for_seed(11)
        self.assertEqual(budget.seed, 11)
        self.assertEqual(budget.num_tasks, 4)
        self.assertEqual(budget.max_turns, 6)

    def test_portability_regime_is_frozen(self) -> None:
        regime = load_regime(PORTABILITY_REGIME_ID)
        self.assertEqual(regime.adapter_name, "toy_control_shifted")
        self.assertEqual(regime.seeds, (5, 13))
        self.assertEqual(regime.attacker_candidates, 2)
        self.assertEqual(regime.defender_candidates, 2)

    def test_unknown_regime_raises(self) -> None:
        with self.assertRaises(ValueError):
            load_regime("does-not-exist")


if __name__ == "__main__":
    unittest.main()
