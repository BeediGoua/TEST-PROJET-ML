# Limites et prochaines étapes

## Faible ROI actuellement

- Réécrire les cinq solveurs Tables publics : Stage 3 est déjà à 80/80 déterministe sur dev.
- Réécrire Fits de zéro : 35/35 publics sont déjà couverts.
- Ajouter des regex uniquement pour augmenter le dev : E01→E02 montre que cela peut dégrader fortement la robustesse.

## Limite principale désormais prouvée

OOD4/OOD5 montrent une classe de tâches importante : **composition d'un filtre/sous-ensemble avec une opération agrégée**.

v9 pouvait reconnaître l'opérateur (`IQR`, weighted mean, top-k, covariance, etc.) tout en ignorant la clause de sous-ensemble, produisant une valeur plausible mais fausse. v10 préfère s'abstenir si la composition n'est pas explicitement supportée.

C'est meilleur du point de vue sécurité, mais cela déplace beaucoup de tâches vers le **fallback LLM** : sur OOD5, v10 s'abstient sur 48/48.

## ROI élevé maintenant

1. **Tester le vrai fallback Qwen sur les abstentions OOD4/OOD5.** C'est désormais l'expérience la plus rentable.
2. **Ablation repair / sampling** : `repair ON/OFF`, `NSAMP=1/2/4`, greedy vs vote, avec score et runtime.
3. **Améliorer la représentation Tables pour le LLM** : dictionnaire, colonnes pertinentes, description compacte des jointures et filtres.
4. **Validateur post-génération** : détecter quand le code généré oublie un filtre présent dans l'objectif.
5. **Fits edge cases** : le 96% privé est compatible avec 24/25 ; tester catégories, missing, probabilité, coefficient, R² et filtres.
6. **Runtime end-to-end** : les mesures subprocess sont sous contrôle, mais la génération Qwen doit encore être mesurée par batch réel.

## Limites connues de v10

- Aucun score privé v10.
- OOD2 laisse 100/120 tâches au LLM.
- OOD3 laisse 8/80 jointures au LLM.
- OOD4 laisse 56/64 compositions au LLM.
- OOD5 laisse 48/48 tâches au LLM.
- Les garde-fous sont conservateurs : ils réduisent les faux positifs déterministes mais ne créent pas de nouvelle capacité de calcul.
- Le résultat final dépend donc fortement du comportement réel de Qwen, du repair et du vote.

## Gate recommandé avant la prochaine soumission

```text
180/180 dev
→ 0 faux positif métamorphique connu
→ OOD2/OOD3/OOD4/OOD5 sans faux positif déterministe
→ 0 mismatch prompt/runtime
→ runtime subprocess sous marge
→ vrai Qwen --test-run
→ vrai Qwen dev complet
→ ablations utiles
→ soumission privée correspondant à une hypothèse écrite
```
