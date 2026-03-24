# autoattacker

autoattacker: AI agents running attacker/defender research loops automatically under fixed-budget evaluations.

autoattacker is autoresearch for red-team / blue-team research.

The repo is built around one idea: let a loop propose new attacker and defender ideas, test them under the same fixed evaluation setup every time, keep the ones that actually help, discard the ones that don't, and leave behind saved run evidence you can inspect the next morning.

The loop is small on purpose. You point it at a bounded toy environment, run a search, and check whether the best-so-far set moved for a real reason or stayed put.

## How it works

`generate -> evaluate -> compare -> decide -> record -> repeat`

The main evaluation setup is `toy_default_v1`. It freezes the adapter, seeds (`7`, `11`, `19`), task count (`4`), turn budget (`6`), and the number of new attacker and defender candidates tested each iteration (`3` per side). That keeps comparisons fair. A new candidate only gets promoted if it beats the current best under that same setup and the result is backed by saved run evidence.

The keep/discard logic is simple. Each new candidate ends in one of four outcomes: `promote`, `archive_interesting`, `discard`, or `crash`. Only `promote` changes the best-so-far set.

The main evidence surfaces are:

- `runs/frontier.json`: the current best attacker, current best defender, and the small best-so-far set written by the loop
- `runs/campaign_results.tsv`: the append-only log of keep/discard decisions
- `runs/campaign-*/campaign_summary.md`: compact summaries for each search run
- `runs/campaign-*/comparisons/` and `runs/*/matches/`: saved comparison and match artifacts

If you only inspect two files, start with `runs/frontier.json` and the latest `runs/campaign-*/campaign_summary.md`.

## Quick start

Requirements: Python `3.11+` and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
python3 -m unittest discover -s tests -v
python3 -m autoattacker.cli campaign --eval toy_default_v1 --iterations 1
```

That gives you the smallest credible verify-and-run path. After it finishes, inspect `runs/frontier.json`, `runs/campaign_results.tsv`, and the newest `runs/campaign-*/campaign_summary.md`.

## Running the agent

The canonical search run uses the main fixed evaluation setup:

```bash
python3 -m autoattacker.cli campaign --eval toy_default_v1 --iterations 4
```

Run it again on the same repo state if you want to see whether the loop can keep improving from the current best-so-far set:

```bash
python3 -m autoattacker.cli campaign --eval toy_default_v1 --iterations 3
```

There is also one tiny portability smoke on a shifted toy variant:

```bash
python3 -m autoattacker.cli campaign --eval toy_shifted_smoke_v1 --iterations 2 --output-root runs/portability_shifted
```

That shifted run exists to check that the loop still behaves sensibly under a small environment change. It is a smoke test, not a second benchmark program.

## Project structure

A few files matter most:

- `README.md`: public entrypoint
- `program.md`: doctrine for the loop
- `autoattacker/cli.py`: command-line entrypoint for search runs
- `autoattacker/kernel/eval.py`: fixed evaluation setup definitions
- `autoattacker/kernel/`: scoring, selection, mutation, state updates, and summary generation
- `autoattacker/adapters/toy_control/`: bounded toy environments used for shipped runs
- `tests/`: verification
- `runs/`: checked-in saved run evidence

## Design choices

A few choices drive the whole repo.

- **Fixed evaluation setup.** The main setup stays frozen so search runs are comparable. That is the whole point of the evidence trail.
- **Keep/discard discipline.** Every new candidate is judged against the current best, then written down. Failed runs are written down too.
- **State written by the loop.** `runs/frontier.json` and `runs/campaign_results.tsv` are the authoritative surfaces. Markdown summaries help humans read the results, but they are not the control plane.
- **Small mutable surface.** The interesting knobs are `program.md`, the operator code, the selector, and the toy adapter. The rest is there to keep evaluation and evidence stable.
- **Toy-first safety.** The shipped environments are bounded, local, and intentionally simplified. They exist to study the research loop itself.

Current scope is deliberately narrow: one main fixed evaluation setup, one tiny shifted smoke, autonomous search runs, and cumulative saved evidence. Broad benchmark coverage, large orchestration layers, and real-world offensive tooling are outside the scope of this repo.

## Platform support

The shipped environments are pure Python and local. You do not need a GPU, a cluster, or external services to run the loop.

macOS and Linux are the expected path. Windows may work with Python `3.11+`, but it has not been exercised in this repo.

## License

A standalone license file is not checked in yet. If you plan to reuse the code, check the repo state before assuming license terms.
