# TEST-PROJET-ML (`projects`)

Pack DS-Harness pour audit local + expérience Colab GPU (forced-fallback Qwen).

## Colab (forced-fallback 80 Tables)

1. Runtime → GPU T4  
2. Ouvrir `audit_independent/colab_forced_fallback.ipynb` depuis ce repo  
3. Régler :

```python
PROJECT_ROOT = Path('/content/TEST-PROJET-ML')  # racine de ce dépôt (= dossier projects)
```

Si tu clones dans `/content/TEST-PROJET-ML`, la racine **est** déjà le contenu de `projects/` (CODEX_AUDIT_HANDOFF, audit_independent, src au même niveau).

---

# DS-Harness — pack expérimental reproductible

Ce dépôt est la version **nettoyée, testée et reproductible** du projet DS-Harness. Il sépare clairement le matériel officiel, le champion privé réellement observé, les candidates expérimentales, les benchmarks de robustesse et les résultats régénérables.

## Les deux nombres à ne jamais confondre

- **Champion privé réellement validé sur ML-Arena : Stage 3 = 92.5/100.**
- **Meilleure candidate locale actuelle : v10 = 180/180 sur le dev déterministe.**

`180/180` local ne signifie **pas** `100/100` sur le privé. v10 n'a pas encore été validée end-to-end avec le vrai Qwen ni sur le leaderboard privé.

## Ce que ce dépôt démontre

1. Stage 3 couvre déterministiquement **140/180** tâches publiques et fait **140/140** sur celles qu'il intercepte.
2. Une première extension No-files atteint **180/180**, mais casse sévèrement sous distracteurs : jusqu'à **26/65** sur un test pourtant sémantiquement équivalent.
3. Les candidates suivantes deviennent plus sélectives : on préfère **s'abstenir** plutôt que produire une réponse déterministe fausse.
4. Un nouveau benchmark OOD3 créé après v8 révèle encore **8 faux positifs IQR**, corrigés par v9.
5. Un nouveau benchmark de compositions filtrées OOD4 créé après v9 révèle une faiblesse plus générale : v9 couvre 48/64 mais produit **40 faux positifs**. v10 ajoute des garde-fous conservateurs et passe à **8/8 correctes parmi 8 couvertes, 0 faux positif**.
6. OOD5 est créé **après le patch v10** et n'est pas utilisé pour le régler : v10 s'abstient sur les 48 tâches et produit **0 faux positif**. Cela valide la sélectivité, mais montre aussi la principale limite actuelle : ces compositions reposent désormais entièrement sur le fallback LLM.

## Philosophie

> Déterministe quand on sait ; abstention quand on n'est pas sûr ; LLM pour le résiduel.

Une règle déterministe fausse est particulièrement dangereuse parce qu'elle court-circuite le fallback.

## Démarrage rapide

```bash
python scripts/check_setup.py
pytest -q
python scripts/run_stage3_audit.py
python scripts/compare_agents.py --agent v10
python scripts/run_metamorphic.py --agent v10
python scripts/run_ood.py --agent v10
python scripts/run_tool_contract.py
python scripts/run_runtime.py --fallback-count 1
```

Puis ouvrir dans cet ordre :

1. `notebooks/01_audit_stage3_and_limits.ipynb`
2. `notebooks/02_champion_to_best_candidate.ipynb`

Pour comprendre le parcours complet, lire `HOW_TO_RUN.md`.

## Structure

```text
agents/
  baselines/             Stage 1 / Stage 2 officiels
  champions/             Stage 3 privé à 92.5
  candidates/            candidates expérimentales jusqu'à v10
benchmarks/
  metamorphic/           transformations sans changement de réponse
  ood_development/       OOD1, utilisé pendant le développement
  ood_holdout/           OOD2 → OOD5, avec chronologie explicite
data/public/              dev.json public
notebooks/                histoire expérimentale expliquée
reference/official_ds_harness/
                          kit officiel du challenge
results/reference/        faits privés / résultats de référence
results/generated/        sorties locales régénérables
scripts/                  commandes reproductibles
src/evaluation/           protocole d'évaluation unique
tests/                    tests de non-régression
archive/original_notes/   anciens rapports, conservés mais sortis du flux principal
audit_independent/        audit Codex + Colab forced-fallback + diagnostic H1–H6
CODEX_AUDIT_HANDOFF/      agents soumis hashés + dev.json
```

## Important sur l'ancien ZIP

Dans `projects.zip`, `ds-harness/agent.py` était strictement identique à `stage1_direct.py`. Ce fichier ne représentait donc **pas** le champion à 92.5. Le champion utilisé dans nos audits est figé ici sous `agents/champions/stage3_92_5.py`.

## Statut actuel

**v10 = meilleure candidate locale**, avec :

- 180/180 dev déterministe ;
- 0 faux positif sur la suite métamorphique incluse ;
- OOD1 : 80/80 ;
- OOD2 : 20/20 parmi 20 couvertes ;
- OOD3 : 72/72 parmi 72 couvertes ;
- OOD4 : 8/8 parmi 8 couvertes, 56 abstentions ;
- OOD5 blind final : 0/48 couvertes, **0 faux positif** ;
- 0 mismatch prompt/runtime détecté ;
- pas de `exec(...)` détecté par l'audit statique.

**Verdict pré-TEST3 :** harness H1–H6 prêt ; **NO-GO** soumission jusqu’au cache Qwen Colab (`audit_independent/colab_forced_fallback.ipynb`).
