from pathlib import Path
import sys, json, hashlib
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=[
  'data/public/dev.json','agents/champions/stage3_92_5.py',
  'agents/baselines/stage1_direct.py','agents/baselines/stage2_tool_loop.py',
  'agents/candidates/stage4_best_local_v10.py',
  'benchmarks/ood_development/ood1_tables.json',
  'benchmarks/ood_holdout/ood2_tables.json',
  'benchmarks/ood_holdout/ood3_fresh_paraphrase.json',
  'benchmarks/ood_holdout/ood4_composition_redteam.json',
  'benchmarks/ood_holdout/ood5_blind_final.json',
  'reference/official_ds_harness/dsh.py',
  'reference/official_ds_harness/scoring.py',
  'reference/official_ds_harness/localtest.py']
missing=[p for p in REQUIRED if not (ROOT/p).exists()]
if missing: raise SystemExit('Missing files: '+', '.join(missing))
dev=json.loads((ROOT/'data/public/dev.json').read_text())
assert len(dev)==180, len(dev)
counts={k:sum(t['type'].startswith(k) for t in dev) for k in ['calc.','table.','fit.']}
assert counts=={'calc.':65,'table.':80,'fit.':35},counts
print('Repository:',ROOT)
print('Python:',sys.version.split()[0])
print('dev.json:',len(dev),'tasks',counts)
print('Core files: OK')
