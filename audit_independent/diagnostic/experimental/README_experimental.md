# Experimental copies (pre-TEST3)

- `stage3_faithful_dsh.py` — TEST1 + one child per sample (correctness oracle; slow).
- `test1_alias_dsh.py` — **E2 candidate**: TEST1 + `__dsh_pd` + SyntaxError pre-compile
  isolation (one child for N samples). Smoke: pandas OK, siblings kept on SyntaxError.
- `executor_e4_importlib.py` — **E4**: Stage3 helpers + importlib module-scope load (in-process).

Rebuild: `python diagnostic/build_experimental.py`

No submission artifacts. TEST3-recovery only after H1–H6 gates pass on a REAL Qwen cache.
