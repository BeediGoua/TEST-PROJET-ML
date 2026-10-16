# Audit indépendant DS-Harness — Stage3 / TEST1 / TEST2

Tu interviens comme **auditeur technique et chercheur indépendant** sur une compétition ML-Arena (DS-Harness). Ton objectif n'est pas de confirmer les conclusions de ChatGPT : **cherche activement à les réfuter** si le code ou les expériences indiquent une autre explication.

## Objectif

Nous voulons dépasser le champion historique **Stage3 = 92.5 = 111/120**, avec très peu de soumissions privées restantes. Une soumission ML-Arena doit donc correspondre à **une hypothèse forte, testée localement et falsifiable**.

Avant toute modification de `agent.py` :

1. audite les artefacts exacts ;
2. reconstruis les différences Stage3 → TEST1 → TEST2 ;
3. classe chaque conclusion comme **MEASURED / INFERRED / HYPOTHESIS** ;
4. cherche des contre-exemples ;
5. propose puis exécute des ablations à modification unique ;
6. construis un notebook expérimental reproductible ;
7. seulement ensuite propose un challenger.

## Artefacts fournis

- `STAGE3_SUBMITTED_92_5.py` — champion historique.
- `TEST1_SUBMITTED_86_7.py` — première reconstruction conforme de Stage3 via `dsh.run_python`.
- `TEST2_SUBMITTED_77_5.py` — gros candidat finalement soumis sous le nom TEST2 ; **ce n'est pas** le TEST2 minimal initialement prévu.
- `TEST2_MINIMAL_NOT_SUBMITTED.py` — ablation minimale de l'exécuteur qui n'a pas été soumise en privé.
- `V10_SUBMITTED_81_7.py` — autre point de comparaison privé utile.
- `dsh_official.py` — helper officiel.
- `dev.json` — 180 tâches publiques.

## Résultats privés observés

### Stage3

- No-files : 95.6% = 43/45.
- Tables : 88.0% = 44/50.
- Fits : 96.0% = 24/25.
- Total : 111/120 = 92.5.

Ces comptes viennent des sous-scores agrégés et des tailles de splits. Ils ne révèlent pas l'identité des tâches correctes.

### V10

- 98/120 = 81.7.
- No-files 88.9%, Tables 68.0%, Fits 96.0%.

### TEST1

- 104/120 = 86.7.
- No-files 88.9%.
- Tables 80.0%.
- Fits 96.0%.

### TEST2 large

- 93/120 = 77.5.
- No-files 95.6%.
- Tables 52.0%.
- Fits 96.0%.

**Règle de méthode impérative : des scores agrégés identiques ne prouvent PAS que les mêmes tâches sont réussies.** Par exemple, deux agents à 24/25 Fits peuvent échouer sur des tâches différentes. De même, 43/45 No-files dans deux versions ne prouve pas que les mêmes 43 sont correctes. Ne parle de “récupération de telle tâche” qu'avec une preuve tâche-par-tâche.

## Architecture Stage3 à auditer

Stage3 route les tâches en No-files / Tables / Fits, applique des solveurs déterministes, puis délègue au LLM si aucune règle ne répond.

Pour Tables, les règles historiques sont notamment :

- `table_stat_rule`
- `table_group_rule`
- `table_join_rule`
- `table_derive_rule`
- `table_filter_rule`

Sur le dev public, l'audit précédent indiquait :

- No-files déterministe : 25/65
- Tables déterministe : 80/80
- Fits déterministe : 35/35
- total déterministe : 140/180, 0 erreur sur ces 140

**Reproduis ces chiffres au lieu de les accepter.**

Le point critique : si les 80 Tables publiques sont absorbées par les règles, le dev public ne mesure presque pas le fallback LLM Tables. Or le privé contient d'autres tirages et quelques types Tables absents du dev. Il faut donc construire un benchmark **forced fallback**.

## Différence d'exécution Stage3 vs versions conformes

