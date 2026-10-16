"""Step E — batch-of-8 contention proxy (CPU).

Measures wall time for 1/4/8 concurrent program executions under TEST1 many,
TEST2 batch, and faithful individual calls. Not a substitute for Linux 40s + Qwen.
"""
from __future__ import annotations

import csv
import importlib.util
import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAG_OUT = HERE / "results"
AUDIT = HERE.parents[0]
ROOT = HERE.parents[1]
EXP = HERE / "experimental"
DIAG_OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(AUDIT))
sys.path.insert(0, str(ROOT))

import audit as audit_mod  # noqa: E402
from probes import SIGNAL_SHIM  # noqa: E402
import pandas as pd  # noqa: E402


def install_dsh():
    from src.evaluation import dsh_compat

    def runner(code, **kwargs):
        kwargs.setdefault("timeout_s", 60)
        return dsh_compat.run_python(SIGNAL_SHIM + "\n" + code, **kwargs)

    sys.modules["dsh"] = types.SimpleNamespace(run_python=runner)


def load_faithful():
    path = EXP / "stage3_faithful_dsh.py"
    spec = importlib.util.spec_from_file_location("faithful_bt", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    install_dsh()
    rows = []
    programs = {
        "trivial": "answer = 2 + 2",
        "import_pandas": 'import pandas as pd\nanswer = float(dfs["data"]["x"].sum())',
    }
    agents = [
        ("stage3", "individual"),
        ("test1", "many"),
        ("test2", "batch"),
        ("faithful", "many"),
    ]

    for label, mode in agents:
        m = load_faithful() if label == "faithful" else audit_mod.load(label)
        dfs = m.Tables({"data": pd.DataFrame({"x": [2.0, 4.0]})})
        for pname, code in programs.items():
            for n in (1, 4, 8):
                codes = [code] * n
                t0 = time.perf_counter()
                ok_count = 0
                try:
                    if mode == "individual":
                        vals = [m.run_code(c, dfs, 2.0, "sum") for c in codes]
                    elif mode == "many":
                        vals = m.run_codes_many(codes, dfs, 60.0, "sum")
                    else:
                        specs = [dict(code=c, dfs=dfs, obj="sum") for c in codes]
                        pack = m.run_code_batch(specs, 60.0)
                        vals = []
                        for item in pack or []:
                            if isinstance(item, dict):
                                vals.append(item.get("value"))
                            else:
                                vals.append(item)
                    for v in vals or []:
                        if isinstance(v, dict):
                            v = v.get("value")
                        if v is not None:
                            ok_count += 1
                except Exception as e:
                    vals = []
                    err = f"{type(e).__name__}:{e}"
                else:
                    err = ""
                elapsed = time.perf_counter() - t0
                rows.append(dict(
                    agent=label, mode=mode, program=pname, n=n,
                    seconds=round(elapsed, 3), ok_count=ok_count,
                    all_ok=ok_count == n, error=err[:200],
                ))
                print(label, pname, n, f"{elapsed:.2f}s", f"ok={ok_count}/{n}")

    with (DIAG_OUT / "batch_timing.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    md = [
        "# Batch timing (CPU proxy)\n",
        "**NOT** Linux 40s / RTX 4090. Cold-start subprocess costs dominate on Windows.\n",
        "| Agent | program | n | seconds | ok |",
        "|---|---|---:|---:|---:|",
    ]
    for r in rows:
        md.append(f"| {r['agent']} | {r['program']} | {r['n']} | {r['seconds']} | {r['ok_count']} |")
    md.append("\n## Interpretation\n")
    md.append("- **MEASURED:** wall times and success counts under mixed program styles.")
    md.append("- **INFERRED:** if import_pandas ok_count collapses while trivial stays OK,")
    md.append("  batch contention is secondary to the pandas contract bug.")
    md.append("- **NOT RUN:** official 40s mixed-task Qwen batches on Linux.\n")
    (DIAG_OUT / "BATCH_TIMING.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[-8:]))


if __name__ == "__main__":
    main()
