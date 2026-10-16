from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.evaluation.core import load_tasks,load_agent_module,evaluate_deterministic
from src.evaluation.metamorphic import objective_variant

def run(agent,mutation):
    dev=[t for t in load_tasks(ROOT/'data/public/dev.json') if t['type'].startswith('calc.')]
    tasks=[objective_variant(t,mutation) for t in dev]
    m=load_agent_module(ROOT/agent,Path(agent).stem+mutation)
    return evaluate_deterministic(m,tasks)

def test_naive_distractor_failure_is_reproducible():
    df=run('agents/candidates/stage4_naive_nofiles.py','explicit_unrelated_pre')
    assert int(df.covered.sum())==65 and int(df.correct.sum())==26 and int(df.wrong.sum())==39

def test_v7_new_redteam_limit_is_reproducible():
    df=run('agents/candidates/stage4_candidate_v7.py','independent_example_post')
    assert int(df.covered.sum())==65 and int(df.correct.sum())==63 and int(df.wrong.sum())==2

def test_v10_keeps_known_nofile_metamorphic_suite_clean():
    for mut in ['explicit_unrelated_pre','explicit_unrelated_post','independent_example_post','parenthetical_unrelated_pre']:
        df=run('agents/candidates/stage4_best_local_v10.py',mut)
        assert int(df.covered.sum())==65 and int(df.correct.sum())==65 and int(df.wrong.sum())==0