Stage3 historique exécutait le code généré par le LLM directement dans le processus via `exec(code, ns)` avec un environnement riche : `SmartFrame`, `fake_read_csv`, helpers de nettoyage, sklearn wrappers, `LAST_ERR`, `LAST_STATE`, etc.

Les soumissions actuelles doivent utiliser `dsh.run_python`, donc un subprocess avec sérialisation / reconstruction de l'état.

Hypothèse à tester, pas à présumer :

> une partie de la régression Stage3 → TEST1 vient d'une non-équivalence sémantique ou temporelle entre l'exécuteur historique et l'exécuteur conforme.

Le bon protocole est de **cacher les générations Qwen** puis d'exécuter exactement le même programme avec :

A. ancien exécuteur Stage3 ;
B. `dsh.run_python` individuel ;
C. exécuteur batch conforme.

Mesurer : valeur, exception, timeout, runtime, état DataFrame, comportement SmartFrame, `read_csv`, dtypes, mutation inter-samples.

## TEST1

TEST1 visait principalement la reproduction conforme de Stage3. Il conserve le même modèle principal (`Qwen/Qwen2.5-Coder-1.5B-Instruct`), les prompts/règles historiques et le vote, mais remplace l'exécution directe par `dsh.run_python` et introduit de la logique de batching pour amortir le coût du subprocess.

Des bugs de cette classe ont déjà été reproduits dans des prototypes :

- contamination d'un sample par mutation d'un DataFrame partagé ;
- perte d'identifiants à zéros initiaux lors de certains round-trips ;
- perte de comportements SmartFrame / alias ;
- perte de diagnostics `LAST_STATE` ;
- un timeout collectif pouvant faire perdre plusieurs samples valides à cause d'un seul sample bloqué.

**Vérifie lesquels existent réellement dans l'artefact exact TEST1.** Ne reporte pas automatiquement les bugs d'une version intermédiaire sur TEST1 sans reproduction.

## TEST2 large

Le fichier réellement soumis comme TEST2 a beaucoup plus de changements que le TEST2 minimal initialement envisagé. Il ajoute notamment des solveurs Tables supplémentaires comme `table_extended_rule` et `table_extra_safe2`, modifie certaines règles historiques et change l'orchestration/exécution.

Dans cette version, lorsqu'une nouvelle règle renvoie une valeur, elle peut être injectée comme candidat de poids 100 avec `ok=False`, ce qui court-circuite le LLM.

Hypothèse à tester :

> une partie importante de l'effondrement Tables de TEST2 provient de faux positifs déterministes ou de changements de couverture/routage qui envoient certaines tâches vers un fallback moins performant.

Mais **52% Tables ne prouve pas à lui seul que les nouvelles règles sont responsables**. Il faut faire des ablations exactes : même exécuteur, même modèle, même prompt, retirer seulement les extensions ; puis inversement garder les extensions en shadow mode.

## Expériences prioritaires

### E1 — Diff exact des artefacts

Produis un diff sémantique fonction par fonction :

- constantes / modèles / budget / timeout ;
- preprocessing ;
- route ;
- solveurs déterministes ;
- prompts ;
- génération ;
- exécution ;
- repair ;
- sampling ;
- vote ;
- fallback final.

Pour chaque différence, indique son effet attendu et si elle est couverte par un test.

### E2 — Reproduction du dev

Pour chaque artefact :

- score déterministe ;
- coverage par famille ;
- precision conditionnelle ;
- tâches qui changent de route/règle ;
- erreurs exactes.

### E3 — Forced fallback sur les 80 Tables publiques

Désactive les solveurs Tables uniquement pour l'expérience et force le LLM.

Enregistre tâche par tâche :

- prompt ;
- greedy code ;
- greedy executable/correct ;
- repair ;
- samples ;
- réponse finale ;
- runtime ;
- type de Table.

