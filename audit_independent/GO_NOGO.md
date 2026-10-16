# GO / NO-GO — TEST3-recovery (pre-submission)

## Decision

**NO-GO for building/submitting TEST3-recovery.**

### Why NO-GO

- FAIL: H1 Qwen pattern freqs (REAL cache)
- FAIL: H2 E2 agree_rate ≥ 0.99 on REAL cache
- FAIL: H3 REAL cache bake-off
- FAIL: H5 forced-fallback Qwen REAL
- FAIL: H6 TEST2 decomposition REAL

Harness scripts `07`–`12` are in place. Fill gates by running `colab_forced_fallback.ipynb` (Linux+CUDA), downloading `generations_*.json` + replay CSV into `audit_independent/results/`, then re-running `07`–`12`.

## Checklist H1–H6

| Check | Result | Level |
|---|---|---|
| Stage3 deterministic parity (public Tables 80/80) | PASS | MEASURED prior |
| Stage3 import_pandas PASS | PASS | MEASURED |
| TEST1 samples import_pandas FAIL | PASS | MEASURED |
| TEST2 + alias fix PASS | PASS | MEASURED |
| H1 Qwen pattern freqs (REAL cache) | FAIL/MISSING | REQUIRED |
| H2 E2 agree_rate ≥ 0.99 on REAL cache | FAIL/MISSING | REQUIRED |
| H3 alias vs importlib decision documented | PASS | REQUIRED |
| H3 REAL cache bake-off | FAIL/MISSING | REQUIRED |
| H4 batch-order probe run | PASS | REQUIRED |
| H4 no order sensitivity (or batch forbidden) | PASS | REQUIRED |
| H5 forced-fallback Qwen REAL | FAIL/MISSING | REQUIRED |
| H6 TEST2 decomposition REAL | FAIL/MISSING | REQUIRED |
| Linux/GPU p95 < 40s documented | FAIL/MISSING | NOT RUN |
| Scanner conformité | FAIL/MISSING | NOT RUN |
| No TEST3 submission file created | PASS | POLICY |

## Artefact presence

- `QWEN_PATTERN_FREQ.md`: present
- `EXECUTOR_AGREEMENT.md`: present
- `ALIAS_VS_IMPORTLIB.md`: present
- `BATCH_ORDER.md`: present
- `FORCED_FALLBACK_QWEN.md`: present (NOT RUN body)
- `TEST2_DECOMPOSITION.md`: present
- `GO_NOGO.md`: present

## H2 snapshot
- E2_alias agree_rate = **0.9688**


## Frozen TEST3-recovery spec (only if GO)

```
STAGE3-COMPLIANT-RECOVERY
Model: Qwen2.5-Coder-1.5B exact
Rules/Prompt/Fits/No-files/Tables/Vote: Stage3 EXACT
BUDGET 29 / MAX_NEW 500 / NSAMP 4 / default vote 0
ONLY change: E2 executor (__dsh_pd alias) if H2/H3 PASS
FORBIDDEN: calc_safe_v2, extended rules, reject-zero, default=1,
           Qwen3, new prompts, inter-task batch
```

## Prior CPU diagnostic (still valid)

| Agent | import_pandas contract |
|---|---|
| stage3 fix=False | True |
| test1 fix=False | False |
| test2 fix=False | False |
| test2 fix=True | True |
| faithful fix=False | True |

## Rules ablation snapshot

- `stage3_hist`: covered 80/80, correct 80, wrong 0
- `test2_full_keep0`: covered 80/80, correct 80, wrong 0
- `test2_full_reject0`: covered 80/80, correct 80, wrong 0
- `test2_hist_keep0`: covered 80/80, correct 80, wrong 0
- `test2_hist_plus_ext_reject0`: covered 80/80, correct 80, wrong 0
- `test2_hist_reject0`: covered 80/80, correct 80, wrong 0


## Next action

1. Keep NO-GO until all REQUIRED gates PASS on a REAL_QWEN cache.
2. Colab: `audit_independent/colab_forced_fallback.ipynb` → download cache+replay.
3. Local: `python make_synthetic_cache.py` is smoke-only; then `07`…`12`, `06_go_nogo.py`.
4. Only after GO: bake one Stage3+E2 agent file — not before.
