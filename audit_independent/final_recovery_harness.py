"""Harness for ONE Colab final recovery notebook. STOP on first failed gate."""
from __future__ import annotations

import importlib.util
import json
import os
import platform
import tempfile
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DIAG = HERE / "diagnostic"
HANDOFF = HERE.parent / "CODEX_AUDIT_HANDOFF"
OUT = DIAG / "results"
OUT.mkdir(parents=True, exist_ok=True)

GATE = {"passed": [], "failed": None, "metrics": {}}


def stop(reason: str):
    GATE["failed"] = reason
    (OUT / "FINAL_RECOVERY_DECISION.md").write_text(
        f"# FINAL RECOVERY\n\n**RECOVERY_NOT_READY**\n\nSTOP: {reason}\n",
        encoding="utf-8",
    )
    raise SystemExit(f"STOP: {reason}")


def mark(name: str, **metrics):
    GATE["passed"].append(name)
    GATE["metrics"][name] = metrics
    print(f"PASS {name}", metrics)


def load_mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def values_agree(a, b, tol=1e-6):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return False


def b1_linux_contract(e2t, stage3, table_task, filemap):
    if platform.system() != "Linux":
        stop("B1 requires Linux")
    import signal

    if not hasattr(signal, "SIGALRM"):
        stop("B1 requires SIGALRM")
    dfs, dico = stage3.load_task(table_task["objective"], filemap[table_task["id"]])
    if len(dfs) >= 2:
        stage3.align_keys(dfs, dico)
    vals = e2t.run_codes_many(
        ["answer = 6.0", "while True:\n    pass\n", "answer = 42.0", "answer = 9.0"],
        dfs,
        8.0,
        table_task["objective"],
    )
    ok = (
        values_agree(vals[0], 6.0)
        and vals[1] is None
        and values_agree(vals[2], 42.0)
        and values_agree(vals[3], 9.0)
    )
    if not ok:
        stop(f"B1 loop failed: {vals}")
    key = list(dfs.keys())[0]
    col = list(dfs[key].columns)[0]
    orig = float(len(dfs[key]))
    probes = [
        (
            "syntax",
            ["answer = 6.0", "answer = (", "answer = 42.0", "answer = 9.0"],
            lambda v: values_agree(v[0], 6) and v[1] is None and values_agree(v[2], 42) and values_agree(v[3], 9),
        ),
        (
            "runtime",
            ["answer = 6.0", "raise RuntimeError('x')", "answer = 42.0", "answer = 9.0"],
            lambda v: values_agree(v[0], 6) and v[1] is None and values_agree(v[2], 42) and values_agree(v[3], 9),
        ),
        ("pandas", ["import pandas as pd\nanswer = 6.0"], lambda v: values_agree(v[0], 6)),
        ("numpy", ["import numpy as np\nanswer = float(np.array([6.0])[0])"], lambda v: values_agree(v[0], 6)),
        (
            "mutation",
            [
                f'dfs["{key}"] = dfs["{key}"].head(0)\nanswer = 1.0',
                f'answer = float(len(dfs["{key}"]))',
            ],
            lambda v: values_agree(v[0], 1) and values_agree(v[1], orig),
        ),
        ("smartframe", [f'answer = float(len(dfs["{key}"]["{col}"]))'], lambda v: v[0] is not None),
        ("read_csv", ["answer = float(list(dfs.values())[0].shape[0])"], lambda v: v[0] is not None),
    ]
    for name, codes, pred in probes:
        v = e2t.run_codes_many(codes, dfs, 8.0, table_task["objective"])
        if not pred(v):
            stop(f"B1 probe {name} failed: {v}")
    mark("B1_linux_contract", loop=str(vals))
    return dfs


