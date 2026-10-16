import json, random
from pathlib import Path
import numpy as np, pandas as pd
SEED=4242707
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
    n=32
    x=np.round(nr.normal(50+rep,12,n),2)
    y=np.round(.5*x+nr.normal(7,6,n),2)
    w=np.round(nr.uniform(.5,5,n),2)
    grps=np.array(['A','B','C','D']*(n//4))
    nr.shuffle(grps)
    labels=np.array([rng.choice(['AA','AB','BA','CA','DA'])+f'{j:02d}' for j in range(n)])
    starts=pd.to_datetime('2025-01-01')+pd.to_timedelta(nr.integers(0,120,n),unit='D')
    days=nr.integers(1,45,n); ends=starts+pd.to_timedelta(days,unit='D')
    return pd.DataFrame({'x':x,'w':w,'grp':grps,'label':labels,'start':starts.strftime('%Y-%m-%d'),'end':ends.strftime('%Y-%m-%d'),'y':y})

def task(idx,fam,df):
    files={'facts.csv':txt(df),'data_dictionary.csv':dd1()}
    if fam=='filtered_iqr':
        z=df.loc[df.grp=='A','x']; ans=float(z.quantile(.75)-z.quantile(.25));
        obj="Among records whose segment label is 'A', what is the interquartile range (75th percentile minus 25th percentile) of the primary measurement? Round to 2 decimals.";tol=.015
    elif fam=='filtered_weighted_mean':
        z=df[df.grp=='B']; ans=float(np.average(z.x,weights=z.w));
        obj="For records whose segment label is 'B', compute the weighted mean of the primary measurement using observation weight as the weight. Round to 2 decimals.";tol=.015
    elif fam=='filtered_topk':
        z=df.loc[df.grp=='C','x'].drop_duplicates().nlargest(3); ans=float(z.mean());
        obj="Within segment label 'C', what is the mean of the 3 largest distinct primary measurement values? Round to 2 decimals.";tol=.015
    elif fam=='filtered_string_prefix':
        z=df[df.grp=='A']; ans=float(z.label.astype(str).str.startswith('A').sum());
        obj="Among records whose segment label is 'A', how many have a record label that starts with 'A'? Give a whole number.";tol=1e-6
    elif fam=='filtered_duration':
        z=df[df.grp=='D']; d=(pd.to_datetime(z.end)-pd.to_datetime(z.start)).dt.days; ans=float(d.mean());
        obj="For records whose segment label is 'D', compute the number of days from the start date to the end date for each row. What is the mean duration? Round to 2 decimals.";tol=.015
    elif fam=='restricted_share':
        z=df[df.grp.isin(['A','B'])]; ans=float(100*z.loc[z.grp=='A','x'].sum()/z.x.sum());
        obj="Considering only records whose segment label is either 'A' or 'B', what percentage of the total primary measurement is contributed by segment label 'A'? Round to 2 decimals.";tol=.015
    elif fam=='filtered_covariance':
        z=df[df.grp=='C'][['x','y']]; ans=float(z.cov(ddof=1).iloc[0,1]);
        obj="Among records in segment label 'C', what is the sample covariance between the primary measurement and the secondary measurement? Round to 2 decimals.";tol=.015
    elif fam=='percentile_gap':
        x=df.x; ans=float(x.quantile(.90,interpolation='linear')-x.quantile(.10,interpolation='linear'));
        obj="Compute the 90th percentile minus the 10th percentile of the primary measurement in facts.csv, using linear interpolation. Round to 2 decimals.";tol=.015
    else: raise KeyError(fam)
    return {'id':f'o4_{idx:03d}','objective':obj,'files':files,'answer':ans,'tol':tol,'type':'table.fresh4_'+fam}

def generate():
    fams=['filtered_iqr','filtered_weighted_mean','filtered_topk','filtered_string_prefix','filtered_duration','restricted_share','filtered_covariance','percentile_gap']
    out=[]; idx=1
    for rep in range(8):
        df=one(rep)
        for fam in fams:
            out.append(task(idx,fam,df)); idx+=1
    return out

if __name__=='__main__':
    p=Path(__file__).with_name('ood4_composition_redteam.json')
    generated=json.dumps(generate(),indent=2)
    import sys
    if '--check' in sys.argv:
        current=p.read_text(encoding='utf-8')
        if current != generated:
            raise SystemExit(f'CHECK FAILED: {p} does not match generator output')
        print('CHECK OK:',p,len(generate()))
    else:
        p.write_text(generated,encoding='utf-8'); print(p,len(generate()))
