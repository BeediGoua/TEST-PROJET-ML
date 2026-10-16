# Diagnostic + pre-TEST3 (H1–H6)

No TEST3 submission in this pack. Goal: measure gates before any Stage3-compliant recovery.

## Run (CPU / Windows)

```bash
.venv\Scripts\python.exe projects/audit_independent/diagnostic/run_all.py
```

This builds experimental executors, a **synthetic smoke cache** (not Qwen), then runs A–F + H1–H6 harnesses.

## GPU / Linux (required for GO)

1. Open [`../colab_forced_fallback.ipynb`](../colab_forced_fallback.ipynb) on Colab T4.
2. Point `PROJECT_ROOT` at an uploaded `projects/` tree.
3. Download `generations_*.json` + `*_replay.csv` into `audit_independent/results/`.
4. Re-run `07`–`12` then `06_go_nogo.py`.

## Scripts

| Script | Hypothesis |
|---|---|
| `07_qwen_pattern_freq.py` | H1 pattern frequencies |
| `08_executor_agreement.py` | H2 P(Ei=E0) ≥99% |
| `09_alias_vs_importlib.py` | H3 E2 vs E4 |
| `10_batch_order.py` | H4 order sensitivity |
| `11_stage3_forced_fallback_qwen.py` | H5 forced-fallback metrics |
| `12_test2_decomposition.py` | H6 one-factor deltas |
| `06_go_nogo.py` | Aggregate GO/NO-GO |

## Experimental executors

- `experimental/test1_alias_dsh.py` — **E2** (`__dsh_pd`)
- `experimental/executor_e4_importlib.py` — **E4** importlib
- `experimental/stage3_faithful_dsh.py` — slow correctness oracle

## Outputs

See `results/QWEN_PATTERN_FREQ.md`, `EXECUTOR_AGREEMENT.md`, `ALIAS_VS_IMPORTLIB.md`, `BATCH_ORDER.md`, `FORCED_FALLBACK_QWEN.md`, `TEST2_DECOMPOSITION.md`, `GO_NOGO.md`.
