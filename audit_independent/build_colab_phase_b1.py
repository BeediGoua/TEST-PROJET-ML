"""Build colab_phase_b1.ipynb — full B1 gate per Phase B prompt (no submission)."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
cells = []


def md(text):
    cells.append(dict(cell_type="markdown", metadata={}, source=text.splitlines(True)))


def code(text):
    cells.append(
        dict(
            cell_type="code",
            metadata={},
            source=text.splitlines(True),
            execution_count=None,
            outputs=[],
        )
    )


md(
    """# Phase B1 — Linux executor gate (no submission)

Aligned with Phase B prompt: loop isolation → dual E0 → outer sweep → PROGRAM vs TASK metrics.

**Stop before B2** unless loop PASS, zero numeric contamination, task-level vote ≈ 100%.

Forbidden: Qwen3, new prompts, regex, TEST3 upload.
"""
)

md("## 00 — Setup (Linux + official dsh + cache)")
code(
    r'''
from pathlib import Path
import sys, os, platform, json, time, tempfile, signal
assert platform.system() == "Linux", "B1 requires Linux (Colab)"
assert hasattr(signal, "SIGALRM") and hasattr(signal, "setitimer"), "need SIGALRM/setitimer"
PROJECT_ROOT = Path("/content/TEST-PROJET-ML")  # adjust
assert (PROJECT_ROOT / "audit_independent" / "audit.py").exists(), PROJECT_ROOT
AUDIT = PROJECT_ROOT / "audit_independent"
sys.path[:0] = [str(AUDIT), str(PROJECT_ROOT), str(AUDIT / "diagnostic")]
os.chdir(AUDIT)
from build_experimental import build_test1_e2t, build_test1_alias
from gpu_experiments import official
from pretest3_common import EXP, load_path, values_agree, DIAG_OUT, AUDIT_OUT, table_tasks, load_cache, is_real_qwen_cache, write_csv
import audit as audit_mod
from src.evaluation.core import _materialize_all
build_test1_alias(); build_test1_e2t(); official()
e2t = load_path(EXP / "test1_e2t_dsh.py", "e2t")
stage3 = audit_mod.load("stage3")
DIAG_OUT.mkdir(parents=True, exist_ok=True)
CACHE = AUDIT_OUT / "generations_34d6ece55b3c092a.json"
assert CACHE.exists(), "upload frozen cache into audit_independent/results/"
print(platform.platform(), "E2T OK, cache", CACHE.name)
'''
)

md("## 01 — OBLIGATORY loop probe → `[6, None, 42, 9]`")
code(
    r'''
tasks = table_tasks(); t0 = tasks[0]
with tempfile.TemporaryDirectory() as td:
    fm = _materialize_all([t0], td)
    dfs, dico = stage3.load_task(t0["objective"], fm[t0["id"]])
    if len(dfs) >= 2: stage3.align_keys(dfs, dico)
    vals = e2t.run_codes_many(
        ["answer = 6.0", "while True:\n    pass\n", "answer = 42.0", "answer = 9.0"],
        dfs, 8.0, t0["objective"])
print("loop:", vals)
assert values_agree(vals[0], 6.0) and vals[1] is None and values_agree(vals[2], 42.0) and values_agree(vals[3], 9.0), vals
print("PASS loop isolation")
'''
)

md("## 02 — Isolation probes (siblings must survive)")
code(
    r'''
key = list(dfs.keys())[0]
col = list(dfs[key].columns)[0]
orig_len = float(len(dfs[key]))
probe_rows = []
def check(name, codes, pred):
    v = e2t.run_codes_many(codes, dfs, 8.0, t0["objective"])
    ok = bool(pred(v))
    probe_rows.append(dict(probe=name, ok=ok, detail=str(v)))
    print(name, ok, v)
    assert ok, (name, v)

check("syntax_middle",
      ["answer = 6.0", "answer = (", "answer = 42.0", "answer = 9.0"],
      lambda v: values_agree(v[0],6) and v[1] is None and values_agree(v[2],42) and values_agree(v[3],9))
check("runtime_middle",
      ["answer = 6.0", "raise RuntimeError('x')", "answer = 42.0", "answer = 9.0"],
      lambda v: values_agree(v[0],6) and v[1] is None and values_agree(v[2],42) and values_agree(v[3],9))
check("import_pandas", ["import pandas as pd\nanswer = 6.0"], lambda v: values_agree(v[0],6))
check("mutation",
      [f'dfs["{key}"] = dfs["{key}"].head(0)\nanswer = 1.0', f'answer = float(len(dfs["{key}"]))'],
      lambda v: values_agree(v[0],1) and values_agree(v[1], orig_len))
check("smartframe_col", [f'answer = float(len(dfs["{key}"]["{col}"]))'], lambda v: v[0] is not None)
check("read_csv_smoke", ['answer = float(list(dfs.values())[0].shape[0])'], lambda v: v[0] is not None)
write_csv(DIAG_OUT / "b1_probes.csv", probe_rows)
print("PASS all isolation probes")
'''
)

md(
    """## 03 — Outer sweep (do NOT freeze 6.5)

