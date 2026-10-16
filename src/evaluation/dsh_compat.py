"""Compatibility layer for dsh.run_python on Windows."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_DSH = ROOT / "reference" / "official_ds_harness" / "dsh.py"

spec = importlib.util.spec_from_file_location(
    "_official_dsh",
    OFFICIAL_DSH,
)

if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {OFFICIAL_DSH}")

official = importlib.util.module_from_spec(spec)
sys.modules["_official_dsh"] = official
spec.loader.exec_module(official)

ExecResult = official.ExecResult
_RUNNER = official._RUNNER


def run_python(
    code: str,
    files: list[str] = (),
    timeout_s: float = 10.0,
    mem_limit_mb: int = 1024,
    max_output: int = 2000,
) -> ExecResult:

    start = time.monotonic()
    workdir = tempfile.mkdtemp(prefix="dsh_local_")

    try:
        for file_path in files:
            src = os.path.abspath(file_path)
            dst = os.path.join(workdir, os.path.basename(file_path))

            try:
                os.symlink(src, dst)
            except (OSError, NotImplementedError):
                shutil.copy2(src, dst)

        with open(
            os.path.join(workdir, "solution.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(code)

        with open(
            os.path.join(workdir, "_runner.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(_RUNNER)

        env = dict(os.environ)
        env.update(
            {
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "MPLBACKEND": "Agg",
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )

        kwargs = {
            "cwd": workdir,
            "env": env,
            "text": True,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }

        if os.name != "nt":

            def limit():
                if sys.platform.startswith("linux"):
                    import resource

                    resource.setrlimit(
                        resource.RLIMIT_AS,
                        (mem_limit_mb << 20, mem_limit_mb << 20),
                    )

            kwargs["start_new_session"] = True
            kwargs["preexec_fn"] = limit

        proc = subprocess.Popen(
            [sys.executable, "_runner.py"],
            **kwargs,
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)

        except subprocess.TimeoutExpired:
            if os.name != "nt":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    proc.kill()
            else:
                proc.kill()

            stdout, _ = proc.communicate()

            return ExecResult(
                False,
                None,
                stdout[-max_output:],
                f"TimeoutError: over {timeout_s:.0f} s",
                time.monotonic() - start,
            )

        if proc.returncode != 0:
            return ExecResult(
                False,
                None,
                stdout[-max_output:],
                stderr[-max_output:] or f"exit {proc.returncode}",
                time.monotonic() - start,
            )

        with open(
            os.path.join(workdir, "result.json"),
            encoding="utf-8",
        ) as f:
            value = json.load(f)

        return ExecResult(
            True,
            value,
            stdout[-max_output:],
            None,
            time.monotonic() - start,
        )

    finally:
        shutil.rmtree(workdir, ignore_errors=True)