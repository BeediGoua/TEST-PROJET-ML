"""H6 — one-factor TEST2 decomposition on shared cached generations."""
from __future__ import annotations

import platform
import tempfile

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
from build_experimental import build_test1_alias


def _vote_stage3(cands, nd, m):
    return m.vote(cands, nd)


def _vote_default1(cands, nd, m):
    if not cands:
        return 1.0
    v = m.vote(cands, nd)
    return 1.0 if v is None else v


def _filter_reject_zero(cands):
    return [(v, w) for v, w in cands if v is not None and float(v) != 0.0]


def main():
    caches = find_generation_caches()
    if not caches:
        write_not_run(
            DIAG_OUT / "TEST2_DECOMPOSITION.md",
            "H6 — TEST2 decomposition",
            "No generations_*.json. Produce cache via Colab first.",
        )
        print("NOT RUN: no cache")
        return

    path = caches[0]
    cache = load_cache(path)
    real = is_real_qwen_cache(cache)
    build_test1_alias()

    stage3 = audit_mod.load("stage3")
    test1 = audit_mod.load("test1")
    test2 = audit_mod.load("test2")
    alias = load_path(EXP / "test1_alias_dsh.py", "e2h6")

    tasks = {t["id"]: t for t in table_tasks()}
    # group programs by task
    by_id = {}
    for r in cache.get("rows") or []:
        by_id.setdefault(r["id"], []).append(r)

    ids = list(by_id.keys())
    if not real:
        ids = ids[:12]

    from src.evaluation.core import _materialize_all

    configs = [
        "S0_stage3_E0",
        "S1_E1_test1_many",
        "S2_E2_alias",
        "S3_reject_zero",
        "S4_default1",
        "S5_reject_zero_default1",
        "S6_test2_batch",
        "S7_test2_batch_alias",
    ]

    detail = []

    with tempfile.TemporaryDirectory(prefix="h6_") as td:
        uniq = [tasks[i] for i in ids if i in tasks]
        filemap = _materialize_all(uniq, td)

        for tid in ids:
            if tid not in tasks:
                continue
            task = tasks[tid]
            programs = by_id[tid]
            dfs, dico = stage3.load_task(task["objective"], filemap[tid])
            if len(dfs) >= 2:
                stage3.align_keys(dfs, dico)
            tol = float(task["tol"])
            gold = float(task["answer"])
            nd = stage3.decimals(task["objective"])

            # Execute each program under several executors
            def exec_e0():
                vals = []
                for r in programs:
                    fresh, _ = stage3.load_task(task["objective"], filemap[tid])
                    v = stage3.run_code(r["code"], fresh, 2.0, task["objective"])
                    vals.append((r, v))
                return vals

            def exec_many(mod):
                install_dsh(False)
                codes = [r["code"] for r in programs]
                fresh, _ = stage3.load_task(task["objective"], filemap[tid])
                out = mod.run_codes_many(codes, fresh, 8.0, task["objective"])
                return list(zip(programs, out))

            def exec_batch(mod, alias_fix=False):
                install_dsh(fix_alias=alias_fix)
                fresh, _ = stage3.load_task(task["objective"], filemap[tid])
                specs = [dict(code=r["code"], dfs=fresh, obj=task["objective"]) for r in programs]
                # Fresh dfs per spec ideally; TEST2 shares — match submitted behavior
                batch = mod.run_code_batch(specs, 8.0)
                vals = []
                for r, b in zip(programs, batch):
                    vals.append((r, b.get("value") if isinstance(b, dict) else None))
                return vals

            runs = {
                "S0_stage3_E0": exec_e0(),
                "S1_E1_test1_many": exec_many(test1),
                "S2_E2_alias": exec_many(alias),
                "S6_test2_batch": exec_batch(test2, False),
                "S7_test2_batch_alias": exec_batch(test2, True),
            }
            # vote variants on E0 values
            e0_vals = runs["S0_stage3_E0"]

            def score(cands, mode):
                pairs = [(v, 1.5 if r.get("phase") == "greedy" else 1.0) for r, v in cands if v is not None]
                if mode == "reject_zero":
                    pairs = _filter_reject_zero(pairs)
                if mode == "default1":
                    v = _vote_default1(pairs, nd, stage3)
                elif mode == "reject_zero_default1":
                    pairs = _filter_reject_zero(
                        [(v, 1.5 if r.get("phase") == "greedy" else 1.0) for r, v in cands if v is not None]
                    )
                    v = _vote_default1(pairs, nd, stage3)
                else:
                    v = _vote_stage3(pairs, nd, stage3) if pairs else 0.0
                if nd is not None and v is not None:
                    try:
                        v = round(v, nd)
                    except Exception:
                        pass
                correct = v is not None and abs(float(v) - gold) <= tol
                exec_rate = sum(1 for _, x in cands if x is not None) / max(1, len(cands))
                default1 = mode in ("default1", "reject_zero_default1") and not pairs
                return v, correct, exec_rate, default1

            for cfg, cands in runs.items():
                mode = "plain"
                v, correct, er, d1 = score(cands, mode)
                detail.append(
                    dict(
                        id=tid,
                        config=cfg,
                        value=v,
                        correct=correct,
                        exec_rate=er,
                        default1_triggered=d1,
                    )
                )

            for cfg, mode in [
                ("S3_reject_zero", "reject_zero"),
                ("S4_default1", "default1"),
                ("S5_reject_zero_default1", "reject_zero_default1"),
            ]:
                v, correct, er, d1 = score(e0_vals, mode)
                detail.append(
                    dict(
                        id=tid,
                        config=cfg,
                        value=v,
                        correct=correct,
                        exec_rate=er,
                        default1_triggered=d1,
                    )
                )

    write_csv(DIAG_OUT / "test2_decomposition_detail.csv", detail)

    summary = []
    for cfg in configs:
        rows = [d for d in detail if d["config"] == cfg]
        n = len(rows)
        if not n:
            continue
        acc = sum(1 for d in rows if d["correct"]) / n
        er = sum(d["exec_rate"] for d in rows) / n
        d1 = sum(1 for d in rows if d["default1_triggered"]) / n
        summary.append(dict(config=cfg, n=n, accuracy=acc, exec_rate=er, default1_rate=d1))
    write_csv(DIAG_OUT / "test2_decomposition_summary.csv", summary)

    # Deltas vs S0
    base = next((s for s in summary if s["config"] == "S0_stage3_E0"), None)
    lines = [
        "# H6 — TEST2 one-factor decomposition\n",
        f"**Cache:** `{path.name}` ({'REAL_QWEN' if real else 'SYNTHETIC_OR_PARTIAL'})\n",
        f"**Platform:** {platform.platform()}\n",
        "## Note on rules\n",
        "Extended table rules (`table_extended_rule` / `table_extra_safe2`) and historical "
        "guards are **not** applied here: this experiment freezes the LLM programs and "
        "varies **executor / vote / batch** only. Public deterministic shadow already showed "
        "`same:80` for rule extensions — private rule FP remains HYPOTHESIS without OOD private labels.\n",
        "## Results\n",
        "| config | n | accuracy | Δ vs S0 | exec_rate | default1_rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    base_acc = base["accuracy"] if base else 0.0
    for s in summary:
        delta = s["accuracy"] - base_acc
        lines.append(
            f"| {s['config']} | {s['n']} | {s['accuracy']:.4f} | {delta:+.4f} | "
            f"{s['exec_rate']:.4f} | {s['default1_rate']:.4f} |"
        )

    lines.append("\n## What never to repeat\n")
    for s in summary:
        if base and s["config"] != "S0_stage3_E0" and s["accuracy"] + 1e-9 < base_acc:
            lines.append(
                f"- `{s['config']}` costs **{base_acc - s['accuracy']:.4f}** absolute accuracy vs S0 on this corpus.\n"
            )
    if not real:
        lines.append("\n- Cache not real Qwen → treat deltas as harness smoke only.\n")

    (DIAG_OUT / "TEST2_DECOMPOSITION.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
