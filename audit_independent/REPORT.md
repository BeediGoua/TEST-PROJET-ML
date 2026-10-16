# Audit indépendant — premier rapport expérimental

Les agents de référence n'ont pas été modifiés. Aucune soumission privée effectuée.

## Conclusion principale

**MEASURED : un défaut de portée Python casse les programmes qui importent pandas dans les exécuteurs groupés.** Ce défaut existe dans les samples TEST1 et TEST2 minimal ; TEST2 large l'expose aussi au greedy, aux continuations et au repair. Il fournit une explication alternative concrète à l'effondrement Tables. Sa contribution au score privé reste **HYPOTHESIS**, faute de générations et de résultats privés par tâche.

## 1. Provenance

Les sept tailles et SHA-256 annoncés (cinq agents, helper, dev) correspondent exactement aux octets du package local. Voir `results/manifest.csv` pour les empreintes complètes. Cela authentifie le package reçu, pas son identité avec un téléchargement ML-Arena indépendant.

| Artefact | Octets | SHA-256 (préfixe) | Provenance externe |
|---|---:|---|---|
| Stage3 | 130431 | 00bfd0d2ef05 | déclaré exact par la passation |
| V10 | 152153 | 0f5491050434 | déclaré soumis, 81.7 |
| TEST1 | 147257 | a83da219d907 | identification forte ; téléchargement original absent |
| TEST2 large | 200878 | aa3a2fd0af57 | identité après normalisation déclarée, non revérifiée contre ML-Arena |
| TEST2 minimal | 148416 | 71ff3b5cdde4 | non soumis |
| dsh officiel | 15301 | 391b22c491c2 | helper fourni |
| dev.json | 923286 | 7e06aeeafa08 | 180 tâches |

Les scores privés sont des observations **rapportées par l'utilisateur**, pas de nouvelles mesures de cet audit. Aucun appariement des erreurs privées n'est possible.

## 2. Diff sémantique

Inventaire AST : `results/semantic_changes.csv`. Les quatre fichiers `.diff` détaillent les corps des fonctions et les constantes ; ils sont destinés à la lecture, pas à être appliqués comme patches. L'AST ignore les seuls changements de commentaires/formatage. Les imports ne sont pas inclus dans cet inventaire de symboles ; les ajouts de dépendances de sérialisation sont visibles dans les sources.

| Composant | Stage3 → TEST1 | TEST1 → TEST2 large |
|---|---|---|
| Modèle, MAX_NEW, NSAMP | identiques | identiques |
| Budget | 29 s inchangé | **34 s**, donc marge réduite à 6 s |
| Exécution | exec local → enfant dsh ; timeout 1.5 → 5 s | batch partagé entre tâches ; timeout programme 1.5 s |
| Prétraitement, routage, prompts initiaux | AST identique | AST identique |
| Règles historiques | AST identique | garde-fous ajoutés à stat/filter ; group/join/derive/fit identiques |
| Nouvelles règles | aucune | calc_safe_v2, table_extended_rule, table_extra_safe2 |
| Orchestration | samples regroupés par tâche | greedy, continuation, repair et samples regroupés entre tâches |
| Vote | fonction identique | fonction identique, mais zéros rejetés et défaut final 1 au lieu de 0 |

TEST2 minimal ajoute des alarmes individuelles mais ne corrige pas l'import pandas ni l'erreur de syntaxe collective. Il n'est donc pas un contrôle « executor fidèle » déjà acquis.

## 3. Reproduction publique

**MEASURED**, via le véritable `Agent.solve()` avec génération remplacée par un témoin vide ; aucun modèle chargé. Une demande de génération marque une abstention. Tests tâche par tâche, sans prétention de mesure temporelle en lots de huit.

