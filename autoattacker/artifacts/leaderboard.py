from __future__ import annotations

from autoattacker.kernel.candidates import EvaluatedCandidate


def build_leaderboard(evaluations: list[EvaluatedCandidate]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in evaluations:
        fitness = (
            record.score["attacker_fitness"]
            if record.role in {"attacker", "system"}
            else record.score["defender_fitness"]
        )
        rows.append(
            {
                "role": record.role,
                "candidate_id": record.candidate_id,
                "opponent_id": record.opponent_id,
                "fitness": round(float(fitness), 6),
                "decision": record.decision.status,
            }
        )
    rows.sort(key=lambda item: item["fitness"], reverse=True)
    return rows
