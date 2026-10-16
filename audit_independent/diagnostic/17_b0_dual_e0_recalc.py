"""B0 — Dual E0 recalculation: E0_semantic (15s) vs E0_production (1.5s) vs E2T.

Does NOT change model/prompt/rules. Documents whether Phase A 97.35% is
production regression or outer-envelope artefact.
"""
from __future__ import annotations

import tempfile
import time
from collections import defaultdict

from pretest3_common import (
    AUDIT_OUT,
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
)
import audit as audit_mod
from build_experimental import build_test1_e2t

CACHE_NAME = "generations_34d6ece55b3c092a.json"
E0_SEMANTIC_TO = 15.0
E0_PRODUCTION_TO = 1.5  # Stage3 EXEC_TIMEOUT
OUTER_DEFAULT = 6.5
# Focus tasks from Phase A disagreements + full sweep later
FOCUS_IDS = {"d_041", "d_100", "d_170"}


def _resolve_cache():
    preferred = AUDIT_OUT / CACHE_NAME
    if preferred.exists():
        return preferred
    for p in find_generation_caches():
        if "34d6ece55b3c092a" in p.name:
            return p
    raise FileNotFoundError(CACHE_NAME)


def main(focus_only: bool = True, outer: float = OUTER_DEFAULT):
    path = _resolve_cache()
    cache = load_cache(path)
    assert is_real_qwen_cache(cache)
    tasks = {t["id"]: t for t in table_tasks()}
    by_id: dict[str, list] = defaultdict(list)
    for r in cache["rows"]:
        by_id[r["id"]].append(r)

    build_test1_e2t()
    install_dsh(False)
    stage3 = audit_mod.load("stage3")
    e2t = load_path(EXP / "test1_e2t_dsh.py", "e2t")

    from src.evaluation.core import _materialize_all

    detail = []
    tids = [tid for tid in by_id if tid in tasks]
    if focus_only:
        tids = [tid for tid in tids if tid in FOCUS_IDS]
        print(f"FOCUS mode: {tids}")

    with tempfile.TemporaryDirectory(prefix="b0_dual_") as td:
        uniq = [tasks[tid] for tid in tids]
        filemap = _materialize_all(uniq, td)

        for tid in tids:
            gens = by_id[tid]
            task = tasks[tid]
            greedy = [g for g in gens if g["phase"] == "greedy"]
            samples = sorted(
                [g for g in gens if g["phase"] == "samples"], key=lambda x: int(x.get("sample", 0))
            )
            ordered = greedy + samples
            codes = [g.get("code") or "" for g in ordered]

            e0s, e0s_rt, e0p, e0p_rt = [], [], [], []
            for code in codes:
                fresh, dd = stage3.load_task(task["objective"], filemap[tid])
                if len(fresh) >= 2:
                    stage3.align_keys(fresh, dd)
                t0 = time.perf_counter()
                v = stage3.run_code(code, fresh, E0_SEMANTIC_TO, task["objective"])
                e0s.append(v)
                e0s_rt.append(time.perf_counter() - t0)

                fresh2, dd2 = stage3.load_task(task["objective"], filemap[tid])
                if len(fresh2) >= 2:
                    stage3.align_keys(fresh2, dd2)
                t0 = time.perf_counter()
                v2 = stage3.run_code(code, fresh2, E0_PRODUCTION_TO, task["objective"])
                e0p.append(v2)
                e0p_rt.append(time.perf_counter() - t0)

            dfs, dico = stage3.load_task(task["objective"], filemap[tid])
            if len(dfs) >= 2:
                stage3.align_keys(dfs, dico)
            t0 = time.perf_counter()
            e2t_vals = e2t.run_codes_many(codes, dfs, outer, task["objective"])
            e2t_batch_rt = time.perf_counter() - t0
            while len(e2t_vals) < len(codes):
                e2t_vals.append(None)

            for i, g in enumerate(ordered):
                reason = ""
                if e2t_vals[i] is None and e0p[i] is not None:
                    reason = "e2t_none_but_e0_prod_finite"
                elif e2t_vals[i] is None and e0s[i] is not None and e0p[i] is None:
                    reason = "e0_prod_would_also_drop_slow_prog"
                elif e2t_vals[i] is None and e0s[i] is None:
                    reason = "both_none_or_fail"
                elif e2t_vals[i] is not None and not values_agree(e2t_vals[i], e0s[i]):
                    reason = "numeric_mismatch_vs_semantic"
                detail.append(
                    dict(
                        id=tid,
                        phase=g["phase"],
                        sample=g.get("sample", 0),
                        e0_semantic=e0s[i],
                        e0_production=e0p[i],
                        e2t=e2t_vals[i],
                        e0_semantic_rt=e0s_rt[i],
                        e0_production_rt=e0p_rt[i],
                        e2t_batch_rt=e2t_batch_rt,
                        outer=outer,
                        agree_semantic=values_agree(e0s[i], e2t_vals[i]),
                        agree_production=values_agree(e0p[i], e2t_vals[i]),
                        timeout_reason=reason,
                    )
                )

    out_name = "b0_dual_e0_focus.csv" if focus_only else "b0_dual_e0_full.csv"
    write_csv(DIAG_OUT / out_name, detail)

    def rate(key_agree, e0_col):
        rows = [d for d in detail if d[e0_col] is not None]
        if not rows:
            return None, 0, 0
        n = len(rows)
        ok = sum(1 for d in rows if d[key_agree])
        return ok / n, ok, n

    as_, ok_s, n_s = rate("agree_semantic", "e0_semantic")
    ap, ok_p, n_p = rate("agree_production", "e0_production")
    num_mismatch = sum(1 for d in detail if d["timeout_reason"] == "numeric_mismatch_vs_semantic")
    e2t_none_prod_ok = sum(1 for d in detail if d["timeout_reason"] == "e2t_none_but_e0_prod_finite")
    prod_also_drop = sum(1 for d in detail if d["timeout_reason"] == "e0_prod_would_also_drop_slow_prog")

    lines = [
        "# B0 Dual E0 recalculation\n",
        f"**Cache:** `{path.name}`\n",
        f"**Mode:** {'FOCUS ' + str(sorted(FOCUS_IDS)) if focus_only else 'FULL'}\n",
        f"**E0_semantic timeout:** {E0_SEMANTIC_TO}s\n",
        f"**E0_production timeout:** {E0_PRODUCTION_TO}s (= Stage3 EXEC_TIMEOUT)\n",
        f"**E2T outer:** {outer}s (per-candidate SIGALRM 1.5s when Linux)\n",
        "\n## Program-level agreement\n",
        f"- vs E0_semantic (among E0_sem finite): **{as_}** ({ok_s}/{n_s})\n" if as_ is not None else "- vs E0_semantic: n/a\n",
        f"- vs E0_production (among E0_prod finite): **{ap}** ({ok_p}/{n_p})\n" if ap is not None else "- vs E0_production: n/a\n",
        f"- numeric mismatches vs semantic: **{num_mismatch}**\n",
        f"- E2T None while E0_production finite: **{e2t_none_prod_ok}**\n",
        f"- E0_production None but E0_semantic finite (slow prog Stage3 would drop): **{prod_also_drop}**\n",
        "\n## Divergent rows\n",
    ]
    for d in detail:
        if not d["agree_production"] or not d["agree_semantic"]:
            lines.append(
                f"- `{d['id']}` {d['phase']}/{d['sample']}: "
                f"sem={d['e0_semantic']}@{d['e0_semantic_rt']:.3f}s "
                f"prod={d['e0_production']}@{d['e0_production_rt']:.3f}s "
                f"e2t={d['e2t']} batch_rt={d['e2t_batch_rt']:.3f}s "
                f"reason={d['timeout_reason']}"
            )
    text = "\n".join(lines)
    md = DIAG_OUT / ("B0_DUAL_E0_FOCUS.md" if focus_only else "B0_DUAL_E0_FULL.md")
    md.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    import sys

    focus = "--full" not in sys.argv
    main(focus_only=focus)
