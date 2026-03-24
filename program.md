# AUTOATTACKER Program

## Objective
Implement the canonical autonomous red/blue research loop:

`objective -> generate -> evaluate -> compare -> decide -> record -> repeat`

## Frozen Regime Doctrine
- The main proving ground is `toy_default_v1`.
- The tiny portability check is `toy_shifted_smoke_v1`.
- Same candidate pairing plus same seed must produce the same result.
- Comparisons are incumbent-relative and artifact-backed.

## Campaign Doctrine
- The canonical command is `python3 -m autoattacker.cli campaign --regime toy_default_v1`.
- Each iteration evaluates a bounded challenger set against the current frontier pair across the frozen seed set.
- The machine-owned state is `runs/frontier.json` plus `runs/campaign_results.tsv`.

## Advancement Doctrine
- Only `promote` changes the frontier.
- A promotion replaces the incumbent for that role.
- `archive_interesting`, `discard`, and `crash` never change the frontier.
- Failed evaluations must be recorded explicitly.

## Operator Doctrine
- Search the current frontier, not the whole architecture.
- Keep the mutable surface small.
- Prefer a few high-signal challenger recipes over broad random search.
- Tune operators against the actual incumbent attacker and defender surfaces.

## Memory Doctrine
- `runs/` is authoritative.
- Generated markdown is descriptive, not the control plane.
- Keep the public repo minimal and cumulative.
