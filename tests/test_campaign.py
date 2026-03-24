from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CampaignTests(unittest.TestCase):
    def test_campaign_emits_frontier_ledger_summary_and_match_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_root = root / "docs"
            docs_root.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "autoattacker.cli",
                    "campaign",
                    "--iterations",
                    "2",
                    "--output-root",
                    str(root / "runs"),
                    "--docs-root",
                    str(docs_root),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("search_run_id=", result.stdout)
            self.assertIn("evaluation_setup=toy_default_v1", result.stdout)
            frontier_path = root / "runs" / "frontier.json"
            ledger_path = root / "runs" / "campaign_results.tsv"
            self.assertTrue(frontier_path.exists())
            self.assertTrue(ledger_path.exists())
            frontier = json.loads(frontier_path.read_text(encoding="utf-8"))
            self.assertEqual(frontier["regime_id"], "toy_default_v1")
            ledger_lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreater(len(ledger_lines), 1)
            self.assertEqual(
                ledger_lines[0].split("\t")[:5],
                ["campaign_id", "iteration", "regime_id", "role", "incumbent_id"],
            )
            summary_paths = list((root / "runs").glob("campaign-*/campaign_summary.md"))
            self.assertTrue(summary_paths)
            self.assertTrue((docs_root / "00CURRENT_STATE.md").exists())
            self.assertTrue((docs_root / "RESEARCH_LEDGER.md").exists())
            batch_summaries = list((root / "runs").glob("**/batch_summary.json"))
            match_artifacts = list((root / "runs").glob("**/matches/*.json"))
            comparison_artifacts = list((root / "runs").glob("campaign-*/comparisons/**/*.json"))
            self.assertTrue(batch_summaries)
            self.assertTrue(match_artifacts)
            self.assertTrue(comparison_artifacts)


if __name__ == "__main__":
    unittest.main()
