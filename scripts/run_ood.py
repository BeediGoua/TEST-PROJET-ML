from pathlib import Path
import sys, argparse, pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.evaluation.core import load_tasks,load_agent_module,evaluate_deterministic
from src.evaluation.metrics import summarize_audit
AGENTS={
 'stage3':'agents/champions/stage3_92_5.py','v7':'agents/candidates/stage4_candidate_v7.py',
 'v8':'agents/candidates/stage4_best_local_v8.py','v9':'agents/candidates/stage4_best_local_v9.py',
 'v10':'agents/candidates/stage4_best_local_v10.py'}
DATASETS={
 'ood1':ROOT/'benchmarks/ood_development/ood1_tables.json',
 'ood2':ROOT/'benchmarks/ood_holdout/ood2_tables.json',
 'ood3':ROOT/'benchmarks/ood_holdout/ood3_fresh_paraphrase.json',
 'ood4':ROOT/'benchmarks/ood_holdout/ood4_composition_redteam.json',
 'ood5':ROOT/'benchmarks/ood_holdout/ood5_blind_final.json'}
ap=argparse.ArgumentParser();ap.add_argument('--agent',choices=list(AGENTS));ap.add_argument('--all',action='store_true');ap.add_argument('--dataset',choices=list(DATASETS),help='Run only one OOD benchmark');args=ap.parse_args()
labels=list(AGENTS) if args.all or args.agent is None else [args.agent]
datasets={args.dataset:DATASETS[args.dataset]} if args.dataset else DATASETS
allrows=[];summary=[];bytype=[]
for label in labels:
    m=load_agent_module(ROOT/AGENTS[label],label)
    for ds,p in datasets.items():
        tasks=load_tasks(p);df=evaluate_deterministic(m,tasks,ds);df.insert(0,'agent',label);allrows.append(df)
        summary.append({'agent':label,'dataset':ds,**summarize_audit(df)})
        for typ,g in df.groupby('type'):bytype.append({'agent':label,'dataset':ds,'type':typ,**summarize_audit(g)})
S=pd.DataFrame(summary);B=pd.DataFrame(bytype);D=pd.concat(allrows,ignore_index=True)
if len(labels)>1:
    D.to_csv(ROOT/'results/generated/ood_details.csv',index=False);S.to_csv(ROOT/'results/generated/ood_summary.csv',index=False);B.to_csv(ROOT/'results/generated/ood_by_type.csv',index=False)
    print(S.to_string(index=False));print('saved consolidated OOD matrix')
else:
    label=labels[0];D.to_csv(ROOT/f'results/generated/ood_rerun_details_{label}.csv',index=False);S.to_csv(ROOT/f'results/generated/ood_rerun_summary_{label}.csv',index=False);B.to_csv(ROOT/f'results/generated/ood_rerun_by_type_{label}.csv',index=False)
    print(S.to_string(index=False));print(f'saved targeted rerun for {label}')
