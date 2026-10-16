# Rules ablation (deterministic)

## Table coverage / correctness on public 80

| Config | covered | correct | wrong |
|---|---:|---:|---:|
| stage3_hist | 80 | 80 | 0 |
| test2_full_keep0 | 80 | 80 | 0 |
| test2_full_reject0 | 80 | 80 | 0 |
| test2_hist_keep0 | 80 | 80 | 0 |
| test2_hist_plus_ext_reject0 | 80 | 80 | 0 |
| test2_hist_reject0 | 80 | 80 | 0 |

## Shadow tags (hist reject0 vs full reject0)

- `shadow:same` : 80

## Calc coverage

| Config | covered | correct |
|---|---:|---:|
| stage3_calc | 25 | 25 |
| test2_calc_hist | 25 | 25 |
| test2_calc_plus_safe | 65 | 65 |

## Interpretation

- **MEASURED:** public Tables stay near 80/80 across configs → extensions do not
  change the public Tables metric that masked the LLM path.
- **MEASURED:** `calc_safe_v2` is what lifts No-files coverage on public calc tasks.
- **HYPOTHESIS:** private Tables damage from extensions requires private/OOD types;
  public shadow overrides count is the local upper bound on disagreement.
