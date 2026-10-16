"""H5 — Stage3 forced-fallback metrics on cached Qwen Table generations."""
from __future__ import annotations

import platform

from pretest3_common import (
    AUDIT_OUT,
    DIAG_OUT,
    find_generation_caches,
    is_real_qwen_cache,
    load_cache,
    table_tasks,
    write_csv,
    write_not_run,
)


def _summarize_like_gpu(rows, gold, vote_fn, decimals_fn):
    """Mirror gpu_experiments.summarize_replay with greedy accuracy extras."""
    import pandas as pd

    data = pd.DataFrame(rows)
    out = []
    for (executor, tid), g in data.groupby(["executor", "id"]):
        task = gold[tid]
        candidates = [
            (r.value, 1.5 if r.phase == "greedy" else 1.0)
            for r in g.itertuples()
            if pd.notna(r.value)
        ]
        nd = decimals_fn(task["objective"]) if decimals_fn else None
        v = vote_fn(candidates, nd)
        if nd is not None:
            try:
                v = round(v, nd)
            except Exception:
                pass
        greedy = g[g.phase == "greedy"]
        samples = g[g.phase == "samples"]
        out.append(
            dict(
                executor=executor,
                id=tid,
                type=task.get("type"),
                execution_rate=float(g.value.notna().mean()),
                greedy_correct=bool(greedy["correct"].any()) if len(greedy) else False,
                oracle_samples_at4=bool(samples["correct"].any()) if len(samples) else False,
                oracle_greedy_plus4=bool(g.correct.any()),
                vote_correct=abs(float(v) - float(task["answer"])) <= float(task["tol"])
                if v is not None
                else False,
            )
        )
    return pd.DataFrame(out)


