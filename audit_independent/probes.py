"""Finite executor counterexamples; Windows signal shim is NOT a timing benchmark."""
from audit import *
import pandas as pd

SIGNAL_SHIM = '''
import signal
if not hasattr(signal, 'SIGALRM'):
    signal.SIGALRM = 999
    signal.ITIMER_REAL = 999
    signal.getsignal = lambda *a: None
    signal.signal = lambda *a: None
    signal.setitimer = lambda *a: None
'''

def run():
    sys.path.insert(0,str(ROOT))
    from src.evaluation import dsh_compat
    captured=[]
    def runner(code,**kwargs):
        result=dsh_compat.run_python(SIGNAL_SHIM+'\n'+code,**kwargs)
        captured.append(dict(ok=result.ok,error=result.error,value=result.value))
        return result
    sys.modules['dsh']=types.SimpleNamespace(run_python=runner)
    programs={
        'control':'answer = float(dfs["data"]["x"].sum())',
        'import_pandas':'import pandas as pd\nanswer = float(dfs["data"]["x"].sum())',
        'import_numpy':'import numpy as np\nanswer = float(dfs["data"]["x"].sum())',
        'syntax_error':'answer = (',
    }
    rows=[]
    for label in ['stage3','test1','minimal','test2']:
        m=load(label)
        dfs=m.Tables({'data':pd.DataFrame({'x':[2.,4.]})})
        for name,code in programs.items():
            captured.clear()
            if label=='test2':
                result=m.run_code_batch([dict(code=code,dfs=dfs,obj='sum')],15)
            elif label in ['test1','minimal']:
                result=m.run_codes_many([code],dfs,15,'sum')
            else:
                result=m.run_code(code,dfs,2,'sum')
            rows.append(dict(agent=label,probe=name,result=json.dumps(result),error=json.dumps(captured[-1] if captured else getattr(m,'LAST_ERR',''))))
        if label in ['test1','minimal','test2']:
            captured.clear();codes=['answer=6','answer = (','answer=42','answer=9']
            result=m.run_code_batch([dict(code=c,dfs=dfs,obj='sum') for c in codes],15) if label=='test2' else m.run_codes_many(codes,dfs,15,'sum')
            rows.append(dict(agent=label,probe='one_syntax_error_four_programs',result=json.dumps(result),error=json.dumps(captured[-1])))
    write_csv('executor_probes.csv',rows)
    for row in rows:print(row['agent'],row['probe'],row['result'])
    return rows

if __name__=='__main__':run()
