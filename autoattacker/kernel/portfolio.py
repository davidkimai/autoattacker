from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from autoattacker.kernel.candidates import (
    AttackerCandidate,
    CandidateBase,
    CandidateLineage,
    DefenderCandidate,
)
from autoattacker.kernel.score import ScoreBreakdown
from autoattacker.utils.io import write_json

FRONTIER_STATE_VERSION = "1"


@dataclass(slots=True)
class FrontierEntry:
    role: str
    candidate_id: str
    fitness: float
    parameters: dict[str, float]
    lineage: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class Frontier:
    attackers: list[FrontierEntry] = field(default_factory=list)
    defenders: list[FrontierEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "attackers": [entry.to_dict() for entry in self.attackers],
            "defenders": [entry.to_dict() for entry in self.defenders],
        }


@dataclass(slots=True)
class FrontierStateEntry:
    role: str
    candidate_id: str
    fitness: float
    candidate: dict[str, object]
    system_report: dict[str, float]
    artifact_ref: str
    batch_ids: list[str]
    updated_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class FrontierState:
    version: str
    regime_id: str
    updated_at: str
    comparator: dict[str, object]
    attackers: list[FrontierStateEntry] = field(default_factory=list)
    defenders: list[FrontierStateEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "regime_id": self.regime_id,
            "updated_at": self.updated_at,
            "comparator": dict(self.comparator),
            "attackers": [entry.to_dict() for entry in self.attackers],
            "defenders": [entry.to_dict() for entry in self.defenders],
        }


def _entry(role: str, candidate: CandidateBase, score: ScoreBreakdown) -> FrontierEntry:
    fitness = score.attacker_fitness if role == "attacker" else score.defender_fitness
    return FrontierEntry(
        role=role,
        candidate_id=candidate.candidate_id,
        fitness=round(fitness, 6),
        parameters=dict(candidate.parameters),
        lineage=candidate.lineage.to_dict(),
    )


def _state_entry(
    *,
    role: str,
    candidate: AttackerCandidate | DefenderCandidate,
    score: ScoreBreakdown,
    artifact_ref: str,
    batch_ids: list[str],
    updated_at: str,
) -> FrontierStateEntry:
    fitness = score.attacker_fitness if role == "attacker" else score.defender_fitness
    return FrontierStateEntry(
        role=role,
        candidate_id=candidate.candidate_id,
        fitness=round(fitness, 6),
        candidate=candidate.to_dict(),
        system_report={key: round(value, 6) for key, value in score.system_report.items()},
        artifact_ref=artifact_ref,
        batch_ids=list(batch_ids),
        updated_at=updated_at,
    )


def seed_frontier(
    attacker: AttackerCandidate,
    defender: DefenderCandidate,
    baseline_score: ScoreBreakdown,
) -> Frontier:
    return Frontier(
        attackers=[_entry("attacker", attacker, baseline_score)],
        defenders=[_entry("defender", defender, baseline_score)],
    )


def frontier_candidates(frontier: Frontier, role: str, lookup: dict[str, CandidateBase]) -> list[CandidateBase]:
    entries = frontier.attackers if role == "attacker" else frontier.defenders
    return [lookup[entry.candidate_id] for entry in entries if entry.candidate_id in lookup]


def update_frontier(
    frontier: Frontier,
    *,
    role: str,
    candidate: AttackerCandidate | DefenderCandidate,
    score: ScoreBreakdown,
    max_size: int = 3,
) -> None:
    entries = frontier.attackers if role == "attacker" else frontier.defenders
    incumbent = _entry(role, candidate, score)
    retained = [entry for entry in entries if entry.candidate_id != candidate.candidate_id]
    retained.sort(key=lambda item: item.fitness, reverse=True)
    entries[:] = [incumbent, *retained[: max(0, max_size - 1)]]


