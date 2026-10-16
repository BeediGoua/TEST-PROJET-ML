from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_dev_shape_and_files():
    dev=json.loads((ROOT/'data/public/dev.json').read_text())
    assert len(dev)==180
    assert sum(t['type'].startswith('calc.') for t in dev)==65
    assert sum(t['type'].startswith('table.') for t in dev)==80
    assert sum(t['type'].startswith('fit.') for t in dev)==35
    for p in [
        'agents/champions/stage3_92_5.py',
        'agents/baselines/stage1_direct.py',
        'agents/baselines/stage2_tool_loop.py',
        'agents/candidates/stage4_best_local_v10.py',
        'benchmarks/ood_development/ood1_tables.json',
        'benchmarks/ood_holdout/ood2_tables.json',
        'benchmarks/ood_holdout/ood3_fresh_paraphrase.json',
        'benchmarks/ood_holdout/ood4_composition_redteam.json',
        'benchmarks/ood_holdout/ood5_blind_final.json',
        'reference/official_ds_harness/dsh.py']:
        assert (ROOT/p).exists(), p
