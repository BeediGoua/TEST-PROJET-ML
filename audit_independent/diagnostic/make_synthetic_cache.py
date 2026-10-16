"""Build a tiny synthetic generations_*.json so H1–H6 harnesses can smoke on CPU/Windows."""
from __future__ import annotations

import json

from pretest3_common import AUDIT_OUT, table_tasks

STYLES = [
    ("greedy", 0, "answer = float(list(dfs.values())[0].select_dtypes('number').iloc[:,0].dropna().sum())"),
    ("samples", 0, "import pandas as pd\nanswer = float(list(dfs.values())[0].select_dtypes('number').iloc[:,0].dropna().sum())"),
    ("samples", 1, "import numpy as np\nanswer = float(list(dfs.values())[0].select_dtypes('number').iloc[:,0].dropna().sum())"),
    ("samples", 2, "answer = ("),
    ("samples", 3, "answer = 0"),
]


def main():
    tasks = table_tasks()[:8]
    rows = []
    for t in tasks:
        for phase, sample, code in STYLES:
            rows.append(
                dict(
                    id=t["id"],
                    type=t["type"],
                    phase=phase,
                    sample=sample,
                    prompt=[],
                    text="",
                    code=code,
                    generation_batch_seconds=0.0,
                )
            )
    payload = dict(
        config=dict(
            model="synthetic-smoke",
            synthetic=True,
            prompt_agent="stage3",
            seed=0,
            note="NOT a Qwen cache — harness smoke only",
        ),
        rows=rows,
    )
    AUDIT_OUT.mkdir(parents=True, exist_ok=True)
    path = AUDIT_OUT / "generations_synthetic_smoke.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", path, "rows", len(rows))


if __name__ == "__main__":
    main()
