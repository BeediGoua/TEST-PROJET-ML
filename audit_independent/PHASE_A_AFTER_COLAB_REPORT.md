# Phase A — Audit après Colab (avant notebook V2 / TEST3)

**Verdict: `NO-GO`** (pas prêt pour Colab V2 end-to-end sous les critères Phase A)

**Cache figé:** `generations_34d6ece55b3c092a` (400 programmes, 80 Tables)  
**Plateforme mesures Phase A:** Windows + `dsh_compat` (pas le subprocess officiel Linux)  
**Interdictions respectées:** pas de régénération Qwen, pas de Qwen3/prompts/règles, pas de soumission TEST3.

---

## 1. Acquis figés (ne pas redécouvrir)

| Point | Statut |
|---|---|
| Stage3 privé 111/120 ; TEST1 104/120 ; −4 Tables −3 No-files | MEASURED (agrégats) |
| ~80 % `import pandas` ; 75/80 tâches | MEASURED (cache) |
| Stage3 = E2 = E4 sur 222 programmes Stage3-finis (replay 15 s) | MEASURED |
| Samples sauvent greedy faux sur 26/80 | MEASURED (Phase A cache deep) |
| TEST1-many casse massivement | MEASURED |
| Vote 63/80 vs oracle 66/80 ; 14/80 aucun candidat | MEASURED (Phase A) |
| E2 sans timeout/candidat → contagion possible | FAIL STRUCTUREL (code) |
| E2 sous vrai budget 29 s | NOT TESTED |
| Executor = exactement les 4 Tables privées | HYPOTHESIS (non observable) |
| Règles → TEST2 | NOT ESTABLISHED — ne pas investir |
| E2 récupère les 3 No-files | NOT TESTED → reporté au Colab V2 |

---

## 2. Nouveaux résultats Phase A

### 2.1 Cache deep analysis — MEASURED

Artefacts: `diagnostic/results/CACHE_DEEP_ANALYSIS.md`, CSVs `cache_*`.

| k | oracle@k | vote@k |
|---:|---:|---:|
| 1 | 52/80 (0.650) | 48/80 (0.600) |
| 2 | 58/80 (0.725) | 53/80 (0.6625) |
| 3 | 64/80 (0.800) | 60/80 (0.750) |
| 4 | 66/80 (0.825) | 63/80 (0.7875) |

Buckets: both 33 · greedy_only 7 · **samples_only 26** · **neither 14**.

Dead-task causes (seed Improvement Benchmark): date 7, missing_values 3, join 2, wrong_filter 1, aggregation 1.  
error_kind: mixed 9, execution 4, reasoning 1.

Ids: `d_006`, `d_021`, `d_024`, `d_029`, `d_035`, `d_059`, `d_092`, `d_100`, `d_105`, `d_112`, `d_124`, `d_129`, `d_165`, `d_166`.

Non-numeric taxonomy (400 programmes): AttributeError 55, KeyError 45, missing_answer 40, other 13, NameError 7, non_finite 7, TypeError 6, IndexError 4, SyntaxError 1; numeric 222.

### 2.2 E2T bake + probes — MEASURED / NOT RUN

- Baked: `diagnostic/experimental/test1_e2t_dsh.py` (E2 + SIGALRM/`setitimer` 1.5 s/candidat si dispo).
- Non-timeout probes: **10/10 PASS** (Windows).
- `infinite_loop` → **NOT RUN** on Windows. **Gate Colab V2 (première cellule):** doit produire `[6, None, 42, 9]`.

### 2.3 Realistic outer timeout 6.5 s — MEASURED

Justification outer: `6.5 = EXEC_TIMEOUT(5)+1.5` (TEST1 `solve`). Stage3 single: `1.5` s.  
Artefact: `diagnostic/results/REALISTIC_TIMEOUT_REPLAY.md`.

| executor | agree E0-finite | agree import_pandas | exec_rate | contam_tasks | gate≥99% | p50/p95/max task-s |
|---|---:|---:|---:|---:|---|---|
| E2 | 0.9886 | 0.9862 | 0.6525 | 0 | False | 4.57/6.09/6.57 |
| E2T | **0.9735** | 0.9679 | 0.6425 | 0 | **False** | 4.50/6.13/6.70 |
| stage3 | 1.0000 | 1.0000 | 0.6600 | 0 | True | 0.33/0.56/4.98 |

