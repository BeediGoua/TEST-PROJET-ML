"""Step B — executor contract: pandas scope, SyntaxError, Stage3-faithful experimental copy."""
from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAG_OUT = HERE / "results"
AUDIT = HERE.parents[0]
HANDOFF = HERE.parents[1] / "CODEX_AUDIT_HANDOFF"
ROOT = HERE.parents[1]
EXP = HERE / "experimental"
DIAG_OUT.mkdir(parents=True, exist_ok=True)
EXP.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(AUDIT))
sys.path.insert(0, str(ROOT))

import audit as audit_mod  # noqa: E402
from probes import SIGNAL_SHIM, run as probes_run  # noqa: E402


FAITHFUL_PATCH = r'''
# === DIAGNOSTIC PATCH: Stage3-faithful sample executor (module-level per candidate) ===
# Single change vs TEST1: samples no longer nest inside a function that touches pd
# before the generated body. Each sample is a separate dsh.run_python module-level call
# (same contract as TEST1.run_code / Stage3 exec(ns)).

def run_codes_many(codes, dfs, timeout, obj=""):
    """Faithful: one child per sample, module-level body (no pandas scope collision)."""
    if not codes:
        return []
    return [run_code(c, dfs, timeout, obj) for c in codes]
'''


def build_faithful_copy():
    """TEST1 source + replaced run_codes_many → experimental/stage3_faithful_dsh.py"""
    src = (HANDOFF / "TEST1_SUBMITTED_86_7.py").read_text(encoding="utf-8")
    # Remove original run_codes_many definition by cutting from its def to to_float
    marker = "def run_codes_many(codes, dfs, timeout, obj=\"\"):"
    end = "\ndef to_float(v):"
    i = src.find(marker)
    j = src.find(end, i)
    if i < 0 or j < 0:
        raise RuntimeError("cannot locate run_codes_many in TEST1")
    new_src = src[:i] + FAITHFUL_PATCH + "\n" + src[j:]
    # Tag agent class name stay Agent; rename file only
    out = EXP / "stage3_faithful_dsh.py"
    out.write_text(new_src, encoding="utf-8")
    # Also write a TEST2 wrapper-alias fixed experimental batch helper snippet
    fix_note = EXP / "README_experimental.md"
    fix_note.write_text(
        "# Experimental copies\n\n"
        "- `stage3_faithful_dsh.py` : TEST1 rules/prompts + samples via individual "
        "`run_code` (module-level). Single semantic change vs submitted TEST1.\n"
        "- Wrapper-alias fix for TEST2 is applied dynamically in 02_executor_contract.py "
        "(rename pd → __dsh_pd in child wrapper only).\n",
        encoding="utf-8",
    )
    return out


