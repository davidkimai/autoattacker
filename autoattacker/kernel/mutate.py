from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from autoattacker.kernel.candidates import (
    ATTACKER_KEYS,
    DEFENDER_KEYS,
    AttackerCandidate,
    CandidateLineage,
    DefenderCandidate,
)
from autoattacker.utils.seeds import rng_for, short_hash


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def _apply_adjustments(parameters: dict[str, float], adjustments: dict[str, float]) -> dict[str, float]:
    return {key: _clamp(parameters[key] + adjustments.get(key, 0.0)) for key in parameters}


def _artifact_path(path_text: str) -> Path:
    return Path(path_text)


def _load_weighted_direction(role: str, keys: tuple[str, ...], ledger_path: Path | None) -> dict[str, float] | None:
    if ledger_path is None or not ledger_path.exists():
        return None

    directions: list[tuple[float, dict[str, float]]] = []
    with ledger_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row.get("role") != role:
                continue
            try:
                delta = float(row.get("delta_vs_incumbent", "nan"))
            except ValueError:
                continue
            if delta <= 0.0:
                continue
            artifact = _artifact_path(row.get("artifact_path", ""))
            if not artifact.exists():
                continue
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            incumbent = dict(payload.get("incumbent", {}).get("parameters", {}))
            challenger = dict(payload.get("challenger", {}).get("parameters", {}))
            direction = {
                key: challenger.get(key, 0.0) - incumbent.get(key, 0.0)
                for key in keys
            }
            directions.append((delta, direction))

    if not directions:
        return None

    top_directions = sorted(directions, key=lambda item: item[0], reverse=True)[:4]
    total_weight = sum(weight for weight, _ in top_directions)
    if total_weight <= 0:
        return None
    return {
        key: sum(weight * direction[key] for weight, direction in top_directions) / total_weight
        for key in keys
    }


def _build_attacker_candidate(
    *,
    base: AttackerCandidate,
    parameters: dict[str, float],
    batch_id: str,
    index: int,
    strategy: str,
    mutation_note: str,
    tags: list[str],
) -> AttackerCandidate:
    candidate_id = f"attacker-{short_hash(batch_id, base.candidate_id, index, strategy)}"
    return AttackerCandidate(
        candidate_id=candidate_id,
        name=f"Attacker {strategy.replace('_', ' ').title()}",
        description=f"{strategy} mutation of {base.candidate_id}.",
        parameters=parameters,
        lineage=CandidateLineage(
            parent_id=base.candidate_id,
            generation=base.lineage.generation + 1,
            mutation_note=mutation_note,
            batch_id=batch_id,
        ),
        tags=["mutated", strategy, *tags],
    )


def _build_defender_candidate(
    *,
    base: DefenderCandidate,
    parameters: dict[str, float],
    batch_id: str,
    index: int,
    strategy: str,
    mutation_note: str,
    tags: list[str],
) -> DefenderCandidate:
    candidate_id = f"defender-{short_hash(batch_id, base.candidate_id, index, strategy)}"
    return DefenderCandidate(
        candidate_id=candidate_id,
        name=f"Defender {strategy.replace('_', ' ').title()}",
        description=f"{strategy} mutation of {base.candidate_id}.",
        parameters=parameters,
        lineage=CandidateLineage(
            parent_id=base.candidate_id,
            generation=base.lineage.generation + 1,
            mutation_note=mutation_note,
            batch_id=batch_id,
        ),
        tags=["mutated", strategy, *tags],
    )


def _guided_attacker(
    base: AttackerCandidate,
    defender: DefenderCandidate | None,
    seed: int,
    index: int,
    batch_id: str,
    ledger_path: Path | None,
) -> AttackerCandidate:
    rng = rng_for("attacker-guided", seed, base.candidate_id, index)
    defender_params = defender.parameters if defender is not None else {"sensitivity": 0.56, "hardening": 0.50, "response_speed": 0.54}
    direction = _load_weighted_direction("attacker", ATTACKER_KEYS, ledger_path) or {
        "aggression": -0.05,
        "stealth": 0.03,
        "persistence": -0.07,
    }
    adjustments = {key: direction.get(key, 0.0) * 0.9 + rng.uniform(-0.015, 0.015) for key in ATTACKER_KEYS}
    if defender_params["hardening"] >= 0.68:
        adjustments["aggression"] += 0.02 + max(0.0, defender_params["hardening"] - 0.68) * 0.15
        adjustments["persistence"] += max(0.0, 0.40 - base.parameters["persistence"]) * 0.70
        adjustments["stealth"] -= 0.05 + max(0.0, defender_params["response_speed"] - 0.62) * 0.25
    parameters = _apply_adjustments(base.parameters, adjustments)
    return _build_attacker_candidate(
        base=base,
        parameters=parameters,
        batch_id=batch_id,
        index=index,
        strategy="guided_delta",
        mutation_note="follow positive historical delta",
        tags=["guided"],
    )


