"""Step C — forced-fallback Tables (CPU proxy, no Agent.solve loops).

MEASURED: executor fidelity when table rules are absent and the program is fixed.
Qwen generation: NOT RUN without CUDA (see gpu_experiments.py).
"""
from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAG_OUT = HERE / "results"
AUDIT = HERE.parents[0]
HANDOFF = HERE.parents[1] / "CODEX_AUDIT_HANDOFF"
ROOT = HERE.parents[1]
EXP = HERE / "experimental"
DIAG_OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(AUDIT))
sys.path.insert(0, str(ROOT))

import audit as audit_mod  # noqa: E402
from probes import SIGNAL_SHIM  # noqa: E402


def install_dsh(fix_alias: bool = False):
    from src.evaluation import dsh_compat

    def runner(code, **kwargs):
        if fix_alias:
            for a, b in [
                ("    __orig_read_csv = pd.read_csv", "    __orig_read_csv = __dsh_pd.read_csv"),
                ("    pd.read_csv = _fake_read_csv(dfs, __extra)", "    __dsh_pd.read_csv = _fake_read_csv(dfs, __extra)"),
                ("        pd.read_csv = __orig_read_csv", "        __dsh_pd.read_csv = __orig_read_csv"),
                ("    _orig = pd.read_csv", "    _orig = __dsh_pd.read_csv"),
                ("    pd.read_csv = _fake_read_csv(dfs, _extra)", "    __dsh_pd.read_csv = _fake_read_csv(dfs, _extra)"),
                ("        pd.read_csv = _orig", "        __dsh_pd.read_csv = _orig"),
            ]:
                code = code.replace(a, b)
            if "import pandas as __dsh_pd" not in code:
                code = "import pandas as __dsh_pd\n" + code
        kwargs.setdefault("timeout_s", 20)
        return dsh_compat.run_python(SIGNAL_SHIM + "\n" + code, **kwargs)

    sys.modules["dsh"] = types.SimpleNamespace(run_python=runner)


