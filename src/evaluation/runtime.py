from pathlib import Path
import os
import sys
import time
import pandas as pd

from .core import repository_root, load_agent_module


def ensure_local_dsh(root=None):
    """
    Use the official dsh module on Linux and the compatibility
    implementation on Windows.
    """
    root = Path(root or repository_root())
    ref = root / "reference" / "official_ds_harness"

    if os.name == "nt":
        from . import dsh_compat
        sys.modules["dsh"] = dsh_compat
    else:
        if str(ref) not in sys.path:
            sys.path.insert(0, str(ref))

    return ref


def benchmark_fallback_subprocesses(
    agent_path,
    fallback_counts=(1, 2, 4, 8),
    repeats=1,
    timeout_per_task=6.0,
):
    root = repository_root(Path(agent_path).resolve())

    ensure_local_dsh(root)

    module = load_agent_module(
        agent_path,
        "runtime_candidate",
    )

    if not hasattr(module, "run_codes_many"):
        raise RuntimeError(
            f"{Path(agent_path).name} has no run_codes_many()"
        )

    # Simulate the four code samples used by the fallback.
    code = ["answer = 2 + 2"] * 4

    rows = []

    for n in fallback_counts:
        for rep in range(repeats):
            start = time.perf_counter()
            ok = True

            for _ in range(n):
                out = module.run_codes_many(
                    code,
                    {},
                    timeout_per_task,
                    obj="runtime smoke",
                )

                ok = (
                    ok
                    and len(out) == 4
                    and all(v == 4.0 for v in out)
                )

            rows.append(
                {
                    "fallback_tasks": n,
                    "repeat": rep,
                    "seconds": time.perf_counter() - start,
                    "ok": ok,
                }
            )

    return pd.DataFrame(rows)