"""Build the ONE final recovery Colab notebook. No more intermediate notebooks."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
cells = []


def md(t):
    cells.append(dict(cell_type="markdown", metadata={}, source=t.splitlines(True)))


def code(t):
    cells.append(
        dict(cell_type="code", metadata={}, source=t.splitlines(True), execution_count=None, outputs=[])
    )


md(
    """# FINAL RECOVERY — one Colab, then decide TEST3

```text
B1 Linux E2T → B1 cache replay → B2 Agent.solve Tables → B2b K (optional)
→ B3 No-files → B4 static → BAKE → RECOVERY_READY
```

**STOP** at first failed gate. No Qwen3 / new prompts / rules / auto-submit.

If `RECOVERY_READY`: submit `STAGE3_E2T_RECOVERY.zip` manually as TEST3.
"""
)

md("## 00 — Setup")
code(
    r'''
from pathlib import Path
import sys, os, platform, json, tempfile, time
assert platform.system()=="Linux", "FINAL RECOVERY requires Colab Linux"
# !git clone https://github.com/BeediGoua/TEST-PROJET-ML.git
PROJECT_ROOT = Path("/content/TEST-PROJET-ML")
assert (PROJECT_ROOT/"audit_independent"/"audit.py").exists()
AUDIT = PROJECT_ROOT/"audit_independent"
sys.path[:0] = [str(AUDIT), str(PROJECT_ROOT), str(AUDIT/"diagnostic")]
os.chdir(AUDIT)
!pip -q install torch transformers accelerate pandas numpy scipy scikit-learn sympy pyarrow 2>/dev/null || true
from gpu_experiments import official
from build_experimental import build_test1_e2t, build_test1_alias
from pretest3_common import EXP, load_path, AUDIT_OUT, DIAG_OUT, table_tasks, load_cache, is_real_qwen_cache
import audit as audit_mod
from src.evaluation.core import _materialize_all
import final_recovery_harness as H
from bake_stage3_e2t_recovery import bake
build_test1_alias(); build_test1_e2t(); official()
e2t = load_path(EXP/"test1_e2t_dsh.py", "e2t")
stage3 = audit_mod.load("stage3")
CACHE = AUDIT_OUT/"generations_34d6ece55b3c092a.json"
assert CACHE.exists(), "Upload frozen cache into audit_independent/results/"
cache = load_cache(CACHE); assert is_real_qwen_cache(cache)
print("OK setup", platform.platform())
'''
)

md("## B1 — Linux E2T contract (STOP if fail)")
code(
    r'''
tasks = table_tasks(); t0 = tasks[0]
with tempfile.TemporaryDirectory() as td:
    fm = _materialize_all([t0], td)
    H.b1_linux_contract(e2t, stage3, t0, fm)
'''
)

md("## B1 — Cache replay 400 programs (task-level gate)")
code(
    r'''
OUTER = float(os.environ.get("DSH_OUTER_MANY", "7.5"))
gold = {t["id"]: t for t in table_tasks()}
with tempfile.TemporaryDirectory() as td:
    fm = _materialize_all(list(gold.values()), td)
    m = H.b1_cache_replay(e2t, stage3, cache, gold, fm, outer=OUTER)
print(m)
'''
)

md("## B2 — REAL Agent.solve Tables (forced fallback) — GATE PRINCIPAL")
code(
    r'''
import torch
assert torch.cuda.is_available(), "B2 needs CUDA"
import final_pre_test3_debug as D
# MUST set env BEFORE loading E2T module (_force_fallback reads env at solve-time;
# also disable Stage3 table rules explicitly — stock Stage3 has no flag)
os.environ["DSH_FORCE_FALLBACK"] = "1"
os.environ["DSH_OUTER_MANY"] = str(OUTER)
agent_path = bake(outer_many=OUTER)
print("baked", agent_path)
A = audit_mod.load("stage3")
D.disable_table_rules(A)
A._rules_disabled = True
Bmod = H.load_mod(agent_path, "stage3_e2t_rec")
A.MODEL = Bmod.MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
agent_a = A.Agent()
agent_b = Bmod.Agent()
tables = table_tasks()
TD_TABLES = tempfile.mkdtemp(prefix="final_tables_")
fm = _materialize_all(tables, TD_TABLES)
batch_tasks = [{**t, "files": fm[t["id"]]} for t in tables]
# Instrument first batch of 8 — must show deterministic=0, llm_live=8, gen time >> 0
first = batch_tasks[:8]
st_a = D.instrumented_solve(agent_a, A, first, "Stage3")
st_b = D.instrumented_solve(agent_b, Bmod, first, "E2T")
print("B2 instrument Stage3", {k: st_a[k] for k in st_a if k != "answers"})
print("B2 instrument E2T", {k: st_b[k] for k in st_b if k != "answers"})
assert st_a["deterministic_count"] == 0 and st_a["llm_live_count"] == 8, st_a
assert st_b["deterministic_count"] == 0 and st_b["llm_live_count"] == 8, st_b
assert st_a["greedy_generation_seconds"] > 1.0 and st_b["greedy_generation_seconds"] > 1.0, "B2 INVALID: no real LLM"
# Full 80
df_t, sum_t = H.run_solve_compare("Stage3", agent_a, "E2T", agent_b, batch_tasks, batch_size=8, force_fallback=True)
df_t.to_csv(DIAG_OUT/"final_b2_tables.csv", index=False)
print(sum_t)
'''
)

md("## B2b — workload K (optional, cheap stress)")
code(
    r'''
# Quantify overhead only; does not veto unless a batch >40s (harness already STOPS)
Ks = [1, 2, 4, 8]
stress = []
# use first 8 tables; mark K as fallback by FORCE_FALLBACK already on all — simulate K by solving subsets
for K in Ks:
    sub = batch_tasks[:K]
    # pad with deterministic answered dummies? skip — just time K-task solve
    t0 = time.perf_counter(); agent_b.solve(sub); dt = time.perf_counter()-t0
    stress.append(dict(K=K, seconds=dt))
    print("K", K, "s", dt)
    if dt > 40:
        H.stop(f"B2b K={K} >40s")
import pandas as pd
pd.DataFrame(stress).to_csv(DIAG_OUT/"final_b2b_stress.csv", index=False)
H.mark("B2b_stress", **{f"K{s['K']}": s["seconds"] for s in stress})
'''
)

md("## B3 — No-files uncovered by calc_rules")
code(
    r'''
HANDOFF = PROJECT_ROOT/"CODEX_AUDIT_HANDOFF"
all_tasks = json.loads((HANDOFF/"dev.json").read_text(encoding="utf-8"))
nofiles = H.uncovered_nofiles(A, all_tasks)
print("uncovered nofiles", len(nofiles))
assert len(nofiles) >= 20, len(nofiles)
os.environ.pop("DSH_FORCE_FALLBACK", None)  # rules stay; uncovered => fallback naturally
TD_NF = tempfile.mkdtemp(prefix="final_nofiles_")
fm = _materialize_all(nofiles, TD_NF)
nf_tasks = []
for t in nofiles:
    tt = dict(t); tt["files"] = fm[t["id"]]; nf_tasks.append(tt)
df_n, sum_n = H.run_solve_compare("Stage3", agent_a, "E2T", agent_b, nf_tasks, batch_size=8, force_fallback=False)
df_n.to_csv(DIAG_OUT/"final_b3_nofiles.csv", index=False)
print(sum_n)
'''
)

md("## B4 — Static / resource check + BAKE decision")
code(
    r'''
rep = H.b4_static_and_resources(agent_path, AUDIT/"STAGE3_E2T_RECOVERY"/"dsh.py")
# Re-bake fresh zip after all greens
bake(outer_many=OUTER)
H.finalize_ready()
print("Download STAGE3_E2T_RECOVERY.zip and submit TEST3 manually if you accept RECOVERY_READY.")
'''
)

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "T4"},
    },
    "cells": cells,
}
out = HERE / "colab_final_recovery.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", out)

# Redirect old notebooks
for name in ("colab_phase_b1.ipynb", "colab_phase_b2.ipynb"):
    p = HERE / name
    stub = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"}},
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# DEPRECATED\n\nUse **`colab_final_recovery.ipynb`** only.\n\n({name} retired — no more intermediate phases.)\n"
                ],
            }
        ],
    }
    p.write_text(json.dumps(stub, indent=1), encoding="utf-8")
    print("retired", name)