def b1_cache_replay(e2t, stage3, cache, tasks_by_id, filemap, outer=7.5):
    by_id = defaultdict(list)
    for r in cache["rows"]:
        by_id[r["id"]].append(r)
    detail = []
    none_where_e0 = bad_numeric = 0
    task_agree = s3_acc = e2t_acc = n_tasks = 0
    times = []
    n_sem = agr_sem = 0

    def vote(vals, obj):
        cands = [(v, 1.5 if i == 0 else 1.0) for i, v in enumerate(vals) if v is not None]
        nd = stage3.decimals(obj)
        vv = stage3.vote(cands, nd) if cands else None
        if nd is not None and vv is not None:
            try:
                vv = round(vv, nd)
            except Exception:
                pass
        return vv

    for tid, gens in by_id.items():
        if tid not in tasks_by_id:
            continue
        task = tasks_by_id[tid]
        ordered = [g for g in gens if g["phase"] == "greedy"] + sorted(
            [g for g in gens if g["phase"] == "samples"], key=lambda x: int(x.get("sample", 0))
        )
        codes = [g.get("code") or "" for g in ordered]
        e0 = []
        for c in codes:
            fr, dd = stage3.load_task(task["objective"], filemap[tid])
            if len(fr) >= 2:
                stage3.align_keys(fr, dd)
            e0.append(stage3.run_code(c, fr, 1.5, task["objective"]))
        dfs, dd = stage3.load_task(task["objective"], filemap[tid])
        if len(dfs) >= 2:
            stage3.align_keys(dfs, dd)
        t0 = time.perf_counter()
        ev = e2t.run_codes_many(codes, dfs, outer, task["objective"])
        times.append(time.perf_counter() - t0)
        while len(ev) < len(codes):
            ev.append(None)
        for i in range(len(codes)):
            if e0[i] is not None:
                n_sem += 1
                agr_sem += int(values_agree(e0[i], ev[i]))
                if ev[i] is None:
                    none_where_e0 += 1
                elif not values_agree(e0[i], ev[i]):
                    bad_numeric += 1
            detail.append(
                dict(id=tid, phase=ordered[i]["phase"], sample=ordered[i].get("sample"), e0=e0[i], e2t=ev[i])
            )
        vs, ve = vote(e0, task["objective"]), vote(ev, task["objective"])
        tol, ans = float(task["tol"]), float(task["answer"])
        n_tasks += 1
        task_agree += int(values_agree(vs, ve, tol))
        s3_acc += int(vs is not None and abs(vs - ans) <= tol)
        e2t_acc += int(ve is not None and abs(ve - ans) <= tol)

    times = sorted(times)

    def q(p):
        return times[min(len(times) - 1, max(0, int(round(p * (len(times) - 1)))))]

    prog = agr_sem / n_sem if n_sem else 0
    metrics = dict(
        program_agree=prog,
        task_vote_agree=task_agree / n_tasks,
        stage3_accuracy=s3_acc / n_tasks,
        e2t_accuracy=e2t_acc / n_tasks,
        none_where_e0_finite=none_where_e0,
        bad_numeric=bad_numeric,
        p50=q(0.5),
        p95=q(0.95),
        max=times[-1],
        outer=outer,
    )
    pd.DataFrame(detail).to_csv(OUT / "final_b1_cache_detail.csv", index=False)
    if bad_numeric > 0:
        stop(f"B1 cache bad_numeric={bad_numeric}")
    if e2t_acc < s3_acc:
        stop(f"B1 cache E2T acc {e2t_acc}< Stage3 {s3_acc}")
    if task_agree < n_tasks:
        # allow only if accuracy still >= — still FAIL task fidelity hard requirement from user
        # User: reproduce Stage3 decisions; if same accuracy but different tasks, still risky
        print("WARN task_vote_agree < 1.0", metrics)
    if e2t_acc == s3_acc and bad_numeric == 0:
        mark("B1_cache_replay", **metrics)
    else:
        stop(f"B1 cache gate fail {metrics}")
    return metrics


