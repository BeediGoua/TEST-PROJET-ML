# Rapport de validation du pack

Ce fichier résume les vérifications effectuées avant création du ZIP final.

## Structure / installation

- `python scripts/check_setup.py` : **PASS**
- `dev.json` : 180 tâches = 65 No-files + 80 Tables + 35 Fits
- compilation de tous les fichiers Python du dépôt : **43 fichiers compilés, 0 erreur** au moment de la validation
- CLI du `localtest.py` officiel : **PASS** (`--tasks`, `--test-run`, `--type`, `--out`, `--timeout` disponibles)

## Tests automatisés

`pytest -q` : **15 tests passés / 15**.

Ces tests couvrent notamment :

- audit Stage 3 140/180, 140/140 correctes parmi les couvertes ;
- échec reproductible de la candidate naïve sur distracteur ;
- limite v7 reproductible ;
- OOD3 : 8 faux positifs v8 ;
- OOD4 : 40 faux positifs v9 ;
- correction sélective v10 sur OOD4 ;
- OOD5 blind : 30 faux positifs v9, 0 faux positif v10 ;
- contrat prompt/runtime v10 ;
- subprocess sécurisé v10.

## Générateurs de benchmarks

OOD1 est conservé comme benchmark de développement figé. Son générateur historique exact n’était plus disponible dans les fichiers récupérés ; le pack ne prétend donc pas le régénérer.

Les contrôles byte-for-byte ont réussi pour les benchmarks générés et versionnés :

- OOD2 : **120 tâches — CHECK OK**
- OOD3 : **80 tâches — CHECK OK**
- OOD4 : **64 tâches — CHECK OK**
- OOD5 : **48 tâches — CHECK OK**

## Notebooks

Les deux notebooks ont été exécutés de bout en bout avec `nbconvert` après la mise à jour finale :

- `01_audit_stage3_and_limits.ipynb` : **PASS**
- `02_champion_to_best_candidate.ipynb` : **PASS**

Les sorties exécutées sont conservées dans les notebooks inclus dans le ZIP.

## Résultats clés reproduits

- Stage 3 dev déterministe : **140/180 couvertes, 140/140 correctes**
- v10 dev déterministe : **180/180**
- v10 suite métamorphique incluse : **0 faux positif**
- v10 OOD1 : **80/80**
- v10 OOD2 : **20/20 parmi 20 couvertes**
- v10 OOD3 : **72/72 parmi 72 couvertes**
- v9 OOD4 : **40 faux positifs** ; v10 OOD4 : **8/8 parmi 8 couvertes, 0 faux positif**
- v9 OOD5 : **30 faux positifs** ; v10 OOD5 blind : **0 couverte, 0 faux positif**
- v10 tool contract : **0 mismatch détecté, pas de `exec(...)`**


## Smoke test rapide

`python scripts/run_all_fast.py` : **PASS** sur la machine de construction (~28 s lors de la validation finale). Il rejoue les preuves clés sans recalculer toutes les matrices historiques : Stage 3, v10 dev, distracteur No-files naïf/v10, rupture OOD4 v9/v10, blind OOD5 v10 et contrat prompt/runtime. Le temps dépend de la machine.

## Runtime v10 mesuré sur la machine de construction

Sous-système `run_codes_many`, sans génération Qwen :

- 1 fallback : ~2.18 s
- 2 fallbacks : ~3.43 s
- 4 fallbacks : ~7.04 s
- 8 fallbacks : ~14.47 s

Ces temps sont dépendants de la machine.

## Ce qui n'a PAS été validé

Deux validations nécessitent un environnement externe qui n'est pas présent ici :

1. **Full Qwen end-to-end** avec les vrais poids montés comme sur ML-Arena ;
2. **nouveau score privé ML-Arena** pour v10.

Donc le dépôt ne prétend pas que v10 vaut 100 sur le privé. Le seul champion privé validé reste **Stage 3 = 92.5**. Le statut de v10 est : **READY FOR FULL QWEN TEST-RUN**.
