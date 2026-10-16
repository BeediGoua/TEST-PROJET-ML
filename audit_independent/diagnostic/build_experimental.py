"""Bake experimental executors: test1_alias (__dsh_pd) and e4_importlib."""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
HANDOFF = HERE.parents[1] / "CODEX_AUDIT_HANDOFF"
EXP = HERE / "experimental"
EXP.mkdir(parents=True, exist_ok=True)

ALIAS_MANY = r'''
def run_codes_many(codes, dfs, timeout, obj=""):
    """TEST1 many-samples path with __dsh_pd alias + SyntaxError isolation (E2).

    Changes vs submitted TEST1:
    1) wrapper touches `__dsh_pd` so `import pandas as pd` is safe in nested bodies;
    2) pre-compile each program; syntax-broken candidates return None without killing siblings.
    Still one dsh child for N samples (budget-friendly).
    """
    import dsh
    if not codes:
        return []
    root = tempfile.mkdtemp(prefix="dsh_stage3_many_")
    try:
        state_path = _write_sandbox_state(dfs, root)
        chunks = []
        for i, code in enumerate(codes):
            raw = (code or "").strip()
            syntax_error = ""
            if not raw:
                syntax_error = "empty"
            else:
                try:
                    compile(raw, "<generated>", "exec")
                    compile("def __dsh_probe():\n" + textwrap.indent(raw, "    "),
                            "<generated-wrapper>", "exec")
                except SyntaxError:
                    syntax_error = "syntax"
            if syntax_error:
                chunks.append(f"\ndef __candidate_{i}():\n    return None\n")
                continue
            body = textwrap.indent(raw, "        ")
            chunk = f"""
def __candidate_{i}():
    dfs = _fresh_dfs()
    _extra = {{"data_dictionary": _DICTIONARY}} if _DICTIONARY is not None else {{}}
    _orig = __dsh_pd.read_csv
    __dsh_pd.read_csv = _fake_read_csv(dfs, _extra)
    answer = None
    try:
__BODY__
        return to_float(answer)
    except BaseException:
        return None
    finally:
        __dsh_pd.read_csv = _orig
""".replace("__BODY__", body)
            chunks.append(chunk)
        calls = ", ".join(f"__candidate_{i}()" for i in range(len(codes)))
        full_code = (
            "import pandas as __dsh_pd\n"
            + _sandbox_header(obj, dfs)
            + "\n"
            + "\n".join(chunks)
            + f"\nRESULT = [{calls}]\n"
        )
        result = dsh.run_python(
            full_code,
            files=[state_path],
            timeout_s=max(0.8, float(timeout)),
            mem_limit_mb=768,
            max_output=2000,
        )
        if not result.ok or not isinstance(result.value, list):
            return [None] * len(codes)
        vals = []
        for v in result.value:
            vals.append(to_float(v) if v is not None else None)
        return vals + [None] * max(0, len(codes) - len(vals))
    except BaseException:
        return [None] * len(codes)
    finally:
        shutil.rmtree(root, ignore_errors=True)
'''


def build_test1_alias() -> Path:
    src = (HANDOFF / "TEST1_SUBMITTED_86_7.py").read_text(encoding="utf-8")
    # Greedy run_code: alias wrapper pandas touches (body stays module-level)
    src = src.replace(
        "_orig_read_csv = pd.read_csv\n"
        "pd.read_csv = _fake_read_csv(_dfs_local, _extra)",
        "_orig_read_csv = __dsh_pd.read_csv\n"
        "__dsh_pd.read_csv = _fake_read_csv(_dfs_local, _extra)",
    )
    src = src.replace(
        "finally:\n    pd.read_csv = _orig_read_csv\n",
        "finally:\n    __dsh_pd.read_csv = _orig_read_csv\n",
    )
    src = src.replace(
        'full_code = _sandbox_header(obj, dfs) + """\n_dfs_local',
        'full_code = "import pandas as __dsh_pd\\n" + _sandbox_header(obj, dfs) + """\n_dfs_local',
    )
    marker = 'def run_codes_many(codes, dfs, timeout, obj=""):'
    end = "\ndef to_float(v):"
    i = src.find(marker)
    j = src.find(end, i)
    if i < 0 or j < 0:
        raise RuntimeError("cannot locate run_codes_many in TEST1")
    new_src = src[:i] + ALIAS_MANY + "\n" + src[j:]
    out = EXP / "test1_alias_dsh.py"
    out.write_text(new_src, encoding="utf-8")
    return out


