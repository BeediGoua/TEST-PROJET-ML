"""Phase A §2 — deep analysis of frozen Qwen cache (no regeneration)."""
from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from pretest3_common import (
    AUDIT_OUT,
    DIAG_OUT,
    HANDOFF,
    find_generation_caches,
    is_real_qwen_cache,
    load_cache,
    write_csv,
)
import audit as audit_mod

CACHE_NAME = "generations_34d6ece55b3c092a.json"


def _resolve_cache() -> Path:
    preferred = AUDIT_OUT / CACHE_NAME
    if preferred.exists():
        return preferred
    for p in find_generation_caches():
        if "34d6ece55b3c092a" in p.name:
            return p
    raise FileNotFoundError(CACHE_NAME)


def _classify_error(err: str, code: str, value) -> str:
    err = str(err or "")
    code = code or ""
    if value is not None and pd.notna(value):
        return "numeric"
    if not code.strip():
        return "missing_answer"
    if "SyntaxError" in err or (not _syntax_ok(code)):
        return "SyntaxError"
    if not re.search(r"\banswer\s*=", code):
        return "missing_answer"
    for name in (
        "KeyError",
        "NameError",
        "TypeError",
        "AttributeError",
        "IndexError",
        "Timeout",
        "timeout",
    ):
        if name.lower() in err.lower() or name in err:
            if "timeout" in name.lower():
                return "timeout"
            return name
    if "non-finite" in err.lower() or "nonfinite" in err.lower():
        return "non_finite"
    if "batch returned None" in err or err.strip() == "":
        # try infer from code
        if not re.search(r"\banswer\s*=", code):
            return "missing_answer"
        return "other"
    return "other"


def _syntax_ok(code: str) -> bool:
    try:
        ast.parse(code or "")
        return True
    except SyntaxError:
        return False


def _classify_dead_task(task, codes, values, errors) -> tuple[str, str]:
    """Return (cause, error_kind) where error_kind is reasoning|execution|mixed."""
    obj = str(task.get("objective", "")).lower()
    n_exec_fail = sum(1 for v in values if v is None or (isinstance(v, float) and pd.isna(v)))
    n = len(values)
    if n_exec_fail == n:
        kind = "execution"
    elif n_exec_fail == 0:
        kind = "reasoning"
    else:
        kind = "mixed"

    joined = "\n".join(codes)
    errj = "\n".join(str(e) for e in errors)
    if all(not re.search(r"\banswer\s*=", c or "") for c in codes):
        return "missing_answer", "execution"
    if "join" in obj or "merge" in joined.lower():
        return "join", kind
    if any(x in obj for x in ("date", "month", "year", "day")):
        return "date", kind
    if "missing" in obj or "nan" in joined.lower() or "isna" in joined.lower():
        return "missing_values", kind
    if "ddof" in joined or "std(" in joined or "var(" in joined:
        return "ddof_statistic", kind
    if "filter" in str(task.get("type", "")) or "query" in joined.lower():
        return "wrong_filter", kind
    if "group" in str(task.get("type", "")) or "groupby" in joined.lower():
        return "aggregation", kind
    if "KeyError" in errj or "column" in errj.lower():
        return "wrong_column", kind
    if n_exec_fail == n:
        return "runtime_failure", "execution"
    if kind == "reasoning":
        return "misunderstanding", "reasoning"
    return "other", kind


