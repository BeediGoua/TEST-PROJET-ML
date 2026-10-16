"""Counterfactual No-files: do correct programs run under Stage3 exec vs E2T dsh?"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0]))
sys.path.insert(0, str(HERE.parents[1]))

from pretest3_common import DIAG_OUT, EXP, HANDOFF, install_dsh, load_path, write_csv
from build_experimental import build_test1_e2t
import audit as audit_mod

# Reference programs that should yield gold (human-written, not LLM)
REF_CODES = {
    "d_026": """
from datetime import datetime
a = datetime(2017, 4, 15)
b = datetime(2017, 4, 28)
answer = (b - a).days
""",
    "d_065": """
vals = [2.48, 1.43, 1.791, 0.64, 2.9, 1.19, 0.47, 2.5, 1.26, 1.11, 0.7, 2.862, 2.56]
answer = sum(1 for v in vals if v > 1.75)
""",
    "d_076": """
from datetime import datetime
a = datetime(2011, 12, 4)
b = datetime(2011, 12, 19)
answer = (b - a).days + 1  # inclusive both ends
""",
    "d_143": """
import numpy as np
laps = np.array([6.8, 13.3, 26.6, 3.3], dtype=float)
answer = float(np.std(laps, ddof=0))
""",
    "d_123": """
answer = 100338135 % 52
""",
}


def main():
    build_test1_e2t()
    install_dsh(False)
    stage3 = audit_mod.load("stage3")
    e2t = load_path(EXP / "test1_e2t_dsh.py", "e2t")
    gold = {t["id"]: t for t in json.loads((HANDOFF / "dev.json").read_text(encoding="utf-8"))}

    rows = []
    for tid, code in REF_CODES.items():
        t = gold[tid]
        obj = t["objective"]
        ans, tol = float(t["answer"]), float(t["tol"])
        empty = {}

        v_s3 = stage3.run_code(code, empty, 1.5, obj)
        err_s3 = getattr(stage3, "LAST_ERR", "") or ""

        vals = e2t.run_codes_many([code], empty, 6.5, obj)
        v_e2t = vals[0] if vals else None

        ok_s3 = v_s3 is not None and abs(float(v_s3) - ans) <= tol
        ok_e2t = v_e2t is not None and abs(float(v_e2t) - ans) <= tol

        if ok_s3 and ok_e2t:
            klass = "EXECUTOR_OK_ON_CORRECT_CODE→losses_are_GENERATION_OR_CONTROL"
        elif ok_s3 and not ok_e2t:
            klass = "EXECUTOR"
        elif not ok_s3 and ok_e2t:
            klass = "STAGE3_REF_CODE_ISSUE"
        else:
            klass = "BOTH_FAIL_REF_OR_ENV"

        rows.append(
            dict(
                id=tid,
                type=t["type"],
                gold=ans,
                stage3_val=v_s3,
                stage3_ok=ok_s3,
                stage3_err=err_s3[:200],
                e2t_val=v_e2t,
                e2t_ok=ok_e2t,
                classification=klass,
                objective=obj[:160],
            )
        )
        print(tid, "s3", v_s3, ok_s3, "e2t", v_e2t, ok_e2t, "→", klass)

    write_csv(DIAG_OUT / "nofile_counterfactual_refcodes.csv", rows)
    lines = [
        "# No-file counterfactual (reference codes)\n",
        "Correct human programs executed under Stage3 `run_code` vs E2T `run_codes_many`.\n",
        "If both OK → Colab losses (0.0) are **not** pure executor incapability on solvable programs.\n",
        "| id | gold | Stage3 | E2T | class |",
        "|---|---:|---:|---:|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['gold']} | {r['stage3_val']} ({r['stage3_ok']}) | "
            f"{r['e2t_val']} ({r['e2t_ok']}) | {r['classification']} |"
        )
    text = "\n".join(lines) + "\n"
    (DIAG_OUT / "NOFILE_COUNTERFACTUAL.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