def main():
    caches = find_generation_caches()
    if not caches:
        write_not_run(
            DIAG_OUT / "FORCED_FALLBACK_QWEN.md",
            "H5 — Stage3 forced-fallback Qwen",
            "No generations_*.json. Run Colab `colab_forced_fallback.ipynb`.",
            "CPU proxy in `FORCED_FALLBACK.md` is **not** a substitute for this gate.\n",
        )
        print("NOT RUN: no cache")
        return

    path = caches[0]
    cache = load_cache(path)
    real = is_real_qwen_cache(cache)

    # Prefer Linux replay CSV produced by gpu_experiments.replay_cache
    replay_csv = path.with_name(path.stem + "_replay.csv")
    alt = AUDIT_OUT / replay_csv.name
    if not replay_csv.exists() and alt.exists():
        replay_csv = alt

    import pandas as pd
    import audit as audit_mod

    gold = {t["id"]: t for t in table_tasks()}
    stage3 = audit_mod.load("stage3")

    if replay_csv.exists():
        rows = pd.read_csv(replay_csv).to_dict("records")
        # normalize types
        for r in rows:
            if r.get("value") == "" or (isinstance(r.get("value"), float) and pd.isna(r["value"])):
                r["value"] = None
            elif r.get("value") is not None:
                try:
                    r["value"] = float(r["value"])
                except Exception:
                    pass
            if isinstance(r.get("correct"), str):
                r["correct"] = r["correct"].lower() in ("true", "1", "yes")
        source = f"replay CSV `{replay_csv.name}`"
    elif platform.system() == "Linux":
        # Attempt live replay
        import sys

        sys.path.insert(0, str(DIAG_OUT.parents[0]))
        from gpu_experiments import replay_cache, summarize_replay

        rows = replay_cache(path)
        source = "live replay_cache"
    else:
        write_not_run(
            DIAG_OUT / "FORCED_FALLBACK_QWEN.md",
            "H5 — Stage3 forced-fallback Qwen",
            f"Cache `{path.name}` present but no `*_replay.csv` and platform is "
            f"{platform.system()} (official replay requires Linux).",
            "Download replay from Colab after `replay_cache()`, or re-run on Linux.\n"
            f"Real Qwen cache: {real}\n"
            "repair_gain: **NOT RUN** (requires paired generate with/without DSH_NO_REPAIR).\n",
        )
        print("NOT RUN: need Linux replay")
        return

    # Filter stage3 executor rows for H5 headline
    df = _summarize_like_gpu(rows, gold, stage3.vote, stage3.decimals)
    per_exec = (
        df.groupby("executor")
        .agg(
            tasks=("id", "count"),
            execution_rate=("execution_rate", "mean"),
            greedy_accuracy=("greedy_correct", "mean"),
            oracle_samples_at4=("oracle_samples_at4", "mean"),
            oracle_greedy_plus4=("oracle_greedy_plus4", "mean"),
            vote_accuracy=("vote_correct", "mean"),
        )
        .reset_index()
    )
    per_type = (
        df[df.executor.str.contains("stage3")]
        .groupby("type")
        .agg(
            tasks=("id", "count"),
            greedy_accuracy=("greedy_correct", "mean"),
            oracle_greedy_plus4=("oracle_greedy_plus4", "mean"),
            vote_accuracy=("vote_correct", "mean"),
            execution_rate=("execution_rate", "mean"),
        )
        .reset_index()
        if "type" in df.columns
        else pd.DataFrame()
    )

    per_exec.to_csv(DIAG_OUT / "forced_fallback_qwen_by_executor.csv", index=False)
    if len(per_type):
        per_type.to_csv(DIAG_OUT / "forced_fallback_qwen_by_type.csv", index=False)
    df.to_csv(DIAG_OUT / "forced_fallback_qwen_per_task.csv", index=False)

    lines = [
        "# H5 — Stage3 forced-fallback Qwen (80 Tables)\n",
        f"**Cache:** `{path.name}` ({'REAL_QWEN' if real else 'SYNTHETIC_OR_PARTIAL'})\n",
        f"**Source:** {source}\n",
        f"**Platform:** {platform.platform()}\n",
        "## By executor\n",
        per_exec.to_markdown(index=False)
        if hasattr(per_exec, "to_markdown")
        else per_exec.to_string(index=False),
        "",
        "## Stage3 by table family\n",
        per_type.to_markdown(index=False)
        if len(per_type) and hasattr(per_type, "to_markdown")
        else (per_type.to_string(index=False) if len(per_type) else "_n/a_"),
        "",
        "## repair_gain\n",
        "**NOT RUN** — requires a second generation pass with `DSH_NO_REPAIR` "
        "(generate_cache currently stores greedy+samples only, not repair).\n",
        "## Interpretation\n",
    ]
    if not real:
        lines.append("- Synthetic/partial cache → **do not** use for GO.\n")
    else:
        s3 = per_exec[per_exec.executor.str.contains("stage3")]
        if len(s3):
            row = s3.iloc[0]
            lines.append(
                f"- Stage3 vote_accuracy ≈ **{row['vote_accuracy']:.3f}** "
                f"oracle_greedy_plus4 ≈ **{row['oracle_greedy_plus4']:.3f}** "
                f"on forced-fallback public Tables.\n"
            )
            lines.append(
                "- This is the missing baseline for private Tables LLM path attribution.\n"
            )

    # Prefer simple markdown table without tabulate dependency
    def df_md(frame):
        if frame is None or not len(frame):
            return "_empty_"
        cols = list(frame.columns)
        out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for _, r in frame.iterrows():
            out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
        return "\n".join(out)

    lines = [
        "# H5 — Stage3 forced-fallback Qwen (80 Tables)\n",
        f"**Cache:** `{path.name}` ({'REAL_QWEN' if real else 'SYNTHETIC_OR_PARTIAL'})\n",
        f"**Source:** {source}\n",
        f"**Platform:** {platform.platform()}\n",
        "## By executor\n",
        df_md(per_exec),
        "",
        "## Stage3 by table family\n",
        df_md(per_type) if len(per_type) else "_n/a_",
        "",
        "## repair_gain\n",
        "**NOT RUN** — requires a second generation pass with `DSH_NO_REPAIR`.\n",
        "## Interpretation\n",
    ]
    if not real:
        lines.append("- Synthetic/partial cache → **do not** use for GO.\n")
    else:
        s3 = per_exec[per_exec["executor"].astype(str).str.contains("stage3")]
        if len(s3):
            row = s3.iloc[0]
            lines.append(
                f"- Stage3 vote_accuracy ≈ **{float(row['vote_accuracy']):.3f}** "
                f"oracle_greedy_plus4 ≈ **{float(row['oracle_greedy_plus4']):.3f}**.\n"
            )

    (DIAG_OUT / "FORCED_FALLBACK_QWEN.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
