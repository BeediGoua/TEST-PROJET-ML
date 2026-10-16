
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.evaluation.core import load_tasks,load_agent_module,evaluate_deterministic
def test_stage3_known_deterministic_audit():
  dev=load_tasks(ROOT/'data/public/dev.json');m=load_agent_module(ROOT/'agents/champions/stage3_92_5.py','s3test');df=evaluate_deterministic(m,dev)
  assert int(df.covered.sum())==140 and int(df.correct.sum())==140 and int(df.wrong.sum())==0
  got={fam:(int(g.covered.sum()),int(g.correct.sum())) for fam,g in df.groupby('family')}
  assert got=={'calc':(25,25),'table':(80,80),'fit':(35,35)}
