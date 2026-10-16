"""FINAL NO-FILES FIX — one last recovery experiment (Colab GPU).

P0 = current E2T (DSH_RESERVE_ONE_SAMPLE unset)
P1 = reserve-one-sample (DSH_RESERVE_ONE_SAMPLE=1)

Does not submit. Bake zip only when GO condition holds.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "diagnostic" / "results"
OUT.mkdir(parents=True, exist_ok=True)

FLIP_LOSS = ["d_026", "d_065", "d_076", "d_143"]
FLIP_GAIN = ["d_123"]
FLIP_IDS = FLIP_LOSS + FLIP_GAIN


def _near(a, b, tol=1e-6):
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) <= float(tol)
    except Exception:
        return False


def trace_solve(agent, mod, task: dict, label: str) -> dict:
    """Single-task solve with phase/code/result/budget tracing."""
    gold = float(task["answer"])
    tol = float(task.get("tol", 1e-6))
    tid = task["id"]
    obj = task["objective"]

    trace = {
        "task_id": tid,
        "label": label,
        "objective": obj[:200],
        "gold": gold,
        "phases": [],
        "candidates": [],
        "budget_before": {},
        "samples_requested": 0,
        "samples_generated": 0,
        "repair_triggered": False,
        "final_vote": None,
        "final_ok": False,
        "total_seconds": 0.0,
        "stage_win_path": None,
        "e2t_fail_reason": None,
    }

    phase = {"name": "other", "zero_temp_n": 0}
    left_fn = {"fn": None}
    t_solve0 = {"t": None}

    orig_gen = agent.generate
    orig_run = getattr(mod, "run_code", None)
    orig_many = getattr(mod, "run_codes_many", None)
    def budget_left():
        if left_fn["fn"] is not None:
            try:
                return float(left_fn["fn"]())
            except Exception:
                pass
        if t_solve0["t"] is None:
            return None
        try:
            return float(mod.BUDGET) - (time.time() - t_solve0["t"])
        except Exception:
            return None

    def gen_wrap(prompts, n, temp, max_new=500, raw=False, max_time=None):
        temp_f = float(temp)
        if temp_f > 0:
            phase["name"] = "SAMPLE"
            trace["samples_requested"] += int(n) * len(prompts)
        elif raw:
            phase["name"] = "CONTINUATION"
        else:
            phase["zero_temp_n"] += 1
            if phase["zero_temp_n"] == 1:
                phase["name"] = "GREEDY"
            else:
                phase["name"] = "REPAIR"
                trace["repair_triggered"] = True

        bl = budget_left()
        trace["budget_before"].setdefault(phase["name"], bl)
        t0 = time.perf_counter()
        outs = orig_gen(prompts, n, temp, max_new=max_new, raw=raw, max_time=max_time)
        dt = time.perf_counter() - t0
        n_out = sum(len(x) for x in outs) if outs else 0
        if phase["name"] == "SAMPLE":
            trace["samples_generated"] += n_out
        trace["phases"].append(
            dict(
                phase=phase["name"],
                n=n,
                temp=temp_f,
                raw=bool(raw),
                generation_seconds=round(dt, 3),
                outputs=n_out,
                budget_before=bl,
                max_time=max_time,
            )
        )
        return outs

    sample_idx = {"i": 0}

    def record_exec(code, val, err, exec_s, many=False):
        ph = phase["name"]
        src = ph
        if ph == "SAMPLE":
            sample_idx["i"] += 1
            src = f"SAMPLE_{sample_idx['i']}"
        trace["candidates"].append(
            dict(
                source=src,
                phase=ph,
                code=(code or "")[:800],
                result=val,
                error=(err or "")[:300] if val is None else "",
                exec_seconds=round(exec_s, 3),
                many=many,
                matches_gold=_near(val, gold, tol),
            )
        )

    def run_wrap(code, dfs, timeout, obj=""):
        t0 = time.perf_counter()
        v = orig_run(code, dfs, timeout, obj)
        dt = time.perf_counter() - t0
        err = getattr(mod, "LAST_ERR", "") or ""
        record_exec(code, v, err, dt, many=False)
        return v

    def many_wrap(codes, dfs, timeout, obj=""):
        t0 = time.perf_counter()
        vals = orig_many(codes, dfs, timeout, obj)
        dt = time.perf_counter() - t0
        per = dt / max(1, len(codes))
        for c, v in zip(codes, vals):
            record_exec(c, v, "batch None" if v is None else "", per, many=True)
        return vals

    agent.generate = gen_wrap
    if orig_run is not None:
        mod.run_code = run_wrap
    if orig_many is not None:
        mod.run_codes_many = many_wrap

    # Hook left() by wrapping solve: capture t0 via BUDGET math (already in budget_left)
    orig_solve = agent.solve

    def solve_wrap(tasks):
        t_solve0["t"] = time.time()
        return orig_solve(tasks)

    agent.solve = solve_wrap
    t0 = time.perf_counter()
    try:
        out = agent.solve([task])
        ans = float(out[0]["answer"]) if out else 0.0
    except Exception as e:
        ans = 0.0
        trace["error"] = repr(e)
    finally:
        trace["total_seconds"] = round(time.perf_counter() - t0, 3)
        agent.generate = orig_gen
        agent.solve = orig_solve
        if orig_run is not None:
            mod.run_code = orig_run
        if orig_many is not None:
            mod.run_codes_many = orig_many

    trace["final_vote"] = ans
    trace["final_ok"] = abs(ans - gold) <= tol

    # First matching candidate source = win path
    for c in trace["candidates"]:
        if c["matches_gold"]:
            trace["stage_win_path"] = c["source"]
            break
    if trace["stage_win_path"] is None and trace["final_ok"]:
        # Deterministic rule hit (no LLM candidates)
        trace["stage_win_path"] = "DETERMINISTIC_OR_VOTE"

    return trace


def classify_pair(tr_s3: dict, tr_e2t: dict) -> dict:
    """Answer: where Stage3 wins; why E2T fails."""
    win = tr_s3.get("stage_win_path") or "UNKNOWN"
    reason = "OTHER"
    if tr_e2t.get("final_ok"):
        reason = "NONE_E2T_OK"
    elif not tr_e2t.get("candidates"):
        # no exec at all beyond empty
        samp_ph = [p for p in tr_e2t.get("phases", []) if p["phase"] == "SAMPLE"]
        if not samp_ph or sum(p["outputs"] for p in samp_ph) == 0:
            if any(p["phase"] == "REPAIR" for p in tr_e2t.get("phases", [])):
                reason = "SKIPPED_SAMPLE"
            elif tr_e2t.get("total_seconds", 0) > 25:
                reason = "NO_TIME"
            else:
                reason = "SKIPPED_SAMPLE"
        else:
            reason = "GENERATION_DIFFERENCE"
    else:
        e2t_ok_cand = any(c["matches_gold"] for c in tr_e2t["candidates"])
        if e2t_ok_cand and not tr_e2t["final_ok"]:
            reason = "REPAIR_CONTROL"
        elif not e2t_ok_cand:
            samp = [p for p in tr_e2t.get("phases", []) if p["phase"] == "SAMPLE"]
            if not samp or sum(p["generation_seconds"] for p in samp) < 0.05:
                reason = "SKIPPED_SAMPLE"
            elif any("timeout" in (c.get("error") or "").lower() for c in tr_e2t["candidates"]):
                reason = "EXEC_TIMEOUT"
            else:
                reason = "GENERATION_DIFFERENCE"
    return {
        "id": tr_s3["task_id"],
        "stage3_win_path": win,
        "e2t_fail_reason": reason,
        "stage3_ok": tr_s3["final_ok"],
        "e2t_ok": tr_e2t["final_ok"],
        "stage3_vote": tr_s3["final_vote"],
        "e2t_vote": tr_e2t["final_vote"],
        "stage3_sample_gen_s": sum(
            p["generation_seconds"] for p in tr_s3["phases"] if p["phase"] == "SAMPLE"
        ),
        "e2t_sample_gen_s": sum(
            p["generation_seconds"] for p in tr_e2t["phases"] if p["phase"] == "SAMPLE"
        ),
        "stage3_repair": tr_s3["repair_triggered"],
        "e2t_repair": tr_e2t["repair_triggered"],
    }


def evidence_supports_p1(class_rows: list[dict]) -> bool:
    """P1 only if losses are Stage3-sample-saved and E2T skipped/late sampling."""
    losses = [r for r in class_rows if r["id"] in FLIP_LOSS]
    if not losses:
        return False
    sample_saved = 0
    skip_or_late = 0
    for r in losses:
        win = str(r["stage3_win_path"])
        if win.startswith("SAMPLE") or win == "SAMPLE":
            sample_saved += 1
        if r["e2t_fail_reason"] in ("SKIPPED_SAMPLE", "NO_TIME"):
            skip_or_late += 1
    # Require majority of the 4 losses match the hypothesized pattern
    return sample_saved >= 2 and skip_or_late >= 2


def run_b3(agent_a, agent_b, nf_tasks, label_b: str, batch_size: int = 8, stage3_answers=None):
    """If stage3_answers={id: answer} is provided, skip re-solving Stage3 (P1 re-run)."""
    import numpy as np

    rows = []
    solve_times_b = []
    cached_a = dict(stage3_answers or {})
    for start in range(0, len(nf_tasks), batch_size):
        batch = nf_tasks[start : start + batch_size]
        if stage3_answers is None:
            t0 = time.perf_counter()
            ra = agent_a.solve(batch)
            ta = time.perf_counter() - t0
            by_a = {r["id"]: r["answer"] for r in ra}
            cached_a.update(by_a)
        else:
            ta = 0.0
            by_a = {t["id"]: cached_a[t["id"]] for t in batch}
        t0 = time.perf_counter()
        rb = agent_b.solve(batch)
        tb = time.perf_counter() - t0
        solve_times_b.append(tb)
        if ta > 40 or tb > 40:
            print(f"WARN solve >40s: Stage3={ta:.1f}s {label_b}={tb:.1f}s")
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
                    time_a=ta,
                    time_b=tb,
                )
            )
    df = pd.DataFrame(rows)
    st = np.array(solve_times_b, dtype=float)
    summary = dict(
        label_b=label_b,
        n=len(df),
        stage3_acc=float(df.a_ok.mean()),
        e2t_acc=float(df.b_ok.mean()),
        stage3_n=int(df.a_ok.sum()),
        e2t_n=int(df.b_ok.sum()),
        losses=int(((df.a_ok == True) & (df.b_ok == False)).sum()),
        gains=int(((df.a_ok == False) & (df.b_ok == True)).sum()),
        solve_p50=float(np.percentile(st, 50)),
        solve_p95=float(np.percentile(st, 95)),
        solve_max=float(st.max()),
        any_solve_gt40=bool((st > 40).any()),
        stage3_answers=cached_a,
    )
    return df, summary


def write_report(
    class_rows,
    traces,
    p1_applied: bool,
    sum_p0,
    sum_p1,
    go: bool,
    go_reason: str,
):
    path = HERE / "FINAL_NOFILES_FIX.md"
    lines = [
        "# FINAL NO-FILES FIX — one last recovery experiment",
        "",
        f"**Decision: `{'GO_BAKE_AND_STOP' if go else 'RECOVERY_UNSUCCESSFUL_STOP'}`**",
        "",
        f"Reason: {go_reason}",
        "",
        f"P1 applied: {p1_applied}",
        "",
        "## 1. Per-task classification (instrumented single-task)",
        "",
        "| id | Stage3 win path | E2T fail reason | S3 ok | E2T ok | S3 sample_s | E2T sample_s |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for r in class_rows:
        lines.append(
            f"| {r['id']} | {r['stage3_win_path']} | {r['e2t_fail_reason']} | "
            f"{r['stage3_ok']} | {r['e2t_ok']} | {r['stage3_sample_gen_s']:.2f} | "
            f"{r['e2t_sample_gen_s']:.2f} |"
        )
    lines += [
        "",
        "## 2. B3 full (40 uncovered No-files)",
        "",
        "| policy | Stage3 | E2T | losses | gains | p50 | p95 | max | >40s |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    if sum_p0:
        lines.append(
            f"| P0 current | {sum_p0['stage3_n']}/{sum_p0['n']} | {sum_p0['e2t_n']}/{sum_p0['n']} | "
            f"{sum_p0['losses']} | {sum_p0['gains']} | {sum_p0['solve_p50']:.1f} | "
            f"{sum_p0['solve_p95']:.1f} | {sum_p0['solve_max']:.1f} | {sum_p0['any_solve_gt40']} |"
        )
    if sum_p1:
        lines.append(
            f"| P1 reserve-one-sample | {sum_p1['stage3_n']}/{sum_p1['n']} | {sum_p1['e2t_n']}/{sum_p1['n']} | "
            f"{sum_p1['losses']} | {sum_p1['gains']} | {sum_p1['solve_p50']:.1f} | "
            f"{sum_p1['solve_p95']:.1f} | {sum_p1['solve_max']:.1f} | {sum_p1['any_solve_gt40']} |"
        )
    lines += [
        "",
        "## 3. GO condition",
        "",
        "```text",
        "E2T-fixed >= Stage3 on B3",
        "no solve >40s",
        "no new semantic regression (B2 structurally unchanged; scanner clean)",
        "```",
        "",
        "If GO: bake zip with DSH_RESERVE_ONE_SAMPLE baked-in default ON, then STOP.",
        "If FAIL: recovery unsuccessful; no further recovery phases.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    (OUT / "nofiles_fix_classification.json").write_text(
        json.dumps({"class_rows": class_rows, "traces": traces}, indent=2, default=str),
        encoding="utf-8",
    )
    print("wrote", path)
    return path


def decide_go(sum_fixed, stage3_n: int) -> tuple[bool, str]:
    if sum_fixed is None:
        return False, "no fixed B3 summary"
    if sum_fixed["any_solve_gt40"]:
        return False, "solve >40s observed"
    if sum_fixed["e2t_n"] < stage3_n:
        return False, f"E2T-fixed {sum_fixed['e2t_n']} < Stage3 {stage3_n}"
    return True, f"E2T-fixed {sum_fixed['e2t_n']} >= Stage3 {stage3_n}, no solve>40s"


if __name__ == "__main__":
    print("Import final_nofiles_fix on Colab and run COLAB_FINAL_NOFILES_FIX.md cells.")
    print("FLIP_IDS", FLIP_IDS)
