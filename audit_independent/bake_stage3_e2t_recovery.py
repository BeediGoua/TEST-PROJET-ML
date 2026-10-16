"""Bake STAGE3-COMPLIANT-RECOVERY: Stage3 exact + E2T executor only.

No Qwen3, no new prompts/rules. Output: STAGE3_E2T_RECOVERY/{agent.py,dsh.py}
"""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HANDOFF = HERE.parent / "CODEX_AUDIT_HANDOFF"
DIAG = HERE / "diagnostic"
EXP = DIAG / "experimental"
OUT = HERE / "STAGE3_E2T_RECOVERY"


def _ensure_e2t():
    import sys

    sys.path.insert(0, str(DIAG))
    from build_experimental import build_test1_e2t

    return build_test1_e2t()


def bake(outer_many: float = 7.5, reserve_one_sample_default: bool = False) -> Path:
    e2t_path = _ensure_e2t()
    e2t = e2t_path.read_text(encoding="utf-8")
    stage3 = (HANDOFF / "STAGE3_SUBMITTED_92_5.py").read_text(encoding="utf-8")

    # Extract sandbox + run_code + run_codes_many from E2T bake (before module to_float)
    i = e2t.find("_SANDBOX_PRELUDE = ")
    j = e2t.find("\ndef to_float(v):", e2t.find("def run_codes_many"))
    if i < 0 or j < 0:
        raise RuntimeError("cannot extract E2T executor block")
    executor_block = e2t[i:j].rstrip() + "\n\n"

    # Replace Stage3 in-process run_code (exec) with compliant block
    r0 = stage3.find("\ndef run_code(code, dfs, timeout, obj=\"\"):")
    r1 = stage3.find("\ndef to_float(v):", r0)
    if r0 < 0 or r1 < 0:
        raise RuntimeError("cannot locate Stage3 run_code")
    # Drop unused thread-timeout helper if present immediately above run_code
    helper = stage3.rfind("\ndef _run_with_timeout", 0, r0)
    cut = helper if helper >= 0 else r0
    new_src = stage3[:cut] + "\n\n" + executor_block + stage3[r1:]

    # Imports required by dsh sandbox path
    inject = "import tempfile\nimport shutil\nimport textwrap\nimport json\n"
    if "import tempfile" not in new_src:
        new_src = new_src.replace("import unicodedata\n", "import unicodedata\n" + inject, 1)

    # Outer many timeout + force-fallback switch
    new_src = new_src.replace(
        "EXEC_TIMEOUT = 1.5     # secondes max par exécution de code généré",
        "EXEC_TIMEOUT = 1.5     # secondes max par exécution de code généré\n"
        f"OUTER_MANY = float(os.environ.get('DSH_OUTER_MANY', '{outer_many}'))  # many-path envelope\n"
        "# Read env at solve-time (NOT import-time) so Colab can set DSH_FORCE_FALLBACK=1 after load.\n"
        "def _force_fallback():\n"
        "    return os.environ.get('DSH_FORCE_FALLBACK', '') == '1'\n",
    )

    # Skip table deterministic rules when FORCE_FALLBACK (B2)
    new_src = new_src.replace(
        '                if kind == "table":\n'
        "                    try:\n"
        "                        rv = table_stat_rule(t[\"objective\"], dfs, dico)",
        '                if kind == "table" and not _force_fallback():\n'
        "                    try:\n"
        "                        rv = table_stat_rule(t[\"objective\"], dfs, dico)",
    )

    # Sample round: use E2T run_codes_many when n>1
    old_absorb_loop = '''            for p, outs in zip(live, gens):
                for o in outs:
                    if not absorb(p, o, weight):
                        return'''
    new_absorb_loop = '''            for p, outs in zip(live, gens):
                if n <= 1:
                    for o in outs:
                        if not absorb(p, o, weight):
                            return
                else:
                    # E2T: one child, per-candidate 1.5s, shared outer envelope
                    if left() < 1.5:
                        return
                    codes = [extract_code(o) for o in outs]
                    vals = run_codes_many(codes, p["dfs"], min(OUTER_MANY, left()), p["obj"])
                    for v in vals:
                        if v is not None:
                            p["c"].append((v, weight))
                        else:
                            p["fail"] = (codes[0] if codes else "", "batch returned None", "")'''
    if old_absorb_loop not in new_src:
        raise RuntimeError("cannot patch sample absorb loop")
    new_src = new_src.replace(old_absorb_loop, new_absorb_loop)

    # P1 (opt-in via env; optional bake default ON for GO zip):
    # reserve wall-time for ≥1 stochastic sample when still empty after greedy.
    # Env: DSH_RESERVE_ONE_SAMPLE, DSH_SAMPLE_RESERVE=9.0. No prompt/model/rules/vote change.
    _rs_default = "1" if reserve_one_sample_default else ""
    old_repair_gen = (
        "            try:\n"
        "                gens = self.generate(msgs, 1, 0.0, max_new=MAX_NEW, max_time=min(8.0, left() - 2))\n"
        "            except Exception:\n"
        "                return\n"
        "            for p, outs in zip(todo, gens):\n"
        "                for o in outs:\n"
        "                    if not absorb(p, o, 1.5):\n"
        "                        return"
    )
    new_repair_gen = (
        "            try:\n"
        "                repair_cap = min(8.0, left() - 2)\n"
        f"                if os.environ.get('DSH_RESERVE_ONE_SAMPLE', '{_rs_default}') == '1' and any(\n"
        "                    p['ok'] and not p['c'] for p in prep\n"
        "                ):\n"
        "                    reserve = float(os.environ.get('DSH_SAMPLE_RESERVE', '9.0'))\n"
        "                    if left() < reserve + 4.0:\n"
        "                        return  # skip repair; protect sample budget\n"
        "                    repair_cap = min(repair_cap, max(1.0, left() - reserve - 2.0))\n"
        "                gens = self.generate(msgs, 1, 0.0, max_new=MAX_NEW, max_time=repair_cap)\n"
        "            except Exception:\n"
        "                return\n"
        "            for p, outs in zip(todo, gens):\n"
        "                for o in outs:\n"
        "                    if not absorb(p, o, 1.5):\n"
        "                        return"
    )
    if old_repair_gen not in new_src:
        raise RuntimeError("cannot patch repair generate cap for P1")
    new_src = new_src.replace(old_repair_gen, new_repair_gen)

    old_sample_gate = (
        "        t3 = time.time()\n"
        "        if left() > 6:                             # OPTIMISATION 2: Vote adaptatif\n"
        "            for p in prep:\n"
        "                if not p[\"ok\"] or not p[\"c\"]:\n"
        "                    continue\n"
        "                # Si les précédentes passes (gloutonne/réparée) sont déjà d'accord, on arrête d'échantillonner cette tâche\n"
        "                vals = [round(v, 4) for v, w in p[\"c\"] if v is not None]\n"
        "                if len(vals) >= 2 and len(set(vals)) == 1:\n"
        "                    p[\"ok\"] = False\n"
        "                    \n"
        "            nsamp_adapt = int(os.environ.get(\"DSH_SAMPLES_ADAPTIVE\", NSAMP))\n"
        "            run_round(nsamp_adapt, 0.5, 1.0, MAX_NEW)"
    )
    new_sample_gate = (
        "        t3 = time.time()\n"
        "        _empty = [p for p in prep if p[\"ok\"] and not p[\"c\"]]\n"
        "        _force_sample = (\n"
        f"            os.environ.get(\"DSH_RESERVE_ONE_SAMPLE\", \"{_rs_default}\") == \"1\"\n"
        "            and bool(_empty)\n"
        "            and left() > 4.0\n"
        "        )\n"
        "        if left() > 6 or _force_sample:             # OPTIMISATION 2 + P1 reserve-one-sample\n"
        "            for p in prep:\n"
        "                if not p[\"ok\"] or not p[\"c\"]:\n"
        "                    continue\n"
        "                # Si les précédentes passes (gloutonne/réparée) sont déjà d'accord, on arrête d'échantillonner cette tâche\n"
        "                vals = [round(v, 4) for v, w in p[\"c\"] if v is not None]\n"
        "                if len(vals) >= 2 and len(set(vals)) == 1:\n"
        "                    p[\"ok\"] = False\n"
        "\n"
        "            nsamp_adapt = int(os.environ.get(\"DSH_SAMPLES_ADAPTIVE\", NSAMP))\n"
        "            if _force_sample and left() < 12.0:\n"
        "                # Thin budget: one sample, prefer tasks still empty\n"
        "                nsamp_adapt = 1\n"
        "                for p in prep:\n"
        "                    if p[\"ok\"] and p[\"c\"]:\n"
        "                        p[\"ok\"] = False\n"
        "            run_round(nsamp_adapt, 0.5, 1.0, MAX_NEW)"
    )
    if old_sample_gate not in new_src:
        raise RuntimeError("cannot patch sample gate for P1")
    new_src = new_src.replace(old_sample_gate, new_sample_gate)

    # Banner
    banner = (
        '"""STAGE3-COMPLIANT-RECOVERY (TEST3 candidate bake)\n\n'
        "Stage3 exact: model, prompts, rules, vote, BUDGET, NSAMP, MAX_NEW.\n"
        "ONLY change: compliant E2T executor (dsh + __dsh_pd + SIGALRM 1.5s/cand).\n"
        "Optional control (env): DSH_RESERVE_ONE_SAMPLE=1 — reserve time for ≥1 sample if empty.\n"
        'No Qwen3 / new prompts / new rules / reject-zero / default=1.\n"""\n'
    )
    if new_src.lstrip().startswith('"""') or new_src.lstrip().startswith("#"):
        # keep after shebang/encoding if any
        pass
    new_src = banner + new_src

    # Hard fail if upload-forbidden exec( remains on agent (allow only inside sandbox strings carefully)
    # Strip Stage3 leftover exec(code, ns) — must be gone
    if re.search(r"exec\(\s*code\s*,\s*ns\s*\)", new_src):
        raise RuntimeError("bake still contains exec(code, ns)")

    OUT.mkdir(parents=True, exist_ok=True)
    agent_path = OUT / "agent.py"
    agent_path.write_text(new_src, encoding="utf-8")
    dsh_src = HANDOFF / "dsh_official.py"
    shutil.copy2(dsh_src, OUT / "dsh.py")

    # Zip for upload (human submits; notebook does not auto-submit)
    zpath = HERE / "STAGE3_E2T_RECOVERY.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(agent_path, "agent.py")
        zf.write(OUT / "dsh.py", "dsh.py")

    # Static scan
    from src.evaluation.tool_contract import inspect_agent_source

    rep = inspect_agent_source(agent_path)
    if rep.get("exec_upload_violation"):
        raise RuntimeError(f"static exec violation: {rep}")

    (OUT / "BAKE_META.txt").write_text(
        f"outer_many={outer_many}\nexec_upload_violation={rep.get('exec_upload_violation')}\n"
        f"mismatch_count={rep.get('prompt_runtime_mismatch_count')}\n"
        f"reserve_one_sample_default={reserve_one_sample_default}\n",
        encoding="utf-8",
    )
    return agent_path


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(HERE.parent))
    p = bake()
    print("baked", p)
    print("zip", HERE / "STAGE3_E2T_RECOVERY.zip")