def _counter_defender_attacker(
    base: AttackerCandidate,
    defender: DefenderCandidate | None,
    seed: int,
    index: int,
    batch_id: str,
) -> AttackerCandidate:
    rng = rng_for("attacker-counter", seed, base.candidate_id, index)
    defender_params = defender.parameters if defender is not None else {"sensitivity": 0.56, "hardening": 0.50, "response_speed": 0.54}
    adjustments = {
        "aggression": 0.02 + max(0.0, defender_params["hardening"] - 0.65) * 0.35 + rng.uniform(-0.01, 0.01),
        "stealth": -(0.07 + max(0.0, defender_params["response_speed"] - 0.60) * 0.32 + rng.uniform(0.0, 0.01)),
        "persistence": max(0.0, 0.40 - base.parameters["persistence"]) * 0.90 + rng.uniform(-0.01, 0.01),
    }
    parameters = _apply_adjustments(base.parameters, adjustments)
    return _build_attacker_candidate(
        base=base,
        parameters=parameters,
        batch_id=batch_id,
        index=index,
        strategy="counter_defender",
        mutation_note="counter incumbent defender surface",
        tags=["counter", "defender-aware"],
    )


def _finisher_attacker(base: AttackerCandidate, seed: int, index: int, batch_id: str) -> AttackerCandidate:
    rng = rng_for("attacker-finisher", seed, base.candidate_id, index)
    adjustments = {
        "aggression": rng.uniform(0.02, 0.05),
        "stealth": -rng.uniform(0.06, 0.10),
        "persistence": rng.uniform(0.0, 0.03),
    }
    parameters = _apply_adjustments(base.parameters, adjustments)
    return _build_attacker_candidate(
        base=base,
        parameters=parameters,
        batch_id=batch_id,
        index=index,
        strategy="finisher",
        mutation_note="raise conversion pressure while keeping heat bounded",
        tags=["conversion"],
    )


def _guided_defender(
    base: DefenderCandidate,
    seed: int,
    index: int,
    batch_id: str,
    ledger_path: Path | None,
) -> DefenderCandidate:
    rng = rng_for("defender-guided", seed, base.candidate_id, index)
    direction = _load_weighted_direction("defender", DEFENDER_KEYS, ledger_path) or {
        "sensitivity": 0.01,
        "hardening": 0.05,
        "response_speed": 0.04,
    }
    adjustments = {
        key: direction.get(key, 0.0) * 0.9 + rng.uniform(-0.012, 0.012)
        for key in DEFENDER_KEYS
    }
    parameters = _apply_adjustments(base.parameters, adjustments)
    return _build_defender_candidate(
        base=base,
        parameters=parameters,
        batch_id=batch_id,
        index=index,
        strategy="guided_delta",
        mutation_note="follow positive historical delta",
        tags=["guided"],
    )


def _counter_attacker_defender(
    base: DefenderCandidate,
    attacker: AttackerCandidate | None,
    seed: int,
    index: int,
    batch_id: str,
) -> DefenderCandidate:
    rng = rng_for("defender-counter", seed, base.candidate_id, index)
    attacker_params = attacker.parameters if attacker is not None else {"aggression": 0.58, "stealth": 0.47, "persistence": 0.55}
    adjustments = {
        "sensitivity": 0.02 + max(0.0, attacker_params["stealth"] - 0.48) * 0.40 + rng.uniform(-0.01, 0.01),
        "hardening": 0.02 + max(0.0, attacker_params["aggression"] - 0.50) * 0.30 + rng.uniform(-0.01, 0.01),
        "response_speed": 0.02 + max(0.0, attacker_params["persistence"] - 0.40) * 0.35 + rng.uniform(-0.01, 0.01),
    }
    parameters = _apply_adjustments(base.parameters, adjustments)
    return _build_defender_candidate(
        base=base,
        parameters=parameters,
        batch_id=batch_id,
        index=index,
        strategy="counter_attacker",
        mutation_note="counter incumbent attacker surface",
        tags=["counter", "attacker-aware"],
    )


