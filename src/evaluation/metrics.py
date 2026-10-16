
import pandas as pd

def summarize_audit(df):
    n=len(df); covered=int(df['covered'].sum()); correct=int(df['correct'].sum()); wrong=int(df['wrong'].sum())
    return {
        'n':n,'covered':covered,'correct':correct,'wrong':wrong,
        'coverage': covered/n if n else 0.0,
        'precision_if_covered': correct/covered if covered else None,
        'selective_risk': 1-correct/covered if covered else None,
        'deterministic_accuracy': correct/n if n else 0.0,
    }

def family_summary(df):
    rows=[]
    group_cols=['family']
    if 'agent' in df.columns: group_cols=['agent','family']
    for key,g in df.groupby(group_cols,dropna=False):
        k=(key,) if not isinstance(key,tuple) else key
        d={c:v for c,v in zip(group_cols,k)}
        d.update(summarize_audit(g)); rows.append(d)
    return pd.DataFrame(rows)
