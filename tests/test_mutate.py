from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from autoattacker.kernel.baseline import load_baseline_attacker, load_baseline_defender
from autoattacker.kernel.candidates import CandidateLineage, DefenderCandidate
from autoattacker.kernel.mutate import generate_attacker_candidates, generate_defender_candidates


class MutationTests(unittest.TestCase):
    def test_guided_generators_use_history_and_context(self) -> None:
        attacker = load_baseline_attacker()
        defender = load_baseline_defender()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            comparison_dir = root / "campaign-1" / "comparisons" / "iter-001"
            comparison_dir.mkdir(parents=True, exist_ok=True)
            comparison_path = comparison_dir / "attacker-guided.json"
            comparison_path.write_text(
                json.dumps(
                    {
                        "incumbent": {"parameters": attacker.parameters},
                        "challenger": {
                            "parameters": {"aggression": 0.51, "stealth": 0.50, "persistence": 0.42}
                        },
                    }
                ),
                encoding="utf-8",
            )
            ledger_path = root / "campaign_results.tsv"
            ledger_path.write_text(
                "\t".join(
                    [
                        "campaign_id",
                        "iteration",
                        "regime_id",
                        "role",
                        "incumbent_id",
                        "challenger_id",
                        "challenger_lineage",
                        "scalar_fitness",
                        "delta_vs_incumbent",
                        "decision",
                        "novelty_score",
                        "artifact_path",
                        "status_note",
                    ]
                )
                + "\n"
                + "\t".join(
                    [
                        "campaign-1",
                        "1",
                        "toy_default_v1",
                        "attacker",
                        attacker.candidate_id,
                        "attacker-guided",
                        "{}",
                        "-0.5",
                        "0.08",
                        "promote",
                        "0.06",
                        str(comparison_path),
                        "guided win",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            attacker_candidates = generate_attacker_candidates(
                attacker,
                3,
                7,
                "batch-guided",
                defender=defender,
                ledger_path=ledger_path,
            )
            self.assertEqual(attacker_candidates[0].lineage.mutation_note, "follow positive historical delta")
            self.assertGreater(attacker_candidates[0].parameters["stealth"], attacker.parameters["stealth"])
            hardened_defender = DefenderCandidate(
                candidate_id="defender-hardened",
                name="Hardened Defender",
                description="scratch defender",
                parameters={"sensitivity": 0.57, "hardening": 0.74, "response_speed": 0.66},
                lineage=CandidateLineage(parent_id=defender.candidate_id, generation=1, mutation_note="scratch", batch_id="scratch"),
                tags=["scratch"],
            )
            hardened_candidates = generate_attacker_candidates(
                attacker,
                3,
                11,
                "batch-hardened",
                defender=hardened_defender,
                ledger_path=ledger_path,
            )
            self.assertLess(hardened_candidates[1].parameters["stealth"], attacker.parameters["stealth"])
            self.assertGreater(hardened_candidates[1].parameters["aggression"], attacker.parameters["aggression"])
            defender_candidates = generate_defender_candidates(
                defender,
                3,
                7,
                "batch-guided",
                attacker=attacker,
                ledger_path=ledger_path,
            )
            self.assertEqual(defender_candidates[1].lineage.mutation_note, "counter incumbent attacker surface")


if __name__ == "__main__":
    unittest.main()
