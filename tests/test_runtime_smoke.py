from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.evaluation.runtime import benchmark_fallback_subprocesses

def test_v10_secure_subprocess_smoke():
    df=benchmark_fallback_subprocesses(ROOT/'agents/candidates/stage4_best_local_v10.py',fallback_counts=(1,),repeats=1,timeout_per_task=6.0)
    assert len(df)==1 and bool(df.iloc[0]['ok'])
