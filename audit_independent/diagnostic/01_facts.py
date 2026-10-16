"""Step A — MEASURED facts table: local vs private, what each protocol measured."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
HANDOFF = HERE.parents[1] / "CODEX_AUDIT_HANDOFF"
AUDIT_RES = HERE.parents[0] / "results"
OUT.mkdir(parents=True, exist_ok=True)

PRIVATE = [
    dict(agent="stage3", private_total=92.5, private_nf=95.6, private_tables=88.0, private_fits=96.0,
         private_correct_nf=43, private_correct_tables=44, private_correct_fits=24,
         evidence="user-reported / CODEX_AUDIT_PROMPT", level="MEASURED_reported"),
    dict(agent="test1", private_total=86.7, private_nf=88.9, private_tables=80.0, private_fits=96.0,
         private_correct_nf=40, private_correct_tables=40, private_correct_fits=24,
         evidence="user-reported / CODEX_AUDIT_PROMPT", level="MEASURED_reported"),
    dict(agent="v10", private_total=81.7, private_nf=88.9, private_tables=68.0, private_fits=96.0,
         private_correct_nf=40, private_correct_tables=34, private_correct_fits=24,
         evidence="user-reported / CODEX_AUDIT_PROMPT", level="MEASURED_reported"),
    dict(agent="test2", private_total=77.5, private_nf=95.6, private_tables=52.0, private_fits=96.0,
         private_correct_nf=43, private_correct_tables=26, private_correct_fits=24,
         evidence="user-reported / CODEX_AUDIT_PROMPT", level="MEASURED_reported"),
    dict(agent="minimal", private_total=None, private_nf=None, private_tables=None, private_fits=None,
         private_correct_nf=None, private_correct_tables=None, private_correct_fits=None,
         evidence="not submitted", level="MEASURED"),
]

PROTOCOLS = [
    dict(protocol="local_deterministic_core",
         what="evaluate_deterministic: rules only via calc_rules/table_*/fit_rules",
         full_solve="no", llm="no", batch8="no", budget40="no",
         where="projects/src/evaluation/core.py",
         typical_claim="v10=180/180, Stage3=140/180",
         predicts_private="no"),
    dict(protocol="audit_real_solve_stub",
         what="Agent.solve with generate stubbed empty; rule coverage only",
         full_solve="yes_stubbed", llm="no", batch8="no", budget40="no",
         where="projects/audit_independent/audit.py",
         typical_claim="tables 80/80 covered for all agents",
         predicts_private="no"),
    dict(protocol="metamorphic_ood_rules",
         what="distractors / OOD holdouts on deterministic rules",
         full_solve="no", llm="no", batch8="no", budget40="no",
         where="projects/scripts/run_metamorphic.py, run_ood.py",
         typical_claim="v10 0 FP; OOD5 48/48 abstentions",
         predicts_private="partial_abstention_risk_only"),
    dict(protocol="runtime_smoke",
         what="run_codes_many on trivial answer=2+2; no Qwen",
         full_solve="no", llm="no", batch8="smoke", budget40="no",
         where="projects/src/evaluation/runtime.py",
         typical_claim="~14s for 8 trivial fallbacks",
         predicts_private="no"),
    dict(protocol="executor_probes",
         what="fixed programs through run_code / run_codes_many / run_code_batch",
         full_solve="no", llm="no", batch8="no", budget40="no",
         where="projects/audit_independent/probes.py",
         typical_claim="pandas UnboundLocalError; SyntaxError contagion",
         predicts_private="mechanism_only"),
    dict(protocol="ml_arena_private",
         what="Agent.solve + mounted Qwen + scoring.run_agent batches of 8 / 40s",
         full_solve="yes", llm="yes", batch8="yes", budget40="yes",
         where="ML-Arena challenge 194",
         typical_claim="Stage3 92.5 champion",
         predicts_private="yes_is_the_target"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_dev_summary():
    path = AUDIT_RES / "dev_summary.csv"
    if not path.exists():
        return {}
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out = {}
    for r in rows:
        out.setdefault(r["agent"], {})[r["family"]] = r
    return out


def main():
    summary = load_dev_summary()
    rows = []
    for p in PRIVATE:
        agent = p["agent"]
        local = summary.get(agent, {})
        rows.append({
            **p,
            "local_calc_covered": local.get("calc", {}).get("covered"),
            "local_calc_correct": local.get("calc", {}).get("correct"),
            "local_calc_total": local.get("calc", {}).get("total"),
            "local_table_covered": local.get("table", {}).get("covered"),
            "local_table_correct": local.get("table", {}).get("correct"),
            "local_table_total": local.get("table", {}).get("total"),
            "local_fit_covered": local.get("fit", {}).get("covered"),
            "local_fit_correct": local.get("fit", {}).get("correct"),
            "local_fit_total": local.get("fit", {}).get("total"),
            "artifact": {
                "stage3": "STAGE3_SUBMITTED_92_5.py",
                "test1": "TEST1_SUBMITTED_86_7.py",
                "test2": "TEST2_SUBMITTED_77_5.py",
                "minimal": "TEST2_MINIMAL_NOT_SUBMITTED.py",
                "v10": "V10_SUBMITTED_81_7.py",
            }.get(agent),
        })

    with (OUT / "facts_scores.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    with (OUT / "facts_protocols.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(PROTOCOLS[0].keys()))
        w.writeheader()
        w.writerows(PROTOCOLS)

    hashes = []
    for name in ["STAGE3_SUBMITTED_92_5.py", "TEST1_SUBMITTED_86_7.py",
                 "TEST2_SUBMITTED_77_5.py", "TEST2_MINIMAL_NOT_SUBMITTED.py",
                 "V10_SUBMITTED_81_7.py", "dsh_official.py", "dev.json"]:
        p = HANDOFF / name
        hashes.append(dict(file=name, bytes=p.stat().st_size, sha256=sha(p)))
    with (OUT / "facts_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "bytes", "sha256"])
        w.writeheader()
        w.writerows(hashes)

    md = []
    md.append("# FAITS — ce qui est prouvé / ce qui a été confondu\n")
    md.append("## Verdict\n")
    md.append("**MEASURED :** aucun score local du dépôt n'est un score privé ML-Arena.")
    md.append("Le « dépassement » de Stage3 est un **180/180 déterministe sur `dev.json`**,")
    md.append("pas un score > 92.5 sous lots de 8 / 40 s / Qwen.\n")
    md.append("## Scores privés (rapportés) vs couverture locale (audit stub)\n")
    md.append("| Agent | Privé total | Privé Tables | Local Tables covered/correct | Local No-files covered |")
    md.append("|---|---:|---:|---:|---:|")
    for r in rows:
        if r["private_total"] is None:
            md.append(f"| {r['agent']} | — | — | {r['local_table_covered']}/{r['local_table_correct']} | {r['local_calc_covered']} |")
        else:
            md.append(
                f"| {r['agent']} | {r['private_total']} | {r['private_tables']} | "
                f"{r['local_table_covered']}/{r['local_table_correct']} | {r['local_calc_covered']} |"
            )
    md.append("\n## Confusion centrale\n")
    md.append("- Local Tables **80/80 pour tous** → le fallback LLM Tables n'est **jamais** scoré sur le public.")
    md.append("- Prive Tables : Stage3 88 -> TEST1 80 -> V10 68 -> TEST2 52.")
    md.append("- Fits restent à 96 partout → la régression n'est pas dans Fits.")
    md.append("- V10/TEST2 couvrent plus de No-files en local ; V10 **perd** des No-files en privé vs Stage3.\n")
    md.append("## Protocoles\n")
    md.append("| Protocole | LLM | batch8 | 40s | Prédit le privé ? |")
    md.append("|---|---|---|---|---|")
    for p in PROTOCOLS:
        md.append(f"| {p['protocol']} | {p['llm']} | {p['batch8']} | {p['budget40']} | {p['predicts_private']} |")
    md.append("\n## Artefacts hashés\n")
    for h in hashes:
        md.append(f"- `{h['file']}` : {h['bytes']} octets, sha256 `{h['sha256'][:16]}…`")
    md.append("\n## Niveau de preuve\n")
    md.append("- Scores privés : **MEASURED_reported** (agrégés utilisateur ; pas de détail tâche-par-tâche).")
    md.append("- Couverture locale 80/80 Tables : **MEASURED** (`dev_summary.csv` / `audit.py`).")
    md.append("- Claim 180/180 = battre 92.5 : **RÉFUTÉ** (métriques différentes).\n")
    (OUT / "FACTS.md").write_text("\n".join(md), encoding="utf-8")
    print((OUT / "FACTS.md").read_text(encoding="utf-8").encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
