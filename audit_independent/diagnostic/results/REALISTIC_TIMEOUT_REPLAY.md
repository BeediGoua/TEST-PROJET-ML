# Realistic timeout replay (outer 6.5s)

**Cache:** `generations_34d6ece55b3c092a.json`

**Outer many:** `6.5` = EXEC_TIMEOUT(5)+1.5 (TEST1 solve)

**Stage3 single:** `1.5`

| executor | agree E0-finite | agree import_pandas | exec_rate | contam_tasks | gate≥99% | p50/p95/max task-s |
|---|---:|---:|---:|---:|---|---|
| E2 | 0.9886 | 0.9862 | 0.6525 | 0 | False | 4.570/6.091/6.567 |
| E2T | 0.9735 | 0.9679 | 0.6425 | 0 | False | 4.497/6.131/6.695 |
| stage3 | 1.0000 | 1.0000 | 0.6600 | 0 | True | 0.332/0.564/4.984 |

**Gate E2T:** agree≥99%=FAIL; 0 contam=PASS
