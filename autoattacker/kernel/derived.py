from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from autoattacker.utils.io import write_text


def load_campaign_results(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_machine_derived_summaries(output_root: Path, docs_root: Path) -> dict[str, Path]:
    frontier_path = output_root / "frontier.json"
    ledger_path = output_root / "campaign_results.tsv"
    if not frontier_path.exists() or not ledger_path.exists():
        return {}

    frontier = json.loads(frontier_path.read_text(encoding="utf-8"))
    rows = load_campaign_results(ledger_path)
    state_path = docs_root / "00CURRENT_STATE.md"
    ledger_md_path = docs_root / "RESEARCH_LEDGER.md"
    write_text(state_path, build_current_state_markdown(frontier, rows, frontier_path, ledger_path))
    write_text(ledger_md_path, build_research_ledger_markdown(frontier, rows, frontier_path, ledger_path))
    return {"current_state": state_path, "research_ledger": ledger_md_path}


def build_current_state_markdown(
    frontier: dict[str, Any],
    rows: list[dict[str, str]],
    frontier_path: Path,
    ledger_path: Path,
) -> str:
    campaigns = _campaign_ids(rows)
    decisions = Counter(row["decision"] for row in rows)
    attacker = frontier["attackers"][0]
    defender = frontier["defenders"][0]
    recent_promotions = [row for row in rows if row["decision"] == "promote"][-5:]
    strongest_archived = _strongest_archived(rows)
    lines = [
        "# Current State",
        "",
        "## Snapshot",
        f"- Fixed evaluation setup: `{frontier['eval_id']}`",
        f"- Best-so-far state file: `{frontier_path}`",
        f"- Campaign ledger: `{ledger_path}`",
        f"- Search runs logged: `{len(campaigns)}`",
        f"- New-candidate rows: `{len(rows)}`",
        f"- Promotions: `{decisions.get('promote', 0)}`",
        f"- Archived: `{decisions.get('archive_interesting', 0)}`",
        f"- Discarded: `{decisions.get('discard', 0)}`",
        f"- Crashes: `{decisions.get('crash', 0)}`",
        "",
        "## Active Best-So-Far Set",
        f"- Current best attacker: `{attacker['candidate_id']}` fitness `{attacker['fitness']:.6f}` attack_success `{attacker['system_report']['attack_success']:.6f}` attack_progress `{attacker['system_report']['attack_progress']:.6f}`",
        f"- Current best defender: `{defender['candidate_id']}` fitness `{defender['fitness']:.6f}` defender_success `{defender['system_report']['defender_success']:.6f}` false_positive_penalty `{defender['system_report']['false_positive_penalty']:.6f}`",
        "",
        "## Recent Promotions",
    ]
    if recent_promotions:
        for row in recent_promotions:
            lines.append(
                f"- campaign `{row['campaign_id']}` iter `{row['iteration']}` {row['role']} `{row['current_best_id']}` -> `{row['new_candidate_id']}` delta `{row['delta_vs_current_best']}`"
            )
    else:
        lines.append("- No promotions logged yet.")
    lines.extend(["", "## Strongest Next Branch"])
    if strongest_archived is None:
        lines.append("- No archived branch currently outranks the active operator surface.")
    else:
        lines.append(
            f"- Revisit {strongest_archived['role']} `{strongest_archived['new_candidate_id']}` from search run `{strongest_archived['campaign_id']}`; delta `{strongest_archived['delta_vs_current_best']}`, novelty `{strongest_archived['novelty_score']}`."
        )
    return "\n".join(lines) + "\n"


def build_research_ledger_markdown(
    frontier: dict[str, Any],
    rows: list[dict[str, str]],
    frontier_path: Path,
    ledger_path: Path,
) -> str:
    campaigns = _group_by_campaign(rows)
    lines = [
        "# Research Ledger",
        "",
        "Machine-derived from `frontier.json` and `campaign_results.tsv`.",
        "",
        f"- Best-so-far state file: `{frontier_path}`",
        f"- Campaign ledger: `{ledger_path}`",
        f"- Current best attacker: `{frontier['attackers'][0]['candidate_id']}`",
        f"- Current best defender: `{frontier['defenders'][0]['candidate_id']}`",
    ]
    for campaign_id in sorted(campaigns):
        campaign_rows = campaigns[campaign_id]
        decision_counts = Counter(row["decision"] for row in campaign_rows)
        promotions = [row for row in campaign_rows if row["decision"] == "promote"]
        archived = [row for row in campaign_rows if row["decision"] == "archive_interesting"]
        lines.extend([
            "",
            f"## {campaign_id}",
            "",
            f"- New-candidate rows: `{len(campaign_rows)}`",
            f"- Promotions: `{decision_counts.get('promote', 0)}`",
            f"- Archived: `{decision_counts.get('archive_interesting', 0)}`",
            f"- Discarded: `{decision_counts.get('discard', 0)}`",
            f"- Crashes: `{decision_counts.get('crash', 0)}`",
            "",
            "### Best-So-Far Changes",
        ])
        if promotions:
            for row in promotions:
                lines.append(
                    f"- iter `{row['iteration']}` {row['role']} `{row['current_best_id']}` -> `{row['new_candidate_id']}` delta `{row['delta_vs_current_best']}`"
                )
        else:
            lines.append("- No best-so-far changes.")
        lines.extend(["", "### Strongest Archived"])
        if archived:
            best = max(archived, key=lambda row: float(row["delta_vs_current_best"]))
            lines.append(
                f"- {best['role']} `{best['new_candidate_id']}` delta `{best['delta_vs_current_best']}` novelty `{best['novelty_score']}`"
            )
        else:
            lines.append("- None.")
    return "\n".join(lines) + "\n"


def _campaign_ids(rows: list[dict[str, str]]) -> list[str]:
    return sorted({row["campaign_id"] for row in rows})


def _group_by_campaign(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["campaign_id"]].append(row)
    return grouped


def _strongest_archived(rows: list[dict[str, str]]) -> dict[str, str] | None:
    archived = [row for row in rows if row["decision"] == "archive_interesting"]
    if not archived:
        return None
    return max(archived, key=lambda row: float(row["delta_vs_current_best"]))
