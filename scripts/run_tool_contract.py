from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.evaluation.tool_contract import inspect_many
paths=[
 ROOT/'agents/champions/stage3_92_5.py',ROOT/'agents/candidates/stage4_naive_nofiles.py',
 ROOT/'agents/candidates/stage4_safe_pre_v7.py',ROOT/'agents/candidates/stage4_candidate_v7.py',
 ROOT/'agents/candidates/stage4_best_local_v8.py',ROOT/'agents/candidates/stage4_best_local_v9.py',
 ROOT/'agents/candidates/stage4_best_local_v10.py']
df=inspect_many(paths);df.to_csv(ROOT/'results/generated/tool_contract_results.csv',index=False);print(df.to_string(index=False))