def main():
    path = _resolve_cache()
    cache = load_cache(path)
    assert is_real_qwen_cache(cache), "cache must be REAL_QWEN"
    replay_path = path.with_name(path.stem + "_replay.csv")
    if not replay_path.exists():
        raise FileNotFoundError(replay_path)

    gold = {t["id"]: t for t in __import__("json").loads((HANDOFF / "dev.json").read_text(encoding="utf-8"))}
    stage3 = audit_mod.load("stage3")
    rows = cache["rows"]
    replay = pd.read_csv(replay_path)
    s3 = replay[replay["executor"] == "stage3"].copy()

    # Index generations
    by_id = defaultdict(list)
    for r in rows:
        by_id[r["id"]].append(r)

    # Per-task candidate correctness from stage3 replay
    task_stats = []
    oracle_at = {k: 0 for k in range(1, 5)}
    vote_at = {k: 0 for k in range(1, 5)}
    buckets = Counter()
    dead = []
    taxonomy = Counter()
    reason_vs_exec = Counter()

    for tid, gens in by_id.items():
        task = gold[tid]
        tol = float(task["tol"])
        ans = float(task["answer"])
        # order: greedy then samples by sample index
        greedy = [g for g in gens if g["phase"] == "greedy"]
        samples = sorted(
            [g for g in gens if g["phase"] == "samples"], key=lambda x: int(x.get("sample", 0))
        )
        ordered = greedy + samples

        def lookup(g):
            m = s3[
                (s3["id"] == tid)
                & (s3["phase"] == g["phase"])
                & (s3["sample"] == g["sample"])
            ]
            if len(m) == 0:
                return None, "", False
            row = m.iloc[0]
            val = row["value"]
            if pd.isna(val):
                val = None
            else:
                val = float(val)
            correct = bool(row["correct"]) if not pd.isna(row["correct"]) else False
            return val, str(row.get("error") or ""), correct

        vals, errs, corrects = [], [], []
        for g in ordered:
            v, e, c = lookup(g)
            vals.append(v)
            errs.append(e)
            corrects.append(c)
            taxonomy[_classify_error(e, g.get("code") or "", v)] += 1

        g_ok = bool(corrects[0]) if corrects else False
        s_ok = any(corrects[1:]) if len(corrects) > 1 else False
        if g_ok and s_ok:
            buckets["both"] += 1
        elif g_ok and not s_ok:
            buckets["greedy_only"] += 1
        elif (not g_ok) and s_ok:
            buckets["samples_only"] += 1
        else:
            buckets["neither"] += 1

        for k in range(1, 5):
            # greedy + first k samples  → k here means number of samples after greedy for oracle@k
            # Plan: oracle@k = among greedy + samples 0..k-1
            subset_corr = corrects[: 1 + k]
            if any(subset_corr):
                oracle_at[k] += 1
            cands = []
            for i, v in enumerate(vals[: 1 + k]):
                if v is None:
                    continue
                w = 1.5 if i == 0 else 1.0
                cands.append((v, w))
            nd = stage3.decimals(task["objective"])
            voted = stage3.vote(cands, nd) if cands else None
            if nd is not None and voted is not None:
                try:
                    voted = round(voted, nd)
                except Exception:
                    pass
            if voted is not None and abs(float(voted) - ans) <= tol:
                vote_at[k] += 1

        if (not g_ok) and (not s_ok):
            cause, ekind = _classify_dead_task(
                task, [g.get("code") or "" for g in ordered], vals, errs
            )
            reason_vs_exec[ekind] += 1
            dead.append(
                dict(
                    id=tid,
                    type=task["type"],
                    objective=task["objective"][:300],
                    gold=ans,
                    tol=tol,
                    cause=cause,
                    error_kind=ekind,
                    greedy_value=vals[0] if vals else None,
                    greedy_error=errs[0] if errs else "",
                    sample_values=str(vals[1:]),
                    sample_errors=str(errs[1:])[:500],
                    greedy_code=(ordered[0].get("code") or "")[:1500] if ordered else "",
                    sample0_code=(ordered[1].get("code") or "")[:800] if len(ordered) > 1 else "",
                )
            )

        task_stats.append(
            dict(
                id=tid,
                type=task["type"],
                greedy_correct=g_ok,
                samples_correct=s_ok,
                bucket=(
                    "both"
                    if g_ok and s_ok
                    else "greedy_only"
                    if g_ok
                    else "samples_only"
                    if s_ok
                    else "neither"
                ),
            )
        )

    n_tasks = len(by_id)
    write_csv(DIAG_OUT / "cache_oracle_vote_at_k.csv", [
        dict(k=k, oracle_at_k=oracle_at[k] / n_tasks, vote_at_k=vote_at[k] / n_tasks,
             oracle_count=oracle_at[k], vote_count=vote_at[k], n_tasks=n_tasks)
        for k in range(1, 5)
    ])
    write_csv(DIAG_OUT / "cache_task_buckets.csv", task_stats)
    write_csv(DIAG_OUT / "cache_dead_tasks.csv", dead)
    write_csv(
        DIAG_OUT / "cache_error_taxonomy.csv",
        [dict(category=k, count=v) for k, v in taxonomy.most_common()],
    )

    lines = [
        "# CACHE DEEP ANALYSIS — Phase A\n",
        f"**Cache:** `{path.name}` (REAL_QWEN, frozen)\n",
        f"**Tasks:** {n_tasks} | **Programs:** {len(rows)}\n",
        "## Definitions\n",
        "- Candidates ordered: greedy, then samples 0..k-1.\n",
        "- `oracle@k`: any correct among greedy + first k samples.\n",
        "- `vote@k`: Stage3.vote on finite values among those candidates.\n",
        "## oracle@k / vote@k\n",
        "| k | oracle@k | vote@k |",
        "|---:|---:|---:|",
    ]
    for k in range(1, 5):
        lines.append(
            f"| {k} | {oracle_at[k]/n_tasks:.4f} ({oracle_at[k]}) | "
            f"{vote_at[k]/n_tasks:.4f} ({vote_at[k]}) |"
        )

    lines += [
        "\n## Greedy vs samples buckets\n",
        f"- both: **{buckets['both']}**",
        f"- greedy_only: **{buckets['greedy_only']}**",
        f"- samples_only (sampling saves greedy): **{buckets['samples_only']}**",
        f"- neither (dead): **{buckets['neither']}**\n",
        "## Dead tasks (neither)\n",
        f"Count: **{len(dead)}**\n",
    ]
    cause_c = Counter(d["cause"] for d in dead)
    lines.append("| cause | count |")
    lines.append("|---|---:|")
    for c, n in cause_c.most_common():
        lines.append(f"| {c} | {n} |")
    lines.append("\n### error_kind (reasoning vs execution)\n")
    for k, n in reason_vs_exec.most_common():
        lines.append(f"- {k}: {n}")
    lines.append("\n### Dead task ids\n")
    for d in dead:
        lines.append(
            f"- `{d['id']}` ({d['type']}): cause={d['cause']} kind={d['error_kind']} gold={d['gold']}"
        )

    lines += [
        "\n## Stage3 non-numeric program taxonomy\n",
        "| category | count |",
        "|---|---:|",
    ]
    for k, v in taxonomy.most_common():
        if k == "numeric":
            continue
        lines.append(f"| {k} | {v} |")
    lines.append(f"\n- numeric programs: {taxonomy.get('numeric', 0)}")
    lines.append(
        "\n## Note\n"
        "These 14 dead tasks are the seed of a future Improvement Benchmark — "
        "not a signal to add regex rules or change prompts in Phase A.\n"
    )

    text = "\n".join(lines)
    (DIAG_OUT / "CACHE_DEEP_ANALYSIS.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
