"""Shared helpers for pre-TEST3 H1–H6 harness (no submission)."""
from __future__ import annotations

import ast
import csv
import importlib.util
import json
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAG_OUT = HERE / "results"
AUDIT = HERE.parents[0]
HANDOFF = HERE.parents[1] / "CODEX_AUDIT_HANDOFF"
ROOT = HERE.parents[1]
EXP = HERE / "experimental"
AUDIT_OUT = AUDIT / "results"

DIAG_OUT.mkdir(parents=True, exist_ok=True)
EXP.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(AUDIT))
sys.path.insert(0, str(ROOT))

import audit as audit_mod  # noqa: E402


def find_generation_caches() -> list[Path]:
    """Prefer real GPU caches; fall back to synthetic smoke cache."""
    found: list[Path] = []
    for base in (AUDIT_OUT, DIAG_OUT):
        if not base.exists():
            continue
        for p in sorted(base.glob("generations_*.json")):
            if p.name.endswith(".partial.json") or ".partial." in p.name:
                continue
            found.append(p)
    real = [p for p in found if "synthetic" not in p.name]
    if real:
        return real
    return found


def load_cache(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_real_qwen_cache(cache: dict) -> bool:
    cfg = cache.get("config") or {}
    plat = str(cfg.get("platform", ""))
    model = str(cfg.get("model", ""))
    if "synthetic" in model.lower() or cfg.get("synthetic"):
        return False
    rows = cache.get("rows") or []
    if not rows:
        return False
    # Real generate_cache always stores revision + artifact sha
    return bool(cfg.get("revision") or cfg.get("artifact_sha256")) and "Qwen" in model


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_not_run(md_path: Path, title: str, reason: str, extra: str = ""):
    text = f"# {title}\n\n**NOT RUN:** {reason}\n\n{extra}\n"
    md_path.write_text(text, encoding="utf-8")


def load_path(path: Path, label: str):
    spec = importlib.util.spec_from_file_location("pretest3_" + label, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def install_dsh(fix_alias: bool = False):
    """Windows-compatible dsh shim (same as 02_executor_contract)."""
    from probes import SIGNAL_SHIM
    from src.evaluation import dsh_compat

    def runner(code, **kwargs):
        if fix_alias:
            code = code.replace("    __orig_read_csv = pd.read_csv", "    __orig_read_csv = __dsh_pd.read_csv")
            code = code.replace(
                "    pd.read_csv = _fake_read_csv(dfs, __extra)",
                "    __dsh_pd.read_csv = _fake_read_csv(dfs, __extra)",
            )
            code = code.replace("        pd.read_csv = __orig_read_csv", "        __dsh_pd.read_csv = __orig_read_csv")
            code = code.replace("    _orig = pd.read_csv", "    _orig = __dsh_pd.read_csv")
            code = code.replace(
                "    pd.read_csv = _fake_read_csv(dfs, _extra)",
                "    __dsh_pd.read_csv = _fake_read_csv(dfs, _extra)",
            )
            code = code.replace("        pd.read_csv = _orig", "        __dsh_pd.read_csv = _orig")
            if "import pandas as __dsh_pd" not in code:
                code = "import pandas as __dsh_pd\n" + code
        return dsh_compat.run_python(SIGNAL_SHIM + "\n" + code, **kwargs)

    sys.modules["dsh"] = types.SimpleNamespace(run_python=runner)
    return runner


def analyze_code_patterns(code: str) -> dict:
    code = code or ""
    syntax_ok = True
    syntax_err = ""
    try:
        ast.parse(code)
    except SyntaxError as e:
        syntax_ok = False
        syntax_err = f"{e.msg} (line {e.lineno})"
    return {
        "empty": not code.strip(),
        "has_answer": bool(re.search(r"\banswer\s*=", code)),
        "import_pandas_as_pd": bool(re.search(r"^\s*import\s+pandas\s+as\s+pd\b", code, re.M)),
        "any_import": bool(re.search(r"^\s*(import|from)\s+\w+", code, re.M)),
        "rebind_pd": bool(re.search(r"^\s*pd\s*=", code, re.M)),
        "syntax_ok": syntax_ok,
        "syntax_error": syntax_err,
        "truncated_heuristic": (not code.strip()) or (not re.search(r"\banswer\s*=", code)),
    }


def table_tasks() -> list[dict]:
    tasks = json.loads((HANDOFF / "dev.json").read_text(encoding="utf-8"))
    return [t for t in tasks if str(t.get("type", "")).startswith("table.")]


def values_agree(a, b, tol: float = 1e-6) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return False
