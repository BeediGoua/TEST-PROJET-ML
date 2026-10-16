# Batch timing (CPU proxy)

**NOT** Linux 40s / RTX 4090. Cold-start subprocess costs dominate on Windows.

| Agent | program | n | seconds | ok |
|---|---|---:|---:|---:|
| stage3 | trivial | 1 | 4.297 | 1 |
| stage3 | trivial | 4 | 0.007 | 4 |
| stage3 | trivial | 8 | 0.014 | 8 |
| stage3 | import_pandas | 1 | 0.003 | 1 |
| stage3 | import_pandas | 4 | 0.009 | 4 |
| stage3 | import_pandas | 8 | 0.018 | 8 |
| test1 | trivial | 1 | 4.335 | 1 |
| test1 | trivial | 4 | 3.679 | 4 |
| test1 | trivial | 8 | 3.874 | 8 |
| test1 | import_pandas | 1 | 3.699 | 0 |
| test1 | import_pandas | 4 | 4.122 | 0 |
| test1 | import_pandas | 8 | 3.57 | 0 |
| test2 | trivial | 1 | 4.275 | 1 |
| test2 | trivial | 4 | 4.931 | 4 |
| test2 | trivial | 8 | 3.692 | 8 |
| test2 | import_pandas | 1 | 3.863 | 0 |
| test2 | import_pandas | 4 | 3.873 | 0 |
| test2 | import_pandas | 8 | 4.335 | 0 |
| faithful | trivial | 1 | 3.605 | 1 |
| faithful | trivial | 4 | 15.52 | 4 |
| faithful | trivial | 8 | 32.386 | 8 |
| faithful | import_pandas | 1 | 4.161 | 1 |
| faithful | import_pandas | 4 | 15.441 | 4 |
| faithful | import_pandas | 8 | 36.18 | 8 |

## Interpretation

- **MEASURED:** wall times and success counts under mixed program styles.
- **INFERRED:** if import_pandas ok_count collapses while trivial stays OK,
  batch contention is secondary to the pandas contract bug.
- **NOT RUN:** official 40s mixed-task Qwen batches on Linux.
