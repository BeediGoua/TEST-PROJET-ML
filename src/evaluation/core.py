
from __future__ import annotations
from pathlib import Path
import importlib.util, json, math, tempfile, time
import pandas as pd

RULE_ORDER = [
    'table_stat_rule','table_group_rule','table_join_rule',
    'table_derive_rule','table_filter_rule','table_extended_rule'
]

def repository_root(start: Path | None = None) -> Path:
    p = Path(start or Path.cwd()).resolve()
    candidates = [p, *p.parents]
    for c in candidates:
        if (c/'README.md').exists() and (c/'agents').exists() and (c/'src/evaluation').exists():
            return c
    # useful when called from a file under src/
    here = Path(__file__).resolve()
    for c in [here.parent, *here.parents]:
        if (c/'README.md').exists() and (c/'agents').exists():
            return c
    raise FileNotFoundError('DS_Harness_Experiments root not found')

def load_tasks(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def load_agent_module(path, label=None):
    path = Path(path)
    label = label or path.stem
    spec = importlib.util.spec_from_file_location(f'dsh_eval_{label}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _materialize_all(tasks, root):
    mapping = {}
    root = Path(root)
    for t in tasks:
        d = root / str(t['id'])
        d.mkdir(parents=True, exist_ok=True)
        paths=[]
        for name, text in (t.get('files') or {}).items():
            p=d/name
            p.write_text(text,encoding='utf-8')
            paths.append(str(p))
        mapping[t['id']] = paths
    return mapping

def _safe_float(value):
    try:
        x=float(value)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def deterministic_answer(module, task, file_paths):
    original = task['objective']
    strip = getattr(module, '_strip_explicit_distractors', None)
    rule_objective = strip(original) if strip else original
    kind = module.route(file_paths)
    try:
        dfs, dico = module.load_task(rule_objective, file_paths)
    except Exception as e:
        return None, None, kind, f'load_task:{type(e).__name__}:{e}'

    if kind == 'nofile':
        calls = [('calc_rules', getattr(module,'calc_rules',None))]
    elif kind == 'fit':
        calls = [('fit_rules', getattr(module,'fit_rules',None))]
    else:
        calls = [(n,getattr(module,n,None)) for n in RULE_ORDER]

    for name, fn in calls:
        if fn is None: continue
        try:
            value = fn(rule_objective) if kind == 'nofile' else fn(rule_objective, dfs, dico)
        except Exception as e:
            # deterministic rules are selective: an exception is treated like abstention
            continue
        value = _safe_float(value)
        if value is not None:
            return value, name, kind, None
    return None, None, kind, None

def evaluate_deterministic(module, tasks, dataset='dataset'):
    rows=[]
    t0=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='dsh_eval_') as td:
        file_map=_materialize_all(tasks,td)
        for t in tasks:
            pred, rule, kind, error = deterministic_answer(module,t,file_map[t['id']])
            answer=float(t['answer']); tol=float(t['tol'])
            covered = pred is not None
            correct = bool(covered and abs(pred-answer) <= tol)
            rows.append({
                'dataset':dataset,'id':t['id'],'type':t.get('type','unknown'),
                'family':t.get('type','unknown').split('.')[0], 'route':kind,
                'covered':covered,'correct':correct,'wrong':bool(covered and not correct),
                'prediction':pred,'answer':answer,'tol':tol,'rule':rule,'error':error,
            })
    df=pd.DataFrame(rows)
    df.attrs['elapsed_s']=time.perf_counter()-t0
    return df

def evaluate_agents(agent_paths: dict[str,Path], tasks, dataset='dataset'):
    parts=[]
    for label,path in agent_paths.items():
        module=load_agent_module(path,label)
        df=evaluate_deterministic(module,tasks,dataset)
        df.insert(0,'agent',label)
        parts.append(df)
    return pd.concat(parts,ignore_index=True)
