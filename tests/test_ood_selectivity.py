from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.evaluation.core import load_tasks,load_agent_module,evaluate_deterministic

PATHS={
    'ood1':'benchmarks/ood_development/ood1_tables.json',
    'ood2':'benchmarks/ood_holdout/ood2_tables.json',
    'ood3':'benchmarks/ood_holdout/ood3_fresh_paraphrase.json',
    'ood4':'benchmarks/ood_holdout/ood4_composition_redteam.json',
    'ood5':'benchmarks/ood_holdout/ood5_blind_final.json',
}

def run(agent,dataset):
    t=load_tasks(ROOT/PATHS[dataset])
    m=load_agent_module(ROOT/agent,Path(agent).stem+dataset)
    return evaluate_deterministic(m,t,dataset)

def test_v10_ood1_development_benchmark():
    df=run('agents/candidates/stage4_best_local_v10.py','ood1')
    assert len(df)==80 and int(df.covered.sum())==80 and int(df.correct.sum())==80 and int(df.wrong.sum())==0

def test_v10_ood2_selectivity():
    df=run('agents/candidates/stage4_best_local_v10.py','ood2')
    assert len(df)==120 and int(df.covered.sum())==20 and int(df.correct.sum())==20 and int(df.wrong.sum())==0

def test_ood3_exposes_v8_iqr_false_positives():
    df=run('agents/candidates/stage4_best_local_v8.py','ood3')
    assert len(df)==80 and int(df.covered.sum())==72 and int(df.correct.sum())==64 and int(df.wrong.sum())==8
    bad=df[df.wrong]
    assert len(bad)==8 and set(bad['type'])=={'table.ood_iqr'} and set(bad['rule'])=={'table_stat_rule'}

def test_v9_fixes_ood3_without_overcoverage():
    df=run('agents/candidates/stage4_best_local_v9.py','ood3')
    assert len(df)==80 and int(df.covered.sum())==72 and int(df.correct.sum())==72 and int(df.wrong.sum())==0

def test_ood4_exposes_v9_compositional_filter_false_positives():
    df=run('agents/candidates/stage4_best_local_v9.py','ood4')
    assert len(df)==64 and int(df.covered.sum())==48 and int(df.correct.sum())==8 and int(df.wrong.sum())==40

def test_v10_turns_ood4_unsafe_compositions_into_abstentions():
    df=run('agents/candidates/stage4_best_local_v10.py','ood4')
    assert len(df)==64 and int(df.covered.sum())==8 and int(df.correct.sum())==8 and int(df.wrong.sum())==0

def test_ood5_is_blind_final_check_for_v10():
    # OOD5 was generated after the v10 patch and was not used to tune it.
    old=run('agents/candidates/stage4_best_local_v9.py','ood5')
    assert len(old)==48 and int(old.covered.sum())==30 and int(old.correct.sum())==0 and int(old.wrong.sum())==30
    new=run('agents/candidates/stage4_best_local_v10.py','ood5')
    assert len(new)==48 and int(new.covered.sum())==0 and int(new.wrong.sum())==0
