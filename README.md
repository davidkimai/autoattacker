# autoattacker

autoattacker: AI agents running attacker/defender research loops automatically under fixed-budget evaluations.

autoattacker is autoresearch for red-team / blue-team research.

The idea is simple: give the loop a small bounded environment, let it propose new attacker and defender ideas, evaluate them under the same fixed evaluation setup every time, keep or discard based on saved run evidence, and repeat. You wake up to a log of experiments and a best-so-far set that only changes when a new candidate actually wins.

Canonical loop:

`generate -> evaluate -> compare -> decide -> record -> repeat`

Advancement rule:

`Only promote when a new candidate beats the current best under the same fixed evaluation setup and the result is backed by saved run evidence.`

## How it works

The repo is deliberately small. The product is not a framework. The product is the loop.

The main public surfaces are:

- `program.md`: the doctrine file
- `python3 -m autoattacker.cli campaign --regime toy_default_v1`: the canonical search-run command
- `runs/frontier.json`: the best-so-far set written by the loop
- `runs/campaign_results.tsv`: the append-only log of keep/discard decisions
- `runs/campaign-*/`: per-search-run summaries, saved comparisons, and per-seed evidence

The `--regime` flag is the code name for the fixed evaluation setup. For the main setup, `toy_default_v1` freezes the seeds, task count, turn budget, batch shape, and promotion threshold so runs stay comparable.

## Keep / discard

Each new candidate ends in one of four outcomes:

- `promote`: it beats the current best and becomes the new current best
- `archive_interesting`: it did not win, but the result is worth keeping as evidence
- `discard`: it clearly lost
- `crash`: the run failed and is recorded explicitly

Only `promote` changes `runs/frontier.json`.

## Files that matter

- `README.md`: public entrypoint
- `program.md`: doctrine
- `autoattacker/cli.py`: command-line entrypoint
- `autoattacker/kernel/`: candidate generation, scoring, selection, and state updates
- `autoattacker/adapters/toy_control/`: the toy-first bounded environment
- `tests/`: verification
- `runs/`: checked-in evidence

## Quick start

```bash
uv sync
python3 -m unittest discover -s tests -v
python3 -m autoattacker.cli campaign --regime toy_default_v1 --iterations 1
```

That is the smallest credible verify-and-run path.

## Canonical search runs

```bash
python3 -m autoattacker.cli campaign --regime toy_default_v1 --iterations 4
python3 -m autoattacker.cli campaign --regime toy_default_v1 --iterations 3
python3 -m autoattacker.cli campaign --regime toy_shifted_smoke_v1 --iterations 2 --output-root runs/portability_shifted
```

Use the first long run to advance the main best-so-far set. Use the second to check whether improvement continues on the same state. Use the shifted smoke only as a tiny portability check, not as a second product.

## Evidence to inspect

Start here:

- `runs/frontier.json`
- `runs/campaign_results.tsv`
- `runs/campaign-*/campaign_summary.md`
- `runs/campaign-*/comparisons/**/*.json`
- `runs/*/batch_summary.json`

If you only read two things, read `runs/frontier.json` and the latest `runs/campaign-*/campaign_summary.md`.

## Design choices

- **Fixed evaluation setup.** `toy_default_v1` holds the comparison surface steady.
- **Keep/discard discipline.** Every result is written down.
- **State written by the loop.** The best-so-far set and experiment log are updated by the code, not by hand.
- **Small mutable surface.** `program.md` plus a small amount of kernel and adapter code drive the system.
- **Cumulative evidence.** The checked-in `runs/` tree is meant to feel like “wake up to a log of experiments”.

## Current scope

Current checked-in scope:

- one main fixed evaluation setup: `toy_default_v1`
- one tiny portability validation setup: `toy_shifted_smoke_v1`
- autonomous search runs
- saved run evidence
- keep/discard/promote decisions backed by those saved runs

## Non-goals

- broad benchmark coverage
- large orchestration frameworks
- LinuxArena-specific infrastructure
- real-world offensive tooling
- markdown as the control plane after the loop is running

## Safety note

autoattacker is toy-first by design. The shipped environments are bounded, seeded, and local. The goal is to study attacker/defender research loops under fixed evaluation setups, not to build real-world offensive capability.

## Minimal public structure

```text
README.md
program.md
pyproject.toml
autoattacker/
tests/
runs/
```
