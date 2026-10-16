# H1 — Qwen pattern frequency

**Cache:** `generations_synthetic_smoke.json` (SYNTHETIC_OR_PARTIAL)

**Programs analyzed:** 40

## Overall rates

| Pattern | count | rate |
|---|---:|---:|
| import pandas as pd | 8 | 0.2000 |
| any import | 16 | 0.4000 |
| rebind pd | 0 | 0.0000 |
| syntax_ok False | 8 | 0.2000 |
| empty / no answer (trunc heuristic) | 0 | 0.0000 |

## By phase

### greedy (n=8)
- import_pandas_as_pd: 0.0000
- any_import: 0.0000
- syntax failures: 0.0000

### samples (n=32)
- import_pandas_as_pd: 0.2500
- any_import: 0.5000
- syntax failures: 0.2500

## Interpretation

- **NOT a real Qwen cache** — rates are not usable for private attribution.
