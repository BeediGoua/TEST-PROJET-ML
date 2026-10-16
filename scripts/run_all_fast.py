"""Quick smoke reproduction of the most important evidence.

This intentionally does not recompute every historical matrix. Use the individual
scripts without --mutation/--dataset, or their --all options, for exhaustive runs.
"""
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
commands=[
    [sys.executable,'scripts/check_setup.py'],
    [sys.executable,'scripts/run_stage3_audit.py'],
    [sys.executable,'scripts/compare_agents.py','--agent','v10'],
    [sys.executable,'scripts/run_metamorphic.py','--agent','naive','--mutation','explicit_unrelated_pre'],
    [sys.executable,'scripts/run_metamorphic.py','--agent','v10','--mutation','explicit_unrelated_pre'],
    [sys.executable,'scripts/run_ood.py','--agent','v9','--dataset','ood4'],
    [sys.executable,'scripts/run_ood.py','--agent','v10','--dataset','ood4'],
    [sys.executable,'scripts/run_ood.py','--agent','v10','--dataset','ood5'],
    [sys.executable,'scripts/run_tool_contract.py'],
]
for cmd in commands:
    print('\n>>>',' '.join(cmd),flush=True)
    subprocess.run(cmd,cwd=ROOT,check=True)
print('\nKEY REPRODUCTION COMPLETE')
