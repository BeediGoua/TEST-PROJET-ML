"""H2 — P(Ei = E0) semantic agreement on cached Table programs."""
from __future__ import annotations

import platform
import tempfile
import time

from pretest3_common import (
    DIAG_OUT,
    EXP,
    ROOT,
    analyze_code_patterns,
    find_generation_caches,
    install_dsh,
    is_real_qwen_cache,
    load_cache,
    load_path,
    table_tasks,
    values_agree,
    write_csv,
    write_not_run,
)
import audit as audit_mod
from build_experimental import build_e4_importlib, build_test1_alias


def _load_executors():
    build_test1_alias()
    build_e4_importlib()
    # Also ensure faithful exists
    from importlib import import_module

    try:
        import_module("02_executor_contract").build_faithful_copy()
    except Exception:
        pass
    return {
        "E0_stage3": audit_mod.load("stage3"),
        "E1_test1": audit_mod.load("test1"),
        "E2_alias": load_path(EXP / "test1_alias_dsh.py", "e2"),
        "E3_test2": audit_mod.load("test2"),
        "E4_importlib": load_path(EXP / "executor_e4_importlib.py", "e4"),
        "E4_faithful": load_path(EXP / "stage3_faithful_dsh.py", "faithful")
        if (EXP / "stage3_faithful_dsh.py").exists()
        else None,
    }


