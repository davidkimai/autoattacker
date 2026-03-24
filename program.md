# autoattacker program

## Objective
Implement the canonical autonomous red/blue research loop:

`objective -> generate -> evaluate -> compare -> decide -> record -> repeat`

## Public Identity
- autoattacker is autoresearch for red-team / blue-team research.
- The public one-liner is: `autoattacker: AI agents running attacker/defender research loops automatically under fixed-budget evaluations.`
- The compressed loop language is doctrine for operating the system, not the public headline.

## Fixed Evaluation Setup Doctrine
- The main proving ground is `toy_default_v1`.
- The tiny portability check is `toy_shifted_smoke_v1`.
- The same pairing plus the same seed must produce the same result.
- Comparisons are made under a fixed evaluation setup so keep/discard decisions stay comparable.

## Search-Run Doctrine
- The canonical search-run command is `python3 -m autoattacker.cli campaign --eval toy_default_v1`.
- Each iteration evaluates a bounded set of new candidates against the current best attacker and defender across the frozen seed set.
- The loop writes its state to `runs/frontier.json` and `runs/campaign_results.tsv`.

## Advancement Doctrine
- Only `promote` changes the best-so-far set.
- A promotion replaces the current best for that role.
- `archive_interesting`, `discard`, and `crash` never change the best-so-far set.
- Failed evaluations must be recorded explicitly.

## Operator Doctrine
- Search around the current best, not around the whole architecture.
- Keep the mutable surface small.
- Prefer a few high-signal new-candidate recipes over broad random search.
- Tune operators against the actual current-best attacker and defender surfaces.

## Memory Doctrine
- `runs/` is authoritative.
- Generated markdown is descriptive, not the control plane.
- Keep the public repo minimal and cumulative.
