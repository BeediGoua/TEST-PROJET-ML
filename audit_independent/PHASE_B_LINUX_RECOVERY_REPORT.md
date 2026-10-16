# Phase B — Linux Recovery Report

**Status:** DRAFT — fill after B1→B4 on Colab.  
**Verdict:** `NOT TESTED` → replace by `RECOVERY_READY` or `RECOVERY_NOT_READY`.

## Policy

No TEST3 submission file. No Qwen3 / new prompts / regex / calc_safe_v2 / reject-zero / default=1 / inter-task batching.

## B0 — Reference protocol

| Item | Label | Notes |
|---|---|---|
| Stage3 EXEC_TIMEOUT | MEASURED | 1.5 s |
| Phase A script `15` used E0=1.5 | MEASURED | see `diagnostic/B0_TIMEOUT_PROTOCOL.md` |
| Script `08` default timeout 5.0 | MEASURED | biased; not production ref |
| Dual E0 focus re-run 100% | MEASURED (Windows) | d_041/100/170 |
| Dual E0 full 400 | NOT TESTED | run `--full` / Linux |

## B1 — Linux executor gate

| Item | Label | Notes |
|---|---|---|
| Loop `[6,None,42,9]` | NOT TESTED | |
| Isolation probes | NOT TESTED | |
| Outer sweep 6.5–8.0 | NOT TESTED | |
| PROGRAM agree vs E0_sem/prod | NOT TESTED | |
| TASK vote agree | NOT TESTED | |
| Final accuracy | NOT TESTED | |
| bad_numeric | NOT TESTED | must be 0 |
| Chosen outer | NOT TESTED | |

## B2 — Agent.solve Tables

| Item | Label |
|---|---|
| Stage3 vs Stage3+E2T forced-fallback | NOT TESTED |
| Batch timings / repair / samples skipped | NOT TESTED |
| Stress K=1,2,4,8 | NOT TESTED |

## B3 — No-files

| Item | Label |
|---|---|
| 40 uncovered No-files Stage3 vs +E2T | NOT TESTED |
| Link to private 43/45→40/45 | HYPOTHESIS until measured |

## B4 — Scanner / resources

| Item | Label |
|---|---|
| Static compliance / exec ban / RAM / tmp / solve&lt;40 | NOT TESTED |

## Final verdict

```
RECOVERY_NOT_READY
```

Justification: B1–B4 not yet executed on Linux. Local B0 only.
