# FINAL NO-FILES FIX — one Colab session, then stop

**GPU required. One agent pair. No broad audit. No TEST3 submit from this notebook.**

```text
git pull → setup → instrument 5 flips → (maybe P1) → B3 only → GO/FAIL → bake only if GO
```

---

## 00 — pull + path

```python
!cd /content/TEST-PROJET-ML && git pull

import sys, json, os, math, tempfile, time
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path("/content/TEST-PROJET-ML")
AUDIT = PROJECT_ROOT / "audit_independent"
sys.path[:0] = [str(AUDIT), str(PROJECT_ROOT), str(AUDIT / "diagnostic")]

from pretest3_common import DIAG_OUT
from src.evaluation.core import _materialize_all
import audit as audit_mod
import final_recovery_harness as H
from bake_stage3_e2t_recovery import bake
import final_nofiles_fix as F
```

Re-run the usual §00 setup from `colab_final_recovery.ipynb` if `dsh` / HF cache not already warm.

---

## 01 — load single agent pair (avoid OOM)

```python
OUTER = 7.5
os.environ["DSH_OUTER_MANY"] = str(OUTER)
os.environ.pop("DSH_FORCE_FALLBACK", None)
os.environ.pop("DSH_RESERVE_ONE_SAMPLE", None)  # P0

agent_path = bake(outer_many=OUTER, reserve_one_sample_default=False)
A = audit_mod.load("stage3")
Bmod = H.load_mod(agent_path, "stage3_e2t_rec")
A.MODEL = Bmod.MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"

# ONE Stage3 + ONE E2T (do not instantiate a second E2T agent)
agent_a = A.Agent()
agent_b = Bmod.Agent()
print("agents ready", agent_path)
```

---

## 02 — instrument ONLY the 5 flip ids (single-task)

```python
HANDOFF = PROJECT_ROOT / "CODEX_AUDIT_HANDOFF"
all_tasks = json.loads((HANDOFF / "dev.json").read_text(encoding="utf-8"))
byid = {t["id"]: t for t in all_tasks}

traces = []
class_rows = []
for tid in F.FLIP_IDS:
    t = {**byid[tid], "files": byid[tid].get("files") or []}
    print("=== TRACE Stage3", tid, "===")
    tr_a = F.trace_solve(agent_a, A, t, "Stage3")
    print("=== TRACE E2T-P0", tid, "===")
    tr_b = F.trace_solve(agent_b, Bmod, t, "E2T-P0")
    row = F.classify_pair(tr_a, tr_b)
    class_rows.append(row)
    traces.append({"stage3": tr_a, "e2t_p0": tr_b})
    print(row)

cls_df = pd.DataFrame(class_rows)
print(cls_df.to_string(index=False))
cls_df.to_csv(DIAG_OUT / "nofiles_fix_class_p0.csv", index=False)

p1_ok = F.evidence_supports_p1(class_rows)
print("EVIDENCE_SUPPORTS_P1", p1_ok)
for r in class_rows:
    print(
        f"{r['id']}: Stage3 wins via {r['stage3_win_path']} | "
        f"E2T fails via {r['e2t_fail_reason']}"
    )
```

**Stop rule before coding further:** if `EVIDENCE_SUPPORTS_P1` is False, read the table — if another *single* control bug is obvious, fix that instead; else declare FAIL without B3-P1.

---

## 03 — B3 P0 (current E2T) on all 40 uncovered No-files

```python
nofiles = H.uncovered_nofiles(A, all_tasks)
print("uncovered", len(nofiles))
TD_NF = tempfile.mkdtemp(prefix="nf_fix_")
fm = _materialize_all(nofiles, TD_NF)
nf_tasks = [{**t, "files": fm[t["id"]]} for t in nofiles]

os.environ.pop("DSH_RESERVE_ONE_SAMPLE", None)
df_p0, sum_p0 = F.run_b3(agent_a, agent_b, nf_tasks, "E2T-P0")
df_p0.to_csv(DIAG_OUT / "final_b3_nofiles_p0.csv", index=False)
print(sum_p0)
print("LOST", df_p0[(df_p0.a_ok) & (~df_p0.b_ok)][["id", "gold", "a", "b"]].to_string(index=False))
print("GAIN", df_p0[(~df_p0.a_ok) & (df_p0.b_ok)][["id", "gold", "a", "b"]].to_string(index=False))
```

---

## 04 — P1 only if evidence supports it, then B3 fixed

```python
sum_p1 = None
df_p1 = None
p1_applied = False

if p1_ok:
    p1_applied = True
    os.environ["DSH_RESERVE_ONE_SAMPLE"] = "1"
    os.environ["DSH_SAMPLE_RESERVE"] = "9.0"
    # Same agent_b weights; reuse Stage3 answers from P0 (only re-solve E2T)
    df_p1, sum_p1 = F.run_b3(
        agent_a, agent_b, nf_tasks, "E2T-P1",
        stage3_answers=sum_p0["stage3_answers"],
    )
    df_p1.to_csv(DIAG_OUT / "final_b3_nofiles_p1.csv", index=False)
    print(sum_p1)
    print("LOST", df_p1[(df_p1.a_ok) & (~df_p1.b_ok)][["id", "gold", "a", "b"]].to_string(index=False))
    print("GAIN", df_p1[(~df_p1.a_ok) & (df_p1.b_ok)][["id", "gold", "a", "b"]].to_string(index=False))
else:
    print("P1 SKIPPED — evidence did not support reserve-one-sample")
```

---

## 05 — GO / FAIL + report + conditional bake

```python
from final_pre_test3_debug import b4_compare

fixed = sum_p1 if p1_applied else None
go, reason = F.decide_go(fixed, stage3_n=int(sum_p0["stage3_n"]))
# Also require no regression vs P0 accuracy when P1 applied
if go and p1_applied and sum_p1["e2t_n"] < sum_p0["e2t_n"]:
    go, reason = False, "P1 accuracy < P0"

df_b4 = b4_compare(HANDOFF / "STAGE3_SUBMITTED_92_5.py", agent_path)
print(df_b4.to_string(index=False))
if bool(df_b4.loc[df_b4.warning == "exec_upload_violation", "e2t"].iloc[0]):
    go, reason = False, "exec_upload_violation on E2T"

F.write_report(class_rows, traces, p1_applied, sum_p0, sum_p1, go, reason)
print("GO" if go else "FAIL", reason)

if go:
    # Re-bake with reserve default ON for submission zip
    os.environ.pop("DSH_RESERVE_ONE_SAMPLE", None)
    final_path = bake(outer_many=OUTER, reserve_one_sample_default=True)
    print("BAKED_FOR_SUBMIT", final_path)
    print("ZIP", AUDIT / "STAGE3_E2T_RECOVERY.zip")
    print("STOP — human may submit TEST3; no more recovery phases.")
else:
    print("RECOVERY_UNSUCCESSFUL_STOP — do not submit; no further recovery.")
```

---

## What to paste back (only if you want confirmation)

From cell 05 stdout:

```text
GO / FAIL + reason
classification table (cell 02)
sum_p0 / sum_p1
BAKED_FOR_SUBMIT path (if GO)
```

Or push/commit `FINAL_NOFILES_FIX.md` + CSVs from Colab if you sync the repo.