Désaccords = uniquement `Ei=None` alors que Stage3 fini (timeout batch outer), jamais une mauvaise valeur numérique.  
E2: 3/264 (`d_170`). E2T: 7/264 (`d_041`, `d_100`). Contagion syntax connue: **0**.

**Gate E2T ≥99%:** FAIL sur Windows/`dsh_compat`. À re-mesurer sur Linux officiel (où SIGALRM isole les candidats lents).

### 2.4 Hybrid TEST1 — MEASURED

Artefact: `diagnostic/results/HYBRID_TEST1_REPLAY.md`.

| arm | vote accuracy | note |
|---|---:|---|
| faithful_hybrid | 41/80 (0.5125) | **≠** score privé TEST1 104/120 |
| recovery E2T | 65/80 (0.8125) | = Stage3 baseline ici |
| stage3 baseline | 65/80 (0.8125) | |
| Gain(recovery, faithful) | +24 | +25 / −1 |
| Gain(recovery, stage3) | 0 | aucune flip |

### 2.5 Bras alias trompeur — MEASURED (code)

- Loader: `test2_batch_alias` / `test2_batch_alias_NOT_IMPLEMENTED` → `None`.
- Retiré de la liste `executors` par défaut dans `gpu_experiments.replay_cache`.

### 2.6 RNG / protocol_version — DERIVED (doc + code)

Voir `RNG_PROTOCOL.md`. Stage3: `manual_seed(0)` par `solve`. Cache: seed une fois (`v1_seed_once`).  
`generate_cache(..., protocol_version="v2_seed_per_batch")` réservé V2 (change la clé; ne pas réutiliser silencieusement `34d6ece55b3c092a`).

### 2.7 Synthèse étiquettes

| Item | Statut |
|---|---|
| E2T ≥99 % agree sous 6.5 s | MEASURED **FAIL** (0.9735 Windows) |
| Contam syntax E2T | MEASURED 0 |
| Hybrid documenté | MEASURED |
| `infinite_loop` probe | NOT RUN (Windows) → gate V2 |
| E2/E2T sous `Agent.solve` BUDGET 29 | NOT TESTED |
| Forced-fallback No-files end-to-end | NOT TESTED (V2) |
| Dépasser 92.5 via les 14 | HYPOTHESIS / hors Phase A |

---

## 3. Verdict

**`NO-GO`** — raisons:

1. Agree E2T vs Stage3 sous outer 6.5 s = **97.35% < 99%** (Windows).
2. Probe `infinite_loop` **NOT RUN** (SIGALRM Linux-only) — gate V2 obligatoire avant tout `solve()`.

Checklist:

- [x] analyse cache complète
- [x] E2T baked + probes non-timeout PASS
- [ ] agree E2T vs Stage3 ≥99 % sous outer 6.5 s
- [x] hybrid TEST1 documenté
- [x] bras alias neutralisé
- [x] RNG / protocol_version documentés
- [x] timeout-loop listé comme gate V2

**Aucun** verdict « prêt à soumettre TEST3 ».

Pour lever le NO-GO: Colab Linux — (a) probe loop PASS, (b) rejouer `15_realistic_timeout_replay` / équivalent officiel avec SIGALRM → agree E2T ≥99 %.

---

## 4. Roadmap hors Phase A (texte seulement)

1. **Colab V2** — première cellule: probe `infinite_loop` → `[6,None,42,9]`. Puis vrai `Agent.solve` BUDGET=29, Tables + **No-files** forced fallback, Stage3 vs Stage3+E2T; re-check agree E2T ≥99 % sous 6.5 s.
2. **Ensuite seulement** « dépasser 92.5 » via taxonomie des 14 dead tasks (prompts/repair/Qwen3/… — pas maintenant).
3. Deux futurs benchmarks:
   - **Recovery** vs **Improvement**
   - \(\mathrm{Gain}(M)=\#(S3\ \mathrm{faux}, M\ \mathrm{vrai})-\#(S3\ \mathrm{vrai}, M\ \mathrm{faux})\)
