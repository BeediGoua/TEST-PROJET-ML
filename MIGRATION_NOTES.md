# Ménage effectué depuis `projects.zip`

## Conservé

- `dev.json` public ;
- kit officiel (`dsh.py`, `scoring.py`, `localtest.py`, `schema.md`, `env.py`, etc.) ;
- Stage 1 / Stage 2 officiels comme baselines ;
- notebook officiel du cours ;
- notes historiques, déplacées sous `archive/original_notes/` ;
- champion Stage 3 utilisé dans les audits ;
- candidates et résultats expérimentaux utiles.

## Supprimé du flux principal

- `.git/` imbriqué ;
- `__pycache__/`, `.pytest_cache/` et fichiers temporaires ;
- doublon `ds-harness/dev.json` ;
- ancien `ds-harness/agent.py`, qui était **strictement identique à `stage1_direct.py`** et pouvait être confondu avec le champion 92.5 ;
- rapports redondants dans le dossier principal.

Les anciens rapports restent archivés pour conserver l'historique, mais leur contenu utile a été consolidé dans `README.md`, `RESULTS_SUMMARY.md`, `EXPERIMENT_LOG.md`, `LIMITATIONS_AND_NEXT_STEPS.md` et `HOW_TO_RUN.md`.

## Améliorations ajoutées pendant le ménage

- protocole d'évaluation partagé dans `src/evaluation/` ;
- tests de non-régression ;
- OOD4 compositions, créé après v9 ;
- candidate v10, qui transforme une classe de faux positifs compositionnels en abstentions ;
- OOD5 blind final, créé après v10 et non utilisé pour le régler ;
- séparation `requirements.txt` / `requirements_full.txt` ;
- manifeste SHA256 ;
- notebooks réécrits et exécutés depuis la racine du dépôt.
