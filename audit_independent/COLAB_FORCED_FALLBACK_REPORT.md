# Rapport Colab — forced-fallback Qwen (80 Tables)

**Source locale :** `resultats_proj/generations_34d6ece55b3c092a.{json,_replay.csv,_summary.csv}`  
**GitHub :** le cache n’est **pas** sur le remote (trop gros / non poussé) ; le notebook et le code le sont. Analyse faite sur les fichiers que tu as mis dans `resultats_proj/`.

---

## 1. Validité de l’expérience (notebook)

| Check | Résultat |
|---|---|
| Modèle | `Qwen/Qwen2.5-Coder-1.5B-Instruct` |
| Prompts | `prompt_agent=stage3` (règles Tables **non** consultées) |
| Plateforme | Linux + glibc (Colab) |
| Seed / samples / max_new | 0 / 4 / 500 |
| Tâches | **80** Tables (16 par famille × 5) |
| Programmes | **400** = 80 greedy + 320 samples |
| Replay | 8 bras d’exécuteurs × 400 programmes |

**Verdict :** expérience **valide** pour H1 + H5 + équivalence exécuteur sur corpus réel. Ce n’est **pas** le protocole privé 8×40 s.

Cellules du notebook :
1. Setup `PROJECT_ROOT` + assert CUDA → OK (sinon pas de cache).
2. `pip install` → deps.
3. `generate_cache` → produit le JSON (ce que Qwen écrit).
4. `replay_cache` → tableau que tu as collé (ce que chaque exécuteur en tire).
5. `download` → fichiers dans `resultats_proj/`.

---

## 2. Tableau replay (tes chiffres) — lecture

| Exécuteur | exec_rate | greedy_acc | oracle@4 samples | oracle greedy+4 | **vote_acc** |
|---|---:|---:|---:|---:|---:|
| **stage3** | 0.555 | 0.500 | 0.7375 | 0.8250 | **0.7875** |
| **test1_alias_many (E2)** | 0.555 | 0.500 | 0.7375 | 0.8250 | **0.7875** |
| **test1_single** | 0.555 | 0.500 | 0.7375 | 0.8250 | **0.7875** |
| **e4_importlib** | 0.555 | 0.500 | 0.7375 | 0.8250 | **0.7875** |
| test1_many (soumis) | 0.030 | 0.025 | 0.0500 | 0.0500 | **0.0500** |
| test2_batch | 0.080 | 0.025 | 0.1625 | 0.1625 | **0.1625** |
| test2_batch_alias* | 0.080 | 0.025 | 0.1625 | 0.1625 | **0.1625** |
| minimal_many | 0.080 | 0.025 | 0.1625 | 0.1625 | **0.1625** |

\*Sur Colab, `test2_batch_alias` charge TEST2 **sans** appliquer le patch `__dsh_pd` (limitation du harness `gpu_experiments._load_executor_module`). Ce n’est **pas** une preuve que l’alias TEST2 échoue — c’est un bras mal branché. Le bras fiable pour l’alias est **`test1_alias_many`**.

---

## 3. H1 — Fréquence des patterns qui cassent les wrappers

**MEASURED sur 400 programmes REAL_QWEN :**

| Pattern | Rate |
|---|---:|
| `import pandas as pd` | **80.0 %** (320/400) |
| any import | **81.0 %** |
| rebind `pd = ...` | 0 % |
| SyntaxError | **0.25 %** (1/400) |
| sans `answer =` (troncature) | **10 %** (40/400) |

Par phase :
- greedy : **87.5 %** `import pandas`
- samples : **78.1 %** `import pandas`

Par tâche : **75 / 80** tâches ont au moins un programme avec `import pandas as pd`.

### Question répondue

> « À quelle fréquence Qwen produit les patterns qui cassent nos wrappers ? »

**Réponse : massivement.** Malgré le prompt Stage3 « no imports », le modèle importe pandas **~4 fois sur 5**. Avec 4 samples, la probabilité qu’un lot many soit contaminé est énorme.

### Déduction

Le bug `UnboundLocalError` / scope `pd` n’est **pas** un détail rare : c’est le mode majoritaire des générations Tables. Ça explique pleinement pourquoi TEST1 (samples nested + `pd`) s’effondre, et pourquoi Stage3 (`exec` module-level) tient.

---

## 4. H5 — Niveau réel du fallback Stage3

Quand **toutes** les règles Tables sont bypassées (forced fallback) :

| Métrique Stage3 | Valeur |
|---|---:|
| Taux d’exécution (prog.) | 55.5 % |
| Greedy accuracy (tâches) | **50 %** |
| Oracle samples@4 | **73.75 %** |
| Oracle greedy∪samples | **82.5 %** |
| **Vote accuracy** | **78.75 %** (= 63/80) |

Familles (exec_rate / correct_rate programme-level Stage3) :

| type | exec_rate | correct_rate |
|---|---:|---:|
| table.filter | 0.81 | 0.55 |
| table.stat | 0.69 | 0.55 |
| table.derive | 0.45 | 0.36 |
| table.join | 0.43 | 0.31 |
| table.group | 0.40 | 0.29 |

### Question répondue

> « Le fallback Stage3 fait-il ~35/80 ou ~70/80 ? »

**Réponse : vote ≈ 63/80 (78.75 %), oracle upper bound ≈ 66/80 (82.5 %).**  
Ni catastrophique ni excellent. Le gisement pour battre 92.5 privé reste surtout les ~9 erreurs Stage3 **hors** ce holdout public + le chemin abstention→LLM, pas « encore des regex ».

