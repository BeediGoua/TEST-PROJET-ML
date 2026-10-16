"""GO/NO-GO for TEST3-recovery — requires H1–H6 gates (no submission file)."""
from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"


def read_csv(name):
    path = OUT / name
    if not path.exists():
        return []
    return list(csv.DictReader(path.open(encoding="utf-8")))


def fnum(x):
    try:
        return float(x)
    except Exception:
        return None


def has_real_section(name: str, needle: str = "REAL_QWEN") -> bool:
    p = OUT / name
    return p.exists() and needle in p.read_text(encoding="utf-8")


def main():
    contract = read_csv("executor_contract.csv")
    ff = read_csv("forced_fallback_summary.csv")
    rules = read_csv("rules_ablation_summary.csv")
    timing = read_csv("batch_timing.csv")
    agree = read_csv("executor_agreement_summary.csv")
    h1 = OUT / "QWEN_PATTERN_FREQ.md"
    h5 = OUT / "FORCED_FALLBACK_QWEN.md"
    h3 = OUT / "ALIAS_VS_IMPORTLIB.md"
    h4 = OUT / "BATCH_ORDER.md"
    h6 = OUT / "TEST2_DECOMPOSITION.md"

    def contract_ok(agent, probe="import_pandas", fix="False"):
        for r in contract:
            if r["agent"] == agent and r["probe"] == probe and r["wrapper_alias_fix"] == fix:
                return r["ok"] == "True"
        return None

    e2_agree = None
    for r in agree:
        if r.get("executor") == "E2_alias":
            e2_agree = fnum(r.get("agree_rate"))
            break

    h1_real = has_real_section("QWEN_PATTERN_FREQ.md")
    h5_real = has_real_section("FORCED_FALLBACK_QWEN.md")
    h2_real = has_real_section("EXECUTOR_AGREEMENT.md")
    h3_real = has_real_section("ALIAS_VS_IMPORTLIB.md")
    h4_done = (OUT / "BATCH_ORDER.md").exists() and "**NOT RUN:**" not in (OUT / "BATCH_ORDER.md").read_text(encoding="utf-8")[:400]
    h6_real = has_real_section("TEST2_DECOMPOSITION.md")

    h4_sensitive = False
    if (OUT / "BATCH_ORDER.md").exists():
        h4_sensitive = "CROSS-TASK BATCHING IS DANGEROUS" in (OUT / "BATCH_ORDER.md").read_text(encoding="utf-8")

    checks = [
        ("Stage3 deterministic parity (public Tables 80/80)", True, "MEASURED prior"),
        ("Stage3 import_pandas PASS", contract_ok("stage3") is True, "MEASURED"),
        ("TEST1 samples import_pandas FAIL", contract_ok("test1") is False, "MEASURED"),
        ("TEST2 + alias fix PASS", contract_ok("test2", fix="True") is True, "MEASURED"),
        ("H1 Qwen pattern freqs (REAL cache)", h1_real, "REQUIRED"),
        ("H2 E2 agree_rate ≥ 0.99 on REAL cache", bool(h2_real and e2_agree is not None and e2_agree >= 0.99), "REQUIRED"),
        ("H3 alias vs importlib decision documented", h3.exists() if hasattr(h3, "exists") else (OUT / "ALIAS_VS_IMPORTLIB.md").exists(), "REQUIRED"),
        ("H3 REAL cache bake-off", h3_real, "REQUIRED"),
        ("H4 batch-order probe run", h4_done, "REQUIRED"),
        ("H4 no order sensitivity (or batch forbidden)", h4_done and not h4_sensitive, "REQUIRED"),
        ("H5 forced-fallback Qwen REAL", h5_real, "REQUIRED"),
        ("H6 TEST2 decomposition REAL", h6_real, "REQUIRED"),
        ("Linux/GPU p95 < 40s documented", False, "NOT RUN"),
        ("Scanner conformité", False, "NOT RUN"),
        ("No TEST3 submission file created", True, "POLICY"),
    ]

    required = [(n, ok, lvl) for n, ok, lvl in checks if lvl == "REQUIRED"]
    go = all(ok for _, ok, _ in required)

    lines = []
    lines.append("# GO / NO-GO — TEST3-recovery (pre-submission)\n")
    lines.append("## Decision\n")
    lines.append(f"**{'GO' if go else 'NO-GO'} for building/submitting TEST3-recovery.**\n")
    if not go:
        lines.append("### Why NO-GO\n")
        for n, ok, lvl in required:
            if not ok:
                lines.append(f"- FAIL: {n}")
        lines.append("")
        lines.append(
            "Harness scripts `07`–`12` are in place. Fill gates by running "
            "`colab_forced_fallback.ipynb` (Linux+CUDA), downloading `generations_*.json` "
            "+ replay CSV into `audit_independent/results/`, then re-running `07`–`12`.\n"
        )

    lines.append("## Checklist H1–H6\n")
    lines.append("| Check | Result | Level |")
    lines.append("|---|---|---|")
    for name, ok, level in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL/MISSING'} | {level} |")

    lines.append("\n## Artefact presence\n")
    for name in [
        "QWEN_PATTERN_FREQ.md",
        "EXECUTOR_AGREEMENT.md",
        "ALIAS_VS_IMPORTLIB.md",
        "BATCH_ORDER.md",
        "FORCED_FALLBACK_QWEN.md",
        "TEST2_DECOMPOSITION.md",
        "GO_NOGO.md",
    ]:
        p = OUT / name
        status = "present" if p.exists() else "missing"
        if p.exists() and "**NOT RUN:**" in p.read_text(encoding="utf-8")[:500]:
            status = "present (NOT RUN body)"
        lines.append(f"- `{name}`: {status}")

    if e2_agree is not None:
        lines.append(f"\n## H2 snapshot\n- E2_alias agree_rate = **{e2_agree:.4f}**\n")

    lines.append("\n## Frozen TEST3-recovery spec (only if GO)\n")
    lines.append("```")
    lines.append("STAGE3-COMPLIANT-RECOVERY")
    lines.append("Model: Qwen2.5-Coder-1.5B exact")
    lines.append("Rules/Prompt/Fits/No-files/Tables/Vote: Stage3 EXACT")
    lines.append("BUDGET 29 / MAX_NEW 500 / NSAMP 4 / default vote 0")
    lines.append("ONLY change: E2 executor (__dsh_pd alias) if H2/H3 PASS")
    lines.append("FORBIDDEN: calc_safe_v2, extended rules, reject-zero, default=1,")
    lines.append("           Qwen3, new prompts, inter-task batch")
    lines.append("```\n")

    lines.append("## Prior CPU diagnostic (still valid)\n")
    lines.append("| Agent | import_pandas contract |")
    lines.append("|---|---|")
    for agent, fix in [("stage3", "False"), ("test1", "False"), ("test2", "False"), ("test2", "True"), ("faithful", "False")]:
        ok = contract_ok(agent, fix=fix)
        lines.append(f"| {agent} fix={fix} | {ok} |")

    if rules:
        lines.append("\n## Rules ablation snapshot\n")
        for r in rules:
            if r.get("family") == "table" and not str(r.get("config", "")).startswith("shadow"):
                lines.append(
                    f"- `{r['config']}`: covered {r['covered']}/{r['n']}, "
                    f"correct {r['correct']}, wrong {r['wrong']}"
                )
        lines.append("")

    lines.append("\n## Next action\n")
    lines.append("1. Keep NO-GO until all REQUIRED gates PASS on a REAL_QWEN cache.")
    lines.append("2. Colab: `audit_independent/colab_forced_fallback.ipynb` → download cache+replay.")
    lines.append("3. Local: `python make_synthetic_cache.py` is smoke-only; then `07`…`12`, `06_go_nogo.py`.")
    lines.append("4. Only after GO: bake one Stage3+E2 agent file — not before.\n")

    text = "\n".join(lines)
    (OUT / "GO_NOGO.md").write_text(text, encoding="utf-8")
    (HERE.parents[0] / "GO_NOGO.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
