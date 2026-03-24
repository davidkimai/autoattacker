from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    def test_run_command_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_root = root / "docs"
            docs_root.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "autoattacker.cli",
                    "run",
                    "--output-root",
                    str(root / "runs"),
                    "--docs-root",
                    str(docs_root),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("run_id=", result.stdout)
            match_files = list((root / "runs").glob("**/matches/*.json"))
            self.assertTrue(match_files)

    def test_end_to_end_run_emits_required_artifact_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_root = root / "docs"
            docs_root.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "autoattacker.cli",
                    "run",
                    "--output-root",
                    str(root / "runs"),
                    "--docs-root",
                    str(docs_root),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            artifact_path = next((root / "runs").glob("**/matches/*.json"))
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            for key in [
                "run_id",
                "attacker_id",
                "defender_id",
                "adapter_name",
                "task_ids",
                "budget",
                "metrics",
                "promotion_decision",
                "trace_refs",
            ]:
                self.assertIn(key, payload)


if __name__ == "__main__":
    unittest.main()