Mesure au minimum : `accuracy`, `execution_rate`, `oracle@k`, `final_vs_oracle_gap`, `repair_gain`, runtime p50/p95/max.

### E4 — Cache des générations

Sauvegarde les programmes générés. Toutes les comparaisons d'exécuteurs et de vote doivent réutiliser les mêmes générations.

### E5 — Executor A/B/C

Comparer l'ancien exécuteur, `dsh.run_python` individuel et batch conforme sur les mêmes programmes. Chercher des divergences minimales et reproductibles.

### E6 — Oracle@k et vote

Si `oracle@4 >> final_accuracy`, le gisement est le vote / selector. Si `oracle@4` est proche de l'accuracy finale, le problème est plutôt modèle / prompt / contexte.

### E7 — Repair

Mesurer le gain net du repair et son coût en secondes. Calculer le nombre de réponses correctes récupérées par seconde consommée.

### E8 — Modèle

Comparer au moins :

- Qwen2.5-Coder-1.5B
- Qwen3-1.7B

avec **même prompt, même exécuteur, même sampling, même vote et mêmes tâches**. Ne modifier qu'une variable à la fois.

### E9 — Shadow mode des nouvelles règles

Les nouvelles règles Tables ne doivent pas immédiatement écraser le LLM. Fais-les produire une proposition parallèle et compare au gold public / au fallback :

- rule right / LLM right
- rule right / LLM wrong
- rule wrong / LLM right
- both wrong

Promouvoir une règle seulement si elle améliore le système end-to-end, pas simplement si sa précision isolée est élevée.

### E10 — No-files et Fits

- No-files : analyser séparément les extensions qui ont changé la couverture ; ne pas supposer que 95.6% privé correspond aux mêmes succès que Stage3.
- Fits : ne pas conclure “stable” tâche-par-tâche depuis trois scores à 96%. Reproduire au moins les 35 tâches publiques et identifier les chemins exacts. Tant qu'aucun gain clair n'est mesuré, geler la logique Fits en production.

## Notebook attendu

Construis un notebook unique, lisible et rejouable, par exemple :

1. Setup / versions / hashes
2. Load artefacts
3. Public dev reproduction
4. Routing/coverage map
5. Forced fallback Tables
6. Cache generations
7. Executor equivalence
8. Coder vs Qwen3
9. Greedy / samples / oracle@k
10. Repair ablation
11. Prompt ablations
12. Shadow rules
13. No-files
14. Robustness / metamorphic
15. Candidate construction
16. GO / NO-GO report

Chaque expérience doit avoir : hypothèse, modification unique, métrique, résultat, conclusion, niveau de preuve.

## Règle de décision avant soumission privée

Avant toute nouvelle soumission, produis un rapport :

- baseline exacte ;
- modification exacte ;
- hypothèse ;
- résultats locaux ;
- forced-fallback accuracy ;
- oracle@k ;
- exec failure rate ;
- runtime ;
- risques ;
- score privé attendu + intervalle ;
- résultat qui falsifierait l'hypothèse.

Pas de soumission juste parce que `dev=180/180` ou des stress tests synthétiques passent.

## Attitude attendue

- Ne protège pas l'analyse précédente.
- Cherche les erreurs de raisonnement et les confusions de causalité.
- Ne déduis jamais l'identité des tâches correctes depuis des métriques agrégées.
- Ne confonds pas tests de régression synthétiques et estimation de généralisation privée.
- Si une hypothèse alternative explique mieux les résultats, démontre-la.
- Priorité : **meilleur score privé avec un minimum de soumissions**, pas élégance du code.

Commence par me rendre :

1. un tableau de provenance/hashes des artefacts ;
2. un diff Stage3 / TEST1 / TEST2 ;
3. les points de l'analyse précédente que tu confirmes, réfutes ou juges non prouvés ;
4. les 5 expériences locales à plus forte valeur d'information ;
5. seulement ensuite le notebook.
