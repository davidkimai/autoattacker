from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_VERSION = "0.1.0"


@dataclass(slots=True)
class RunArtifact:
    schema_version: str
    created_at: str
    batch_id: str
    run_id: str
    attacker_id: str
    defender_id: str
    attacker_lineage: dict[str, Any]
    defender_lineage: dict[str, Any]
    adapter_name: str
    task_ids: list[str]
    config: dict[str, Any]
    budget: dict[str, Any]
    metrics: dict[str, float]
    outcome: dict[str, Any]
    score: dict[str, Any]
    promotion_decision: dict[str, Any]
    trace_refs: list[str]
    reproducibility: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BatchArtifact:
    schema_version: str
    created_at: str
    batch_id: str
    adapter_name: str
    budget: dict[str, Any]
    frontier: dict[str, Any]
    evaluations: list[dict[str, Any]]
    promoted: list[dict[str, Any]]
    archived: list[dict[str, Any]]
    discarded: list[dict[str, Any]]
    leaderboard: list[dict[str, Any]]
    reproducibility: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
