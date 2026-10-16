# Résultats de référence

## 1. Privé : seul résultat réellement validé

Stage 3 : **92.5/100**, avec No-files **95.6**, Tables **88.0**, Fits **96.0**, 120/120 réponses et 0 erreur de format. Le total implique **111/120** bonnes réponses. Les comptes 43/45, 44/50 et 24/25 sont **inférés** des tailles de familles et des pourcentages affichés ; les identifiants privés erronés restent inconnus.

## 2. Dev déterministe

| Agent | Couvertes | Correctes | Faux positifs | No-files | Tables | Fits |
|---|---:|---:|---:|---:|---:|---:|
| Stage 3 | 140/180 | 140 | 0 | 25/65 | 80/80 | 35/35 |
| Stage 4 naïve | 180/180 | 180 | 0 | 65/65 | 80/80 | 35/35 |
| v7 | 180/180 | 180 | 0 | 65/65 | 80/80 | 35/35 |
| v8 | 180/180 | 180 | 0 | 65/65 | 80/80 | 35/35 |
| v9 | 180/180 | 180 | 0 | 65/65 | 80/80 | 35/35 |
| **v10** | **180/180** | **180** | **0** | **65/65** | **80/80** | **35/35** |

Le 180/180 ne suffit pas : la robustesse est évaluée séparément.

## 3. Métamorphique

La candidate naïve avec un faux `2 + 2` sans rapport :

- distracteur avant l'objectif : **26/65** ;
- distracteur après l'objectif : **29/65**.

v7 corrige ces cas mais échoue encore sur `This example is independent of the question` : **63/65**, et s'abstient totalement sur une parenthèse `Unrelated example`.

v8/v9/v10 passent toutes les transformations incluses avec **0 faux positif**.

## 4. OOD — chronologie réelle

| Jeu | Statut | v9 | v10 | Leçon |
|---|---|---|---|---|
| OOD1 (80) | développement | 80/80 | 80/80 | régression utile, pas holdout |
| OOD2 (120) | holdout | 20/20 parmi 20 couvertes | 20/20 parmi 20 | bonne sélectivité, 100 abstentions |
| OOD3 (80) | après v8 | 72/72 parmi 72 | 72/72 parmi 72 | v8 avait 8 faux positifs IQR |
| OOD4 (64) | après v9, utilisé pour v10 | 48 couvertes, 8 correctes, **40 fausses** | 8/8, 56 abstentions | filtres composés ignorés par certaines règles |
| OOD5 (48) | **blind après v10** | 30 couvertes, **30 fausses** | **0 couverte, 0 fausse** | v10 est sélective, mais le fallback doit prendre tout le résiduel |

OOD4 a révélé une classe de défauts plus générale que l'IQR : une règle spécialisée reconnaissait l'opération mais ignorait parfois une clause de sous-ensemble supplémentaire. v10 ajoute des garde-fous conservateurs. OOD5 n'a pas servi à modifier v10 et confirme qu'elle ne répète plus ces faux positifs sur de nouvelles formulations, au prix d'une abstention complète.

## 5. Prompt/runtime et conformité

- Stage 3 / candidate naïve : `exec(...)` historique et 3 incohérences prompt/runtime détectées.
- `safe_pre_v7` : pas de `exec`, mais encore 3 incohérences.
- v7/v8/v9/**v10** : **0 incohérence détectée**, pas de `exec(...)` selon l'audit statique.

## 6. Runtime subprocess v10

Mesure locale du sous-système sécurisé `run_codes_many`, **sans génération Qwen** :

| Nombre de tâches fallback | Temps mesuré |
|---:|---:|
| 1 | ~2.18 s |
| 2 | ~3.43 s |
| 4 | ~7.04 s |
| 8 | ~14.47 s |

Ces nombres sont dépendants de la machine et doivent être régénérés avec `python scripts/run_runtime.py --all`.

## 7. Verdict

- **Champion privé réel : Stage 3 = 92.5.**
- **Meilleure candidate locale actuelle : v10.**
- **Statut : READY FOR FULL QWEN TEST-RUN.**

La prochaine information décisive n'est plus un autre 180/180 déterministe : c'est la qualité du fallback Qwen sur les abstentions OOD, en particulier les compositions `filter + aggregate`.
