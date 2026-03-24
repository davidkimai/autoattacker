# autoattacker

autoattacker: AI agents running attacker/defender research loops automatically under fixed-budget evaluations.

autoattacker is autoresearch for red-team / blue-team research.

The core move is simple. Give the loop a bounded attacker/defender environment, freeze the evaluation setup, let it generate new attacker and defender ideas, and only keep the ones that actually beat the current best under saved run evidence. You wake up to a log of experiments and a best-so-far set that moved for a reason.

## How it works

`generate -> evaluate -> compare -> decide -> record -> repeat`

The repo is intentionally small. In practice, a few files and surfaces matter most:

- `program.md`: the doctrine file. This is the main human-written surface and the first thing to point an agent at.
- `autoattacker/cli.py`: the command-line entrypoint. It runs search loops, writes evidence, and updates best-so-far state.
- `autoattacker/kernel/eval.py`: fixed evaluation setup definitions. `toy_default_v1` lives here, along with the tiny shifted smoke setup.
- `autoattacker/kernel/` and `autoattacker/adapters/toy_control/`: the small active code surface. This is where operators, scoring, selection, and the bounded toy environment live.
- `runs/frontier.json` and `runs/campaign_results.tsv`: state written by the loop. `frontier.json` holds the current best attacker and defender. `campaign_results.tsv` is the append-only experiment log.

The main evaluation setup is `toy_default_v1`. It freezes the adapter, seeds (`7`, `11`, `19`), task count (`4`), turn budget (`6`), and the number of new attacker and defender candidates tested each iteration (`3` per side). That keeps comparisons fair across search runs.

The keep/discard rule is also simple. Every new candidate ends in one of four outcomes: `promote`, `archive_interesting`, `discard`, or `crash`. Only `promote` changes the best-so-far set.

The shipped environments are toy-first and bounded. They are there to study the loop under controlled conditions, not to build real-world offensive capability.

## Quick start

Requirements: Python `3.11+` and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
python3 -m unittest discover -s tests -v
python3 -m autoattacker.cli campaign --eval toy_default_v1 --iterations 1
```

That is the smallest credible verify-and-run path. After it finishes, inspect `runs/frontier.json`, `runs/campaign_results.tsv`, and the newest `runs/campaign-*/campaign_summary.md`.

## Running the agent

Open Codex, Claude, or any similar coding agent in this repo and point it at `program.md`. A good first prompt is:

```text
Read program.md, runs/frontier.json, runs/campaign_results.tsv, and the latest runs/campaign-*/campaign_summary.md. Then run 1 search iteration under toy_default_v1, inspect the saved evidence, and tell me whether the current best changed.
```

`program.md` is basically a lightweight skill. It tells the agent what kind of loop it is operating, what surfaces are meant to change, and what counts as a real improvement.

### Working with the current best

Start with `runs/frontier.json`. That file is the source of truth for the current best attacker and defender.

Then read `runs/campaign_results.tsv`. That gives the agent the short history of what has already been tried, what got promoted, and what got discarded.

A useful follow-up prompt looks like this:

```text
Read program.md and the current best state in runs/frontier.json. Propose 1 focused operator or adapter-calibration change for toy_default_v1, run it under the same fixed evaluation setup, and summarize whether the new candidate beat the current best or should be kept as archive/discarded.
```

The canonical search run uses the main fixed evaluation setup:

```bash
python3 -m autoattacker.cli campaign --eval toy_default_v1 --iterations 4
```

Run it again on the same repo state if you want to see whether progress continues from the same best-so-far set:

```bash
python3 -m autoattacker.cli campaign --eval toy_default_v1 --iterations 3
```

There is also one tiny portability smoke on a shifted toy variant:

```bash
python3 -m autoattacker.cli campaign --eval toy_shifted_smoke_v1 --iterations 2 --output-root runs/portability_shifted
```

That shifted run is there as a small portability check. It is not a second benchmark program.

## Project structure

```text
README.md                         public entrypoint
program.md                        doctrine for the loop
autoattacker/cli.py               search-run entrypoint
autoattacker/kernel/eval.py       fixed evaluation setups
autoattacker/kernel/              operators, scoring, selection, summaries
autoattacker/adapters/toy_control/ bounded toy environments
runs/                             saved run evidence and best-so-far state
tests/                            verification
```

## Design choices

- **Fixed evaluation setup.** Search runs are only useful if comparisons stay comparable.
- **Keep/discard discipline.** Every new candidate is judged against the current best, then written down.
- **State written by the loop.** `runs/frontier.json` and `runs/campaign_results.tsv` are authoritative. Markdown summaries are there to help humans read the results.
- **Small mutable surface.** `program.md`, the operator code, the selector, and the toy adapter do most of the work.
- **Narrow scope.** The repo stays focused on one main evaluation setup, one tiny shifted smoke, autonomous search runs, and cumulative saved evidence.

## Platform support

The shipped environments are pure Python and local. You do not need a GPU, a cluster, or external services to run the loop.

macOS and Linux are the expected path. Windows may work with Python `3.11+`, but it has not been exercised in this repo.

## License

A standalone license file is not checked in yet. If you plan to reuse the code, check the repo state before assuming license terms.
