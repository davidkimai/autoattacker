from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


def _git_value(args: list[str], cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def capture_reproducibility(*, cwd: Path, argv: list[str], seed: int) -> dict[str, Any]:
    return {
        "cwd": str(cwd.resolve()),
        "argv": argv,
        "seed": seed,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "git_commit": _git_value(["rev-parse", "--short", "HEAD"], cwd),
        "git_branch": _git_value(["branch", "--show-current"], cwd),
        "git_dirty": bool(_git_value(["status", "--short"], cwd)),
    }
