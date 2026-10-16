# Forced fallback (CPU proxy)

**Qwen GPU:** NOT RUN: torch.cuda.is_available() is False.

## Method

- Table rules assumed absent (programs fixed; no Agent.solve loop).
- Stratified sample of 12 / 80 public Tables.
- Styles: no_import / import_pandas / import_numpy / syntax_broken.
- TEST1/faithful measured on **samples path** (`run_codes_many`); TEST2 on `run_code_batch`.

## Execution rates

| Agent | fix | no_import | import_pandas | import_numpy | finite(pandas) | default=1 |
|---|---|---:|---:|---:|---:|---:|
| stage3 | False | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| test1 | False | 1.00 | 0.00 | 1.00 | 0.00 | 0.00 |
| test2 | False | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 |
| test2 | True | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| faithful | False | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |

## Interpretation

- **MEASURED:** import_pandas collapses on TEST1 samples and TEST2 batch; Stage3 and faithful stay at 1.0.
- **MEASURED:** TEST2 failure mode maps to default=1 answers when candidates are empty.
- **HYPOTHESIS:** private Tables gap size scales with how often Qwen emits `import pandas as pd`.
- Real Qwen forced-fallback (oracle@4, repair_gain, 40s batches) remains **NOT RUN**.