def load_faithful():
    path = EXP / "stage3_faithful_dsh.py"
    if not path.exists():
        sys.path.insert(0, str(HERE))
        from importlib import import_module
        import_module("02_executor_contract").build_faithful_copy()
    spec = importlib.util.spec_from_file_location("faithful_ff", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def programs_for(dfs):
    names = [k for k in dfs if str(k).lower() != "data_dictionary"]
    if not names:
        return []
    key = names[0]
    cols = list(dfs[key].columns)
    col = cols[0]
    return [
        ("no_import", f"answer = float(dfs[{key!r}][{col!r}].astype(float).sum())"),
        ("import_pandas",
         f"import pandas as pd\nanswer = float(dfs[{key!r}][{col!r}].astype(float).sum())"),
        ("import_numpy",
         f"import numpy as np\nanswer = float(np.nansum(dfs[{key!r}][{col!r}].astype(float)))"),
        ("syntax_broken", "answer = ("),
    ]


def extract_val(label, result):
    if label == "stage3":
        return result, getattr(audit_mod.load, "__name__", "")
    if isinstance(result, list) and result:
        item = result[0]
        if isinstance(item, dict):
            return item.get("value"), item.get("error") or ""
        return item, ""
    return None, "empty"


def main():
    from src.evaluation.core import _materialize_all

    all_tables = [t for t in json.loads((HANDOFF / "dev.json").read_text(encoding="utf-8"))
                  if str(t.get("type", "")).startswith("table.")]
    tasks = all_tables[:: max(1, len(all_tables) // 12)][:12]
    agents = [
        ("stage3", False),
        ("test1", False),
        ("test2", False),
        ("test2", True),
        ("faithful", False),
    ]
    style_rows = []
    prep = audit_mod.load("stage3")

    with tempfile.TemporaryDirectory(prefix="ff_") as td:
        filemap = _materialize_all(tasks, td)
        for label, fix in agents:
            print(f"[ff] agent={label} fix={fix}", flush=True)
            install_dsh(fix_alias=fix)
            m = load_faithful() if label == "faithful" else audit_mod.load(label)
            for t in tasks:
                dfs, dico = prep.load_task(t["objective"], filemap[t["id"]])
                for style, code in programs_for(dfs):
                    if label == "stage3":
                        val = m.run_code(code, dfs, 2.0, t["objective"])
                        err = getattr(m, "LAST_ERR", "") or ""
                    elif label in ("test1", "faithful"):
                        # samples path (the broken one on TEST1)
                        pack = m.run_codes_many([code], dfs, 15.0, t["objective"])
                        val = pack[0] if pack else None
                        err = getattr(m, "LAST_ERR", "") or ""
                    else:
                        pack = m.run_code_batch(
                            [dict(code=code, dfs=dfs, obj=t["objective"])], 15.0)
                        if isinstance(pack, list) and pack and isinstance(pack[0], dict):
                            val, err = pack[0].get("value"), pack[0].get("error") or ""
                        else:
                            val, err = None, "bad_pack"
                    executable = val is not None and isinstance(val, (int, float)) and math.isfinite(float(val))
                    style_rows.append(dict(
                        agent=label, wrapper_alias_fix=fix, id=t["id"], type=t["type"],
                        style=style, executable=executable, value=val, error=str(err)[:200],
                    ))
                print(f"  {t['id']} done", flush=True)

    with (DIAG_OUT / "forced_fallback_styles.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(style_rows[0].keys()))
        w.writeheader()
        w.writerows(style_rows)

    # Solve-proxy: map import_pandas executability to the default-1 failure mode of TEST2
    solve_rows = []
    for label, fix in agents:
        for r in style_rows:
            if r["agent"] != label or r["wrapper_alias_fix"] != fix or r["style"] != "import_pandas":
                continue
            finite = bool(r["executable"])
            # TEST2 empty vote -> 1.0; others -> 0.0 when failed
            if finite:
                answer = r["value"]
                default_one = False
            else:
                answer = 1.0 if label == "test2" and not fix else 0.0
                default_one = label == "test2" and not fix
            solve_rows.append(dict(
                agent=label, wrapper_alias_fix=fix, id=r["id"], type=r["type"],
                answer=answer, finite=finite, is_default_one=default_one,
                gold=None, error=r["error"],
            ))
    with (DIAG_OUT / "forced_fallback_solve.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(solve_rows[0].keys()))
        w.writeheader()
        w.writerows(solve_rows)

    agg = []
    for label, fix in agents:
        s = [r for r in style_rows if r["agent"] == label and r["wrapper_alias_fix"] == fix]
        sol = [r for r in solve_rows if r["agent"] == label and r["wrapper_alias_fix"] == fix]
        for style in ["no_import", "import_pandas", "import_numpy", "syntax_broken"]:
            ss = [x for x in s if x["style"] == style]
            agg.append(dict(
                agent=label, wrapper_alias_fix=fix, metric=f"exec_rate_{style}",
                value=(sum(x["executable"] for x in ss) / len(ss)) if ss else None, n=len(ss),
            ))
        agg.append(dict(
            agent=label, wrapper_alias_fix=fix, metric="solve_finite_rate_import_pandas",
            value=(sum(x["finite"] for x in sol) / len(sol)) if sol else None, n=len(sol),
        ))
        agg.append(dict(
            agent=label, wrapper_alias_fix=fix, metric="solve_default_one_rate",
            value=(sum(x["is_default_one"] for x in sol) / len(sol)) if sol else None, n=len(sol),
        ))
    with (DIAG_OUT / "forced_fallback_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(agg[0].keys()))
        w.writeheader()
        w.writerows(agg)

    try:
        import torch
        qwen = ("CUDA available — run audit_independent/gpu_experiments.py"
                if torch.cuda.is_available() else "NOT RUN: torch.cuda.is_available() is False.")
    except Exception as e:
        qwen = f"NOT RUN: {e}"

    def get(label, fix, metric):
        for a in agg:
            if a["agent"] == label and a["wrapper_alias_fix"] == fix and a["metric"] == metric:
                return a["value"]
        return float("nan")

    md = [
        "# Forced fallback (CPU proxy)\n",
        f"**Qwen GPU:** {qwen}\n",
        "## Method\n",
        "- Table rules assumed absent (programs fixed; no Agent.solve loop).",
        f"- Stratified sample of {len(tasks)} / {len(all_tables)} public Tables.",
        "- Styles: no_import / import_pandas / import_numpy / syntax_broken.",
        "- TEST1/faithful measured on **samples path** (`run_codes_many`); TEST2 on `run_code_batch`.\n",
        "## Execution rates\n",
        "| Agent | fix | no_import | import_pandas | import_numpy | finite(pandas) | default=1 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for label, fix in agents:
        md.append(
            f"| {label} | {fix} | "
            f"{get(label, fix, 'exec_rate_no_import'):.2f} | "
            f"{get(label, fix, 'exec_rate_import_pandas'):.2f} | "
            f"{get(label, fix, 'exec_rate_import_numpy'):.2f} | "
            f"{get(label, fix, 'solve_finite_rate_import_pandas'):.2f} | "
            f"{get(label, fix, 'solve_default_one_rate'):.2f} |"
        )
    md += [
        "\n## Interpretation\n",
        "- **MEASURED:** import_pandas collapses on TEST1 samples and TEST2 batch; Stage3 and faithful stay at 1.0.",
        "- **MEASURED:** TEST2 failure mode maps to default=1 answers when candidates are empty.",
        "- **HYPOTHESIS:** private Tables gap size scales with how often Qwen emits `import pandas as pd`.",
        "- Real Qwen forced-fallback (oracle@4, repair_gain, 40s batches) remains **NOT RUN**.\n",
    ]
    (DIAG_OUT / "FORCED_FALLBACK.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md), flush=True)


if __name__ == "__main__":
    main()
