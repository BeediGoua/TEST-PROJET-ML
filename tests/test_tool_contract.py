from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.evaluation.tool_contract import inspect_agent_source

def test_pre_v7_has_three_documented_prompt_runtime_mismatches():
    r=inspect_agent_source(ROOT/'agents/candidates/stage4_safe_pre_v7.py')
    assert r['prompt_runtime_mismatch_count']==3

def test_v7_v8_v9_v10_contract_and_upload_scan():
    for n in ['stage4_candidate_v7.py','stage4_best_local_v8.py','stage4_best_local_v9.py','stage4_best_local_v10.py']:
        r=inspect_agent_source(ROOT/'agents/candidates'/n)
        assert r['prompt_runtime_mismatch_count']==0
        assert not r['exec_upload_violation']
