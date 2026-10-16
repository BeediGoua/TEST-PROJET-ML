# FINAL PRE-TEST3 DEBUG

**Recommendation today: `DO_NOT_SUBMIT`**

No Qwen3 / new prompts / regex / rules. Targeted findings only.

---

## 1. B2 Tables — VALID / INVALID

### Verdict: **INVALID** (previous Colab result)

| Evidence | Value | Interpretation |
|---|---|---|
| max_batch_a / b | **~0.36 s** | Impossible for real Qwen greedy+repair+samples on 8 Tables |
| No-files batch times | **9–28 s** | Real LLM path looks like this |
| Public Tables | all covered by Stage3 rules when enabled | Classic trap: 80/80 deterministic |

### Root cause (MEASURED in code)

1. **`FORCE_FALLBACK` was bound at import time** in the baked agent:
   `FORCE_FALLBACK = os.environ.get(...) == '1'`  
   Colab set the env **after** `load_mod` → flag stayed `False` → table rules still ran.
2. **Historical Stage3** (`audit.load("stage3")`) has **no** force-fallback switch at all → always deterministic on public Tables.

So previous `acc_a=1.0 / acc_b=1.0` on 80 Tables is almost certainly **80/80 rules**, not recovery proof.

### Fix applied (local, pushed next)

- Bake now uses **`_force_fallback()` read at solve-time**.
- Notebook B2: set `DSH_FORCE_FALLBACK=1` **before** load; `disable_table_rules(Stage3)`; instrument first batch requiring:
  - `deterministic_count=0`, `llm_live_count=8`
  - `greedy_generation_seconds > 1`

### Colab re-instrument (MEASURED 2026-10-16) — **VALID** for forced-fallback path

Single-agent E2T, batch of 8 Tables, `DSH_FORCE_FALLBACK=1`:

| metric | value |
|---|---:|
| deterministic_count | **0** |
| llm_live_count | **8** |
| greedy_generation_seconds | **10.81** |
| greedy_outputs_count | 8 |
| repair_count | 3 |
| sample_outputs_count | 0 (adaptive skip / budget) |
| total_seconds | **28.16** |

Previous `0.36s / 80/80` remains **INVALID**. This instrument proves real LLM fallback works after the `_force_fallback` fix. Full 80-task Stage3-vs-E2T accuracy under true fallback still optional (VRAM: one agent at a time).

---

## 2. B3 No-files flips

### Aggregates (MEASURED Colab)

| | Accuracy |
|---|---:|
| Stage3 | 39/40 = 0.975 |
| E2T | 36/40 = 0.900 |

### Stage3 OK → E2T KO (4) — MEASURED

| id | type | gold | Stage3 | E2T |
|---|---|---:|---:|---:|
| d_026 | calc.dates | 13 | 13 | **0.0** |
| d_065 | calc.arithmetic | 6 | 6 | **0.0** |
| d_076 | calc.dates | 16 | 16 | **0.0** |
| d_143 | calc.stats_inline | 8.9 | 8.9 | **0.0** |

`0.0` = empty vote default in `solve()`, not a wrong numeric from E2T.

### Stage3 KO → E2T OK (1) — MEASURED Colab

| id | gold | Stage3 | E2T |
|---|---:|---:|---:|
| **d_123** | 27.0 | **13.0** (wrong) | **27.0** (correct) |

Net: \(39 - 4 + 1 = 36\). E2T is not strictly worse everywhere — it **wins 1** and **loses 4** (all losses = vote default `0.0` = no finite candidate).

### Counterfactual / classification

**NOT TESTED yet** (optional next): replay Stage3-generated codes on E2T for the 4 losses.

Working hypothesis on losses: **GENERATION or TIMING/BUDGET/REPAIR** (empty candidate list → 0.0), not “wrong numeric from E2T”. Gain d_123 suggests E2T sampling/exec can beat Stage3 on at least one nofile.

---

## 3. B4 warnings — Stage3 vs E2T (MEASURED local)

| warning | Stage3 | E2T bake | Status |
|---|---|---|---|
| exec_upload_violation | **True** | **False** | Fixed by E2T (good) |
| sympy_prompt_runtime_mismatch | True | True | **INHERITED** |
| onehot_prompt_runtime_mismatch | True | True | **INHERITED** |
| no_imports_example_mismatch | True | True | **INHERITED** |

No new mismatch introduced by E2T. Sympy mismatch is inherited Stage3 prompt/runtime debt — relevant to No-files but **not** a new E2T regression on the scanner axis.

---

## 4. Minimal fix + rerun plan

1. Pull + rebake (`_force_fallback` dynamic) — done in repo.  
2. Colab: run **debug cells only** (`COLAB_FINAL_DEBUG_CELLS.md`):
   - B2 instrument → must show real LLM  
   - B3 flips + counterfactual on 4+1  
3. If B2 valid and B3 still E2T &lt; Stage3: fix **only** nofile sandbox/exec path for classified EXECUTOR bugs (no new rules).  
4. Rerun B3 only → if E2T ≥ Stage3 and B2 valid → then SUBMIT.

---

## 5. Final recommendation

```text
DO_NOT_SUBMIT
```

Reasons:

1. B3 No-files FAIL (36 &lt; 39).  
2. Prior B2 Tables result **INVALID** (timing + force-fallback bug).  

After Colab debug cells: update this file’s B2 line to VALID/INVALID with numbers, fill the +1 gain id and counterfactual classes, then flip to `SUBMIT` only if both B2 valid and B3 E2T ≥ Stage3.
