# FINAL NO-FILES FIX — one last recovery experiment

**Decision: `RECOVERY_UNSUCCESSFUL_STOP`**

Do **not** submit E2T to TEST3. No further recovery phases.

---

## Measured (Colab, 2026-10-16)

### Stage3 win path (single-task instrument)

| id | Stage3 win | Stage3 ok |
|---|---|---|
| d_026 | SAMPLE_1 | True |
| d_065 | SAMPLE_1 | True |
| d_076 | SAMPLE_2 | True |
| d_143 | SAMPLE_1 | True |
| d_123 | GREEDY | True |

### Single-task E2T-P0

All 5 flips **OK** (including the 4 historical losses).  
→ Regression is **batch budget / batch generation**, not executor math.

### B3 full (40 uncovered No-files)

| policy | Stage3 | E2T | losses | gains | max solve | >40s |
|---|---:|---:|---:|---:|---:|---|
| P0 current | 39/40 | **36/40** | 4 | 1 (d_123) | 28.4s | False |
| P1 reserve-one-sample | 39/40 | **36/40** | 4 | 1 (d_123) | 28.7s | False |

P0 losses: `d_026, d_065, d_076, d_143` (all vote `0.0`).  
P1 losses: **same four**.

### P1 scheduling effect (real)

| batch | P0 samples | P1 samples | P1 repair |
|---|---:|---:|---|
| 0 | 0.0s | 12.1s | 0.0s (reserved) |
| 8 | 0.0s | 11.6s | 0.0s |
| 24 | 0.0s | 4.0s | 3.8s (capped) |

P1 **did** restore sampling wall-time. It did **not** restore accuracy.

---

## GO condition

```text
E2T-fixed >= Stage3 on B3  → FAIL (36 < 39)
no solve >40s              → OK
```

**FAIL** → recovery unsuccessful; stop.

---

## What this means next (outside recovery)

- Do not bake/submit the P1 zip for TEST3 recovery.
- Champion remains Stage3 for submission safety.
- Future work = **BEAT STAGE3** (candidate quality), not more E2T executor/recovery loops.
