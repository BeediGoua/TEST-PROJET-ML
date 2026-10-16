"""Offline forced-fallback generation/replay. This is NOT the 40-second solve benchmark."""
from audit import *
import math, os, platform, time
sys.path.insert(0,str(ROOT))

def official():
    spec=importlib.util.spec_from_file_location('dsh',HANDOFF/'dsh_official.py')
    m=importlib.util.module_from_spec(spec);sys.modules['dsh']=m;spec.loader.exec_module(m)
    return m

def require_gpu():
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('NOT RUN: CUDA absent. No CPU timing substituted for GPU measurements.')
    if platform.system()!='Linux':
        raise RuntimeError('NOT RUN: Linux required for official subprocess and alarm semantics.')

def generate_cache(model='Qwen/Qwen2.5-Coder-1.5B-Instruct',prompt_agent='stage3',seed=0,
                   protocol_version='v1_seed_once'):
    """Generate frozen Qwen cache. Do not silently reuse after protocol_version changes.

    protocol_version:
      - v1_seed_once: torch.manual_seed(seed) once before all batches (legacy cache 34d6ece55b3c092a)
      - v2_seed_per_batch: reserved for Colab V2 — seed each generate batch like Stage3 solve
        (manual_seed(0) per Agent.solve). Changing this string MUST change the cache key.
    """
    require_gpu();dsh=official()
    from src.evaluation.core import _materialize_all
    m=load(prompt_agent);m.MODEL=model
    import torch
    torch.manual_seed(seed)
    agent=m.Agent()
    tasks=[t for t in json.loads((HANDOFF/'dev.json').read_text(encoding='utf-8')) if t['type'].startswith('table.')]
    config=dict(model=model,revision=dsh.cached_revision(model),prompt_agent=prompt_agent,seed=seed,
                protocol_version=protocol_version,max_new=m.MAX_NEW,samples=4,temperature=.5,
                artifact_sha256=hashlib.sha256((HANDOFF/FILES[prompt_agent]).read_bytes()).hexdigest(),
                dev_sha256=hashlib.sha256((HANDOFF/'dev.json').read_bytes()).hexdigest(),torch=torch.__version__,platform=platform.platform())
    key=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
    path=OUT/f'generations_{key}.json'
    if path.exists():return path
    if protocol_version=='v2_seed_per_batch':
        raise NotImplementedError(
            'v2_seed_per_batch is reserved for Colab V2; implement seed-per-batch then regenerate. '
            'Do not reuse generations_34d6ece55b3c092a under this protocol.')
    rows=[]
    with tempfile.TemporaryDirectory(prefix='audit_gpu_') as td:
        filemap=_materialize_all(tasks,td)
        for start in range(0,len(tasks),8):
            batch=tasks[start:start+8];prompts=[]
            for t in batch:
                dfs,dico=m.load_task(t['objective'],filemap[t['id']])
                notes=(m.align_keys(dfs,dico) if len(dfs)>=2 else [])+m.entity_hints(t['objective'],dico)
                prompts.append(m.build_messages('table',m.build_user('table',t['objective'],dfs,dico,notes),t['objective'],len(dfs)))
            for phase,n,temp in [('greedy',1,0.),('samples',4,.5)]:
                begin=time.perf_counter();outs=agent.generate(prompts,n,temp,max_new=m.MAX_NEW)
                elapsed=time.perf_counter()-begin
                for t,p,oo in zip(batch,prompts,outs):
                    for index,out in enumerate(oo):
                        rows.append(dict(id=t['id'],type=t['type'],phase=phase,sample=index,prompt=p,text=out,code=m.extract_code(out),generation_batch_seconds=elapsed))
            # A partial file is explicitly distinguished from a complete cache.
            path.with_suffix('.partial.json').write_text(json.dumps(dict(config=config,rows=rows),ensure_ascii=False,indent=2),encoding='utf-8')
    path.write_text(json.dumps(dict(config=config,rows=rows),ensure_ascii=False,indent=2),encoding='utf-8')
    return path

