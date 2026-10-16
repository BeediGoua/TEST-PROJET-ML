# FINAL NO-FILES FIX — one last recovery experiment

**Status: READY FOR COLAB (not yet measured)**

Follow `COLAB_FINAL_NOFILES_FIX.md` — single session:

1. Instrument `d_026 / d_065 / d_076 / d_143 / d_123` (Stage3 vs E2T-P0)
2. Answer win-path / fail-reason per loss
3. Apply **P1 reserve-one-sample** only if evidence supports it
4. Re-run **B3 only** (40 uncovered No-files)
5. `GO` → bake zip with reserve default ON and **STOP**  
   `FAIL` → recovery unsuccessful, **STOP** (no further phases)

No Qwen3 / new prompts / regex / rules / vote changes.

P1 code is already in the baker (`DSH_RESERVE_ONE_SAMPLE`); Colab toggles it via env for P0 vs P1.
