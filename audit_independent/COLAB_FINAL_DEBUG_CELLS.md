# Cells to paste on Colab (after `git pull`) — targeted debug only

Runtime: GPU. Do **not** run old B2/B4 bake as “READY”.

```python
!cd /content/TEST-PROJET-ML && git pull
```

Then ensure imports from a prior session still work, or re-run setup from `colab_final_recovery.ipynb` §00.

---

## Cell A — B2 VALIDATION (forced fallback must be real)

```python
import os, time, tempfile, json
import final_pre_test3_debug as D
from bake_stage3_e2t_recovery import bake
from pretest3_common import table_tasks, DIAG_OUT
from src.evaluation.core import _materialize_all
import audit as audit_mod
import final_recovery_harness as H

OUTER = 7.5
os.environ["DSH_FORCE_FALLBACK"] = "1"
os.environ["DSH_OUTER_MANY"] = str(OUTER)

agent_path = bake(outer_many=OUTER)
A = audit_mod.load("stage3")
D.disable_table_rules(A)
A._rules_disabled = True
Bmod = H.load_mod(agent_path, "stage3_e2t_rec")
A.MODEL = Bmod.MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
agent_a, agent_b = A.Agent(), Bmod.Agent()

tables = table_tasks()
TD = tempfile.mkdtemp(prefix="b2val_")
fm = _materialize_all(tables, TD)
batch = [{**t, "files": fm[t["id"]]} for t in tables]
first = batch[:8]

st_a = D.instrumented_solve(agent_a, A, first, "Stage3")
st_b = D.instrumented_solve(agent_b, Bmod, first, "E2T")
for st in (st_a, st_b):
    print(st["label"], {k: st[k] for k in st if k != "answers"})

assert st_a["deterministic_count"] == 0 and st_a["llm_live_count"] == 8
assert st_b["deterministic_count"] == 0 and st_b["llm_live_count"] == 8
assert st_a["greedy_generation_seconds"] > 1 and st_b["greedy_generation_seconds"] > 1
print("B2 instrument PASS — real LLM forced-fallback")
```

If assert fails or times ~0.3s → **B2 INVALID**.

Optional full 80 after PASS (long): use `H.run_solve_compare` as before.

---

## Cell B — B3 flips + the missing +1 gain

```python
import math, pandas as pd
from pathlib import Path

# Prefer existing CSV from diagnostic B3; else rebuild path
csv = DIAG_OUT / "final_b3_nofiles.csv"
assert csv.exists(), "Re-run nofiles diagnostic first to create final_b3_nofiles.csv"
df = pd.read_csv(csv)
lost = df[(df.a_ok == True) & (df.b_ok == False)]
gain = df[(df.a_ok == False) & (df.b_ok == True)]
print("LOST", len(lost)); print(lost[["id","gold","a","b"]].to_string(index=False))
print("GAIN", len(gain)); print(gain[["id","gold","a","b"]].to_string(index=False))
```

---

## Cell C — Counterfactual on flip ids only

```python
# Requires agent_a (Stage3 exec), agent_b / Bmod (E2T), and DEBUG=1 style access to codes.
# Minimal: for each flip id, run one greedy generate+extract under each agent with DSH_DEBUG if needed.
# Paste flip ids:
FLIP_IDS = list(lost["id"]) + list(gain["id"])
HANDOFF = PROJECT_ROOT / "CODEX_AUDIT_HANDOFF"
byid = {t["id"]: t for t in json.loads((HANDOFF/"dev.json").read_text(encoding="utf-8"))}

rows = []
os.environ.pop("DSH_FORCE_FALLBACK", None)
for tid in FLIP_IDS:
    t = byid[tid]
    tt = {**t, "files": []}
    # single-task solve both arms
    ra = agent_a.solve([tt])[0]["answer"]
    rb = agent_b.solve([tt])[0]["answer"]
    rows.append(dict(id=tid, gold=t["answer"], stage3=ra, e2t=rb))
print(pd.DataFrame(rows).to_string(index=False))
print("For full code-level counterfactual enable DSH_DEBUG=1 and capture LAST codes — or use notebook debug helper next.")
```

For **exact code replay** (critical), run with debug logging:

```python
os.environ["DSH_DEBUG"] = "1"
# re-solve one task at a time and copy printed code blocks from logs into:
#   Bmod.run_code(stage3_code, {}, 1.5, obj)  vs  A.run_code(e2t_code, {}, 1.5, obj)
```

---

## Cell D — B4 warning compare (no GPU)

```python
from final_pre_test3_debug import b4_compare
from pathlib import Path
dfw = b4_compare(
    PROJECT_ROOT/"CODEX_AUDIT_HANDOFF"/"STAGE3_SUBMITTED_92_5.py",
    AUDIT/"STAGE3_E2T_RECOVERY"/"agent.py",
)
print(dfw.to_string(index=False))
dfw.to_csv(DIAG_OUT/"b4_warning_compare.csv", index=False)
```

Expected: 3 mismatches **INHERITED**; `exec_upload_violation` False only on E2T.