def replay_cache(path,timeout=15.):
    if platform.system()!='Linux':raise RuntimeError('NOT RUN: official replay requires Linux; use probes only for Windows semantic counterexamples.')
    official()
    from src.evaluation.core import _materialize_all
    cache=json.loads(Path(path).read_text(encoding='utf-8'));tasks=json.loads((HANDOFF/'dev.json').read_text(encoding='utf-8'));byid={t['id']:t for t in tasks}
    outputs=[]
    # Every executor receives exactly the same cached code and Stage3-prepared state.
    prep=load('stage3')
    with tempfile.TemporaryDirectory(prefix='audit_replay_') as td:
        filemap=_materialize_all(tasks,td)
        for tid in dict.fromkeys(r['id'] for r in cache['rows']):
            task=byid[tid];programs=[r for r in cache['rows'] if r['id']==tid]
            # Default arms only — no ambiguous fake alias. Legacy name kept in loader as NOT_IMPLEMENTED.
            executors=['stage3','test1_single','test1_many','test1_alias_many','minimal_many','test2_batch','e4_importlib']
            for executor in executors:
                m=_load_executor_module(executor)
                if m is None:continue
                dfs,dico=prep.load_task(task['objective'],filemap[tid])
                if len(dfs)>=2:prep.align_keys(dfs,dico)
                begin=time.perf_counter()
                if executor in ('test2_batch',):
                    vals=m.run_code_batch([dict(code=r['code'],dfs=dfs,obj=task['objective']) for r in programs],timeout)
                elif executor.endswith('_many') or executor=='test1_alias_many':
                    raw=m.run_codes_many([r['code'] for r in programs],dfs,timeout,task['objective'])
                    vals=[dict(value=v,error='' if v is not None else 'batch returned None') for v in raw]
                else:
                    vals=[]
                    for r in programs:
                        # Fresh state per independent program, including the historical executor.
                        fresh,dd=prep.load_task(task['objective'],filemap[tid])
                        if len(fresh)>=2:prep.align_keys(fresh,dd)
                        v=m.run_code(r['code'],fresh,1.5 if executor in ('stage3','e4_importlib') else timeout,task['objective'])
                        vals.append(dict(value=v,error=getattr(m,'LAST_ERR','')))
                elapsed=time.perf_counter()-begin
                for r,v in zip(programs,vals):
                    value=v['value'];correct=value is not None and abs(value-float(task['answer']))<=float(task['tol'])
                    outputs.append(dict(executor=executor,id=tid,type=task['type'],phase=r['phase'],sample=r['sample'],code=r['code'],value=value,error=v.get('error',''),correct=correct,task_replay_seconds=elapsed))
    write_csv(Path(path).stem+'_replay.csv',outputs)
    return outputs

def _load_executor_module(executor):
    """Map replay arm name → agent module (supports pre-TEST3 experimental arms)."""
    if executor=='e4_importlib':
        path=Path(__file__).resolve().parent/'diagnostic'/'experimental'/'executor_e4_importlib.py'
        if not path.exists():
            return None
        spec=importlib.util.spec_from_file_location('e4_importlib',path)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    if executor=='test1_alias_many':
        path=Path(__file__).resolve().parent/'diagnostic'/'experimental'/'test1_alias_dsh.py'
        if not path.exists():
            # try bake
            try:
                sys.path.insert(0,str(Path(__file__).resolve().parent/'diagnostic'))
                from build_experimental import build_test1_alias
                build_test1_alias()
            except Exception:
                return None
            path=Path(__file__).resolve().parent/'diagnostic'/'experimental'/'test1_alias_dsh.py'
        spec=importlib.util.spec_from_file_location('test1_alias',path)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    if executor in ('test2_batch_alias','test2_batch_alias_NOT_IMPLEMENTED'):
        # NOT IMPLEMENTED: harness never injects __dsh_pd into TEST2. Do not use in default replay.
        # Kept only so old CSVs mentioning the name remain interpretable as a stub arm.
        return None
    label=executor.split('_')[0]
    if label=='minimal':
        return load('minimal')
    if label in FILES:
        return load(label)
    return None

def summarize_replay(rows):
    import pandas as pd
    data=pd.DataFrame(rows);gold={t['id']:t for t in json.loads((HANDOFF/'dev.json').read_text(encoding='utf-8'))};m=load('stage3');out=[]
    for (executor,tid),g in data.groupby(['executor','id']):
        candidates=[(r.value,1.5 if r.phase=='greedy' else 1.) for r in g.itertuples() if pd.notna(r.value)]
        task=gold[tid];nd=m.decimals(task['objective']);v=m.vote(candidates,nd)
        if nd is not None:v=round(v,nd)
        out.append(dict(executor=executor,id=tid,execution_rate=g.value.notna().mean(),
                        greedy_correct=bool(g.loc[g.phase=='greedy','correct'].any()) if (g.phase=='greedy').any() else False,
                        oracle_samples_at4=bool(g.loc[g.phase=='samples','correct'].any()),
                        oracle_greedy_plus4=bool(g.correct.any()),
                        vote_correct=abs(v-task['answer'])<=task['tol'] if v is not None else False))
    return pd.DataFrame(out).groupby('executor').agg(
        tasks=('id','count'),
        execution_rate=('execution_rate','mean'),
        greedy_accuracy=('greedy_correct','mean'),
        oracle_samples_at4=('oracle_samples_at4','mean'),
        oracle_greedy_plus4=('oracle_greedy_plus4','mean'),
        vote_accuracy=('vote_correct','mean'),
    )
