# Campaign campaign-ae7a616f76

- Regime: toy_shifted_smoke_v1
- Iterations: 2
- Frontier state: runs/portability_shifted/frontier.json
- Promotions: 3
- Archived: 4
- Crashes: 0

## What Was Tried
- iter 1 attacker attacker-289bd135cc vs attacker-baseline: archive_interesting (beats incumbent but loses same-iteration comparison to attacker-deaa4dd1ad (-0.665 vs -0.650))
- iter 1 attacker attacker-deaa4dd1ad vs attacker-baseline: promote (beats comparator by 0.062 with novelty 0.035)
- iter 1 defender defender-756992e9e4 vs defender-baseline: discard (loses comparator by 0.026 without compensating novelty)
- iter 1 defender defender-67f0087c7d vs defender-baseline: archive_interesting (informative result: delta 0.001, novelty 0.045)
- iter 2 attacker attacker-b44bf48664 vs attacker-deaa4dd1ad: archive_interesting (beats incumbent but loses same-iteration comparison to attacker-ae22962f0b (-0.517 vs -0.404))
- iter 2 attacker attacker-ae22962f0b vs attacker-deaa4dd1ad: promote (beats comparator by 0.246 with novelty 0.035)
- iter 2 defender defender-c17343b4d6 vs defender-baseline: archive_interesting (informative result: delta 0.022, novelty 0.047)
- iter 2 defender defender-7dc5fab0db vs defender-baseline: promote (beats comparator by 0.061 with novelty 0.049)

## Frontier Delta
- attacker frontier advanced: attacker-baseline -> attacker-deaa4dd1ad (delta 0.062190)
- attacker frontier advanced: attacker-deaa4dd1ad -> attacker-ae22962f0b (delta 0.246063)
- defender frontier advanced: defender-baseline -> defender-7dc5fab0db (delta 0.061083)

## Strongest Next Branch
- Revisit attacker challenger attacker-b44bf48664 first; it archived with delta 0.132526 and novelty 0.024633.