E4_IMPORTLIB = r'''
"""E4 executor: Stage3 namespace + importlib module-scope load of generated code.

Not a full Agent. Read-only experimental harness for H2/H3 agreement.
"""
from __future__ import annotations

import importlib.util
import io
import tempfile
from pathlib import Path

_HANDOFF = Path(__file__).resolve().parents[3] / "CODEX_AUDIT_HANDOFF"
_STAGE3 = _HANDOFF / "STAGE3_SUBMITTED_92_5.py"


def _load_stage3():
    spec = importlib.util.spec_from_file_location("stage3_e4_base", _STAGE3)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_S3 = _load_stage3()

pd = _S3.pd
np = _S3.np
math = _S3.math
datetime = _S3.datetime
contextlib = _S3.contextlib
re = _S3.re
SmartFrame = _S3.SmartFrame
to_float = _S3.to_float
clean_numeric = _S3.clean_numeric
clean_dates = _S3.clean_dates
safe_divide = _S3.safe_divide
vote = _S3.vote
decimals = getattr(_S3, "decimals", None)
load_task = _S3.load_task
align_keys = _S3.align_keys
entity_hints = _S3.entity_hints
LAST_ERR = ""
LAST_STATE = ""


def run_code(code, dfs, timeout, obj=""):
    """Module-scope importlib load — equivalent intent to exec(code, ns)."""
    from scipy import stats
    from sklearn.metrics import r2_score

    global LAST_ERR, LAST_STATE
    LAST_ERR, LAST_STATE = "", ""

    unreg = bool(re.search(
        r"without regularis|no regularis|unregularis|unpenali|without penal",
        str(obj).lower(),
    ))
    LinearRegression, LogisticRegression = _S3._make_models(unreg)
    for _n in ("nanmean", "nanmedian", "nanstd", "nansum"):
        if not hasattr(stats, _n):
            setattr(stats, _n, getattr(np, _n))
    if not hasattr(stats, "median"):
        setattr(stats, "median", np.median)
    if not hasattr(stats, "scoreatpercentile"):
        setattr(stats, "scoreatpercentile", np.percentile)
    import sympy

    try:
        SmartFrame._desc = dict(getattr(dfs, "desc", {}) or {})
        cdfs = {k: SmartFrame(v) for k, v in dfs.items()}
    except Exception:
        cdfs = {k: v.copy() for k, v in dfs.items()}
    dd = getattr(dfs, "dictionary", None)
    extra = {"data_dictionary": dd} if dd is not None else {}
    ns = {
        "pd": pd, "np": np, "math": math, "stats": stats, "sympy": sympy, "datetime": datetime,
        "clean_numeric": clean_numeric, "clean_dates": clean_dates, "safe_divide": safe_divide,
        "LinearRegression": LinearRegression, "LogisticRegression": LogisticRegression,
        "r2_score": r2_score, "dfs": cdfs, "__name__": "dsh_candidate", "__package__": None,
    }
    orig_read_csv = pd.read_csv
    pd.read_csv = _S3._fake_read_csv(cdfs, extra)
    holder = {"ns": ns}

    def job():
        global LAST_STATE
        path = None
        mod = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
                fh.write(code if (code or "").strip() else "answer = None\n")
                path = fh.name
            spec = importlib.util.spec_from_file_location("dsh_candidate", path)
            mod = importlib.util.module_from_spec(spec)
            mod.__dict__.update(ns)
            holder["ns"] = mod.__dict__
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                spec.loader.exec_module(mod)
            value = to_float(getattr(mod, "answer", None))
            if value is None:
                raise ValueError("answer missing, non-numeric, or non-finite")
            return value
        except BaseException:
            LAST_STATE = _S3._runtime_state(holder["ns"])
            raise
        finally:
            if path:
                try:
                    Path(path).unlink(missing_ok=True)
                except Exception:
                    pass

    try:
        return _S3._run_with_timeout(job, timeout)
    except BaseException as e:
        LAST_ERR = f"{type(e).__name__}: {str(e)[:150]}"
        if not LAST_STATE:
            LAST_STATE = _S3._runtime_state(holder["ns"])
        return None
    finally:
        pd.read_csv = orig_read_csv


def run_codes_many(codes, dfs, timeout, obj=""):
    if not codes:
        return []
    return [run_code(c, dfs, timeout, obj) for c in codes]
'''


def build_e4_importlib() -> Path:
    out = EXP / "executor_e4_importlib.py"
    out.write_text(E4_IMPORTLIB.lstrip("\n"), encoding="utf-8")
    return out


def update_readme():
    (EXP / "README_experimental.md").write_text(
        "# Experimental copies (pre-TEST3)\n\n"
        "- `stage3_faithful_dsh.py` — TEST1 + one child per sample (correctness oracle; slow).\n"
        "- `test1_alias_dsh.py` — **E2 candidate**: TEST1 + `__dsh_pd` + SyntaxError "
        "pre-compile isolation (one child for N samples).\n"
        "- `executor_e4_importlib.py` — **E4**: Stage3 helpers + importlib module-scope load.\n"
        "\n"
        "No submission artifacts. TEST3-recovery only after H1–H6 gates pass on REAL Qwen.\n",
        encoding="utf-8",
    )


def main():
    a = build_test1_alias()
    b = build_e4_importlib()
    update_readme()
    print("wrote", a)
    print("wrote", b)


if __name__ == "__main__":
    main()