def build_frontier_state(
    *,
    regime_id: str,
    updated_at: str,
    comparator: dict[str, object],
    attacker: AttackerCandidate,
    attacker_score: ScoreBreakdown,
    attacker_artifact_ref: str,
    attacker_batch_ids: list[str],
    defender: DefenderCandidate,
    defender_score: ScoreBreakdown,
    defender_artifact_ref: str,
    defender_batch_ids: list[str],
) -> FrontierState:
    return FrontierState(
        version=FRONTIER_STATE_VERSION,
        regime_id=regime_id,
        updated_at=updated_at,
        comparator=dict(comparator),
        attackers=[
            _state_entry(
                role="attacker",
                candidate=attacker,
                score=attacker_score,
                artifact_ref=attacker_artifact_ref,
                batch_ids=attacker_batch_ids,
                updated_at=updated_at,
            )
        ],
        defenders=[
            _state_entry(
                role="defender",
                candidate=defender,
                score=defender_score,
                artifact_ref=defender_artifact_ref,
                batch_ids=defender_batch_ids,
                updated_at=updated_at,
            )
        ],
    )


def frontier_state_candidates(state: FrontierState, role: str) -> list[AttackerCandidate | DefenderCandidate]:
    entries = state.attackers if role == "attacker" else state.defenders
    return [_candidate_from_payload(entry.candidate) for entry in entries]


def frontier_incumbent(state: FrontierState, role: str) -> AttackerCandidate | DefenderCandidate:
    entries = frontier_state_candidates(state, role)
    if not entries:
        raise ValueError(f"missing frontier entry for role {role}")
    return entries[0]


def update_frontier_state(
    state: FrontierState,
    *,
    role: str,
    candidate: AttackerCandidate | DefenderCandidate,
    score: ScoreBreakdown,
    artifact_ref: str,
    batch_ids: list[str],
    updated_at: str,
    max_size: int,
) -> None:
    entries = state.attackers if role == "attacker" else state.defenders
    incumbent = _state_entry(
        role=role,
        candidate=candidate,
        score=score,
        artifact_ref=artifact_ref,
        batch_ids=batch_ids,
        updated_at=updated_at,
    )
    retained = [entry for entry in entries if entry.candidate_id != candidate.candidate_id]
    retained.sort(key=lambda item: item.fitness, reverse=True)
    entries[:] = [incumbent, *retained[: max(0, max_size - 1)]]
    state.updated_at = updated_at


def load_frontier_state(path: Path) -> FrontierState | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return FrontierState(
        version=str(payload["version"]),
        regime_id=str(payload["regime_id"]),
        updated_at=str(payload["updated_at"]),
        comparator=dict(payload.get("comparator", {})),
        attackers=[_state_entry_from_dict(entry) for entry in payload.get("attackers", [])],
        defenders=[_state_entry_from_dict(entry) for entry in payload.get("defenders", [])],
    )


def persist_frontier_state(path: Path, state: FrontierState) -> Path:
    write_json(path, state.to_dict())
    return path


def _candidate_from_payload(payload: dict[str, Any]) -> AttackerCandidate | DefenderCandidate:
    lineage = CandidateLineage(**dict(payload.get("lineage", {})))
    common = {
        "candidate_id": str(payload["candidate_id"]),
        "name": str(payload["name"]),
        "description": str(payload["description"]),
        "parameters": dict(payload["parameters"]),
        "lineage": lineage,
        "notes": list(payload.get("notes", [])),
        "tags": list(payload.get("tags", [])),
    }
    role = payload.get("role")
    if role == "attacker":
        return AttackerCandidate(**common)
    if role == "defender":
        return DefenderCandidate(**common)
    raise ValueError(f"unknown candidate role {role}")


def _state_entry_from_dict(payload: dict[str, Any]) -> FrontierStateEntry:
    return FrontierStateEntry(
        role=str(payload["role"]),
        candidate_id=str(payload["candidate_id"]),
        fitness=float(payload["fitness"]),
        candidate=dict(payload["candidate"]),
        system_report={key: float(value) for key, value in dict(payload.get("system_report", {})).items()},
        artifact_ref=str(payload["artifact_ref"]),
        batch_ids=[str(batch_id) for batch_id in payload.get("batch_ids", [])],
        updated_at=str(payload["updated_at"]),
    )