| Agent | No-files correct/couvert | Tables correct/couvert | Fits correct/couvert |
|---|---:|---:|---:|
| Stage3 | 25/25 sur 65 | 80/80 | 35/35 |
| TEST1 | 25/25 sur 65 | 80/80 | 35/35 |
| TEST2 minimal | 25/25 sur 65 | 80/80 | 35/35 |
| TEST2 large | 65/65 | 80/80 | 35/35 |
| V10 | 65/65 | 80/80 | 35/35 |

Le précédent évaluateur `src/evaluation/core.py` omet calc_safe_v2 et table_extra_safe2, n'applique pas tous les rejets de zéro et ne mesure pas l'arrondi final de solve. **MEASURED : il sous-estime la couverture No-files de TEST2 de 40 tâches.** Sur ces 80 Tables publiques, cela ne change pas la couverture : l'écart d'évaluateur n'explique donc pas ici la chute privée Tables.

## 4. Contre-exemples d'exécuteur

Corpus explicite de programmes écrits pour tester le contrat, **pas des générations Qwen**. Même DataFrame x=[2,4], même code dans chaque bras.

```python
import pandas as pd
answer = float(dfs['data']['x'].sum())
```

**MEASURED** : Stage3 renvoie 6 ; TEST1/miminal en mode samples renvoient None ; TEST2 batch renvoie `UnboundLocalError: cannot access local variable 'pd' where it is not associated with a value`.

Cause : les wrappers exécutent `pd.read_csv` avant le corps généré. Mais l'import dans ce corps rend `pd` local à toute la fonction. L'accès préliminaire échoue avant le `try` interne. TEST1 perd alors tout le groupe ; TEST2 capture l'erreur par programme. `import numpy as np` ne provoque pas ce défaut dans le contrôle testé.

Conséquence **INFERRED** : TEST2 peut demander au modèle de réparer un programme parfaitement correct ; réimporter pandas ne résout pas une erreur créée par le wrapper. Une fréquence plus élevée d'imports pandas en Tables pourrait produire une régression sélective Tables, même si les règles étaient parfaites. Fréquence réelle et impact privé : **non mesurés**.

**Ablation supplémentaire MEASURED dans le vrai solve**, règles Tables désactivées et génération remplacée par ce même programme fixe :

| Agent | Réponse finale | Correct |
|---|---:|---|
| Stage3 | 6 | oui |
| TEST1 | 6 | oui (greedy individuel préservé) |
| TEST2 minimal | 6 | oui |
| TEST2 large original | 1 | non (défaut final) |
| TEST2 large, seul alias du wrapper corrigé | 6 | oui |

Le corps généré reste inchangé. Seules les références pandas du wrapper sont renommées en `__dsh_pd` dans le code enfant de l'expérience. Les budgets sont relâchés uniformément pour éviter de confondre sémantique et lenteur de démarrage Windows. Voir `results/wrapper_ablation.csv`. Ce n'est pas un test de score sous 40 secondes.

Deuxième contre-exemple : `[answer=6, answer=(, answer=42, answer=9]`.

- TEST1 et minimal : `[None,None,None,None]`.
- TEST2 large : `[6,None,42,9]`.

**MEASURED** : une SyntaxError contamine tout le fichier concaténé avant exécution dans TEST1/minimal. Ajouter des timeouts ne la corrige pas. TEST2 effectue une vérification syntaxique par programme et conserve les réponses valides. Le défaut ne concerne donc pas seulement les boucles infinies envisagées dans la passation.

Limite des tests : Windows, transport `dsh_compat`, alarmes POSIX remplacées par des opérations vides uniquement pour ces programmes finis. Les résultats démontrent la portée des variables et la compilation ; **ils ne valident ni les délais Linux, ni les limites mémoire, ni l'isolation contre un programme bloqué**. Le helper officiel utilise preexec_fn/RLIMIT_AS et ne fonctionne pas tel quel sous Windows.

## 5. Ce qui est confirmé, réfuté ou non établi

