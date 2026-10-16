from pathlib import Path
import sys, argparse, pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.evaluation.core import load_tasks,load_agent_module,evaluate_deterministic
from src.evaluation.metrics import summarize_audit
AGENTS={
 'stage3':'agents/champions/stage3_92_5.py',
 'naive':'agents/candidates/stage4_naive_nofiles.py',
 'safe_pre_v7':'agents/candidates/stage4_safe_pre_v7.py',
 'v7':'agents/candidates/stage4_candidate_v7.py',
 'v8':'agents/candidates/stage4_best_local_v8.py',
 'v9':'agents/candidates/stage4_best_local_v9.py',
 'v10':'agents/candidates/stage4_best_local_v10.py',
}
ap=argparse.ArgumentParser();ap.add_argument('--agent',choices=list(AGENTS));ap.add_argument('--all',action='store_true');args=ap.parse_args()
labels=list(AGENTS) if args.all or args.agent is None else [args.agent]
dev=load_tasks(ROOT/'data/public/dev.json');rows=[];details=[]
for label in labels:
    m=load_agent_module(ROOT/AGENTS[label],label);df=evaluate_deterministic(m,dev,'dev');df.insert(0,'agent',label);details.append(df)
    row={'agent':label,**summarize_audit(df)}
    for fam in ['calc','table','fit']:
        g=df[df.family==fam];row[f'{fam}_covered']=int(g.covered.sum());row[f'{fam}_correct']=int(g.correct.sum())
    rows.append(row)
out=pd.DataFrame(rows)
if len(labels)>1:
    out.to_csv(ROOT/'results/generated/dev_comparison.csv',index=False)
    pd.concat(details,ignore_index=True).to_csv(ROOT/'results/generated/dev_details_all_agents.csv',index=False)
    print(out.to_string(index=False));print('saved consolidated dev comparison')
else:
    label=labels[0]
    out.to_csv(ROOT/f'results/generated/dev_rerun_{label}.csv',index=False)
    details[0].to_csv(ROOT/f'results/generated/dev_rerun_details_{label}.csv',index=False)
    print(out.to_string(index=False));print(f'saved targeted rerun for {label}')
