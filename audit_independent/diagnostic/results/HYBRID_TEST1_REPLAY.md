# Hybrid TEST1 replay

**Cache:** `generations_34d6ece55b3c092a.json`

## Arms

- **Fidèle:** greedy `test1.run_code` + samples `test1.run_codes_many` + Stage3.vote

- **Recovery:** greedy E2 + samples E2T + Stage3.vote

- **Stage3 baseline:** independent `run_code` 1.5s + Stage3.vote


**WARNING:** Do **not** call the fidèle arm accuracy the real TEST1 private score (104/120). `test1_many` collapses under import pandas.

| arm | vote accuracy | n / note |
|---|---:|---|
| faithful_hybrid (NOT private TEST1) | 0.5125 (41/80) | many contaminated |
| recovery E2T | 0.8125 (65/80) | |
| stage3 baseline | 0.8125 (65/80) | |
| Gain(recovery, faithful) | 24 | +25 / -1 |
| Gain(recovery, stage3) | 0 | +0 / -0 |

## Task-level flips (recovery vs stage3)

- (none)
