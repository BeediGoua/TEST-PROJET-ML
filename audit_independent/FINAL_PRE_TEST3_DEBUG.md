# FINAL PRE-TEST3 DEBUG — rapport complet

**Recommendation: `DO_NOT_SUBMIT`**

Pas de Qwen3 / nouveaux prompts / regex / règles. Diagnostic ciblé seulement.

---

## 1. B2 Tables

### Ancien résultat Colab → **INVALID**
- 80/80 en ~0.36 s = règles déterministes, pas LLM
- Cause code : `FORCE_FALLBACK` figé à l’import + Stage3 stock sans flag

### Re-instrument Colab → **VALID** (chemin forced-fallback)
Batch 8 Tables, un seul agent E2T, `DSH_FORCE_FALLBACK=1` :

| metric | value |
|---|---:|
| deterministic_count | **0** |
| llm_live_count | **8** |
| greedy_generation_seconds | **10.81** |
| greedy_outputs | 8 |
| repair_count | 3 |
| sample_outputs | 0 |
| total_seconds | **28.16** |

→ Recovery Tables sous vrai LLM est crédible. Accuracy 80 tâches Stage3-vs-E2T sous vrai fallback non rejouée (VRAM) — secondaire tant que B3 bloque.

---

## 2. B3 No-files flips (MEASURED Colab)

| bras | accuracy |
|---|---:|
| Stage3 | **39/40** |
| E2T | **36/40** |

### Pertes (Stage3 OK → E2T = 0.0)

| id | type | gold | lecture |
|---|---|---:|---|
| d_026 | calc.dates | 13 | E2T aucun candidat fini |
| d_065 | calc.arithmetic | 6 | idem |
| d_076 | calc.dates | 16 | idem |
| d_143 | calc.stats_inline | 8.9 | idem |

`0.0` = défaut `solve()` quand vote vide, pas une mauvaise valeur numérique E2T.

### Gain (Stage3 KO → E2T OK)

| id | type | gold | Stage3 | E2T |
|---|---|---:|---:|---:|
| d_123 | calc.integer (modulo) | 27 | 13 | **27** |

Net : −4 +1 = −3 vs Stage3.

---

## 3. Counterfactual exécuteur (MEASURED local)

Programmes **corrects** (humains) exécutés sous Stage3 `run_code` et E2T `run_codes_many` (dfs vides) :

| id | Stage3 | E2T | class |
|---|---|---|---|
| d_026 | OK | OK | executor OK |
| d_065 | OK | OK | executor OK |
| d_076 | OK | OK | executor OK |
| d_143 | OK | OK | executor OK |
| d_123 | OK | OK | executor OK |

Artefacts : `diagnostic/results/NOFILE_COUNTERFACTUAL.md`, `nofile_counterfactual_refcodes.csv`.

### Classification des 4 pertes Colab

```text
GENERATION / REPAIR / CONTROL-FLOW / BUDGET
```

**Pas** « E2T incapable d’exécuter la bonne solution » pour ces énoncés.

(Counterfactual sur les *codes LLM Stage3 exacts* non capturés — optionnel ; le ref-code suffit à écarter un bug exécuteur dur sur ces tâches.)

---

## 4. B4 warnings (MEASURED)

| warning | Stage3 | E2T | |
|---|---|---|---|
| exec_upload_violation | True | **False** | corrigé par E2T |
| sympy_prompt_runtime_mismatch | True | True | **INHERITED** |
| onehot_prompt_runtime_mismatch | True | True | **INHERITED** |
| no_imports_example_mismatch | True | True | **INHERITED** |

Pas de nouveau mismatch introduit par E2T.

---

## 5. Minimal fix (si on continue)

1. Instrumenter `solve` No-files sur les 4 ids : logger codes greedy/repair/samples + erreurs.  
2. Si codes absents / tronqués / timeout → **TIMING/BUDGET/CONTROL** (ex. samples skip trop agressif sous dsh plus lent).  
3. Si codes présents mais crash sous dsh → rare (ref-codes OK) → cas par cas.  
4. Fix minimal possible : garantir ≥1 sample exécuté sur nofile si greedy+repair vides ; ou aligner budget outer.  
5. **Interdit** : nouvelles regex, prompts, Qwen3.  
6. Rejouer **B3 seul** → gate E2T ≥ Stage3.

---

## 6. Recommendation

```text
DO_NOT_SUBMIT
```

| Gate | Statut |
|---|---|
| B2 vrai LLM | VALID |
| B3 No-files E2T ≥ Stage3 | **FAIL** |
| B4 exec clean | OK (warnings hérités) |

Soumettre le zip actuel serait une recovery **incomplète** sur No-files (−3 net vs Stage3 public uncovered).