Per-candidate always 1.5s (SIGALRM). Outers: 6.5, 7.0, 7.5, 8.0.

References:
- `E0_semantic` timeout=15
- `E0_production` timeout=1.5 (= Stage3 EXEC_TIMEOUT)

Metrics per outer: PROGRAM agree (sem/prod), #None, candidates executed (finite E2T),
task-level vote agree, final accuracy (gold), p50/p95/max batch time.
All divergences logged with runtimes + timeout_reason.
"""
)
code(
    r'''
from collections import defaultdict
import pandas as pd

cache = load_cache(CACHE); assert is_real_qwen_cache(cache)
by_id = defaultdict(list)
for r in cache["rows"]:
    by_id[r["id"]].append(r)
gold = {t["id"]: t for t in table_tasks()}
OUTERS = [6.5, 7.0, 7.5, 8.0]
E0_SEM, E0_PROD = 15.0, 1.5

def vote(vals, obj):
    cands = [(v, 1.5 if i == 0 else 1.0) for i, v in enumerate(vals) if v is not None]
    nd = stage3.decimals(obj)
    vv = stage3.vote(cands, nd) if cands else None
    if nd is not None and vv is not None:
        try: vv = round(vv, nd)
        except Exception: pass
    return vv

summary, divergences = [], []
with tempfile.TemporaryDirectory() as td:
    uniq = [gold[i] for i in by_id if i in gold]
    fm = _materialize_all(uniq, td)
    for outer in OUTERS:
        n_sem = n_prod = agr_sem = agr_prod = 0
        none_e2t = exec_cand = 0
        task_vote_agree = final_acc_e0 = final_acc_e2t = task_n = 0
        bad_numeric = 0
        times = []
        for tid, gens in by_id.items():
            if tid not in gold: continue
            task = gold[tid]
            ordered = [g for g in gens if g["phase"] == "greedy"] + sorted(
                [g for g in gens if g["phase"] == "samples"], key=lambda x: int(x.get("sample", 0)))
            codes = [g.get("code") or "" for g in ordered]
            e0s, e0p, rts_sem, rts_prod = [], [], [], []
            for c in codes:
                fr, _ = stage3.load_task(task["objective"], fm[tid])
                if len(fr) >= 2: stage3.align_keys(fr, _)
                t0 = time.perf_counter(); e0s.append(stage3.run_code(c, fr, E0_SEM, task["objective"])); rts_sem.append(time.perf_counter() - t0)
                fr2, _ = stage3.load_task(task["objective"], fm[tid])
                if len(fr2) >= 2: stage3.align_keys(fr2, _)
                t0 = time.perf_counter(); e0p.append(stage3.run_code(c, fr2, E0_PROD, task["objective"])); rts_prod.append(time.perf_counter() - t0)
            dfs, _ = stage3.load_task(task["objective"], fm[tid])
            if len(dfs) >= 2: stage3.align_keys(dfs, _)
            t0 = time.perf_counter()
            ev = e2t.run_codes_many(codes, dfs, outer, task["objective"])
            batch_rt = time.perf_counter() - t0
            times.append(batch_rt)
            while len(ev) < len(codes): ev.append(None)
            none_e2t += sum(v is None for v in ev)
            exec_cand += sum(v is not None for v in ev)
            for i in range(len(codes)):
                if e0s[i] is not None:
                    n_sem += 1; agr_sem += int(values_agree(e0s[i], ev[i]))
                    if ev[i] is not None and not values_agree(e0s[i], ev[i]):
                        bad_numeric += 1
                if e0p[i] is not None:
                    n_prod += 1; agr_prod += int(values_agree(e0p[i], ev[i]))
                if not values_agree(e0p[i], ev[i]) or not values_agree(e0s[i], ev[i]):
                    reason = ""
                    if ev[i] is None and e0p[i] is not None: reason = "e2t_none_but_e0_prod_finite"
                    elif ev[i] is None and e0s[i] is not None and e0p[i] is None: reason = "e0_prod_would_also_drop"
                    elif ev[i] is not None and e0s[i] is not None and not values_agree(ev[i], e0s[i]): reason = "numeric_mismatch"
                    else: reason = "both_none_or_other"
                    divergences.append(dict(
                        outer=outer, id=tid, phase=ordered[i]["phase"], sample=ordered[i].get("sample"),
                        e0_semantic_rt=rts_sem[i], e0_production_rt=rts_prod[i], e2t_batch_rt=batch_rt,
                        e0_semantic=e0s[i], e0_production=e0p[i], e2t=ev[i], timeout_reason=reason))
            vs, ve = vote(e0p, task["objective"]), vote(ev, task["objective"])
            tol = float(task["tol"]); ans = float(task["answer"])
            task_n += 1
            task_vote_agree += int(values_agree(vs, ve, tol))
            final_acc_e0 += int(vs is not None and abs(vs - ans) <= tol)
            final_acc_e2t += int(ve is not None and abs(ve - ans) <= tol)
        times = sorted(times)
        def q(p): return times[min(len(times)-1, max(0, int(round(p * (len(times)-1)))))]
        summary.append(dict(
            outer=outer,
            PROGRAM_agree_E0_semantic=agr_sem / n_sem if n_sem else None,
            PROGRAM_agree_E0_production=agr_prod / n_prod if n_prod else None,
            none_e2t=none_e2t, candidates_executed=exec_cand,
            bad_numeric_vs_semantic=bad_numeric,
            TASK_vote_agree=task_vote_agree / task_n,
            final_accuracy_E0_production=final_acc_e0 / task_n,
            final_accuracy_E2T=final_acc_e2t / task_n,
            p50=q(0.5), p95=q(0.95), max=times[-1],
        ))

print(pd.DataFrame(summary).to_string(index=False))
pd.DataFrame(summary).to_csv(DIAG_OUT / "b1_outer_sweep_summary.csv", index=False)
pd.DataFrame(divergences).to_csv(DIAG_OUT / "b1_all_divergences.csv", index=False)
focus = [d for d in divergences if d["id"] in ("d_041", "d_100", "d_170")]
pd.DataFrame(focus).to_csv(DIAG_OUT / "b1_focus_d041_d100_d170.csv", index=False)
print("divergences", len(divergences), "focus", len(focus), "bad_numeric", sum(s["bad_numeric_vs_semantic"] for s in summary))
'''
)

md(
    """## 04 — B1 verdict cell (fill after run)

Require:
- loop PASS
- bad_numeric == 0 for chosen outer
- TASK_vote_agree as close as possible to 1.0
- PROGRAM ≥ 0.99 desirable but secondary to task-level

Choose outer as compromise under BUDGET=29 (not the one that artificially hits 100%).

Then download `diagnostic/results/b1_*.csv` and only then open B2.
"""
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
out = HERE / "colab_phase_b1.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", out)