def _trim_false_positives_defender(base: DefenderCandidate, seed: int, index: int, batch_id: str) -> DefenderCandidate:
    rng = rng_for("defender-trim-fp", seed, base.candidate_id, index)
    adjustments = {
        "sensitivity": -rng.uniform(0.01, 0.03),
        "hardening": rng.uniform(0.03, 0.06),
        "response_speed": rng.uniform(0.02, 0.05),
    }
    parameters = _apply_adjustments(base.parameters, adjustments)
    return _build_defender_candidate(
        base=base,
        parameters=parameters,
        batch_id=batch_id,
        index=index,
        strategy="trim_false_positives",
        mutation_note="trade excess sensitivity for harder blocking",
        tags=["fp-trim"],
    )


def mutate_attacker(base: AttackerCandidate, seed: int, index: int, batch_id: str) -> AttackerCandidate:
    rng = rng_for("attacker-mutation", seed, base.candidate_id, index)
    parameters = dict(base.parameters)
    primary = rng.choice(ATTACKER_KEYS)
    secondary = rng.choice(tuple(key for key in ATTACKER_KEYS if key != primary))
    parameters[primary] = _clamp(parameters[primary] + rng.choice((-1.0, 1.0)) * rng.uniform(0.05, 0.16))
    parameters[secondary] = _clamp(parameters[secondary] + rng.choice((-1.0, 1.0)) * rng.uniform(0.02, 0.08))
    return _build_attacker_candidate(
        base=base,
        parameters=parameters,
        batch_id=batch_id,
        index=index,
        strategy="random_explore",
        mutation_note=f"mutate {primary}/{secondary}",
        tags=[primary, secondary],
    )


def mutate_defender(base: DefenderCandidate, seed: int, index: int, batch_id: str) -> DefenderCandidate:
    rng = rng_for("defender-mutation", seed, base.candidate_id, index)
    parameters = dict(base.parameters)
    primary = rng.choice(DEFENDER_KEYS)
    secondary = rng.choice(tuple(key for key in DEFENDER_KEYS if key != primary))
    parameters[primary] = _clamp(parameters[primary] + rng.choice((-1.0, 1.0)) * rng.uniform(0.05, 0.16))
    parameters[secondary] = _clamp(parameters[secondary] + rng.choice((-1.0, 1.0)) * rng.uniform(0.02, 0.08))
    return _build_defender_candidate(
        base=base,
        parameters=parameters,
        batch_id=batch_id,
        index=index,
        strategy="random_explore",
        mutation_note=f"mutate {primary}/{secondary}",
        tags=[primary, secondary],
    )


def generate_attacker_candidates(
    base: AttackerCandidate,
    count: int,
    seed: int,
    batch_id: str,
    *,
    defender: DefenderCandidate | None = None,
    ledger_path: str | Path | None = None,
) -> list[AttackerCandidate]:
    recipes = [
        lambda index: _guided_attacker(base, defender, seed, index, batch_id, Path(ledger_path) if ledger_path is not None else None),
        lambda index: _counter_defender_attacker(base, defender, seed, index, batch_id),
        lambda index: _finisher_attacker(base, seed, index, batch_id),
    ]
    candidates: list[AttackerCandidate] = []
    for index in range(count):
        if index < len(recipes):
            candidates.append(recipes[index](index))
        else:
            candidates.append(mutate_attacker(base, seed, index, batch_id))
    return candidates


def generate_defender_candidates(
    base: DefenderCandidate,
    count: int,
    seed: int,
    batch_id: str,
    *,
    attacker: AttackerCandidate | None = None,
    ledger_path: str | Path | None = None,
) -> list[DefenderCandidate]:
    recipes = [
        lambda index: _guided_defender(base, seed, index, batch_id, Path(ledger_path) if ledger_path is not None else None),
        lambda index: _counter_attacker_defender(base, attacker, seed, index, batch_id),
        lambda index: _trim_false_positives_defender(base, seed, index, batch_id),
    ]
    candidates: list[DefenderCandidate] = []
    for index in range(count):
        if index < len(recipes):
            candidates.append(recipes[index](index))
        else:
            candidates.append(mutate_defender(base, seed, index, batch_id))
    return candidates
