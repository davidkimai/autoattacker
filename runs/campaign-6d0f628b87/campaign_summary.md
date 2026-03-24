# Search Run campaign-6d0f628b87

- Fixed evaluation setup: toy_default_v1
- Iterations: 4
- Best-so-far state file: runs/frontier.json
- Promotions: 5
- Archived: 9
- Crashes: 0

## What Was Tried
- iter 1 attacker new candidate attacker-b1a0e99519 vs current best attacker-baseline: discard (does not beat current best (delta -0.018) and does not add enough novelty)
- iter 1 attacker new candidate attacker-4a87a2b4af vs current best attacker-baseline: archive_interesting (informative result: delta -0.003, novelty 0.035)
- iter 1 attacker new candidate attacker-b0fdf27b6c vs current best attacker-baseline: promote (beats current best by 0.122 with novelty 0.030)
- iter 1 defender new candidate defender-6c471aafd9 vs current best defender-baseline: archive_interesting (informative result: delta 0.036, novelty 0.027)
- iter 1 defender new candidate defender-f7d5bfd82c vs current best defender-baseline: promote (beats current best by 0.071 with novelty 0.043)
- iter 1 defender new candidate defender-b382acd673 vs current best defender-baseline: archive_interesting (informative result: delta 0.021, novelty 0.031)
- iter 2 attacker new candidate attacker-e032b99d59 vs current best attacker-b0fdf27b6c: archive_interesting (beats current best but loses the same-iteration comparison to attacker-5021dd83db (-0.561 vs -0.541))
- iter 2 attacker new candidate attacker-5021dd83db vs current best attacker-b0fdf27b6c: promote (beats current best by 0.120 with novelty 0.038)
- iter 2 attacker new candidate attacker-89d8de6fa4 vs current best attacker-b0fdf27b6c: archive_interesting (beats current best but loses the same-iteration comparison to attacker-5021dd83db (-0.542 vs -0.541))
- iter 2 defender new candidate defender-e89f00fa0f vs current best defender-f7d5bfd82c: archive_interesting (informative result: delta 0.032, novelty 0.036)
- iter 2 defender new candidate defender-c1095bf7ea vs current best defender-f7d5bfd82c: archive_interesting (informative result: delta 0.020, novelty 0.047)
- iter 2 defender new candidate defender-0e66185885 vs current best defender-f7d5bfd82c: promote (beats current best by 0.063 with novelty 0.032)
- iter 3 attacker new candidate attacker-3ace0c1287 vs current best attacker-5021dd83db: discard (does not beat current best (delta -0.289) and does not add enough novelty)
- iter 3 attacker new candidate attacker-1223e0ecbb vs current best attacker-5021dd83db: discard (does not beat current best (delta -0.292) and does not add enough novelty)
- iter 3 attacker new candidate attacker-11aacfbd8e vs current best attacker-5021dd83db: discard (does not beat current best (delta -0.295) and does not add enough novelty)
- iter 3 defender new candidate defender-0ef4ee4690 vs current best defender-0e66185885: archive_interesting (beats current best but loses the same-iteration comparison to defender-78930f158c (-0.362 vs -0.315))
- iter 3 defender new candidate defender-78930f158c vs current best defender-0e66185885: promote (beats current best by 0.113 with novelty 0.056)
- iter 3 defender new candidate defender-10c0239a10 vs current best defender-0e66185885: archive_interesting (informative result: delta -0.000, novelty 0.028)
- iter 4 attacker new candidate attacker-462707e3e7 vs current best attacker-5021dd83db: discard (does not beat current best (delta -0.180) and does not add enough novelty)
- iter 4 attacker new candidate attacker-04c90698a2 vs current best attacker-5021dd83db: discard (does not beat current best (delta -0.196) and does not add enough novelty)
- iter 4 attacker new candidate attacker-0f3192c57a vs current best attacker-5021dd83db: discard (does not beat current best (delta -0.181) and does not add enough novelty)
- iter 4 defender new candidate defender-8e4614f194 vs current best defender-78930f158c: discard (does not beat current best (delta -0.038) and does not add enough novelty)
- iter 4 defender new candidate defender-f15844b6e2 vs current best defender-78930f158c: discard (does not beat current best (delta -0.124) and does not add enough novelty)
- iter 4 defender new candidate defender-a3bd398718 vs current best defender-78930f158c: discard (does not beat current best (delta -0.080) and does not add enough novelty)

## Best-So-Far Changes
- attacker best-so-far set updated: attacker-baseline -> attacker-b0fdf27b6c (delta 0.122285)
- defender best-so-far set updated: defender-baseline -> defender-f7d5bfd82c (delta 0.070899)
- attacker best-so-far set updated: attacker-b0fdf27b6c -> attacker-5021dd83db (delta 0.119536)
- defender best-so-far set updated: defender-f7d5bfd82c -> defender-0e66185885 (delta 0.063309)
- defender best-so-far set updated: defender-0e66185885 -> defender-78930f158c (delta 0.112992)

## Strongest Next Branch
- Revisit attacker new candidate attacker-89d8de6fa4 first; it was kept as informative evidence with delta 0.117803 and novelty 0.041133.
