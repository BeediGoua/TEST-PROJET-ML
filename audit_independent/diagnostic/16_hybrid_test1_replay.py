"""Phase A §6 — TEST1 faithful hybrid vs recovery (E2T samples).

Fidèle: greedy test1_single + samples test1_many + Stage3.vote
Recovery: greedy Stage3-compliant (E2/E2T single-equivalent) + samples E2T + Stage3.vote

Never report test1_many vote accuracy as the real TEST1 private score.
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
    write_csv,
)
import audit as audit_mod
from build_experimental import build_test1_alias, build_test1_e2t

CACHE_NAME = "generations_34d6ece55b3c092a.json"
OUTER = 6.5
SINGLE_TO = 5.0  # TEST1 EXEC_TIMEOUT for single


def _resolve_cache():
    preferred = AUDIT_OUT / CACHE_NAME
    if preferred.exists():
        return preferred
    for p in find_generation_caches():
        if "34d6ece55b3c092a" in p.name:
            return p
    raise FileNotFoundError(CACHE_NAME)


def _vote(stage3, vals, obj, gold, tol):
    cands = []
    for i, v in enumerate(vals):
        if v is None:
            continue
        cands.append((v, 1.5 if i == 0 else 1.0))
    nd = stage3.decimals(obj)
    v = stage3.vote(cands, nd) if cands else None
    if nd is not None and v is not None:
        try:
            v = round(v, nd)
        except Exception:
            pass
    ok = v is not None and abs(float(v) - float(gold)) <= float(tol)
    return v, ok


def main():
    path = _resolve_cache()
    cache = load_cache(path)
    assert is_real_qwen_cache(cache)
    tasks = {t["id"]: t for t in table_tasks()}
    by_id: dict[str, list] = defaultdict(list)
    for r in cache["rows"]:
        by_id[r["id"]].append(r)

    build_test1_alias()
    build_test1_e2t()
    install_dsh(False)
    stage3 = audit_mod.load("stage3")
    test1 = audit_mod.load("test1")
    e2t = load_path(EXP / "test1_e2t_dsh.py", "e2t")
    # E2 alias as Stage3-compliant greedy executor (same semantics as E2T single)
    e2 = load_path(EXP / "test1_alias_dsh.py", "e2")

    from src.evaluation.core import _materialize_all

    rows_out = []
    with tempfile.TemporaryDirectory(prefix="hybrid_") as td:
        uniq = [tasks[tid] for tid in by_id if tid in tasks]
        filemap = _materialize_all(uniq, td)

        for tid, gens in by_id.items():
            if tid not in tasks:
                continue
            task = tasks[tid]
            greedy = [g for g in gens if g["phase"] == "greedy"]
            samples = sorted(
                [g for g in gens if g["phase"] == "samples"], key=lambda x: int(x.get("sample", 0))
            )
            g_code = (greedy[0].get("code") or "") if greedy else ""
            s_codes = [g.get("code") or "" for g in samples]

            # --- Fidèle TEST1: single greedy + many samples ---
            dfs, dico = stage3.load_task(task["objective"], filemap[tid])
            if len(dfs) >= 2:
                stage3.align_keys(dfs, dico)
            t0 = time.perf_counter()
            # fresh for greedy
            fresh, dd = stage3.load_task(task["objective"], filemap[tid])
            if len(fresh) >= 2:
                stage3.align_keys(fresh, dd)
            g_fid = test1.run_code(g_code, fresh, SINGLE_TO, task["objective"])
            s_fid = test1.run_codes_many(s_codes, dfs, OUTER, task["objective"])
            fid_vals = [g_fid] + list(s_fid)
            fid_vote, fid_ok = _vote(
                stage3, fid_vals, task["objective"], task["answer"], task["tol"]
            )
            t_fid = time.perf_counter() - t0

            # --- Recovery: greedy E2 (compliant) + samples E2T + Stage3 vote ---
            dfs2, dico2 = stage3.load_task(task["objective"], filemap[tid])
            if len(dfs2) >= 2:
                stage3.align_keys(dfs2, dico2)
            t0 = time.perf_counter()
            g_rec_l = e2.run_codes_many([g_code], dfs2, OUTER, task["objective"])
            g_rec = g_rec_l[0] if g_rec_l else None
            dfs3, dico3 = stage3.load_task(task["objective"], filemap[tid])
            if len(dfs3) >= 2:
                stage3.align_keys(dfs3, dico3)
            s_rec = e2t.run_codes_many(s_codes, dfs3, OUTER, task["objective"])
            rec_vals = [g_rec] + list(s_rec)
            rec_vote, rec_ok = _vote(
                stage3, rec_vals, task["objective"], task["answer"], task["tol"]
            )
            t_rec = time.perf_counter() - t0

            # Stage3 baseline vote on same codes (independent singles)
            s3_vals = []
            for code in [g_code] + s_codes:
                fr, dd = stage3.load_task(task["objective"], filemap[tid])
                if len(fr) >= 2:
                    stage3.align_keys(fr, dd)
                s3_vals.append(stage3.run_code(code, fr, 1.5, task["objective"]))
            s3_vote, s3_ok = _vote(
                stage3, s3_vals, task["objective"], task["answer"], task["tol"]
            )

            rows_out.append(
                dict(
                    id=tid,
                    type=task["type"],
                    gold=task["answer"],
                    faithful_vote=fid_vote,
                    faithful_correct=fid_ok,
                    recovery_vote=rec_vote,
                    recovery_correct=rec_ok,
                    stage3_vote=s3_vote,
                    stage3_correct=s3_ok,
                    delta_rec_vs_fid=int(rec_ok) - int(fid_ok),
                    delta_rec_vs_s3=int(rec_ok) - int(s3_ok),
                    faithful_seconds=t_fid,
                    recovery_seconds=t_rec,
                    note="faithful≠private TEST1 score; hybrid replay only",
                )
            )

    write_csv(DIAG_OUT / "hybrid_test1_detail.csv", rows_out)
    n = len(rows_out)
    fid_acc = sum(r["faithful_correct"] for r in rows_out) / n if n else 0
    rec_acc = sum(r["recovery_correct"] for r in rows_out) / n if n else 0
    s3_acc = sum(r["stage3_correct"] for r in rows_out) / n if n else 0
    gain_vs_fid = sum(1 for r in rows_out if r["recovery_correct"] and not r["faithful_correct"])
    loss_vs_fid = sum(1 for r in rows_out if r["faithful_correct"] and not r["recovery_correct"])
    gain_vs_s3 = sum(1 for r in rows_out if r["recovery_correct"] and not r["stage3_correct"])
    loss_vs_s3 = sum(1 for r in rows_out if r["stage3_correct"] and not r["recovery_correct"])

    summary = [
        dict(
            arm="faithful_hybrid_TEST1",
            vote_accuracy=fid_acc,
            n=n,
            warning="NOT the private TEST1 104/120; many-path contaminated",
        ),
        dict(arm="recovery_E2T", vote_accuracy=rec_acc, n=n, warning=""),
        dict(arm="stage3_baseline", vote_accuracy=s3_acc, n=n, warning=""),
        dict(
            arm="Gain(recovery,faithful)",
            vote_accuracy=None,
            n=gain_vs_fid - loss_vs_fid,
            warning=f"gain={gain_vs_fid} loss={loss_vs_fid}",
        ),
        dict(
            arm="Gain(recovery,stage3)",
            vote_accuracy=None,
            n=gain_vs_s3 - loss_vs_s3,
            warning=f"gain={gain_vs_s3} loss={loss_vs_s3}",
        ),
    ]
    write_csv(DIAG_OUT / "hybrid_test1_summary.csv", summary)

    lines = [
        "# Hybrid TEST1 replay\n",
        f"**Cache:** `{path.name}`\n",
        "## Arms\n",
        "- **Fidèle:** greedy `test1.run_code` + samples `test1.run_codes_many` + Stage3.vote\n",
        "- **Recovery:** greedy E2 + samples E2T + Stage3.vote\n",
        "- **Stage3 baseline:** independent `run_code` 1.5s + Stage3.vote\n",
        "\n**WARNING:** Do **not** call the fidèle arm accuracy the real TEST1 private score "
        "(104/120). `test1_many` collapses under import pandas.\n",
        "| arm | vote accuracy | n / note |",
        "|---|---:|---|",
        f"| faithful_hybrid (NOT private TEST1) | {fid_acc:.4f} ({int(fid_acc*n)}/{n}) | many contaminated |",
        f"| recovery E2T | {rec_acc:.4f} ({int(rec_acc*n)}/{n}) | |",
        f"| stage3 baseline | {s3_acc:.4f} ({int(s3_acc*n)}/{n}) | |",
        f"| Gain(recovery, faithful) | {gain_vs_fid - loss_vs_fid} | +{gain_vs_fid} / -{loss_vs_fid} |",
        f"| Gain(recovery, stage3) | {gain_vs_s3 - loss_vs_s3} | +{gain_vs_s3} / -{loss_vs_s3} |",
        "\n## Task-level flips (recovery vs stage3)\n",
    ]
    for r in rows_out:
        if r["recovery_correct"] != r["stage3_correct"]:
            lines.append(
                f"- `{r['id']}`: stage3={r['stage3_correct']} recovery={r['recovery_correct']} "
                f"fidèle={r['faithful_correct']}"
            )
    if all(r["recovery_correct"] == r["stage3_correct"] for r in rows_out):
        lines.append("- (none)\n")
    text = "\n".join(lines)
    (DIAG_OUT / "HYBRID_TEST1_REPLAY.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
