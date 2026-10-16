# H1 — Qwen pattern frequency

**Cache:** `generations_34d6ece55b3c092a.json` (REAL_QWEN)

**Programs analyzed:** 400

## Overall rates

| Pattern | count | rate |
|---|---:|---:|
| import pandas as pd | 320 | 0.8000 |
| any import | 324 | 0.8100 |
| rebind pd | 0 | 0.0000 |
| syntax_ok False | 1 | 0.0025 |
| empty / no answer (trunc heuristic) | 40 | 0.1000 |

## By phase

### greedy (n=80)
- import_pandas_as_pd: 0.8750
- any_import: 0.8750
- syntax failures: 0.0000

### samples (n=320)
- import_pandas_as_pd: 0.7812
- any_import: 0.7937
- syntax failures: 0.0031

## Interpretation

- Measured `import pandas as pd` rate = **0.8000** on forced-fallback generations.

- Material rate: with 4 samples/task, amplification can wipe self-consistency votes.
