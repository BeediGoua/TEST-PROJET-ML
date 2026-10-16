"""Run diagnostic A→F then pre-TEST3 H1–H6 harness (CPU-safe; GPU cache optional)."""
from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def run_step(name: str):
    print("\n" + "=" * 60)
    print("RUNNING", name)
    print("=" * 60, flush=True)
    t0 = time.perf_counter()
    mod = importlib.import_module(name)
    mod.main()
    print(f"DONE {name} in {time.perf_counter() - t0:.1f}s", flush=True)


def main():
    # Ensure experimental executors + synthetic smoke cache exist
    run_step("build_experimental")
    run_step("make_synthetic_cache")

    for name in [
        "01_facts",
        "02_executor_contract",
        "03_forced_fallback",
        "04_rules_ablation",
        "05_batch_timing",
        # Pre-TEST3
        "07_qwen_pattern_freq",
        "08_executor_agreement",
        "09_alias_vs_importlib",
        "10_batch_order",
        "11_stage3_forced_fallback_qwen",
        "12_test2_decomposition",
        "06_go_nogo",
    ]:
        run_step(name)
    print("\nAll diagnostic artefacts in:", HERE / "results")
    print("Colab GPU entrypoint: ../colab_forced_fallback.ipynb")


if __name__ == "__main__":
    main()