### Nuance privée

En privé, Stage3 Tables = **88 %** avec règles + LLM. Ici on force 100 % LLM sur le public → 78.75 % vote. Cohérent : les règles absorbent les templates faciles ; le LLM porte le résiduel plus dur.

---

## 5. Équivalence exécuteur (cœur H2) — MEASURED sur corpus réel

Parmi les programmes où Stage3 renvoie une valeur finie (**222**/400) :

| Bras | Accord numérique vs Stage3 | Sur sous-ensemble `import_pandas` |
|---|---:|---:|
| **test1_alias_many (E2)** | **222/222 = 100 %** | **190/190 = 100 %** |
| test1_single | 100 % | 100 % |
| e4_importlib | 100 % | 100 % |
| test1_many (soumis) | **12/222 = 5.4 %** | **0/190 = 0 %** |
| test2_batch | 14.4 % | 0 % |

Quand Stage3 réussit et TEST1 many échoue : **210** cas → erreurs vides/`None` (échec d’exécution batch), pattern typique du wrapper cassé.

### Questions répondues

| Q | R |
|---|---|
| E2 est-il équivalent à Stage3 sur vrais codes Qwen ? | **Oui, 100 %** sur ce corpus (valeurs finies Stage3). |
| Le bug pandas explique-t-il TEST1 ? | **Oui** : 0 % d’accord sur les 190 programmes `import pandas`. |
| Faut-il E4 importlib pour soumettre ? | **Non** pour la fidélité numérique : E2 = E4 = Stage3. E4 reste oracle ; E2 reste le candidat `dsh` budget-friendly. |

### Gate ≥99 %

Sur ce replay Colab : **E2 PASS largement** (100 %).  
Le GO local `06` peut encore dire FAIL si `08_executor_agreement.py` n’a pas été rejoué sur le cache réel (il garde l’ancien smoke 0.9688). Les **chiffres Colab** sont la référence.

---

## 6. Ce que ça dit sur TEST1 / TEST2 privés

Rappel privé : Stage3 Tables **88** → TEST1 **80** → TEST2 **52**.

| Observation Colab | Lecture privée |
|---|---|
| vote Stage3 78.75 % vs test1_many **5 %** | Sur le chemin LLM Tables, TEST1 est **détruit** dès que les samples passent par `run_codes_many`. |
| test1_single = Stage3 | Le greedy TEST1 (module-level) est sain → baisse privée modérée (−8 Tables) = surtout **self-consistency samples**, pas tout le solve. |
| test1_alias = Stage3 | **Un seul fix E2** récupère le niveau Stage3 sur ce holdout forced-fallback. |
| test2_batch ~16 % vote | Batch + même collision pandas (et bras alias Colab non patché) → effondrement type TEST2. |

**Déduction forte :** la régression Stage3→TEST1 n’était **pas** un problème de règles ; c’était le contrat d’exécution samples. TEST2 a empiré en élargissant le wrapper cassé à greedy/repair + vote default 1.

---

## 7. Limites (honnêteté)

1. **Pas le protocole 8×40 s** — pas de contention multi-tâches ni budget Qwen+exec.
2. **`repair_gain` NOT RUN** — pas de 2ᵉ passe `DSH_NO_REPAIR`.
3. **`test2_batch_alias` Colab non fiable** — alias non injecté dans ce bras.
4. **H4 ordre batch** — pas rejoué sur ce cache Linux avec vrais codes lents.
5. **GitHub** n’héberge pas encore ces JSON (tu les as en local dans `resultats_proj/`).
6. Forced-fallback public ≠ distribution privée exacte.

---

## 8. Décision / suite

### Ce qui est maintenant **prouvé**

1. Qwen importe pandas **~80 %** du temps en Tables forced-fallback.  
2. Fallback Stage3 vote ≈ **78.75 %** sur 80 Tables publiques.  
3. **E2 (`test1_alias_many`) = Stage3** sur ce corpus (100 % accord).  
4. TEST1 many soumis = quasi mort (5 % vote).  

### Implication TEST3-recovery

La spec gelée reste valide et **beaucoup plus crédible** :

```text
Stage3 exact + seul changement E2 (__dsh_pd + isolation SyntaxError)
```

Tu as la preuve locale/Colab que ce delta restaure le chemin LLM Tables.

### GO formel

- Scientifiquement : **GO pour baker Stage3+E2** comme candidat recovery (pas encore pour « battre 92.5 »).  
- Checklist automatique `06` : à rafraîchir (rejouer 08/09/12 sur ce cache) ; H4 Linux + scanner restent ouverts.  
- **Ne pas** soumettre un bundle type TEST2.

### Prochaines actions recommandées

1. Copier `resultats_proj/*` → `projects/audit_independent/results/` (déjà fait pour json/replay).  
2. Rejouer localement `08`, `09`, `12`, `06` sur ce cache (timing long OK).  
3. Si tu confirmes : je **bake** l’agent `STAGE3_E2_RECOVERY` (Stage3 + exécuteur alias).  
4. Soumission privée seulement après scan + smoke ; prédire Tables ≈ proche Stage3 si samples étaient le leak principal.

---

## 9. Leçons

1. Le prompt « no imports » **ne suffit pas** — mesurer les sorties, pas les instructions.  
2. 180/180 déterministe masquait un fallback à ~79 % vote et un wrapper à 5 %.  
3. Une expérience Colab a plus d’information que trois soumissions à l’aveugle.  
4. E2 n’est plus une hypothèse : c’est une **équivalence mesurée** sur 80×5 programmes Qwen réels.
