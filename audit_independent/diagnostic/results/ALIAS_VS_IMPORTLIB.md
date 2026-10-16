# H3 — Alias vs importlib bake-off

**Cache:** `generations_synthetic_smoke.json` (SYNTHETIC_OR_PARTIAL)

**Platform:** Windows-11-10.0.26200-SP0

## Agreement vs E0 (E0-finite only)

- E2 alias agree_rate: **0.8947** (n=19)
- E4 importlib agree_rate: **1.0000**

## Timing snapshot

| agent | program | n | seconds | ok |
|---|---|---:|---:|---:|
| E2_alias | trivial | 1 | 3.934 | 1 |
| E4_importlib | trivial | 1 | 0.007 | 1 |
| E4_faithful | trivial | 1 | 3.852 | 1 |
| E2_alias | import_pandas | 1 | 4.322 | 1 |
| E4_importlib | import_pandas | 1 | 0.022 | 1 |
| E4_faithful | import_pandas | 1 | 3.794 | 1 |
| E2_alias | trivial | 4 | 3.897 | 4 |
| E4_importlib | trivial | 4 | 0.037 | 4 |
| E4_faithful | trivial | 4 | 16.708 | 4 |
| E2_alias | import_pandas | 4 | 3.966 | 4 |
| E4_importlib | import_pandas | 4 | 0.036 | 4 |
| E4_faithful | import_pandas | 4 | 17.143 | 4 |
| E2_alias | trivial | 8 | 3.752 | 8 |
| E4_importlib | trivial | 8 | 0.071 | 8 |
| E4_faithful | trivial | 8 | 32.393 | 8 |
| E2_alias | import_pandas | 8 | 3.822 | 8 |
| E4_importlib | import_pandas | 8 | 0.066 | 8 |
| E4_faithful | import_pandas | 8 | 33.595 | 8 |

## Decision

- Cache not real Qwen → decision is **provisional**. Plan default remains: prefer E2 if ≥99% and faster than E4.

- E4 wins on agreement; still check timing veto (faithful ~36s for n=8 historically).