- **Confirmé** : les 80 Tables publiques masquent entièrement le fallback ; TEST1 préserve les règles et prompts de Stage3 ; TEST2 est une modification multiple.
- **Réfuté** : considérer TEST2 minimal comme une correction suffisante du batch ; traiter l'ancien évaluateur comme fidèle à tous les agents ; penser que seul un timeout peut faire perdre un groupe de samples.
- **Non établi** : les nouvelles règles expliqueraient la majorité des 14 bonnes réponses nettes perdues en Tables ; Qwen3 serait meilleur ; le vote serait la faiblesse principale ; les mêmes Fits échoueraient.
- **À nuancer** : un grand écart oracle/final est un potentiel de sélection, pas la preuve qu'un sélecteur réalisable saura reconnaître la bonne réponse sans le gold.
- **À corriger dans le protocole** : une ablation de prompt doit régénérer le code ; fixer les générations convient aux exécuteurs et au vote, pas à mesurer un effet du prompt.

## 6. Cinq expériences prioritaires

| Rang | Expérience à changement unique | Impact plausible | Probabilité / preuve | Coût | Risque |
|---|---|---|---|---|---|
| 1 | Replay d'un code fixe avec/sans collision pd ; vrai solve forced fallback | élevé pour Tables | défaut confirmé ; effet privé inconnu | faible, CPU | faible, uniquement copie expérimentale |
| 2 | Corpus Qwen caché : Stage3 / individuel / batch ; stratifier par imports et syntaxe | élevé | divergences déjà prouvées sur témoins | moyen, GPU pour cache initial | faible hors soumission |
| 3 | TEST2 : extensions on/off puis garde-fous historiques on/off séparément ; mêmes générations lorsque même prompt | élevé | responsabilité des règles non démontrée | moyen | ne pas combiner les deux ablations |
| 4 | Lots mixtes de 8, ordre permuté, 1/4/8 fallbacks, Linux 40 s et limites mémoire | élevé | contention déduite du code | GPU/Linux requis | résultats Windows non transposables |
| 5 | Après stabilisation : Coder/Qwen3, repair on/off, vote sur cache, essais séparés | potentiel inconnu | hypothèses | élevé | sélection sur dev suradaptée |

La règle de routage ne doit pas seulement comparer deux probabilités de réussite par tâche : le coût d'un fallback réduit aussi le temps disponible pour les sept autres tâches. Il faut mesurer l'effet sur le lot complet.

Autre risque temporel **INFERRED** : dans TEST2, `__BATCH_END` démarre après les imports ; le timeout extérieur commence avant. La réserve fixe d'une seconde n'est pas une garantie que les résultats partiels seront sérialisés avant que le parent tue l'enfant. À tester sous Linux, sans conclure depuis le shim.

## 7. Environnement et décision

Python 3.12.13, torch 2.14.1+cpu, CUDA indisponible. Cache Hugging Face : seul MiniLM repéré, aucun Qwen. L'énumération WSL renvoie accès refusé. Aucune mesure de forced-fallback Qwen, oracle@4, repair gain ou p95 GPU n'est disponible à ce stade.

**NO-GO pour une nouvelle soumission privée.** Proposition de prochain contrôle : Stage3 + exécution individuelle conforme, puis batch seulement après validation du contrat, avant toute extension de règles. Le correctif de collision pd est une ablation expérimentale, pas un nouveau champion validé.

Un score privé attendu et un intervalle ne seraient pas justifiables avec ces données ; ils restent non estimés. L'hypothèse « collision pd responsable d'une part importante » serait affaiblie si les générations privées représentatives importaient rarement pandas, ou si sa correction n'améliorait pas le replay et les lots limités en temps.

## Reproduction

Depuis la racine du workspace, utiliser `.venv/Scripts/python.exe projects/audit_independent/audit.py`, puis `probes.py` et `ablation.py`. Les CSV conservent les résultats par tâche et les erreurs. Le notebook unique de ce dossier réunit le rapport, les expériences CPU et le protocole GPU ; il signale explicitement les expériences non exécutées.
