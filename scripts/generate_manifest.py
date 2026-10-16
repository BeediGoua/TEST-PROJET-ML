from pathlib import Path
import hashlib, csv
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE_PARTS={'.pytest_cache','__pycache__'}
rows=[]
for p in sorted(ROOT.rglob('*')):
    if not p.is_file() or any(part in EXCLUDE_PARTS for part in p.parts):
        continue
    rel=p.relative_to(ROOT).as_posix()
    if rel=='results/file_manifest.csv':
        continue
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    rows.append((rel,p.stat().st_size,h))
out=ROOT/'results/file_manifest.csv';out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['file','bytes','sha256']);w.writerows(rows)
print('manifest:',out,'files=',len(rows))
