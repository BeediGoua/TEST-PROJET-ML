import csv, io, json, math, random, statistics
from pathlib import Path
import numpy as np
import pandas as pd

SEED=9102026
rng=random.Random(SEED)
np_rng=np.random.default_rng(SEED)

def csv_text(df):
 return df.to_csv(index=False, lineterminator='\n')

def dd_one():
 return ('file,column,description,unit\n'
         'facts.csv,x,"Primary measurement",unit\n'
         'facts.csv,y,"Secondary measurement",unit\n'
         'facts.csv,w,"Observation weight",unitless\n'
         'facts.csv,grp,"Segment label",\n'
         'facts.csv,label,"Record label",\n'
         'facts.csv,year,"Observation year",year\n')

def make_one(i):
 n=28
 x=np.round(np_rng.normal(50+i*.1,14,n),2)
 y=np.round(0.4*x+np_rng.normal(10,7,n),2)
 w=np.round(np_rng.uniform(.5,5,n),2)
 grp=np.array([rng.choice(['A','B','C']) for _ in range(n)])
 label=np.array([rng.choice(['ALPHA','BETA','GAMMA','DELTA'])+rng.choice(['X','Y','Z']) for _ in range(n)])
 year=np.array([rng.choice([2021,2022,2023,2024,2025]) for _ in range(n)])
 return pd.DataFrame({'x':x,'y':y,'w':w,'grp':grp,'label':label,'year':year})

def task_one(idx,fam,df):
 files={'facts.csv':csv_text(df),'data_dictionary.csv':dd_one()}
 x=df.x.astype(float); y=df.y.astype(float)
 if fam=='trimmed_mean':
  # 10% trimmed on each side using floor(n*0.1), explicit definition
  k=int(math.floor(len(x)*0.10)); z=np.sort(x.to_numpy())[k:len(x)-k]; ans=float(z.mean())
  obj='Using facts.csv, compute the 10% trimmed mean of the primary measurement: sort the non-missing values, remove floor(10% of n) observations from each tail, then take the mean. Round to 2 decimals.'
  tol=.015
 elif fam=='coef_variation':
  ans=float(x.std(ddof=1)/x.mean()*100)
  obj='What is the sample coefficient of variation of the primary measurement in facts.csv, defined as 100 times the sample standard deviation (ddof=1) divided by the mean? Round to 2 decimals.';tol=.015
 elif fam=='p90':
  ans=float(x.quantile(.90,interpolation='linear'))
  obj='What is the 90th percentile of the primary measurement in facts.csv using linear interpolation? Round to 2 decimals.';tol=.015
 elif fam=='prop_above':
  thr=float(np.median(x)); ans=float(100*(x>thr).mean())
  obj=f'What percentage of records in facts.csv have primary measurement strictly greater than {thr:.2f}? Round to 2 decimals.';tol=.015
 elif fam=='mad':
  med=float(x.median()); ans=float(np.median(np.abs(x-med)))
  obj='Compute the median absolute deviation of the primary measurement in facts.csv, defined as median(|x - median(x)|), without any scaling constant. Round to 2 decimals.';tol=.015
 elif fam=='group_median_diff':
  # ensure groups exist
  a=x[df.grp=='A']; b=x[df.grp=='B']; ans=float(a.median()-b.median())
  obj="What is the median primary measurement for segment 'A' minus the median primary measurement for segment 'B' in facts.csv? Round to 2 decimals.";tol=.015
 elif fam=='string_suffix':
  suffix='X';ans=float(df.label.astype(str).str.endswith(suffix).sum())
  obj="How many records in facts.csv have a record label that ends with 'X'? Give a whole number.";tol=1e-6
 elif fam=='ratio_sums':
  ans=float(x.sum()/y.sum())
  obj='Compute the sum of the primary measurement divided by the sum of the secondary measurement over all records in facts.csv. Round to 3 decimals.';tol=.0015
 elif fam=='filtered_corr':
  target='A'; z=df[df.grp==target][['x','y']]; ans=float(z.x.corr(z.y))
  obj="Among records whose segment label is 'A', compute the Pearson correlation between the primary measurement and the secondary measurement. Round to 3 decimals.";tol=.0015
 elif fam=='year_max_median':
  g=df.groupby('year').x.median(); ans=float(g.idxmax())
  obj='For each observation year in facts.csv, compute the median primary measurement. Which year has the largest median? Return the year as an integer.';tol=1e-6
 else: raise KeyError(fam)
 return {'id':f'h2_{idx:03d}','objective':obj,'files':files,'answer':ans,'tol':tol,'type':'table.holdout_'+fam}

def dd_join():
 return ('file,column,description,unit\n'
         'events.csv,eid,"Event identifier",\n'
         'events.csv,entity,"Entity identifier",\n'
         'events.csv,value,"Event value",unit\n'
         'entities.csv,entity,"Entity identifier",\n'
         'entities.csv,segment,"Entity segment",\n'
         'entities.csv,weight,"Entity weight",unitless\n')

def make_join(i):
 nent=12
 entities=pd.DataFrame({'entity':[f'E{j:02d}' for j in range(nent)],
                        'segment':[rng.choice(['North','South']) for _ in range(nent)],
                        'weight':np.round(np_rng.uniform(.5,4,nent),2)})
 nevt=36
 events=pd.DataFrame({'eid':range(1,nevt+1),
                      'entity':[rng.choice(entities.entity.tolist()) for _ in range(nevt)],
                      'value':np.round(np_rng.normal(25,8,nevt),2)})
 return events,entities

def task_join(idx,fam,ev,en):
 files={'events.csv':csv_text(ev),'entities.csv':csv_text(en),'data_dictionary.csv':dd_join()}
 j=ev.merge(en,on='entity',how='inner')
 if fam=='join_count':
  ans=float((j.segment=='North').sum())
  obj="Join events.csv to entities.csv using the entity identifier. How many event rows belong to entities whose entity segment is 'North'? Give a whole number.";tol=1e-6
 elif fam=='join_weighted_mean':
  z=j[j.segment=='South'];ans=float(np.average(z.value,weights=z.weight))
  obj="Join events.csv to entities.csv using the entity identifier. For event rows belonging to entities whose entity segment is 'South', compute the weighted mean of event value using entity weight as the weight. Round to 2 decimals.";tol=.015
 else:raise KeyError(fam)
 return {'id':f'h2_{idx:03d}','objective':obj,'files':files,'answer':ans,'tol':tol,'type':'table.holdout_'+fam}

def generate():
 families=['trimmed_mean','coef_variation','p90','prop_above','mad','group_median_diff','string_suffix','ratio_sums','filtered_corr','year_max_median','join_count','join_weighted_mean']
 tasks=[];idx=1
 for rep in range(10):
  df=make_one(rep)
  for fam in families[:10]: tasks.append(task_one(idx,fam,df));idx+=1
  ev,en=make_join(rep)
  for fam in families[10:]: tasks.append(task_join(idx,fam,ev,en));idx+=1
 return tasks

if __name__=='__main__':
 import sys
 p=Path(__file__).with_name('ood2_tables.json')
 generated=json.dumps(generate(),ensure_ascii=False,indent=2) if 'generate_ood2.py'=='generate_ood2.py' else json.dumps(generate(),indent=2)
 if '--check' in sys.argv:
  current=p.read_text(encoding='utf-8')
  if current != generated:
   raise SystemExit(f'CHECK FAILED: {p} does not match generator output')
  print('CHECK OK:',p,len(generate()))
 else:
  p.write_text(generated,encoding='utf-8'); print(p,len(generate()))
