from pathlib import Path
import sys, argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.evaluation.runtime import benchmark_fallback_subprocesses
ap=argparse.ArgumentParser();ap.add_argument('--fallback-count',type=int,choices=[1,2,4,8]);ap.add_argument('--all',action='store_true');args=ap.parse_args()
counts=(1,2,4,8) if args.all else ((args.fallback_count or 1),)
path=ROOT/'agents/candidates/stage4_best_local_v10.py'
df=benchmark_fallback_subprocesses(path,fallback_counts=counts,repeats=1,timeout_per_task=6.0)
if len(counts)>1:
 out=ROOT/'results/generated/runtime_results.csv'
else:
 out=ROOT/f'results/generated/runtime_rerun_{counts[0]}.csv'
df.to_csv(out,index=False);print(df.to_string(index=False));print('saved:',out)