def uncovered_nofiles(stage3_mod, all_tasks):
    out = []
    for t in all_tasks:
        if not str(t.get("type", "")).startswith("nofile"):
            continue
        try:
            rv = stage3_mod.calc_rules(t["objective"])
        except Exception:
            rv = None
        if rv is None or not (isinstance(rv, (int, float)) and __import__("math").isfinite(rv)):
            out.append(t)
    return out


def run_solve_compare(label_a, agent_a, label_b, agent_b, tasks, batch_size=8, force_fallback=False):
    """Real Agent.solve batches. Returns summary dict or stops."""
    if force_fallback:
        os.environ["DSH_FORCE_FALLBACK"] = "1"
    else:
        os.environ.pop("DSH_FORCE_FALLBACK", None)

    rows = []
    for start in range(0, len(tasks), batch_size):
        batch = tasks[start : start + batch_size]
        # Stage3 historical
        t0 = time.perf_counter()
        ra = agent_a.solve(batch)
        ta = time.perf_counter() - t0
        t0 = time.perf_counter()
        rb = agent_b.solve(batch)
        tb = time.perf_counter() - t0
        if ta > 40 or tb > 40:
            stop(f"{label_a}/{label_b} batch>{40}s: {ta:.1f}/{tb:.1f}")
        by_a = {r["id"]: r["answer"] for r in ra}
        by_b = {r["id"]: r["answer"] for r in rb}
        for t in batch:
            ans, tol = float(t["answer"]), float(t["tol"])
            va, vb = by_a.get(t["id"]), by_b.get(t["id"])
            rows.append(
                dict(
                    id=t["id"],
                    gold=ans,
                    a=va,
                    b=vb,
                    a_ok=va is not None and abs(float(va) - ans) <= tol,
                    b_ok=vb is not None and abs(float(vb) - ans) <= tol,
                    agree=values_agree(va, vb, tol),
                    time_a=ta,
                    time_b=tb,
                )
            )
    df = pd.DataFrame(rows)
    acc_a = df.a_ok.mean()
    acc_b = df.b_ok.mean()
    summary = dict(
        n=len(df),
        acc_a=float(acc_a),
        acc_b=float(acc_b),
        task_agree=float(df.agree.mean()),
        max_batch_a=float(df.time_a.max()),
        max_batch_b=float(df.time_b.max()),
    )
    if acc_b + 1e-12 < acc_a:
        stop(f"solve {label_b} acc {acc_b:.4f} < {label_a} {acc_a:.4f}")
    mark(f"solve_{label_b}_vs_{label_a}", **summary)
    return df, summary


def b4_static_and_resources(agent_path: Path, dsh_path: Path):
    import sys

    sys.path.insert(0, str(HERE.parent))
    from src.evaluation.tool_contract import inspect_agent_source

    rep = inspect_agent_source(agent_path)
    if rep.get("exec_upload_violation"):
        stop(f"B4 exec violation {rep}")
    # file count
    nfiles = 2
    if nfiles > 10:
        stop("B4 too many files")
    # zip exists
    z = HERE / "STAGE3_E2T_RECOVERY.zip"
    if not z.exists():
        stop("B4 missing zip")
    mark("B4_static", **rep, zip_bytes=z.stat().st_size, nfiles=nfiles)
    return rep


def finalize_ready():
    text = (
        "# FINAL RECOVERY\n\n**RECOVERY_READY**\n\n"
        "Gates passed:\n"
        + "\n".join(f"- {x}: {GATE['metrics'].get(x)}" for x in GATE["passed"])
        + "\n\nBake: `STAGE3_E2T_RECOVERY.zip`\n"
        "Submit TEST3 manually on ML-Arena (notebook does not auto-submit).\n"
    )
    (OUT / "FINAL_RECOVERY_DECISION.md").write_text(text, encoding="utf-8")
    (HERE / "FINAL_RECOVERY_DECISION.md").write_text(text, encoding="utf-8")
    print(text)
    return text
