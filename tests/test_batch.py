from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class BatchTests(unittest.TestCase):
    def test_batch_mode_writes_summary_and_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_root = root / "docs"
            docs_root.mkdir(parents=True, exist_ok=True)
            ledger_path = docs_root / "RESEARCH_LEDGER.md"
            ledger_path.write_text("# Research Ledger\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "autoattacker.cli",
                    "batch",
                    "--attacker-candidates",
                    "2",
                    "--defender-candidates",
                    "2",
                    "--output-root",
                    str(root / "runs"),
                    "--docs-root",
                    str(docs_root),
                    "--update-ledger",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("batch_id=", result.stdout)
            summary_path = next((root / "runs").glob("**/batch_summary.json"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(summary["evaluations"]), 5)
            self.assertIn("Batch", ledger_path.read_text(encoding="utf-8"))
            match_files = list((root / "runs").glob("**/matches/*.json"))
            self.assertGreaterEqual(len(match_files), 5)


if __name__ == "__main__":
    unittest.main()
