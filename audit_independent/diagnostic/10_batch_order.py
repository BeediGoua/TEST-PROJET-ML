"""H4 — cross-task batch order sensitivity (TEST2-style run_code_batch)."""
from __future__ import annotations

import itertools
import platform
import random
import tempfile
import time

from pretest3_common import (
    DIAG_OUT,
    find_generation_caches,
    install_dsh,
    is_real_qwen_cache,
    load_cache,
    table_tasks,
    values_agree,
    write_csv,
    write_not_run,
)
import audit as audit_mod


def main():
    caches = find_generation_caches()
    # Can also run with synthetic programs if no cache — still useful for order probe
    real = False
    programs_by_task = {}
    if caches:
        cache = load_cache(caches[0])
        real = is_real_qwen_cache(cache)
        for r in cache.get("rows") or []:
            if r.get("phase") == "greedy":
                programs_by_task[r["id"]] = r.get("code") or "answer = None"

    tasks = table_tasks()
    # Pick 8 tasks
    chosen = tasks[:8]
    if len(chosen) < 8:
        write_not_run(
            DIAG_OUT / "BATCH_ORDER.md",
            "H4 — Batch order sensitivity",
            "Fewer than 8 table tasks in dev.json.",
        )
        return

    for t in chosen:
        if t["id"] not in programs_by_task:
            programs_by_task[t["id"]] = "answer = 1.0"

    install_dsh(False)
    m = audit_mod.load("test2")
    prep = audit_mod.load("stage3")

    from src.evaluation.core import _materialize_all

    detail = []
    rng = random.Random(0)
    orders = []
    ids = [t["id"] for t in chosen]
    orders.append(("forward", list(ids)))
    orders.append(("reverse", list(reversed(ids))))
    # 20 fixed permutations
    for i in range(20):
        perm = list(ids)
        rng.shuffle(perm)
        orders.append((f"perm_{i:02d}", perm))

    with tempfile.TemporaryDirectory(prefix="order_") as td:
        filemap = _materialize_all(chosen, td)
        # Preload dfs
        dfs_map = {}
        for t in chosen:
            dfs, dico = prep.load_task(t["objective"], filemap[t["id"]])
            if len(dfs) >= 2:
                prep.align_keys(dfs, dico)
            dfs_map[t["id"]] = dfs

        answers_by_order = {tid: {} for tid in ids}

        for oname, order in orders:
            specs = []
            for pos, tid in enumerate(order):
                specs.append(
                    dict(
                        code=programs_by_task[tid],
                        dfs=dfs_map[tid],
                        obj=next(t["objective"] for t in chosen if t["id"] == tid),
                        _tid=tid,
                        _pos=pos,
                    )
                )
            t0 = time.perf_counter()
            try:
                outs = m.run_code_batch(
                    [dict(code=s["code"], dfs=s["dfs"], obj=s["obj"]) for s in specs],
                    timeout=8.0,
                )
            except Exception as e:
                outs = [dict(value=None, error=str(e)) for _ in specs]
            elapsed = time.perf_counter() - t0
            for s, o in zip(specs, outs):
                val = o.get("value") if isinstance(o, dict) else None
                err = (o.get("error") if isinstance(o, dict) else "") or ""
                budget_expired = "Budget" in err or "budget" in err or "timeout" in err.lower()
                answers_by_order[s["_tid"]][oname] = val
                detail.append(
                    dict(
                        order=oname,
                        task_id=s["_tid"],
                        position=s["_pos"],
                        value=val,
                        executed=val is not None,
                        timeout="timeout" in err.lower(),
                        batch_budget_expired=budget_expired,
                        error=err[:200],
                        batch_seconds=round(elapsed, 3),
                        platform=platform.platform(),
                        real_qwen_codes=real,
                    )
                )

    write_csv(DIAG_OUT / "batch_order_detail.csv", detail)

    # Sensitivity: for each task, distinct answers across orders
    sens_rows = []
    sensitive = 0
    for tid in ids:
        vals = answers_by_order[tid]
        # normalize None
        uniq = []
        for v in vals.values():
            if not any(values_agree(v, u) for u in uniq):
                uniq.append(v)
        is_sens = len(uniq) > 1
        if is_sens:
            sensitive += 1
        sens_rows.append(
            dict(
                task_id=tid,
                n_distinct_answers=len(uniq),
                sensitive=is_sens,
                forward=vals.get("forward"),
                reverse=vals.get("reverse"),
            )
        )
    write_csv(DIAG_OUT / "batch_order_sensitivity.csv", sens_rows)

    lines = [
        "# H4 — Batch order sensitivity\n",
        f"**Platform:** {platform.platform()}\n",
        f"**Codes:** {'real Qwen greedy from cache' if real else 'placeholder/synthetic codes'}\n",
        f"**Orders tested:** {len(orders)} (forward, reverse, 20 perms)\n",
        f"**Tasks with order-sensitive answers:** {sensitive} / {len(ids)}\n",
        "## Verdict\n",
    ]
    if sensitive > 0:
        lines.append(
            "- **CROSS-TASK BATCHING IS DANGEROUS** — at least one task answer depends on position.\n"
        )
        lines.append("- TEST3 must **not** use inter-task `run_code_batch`.\n")
    else:
        lines.append(
            "- No answer divergence across orders on this corpus "
            "(still forbid inter-task batch in TEST3-recovery by policy).\n"
        )
    if platform.system() != "Linux":
        lines.append(
            "- **NOTE:** not Linux official alarm semantics; re-run on Colab/Linux for GO gate.\n"
        )
    if not real:
        lines.append("- **NOTE:** codes not from real Qwen cache — treat as structural probe only.\n")

    lines.append("\n## Per-task\n")
    for s in sens_rows:
        lines.append(
            f"- `{s['task_id']}`: distinct={s['n_distinct_answers']} "
            f"sensitive={s['sensitive']} forward={s['forward']} reverse={s['reverse']}"
        )

    (DIAG_OUT / "BATCH_ORDER.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
