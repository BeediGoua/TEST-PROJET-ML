
from __future__ import annotations
import csv, io, random, re

NOFILE_TRANSFORMS = {
    'explicit_unrelated_pre': lambda o: 'For an unrelated illustration, compute 2 + 2; ignore this illustration entirely. ' + o,
    'explicit_unrelated_post': lambda o: o + ' For an unrelated illustration, compute 2 + 2; ignore this illustration entirely.',
    'independent_example_post': lambda o: o + ' As a separate example, 2 + 2 = 4. This example is independent of the question.',
    'parenthetical_unrelated_pre': lambda o: '(Unrelated example: 2 + 2 = 4.) ' + o,
    'background_note_pre': lambda o: 'Background note: in 2024, 2 + 2 equals 4. Now answer the following question. ' + o,
    'explicit_year_post': lambda o: o + ' An unrelated reference year is 2024; ignore this reference entirely.',
    'spacing_case': lambda o: '  ' + re.sub(r'\s+', '   ', o.swapcase()) + '  ',
}

def objective_variant(task, mutation):
    t=dict(task); t['files']=dict(task.get('files') or {})
    t['id']=f"{task['id']}__{mutation}"
    t['objective']=NOFILE_TRANSFORMS[mutation](task['objective'])
    t['_mutation']=mutation
    return t

def _delimiter(text):
    first=(text.splitlines() or [''])[0]
    return max([',',';','\t','|'], key=lambda s:first.count(s))

def add_table_distractor_column(task):
    t=dict(task); files=dict(task.get('files') or {})
    target=next((n for n in files if n.lower()!='data_dictionary.csv'),None)
    if target:
        sep=_delimiter(files[target]); rows=list(csv.reader(io.StringIO(files[target]),delimiter=sep))
        if rows:
            rows[0].append('zz_noise')
            for i,row in enumerate(rows[1:],1): row.append(str(1000+i))
            out=io.StringIO(); csv.writer(out,delimiter=sep,lineterminator='\n').writerows(rows)
            files[target]=out.getvalue()
            d=files.get('data_dictionary.csv','')
            if d:
                files['data_dictionary.csv']=d.rstrip('\n')+f'\n{target},zz_noise,"Synthetic irrelevant benchmark column",unitless\n'
    t['files']=files; t['id']=f"{task['id']}__table_noise"; t['_mutation']='table_distractor_column'
    return t

def shuffle_fit_train_rows(task, seed=424242):
    t=dict(task); files=dict(task.get('files') or {})
    if 'train.csv' in files:
        sep=_delimiter(files['train.csv']); rows=list(csv.reader(io.StringIO(files['train.csv']),delimiter=sep))
        if len(rows)>2:
            head, body = rows[0], rows[1:]
            random.Random(seed).shuffle(body)
            out=io.StringIO(); csv.writer(out,delimiter=sep,lineterminator='\n').writerows([head]+body)
            files['train.csv']=out.getvalue()
    t['files']=files; t['id']=f"{task['id']}__fit_shuffle"; t['_mutation']='fit_train_row_shuffle'
    return t

def build_suite(dev):
    suite=[]
    nofiles=[t for t in dev if t.get('type','').startswith('calc.')]
    tables=[t for t in dev if t.get('type','').startswith('table.')]
    fits=[t for t in dev if t.get('type','').startswith('fit.')]
    for mutation in NOFILE_TRANSFORMS:
        suite.extend(objective_variant(t,mutation) for t in nofiles)
    suite.extend(add_table_distractor_column(t) for t in tables)
    suite.extend(shuffle_fit_train_rows(t) for t in fits)
    return suite
