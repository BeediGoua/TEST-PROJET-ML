# Benchmarks supplémentaires

Ces jeux ne prétendent pas reproduire le privé ML-Arena. Leur but est de tester la généralisation et surtout le risque de **faux positifs déterministes**.

- `ood_development/ood1_tables.json` — 80 tâches, 10 familles. Utilisé pendant le développement : **pas un holdout**. Le JSON est figé et versionné ; le générateur exact historique n'était plus présent dans l'ancien dossier, donc le pack ne prétend pas pouvoir le régénérer byte-for-byte.
- `ood_holdout/ood2_tables.json` — 120 tâches, 12 familles. Premier holdout de sélectivité.
- `ood_holdout/ood3_fresh_paraphrase.json` — créé après v8 ; a révélé 8 faux positifs IQR, utilisés ensuite pour construire v9.
- `ood_holdout/ood4_composition_redteam.json` — créé après v9 ; 64 tâches `filtre + agrégat`. Il a révélé 40 faux positifs chez v9 et a servi à construire les garde-fous de v10.
- `ood_holdout/ood5_blind_final.json` — créé **après le patch v10** avec de nouvelles formulations. Il n'a pas servi à modifier v10. v10 s'y abstient sur 48/48 avec 0 faux positif.
- `metamorphic/` — transformations censées conserver exactement la réponse : distracteurs explicitement inutiles, colonne inutile, permutation des lignes d'entraînement, casse/espacement.

## Reproductibilité

```bash
python benchmarks/ood_holdout/generate_ood2.py --check
python benchmarks/ood_holdout/generate_ood3.py --check
python benchmarks/ood_holdout/generate_ood4_compositions.py --check
python benchmarks/ood_holdout/generate_ood5_blind.py --check
```

Les générateurs OOD2→OOD5 sont déterministes avec un seed fixé et doivent reproduire les JSON inclus. OOD1 est volontairement conservé comme benchmark de développement figé : son générateur historique exact n'était pas disponible dans les fichiers récupérés.
