"""Single-change wrapper ablation, applied only to child code in the experiment."""
from probes import *

def run():
    from src.evaluation import dsh_compat
    rows=[]
    code='import pandas as pd\nanswer = float(dfs["data"]["x"].sum())'
    with tempfile.TemporaryDirectory(prefix='audit_ablation_') as td:
        p=Path(td)/'data.csv';p.write_text('x\n2\n4\n',encoding='utf-8')
        for label,fix in [('stage3',False),('test1',False),('minimal',False),('test2',False),('test2',True)]:
            def runner(source,**kw):
                if fix:
                    source=source.replace('    __orig_read_csv = pd.read_csv','    __orig_read_csv = __dsh_pd.read_csv')
                    source=source.replace('    pd.read_csv = _fake_read_csv(dfs, __extra)','    __dsh_pd.read_csv = _fake_read_csv(dfs, __extra)')
                    source=source.replace('        pd.read_csv = __orig_read_csv','        __dsh_pd.read_csv = __orig_read_csv')
                    source='import pandas as __dsh_pd\n'+source
                return dsh_compat.run_python(SIGNAL_SHIM+'\n'+source,**kw)
            sys.modules['dsh']=types.SimpleNamespace(run_python=runner)
            m=load(label)
            # Semantics-only experiment: avoid host startup speed confounding the result.
            m.BUDGET=180;m.EXEC_TIMEOUT=20
            for name in ['table_stat_rule','table_group_rule','table_join_rule','table_derive_rule','table_filter_rule','table_extended_rule','table_extra_safe2']:
                if hasattr(m,name):setattr(m,name,lambda *a:None)
            # Preserve production orchestration, increase only tool timeout equally in all sandbox arms.
            base_runner=runner
            def generous(source,**kw):
                kw['timeout_s']=30
                return base_runner(source,**kw)
            sys.modules['dsh']=types.SimpleNamespace(run_python=generous)
            a=m.Agent.__new__(m.Agent);a.torch=types.SimpleNamespace(manual_seed=lambda _:None)
            a.tok=types.SimpleNamespace(chat_template='',apply_chat_template=lambda *a,**kw:'')
            a.generate=lambda prompts,n,temp,**kw:[[code+'\n```']*n for _ in prompts]
            with contextlib.redirect_stdout(io.StringIO()) as log:
                result=a.solve([dict(id='fixed_code',objective='What is the sum of x? Round to 2 decimals.',files=[str(p)])])
            rows.append(dict(agent=label,wrapper_alias_fix=fix,code=code,answer=result[0]['answer'],correct=result[0]['answer']==6,log=log.getvalue()))
    write_csv('wrapper_ablation.csv',rows)
    print(json.dumps(rows,indent=2))
    return rows

if __name__=='__main__':
    sys.path.insert(0,str(ROOT));run()
