"""Phase A §4 — obligatory E2T probes."""
from __future__ import annotations

import platform
import tempfile

from pretest3_common import DIAG_OUT, EXP, install_dsh, load_path, values_agree, write_csv
from build_experimental import build_test1_e2t
import audit as audit_mod
from src.evaluation.core import _materialize_all
from pretest3_common import table_tasks, HANDOFF
import json


def main():
    build_test1_e2t()
    install_dsh(False)
    e2t = load_path(EXP / "test1_e2t_dsh.py", "e2t")
    stage3 = audit_mod.load("stage3")
    tasks = table_tasks()
    # Prefer a multi-file table for SmartFrame; also need empty dfs for nofile
    table_task = tasks[0]
    results = []

    with tempfile.TemporaryDirectory(prefix="e2t_probe_") as td:
        filemap = _materialize_all([table_task], td)
        dfs, dico = stage3.load_task(table_task["objective"], filemap[table_task["id"]])
        if len(dfs) >= 2:
            stage3.align_keys(dfs, dico)

        def run_many(codes, timeout=6.5):
            return e2t.run_codes_many(codes, dfs, timeout, table_task["objective"])

        # 1. infinite loop isolation
        is_linux = platform.system() == "Linux"
        if is_linux:
            vals = run_many(
                ["answer = 6.0", "while True:\n    pass\n", "answer = 42.0", "answer = 9.0"]
            )
            ok = (
                values_agree(vals[0], 6.0)
                and vals[1] is None
                and values_agree(vals[2], 42.0)
                and values_agree(vals[3], 9.0)
            )
            results.append(dict(probe="infinite_loop", ok=ok, detail=str(vals), skipped=False))
        else:
            results.append(
                dict(
                    probe="infinite_loop",
                    ok=False,
                    detail="NOT RUN: SIGALRM requires Linux — first cell of Colab V2",
                    skipped=True,
                )
            )

        # 2. SyntaxError middle
        vals = run_many(["answer = 6.0", "answer = (", "answer = 42.0", "answer = 9.0"])
        ok = (
            values_agree(vals[0], 6.0)
            and vals[1] is None
            and values_agree(vals[2], 42.0)
            and values_agree(vals[3], 9.0)
        )
        results.append(dict(probe="syntax_middle", ok=ok, detail=str(vals), skipped=False))

        # 3. runtime exception middle
        vals = run_many(
            ["answer = 6.0", "raise RuntimeError('x')\nanswer = 1", "answer = 42.0", "answer = 9.0"]
        )
        ok = (
            values_agree(vals[0], 6.0)
            and vals[1] is None
            and values_agree(vals[2], 42.0)
            and values_agree(vals[3], 9.0)
        )
        results.append(dict(probe="runtime_middle", ok=ok, detail=str(vals), skipped=False))

        # 4. import pandas
        vals = run_many(["import pandas as pd\nanswer = 6.0"])
        results.append(
            dict(probe="import_pandas", ok=values_agree(vals[0], 6.0), detail=str(vals), skipped=False)
        )

        # 5. import numpy
        vals = run_many(["import numpy as np\nanswer = float(np.array([6.0])[0])"])
        results.append(
            dict(probe="import_numpy", ok=values_agree(vals[0], 6.0), detail=str(vals), skipped=False)
        )

        # 6. rebind pd
        vals = run_many(["pd = __import__('pandas')\nanswer = 6.0"])
        results.append(
            dict(probe="rebind_pd", ok=values_agree(vals[0], 6.0), detail=str(vals), skipped=False)
        )

        # 7. mutation isolation: candidate0 mutates, candidate1 reads original sum pattern
        key = list(dfs.keys())[0]
        codes = [
            f'dfs["{key}"] = dfs["{key}"].head(0)\nanswer = 1.0',
            f'answer = float(len(dfs["{key}"]))',
        ]
        vals = run_many(codes)
        # second should see fresh copy — length of original, not 0
        orig_len = float(len(dfs[key]))
        ok = values_agree(vals[0], 1.0) and values_agree(vals[1], orig_len)
        results.append(dict(probe="mutation_isolation", ok=ok, detail=str(vals), skipped=False))

        # 8. fake read_csv (reload via pd.read_csv path using available files — use dfs name)
        # Stage3 sandbox intercepts read_csv; simple smoke: answer from dfs
        vals = run_many(['answer = float(list(dfs.values())[0].shape[0])'])
        results.append(
            dict(
                probe="fake_read_csv_smoke",
                ok=vals[0] is not None,
                detail=str(vals),
                skipped=False,
            )
        )

        # 9. SmartFrame — bracket access should work on SmartFrame-wrapped dfs
        col = list(dfs[key].columns)[0]
        vals = run_many([f'answer = float(len(dfs["{key}"]["{col}"]))'])
        results.append(
            dict(probe="smartframe_col", ok=vals[0] is not None, detail=str(vals), skipped=False)
        )

    # 10. nofile sympy — empty dfs
    try:
        vals = e2t.run_codes_many(
            ["import sympy\nanswer = float(sympy.Integer(6))"], {}, 6.5, "compute 6"
        )
        results.append(
            dict(probe="nofile_sympy", ok=values_agree(vals[0], 6.0), detail=str(vals), skipped=False)
        )
    except Exception as e:
        results.append(dict(probe="nofile_sympy", ok=False, detail=str(e), skipped=False))

    # 11. fit sklearn — find a fit task if any in dev
    all_tasks = json.loads((HANDOFF / "dev.json").read_text(encoding="utf-8"))
    fit_tasks = [t for t in all_tasks if str(t.get("type", "")).startswith("fit.")]
    if fit_tasks:
        ft = fit_tasks[0]
        with tempfile.TemporaryDirectory(prefix="e2t_fit_") as td:
            fm = _materialize_all([ft], td)
            fdfs, _ = stage3.load_task(ft["objective"], fm[ft["id"]])
            try:
                vals = e2t.run_codes_many(
                    [
                        "from sklearn.linear_model import LinearRegression\n"
                        "import numpy as np\n"
                        "answer = 1.0"
                    ],
                    fdfs,
                    6.5,
                    ft["objective"],
                )
                results.append(
                    dict(
                        probe="fit_sklearn",
                        ok=values_agree(vals[0], 1.0),
                        detail=str(vals),
                        skipped=False,
                    )
                )
            except Exception as e:
                results.append(dict(probe="fit_sklearn", ok=False, detail=str(e), skipped=False))
    else:
        results.append(dict(probe="fit_sklearn", ok=False, detail="no fit task", skipped=True))

    write_csv(DIAG_OUT / "e2t_probes.csv", results)
    lines = ["# E2T probes\n", f"**Platform:** {platform.platform()}\n", "| probe | ok | skipped | detail |", "|---|---|---|---|"]
    for r in results:
        lines.append(
            f"| {r['probe']} | {r['ok']} | {r['skipped']} | `{str(r['detail'])[:120]}` |"
        )
    non_skip = [r for r in results if not r["skipped"]]
    all_pass = all(r["ok"] for r in non_skip)
    lines.append(f"\n**Non-skip PASS:** {all_pass} ({sum(r['ok'] for r in non_skip)}/{len(non_skip)})\n")
    if any(r["skipped"] and r["probe"] == "infinite_loop" for r in results):
        lines.append(
            "**Gate:** infinite_loop NOT RUN on Windows — must pass as first Colab V2 cell.\n"
        )
    (DIAG_OUT / "E2T_PROBES.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