def _run_one(label, m, code, dfs, obj, timeout=5.0):
    """Return (value, error_str)."""
    try:
        if label.startswith("E0") or label.startswith("E4_importlib"):
            v = m.run_code(code, dfs, timeout, obj)
            err = getattr(m, "LAST_ERR", "") or ""
            return v, err
        if label.startswith("E3"):
            out = m.run_code_batch([dict(code=code, dfs=dfs, obj=obj)], timeout)
            if not out:
                return None, "empty batch"
            return out[0].get("value"), out[0].get("error", "")
        # E1 / E2 / faithful many path with single code
        if hasattr(m, "run_codes_many"):
            vals = m.run_codes_many([code], dfs, timeout, obj)
            v = vals[0] if vals else None
            return v, "" if v is not None else "many returned None"
        v = m.run_code(code, dfs, timeout, obj)
        return v, getattr(m, "LAST_ERR", "") or ""
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def main():
    caches = find_generation_caches()
    if not caches:
        write_not_run(
            DIAG_OUT / "EXECUTOR_AGREEMENT.md",
            "H2 — Executor semantic agreement",
            "No generations_*.json. Produce cache via Colab first.",
        )
        print("NOT RUN: no cache")
        return

    path = caches[0]
    cache = load_cache(path)
    tasks = {t["id"]: t for t in table_tasks()}
    real = is_real_qwen_cache(cache)

    # Limit smoke synthetic to keep Windows runtime reasonable
    programs = cache.get("rows") or []
    if not real and len(programs) > 40:
        programs = programs[:40]

    install_dsh(False)
    execs = _load_executors()
    execs = {k: v for k, v in execs.items() if v is not None}

    from src.evaluation.core import _materialize_all

    detail = []
    # Materialize once
    task_list = [tasks[r["id"]] for r in programs if r["id"] in tasks]
    # unique tasks
    uniq = list({t["id"]: t for t in task_list}.values())

    with tempfile.TemporaryDirectory(prefix="agree_") as td:
        filemap = _materialize_all(uniq, td)
        prep = execs["E0_stage3"]

        # Mutation probe: run E0 twice on first finite program
        mutation_divergent = 0
        mutation_n = 0

        for r in programs:
            tid = r["id"]
            if tid not in tasks:
                continue
            task = tasks[tid]
            code = r.get("code") or ""
            pat = analyze_code_patterns(code)
            dfs, dico = prep.load_task(task["objective"], filemap[tid])
            if len(dfs) >= 2:
                prep.align_keys(dfs, dico)

            # Fresh dfs per executor
            values = {}
            errors = {}
            for label, m in execs.items():
                # E2 already baked with alias; others use plain dsh
                if label == "E2_alias":
                    install_dsh(False)  # alias is in source
                else:
                    install_dsh(False)
                fresh, dd = prep.load_task(task["objective"], filemap[tid])
                if len(fresh) >= 2:
                    prep.align_keys(fresh, dd)
                # E0/E4_importlib don't need dsh
                if label.startswith("E0") or label == "E4_importlib":
                    pass
                else:
                    install_dsh(False)
                v, err = _run_one(label, m, code, fresh, task["objective"])
                values[label] = v
                errors[label] = err

            e0 = values.get("E0_stage3")
            # double-run mutation check
            if e0 is not None and mutation_n < 20:
                fresh2, dd2 = prep.load_task(task["objective"], filemap[tid])
                if len(fresh2) >= 2:
                    prep.align_keys(fresh2, dd2)
                v2, _ = _run_one("E0_stage3", prep, code, fresh2, task["objective"])
                mutation_n += 1
                if not values_agree(e0, v2, float(task.get("tol", 1e-6))):
                    mutation_divergent += 1

            for label in execs:
                if label == "E0_stage3":
                    continue
                agree = values_agree(e0, values[label], float(task.get("tol", 1e-6)))
                detail.append(
                    dict(
                        id=tid,
                        phase=r.get("phase"),
                        sample=r.get("sample"),
                        executor=label,
                        e0_finite=e0 is not None,
                        ei_finite=values[label] is not None,
                        agree=agree,
                        e0=e0,
                        ei=values[label],
                        import_pandas=pat["import_pandas_as_pd"],
                        syntax_ok=pat["syntax_ok"],
                        e0_err=errors.get("E0_stage3", "")[:200],
                        ei_err=errors.get(label, "")[:200],
                    )
                )

    write_csv(DIAG_OUT / "executor_agreement_detail.csv", detail)

    # Aggregate among E0-finite
    summary = []
    for label in execs:
        if label == "E0_stage3":
            continue
        rows = [d for d in detail if d["executor"] == label and d["e0_finite"]]
        n = len(rows)
        agree_n = sum(1 for d in rows if d["agree"])
        rate = agree_n / n if n else 0.0
        # Syntax contagion proxy: when code is syntax-broken, E0 is None; skip.
        # When code is OK and import_pandas, measure E1 fail vs E2 ok
        ip_rows = [d for d in rows if d["import_pandas"]]
        ip_agree = sum(1 for d in ip_rows if d["agree"]) / len(ip_rows) if ip_rows else None
        summary.append(
            dict(
                executor=label,
                n_e0_finite=n,
                agree_n=agree_n,
                agree_rate=rate,
                gate_99=rate >= 0.99,
                import_pandas_n=len(ip_rows),
                import_pandas_agree_rate=ip_agree if ip_agree is not None else "",
            )
        )
    write_csv(DIAG_OUT / "executor_agreement_summary.csv", summary)

    # Syntax isolation probe (4 programs, one broken)
    install_dsh(False)
    contagion = []
    dfs_probe = None
    # use first task dfs
    if uniq:
        with tempfile.TemporaryDirectory(prefix="cont_") as td2:
            fm = _materialize_all(uniq[:1], td2)
            prep = execs["E0_stage3"]
            dfs_probe, _ = prep.load_task(uniq[0]["objective"], fm[uniq[0]["id"]])
            codes = ["answer = 6.0", "answer = (", "answer = 42.0", "answer = 9.0"]
            for label, m in execs.items():
                if label.startswith("E0") or label == "E4_importlib":
                    vals = [m.run_code(c, dfs_probe, 2.0, "") for c in codes]
                elif label.startswith("E3"):
                    batch = m.run_code_batch(
                        [dict(code=c, dfs=dfs_probe, obj="") for c in codes], 5.0
                    )
                    vals = [b.get("value") for b in batch]
                else:
                    install_dsh(False)
                    vals = m.run_codes_many(codes, dfs_probe, 5.0, "")
                # Expected: keep siblings → [6, None, 42, 9]
                ok = (
                    values_agree(vals[0], 6.0)
                    and vals[1] is None
                    and values_agree(vals[2], 42.0)
                    and values_agree(vals[3], 9.0)
                )
                wiped = all(v is None for v in vals)
                contagion.append(
                    dict(executor=label, vals=str(vals), siblings_kept=ok, all_none=wiped)
                )
    write_csv(DIAG_OUT / "executor_syntax_isolation.csv", contagion)

    lines = [
        "# H2 — Executor semantic agreement\n",
        f"**Cache:** `{path.name}` ({'REAL_QWEN' if real else 'SYNTHETIC_OR_PARTIAL'})\n",
        f"**Platform:** {platform.platform()}\n",
        "## Agreement vs E0 (Stage3 exec) among E0-finite programs\n",
        "| Executor | n | agree_rate | ≥99% | import_pandas agree |",
        "|---|---:|---:|---|---:|",
    ]
    e2_ok = False
    for s in summary:
        ip = s["import_pandas_agree_rate"]
        ip_s = f"{ip:.3f}" if ip != "" else "n/a"
        lines.append(
            f"| {s['executor']} | {s['n_e0_finite']} | {s['agree_rate']:.4f} | "
            f"{'PASS' if s['gate_99'] else 'FAIL'} | {ip_s} |"
        )
        if s["executor"] == "E2_alias":
            e2_ok = bool(s["gate_99"])

    lines.append("\n## Syntax isolation (one SyntaxError among 4)\n")
    for c in contagion:
        lines.append(
            f"- `{c['executor']}`: siblings_kept={c['siblings_kept']} all_none={c['all_none']} vals={c['vals']}"
        )

    lines.append("\n## Mutation (E0 double replay)\n")
    lines.append(
        f"- divergent / n = {mutation_divergent} / {mutation_n}\n"
    )
    lines.append("## Gate\n")
    if not real:
        lines.append("- **NOT RUN for GO:** cache is not a real Qwen generation set.\n")
        lines.append("- Local numbers are smoke-only.\n")
    else:
        lines.append(
            f"- E2 alias ≥99%: **{'PASS' if e2_ok else 'FAIL'}**\n"
        )
        lines.append(
            f"- Mutation divergence: **{'PASS' if mutation_divergent == 0 else 'FAIL'}**\n"
        )

    (DIAG_OUT / "EXECUTOR_AGREEMENT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
