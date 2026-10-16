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
