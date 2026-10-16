"""Phase A §5 — Stage3 / E2 / E2T replay with realistic outer timeout 6.5s."""
from __future__ import annotations

import tempfile
import time
from collections import defaultdict

from pretest3_common import (
    AUDIT_OUT,
    DIAG_OUT,
    EXP,
    analyze_code_patterns,
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
from build_experimental import build_test1_alias, build_test1_e2t

CACHE_NAME = "generations_34d6ece55b3c092a.json"
OUTER = 6.5
STAGE3_TO = 1.5


def _resolve_cache():
    preferred = AUDIT_OUT / CACHE_NAME
    if preferred.exists():
        return preferred
    for p in find_generation_caches():
        if "34d6ece55b3c092a" in p.name:
            return p
    raise FileNotFoundError(CACHE_NAME)


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
    e2 = load_path(EXP / "test1_alias_dsh.py", "e2")
    e2t = load_path(EXP / "test1_e2t_dsh.py", "e2t")

    from src.evaluation.core import _materialize_all

    detail = []
    times = {"stage3": [], "E2": [], "E2T": []}

    with tempfile.TemporaryDirectory(prefix="realistic_") as td:
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
            ordered = greedy + samples
            codes = [g.get("code") or "" for g in ordered]
            pats = [analyze_code_patterns(c) for c in codes]

            # Stage3: independent 1.5s each
            s3_vals = []
            t0 = time.perf_counter()
            for code in codes:
                fresh, dd = stage3.load_task(task["objective"], filemap[tid])
                if len(fresh) >= 2:
                    stage3.align_keys(fresh, dd)
                v = stage3.run_code(code, fresh, STAGE3_TO, task["objective"])
                s3_vals.append(v)
            times["stage3"].append(time.perf_counter() - t0)

            dfs, dico = stage3.load_task(task["objective"], filemap[tid])
            if len(dfs) >= 2:
                stage3.align_keys(dfs, dico)

            t0 = time.perf_counter()
            e2_vals = e2.run_codes_many(codes, dfs, OUTER, task["objective"])
            times["E2"].append(time.perf_counter() - t0)

            dfs2, dico2 = stage3.load_task(task["objective"], filemap[tid])
            if len(dfs2) >= 2:
                stage3.align_keys(dfs2, dico2)
            t0 = time.perf_counter()
            e2t_vals = e2t.run_codes_many(codes, dfs2, OUTER, task["objective"])
            times["E2T"].append(time.perf_counter() - t0)

            # Pad
            while len(e2_vals) < len(codes):
                e2_vals.append(None)
            while len(e2t_vals) < len(codes):
                e2t_vals.append(None)

            # Contamination heuristic: sibling finite under Stage3 but None under E2,
            # while another candidate has syntax/empty — batch contagion signature
            n_contam_e2 = 0
            n_contam_e2t = 0
            for i in range(len(codes)):
                s3_ok = s3_vals[i] is not None
                if s3_ok and e2_vals[i] is None:
                    # any other broken syntax in batch?
                    if any(not pats[j]["syntax_ok"] for j in range(len(codes)) if j != i):
                        n_contam_e2 += 1
                if s3_ok and e2t_vals[i] is None:
                    if any(not pats[j]["syntax_ok"] for j in range(len(codes)) if j != i):
                        n_contam_e2t += 1

            for i, g in enumerate(ordered):
                detail.append(
                    dict(
                        id=tid,
                        phase=g["phase"],
                        sample=g.get("sample", 0),
                        import_pandas=pats[i]["import_pandas_as_pd"],
                        syntax_ok=pats[i]["syntax_ok"],
                        stage3=s3_vals[i],
                        E2=e2_vals[i],
                        E2T=e2t_vals[i],
                        agree_E2=values_agree(s3_vals[i], e2_vals[i]),
                        agree_E2T=values_agree(s3_vals[i], e2t_vals[i]),
                        task_contam_e2=n_contam_e2,
                        task_contam_e2t=n_contam_e2t,
                    )
                )

    write_csv(DIAG_OUT / "realistic_timeout_detail.csv", detail)

    def pct(xs):
        if not xs:
            return dict(p50=None, p95=None, max=None)
        xs = sorted(xs)
        def q(p):
            i = min(len(xs) - 1, max(0, int(round(p * (len(xs) - 1)))))
            return xs[i]
        return dict(p50=q(0.50), p95=q(0.95), max=xs[-1])

    summary = []
    for label, key in [("E2", "agree_E2"), ("E2T", "agree_E2T")]:
        rows = detail
        e0_finite = [d for d in rows if d["stage3"] is not None]
        agree_n = sum(1 for d in e0_finite if d[key])
        rate = agree_n / len(e0_finite) if e0_finite else 0.0
        ip = [d for d in e0_finite if d["import_pandas"]]
        ip_agree = sum(1 for d in ip if d[key]) / len(ip) if ip else None
        exec_rate = sum(1 for d in rows if d[label] is not None) / len(rows) if rows else 0.0
        contam_tasks = len(
            {
                d["id"]
                for d in rows
                if d[f"task_contam_{'e2' if label == 'E2' else 'e2t'}"] > 0
            }
        )
        tstat = pct(times[label])
        summary.append(
            dict(
                executor=label,
                n_programs=len(rows),
                n_e0_finite=len(e0_finite),
                agree_e0_finite=rate,
                agree_import_pandas=ip_agree,
                exec_rate=exec_rate,
                contamination_tasks=contam_tasks,
                gate_99=rate >= 0.99,
                gate_0_contam=contam_tasks == 0,
                outer_timeout=OUTER,
                **{f"task_seconds_{k}": v for k, v in tstat.items()},
            )
        )

    # stage3 timing row
    tstat = pct(times["stage3"])
    summary.append(
        dict(
            executor="stage3",
            n_programs=len(detail),
            n_e0_finite=sum(1 for d in detail if d["stage3"] is not None),
            agree_e0_finite=1.0,
            agree_import_pandas=1.0,
            exec_rate=sum(1 for d in detail if d["stage3"] is not None) / len(detail) if detail else 0,
            contamination_tasks=0,
            gate_99=True,
            gate_0_contam=True,
            outer_timeout=STAGE3_TO,
            **{f"task_seconds_{k}": v for k, v in tstat.items()},
        )
    )
    write_csv(DIAG_OUT / "realistic_timeout_summary.csv", summary)

    lines = [
        "# Realistic timeout replay (outer 6.5s)\n",
        f"**Cache:** `{path.name}`\n",
        f"**Outer many:** `{OUTER}` = EXEC_TIMEOUT(5)+1.5 (TEST1 solve)\n",
        f"**Stage3 single:** `{STAGE3_TO}`\n",
        "| executor | agree E0-finite | agree import_pandas | exec_rate | contam_tasks | gate≥99% | p50/p95/max task-s |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for s in summary:
        ip = s["agree_import_pandas"]
        ip_s = f"{ip:.4f}" if ip is not None else "n/a"
        lines.append(
            f"| {s['executor']} | {s['agree_e0_finite']:.4f} | {ip_s} | "
            f"{s['exec_rate']:.4f} | {s['contamination_tasks']} | {s['gate_99']} | "
            f"{s['task_seconds_p50']:.3f}/{s['task_seconds_p95']:.3f}/{s['task_seconds_max']:.3f} |"
        )
    e2t = next(s for s in summary if s["executor"] == "E2T")
    lines.append(
        f"\n**Gate E2T:** agree≥99%={'PASS' if e2t['gate_99'] else 'FAIL'}; "
        f"0 contam={'PASS' if e2t['gate_0_contam'] else 'FAIL'}\n"
    )
    text = "\n".join(lines)
    (DIAG_OUT / "REALISTIC_TIMEOUT_REPLAY.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
