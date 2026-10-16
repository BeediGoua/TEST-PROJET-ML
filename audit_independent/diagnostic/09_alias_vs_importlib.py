"""H3 — bake-off E2 (__dsh_pd alias) vs E4 (importlib / faithful) on same cache."""
from __future__ import annotations

import platform
import tempfile
import time

from pretest3_common import (
    DIAG_OUT,
    EXP,
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


def main():
    caches = find_generation_caches()
    if not caches:
        write_not_run(
            DIAG_OUT / "ALIAS_VS_IMPORTLIB.md",
            "H3 — Alias vs importlib",
            "No generations_*.json. Produce cache via Colab first.",
        )
        print("NOT RUN: no cache")
        return

    path = caches[0]
    cache = load_cache(path)
    real = is_real_qwen_cache(cache)
    build_test1_alias()
    build_e4_importlib()
    try:
        from importlib import import_module

        import_module("02_executor_contract").build_faithful_copy()
    except Exception:
        pass

    e0 = audit_mod.load("stage3")
    e2 = load_path(EXP / "test1_alias_dsh.py", "e2h3")
    e4 = load_path(EXP / "executor_e4_importlib.py", "e4h3")
    faithful = (
        load_path(EXP / "stage3_faithful_dsh.py", "fh3")
        if (EXP / "stage3_faithful_dsh.py").exists()
        else None
    )

    tasks = {t["id"]: t for t in table_tasks()}
    programs = cache.get("rows") or []
    if not real:
        programs = programs[:24]

    from src.evaluation.core import _materialize_all

    detail = []
    timing = []

    with tempfile.TemporaryDirectory(prefix="h3_") as td:
        uniq = list({r["id"]: tasks[r["id"]] for r in programs if r["id"] in tasks}.values())
        filemap = _materialize_all(uniq, td)

        # Agreement slice
        for r in programs:
            tid = r["id"]
            if tid not in tasks:
                continue
            task = tasks[tid]
            code = r.get("code") or ""
            dfs, dico = e0.load_task(task["objective"], filemap[tid])
            if len(dfs) >= 2:
                e0.align_keys(dfs, dico)
            v0 = e0.run_code(code, dfs, 2.0, task["objective"])

            install_dsh(False)
            fresh, _ = e0.load_task(task["objective"], filemap[tid])
            v2 = e2.run_codes_many([code], fresh, 5.0, task["objective"])[0]

            fresh4, _ = e0.load_task(task["objective"], filemap[tid])
            v4 = e4.run_code(code, fresh4, 2.0, task["objective"])

            detail.append(
                dict(
                    id=tid,
                    phase=r.get("phase"),
                    sample=r.get("sample"),
                    e0=v0,
                    e2=v2,
                    e4=v4,
                    e2_agree=values_agree(v0, v2, float(task.get("tol", 1e-6))),
                    e4_agree=values_agree(v0, v4, float(task.get("tol", 1e-6))),
                    e0_finite=v0 is not None,
                )
            )

        # Timing on synthetic programs (same style as 05)
        for n in (1, 4, 8):
            codes_ok = ["import pandas as pd\nanswer = 6.0"] * n
            codes_triv = ["answer = 6.0"] * n
            # need any dfs
            t0 = uniq[0]
            dfs, _ = e0.load_task(t0["objective"], filemap[t0["id"]])
            for name, codes in [("trivial", codes_triv), ("import_pandas", codes_ok)]:
                for label, runner in [
                    ("E2_alias", lambda cs: (install_dsh(False), e2.run_codes_many(cs, dfs, 8.0, ""))[1]),
                    ("E4_importlib", lambda cs: [e4.run_code(c, dfs, 2.0, "") for c in cs]),
                ]:
                    t1 = time.perf_counter()
                    vals = runner(codes)
                    elapsed = time.perf_counter() - t1
                    ok = sum(1 for v in vals if values_agree(v, 6.0))
                    timing.append(
                        dict(agent=label, program=name, n=n, seconds=round(elapsed, 3), ok_count=ok)
                    )
                if faithful is not None:
                    t1 = time.perf_counter()
                    install_dsh(False)
                    vals = faithful.run_codes_many(codes, dfs, 8.0, "")
                    elapsed = time.perf_counter() - t1
                    ok = sum(1 for v in vals if values_agree(v, 6.0))
                    timing.append(
                        dict(
                            agent="E4_faithful",
                            program=name,
                            n=n,
                            seconds=round(elapsed, 3),
                            ok_count=ok,
                        )
                    )

    write_csv(DIAG_OUT / "alias_vs_importlib_detail.csv", detail)
    write_csv(DIAG_OUT / "alias_vs_importlib_timing.csv", timing)

    e0f = [d for d in detail if d["e0_finite"]]
    e2_rate = sum(d["e2_agree"] for d in e0f) / len(e0f) if e0f else 0.0
    e4_rate = sum(d["e4_agree"] for d in e0f) if e0f else 0.0
    e4_rate = e4_rate / len(e0f) if e0f else 0.0

    # Decision rule from plan
    e2_fast = True
    for row in timing:
        if row["agent"] == "E2_alias" and row["n"] == 8 and row["program"] == "import_pandas":
            for row2 in timing:
                if (
                    row2["agent"] in ("E4_importlib", "E4_faithful")
                    and row2["n"] == 8
                    and row2["program"] == "import_pandas"
                ):
                    if row2["seconds"] + 0.5 < row["seconds"]:
                        e2_fast = False
    prefer_e2 = e2_rate >= 0.99 and e2_rate >= e4_rate - 1e-9

    lines = [
        "# H3 — Alias vs importlib bake-off\n",
        f"**Cache:** `{path.name}` ({'REAL_QWEN' if real else 'SYNTHETIC_OR_PARTIAL'})\n",
        f"**Platform:** {platform.platform()}\n",
        "## Agreement vs E0 (E0-finite only)\n",
        f"- E2 alias agree_rate: **{e2_rate:.4f}** (n={len(e0f)})",
        f"- E4 importlib agree_rate: **{e4_rate:.4f}**\n",
        "## Timing snapshot\n",
        "| agent | program | n | seconds | ok |",
        "|---|---|---:|---:|---:|",
    ]
    for t in timing:
        lines.append(
            f"| {t['agent']} | {t['program']} | {t['n']} | {t['seconds']} | {t['ok_count']} |"
        )

    lines.append("\n## Decision\n")
    if not real:
        lines.append(
            "- Cache not real Qwen → decision is **provisional**. "
            "Plan default remains: prefer E2 if ≥99% and faster than E4.\n"
        )
    if prefer_e2 and e2_fast:
        lines.append(
            "- **KEEP E2 (`__dsh_pd` alias)** as sole TEST3-recovery executor change.\n"
        )
        lines.append("- E4 remains correctness oracle only.\n")
    elif e4_rate > e2_rate and e4_rate >= 0.99:
        lines.append(
            "- E4 wins on agreement; still check timing veto (faithful ~36s for n=8 historically).\n"
        )
    else:
        lines.append("- Neither arm clearly passes ≥99% on this corpus — NO-GO for TEST3.\n")

    (DIAG_OUT / "ALIAS_VS_IMPORTLIB.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
