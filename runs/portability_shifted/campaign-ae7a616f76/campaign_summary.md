# Search Run campaign-ae7a616f76

- Fixed evaluation setup: toy_shifted_smoke_v1
- Iterations: 2
- Best-so-far state file: runs/portability_shifted/frontier.json
- Promotions: 3
- Archived: 4
- Crashes: 0

## What Was Tried
- iter 1 attacker new candidate attacker-289bd135cc vs current best attacker-baseline: archive_interesting (beats current best but loses the same-iteration comparison to attacker-deaa4dd1ad (-0.665 vs -0.650))
- iter 1 attacker new candidate attacker-deaa4dd1ad vs current best attacker-baseline: promote (beats current best by 0.062 with novelty 0.035)
- iter 1 defender new candidate defender-756992e9e4 vs current best defender-baseline: discard (does not beat current best (delta -0.026) and does not add enough novelty)
- iter 1 defender new candidate defender-67f0087c7d vs current best defender-baseline: archive_interesting (informative result: delta 0.001, novelty 0.045)
- iter 2 attacker new candidate attacker-b44bf48664 vs current best attacker-deaa4dd1ad: archive_interesting (beats current best but loses the same-iteration comparison to attacker-ae22962f0b (-0.517 vs -0.404))
- iter 2 attacker new candidate attacker-ae22962f0b vs current best attacker-deaa4dd1ad: promote (beats current best by 0.246 with novelty 0.035)
- iter 2 defender new candidate defender-c17343b4d6 vs current best defender-baseline: archive_interesting (informative result: delta 0.022, novelty 0.047)
- iter 2 defender new candidate defender-7dc5fab0db vs current best defender-baseline: promote (beats current best by 0.061 with novelty 0.049)

## Best-So-Far Changes
- attacker best-so-far set updated: attacker-baseline -> attacker-deaa4dd1ad (delta 0.062190)
- attacker best-so-far set updated: attacker-deaa4dd1ad -> attacker-ae22962f0b (delta 0.246063)
- defender best-so-far set updated: defender-baseline -> defender-7dc5fab0db (delta 0.061083)

## Strongest Next Branch
- Revisit attacker new candidate attacker-b44bf48664 first; it was kept as informative evidence with delta 0.132526 and novelty 0.024633.
