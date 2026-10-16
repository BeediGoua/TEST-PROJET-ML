# H5 — Stage3 forced-fallback Qwen (80 Tables)

**Cache:** `generations_34d6ece55b3c092a.json` (REAL_QWEN)

**Source:** replay CSV `generations_34d6ece55b3c092a_replay.csv`

**Platform:** Windows-11-10.0.26200-SP0

## By executor

| executor | tasks | execution_rate | greedy_accuracy | oracle_samples_at4 | oracle_greedy_plus4 | vote_accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| e4_importlib | 80 | 0.5549999999999999 | 0.5 | 0.7375 | 0.825 | 0.7875 |
| minimal_many | 80 | 0.08 | 0.025 | 0.1625 | 0.1625 | 0.1625 |
| stage3 | 80 | 0.5549999999999999 | 0.5 | 0.7375 | 0.825 | 0.7875 |
| test1_alias_many | 80 | 0.5549999999999999 | 0.5 | 0.7375 | 0.825 | 0.7875 |
| test1_many | 80 | 0.03 | 0.025 | 0.05 | 0.05 | 0.05 |
| test1_single | 80 | 0.5549999999999999 | 0.5 | 0.7375 | 0.825 | 0.7875 |
| test2_batch | 80 | 0.08 | 0.025 | 0.1625 | 0.1625 | 0.1625 |
| test2_batch_alias | 80 | 0.08 | 0.025 | 0.1625 | 0.1625 | 0.1625 |

## Stage3 by table family

| type | tasks | greedy_accuracy | oracle_greedy_plus4 | vote_accuracy | execution_rate |
| --- | --- | --- | --- | --- | --- |
| table.derive | 16 | 0.5625 | 0.75 | 0.75 | 0.45 |
| table.filter | 16 | 0.75 | 0.8125 | 0.75 | 0.8125 |
| table.group | 16 | 0.3125 | 0.75 | 0.75 | 0.4 |
| table.join | 16 | 0.25 | 0.875 | 0.75 | 0.425 |
| table.stat | 16 | 0.625 | 0.9375 | 0.9375 | 0.6875 |

## repair_gain

**NOT RUN** — requires a second generation pass with `DSH_NO_REPAIR`.

## Interpretation

- Stage3 vote_accuracy ≈ **0.787** oracle_greedy_plus4 ≈ **0.825**.
