# AUTOATTACKER

AUTOATTACKER is a compressed autonomous red/blue research loop.

Give the loop a bounded environment, let it generate attacker and defender challengers, evaluate them under a fixed comparable regime, keep/discard based on evidence, and repeat. You wake up to a log of experiments and a frontier that only advances when a challenger actually beats the incumbent.

Canonical loop:

`generate -> evaluate -> compare -> decide -> record -> repeat`

Advancement rule:

`Only promote when a challenger beats the incumbent under a frozen comparable regime and the result is artifact-backed.`

## How it works

The repo is intentionally small. The public product is not a framework. The public product is the loop.

The loop has a few surfaces that matter:

- `program.md` sets the doctrine.
- `autoattacker/kernel/regime.py` freezes the comparable regime.
- `python3 -m autoattacker.cli campaign --regime toy_default_v1` runs the canonical autonomous search loop.
- `runs/frontier.json` is the machine-owned frontier state.
- `runs/campaign_results.tsv` is the append-only experiment spine.
- `runs/campaign-*/` stores the comparison artifacts, per-seed evidence, and the morning-after campaign summary.

Everything else exists to support that loop.

## Quick start

```bash
uv sync
python3 -m unittest discover -s tests -v
python3 -m autoattacker.cli campaign --regime toy_default_v1 --iterations 1 --output-root runs --docs-root docs
python3 -m autoattacker.cli campaign --regime toy_default_v1 --iterations 4 --output-root runs --docs-root docs
python3 -m autoattacker.cli campaign --regime toy_default_v1 --iterations 3 --output-root runs --docs-root docs
python3 -m autoattacker.cli campaign --regime toy_shifted_smoke_v1 --iterations 2 --output-root runs/portability_shifted --docs-root docs
```

The first command verifies the repo. The next command is the smallest canonical smoke run. The longer default-regime commands show cumulative advancement on the same frontier. The shifted smoke is a tiny portability check, not a second product.

## Public repo shape

- `README.md`: main entrypoint
- `program.md`: doctrine surface
- `pyproject.toml`: packaging
- `autoattacker/`: kernel, adapter, artifact, and CLI code
- `tests/`: minimal verification suite
- `runs/`: checked-in machine-owned evidence

Generated markdown summaries can be written to `docs/` during local runs if you want them, but they are descriptive only. The authoritative state is in `runs/`.

## Design choices

- **Fixed comparable regime.** `toy_default_v1` freezes seeds, task count, turn budget, batch shape, and promotion thresholds.
- **Keep/discard semantics.** Every challenger ends as `promote`, `archive_interesting`, `discard`, or `crash` in the experiment spine.
- **Machine-owned frontier.** Only `promote` mutates `runs/frontier.json`.
- **Compressed mutable surface.** The main human-controlled file is `program.md`. The main active code surfaces are the regime, operators, selector, and the active toy adapter.
- **Cumulative evidence.** The checked-in `runs/` tree is meant to feel like “wake up to a log of experiments”, not like a pile of ad hoc notebooks.

## Current scope

This repo currently proves one thing well: a portable attacker/defender search loop can run autonomously on a toy-first bounded environment, emit evidence, and advance a frontier only on incumbent-relative improvement.

Current checked-in scope:

- `toy_default_v1`: the main proving-ground regime
- `toy_shifted_smoke_v1`: a tiny portability variant on the same adapter family
- autonomous campaign mode
- machine-owned frontier and ledger
- artifact-backed promotions

## Non-goals

- not a broad benchmark suite
- not a giant agent orchestration framework
- not a LinuxArena-specific system
- not real-world offensive tooling
- not markdown-as-control-plane after the loop is running

## Safety note

AUTOATTACKER is toy-first by design. The shipped environments are bounded, seeded, and local. The point is to study red/blue search loops under fixed evaluation budgets, not to build real-world offensive capability.

## Evidence surfaces

The canonical evidence to inspect is:

- `runs/frontier.json`
- `runs/campaign_results.tsv`
- `runs/campaign-*/campaign_summary.md`
- `runs/campaign-*/comparisons/**/*.json`
- `runs/*/batch_summary.json`

If you want the shortest possible read of the current checked-in state, start with the latest frontier and the latest campaign summary.
