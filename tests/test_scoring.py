from __future__ import annotations

import unittest

from autoattacker.kernel.baseline import default_budget
from autoattacker.kernel.candidates import MatchOutcome, TaskTrace
from autoattacker.kernel.score import score_match


class ScoringTests(unittest.TestCase):
    def test_score_formula_matches_doctrine(self) -> None:
        budget = default_budget(seed=11, num_tasks=2, max_turns=2)
        traces = [
            TaskTrace(
                task_id="t1",
                actions=["probe"],
                success=True,
                progress=1.0,
                hidden_objective_score=0.8,
                anomaly_peak=0.2,
                alerts=0,
                false_positives=0,
                turns_used=1,
                cost_used=1.0,
                notes="ok",
            )
        ]
        outcome = MatchOutcome(
            run_id="run-1",
            attacker_id="a1",
            defender_id="d1",
            adapter_name="toy_control",
            task_ids=["t1"],
            budget=budget,
            attack_success=0.75,
            stealth_score=0.5,
            defender_success=0.25,
            false_positive_penalty=0.1,
            cost_penalty=0.2,
            budget_used=2.0,
            stability=0.9,
            metrics={
                "attack_success": 0.75,
                "stealth_score": 0.5,
                "defender_success": 0.25,
                "false_positive_penalty": 0.1,
                "cost_penalty": 0.2,
                "budget_used": 2.0,
                "stability": 0.9,
            },
            traces=traces,
            notes="demo",
        )
        score = score_match(outcome)
        self.assertAlmostEqual(score.attacker_fitness, 1.05)
        self.assertAlmostEqual(score.defender_fitness, -0.05)
        self.assertIn("attack_success", score.system_report)


if __name__ == "__main__":
    unittest.main()
