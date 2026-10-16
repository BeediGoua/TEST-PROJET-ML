# E2T probes

**Platform:** Windows-11-10.0.26200-SP0

| probe | ok | skipped | detail |
|---|---|---|---|
| infinite_loop | False | True | `NOT RUN: SIGALRM requires Linux — first cell of Colab V2` |
| syntax_middle | True | False | `[6.0, None, 42.0, 9.0]` |
| runtime_middle | True | False | `[6.0, None, 42.0, 9.0]` |
| import_pandas | True | False | `[6.0]` |
| import_numpy | True | False | `[6.0]` |
| rebind_pd | True | False | `[6.0]` |
| mutation_isolation | True | False | `[1.0, 39.0]` |
| fake_read_csv_smoke | True | False | `[39.0]` |
| smartframe_col | True | False | `[39.0]` |
| nofile_sympy | True | False | `[6.0]` |
| fit_sklearn | True | False | `[1.0]` |

**Non-skip PASS:** True (10/10)

**Gate:** infinite_loop NOT RUN on Windows — must pass as first Colab V2 cell.
