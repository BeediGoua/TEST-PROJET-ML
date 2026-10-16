import json, random, math
from pathlib import Path
import numpy as np, pandas as pd
SEED=4242601
rng=random.Random(SEED); nr=np.random.default_rng(SEED)

def txt(df): return df.to_csv(index=False,lineterminator='\n')

def dd1(): return ('file,column,description,unit\n'
'facts.csv,x,"Primary measurement",unit\n'
'facts.csv,w,"Observation weight",unitless\n'
'facts.csv,grp,"Segment",\n'
'facts.csv,label,"Record label",\n'
'facts.csv,start,"Start date",\n'
'facts.csv,end,"End date",\n'
'facts.csv,y,"Secondary measurement",unit\n')

def one(rep):
 n=24
 x=np.round(nr.normal(50,13,n),2); y=np.round(.6*x+nr.normal(8,5,n),2); w=np.round(nr.uniform(.5,4,n),2)
 grp=np.array([rng.choice(['A','B','C','D']) for _ in range(n)])
 label=np.array([rng.choice(['AX','AY','BX','CY','DZ'])+str(j) for j in range(n)])
 starts=pd.to_datetime('2024-01-01')+pd.to_timedelta(nr.integers(0,100,n),unit='D'); days=nr.integers(1,30,n); ends=starts+pd.to_timedelta(days,unit='D')
 return pd.DataFrame({'x':x,'w':w,'grp':grp,'label':label,'start':starts.strftime('%Y-%m-%d'),'end':ends.strftime('%Y-%m-%d'),'y':y})

def task(idx,fam,df):
 f={'facts.csv':txt(df),'data_dictionary.csv':dd1()}; x=df.x.astype(float); y=df.y.astype(float)
 if fam=='iqr': ans=float(x.quantile(.75)-x.quantile(.25)); obj='What is the interquartile range (75th percentile minus 25th percentile) of the primary measurement over all records in facts.csv? Round to 2 decimals.';tol=.015
 elif fam=='weighted_mean': ans=float(np.average(x,weights=df.w)); obj='Using facts.csv and its data dictionary, compute the weighted mean of the primary measurement, using observation weight as the weight. Ignore rows missing either value. Report it with 2 decimals.';tol=.015
 elif fam=='group_diff': ans=float(x[df.grp=='A'].mean()-x[df.grp=='B'].mean()); obj="What is the mean primary measurement for segment 'A' minus the mean primary measurement for segment 'B' in facts.csv? Round to 2 decimals.";tol=.015
 elif fam=='membership':
  z=x[df.grp.isin(['A','C'])];ans=float(z.mean());obj="What is the mean primary measurement for records whose segment is either 'A' or 'C' in facts.csv? Round to 2 decimals.";tol=.015
 elif fam=='string': ans=float(df.label.str.startswith('A').sum());obj="How many records in facts.csv have a record label that starts with 'A'? Give a whole number.";tol=1e-6
 elif fam=='date_delta':
  d=(pd.to_datetime(df.end)-pd.to_datetime(df.start)).dt.days;ans=float(d.mean());obj='For each row of facts.csv, compute the number of days from the start date to the end date. What is the mean duration? Round to 2 decimals.';tol=.015
 elif fam=='topk':
  z=x.drop_duplicates().nlargest(3);ans=float(z.mean());obj='What is the mean of the 3 largest distinct primary measurement values in facts.csv? Round to 2 decimals.';tol=.015
 elif fam=='share':
  ans=float(100*x[df.grp=='A'].sum()/x.sum());obj="What percentage of the total primary measurement is contributed by segment 'A' in facts.csv? Round to 2 decimals.";tol=.015
 elif fam=='covariance': ans=float(pd.DataFrame({'x':x,'y':y}).cov(ddof=1).iloc[0,1]);obj='What is the sample covariance between the primary measurement and the secondary measurement in facts.csv? Round to 2 decimals.';tol=.015
 else: raise KeyError
 return {'id':f'o1_{idx:03d}','objective':obj,'files':f,'answer':ans,'tol':tol,'type':'table.ood_'+fam}

def ddj(): return ('file,column,description,unit\n'
'fact.csv,k,"Entity key",\n'
'fact.csv,num,"Numerator measure",unit\n'
'dim.csv,k,"Entity key",\n'
'dim.csv,den,"Denominator measure",unit\n'
'dim.csv,grp,"Region",\n')

def join_task(idx,rep):
 n=14; keys=[f'K{i:02d}' for i in range(n)];dim=pd.DataFrame({'k':keys,'den':np.round(nr.uniform(2,12,n),2),'grp':[rng.choice(['North','South']) for _ in range(n)]});fact=pd.DataFrame({'k':[rng.choice(keys) for _ in range(36)],'num':np.round(nr.uniform(10,120,36),2)})
 J=fact.merge(dim,on='k');z=J[J.grp=='North'];ans=float((z.num/z.den).mean())
 obj="Join fact.csv and dim.csv on the entity key. Compute numerator measure divided by denominator measure for each joined row belonging to a region 'North'. What is the mean of these ratios? Round to 2 decimals."
 return {'id':f'o1_{idx:03d}','objective':obj,'files':{'fact.csv':txt(fact),'dim.csv':txt(dim),'data_dictionary.csv':ddj()},'answer':ans,'tol':.015,'type':'table.ood_join_derive'}

def generate():
 fams=['iqr','weighted_mean','group_diff','membership','string','date_delta','topk','share','covariance']
 out=[];idx=1
 for rep in range(8):
  df=one(rep)
  for fam in fams: out.append(task(idx,fam,df));idx+=1
  out.append(join_task(idx,rep));idx+=1
 return out
if __name__=='__main__':
 import sys
 p=Path(__file__).with_name('ood3_fresh_paraphrase.json')
 generated=json.dumps(generate(),ensure_ascii=False,indent=2) if 'generate_ood3.py'=='generate_ood2.py' else json.dumps(generate(),indent=2)
 if '--check' in sys.argv:
  current=p.read_text(encoding='utf-8')
  if current != generated:
   raise SystemExit(f'CHECK FAILED: {p} does not match generator output')
  print('CHECK OK:',p,len(generate()))
 else:
  p.write_text(generated,encoding='utf-8'); print(p,len(generate()))
