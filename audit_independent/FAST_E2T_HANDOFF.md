# FAST_E2T — handoff for the next builder (ChatGPT / Codex / human)

**Status:** E2T recovery STOPPED. Do not submit E2T. Do not invent P2/P3 scheduler patches.

This document pre-chews the repo so the next agent builds **one** thing: `FAST_E2T`.

---

## 0. Final goal (do not confuse stages)

| Stage | Goal | Success means |
|---|---|---|
| **Now** | Compliant executor as **fast as Stage3**, same isolation as E2T | B3 No-files ≥ **39/40**, greedy batch ~Stage3 (not ~16s), zero contamination |
| **Later** | Beat Stage3 **92.5** | Net flips: `# (S3 wrong→new right) > # (S3 right→new wrong)` on real hard cases (esp. dates) |

**Beating 92.5 is NOT the next commit.**  
If FAST_E2T cannot reach Stage3 parity on B3 with speed restored → **STOP this architecture family**. Do not “almost” submit.

Champion until proven otherwise: **Stage3 92.5**.

---

## 1. Frozen scientific baseline (Colab, 2026-10-16)

```text
Stage3 B3 No-files     = 39/40
E2T P0 B3              = 36/40   (same 4 losses: d_026, d_065, d_076, d_143 → vote 0.0)
E2T P1 reserve-sample  = 36/40   (samples restored 0→~12s; score unchanged)
E2T single-task flips  = 5/5 OK  (including the 4 losses)
Stage3 win path        = SAMPLE on the 4 losses; GREEDY on d_123
B2 forced-fallback LLM = VALID
Counterfactual refcodes= Stage3 OK + E2T OK on all 5
```

Reports: `FINAL_NOFILES_FIX.md`, `FINAL_PRE_TEST3_DEBUG.md`, `diagnostic/results/NOFILE_COUNTERFACTUAL.md`.

**Falsified:** “E2T just needs time to sample.”  
**Still true:** executor math is fine; **latency changes which algorithmic path runs**.

---

## 2. What actually differs in code (read these)

### Keep from E2T (source of truth for isolation)

File: `diagnostic/experimental/test1_e2t_dsh.py`  
Also baked: `STAGE3_E2T_RECOVERY/agent.py`

- `run_code` / `run_codes_many`: `__dsh_pd` everywhere in wrapper
- pre-compile SyntaxError → candidate returns None (siblings live)
- fresh dfs per candidate
- per-candidate `SIGALRM` / `ITIMER_REAL` **1.5s** (Linux)
- no `default=1`, no reject-zero, Stage3 vote unchanged

**Limit of E2T today:** `run_codes_many` amortizes only **samples of ONE task**.  
Greedy still uses `absorb()` → **one `dsh.run_python` per task** → measured greedy batch **~14–17s** vs Stage3 **~3–5s**.

### Steal structure from TEST2 (NOT the whole agent)

File: `CODEX_AUDIT_HANDOFF/TEST2_SUBMITTED_77_5.py`

- `run_code_batch(specs, timeout)` ~L1516: **multi-task** in one child
- `solve` greedy path builds `specs` across live tasks then one batch call ~L3825–3843

### FORBIDDEN leftovers from TEST2 (must not reappear)

| Landmine | Where | Why fatal |
|---|---|---|
| `pd.read_csv` in child wrapper | `run_code_batch` ~L1588–1604 | Lexical collision with `import pandas as pd` in generated body |
| `vote(...) if p["c"] else 1.0` | solve ~L3935 | Empty candidates → **default=1** (TEST2 private collapse amplifier) |
| Shared `__BATCH_END` soft budget | driver ~L1609–1613 | Mid-batch `BatchBudgetExpired` can starve later tasks |
| Any new rules / reject-zero / Qwen3 / new prompts | whole file | Confounds; out of scope |
| `BUDGET=34` etc. | constants | Keep Stage3 `BUDGET=29` unless separately A/B’d |

---

## 3. Spec: FAST_E2T (single delta)

```text
Stage3 agent EXACT (model, prompts, rules, vote, BUDGET, NSAMP, MAX_NEW)
+ E2T isolation contract (__dsh_pd, fresh state, syntax isolate, SIGALRM 1.5s/cand)
+ TEST2-style ONE subprocess for multi-task greedy (and preferably repair/continue too)
− NOTHING else from TEST2
```

