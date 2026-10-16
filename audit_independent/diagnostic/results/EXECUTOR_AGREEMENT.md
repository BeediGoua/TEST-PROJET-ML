# H2 — Executor semantic agreement

**Cache:** `generations_synthetic_smoke.json` (SYNTHETIC_OR_PARTIAL)

**Platform:** Windows-11-10.0.26200-SP0

## Agreement vs E0 (Stage3 exec) among E0-finite programs

| Executor | n | agree_rate | ≥99% | import_pandas agree |
|---|---:|---:|---|---:|
| E1_test1 | 32 | 0.6250 | FAIL | 0.000 |
| E2_alias | 32 | 0.9688 | FAIL | 1.000 |
| E3_test2 | 32 | 0.6562 | FAIL | 0.000 |
| E4_importlib | 32 | 1.0000 | PASS | 1.000 |
| E4_faithful | 32 | 0.8438 | FAIL | 0.875 |

## Syntax isolation (one SyntaxError among 4)

- `E0_stage3`: siblings_kept=True all_none=False vals=[6.0, None, 42.0, 9.0]
- `E1_test1`: siblings_kept=False all_none=True vals=[None, None, None, None]
- `E2_alias`: siblings_kept=False all_none=True vals=[None, None, None, None]
- `E3_test2`: siblings_kept=False all_none=True vals=[None, None, None, None]
- `E4_importlib`: siblings_kept=True all_none=False vals=[6.0, None, 42.0, 9.0]
- `E4_faithful`: siblings_kept=False all_none=True vals=[None, None, None, None]

## Mutation (E0 double replay)

- divergent / n = 0 / 20

## Gate

- **NOT RUN for GO:** cache is not a real Qwen generation set.

- Local numbers are smoke-only.
