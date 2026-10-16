# CACHE DEEP ANALYSIS — Phase A

**Cache:** `generations_34d6ece55b3c092a.json` (REAL_QWEN, frozen)

**Tasks:** 80 | **Programs:** 400

## Definitions

- Candidates ordered: greedy, then samples 0..k-1.

- `oracle@k`: any correct among greedy + first k samples.

- `vote@k`: Stage3.vote on finite values among those candidates.

## oracle@k / vote@k

| k | oracle@k | vote@k |
|---:|---:|---:|
| 1 | 0.6500 (52) | 0.6000 (48) |
| 2 | 0.7250 (58) | 0.6625 (53) |
| 3 | 0.8000 (64) | 0.7500 (60) |
| 4 | 0.8250 (66) | 0.7875 (63) |

## Greedy vs samples buckets

- both: **33**
- greedy_only: **7**
- samples_only (sampling saves greedy): **26**
- neither (dead): **14**

## Dead tasks (neither)

Count: **14**

| cause | count |
|---|---:|
| date | 7 |
| missing_values | 3 |
| join | 2 |
| wrong_filter | 1 |
| aggregation | 1 |

### error_kind (reasoning vs execution)

- mixed: 9
- execution: 4
- reasoning: 1

### Dead task ids

- `d_006` (table.group): cause=join kind=execution gold=30.73
- `d_021` (table.filter): cause=wrong_filter kind=mixed gold=21.43
- `d_024` (table.group): cause=date kind=mixed gold=4.0
- `d_029` (table.derive): cause=date kind=mixed gold=1536.79
- `d_035` (table.stat): cause=date kind=execution gold=943.0
- `d_059` (table.group): cause=missing_values kind=execution gold=1.0
- `d_092` (table.join): cause=aggregation kind=mixed gold=707.4
- `d_100` (table.derive): cause=date kind=mixed gold=1.31
- `d_105` (table.group): cause=date kind=mixed gold=4436.0
- `d_112` (table.filter): cause=missing_values kind=reasoning gold=73.42
- `d_124` (table.filter): cause=date kind=mixed gold=0.333
- `d_129` (table.derive): cause=missing_values kind=mixed gold=0.95
- `d_165` (table.derive): cause=date kind=execution gold=0.5
- `d_166` (table.join): cause=join kind=mixed gold=127.07

## Stage3 non-numeric program taxonomy

| category | count |
|---|---:|
| AttributeError | 55 |
| KeyError | 45 |
| missing_answer | 40 |
| other | 13 |
| NameError | 7 |
| non_finite | 7 |
| TypeError | 6 |
| IndexError | 4 |
| SyntaxError | 1 |

- numeric programs: 222

## Note
These 14 dead tasks are the seed of a future Improvement Benchmark — not a signal to add regex rules or change prompts in Phase A.
