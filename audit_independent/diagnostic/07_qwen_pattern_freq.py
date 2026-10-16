"""H1 — frequency of wrapper-breaking patterns in Qwen Table generations."""
from __future__ import annotations

from collections import defaultdict

from pretest3_common import (
    DIAG_OUT,
    analyze_code_patterns,
    find_generation_caches,
    is_real_qwen_cache,
    load_cache,
    write_csv,
    write_not_run,
)


def main():
    caches = find_generation_caches()
    if not caches:
        write_not_run(
            DIAG_OUT / "QWEN_PATTERN_FREQ.md",
            "H1 — Qwen pattern frequency",
            "No generations_*.json found. Run Colab notebook "
            "`audit_independent/colab_forced_fallback.ipynb` then place the cache under "
            "`audit_independent/results/`.",
        )
        print("NOT RUN: no cache")
        return

    path = caches[0]
    cache = load_cache(path)
    real = is_real_qwen_cache(cache)
    rows_out = []
    counts = defaultdict(int)
    n = 0
    by_phase = defaultdict(lambda: defaultdict(int))

    for r in cache.get("rows") or []:
        code = r.get("code") or ""
        pat = analyze_code_patterns(code)
        n += 1
        phase = r.get("phase", "?")
        by_phase[phase]["n"] += 1
        for k, v in pat.items():
            if k == "syntax_error":
                continue
            if v is True:
                counts[k] += 1
                by_phase[phase][k] += 1
        rows_out.append(
            dict(
                cache=path.name,
                id=r.get("id"),
                type=r.get("type"),
                phase=phase,
                sample=r.get("sample"),
                **{k: pat[k] for k in pat if k != "syntax_error"},
                syntax_error=pat["syntax_error"],
            )
        )

    write_csv(DIAG_OUT / "qwen_pattern_freq.csv", rows_out)

    def rate(key):
        return counts[key] / n if n else 0.0

    lines = [
        "# H1 — Qwen pattern frequency\n",
        f"**Cache:** `{path.name}` ({'REAL_QWEN' if real else 'SYNTHETIC_OR_PARTIAL'})\n",
        f"**Programs analyzed:** {n}\n",
        "## Overall rates\n",
        "| Pattern | count | rate |",
        "|---|---:|---:|",
        f"| import pandas as pd | {counts['import_pandas_as_pd']} | {rate('import_pandas_as_pd'):.4f} |",
        f"| any import | {counts['any_import']} | {rate('any_import'):.4f} |",
        f"| rebind pd | {counts['rebind_pd']} | {rate('rebind_pd'):.4f} |",
        f"| syntax_ok False | {n - counts['syntax_ok']} | {1 - rate('syntax_ok'):.4f} |",
        f"| empty / no answer (trunc heuristic) | {counts['truncated_heuristic']} | {rate('truncated_heuristic'):.4f} |",
        "",
        "## By phase\n",
    ]
    for phase, c in sorted(by_phase.items()):
        nn = c["n"] or 1
        lines.append(f"### {phase} (n={c['n']})")
        lines.append(
            f"- import_pandas_as_pd: {c.get('import_pandas_as_pd', 0) / nn:.4f}"
        )
        lines.append(f"- any_import: {c.get('any_import', 0) / nn:.4f}")
        lines.append(
            f"- syntax failures: {(nn - c.get('syntax_ok', 0)) / nn:.4f}"
        )
        lines.append("")

    lines.append("## Interpretation\n")
    if not real:
        lines.append(
            "- **NOT a real Qwen cache** — rates are not usable for private attribution.\n"
        )
    else:
        ip = rate("import_pandas_as_pd")
        lines.append(
            f"- Measured `import pandas as pd` rate = **{ip:.4f}** on forced-fallback generations.\n"
        )
        if ip < 0.01:
            lines.append(
                "- Low rate: pandas scope bug may exist but is unlikely to explain all of TEST1 −8 Tables alone.\n"
            )
        elif ip >= 0.05:
            lines.append(
                "- Material rate: with 4 samples/task, amplification can wipe self-consistency votes.\n"
            )
        else:
            lines.append(
                "- Moderate rate: bug is a plausible contributor; combine with H2/H5 before attributing points.\n"
            )

    (DIAG_OUT / "QWEN_PATTERN_FREQ.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
