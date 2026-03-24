# Campaign campaign-6d0f628b87

- Regime: toy_default_v1
- Iterations: 4
- Frontier state: runs/frontier.json
- Promotions: 5
- Archived: 9
- Crashes: 0

## What Was Tried
- iter 1 attacker attacker-b1a0e99519 vs attacker-baseline: discard (loses comparator by 0.018 without compensating novelty)
- iter 1 attacker attacker-4a87a2b4af vs attacker-baseline: archive_interesting (informative result: delta -0.003, novelty 0.035)
- iter 1 attacker attacker-b0fdf27b6c vs attacker-baseline: promote (beats comparator by 0.122 with novelty 0.030)
- iter 1 defender defender-6c471aafd9 vs defender-baseline: archive_interesting (informative result: delta 0.036, novelty 0.027)
- iter 1 defender defender-f7d5bfd82c vs defender-baseline: promote (beats comparator by 0.071 with novelty 0.043)
- iter 1 defender defender-b382acd673 vs defender-baseline: archive_interesting (informative result: delta 0.021, novelty 0.031)
- iter 2 attacker attacker-e032b99d59 vs attacker-b0fdf27b6c: archive_interesting (beats incumbent but loses same-iteration comparison to attacker-5021dd83db (-0.561 vs -0.541))
- iter 2 attacker attacker-5021dd83db vs attacker-b0fdf27b6c: promote (beats comparator by 0.120 with novelty 0.038)
- iter 2 attacker attacker-89d8de6fa4 vs attacker-b0fdf27b6c: archive_interesting (beats incumbent but loses same-iteration comparison to attacker-5021dd83db (-0.542 vs -0.541))
- iter 2 defender defender-e89f00fa0f vs defender-f7d5bfd82c: archive_interesting (informative result: delta 0.032, novelty 0.036)
- iter 2 defender defender-c1095bf7ea vs defender-f7d5bfd82c: archive_interesting (informative result: delta 0.020, novelty 0.047)
- iter 2 defender defender-0e66185885 vs defender-f7d5bfd82c: promote (beats comparator by 0.063 with novelty 0.032)
- iter 3 attacker attacker-3ace0c1287 vs attacker-5021dd83db: discard (loses comparator by 0.289 without compensating novelty)
- iter 3 attacker attacker-1223e0ecbb vs attacker-5021dd83db: discard (loses comparator by 0.292 without compensating novelty)
- iter 3 attacker attacker-11aacfbd8e vs attacker-5021dd83db: discard (loses comparator by 0.295 without compensating novelty)
- iter 3 defender defender-0ef4ee4690 vs defender-0e66185885: archive_interesting (beats incumbent but loses same-iteration comparison to defender-78930f158c (-0.362 vs -0.315))
- iter 3 defender defender-78930f158c vs defender-0e66185885: promote (beats comparator by 0.113 with novelty 0.056)
- iter 3 defender defender-10c0239a10 vs defender-0e66185885: archive_interesting (informative result: delta -0.000, novelty 0.028)
- iter 4 attacker attacker-462707e3e7 vs attacker-5021dd83db: discard (loses comparator by 0.180 without compensating novelty)
- iter 4 attacker attacker-04c90698a2 vs attacker-5021dd83db: discard (loses comparator by 0.196 without compensating novelty)
- iter 4 attacker attacker-0f3192c57a vs attacker-5021dd83db: discard (loses comparator by 0.181 without compensating novelty)
- iter 4 defender defender-8e4614f194 vs defender-78930f158c: discard (loses comparator by 0.038 without compensating novelty)
- iter 4 defender defender-f15844b6e2 vs defender-78930f158c: discard (loses comparator by 0.124 without compensating novelty)
- iter 4 defender defender-a3bd398718 vs defender-78930f158c: discard (loses comparator by 0.080 without compensating novelty)

## Frontier Delta
- attacker frontier advanced: attacker-baseline -> attacker-b0fdf27b6c (delta 0.122285)
- defender frontier advanced: defender-baseline -> defender-f7d5bfd82c (delta 0.070899)
- attacker frontier advanced: attacker-b0fdf27b6c -> attacker-5021dd83db (delta 0.119536)
- defender frontier advanced: defender-f7d5bfd82c -> defender-0e66185885 (delta 0.063309)
- defender frontier advanced: defender-0e66185885 -> defender-78930f158c (delta 0.112992)

## Strongest Next Branch
- Revisit attacker challenger attacker-89d8de6fa4 first; it archived with delta 0.117803 and novelty 0.041133.
