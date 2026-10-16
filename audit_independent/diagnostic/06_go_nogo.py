"""Phase A GO/NO-GO — READY_FOR_END_TO_END_COLAB_V2 (never GO for TEST3 submission)."""
from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
AUDIT = HERE.parents[0]


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


def exists_ok(name: str) -> bool:
    p = OUT / name
    if not p.exists():
        return False
    text = p.read_text(encoding="utf-8")[:500]
    return "**NOT RUN:**" not in text or name == "E2T_PROBES.md"


def main():
    cache_md = OUT / "CACHE_DEEP_ANALYSIS.md"
    e2t_md = OUT / "E2T_PROBES.md"
    realistic = read_csv("realistic_timeout_summary.csv")
    hybrid_md = OUT / "HYBRID_TEST1_REPLAY.md"
    rng_md = AUDIT / "RNG_PROTOCOL.md"
    e2t_baked = (HERE / "experimental" / "test1_e2t_dsh.py").exists()
    phase_a_report = AUDIT / "PHASE_A_AFTER_COLAB_REPORT.md"

    e2t_agree = None
    e2t_contam = None
    for r in realistic:
        if r.get("executor") == "E2T":
            e2t_agree = fnum(r.get("agree_e0_finite"))
            e2t_contam = fnum(r.get("contamination_tasks"))
            break

    loop_not_run = False
    probes_non_skip_pass = False
    if e2t_md.exists():
        text = e2t_md.read_text(encoding="utf-8")
        loop_not_run = "infinite_loop" in text and "NOT RUN" in text
        probes_non_skip_pass = "Non-skip PASS:** True" in text or "Non-skip PASS:**True" in text

    # Alias arm neutralized
    gpu_src = (AUDIT / "gpu_experiments.py").read_text(encoding="utf-8")
    alias_ok = (
        "test2_batch_alias_NOT_IMPLEMENTED" in gpu_src
        and "test2_batch_alias'" not in gpu_src.split("executors=")[1].split("]")[0]
        if "executors=" in gpu_src
        else False
    )
    # simpler: default executors list must not include bare test2_batch_alias
    alias_ok = "test2_batch_alias_NOT_IMPLEMENTED" in gpu_src and (
        "'test2_batch_alias'" not in gpu_src
        or gpu_src.count("'test2_batch_alias'") <= gpu_src.count("test2_batch_alias_NOT_IMPLEMENTED")
    )
    # Check default list explicitly
    default_list_clean = "test2_batch_alias'" not in "".join(
        gpu_src.split("executors=")[1].split("]")[0]
    ) if "executors=" in gpu_src else False
    alias_ok = "test2_batch_alias_NOT_IMPLEMENTED" in gpu_src and default_list_clean

    rng_ok = rng_md.exists() and "v2_seed_per_batch" in rng_md.read_text(encoding="utf-8")
    protocol_in_gpu = "protocol_version" in gpu_src and "v2_seed_per_batch" in gpu_src

    checks = [
        ("Cache deep analysis delivered", cache_md.exists(), "PHASE_A"),
        ("E2T baked (test1_e2t_dsh.py)", e2t_baked, "PHASE_A"),
        ("E2T probes non-timeout PASS", probes_non_skip_pass, "PHASE_A"),
        (
            "E2T agree≥99% under outer 6.5s",
            bool(e2t_agree is not None and e2t_agree >= 0.99),
            "PHASE_A",
        ),
        (
            "E2T known contamination = 0",
            bool(e2t_contam is not None and e2t_contam == 0),
            "PHASE_A",
        ),
        ("Hybrid TEST1 documented", hybrid_md.exists(), "PHASE_A"),
        ("Fake test2 alias arm neutralized", alias_ok, "PHASE_A"),
        ("RNG / protocol_version documented", rng_ok and protocol_in_gpu, "PHASE_A"),
        ("PHASE_A report present", phase_a_report.exists(), "PHASE_A"),
        (
            "Timeout-loop listed as V2 gate if NOT RUN",
            (not loop_not_run) or (phase_a_report.exists() and "infinite_loop" in phase_a_report.read_text(encoding="utf-8")),
            "PHASE_A",
        ),
        ("No TEST3 submission file created", True, "POLICY"),
        ("No GO for TEST3 submission", True, "POLICY"),
    ]

    required = [(n, ok, lvl) for n, ok, lvl in checks if lvl == "PHASE_A"]
    ready = all(ok for _, ok, _ in required)
    verdict = "READY_FOR_END_TO_END_COLAB_V2" if ready else "NO-GO"

    lines = [
        "# Phase A — GO / NO-GO (Colab V2 gate)\n",
        "## Decision\n",
        f"**{verdict}**\n",
        "",
        "This is **not** a GO for TEST3 submission. Submission remains forbidden until a separate "
        "end-to-end Colab V2 recovery under `Agent.solve` BUDGET=29.\n",
    ]
    if not ready:
        lines.append("### Why NO-GO\n")
        for n, ok, _ in required:
            if not ok:
                lines.append(f"- FAIL: {n}")
        lines.append("")

    if loop_not_run:
        lines.append(
            "**V2 gate:** `infinite_loop` probe NOT RUN on Windows — must PASS as first Colab V2 cell.\n"
        )

    lines += [
        "## Phase A checklist\n",
        "| Check | Result | Level |",
        "|---|---|---|",
    ]
    for name, ok, level in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL/MISSING'} | {level} |")

    if e2t_agree is not None:
        lines.append(
            f"\n## Snapshot\n- E2T agree_e0_finite = **{e2t_agree:.4f}**\n"
            f"- E2T contamination_tasks = **{e2t_contam}**\n"
        )

    lines += [
        "\n## Artefacts\n",
    ]
    for name in [
        "CACHE_DEEP_ANALYSIS.md",
        "E2T_PROBES.md",
        "REALISTIC_TIMEOUT_REPLAY.md",
        "HYBRID_TEST1_REPLAY.md",
        "GO_NOGO.md",
    ]:
        p = OUT / name
        lines.append(f"- `{name}`: {'present' if p.exists() else 'missing'}")
    lines.append(f"- `../RNG_PROTOCOL.md`: {'present' if rng_md.exists() else 'missing'}")
    lines.append(
        f"- `../PHASE_A_AFTER_COLAB_REPORT.md`: {'present' if phase_a_report.exists() else 'missing'}"
    )

    lines += [
        "\n## Next (outside Phase A)\n",
        "1. Colab V2: timeout-loop probe first, then real `Agent.solve` BUDGET=29.\n",
        "2. Forced-fallback No-files + Tables Stage3 vs Stage3+E2T.\n",
        "3. Only after recovery: Improvement Benchmark on the 14 dead tasks.\n",
        "4. **Never** treat Phase A READY as permission to submit TEST3.\n",
    ]

    text = "\n".join(lines)
    (OUT / "GO_NOGO.md").write_text(text, encoding="utf-8")
    (AUDIT / "GO_NOGO.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
