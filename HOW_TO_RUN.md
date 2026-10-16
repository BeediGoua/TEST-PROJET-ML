# Utilisation progressive du pack

Le but est de ne pas tout lancer au hasard. On reproduit d'abord les faits connus, puis les échecs, puis les améliorations, et seulement à la fin le vrai LLM.

## Niveau 0 — Installation et intégrité

La plateforme cible Python 3.12. Le pack déterministe a également été testé dans l'environnement de construction actuel.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r projects/requirements_full.txt
python projects/scripts/check_setup.py
pytest -q
```


Pour un smoke test rapide des preuves principales :

```bash
python projects/scripts/run_all_fast.py
```

Les matrices métamorphiques/OOD exhaustives peuvent prendre plusieurs minutes selon la machine. Les scripts acceptent aussi `--mutation` et `--dataset` pour travailler progressivement.

Pour le vrai Qwen local, installer ensuite les dépendances lourdes :

```bash
pip install -r requirements_full.txt
```

## Niveau 1 — Reproduire le champion Stage 3

```bash
python projects/scripts/run_stage3_audit.py
```

Résultats attendus sur `dev.json` :

- No-files : 25/65 couvertes, 25/25 correctes ;
- Tables : 80/80, 80/80 ;
- Fits : 35/35, 35/35 ;
- total : **140/180 couvertes, 140/140 correctes parmi les couvertes**.

Ouvrir ensuite `notebooks/01_audit_stage3_and_limits.ipynb`.

## Niveau 2 — Rejouer l'échec du 100 % dev naïf

```bash
python projects/scripts/compare_agents.py --agent naive
python projects/scripts/run_metamorphic.py --agent naive
```

La candidate naïve atteint 180/180 sur le dev mais tombe à **26/65** avec un faux `2 + 2` explicitement sans rapport placé avant l'objectif. Le test montre qu'un dev parfait peut masquer un solveur trop dépendant des formulations.

Comparer à la candidate actuelle :

```bash
python projects/scripts/compare_agents.py --agent v10
python projects/scripts/run_metamorphic.py --agent v10 --mutation explicit_unrelated_pre
python projects/scripts/run_metamorphic.py --agent v10
```

v10 conserve 180/180 et 0 faux positif sur la suite métamorphique incluse.

## Niveau 3 — Rejouer la progression OOD

```bash
# Rejouer rapidement la rupture OOD4 puis le blind check OOD5
python projects/scripts/run_ood.py --agent v9 --dataset ood4
python projects/scripts/run_ood.py --agent v10 --dataset ood4
python projects/scripts/run_ood.py --agent v10 --dataset ood5

# Matrices complètes :
python projects/scripts/run_ood.py --agent v9
python projects/scripts/run_ood.py --agent v10
```

Les jeux ont des statuts différents :

- **OOD1** : développement, 80 tâches ; il a servi à écrire des règles et n'est donc plus un holdout. Son JSON est figé ; le générateur exact historique n'était plus disponible dans l'ancien dossier.
- **OOD2** : holdout de 120 tâches ; v10 couvre 20/120 et fait 20/20 sur ces 20.
- **OOD3** : créé après v8 ; il révèle 8 faux positifs IQR dans v8, puis v9 les corrige.
- **OOD4** : créé après v9 ; il cible des compositions `filtre + agrégat`. v9 produit 40 faux positifs. v10 transforme ces interceptions dangereuses en abstentions sûres.
- **OOD5** : créé après le patch v10 et **jamais utilisé pour régler v10**. v10 produit 0 faux positif mais s'abstient sur 48/48 : la capacité restante appartient au fallback LLM.

Vérifier que les benchmarks générés correspondent aux fichiers inclus :

```bash
python projects/benchmarks/ood_holdout/generate_ood2.py --check
python projects/benchmarks/ood_holdout/generate_ood3.py --check
python projects/benchmarks/ood_holdout/generate_ood4_compositions.py --check
python projects/benchmarks/ood_holdout/generate_ood5_blind.py --check
```

## Niveau 4 — Vérifier le contrat prompt ↔ runtime

```bash
python projects/scripts/run_tool_contract.py
```

La branche `safe_pre_v7` conserve trois incohérences documentées. v7/v8/v9/v10 en ont 0 selon cet audit statique. Stage 3 et la candidate naïve utilisent `exec(...)` historiquement et ne doivent pas être soumises telles quelles sous la règle actuelle.

## Niveau 5 — Runtime subprocess

Commencer petit :

```bash
python projects/scripts/run_runtime.py --fallback-count 1
```

Puis, si nécessaire :

```bash
python projects/scripts/run_runtime.py --fallback-count 2
python projects/scripts/run_runtime.py --fallback-count 4
python projects/scripts/run_runtime.py --fallback-count 8
```

Ou tout d'un coup :

```bash
python projects/scripts/run_runtime.py --all
```

Le fichier `results/generated/runtime_results.csv` contient les mesures de la machine de construction. Elles n'incluent **pas** la génération Qwen.

## Niveau 6 — Lire le notebook Champion → Challenger

Ouvrir :

```text
notebooks/02_champion_to_best_candidate.ipynb
```

Il raconte chronologiquement E00→E12 avec le format :

```text
question → hypothèse → test → résultat → interprétation → décision
```

et distingue systématiquement `MEASURED`, `INFERRED`, `HYPOTHESIS`, `UNKNOWN`.

## Niveau 7 — Régénération exhaustive des matrices locales

Les commandes `--all` recalculent toutes les anciennes candidates et sont plus lentes :

```bash
python projects/scripts/compare_agents.py --all
python projects/scripts/run_metamorphic.py --all
python projects/scripts/run_ood.py --all
```

Pour une vérification quotidienne, les appels ciblés `--agent v10` sont préférables.

## Niveau 8 — Vrai Qwen end-to-end

Le matériel officiel est dans `reference/official_ds_harness/`. Le runner accepte explicitement `--tasks`, donc aucun doublon de `dev.json` n'est nécessaire :

```bash
python projects/reference/official_ds_harness/localtest.py \
  agents/candidates/stage4_best_local_v10.py \
  --tasks data/public/dev.json \
  --test-run
```

Puis le run complet :

```bash
python projects/reference/official_ds_harness/localtest.py \
  agents/candidates/stage4_best_local_v10.py \
  --tasks data/public/dev.json \
  --out results/generated/full_qwen_v10.json
```

Cette étape nécessite les poids du modèle accessibles localement comme sur ML-Arena.

## Niveau 9 — Gate avant soumission privée

Ne soumettre v10 que si :

```text
DEV              PASS
METAMORPHIC      PASS
OOD              PASS
TOOL CONTRACT    PASS
RUNTIME          PASS
FULL QWEN        PASS
```

La soumission doit répondre à une hypothèse écrite. Tant qu'elle n'a pas été réellement scorée sur le privé, le seul champion privé du dépôt reste **Stage 3 = 92.5**.
