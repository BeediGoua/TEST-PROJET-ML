"""Build colab_phase_b2.ipynb — Agent.solve recovery scaffold (run ONLY after B1 PASS)."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
cells = []


def md(text):
    cells.append(dict(cell_type="markdown", metadata={}, source=text.splitlines(True)))


def code(text):
    cells.append(
        dict(
            cell_type="code",
            metadata={},
            source=text.splitlines(True),
            execution_count=None,
            outputs=[],
        )
    )


md(
    """# Phase B2/B3/B4 — End-to-end recovery (NO submission)

**Prerequisite:** B1 PASS (loop, zero bad_numeric, task-level vote ≈ 100%, outer chosen).

Do **not** reuse `generations_*.json` as B2 result — call real `Agent.solve()`.

Agents:
- A: Stage3 exact (historical exec allowed on Colab only)
- B: Stage3 + E2T executor only change

Then B2.2 stress K∈{1,2,4,8}, B3 No-files, B4 scanner → fill `PHASE_B_LINUX_RECOVERY_REPORT.md`.
"""
)

md("## 00 — Gate: refuse to run if B1 incomplete")
code(
    r'''
from pathlib import Path
import sys, os, platform, json
assert platform.system() == "Linux"
PROJECT_ROOT = Path("/content/TEST-PROJET-ML")
AUDIT = PROJECT_ROOT / "audit_independent"
sys.path[:0] = [str(AUDIT), str(PROJECT_ROOT), str(AUDIT / "diagnostic")]
os.chdir(AUDIT)
b1 = AUDIT / "diagnostic" / "results" / "b1_outer_sweep_summary.csv"
assert b1.exists(), "Run colab_phase_b1.ipynb first and keep b1_*.csv"
print("B1 summary present — proceed only if you reviewed TASK_vote_agree / bad_numeric")
CHOSEN_OUTER = 7.5  # set after B1 review
print("CHOSEN_OUTER", CHOSEN_OUTER)
'''
)

md(
    """## 01 — Bake experimental agents (TODO implementation cell)

Construct two modules without changing prompts/rules/model:
- `experimental/agent_stage3_ref_solve.py` — Stage3 exact, BUDGET=29
- `experimental/agent_stage3_e2t_solve.py` — same + E2T many path

Disable table rules only (forced fallback). Keep seed=0 at start of each solve.
"""
)
code(
    r'''
# TODO: implement bake_stage3_e2t_agent() after B1 PASS.
# Must wire: greedy, continuation, repair, samples, vote, BUDGET=29.
# Only executor differs.
raise NotImplementedError("Implement after B1 PASS — see Phase B prompt §B2")
'''
)

md("## 02 — B2 Tables: 10×8 real solve + metrics")
code(
    r'''
raise NotImplementedError("B2 Tables solve loop — metrics per batch as in Phase B prompt")
'''
)

md("## 03 — B2.2 Stress K = 1,2,4,8")
code(
    r'''
raise NotImplementedError("B2.2 stress fallback load")
'''
)

md("## 04 — B3 No-files (40 uncovered by Stage3 calc_rules)")
code(
    r'''
raise NotImplementedError("B3 No-files recovery")
'''
)

md("## 05 — B4 Scanner / resources")
code(
    r'''
raise NotImplementedError("B4 static + runtime resource checks")
'''
)

md("## 06 — Write PHASE_B_LINUX_RECOVERY_REPORT.md verdict")
code(
    r'''
# Fill MEASURED rows then set RECOVERY_READY or RECOVERY_NOT_READY.
print("Update audit_independent/PHASE_B_LINUX_RECOVERY_REPORT.md manually or via writer helper")
'''
)

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "T4"},
    },
    "cells": cells,
}
out = HERE / "colab_phase_b2.ipynb"
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", out)
