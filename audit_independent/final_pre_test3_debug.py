"""Targeted FINAL DEBUG before TEST3 — paste/run on Colab Linux+GPU.

Does not submit. Proves B2 forced-fallback, dumps B3 flips, compares B4 warnings.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "diagnostic" / "results"
OUT.mkdir(parents=True, exist_ok=True)


def disable_table_rules(mod):
    """Force LLM path on historical Stage3 (no FORCE_FALLBACK flag in stock file)."""
    names = [
        "table_stat_rule",
        "table_group_rule",
        "table_join_rule",
        "table_derive_rule",
        "table_filter_rule",
    ]
    for n in names:
        if hasattr(mod, n):
            setattr(mod, n, lambda *a, **k: None)


def instrumented_solve(agent, mod, tasks, label: str):
    """Wrap prep path counters by monkeypatching generate + counting rule hits."""
    stats = dict(
        label=label,
        n_tasks=len(tasks),
        deterministic_count=0,
        llm_live_count=0,
        greedy_generation_seconds=0.0,
        greedy_outputs_count=0,
        repair_count=0,
        sample_outputs_count=0,
        total_seconds=0.0,
    )
    orig_gen = agent.generate
    phase = {"name": "other"}

    def gen_wrap(prompts, n, temp, **kw):
        t0 = time.perf_counter()
        outs = orig_gen(prompts, n, temp, **kw)
        dt = time.perf_counter() - t0
        n_out = sum(len(x) for x in outs) if outs else 0
        if phase["name"] == "greedy":
            stats["greedy_generation_seconds"] += dt
            stats["greedy_outputs_count"] += n_out
        elif phase["name"] == "repair":
            stats["repair_count"] += n_out
        elif phase["name"] == "samples":
            stats["sample_outputs_count"] += n_out
        return outs

    agent.generate = gen_wrap

    # Patch solve internals via wrapping run_round if present — instead count via env hooks
    # Simpler: call solve and infer from generate counters; also pre-scan rules
    for t in tasks:
        files = t.get("files") or []
        kind = mod.route(files)
        if kind == "table" and not (
            os.environ.get("DSH_FORCE_FALLBACK") == "1" or getattr(mod, "_rules_disabled", False)
        ):
            # estimate deterministic without full load if rules still active
            pass

    # Count deterministic by dry-running rule functions when files materialized
    live_ids = []
    det_ids = []
    for t in tasks:
        files = t.get("files") or []
        kind = mod.route(files)
        if kind != "table":
            live_ids.append(t["id"])
            continue
        if os.environ.get("DSH_FORCE_FALLBACK") == "1" or getattr(mod, "_rules_disabled", False):
            live_ids.append(t["id"])
            continue
        dfs, dico = mod.load_task(t["objective"], files)
        hit = None
        for fn in (
            getattr(mod, "table_stat_rule", None),
            getattr(mod, "table_group_rule", None),
            getattr(mod, "table_join_rule", None),
            getattr(mod, "table_derive_rule", None),
            getattr(mod, "table_filter_rule", None),
        ):
            if fn is None:
                continue
            try:
                hit = fn(t["objective"], dfs, dico)
            except Exception:
                hit = None
            if hit is not None and math.isfinite(float(hit)):
                break
        if hit is not None and math.isfinite(float(hit)):
            det_ids.append(t["id"])
        else:
            live_ids.append(t["id"])

    stats["deterministic_count"] = len(det_ids)
    stats["llm_live_count"] = len(live_ids)

    # Instrument Agent.solve phases by temporarily wrapping methods if we patch generate only —
    # Stage3 solve calls generate from nested run_round; we tag phases via sequential wraps.
    orig_solve = agent.solve

    def solve_wrap(batch):
        # Monkeypatch nested functions by rewriting generate tags around full solve:
        # greedy first call(s), then repair, then samples — heuristic on temp/n
        calls = []

        def gen2(prompts, n, temp, **kw):
            if n == 1 and float(temp) == 0.0:
                # could be greedy, continue, or repair — count order
                calls.append("zero_temp")
                if len([c for c in calls if c == "zero_temp"]) == 1:
                    phase["name"] = "greedy"
                else:
                    phase["name"] = "repair"
            else:
                phase["name"] = "samples"
            return gen_wrap(prompts, n, temp, **kw)

        agent.generate = gen2
        t0 = time.perf_counter()
        out = orig_solve(batch)
        stats["total_seconds"] = time.perf_counter() - t0
        agent.generate = orig_gen
        return out

    agent.solve = solve_wrap
    answers = agent.solve(tasks)
    agent.solve = orig_solve
    agent.generate = orig_gen
    stats["answers"] = answers
    return stats


def b4_compare(stage3_path: Path, e2t_path: Path) -> pd.DataFrame:
    import sys

    sys.path.insert(0, str(HERE.parent))
    from src.evaluation.tool_contract import inspect_agent_source

    a = inspect_agent_source(stage3_path)
    b = inspect_agent_source(e2t_path)
    rows = []
    for k in (
        "exec_upload_violation",
        "sympy_prompt_runtime_mismatch",
        "onehot_prompt_runtime_mismatch",
        "no_imports_example_mismatch",
    ):
        rows.append(
            dict(
                warning=k,
                stage3=a.get(k),
                e2t=b.get(k),
                status="INHERITED" if a.get(k) == b.get(k) else ("INTRODUCED_BY_E2T" if b.get(k) and not a.get(k) else "CHANGED"),
            )
        )
    return pd.DataFrame(rows)


def analyze_b3_csv(path: Path) -> dict:
    df = pd.read_csv(path)
    lost = df[(df.a_ok == True) & (df.b_ok == False)]
    gained = df[(df.a_ok == False) & (df.b_ok == True)]
    return dict(df=df, lost=lost, gained=gained)


def classify_counterfactual(s3_val, e2t_val, s3_on_e2t_code, e2t_on_s3_code):
    """Rough classification from counterfactual replay values."""
    if e2t_on_s3_code is not None and s3_val is not None:
        # Stage3 code works on E2T → generation/control for E2T path, not executor incapability
        if abs(float(e2t_on_s3_code) - float(s3_val)) < 1e-6:
            return "GENERATION_OR_CONTROL_FLOW"
    if s3_on_e2t_code is None and e2t_val is None:
        return "GENERATION"
    if s3_on_e2t_code is not None and e2t_val is None:
        return "EXECUTOR"
    if s3_on_e2t_code is None and e2t_val is not None:
        return "GENERATION"
    return "MIXED_OR_TIMING"


if __name__ == "__main__":
    # Local-only: B4 compare + template report
    handoff = HERE.parent / "CODEX_AUDIT_HANDOFF"
    df = b4_compare(handoff / "STAGE3_SUBMITTED_92_5.py", HERE / "STAGE3_E2T_RECOVERY" / "agent.py")
    print(df.to_string(index=False))
    df.to_csv(OUT / "b4_warning_compare.csv", index=False)
