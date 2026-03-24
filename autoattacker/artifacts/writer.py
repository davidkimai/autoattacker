from __future__ import annotations

from pathlib import Path

from autoattacker.artifacts.schema import BatchArtifact, RunArtifact
from autoattacker.utils.io import ensure_dir, write_json, write_text


def write_run_artifact(output_root: Path, artifact: RunArtifact) -> Path:
    batch_dir = ensure_dir(output_root / artifact.batch_id / "matches")
    artifact_path = batch_dir / f"{artifact.run_id}.json"
    write_json(artifact_path, artifact.to_dict())
    return artifact_path


def write_batch_artifact(output_root: Path, artifact: BatchArtifact) -> Path:
    batch_dir = ensure_dir(output_root / artifact.batch_id)
    artifact_path = batch_dir / "batch_summary.json"
    write_json(artifact_path, artifact.to_dict())
    return artifact_path


def write_batch_summary(output_root: Path, artifact: BatchArtifact) -> Path:
    batch_dir = ensure_dir(output_root / artifact.batch_id)
    summary_path = batch_dir / "summary.md"
    promoted = [record for record in artifact.promoted if record["role"] != "system"]
    lines = [
        f"# Batch {artifact.batch_id}",
        "",
        f"- Adapter: {artifact.adapter_name}",
        f"- Evaluations: {len(artifact.evaluations)}",
        f"- Promoted: {len(promoted)}",
        f"- Archived: {len(artifact.archived)}",
        f"- Discarded: {len(artifact.discarded)}",
        "",
        "## Leaderboard",
    ]
    for row in artifact.leaderboard:
        lines.append(
            f"- {row['role']} {row['candidate_id']} vs {row['opponent_id']}: fitness={row['fitness']:.3f} decision={row['decision']}"
        )
    write_text(summary_path, "\n".join(lines) + "\n")
    return summary_path
