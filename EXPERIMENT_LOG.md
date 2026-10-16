# Journal des expériences

| ID | Question / hypothèse | Résultat principal | Décision |
|---|---|---|---|
| E00 | Que fait réellement Stage 3 sans LLM ? | 140/180 couvertes, 140/140 correctes sur dev | Champion conservé |
| E01 | Peut-on rendre les 40 No-files restantes déterministes ? | candidate naïve : 65/65 No-files, donc 180/180 dev | Challenger |
| E02 | Ce 180/180 résiste-t-il à un distracteur sans effet ? | faux `2+2` avant : 26/65, 39 faux positifs | **REJECT naïve** |
| E03 | Peut-on garder la couverture avec une logique plus sélective ? | v7 conserve 180/180 et corrige les distracteurs initiaux | Continuer |
| E04 | Peut-on couvrir des opérations Tables nouvelles ? | OOD1 : v7+ 80/80 | Benchmark de développement, pas holdout |
| E05 | La précision sélective tient-elle sur OOD2 ? | 20/120 couvertes, 20/20 correctes, 0 faux positif | Bonne sélectivité |
| E06 | Prompt et runtime promettent-ils les mêmes outils ? | pré-v7 : 3 mismatches ; v7+ : 0 | v7+ préférable |
| E07 | Peut-on encore casser v7 avec de nouvelles formulations ? | `independent...` : 63/65 ; parenthèse unrelated : 0/65 couvertes | Limite trouvée |
| E08 | Patch minimal sans régression ? | v8 : 180/180 dev, stress connus propres, OOD1/OOD2 propres | v8 challenger |
| E09 | Un jeu créé après v8 révèle-t-il encore un faux positif ? | OOD3 : v8 = 8 faux positifs IQR ; v9 = 0 | v9 challenger |
| E10 | v9 gère-t-elle les compositions filtre + agrégat ? | OOD4 : 48 couvertes, seulement 8 correctes, **40 faux positifs** | Nouvelle classe de défauts |
| E11 | Un garde-fou de composition peut-il éviter ces erreurs sans régression ? | v10 : 180/180 dev, OOD1 80/80, OOD2 20/20, OOD3 72/72, OOD4 8/8 avec 56 abstentions | **v10 = meilleure candidate locale** |
| E12 | Un jeu blind créé après v10 reproduit-il le défaut ? | OOD5 : v9 = 30/30 couvertes fausses ; v10 = 0/48 couvertes, **0 faux positif** | v10 reste sélective ; fallback devient priorité |

Le score privé reste **92.5** tant que v10 n'a pas été validée end-to-end puis sur ML-Arena.
