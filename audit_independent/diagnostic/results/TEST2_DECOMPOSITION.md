# H6 — TEST2 one-factor decomposition

**Cache:** `generations_synthetic_smoke.json` (SYNTHETIC_OR_PARTIAL)

**Platform:** Windows-11-10.0.26200-SP0

## Note on rules

Extended table rules (`table_extended_rule` / `table_extra_safe2`) and historical guards are **not** applied here: this experiment freezes the LLM programs and varies **executor / vote / batch** only. Public deterministic shadow already showed `same:80` for rule extensions — private rule FP remains HYPOTHESIS without OOD private labels.

## Results

| config | n | accuracy | Δ vs S0 | exec_rate | default1_rate |
|---|---:|---:|---:|---:|---:|
| S0_stage3_E0 | 8 | 0.0000 | +0.0000 | 0.8000 | 0.0000 |
| S1_E1_test1_many | 8 | 0.0000 | +0.0000 | 0.0000 | 0.0000 |
| S2_E2_alias | 8 | 0.0000 | +0.0000 | 0.0000 | 0.0000 |
| S3_reject_zero | 8 | 0.0000 | +0.0000 | 0.8000 | 0.0000 |
| S4_default1 | 8 | 0.0000 | +0.0000 | 0.8000 | 0.0000 |
| S5_reject_zero_default1 | 8 | 0.0000 | +0.0000 | 0.8000 | 0.0000 |
| S6_test2_batch | 8 | 0.0000 | +0.0000 | 0.6000 | 0.0000 |
| S7_test2_batch_alias | 8 | 0.0000 | +0.0000 | 0.8000 | 0.0000 |

## What never to repeat


- Cache not real Qwen → treat deltas as harness smoke only.
