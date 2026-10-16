import json, random
from pathlib import Path
import numpy as np, pandas as pd
SEED=4242819
rng=random.Random(SEED); nr=np.random.default_rng(SEED)

def txt(df): return df.to_csv(index=False,lineterminator='\n')

def dd1(): return ('file,column,description,unit\n'
'facts.csv,x,"Primary measurement",unit\n'
'facts.csv,w,"Observation weight",unitless\n'
'facts.csv,grp,"Segment label",\n'
'facts.csv,label,"Record label",\n'
'facts.csv,start,"Start date",\n'
'facts.csv,end,"End date",\n'
'facts.csv,y,"Secondary measurement",unit\n')

def one(rep):
    n=36
    x=np.round(nr.normal(48+rep,14,n),2)
    y=np.round(.55*x+nr.normal(4,7,n),2)
    w=np.round(nr.uniform(.4,5.5,n),2)
    grps=np.array(['A','B','C','D']*9); nr.shuffle(grps)
    labels=np.array([rng.choice(['AA','AC','BA','CB','DX'])+f'{j:02d}' for j in range(n)])
    starts=pd.to_datetime('2025-04-01')+pd.to_timedelta(nr.integers(0,140,n),unit='D')
    days=nr.integers(1,50,n); ends=starts+pd.to_timedelta(days,unit='D')
    return pd.DataFrame({'x':x,'w':w,'grp':grps,'label':labels,'start':starts.strftime('%Y-%m-%d'),'end':ends.strftime('%Y-%m-%d'),'y':y})

def task(idx,fam,df):
    files={'facts.csv':txt(df),'data_dictionary.csv':dd1()}
    if fam=='selected_iqr':
        z=df.loc[df.grp=='B','x']; ans=float(z.quantile(.75)-z.quantile(.25));
        obj="After selecting segment label 'B', compute the interquartile range (75th percentile minus 25th percentile) of the primary measurement. Round to 2 decimals.";tol=.015
    elif fam=='onlyrows_weighted_mean':
        z=df[df.grp=='C']; ans=float(np.average(z.x,weights=z.w));
        obj="Use only rows assigned to segment label 'C'. Compute the weighted mean of the primary measurement using observation weight as the weight. Round to 2 decimals.";tol=.015
    elif fam=='assigned_topk':
        z=df.loc[df.grp=='D','x'].drop_duplicates().nlargest(3); ans=float(z.mean());
        obj="On rows assigned to segment label 'D', what is the mean of the 3 largest distinct primary measurement values? Round to 2 decimals.";tol=.015
    elif fam=='selected_string_prefix':
        z=df[df.grp=='B']; ans=float(z.label.astype(str).str.startswith('A').sum());
        obj="After selecting segment label 'B', how many rows have a record label that starts with 'A'? Give a whole number.";tol=1e-6
    elif fam=='selected_duration':
        z=df[df.grp=='A']; d=(pd.to_datetime(z.end)-pd.to_datetime(z.start)).dt.days; ans=float(d.mean());
        obj="Use only rows assigned to segment label 'A'. For each selected row compute days from the start date to the end date. What is the mean duration? Round to 2 decimals.";tol=.015
    elif fam=='two_group_share':
        z=df[df.grp.isin(['C','D'])]; ans=float(100*z.loc[z.grp=='C','x'].sum()/z.x.sum());
        obj="After retaining segment labels 'C' and 'D' only, what percentage of their total primary measurement is contributed by segment label 'C'? Round to 2 decimals.";tol=.015
    elif fam=='selected_covariance':
        z=df[df.grp=='A'][['x','y']]; ans=float(z.cov(ddof=1).iloc[0,1]);
        obj="Using only rows assigned to segment label 'A', compute the sample covariance between the primary measurement and the secondary measurement. Round to 2 decimals.";tol=.015
    elif fam=='decile_spread':
        x=df.x; ans=float(x.quantile(.9,interpolation='linear')-x.quantile(.1,interpolation='linear'));
        obj="What is the spread from the 10th percentile to the 90th percentile of the primary measurement in facts.csv, i.e. P90 minus P10? Round to 2 decimals.";tol=.015
    else: raise KeyError(fam)
    return {'id':f'o5_{idx:03d}','objective':obj,'files':files,'answer':ans,'tol':tol,'type':'table.blind5_'+fam}

def generate():
    fams=['selected_iqr','onlyrows_weighted_mean','assigned_topk','selected_string_prefix','selected_duration','two_group_share','selected_covariance','decile_spread']
    out=[];idx=1
    for rep in range(6):
        df=one(rep)
        for fam in fams:
            out.append(task(idx,fam,df));idx+=1
    return out

if __name__=='__main__':
    p=Path(__file__).with_name('ood5_blind_final.json')
    generated=json.dumps(generate(),indent=2)
    import sys
    if '--check' in sys.argv:
        current=p.read_text(encoding='utf-8')
        if current != generated:
            raise SystemExit(f'CHECK FAILED: {p} does not match generator output')
        print('CHECK OK:',p,len(generate()))
    else:
        p.write_text(generated,encoding='utf-8'); print(p,len(generate()))
