from pathlib import Path
import sys, argparse, pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.evaluation.core import load_tasks,load_agent_module,evaluate_deterministic
from src.evaluation.metamorphic import build_suite
from src.evaluation.metrics import summarize_audit
AGENTS={
  'stage3':'agents/champions/stage3_92_5.py','naive':'agents/candidates/stage4_naive_nofiles.py',
  'safe':'agents/candidates/stage4_safe_pre_v7.py','v7':'agents/candidates/stage4_candidate_v7.py',
  'v8':'agents/candidates/stage4_best_local_v8.py','v9':'agents/candidates/stage4_best_local_v9.py',
  'v10':'agents/candidates/stage4_best_local_v10.py'}
ap=argparse.ArgumentParser();ap.add_argument('--agent',choices=list(AGENTS));ap.add_argument('--all',action='store_true');ap.add_argument('--mutation',help='Run only one metamorphic mutation (e.g. explicit_unrelated_pre)');args=ap.parse_args()
labels=list(AGENTS) if args.all or args.agent is None else [args.agent]
dev=load_tasks(ROOT/'data/public/dev.json');suite=build_suite(dev)
if args.mutation:
    available=sorted({t.get('_mutation') for t in suite if t.get('_mutation')})
    if args.mutation not in available:
        raise SystemExit(f'Unknown mutation {args.mutation!r}. Available: {available}')
    suite=[t for t in suite if t.get('_mutation')==args.mutation]
all_details=[];all_summaries=[]
for label in labels:
    mod=load_agent_module(ROOT/AGENTS[label],label);df=evaluate_deterministic(mod,suite,'metamorphic');df.insert(0,'agent',label)
    muts=[]
    for i in df.id:
        if '__table_noise' in i:m='table_distractor_column'
        elif '__fit_shuffle' in i:m='fit_train_row_shuffle'
        else:m=i.split('__',1)[1] if '__' in i else 'unknown'
        muts.append(m)
    df['mutation']=muts;all_details.append(df)
    for mut,g in df.groupby('mutation'):
        all_summaries.append({'agent':label,'mutation':mut,**summarize_audit(g)})
ss=pd.DataFrame(all_summaries)
if len(labels)>1:
    pd.concat(all_details,ignore_index=True).to_csv(ROOT/'results/generated/metamorphic_details.csv',index=False)
    ss.to_csv(ROOT/'results/generated/metamorphic_summary.csv',index=False)
    print(ss.to_string(index=False));print('saved consolidated metamorphic matrix')
else:
    label=labels[0];all_details[0].to_csv(ROOT/f'results/generated/metamorphic_rerun_details_{label}.csv',index=False)
    ss.to_csv(ROOT/f'results/generated/metamorphic_rerun_summary_{label}.csv',index=False)
    print(ss.to_string(index=False));print(f'saved targeted rerun for {label}')
