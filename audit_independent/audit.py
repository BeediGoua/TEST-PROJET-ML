"""Read-only audit of submitted agents. No model initialization or private submission."""
from pathlib import Path
import ast, contextlib, csv, difflib, hashlib, importlib.util, io, json, sys, tempfile, types

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / 'CODEX_AUDIT_HANDOFF'
OUT = Path(__file__).resolve().parent / 'results'
FILES = {'stage3':'STAGE3_SUBMITTED_92_5.py','test1':'TEST1_SUBMITTED_86_7.py',
         'test2':'TEST2_SUBMITTED_77_5.py','minimal':'TEST2_MINIMAL_NOT_SUBMITTED.py','v10':'V10_SUBMITTED_81_7.py'}

def load(label):
    spec = importlib.util.spec_from_file_location('audit_'+label, HANDOFF/FILES[label])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def write_csv(name, rows):
    if rows:
        with (OUT/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def inventory():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=[]; trees={}; sources={}
    for p in HANDOFF.iterdir():
        if p.is_file():
            b=p.read_bytes();manifest.append(dict(file=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    write_csv('manifest.csv',manifest)
    for label, file in FILES.items():
        s=(HANDOFF/file).read_text(encoding='utf-8');sources[label]=s
        nodes={}
        for n in ast.parse(s).body:
            if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
                nodes[n.name]=n
                if isinstance(n,ast.ClassDef):
                    for c in n.body:
                        if isinstance(c,ast.FunctionDef):nodes[n.name+'.'+c.name]=c
            elif isinstance(n,ast.Assign):
                for t in n.targets:
                    if isinstance(t,ast.Name):nodes[t.id]=n
        trees[label]=nodes
    changes=[]
    for a,b in [('stage3','test1'),('test1','minimal'),('test1','test2'),('stage3','v10')]:
        diff=[]
        for name in sorted(trees[a].keys()|trees[b].keys()):
            x,y=trees[a].get(name),trees[b].get(name)
            same=x is not None and y is not None and ast.dump(x)==ast.dump(y)
            if same:continue
            changes.append(dict(baseline=a,candidate=b,symbol=name,status='added' if x is None else 'removed' if y is None else 'changed',old_line=x.lineno if x else '',new_line=y.lineno if y else ''))
            xs=ast.get_source_segment(sources[a],x) if x else '';ys=ast.get_source_segment(sources[b],y) if y else ''
            diff.extend(difflib.unified_diff(xs.splitlines(True),ys.splitlines(True),fromfile=a+':'+name,tofile=b+':'+name))
        (OUT/f'{a}_to_{b}.diff').write_text(''.join(diff),encoding='utf-8')
    write_csv('semantic_changes.csv',changes)
    return manifest,changes

def reproduce():
    sys.path.insert(0,str(ROOT))
    from src.evaluation.core import evaluate_deterministic, _materialize_all
    tasks=json.loads((HANDOFF/'dev.json').read_text(encoding='utf-8'))
    rows=[]; legacy=[]; prompts=[]
    for label in FILES:
        m=load(label)
        old=evaluate_deterministic(m,tasks);old.insert(0,'agent',label);legacy.extend(old.to_dict('records'))
        # Execute the real solve orchestration, stopping generation with an explicit sentinel.
        # No fallback answer is counted as deterministic coverage.
        agent=m.Agent.__new__(m.Agent);agent.torch=types.SimpleNamespace(manual_seed=lambda _:None)
        state={}
        def no_generation(messages,n,temp,**kw):
            state['fallback']=True;state['messages']=messages
            return [[] for _ in messages]
        agent.generate=no_generation
        with tempfile.TemporaryDirectory(prefix='audit_dev_') as td:
            paths=_materialize_all(tasks,td)
            for t in tasks:
                state.clear(); calls=[];originals={}
                for name in ['calc_rules','calc_safe_v2','fit_rules','table_stat_rule','table_group_rule','table_join_rule','table_derive_rule','table_filter_rule','table_extended_rule','table_extra_safe2']:
                    if not hasattr(m,name):continue
                    fn=getattr(m,name); originals[name]=fn
                    def wrap(*args,_fn=fn,_name=name,**kwargs):
                        try:
                            v=_fn(*args,**kwargs);calls.append((_name,str(v)));return v
                        except Exception as e:
                            calls.append((_name,type(e).__name__+':'+str(e)));raise
                    setattr(m,name,wrap)
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        result=agent.solve([dict(id=t['id'],objective=t['objective'],files=paths[t['id']])])[0]['answer']
                finally:
                    for name,fn in originals.items():setattr(m,name,fn)
                covered=not state.get('fallback',False)
                rows.append(dict(agent=label,id=t['id'],type=t['type'],family=t['type'].split('.')[0],covered=covered,prediction=result if covered else None,correct=covered and abs(result-float(t['answer']))<=float(t['tol']),answer=t['answer'],tol=t['tol'],calls=json.dumps(calls)))
                if state.get('messages'):prompts.append(dict(agent=label,id=t['id'],messages=state['messages'][0]))
    write_csv('real_solve_dev.csv',rows);write_csv('legacy_dev.csv',legacy)
    (OUT/'fallback_prompts.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2),encoding='utf-8')
    summary=[]
    for label in FILES:
        for family in ['calc','table','fit']:
            r=[x for x in rows if x['agent']==label and x['family']==family]
            summary.append(dict(agent=label,family=family,total=len(r),covered=sum(x['covered'] for x in r),correct=sum(x['correct'] for x in r)))
    write_csv('dev_summary.csv',summary)
    print(json.dumps(summary,indent=2))
    return rows

if __name__=='__main__':
    inventory();reproduce()