### Required API shape

```python
def run_code_batch(specs, timeout):
    """specs: list[{code, dfs, obj}]
    ONE dsh.run_python.
    Each candidate: __dsh_pd, fresh dfs, precompile, SIGALRM 1.5s, isolated except.
    Outer timeout_s = timeout (generous enough that per-cand 1.5s is the real cap).
    Prefer FIXED 1.5s per cand (E2T), NOT shrinking shared batch wallet (TEST2).
    """
```

Wire into `solve()` `run_round` for **n==1 (greedy)** across the live batch — this is the ~16s→~6s bet.  
Optionally also continue/repair. Samples can keep E2T `run_codes_many` (already one child per task).

### Hard gates before any GPU

1. Adversarial probes (Linux): infinite loop middle, syntax middle, runtime middle, import pandas, import numpy, DF mutation isolation, mixed tasks different dfs, reverse order, K∈{1,2,4,8}.
2. Cache replay (`generations_34d6ece55b3c092a.json`): agreement vs Stage3 on executable programs; **bad numeric ≈ 0**; no default-1 signature.
3. Timing microbench: N nofile/table programs × cold-ish — FAST_E2T wall time << N×E2T single `run_code`.

### Hard gates on GPU (one Colab)

```text
B3 uncovered No-files: FAST_E2T >= 39/40
greedy batch wall closer to Stage3 (~5s) than E2T (~16s)
no solve >40s
scanner clean (no exec_upload_violation)
B2 path structurally unchanged (or re-spot-check 8 forced-fallback live)
```

Pass → `CANDIDATE WORTH GPU/SUBMIT DISCUSSION`.  
Fail B3 or contamination → `STOP — bury FAST_E2T family`.

---

## 4. Key paths in this repo

```text
CODEX_AUDIT_HANDOFF/
  STAGE3_SUBMITTED_92_5.py          # champion source
  TEST2_SUBMITTED_77_5.py           # run_code_batch + default=1 landmine
  dsh_official.py
  dev.json

audit_independent/
  STAGE3_E2T_RECOVERY/agent.py      # current E2T bake
  diagnostic/experimental/test1_e2t_dsh.py
  bake_stage3_e2t_recovery.py
  final_nofiles_fix.py
  FINAL_NOFILES_FIX.md              # P1 FAIL evidence
  diagnostic/14_e2t_probes.py       # probe suite (SIGALRM needs Linux)
  results/generations_34d6ece55b3c092a.json          # ~1.7MB Qwen cache
  results/generations_34d6ece55b3c092a_replay.csv
  results/generations_34d6ece55b3c092a_summary.csv
```

Also duplicated under `../resultats_proj/` (same cache).

---

## 5. Environment notes

- **Windows host:** `signal.SIGALRM` absent → infinite-loop isolation probes **cannot** be validated here; need Linux (Colab / ChatGPT Linux).
- **VRAM:** never load two Qwen Agents on T4; sequential Stage3 then FAST_E2T.
- Do not `git reset --hard` over unsaved Colab agent edits without stash if experimenting.

---

## 6. What NOT to optimize

- Do not add rules for `d_026/065/076/143` (public overfit; V10 lesson: 65/65 public No-files ≠ private).
- Do not retune sample reserve (P1 already falsified).
- Do not change vote / prompts / model in stage 1.

---

## 7. After FAST_E2T passes (only then — Beat Stage3)

Separate phase. Evidence already points to:

```text
~66/80 tables have ≥1 correct candidate; vote recovers ~63/80
~14/80 have ZERO correct candidates (many dates)
```

Interventions one-at-a-time with net-flip gate. Not part of FAST_E2T bake.

---

## 8. Decision string to return to the human

Either:

```text
CANDIDATE WORTH GPU TEST
+ agent.py / zip
+ probe table
+ cache replay metrics
+ expected B3 notebook (single paste)
```

or:

```text
STOP — FAST_E2T does not restore Stage3 B3 / contaminates / no speedup
```

No intermediate “try P2”.