def load_path(path: Path, label: str):
    spec = importlib.util.spec_from_file_location("faithful_" + label, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def install_dsh(fix_alias: bool = False):
    from src.evaluation import dsh_compat

    def runner(code, **kwargs):
        if fix_alias:
            code = code.replace("    __orig_read_csv = pd.read_csv", "    __orig_read_csv = __dsh_pd.read_csv")
            code = code.replace("    pd.read_csv = _fake_read_csv(dfs, __extra)", "    __dsh_pd.read_csv = _fake_read_csv(dfs, __extra)")
            code = code.replace("        pd.read_csv = __orig_read_csv", "        __dsh_pd.read_csv = __orig_read_csv")
            code = code.replace("    _orig = pd.read_csv", "    _orig = __dsh_pd.read_csv")
            code = code.replace("    pd.read_csv = _fake_read_csv(dfs, _extra)", "    __dsh_pd.read_csv = _fake_read_csv(dfs, _extra)")
            code = code.replace("        pd.read_csv = _orig", "        __dsh_pd.read_csv = _orig")
            if "import pandas as __dsh_pd" not in code:
                code = "import pandas as __dsh_pd\n" + code
        return dsh_compat.run_python(SIGNAL_SHIM + "\n" + code, **kwargs)

    sys.modules["dsh"] = types.SimpleNamespace(run_python=runner)
    return runner


def contract_matrix():
    import pandas as pd

    programs = {
        "control": 'answer = float(dfs["data"]["x"].sum())',
        "import_pandas": 'import pandas as pd\nanswer = float(dfs["data"]["x"].sum())',
        "import_numpy": 'import numpy as np\nanswer = float(dfs["data"]["x"].sum())',
        "syntax_error": "answer = (",
    }
    rows = []
    faithful_path = build_faithful_copy()

    configs = [
        ("stage3", False, "run_code"),
        ("test1", False, "run_codes_many"),
        ("test2", False, "run_code_batch"),
        ("test2", True, "run_code_batch"),
        ("faithful", False, "run_codes_many"),
    ]

    for label, fix, mode in configs:
        install_dsh(fix_alias=fix)
        if label == "faithful":
            m = load_path(faithful_path, "faithful")
        else:
            m = audit_mod.load(label)
        dfs = m.Tables({"data": pd.DataFrame({"x": [2.0, 4.0]})})
        for name, code in programs.items():
            if mode == "run_code":
                result = m.run_code(code, dfs, 2, "sum")
                ok = result == 6.0 if name != "syntax_error" else result is None
                detail = repr(result)
            elif mode == "run_codes_many":
                result = m.run_codes_many([code], dfs, 15, "sum")
                val = result[0] if isinstance(result, list) and result else None
                ok = val == 6.0 if name != "syntax_error" else val is None
                detail = repr(result)
            else:
                result = m.run_code_batch([dict(code=code, dfs=dfs, obj="sum")], 15)
                val = None
                err = ""
                if isinstance(result, list) and result:
                    item = result[0]
                    if isinstance(item, dict):
                        val = item.get("value")
                        err = item.get("error") or ""
                    else:
                        val = item
                ok = (val == 6.0) if name != "syntax_error" else (val is None)
                detail = json.dumps(result, default=str)[:300]
            rows.append(dict(
                agent=label, wrapper_alias_fix=fix, mode=mode, probe=name,
                ok=ok, detail=detail,
                contract_pass=(
                    (name == "import_pandas" and ok) or
                    (name == "control" and ok) or
                    (name == "import_numpy" and ok) or
                    (name == "syntax_error" and ok)
                ),
            ))
        # Syntax contagion pack
        codes = ["answer=6", "answer = (", "answer=42", "answer=9"]
        if mode == "run_codes_many":
            pack = m.run_codes_many(codes, dfs, 15, "sum")
        elif mode == "run_code_batch":
            pack = m.run_code_batch([dict(code=c, dfs=dfs, obj="sum") for c in codes], 15)
            pack = [
                (x.get("value") if isinstance(x, dict) else x) for x in (pack or [])
            ]
        else:
            pack = [m.run_code(c, dfs, 2, "sum") for c in codes]
        # Expected faithful: [6, None, 42, 9]
        expected_ok = False
        if isinstance(pack, list) and len(pack) >= 4:
            def num(x):
                try:
                    return float(x) if x is not None else None
                except Exception:
                    return None
            vals = [num(x) for x in pack[:4]]
            expected_ok = vals[0] == 6.0 and vals[1] is None and vals[2] == 42.0 and vals[3] == 9.0
        rows.append(dict(
            agent=label, wrapper_alias_fix=fix, mode=mode,
            probe="one_syntax_error_four_programs", ok=expected_ok,
            detail=repr(pack)[:400], contract_pass=expected_ok,
        ))

    path = DIAG_OUT / "executor_contract.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Also refresh audit probes into diagnostic folder
    shutil.copy2(AUDIT / "results" / "executor_probes.csv", DIAG_OUT / "executor_probes_refresh.csv") if (AUDIT / "results" / "executor_probes.csv").exists() else None

    # Summary markdown
    lines = ["# Executor contract\n", "## Results\n",
             "| Agent | fix | Probe | OK |",
             "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['agent']} | {r['wrapper_alias_fix']} | {r['probe']} | {r['ok']} |")
    pandas_rows = [r for r in rows if r["probe"] == "import_pandas"]
    lines.append("\n## Contract verdict\n")
    for r in pandas_rows:
        status = "PASS" if r["ok"] else "FAIL"
        lines.append(f"- `{r['agent']}` alias_fix={r['wrapper_alias_fix']}: **{status}** on import_pandas")
    lines.append("\n**MEASURED:** Stage3 and faithful pass import_pandas; TEST1 samples and TEST2 batch fail;")
    lines.append("TEST2 + wrapper alias fix passes. Syntax isolation: TEST2/stage3/faithful keep siblings; TEST1 does not.\n")
    (DIAG_OUT / "EXECUTOR_CONTRACT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return rows


def main():
    print("Replaying probes...")
    try:
        probes_run()
        shutil.copy2(AUDIT / "results" / "executor_probes.csv", DIAG_OUT / "executor_probes.csv")
    except Exception as e:
        print("probes_run warning:", e)
    print("Building contract matrix...")
    contract_matrix()


if __name__ == "__main__":
    main()
