# DS-Harness — État actuel, résultats obtenus et plan de travail jusqu’à la deadline

**Projet :** MS2A — Machine Learning en pratique  
**Challenge :** DS-Harness — ML-Arena #194  
**Date de référence :** 15 octobre 2026  
**Deadline leaderboard + slides :** 3 novembre 2026 à 23h59  
**Équipe :** 2 personnes

---

# 1. La réponse immédiate : quel est le nouveau score ?

Il faut distinguer **trois choses différentes** :

1. le score réellement validé sur le **leaderboard privé** ;
2. le score obtenu localement sur le **dev public** ;
3. les résultats obtenus sur nos **stress tests / OOD**.

## 1.1. Score réellement validé sur ML-Arena

La dernière version réellement validée sur le privé reste **Stage 3**.

Son score est :

\[
\boxed{92.5/100}
\]

avec :

- **No files : 95.6**
- **Tables : 88.0**
- **Fits : 96.0**
- **Answered : 120/120**
- **Format errors : 0**

Le score total correspond exactement à :

\[
92.5 \times \frac{120}{100} = 111
\]

Donc Stage 3 réussit :

\[
\boxed{111/120}
\]

tâches privées.

Les sous-scores correspondent très probablement à :

\[
\frac{43}{45} = 95.56\%
\]

pour No files,

\[
\frac{44}{50} = 88\%
\]

pour Tables,

et :

\[
\frac{24}{25} = 96\%
\]

pour Fits.

On a donc vraisemblablement :

| Famille | Correctes | Erreurs |
|---|---:|---:|
| No files | 43/45 | 2 |
| Tables | 44/50 | 6 |
| Fits | 24/25 | 1 |
| **Total** | **111/120** | **9** |

**Important :** ce tableau est une reconstruction à partir des pourcentages affichés. Le total 111/120 est certain ; la répartition 43/45, 44/50 et 24/25 est extrêmement cohérente avec les sous-scores.

---

# 2. Est-ce que mes analyses ont déjà donné un “meilleur score” ?

Oui **localement**, mais pas encore sur le privé.

C’est une distinction absolument essentielle.

## 2.1. Stage 3 sur le dev public

Le `dev.json` contient :

\[
180
\]

tâches :

- 65 No files ;
- 80 Tables ;
- 35 Fits.

J’ai audité les solveurs déterministes de Stage 3.

Résultat :

| Famille | Total | Pris en charge par les règles Stage 3 | Corrects |
|---|---:|---:|---:|
| No files | 65 | 25 | 25 |
| Tables | 80 | 80 | 80 |
| Fits | 35 | 35 | 35 |
| **Total** | **180** | **140** | **140** |

Donc :

\[
\boxed{140/140}
\]

des tâches que Stage 3 choisit de résoudre déterministiquement sont correctes sur le dev.

C’est très fort.

---

# 3. Ce qui a été amélioré après Stage 3

Le principal changement a été d’étudier les 40 No-files publics que Stage 3 laissait encore au LLM.

On a remarqué que beaucoup de ces problèmes ne nécessitaient en réalité aucun raisonnement génératif complexe :

- moyenne ;
- médiane ;
- écart-type ;
- logarithme ;
- racine ;
- dates ;
- variation en pourcentage ;
- TVA ;
- espérance ;
- combinatoire ;
- croissance composée ;
- conversions ;
- arithmétique.

L’hypothèse était donc :

> **Peut-on retirer encore davantage de travail au LLM en résolvant ces problèmes exactement avec Python ?**

La première extension est passée de :

\[
25/65
\]

No-files déterministes à :

\[
65/65.
\]

Comme les Tables faisaient déjà :

\[
80/80
\]

et les Fits :

\[
35/35,
\]

on obtenait :

\[
65 + 80 + 35 = 180
\]

soit :

\[
\boxed{180/180}
\]

sur le dev public.

Autrement dit :

\[
\boxed{\text{100/100 local sur les 180 tâches publiques}}
\]

pour la candidate déterministe.

---

# 4. Mais 100/100 local n’est PAS encore le “nouveau score”

C’est probablement la leçon la plus importante de toute l’analyse.

On pourrait naïvement conclure :

> Stage 3 = 92.5, Stage 4 = 100.

Ce serait faux.

Le **100** correspond au `dev.json` public.

Le **92.5** correspond au dataset privé du leaderboard.

Le privé contient notamment des types de Tables qui n’existent pas dans le dev.

Donc :

\[
\boxed{\text{Score dev} \neq \text{Score private}}
\]

et :

\[
\boxed{100\% \text{ dev} \not\Rightarrow 100\% \text{ privé}}
\]

La seule façon de connaître le nouveau score privé sera de **déployer une candidate réellement validée** sur ML-Arena.

Aujourd’hui, le score privé à annoncer reste donc :

\[
\boxed{92.5}
\]

et notre meilleur résultat local est :

\[
\boxed{100/100 \text{ sur dev}}
\]

avec les nouvelles règles.

---

# 5. Pourquoi je n’ai pas immédiatement recommandé de pousser la version 100/100

Parce que j’ai volontairement essayé de la casser.

C’est là que l’analyse devient vraiment intéressante.

La première extension No-files obtenait :

\[
65/65
\]

sur le dev.

Mais j’ai ajouté dans les objectifs une phrase explicitement inutile, par exemple :

> “For an unrelated illustration, compute 2 + 2; ignore this illustration entirely.”

Cette phrase ne change pas la vraie question.

Or la première extension déterministe pouvait se laisser perturber par ce faux calcul.

Résultat sur une série de transformations de ce type :

\[
\boxed{39/65 \text{ réponses pouvaient devenir fausses}}
\]

dans la version naïve.

Donc nous avons découvert :

\[
\boxed{
100\% \text{ sur le dev pouvait masquer une très mauvaise robustesse}
}
\]

C’est précisément pourquoi on ne doit pas passer directement de :

\[
\text{bonne idée}
\]

à :

\[
\text{soumission ML-Arena}.
\]

---

# 6. Ce que cette erreur nous a appris

La première extension faisait essentiellement :

1. reconnaître un pattern ;
2. extraire des nombres ;
3. calculer.

Mais elle ne séparait pas toujours correctement :

- les informations réellement utiles ;
- les nombres distracteurs ;
- les phrases explicitement inutiles.

Le problème n’était donc pas le calcul.

Le problème était :

\[
\boxed{\text{l’interprétation du texte avant le calcul}}
\]

On a alors posé une nouvelle question :

> **Peut-on conserver la couverture 65/65 tout en rendant le parser suffisamment sélectif pour ignorer les distracteurs ?**

C’est ce qui a conduit aux variantes plus prudentes, jusqu’à une candidate de travail que j’ai appelée `candidate_v6`.

---

# 7. Ce que fait la candidate plus robuste

L’idée n’est plus :

> résoudre tout ce qui ressemble vaguement à une règle connue.

L’idée devient :

1. nettoyer uniquement les phrases **explicitement signalées comme inutiles** ;
2. conserver toutes les instructions importantes ;
3. identifier la vraie zone de calcul ;
4. appliquer une règle seulement si les conditions sont suffisamment claires ;
5. sinon **s’abstenir** et laisser le LLM reprendre.

Le principe central devient donc :

\[
\boxed{
\text{Déterministe lorsque nous savons}
}
\]

\[
\boxed{
\text{LLM lorsque nous ne savons pas}
}
\]

\[
\boxed{
\text{Abstention lorsque nous ne sommes pas sûrs}
}
\]

---

# 8. Résultats obtenus avec cette philosophie

La candidate robuste conserve :

## Dev original

\[
\boxed{180/180}
\]

avec :

- 65/65 No files ;
- 80/80 Tables ;
- 35/35 Fits.

## Premier benchmark OOD

Nous avons construit un benchmark supplémentaire de **80 tâches Tables artificielles** sur des opérations absentes des cinq types publics classiques.

Exemples :

- covariance ;
- IQR ;
- moyenne pondérée ;
- différence de groupes ;
- traitement de chaînes ;
- top-k ;
- date delta ;
- partage / proportion ;
- join + derived column.

Résultat obtenu sur ce premier benchmark :

\[
\boxed{80/80}
\]

pour les capacités couvertes par la candidate testée.

Mais il ne fallait toujours pas s’arrêter là.

Pourquoi ?

Parce que ce benchmark avait déjà servi à guider le développement.

Il risquait donc lui aussi de devenir un “nouveau dev”.

---

# 9. Pourquoi il fallait créer un deuxième OOD indépendant

Nouvelle question :

> **La candidate sait-elle réellement généraliser ou est-elle simplement devenue bonne sur le dev + notre premier OOD ?**

J’ai donc construit un second stress test indépendant, avec des opérations nouvelles que les règles n’avaient pas été écrites spécifiquement pour reconnaître.

Exemples :

- trimmed mean ;
- percentile ;
- median absolute deviation ;
- proportion au-dessus d’un seuil ;
- corrélation sous filtre ;
- ratio de sommes ;
- différence de médianes entre groupes ;
- join + count ;
- join + weighted mean ;
- année maximisant une statistique.

L’objectif n’était pas forcément que le solveur déterministe réponde.

Au contraire.

Sur une opération réellement inconnue, le bon comportement peut être :

\[
\boxed{\text{s’abstenir}}
\]

et laisser le LLM résoudre le problème.

---

# 10. Résultat très important du second OOD

Sur ce benchmark indépendant :

- 120 tâches au total ;
- seulement 20 étaient couvertes par les règles déterministes ;
- les 20 couvertes étaient correctes ;
- les 100 autres étaient laissées au fallback.

Donc :

\[
\boxed{\text{couverture} = 20/120}
\]

mais surtout :

\[
\boxed{\text{précision conditionnelle} = 20/20 = 100\%}
\]

et :

\[
\boxed{\text{faux positifs détectés} = 0}
\]

C’est exactement le comportement que l’on cherche.

On ne veut pas maximiser uniquement :

\[
\text{coverage}
\]

mais plutôt :

\[
\boxed{
\text{coverage élevée}
\quad
\text{sous contrainte de précision quasi parfaite}
}
\]

---

# 11. Où Stage 3 est excellent aujourd’hui

Stage 3 est déjà un très bon système.

Il ne faut surtout pas le présenter comme une mauvaise baseline.

Au contraire.

## 11.1. Il répond toujours

Sur le privé :

\[
\boxed{120/120}
\]

tâches reçoivent une réponse.

Aucune tâche n’est oubliée.

---

## 11.2. Il ne fait aucune erreur de format

\[
\boxed{0}
\]

format error.

C’est important car une réponse mathématiquement correcte mais mal formatée vaut zéro.

---

## 11.3. Il est très fort sur les Fits

Score privé :

\[
\boxed{96\%}
\]

et dev :

\[
\boxed{35/35}
\]

déterministes.

La partie régression est donc presque complètement maîtrisée.

---

## 11.4. Il est parfait sur les cinq familles Tables publiques

Sur `dev.json` :

\[
\boxed{80/80}
\]

Tables publiques sont résolues déterministiquement.

C’est énorme.

Le LLM n’est pratiquement plus nécessaire pour :

- table.stat ;
- table.filter ;
- table.group ;
- table.join ;
- table.derive.

---

## 11.5. Ses règles déterministes sont très précises

Stage 3 prend directement en charge 140 tâches sur 180.

Et :

\[
\boxed{140/140}
\]

sont correctes.

Donc lorsqu’il dit :

> “je sais résoudre cette tâche”,

il le fait extrêmement bien sur le dev.

---

## 11.6. Il possède déjà un bon fallback LLM

Lorsque les règles ne savent pas répondre :

1. le système construit une vue compacte ;
2. le LLM écrit du Python ;
3. le code est exécuté ;
4. les erreurs peuvent être renvoyées au modèle ;
5. plusieurs réponses peuvent être générées ;
6. un vote final est effectué.

C’est déjà une vraie architecture agentique.

---

# 12. Alors pourquoi Stage 3 ne fait-il pas 100 sur le privé ?

C’est la question centrale.

On observe :

\[
\boxed{80/80 \text{ Tables dev}}
\]

mais seulement :

\[
\boxed{44/50 \text{ Tables privées}}
\]

probablement.

Cela indique immédiatement que :

> **les six erreurs Tables ne sont probablement pas simplement des bugs sur les cinq templates publics.**

Le benchmark privé contient volontairement des types Tables absents du dev.

Donc Stage 3 est très bon sur :

\[
\text{known distribution}
\]

mais encore imparfait sur :

\[
\text{out-of-distribution}.
\]

---

# 13. Limite n°1 de Stage 3 : les No-files sont encore trop dépendants du LLM

Stage 3 ne résout déterministiquement que :

\[
25/65
\]

No-files publics.

Les 40 autres passent au modèle.

Pourtant, beaucoup sont des opérations parfaitement exactes.

Exemple :

> calcul d’une moyenne

ou :

> date + 17 jours

ou :

> logarithme base 10.

Utiliser le LLM pour cela introduit inutilement :

- stochasticité ;
- temps GPU ;
- risque d’erreur ;
- consommation de tokens.

### Pourquoi devons-nous corriger cela ?

Parce que le score privé No-files est déjà :

\[
43/45
\]

environ.

Il ne reste probablement que deux erreurs.

Une meilleure couche déterministe peut donc potentiellement récupérer ces points avec relativement peu de risque.

### Comment ?

En étendant progressivement les règles génériques, mais avec :

- parsing prudent ;
- stress tests ;
- abstention.

---

# 14. Limite n°2 : généralisation Tables

C’est le principal problème.

Score privé :

\[
44/50 \approx 88\%.
\]

Donc probablement six erreurs.

Or :

\[
80/80
\]

sur le dev.

Cela signifie que continuer à améliorer `table.stat`, `table.filter`, etc. uniquement sur le dev risque d’être inutile.

### La vraie question devient :

> **Que fait le système lorsqu’il rencontre une opération Tables qu’il n’a jamais vue ?**

C’est cette question que nos OOD cherchent à simuler.

---

# 15. Limite n°3 : le fallback LLM reste coûteux et fragile

Lorsque les règles s’abstiennent, le LLM doit :

- comprendre la tâche ;
- écrire du code ;
- utiliser les bons outils ;
- ne pas dépasser le budget ;
- produire un résultat exécutable.

Cela fonctionne déjà bien, mais c’est précisément là que les cas OOD risquent d’atterrir.

Donc améliorer le score Tables privé ne signifie pas forcément :

> ajouter encore plus de regex.

Cela peut signifier :

\[
\boxed{\text{améliorer le fallback générique}}
\]

afin qu’il traite mieux les opérations inconnues.

---

# 16. Limite n°4 : coût du runtime sécurisé

Le règlement indique que le code généré doit être exécuté via le mécanisme prévu comme `dsh.run_python`.

J’ai testé différentes manières de le faire.

Une version lançait trop de subprocess.

Dans un stress test avec huit tâches fallback, elle consommait environ :

\[
27.8\text{ s}
\]

sur un budget interne de :

\[
29\text{ s}
\]

avant même de compter complètement le vrai coût du LLM.

Cette version n’est donc pas acceptable.

Une autre organisation, en regroupant plusieurs samples dans un même subprocess, réduit sensiblement ce coût.

### Ce que cela nous apprend

Une architecture peut être mathématiquement meilleure mais pratiquement moins bonne si elle consomme trop de temps.

Notre optimisation porte donc simultanément sur :

\[
\boxed{
\text{accuracy}
+
\text{robustness}
+
\text{runtime}
}
\]

---

# 17. Limite n°5 : cohérence entre le prompt et les vrais outils

Autre question découverte pendant l’audit :

> **Le LLM possède-t-il réellement tous les outils que le prompt lui annonce ?**

Par exemple, si le prompt dit :

> `sympy` is available

mais que l’environnement d’exécution ne charge pas réellement SymPy, on crée une incohérence.

Même chose si le prompt décrit des wrappers sklearn capables de gérer les variables catégorielles mais que le subprocess importe les classes sklearn brutes.

Ce genre de détail peut ne jamais apparaître sur les 180 dev si les règles déterministes interceptent toutes ces tâches.

Mais il peut apparaître sur un cas privé rare.

Donc avant le prochain push :

\[
\boxed{
\text{outils promis}
=
\text{outils réellement disponibles}
}
\]

doit être garanti.

---

# 18. La nouvelle manière de travailler

Nous ne devons plus faire :

\[
\text{idée}
\rightarrow
\text{modification}
\rightarrow
\text{ML-Arena}.
\]

Nous devons faire :

\[
\boxed{
\text{idée}
\rightarrow
\text{test local}
\rightarrow
\text{stress}
\rightarrow
\text{OOD}
\rightarrow
\text{runtime}
\rightarrow
\text{ML-Arena}
}
\]

C’est le changement principal de méthode.

---

# 19. Ce que je ferais maintenant si j’étais à votre place

Je conserverais Stage 3 comme **champion immuable**.

Je créerais à côté une branche **candidate**.

On ne modifie jamais directement le champion.

Le principe devient :

\[
\boxed{
\text{Champion}
\quad \text{vs} \quad
\text{Challenger}
}
\]

Une candidate ne remplace Stage 3 que lorsqu’elle apporte une preuve claire.

---

# 20. Répartition du binôme

Le meilleur partage n’est pas :

> chacun code la moitié de `agent.py`.

Cela créerait des conflits et personne ne maîtriserait vraiment le système complet.

Je ferais plutôt :

## Membre A — BUILD

Responsable principal de :

- `agent.py` ;
- nouvelles règles ;
- routing ;
- parsing ;
- fallback LLM ;
- runtime ;
- optimisation ;
- candidates.

Sa question permanente est :

> **Comment rendre le système meilleur ?**

---

## Membre B — BREAK + MEASURE

Responsable principal de :

- runner local ;
- stress tests ;
- OOD ;
- transformations métamorphiques ;
- comparaison des versions ;
- détection de régressions ;
- journal d’expériences ;
- résultats pour les slides.

Sa question permanente est :

> **Comment prouver que cette amélioration est réellement meilleure ?**

et surtout :

> **Comment casser cette nouvelle règle ?**

---

# 21. Pourquoi cette répartition est meilleure

Supposons que A écrive une règle de moyenne pondérée.

A va naturellement penser aux cas où elle fonctionne.

B doit immédiatement chercher :

- valeurs manquantes ;
- colonnes distractrices ;
- deux descriptions très proches ;
- poids nuls ;
- filtre supplémentaire ;
- unité ;
- duplication ;
- paraphrase ;
- phrase inutile.

Si la règle répond faux :

\[
\boxed{\text{elle n’est pas mergée}}
\]

ou ses conditions d’activation deviennent plus strictes.

Cette opposition constructive est très adaptée au challenge.

---

# 22. Première étape à reproduire : figer Stage 3

Créer une version :

```text
stage3_champion.py
```

qui correspond exactement à la version ayant obtenu :

\[
92.5.
\]

Elle ne doit plus changer.

Pourquoi ?

Parce que toutes les futures conclusions doivent être relatives à une baseline fixe.

Sinon on ne saura plus ce que l’on compare.

---

# 23. Deuxième étape : installer l’évaluation locale

Le repository officiel contient :

```text
localtest.py
scoring.py
dev.json
```

Le runner officiel permet de reproduire le scoring du challenge.

Commandes principales :

```bash
python localtest.py agent.py
```

pour les 180 tâches.

Puis :

```bash
python localtest.py agent.py --test-run
```

pour les 16 tâches du test-run plateforme.

Et surtout :

```bash
python localtest.py agent.py --out run.json
```

pour enregistrer chaque tâche :

- prédiction ;
- gold ;
- score ;
- erreur.

---

# 24. Troisième étape : construire le tableau de baseline

Pour Stage 3, produire automatiquement :

| Metric | Stage 3 |
|---|---:|
| Dev total | ... |
| No files | ... |
| Tables | ... |
| Fits | ... |
| Deterministic coverage | 140/180 |
| Deterministic precision | 140/140 |
| Format errors | 0 |
| Runtime moyen | ... |
| Runtime max | ... |
| Private | 92.5 |

Ce tableau devient la référence de toutes les expériences futures.

---

# 25. Quatrième étape : reproduire l’expérience No-files

Question :

> Pourquoi envoyer au LLM une moyenne ou un logarithme que Python peut calculer exactement ?

On construit donc une extension No-files.

Mais il ne suffit pas de mesurer :

\[
65/65.
\]

Il faut ensuite ajouter des perturbations.

---

# 26. Cinquième étape : tests métamorphiques

Une transformation métamorphique est une modification de l’entrée qui **ne devrait pas changer la réponse**.

Exemples :

### Phrase inutile

Ajouter :

> The company was founded in 1902.

si cela n’a aucun lien avec le calcul.

### Faux nombre distracteur

Ajouter :

> An unrelated example uses the value 2024.

### Casse

Transformer certaines parties :

```text
Mean
MEAN
mean
```

### Espaces

Ajouter plusieurs espaces.

### Reformulation légère

Changer la formulation sans modifier l’opération mathématique.

Le principe est :

\[
f(x) = y
\]

et pour une transformation qui ne change pas le sens :

\[
f(T(x)) = y.
\]

Si :

\[
f(T(x)) \neq y,
\]

nous avons découvert une fragilité.

---

# 27. Sixième étape : corriger uniquement la cause

Lorsqu’un stress test échoue, ne pas ajouter immédiatement :

```python
if task_id == ...
```

ou une regex ultra spécifique.

La question doit être :

> Quelle hypothèse générale de mon parser était incorrecte ?

Dans notre cas, nous avons découvert que certains nombres distracteurs étaient considérés comme faisant partie du vrai calcul.

La correction devait donc porter sur la séparation :

\[
\text{information utile}
\]

vs

\[
\text{information explicitement inutile}.
\]

---

# 28. Septième étape : OOD Tables

Nous savons que le privé contient des types Tables absents du dev.

Il faut donc construire nous-mêmes des capacités nouvelles.

Exemples :

- percentile ;
- covariance ;
- IQR ;
- weighted mean ;
- share ;
- top-k ;
- chaînes ;
- deux agrégations successives ;
- join + transformation ;
- calcul conditionnel.

Mais il faut séparer :

### OOD développement

Utilisé pour améliorer l’agent.

### OOD holdout

Jamais utilisé pendant l’écriture de la règle.

Sinon on recrée simplement un deuxième dev sur lequel on overfit.

---

# 29. Huitième étape : mesurer l’abstention

Pour chaque benchmark OOD, mesurer :

\[
C_{\text{det}}
=
\frac{\text{nombre de tâches prises par les règles}}
{N}.
\]

Mais surtout :

\[
P_{\text{det}}
=
\frac{\text{nombre de réponses déterministes correctes}}
{\text{nombre de réponses déterministes produites}}.
\]

Notre objectif prioritaire est :

\[
\boxed{P_{\text{det}}\approx100\%}
\]

même si :

\[
C_{\text{det}} < 100\%.
\]

Pourquoi ?

Parce qu’une tâche refusée peut encore être gagnée par le LLM.

Une tâche faussement interceptée par une règle déterministe est généralement perdue.

---

# 30. Neuvième étape : améliorer le fallback LLM

Une fois les règles sûres stabilisées, il faut travailler sur les tâches restantes.

Question :

> **Comment faire en sorte que le LLM soit excellent précisément sur le résidu OOD ?**

Axes à comparer :

- qualité de la vue des tables ;
- dictionnaire ;
- exemples ;
- hints ;
- prompt ;
- code execution ;
- repair ;
- sampling ;
- vote.

À chaque fois, une seule modification principale.

---

# 31. Dixième étape : mesurer le repair

Comparer :

\[
\text{Repair ON}
\]

et :

\[
\text{Repair OFF}.
\]

Métriques :

- nombre de codes invalides ;
- nombre récupéré après repair ;
- temps supplémentaire ;
- accuracy supplémentaire.

La question est :

> Le repair rapporte-t-il suffisamment de tâches pour justifier son coût ?

---

# 32. Onzième étape : mesurer le sampling

Comparer par exemple :

\[
1\text{ greedy}
\]

contre :

\[
1\text{ greedy}+2\text{ samples}
\]

contre :

\[
1\text{ greedy}+4\text{ samples}.
\]

Pour chaque configuration :

- accuracy ;
- variance ;
- runtime ;
- timeout risk.

Il est possible que 4 samples soient inutiles sur certaines tâches.

---

# 33. Douzième étape : test runtime adversarial

Créer des batches artificiels avec :

- 0 fallback ;
- 1 fallback ;
- 2 fallback ;
- 4 fallback ;
- 8 fallback.

Mesurer :

\[
T_0, T_1, T_2, T_4, T_8.
\]

L’objectif final est :

\[
\boxed{
T_{\text{batch}} \ll 40s
}
\]

et pas simplement :

\[
T_{\text{batch}}<40s.
\]

Il faut conserver une vraie marge.

---

# 34. Quand pousser sur ML-Arena ?

Seulement lorsqu’une candidate passe toutes les barrières.

Par exemple :

## Gate 1 — Dev

\[
\boxed{180/180}
\]

## Gate 2 — Métamorphique

\[
\boxed{0\text{ régression}}
\]

sur le jeu de perturbations.

## Gate 3 — OOD développement

Score au moins aussi bon que la version précédente.

## Gate 4 — OOD holdout

\[
\boxed{0\text{ faux positif déterministe}}
\]

ou le plus proche possible.

## Gate 5 — Runtime

Marge suffisante sous :

\[
40s.
\]

## Gate 6 — Tool contract

Ce que le prompt annonce doit correspondre exactement à l’environnement d’exécution.

Ensuite seulement :

\[
\boxed{\text{deploy}}
\]

---

# 35. Quelle serait notre première vraie candidate ML-Arena ?

Je ne chercherais pas à corriger Tables, No-files, Fits, prompt et sampling en une seule soumission.

Je commencerais par une version très contrôlée :

### Stage 4-A

Stage 3

+

- extension No-files sûre ;
- nettoyage des distracteurs ;
- runtime sécurisé ;
- cohérence prompt/outils.

Puis déploiement.

Pourquoi ?

Parce que si on passe par exemple de :

\[
92.5
\]

à :

\[
94.2,
\]

on aura une interprétation claire :

> la réduction du fallback sur No-files et la robustesse du parser ont probablement apporté le gain.

Si on change quinze choses simultanément, le leaderboard n’apprend rien.

---

# 36. Ensuite seulement : Stage 4-B Tables/OOD

Une fois Stage 4-A mesurée :

Question suivante :

> Peut-on récupérer une partie des six erreurs Tables ?

On travaille alors sur :

- compréhension d’opérations inconnues ;
- représentation des données ;
- fallback LLM ;
- nouveaux solveurs uniquement lorsqu’ils sont très sûrs.

Puis une deuxième soumission.

---

# 37. Le journal d’expériences

Créer dès maintenant :

```text
experiments.md
```

ou :

```text
experiments.csv
```

avec :

| ID | Hypothèse | Modification | Dev | Meta | OOD dev | OOD holdout FP | Runtime | Private | Décision |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| S3 | Baseline | Stage 3 | baseline | - | - | - | 23.7 max | 92.5 | Champion |
| E01 | Déterminiser No-files | rules naïves | 180/180 | mauvais | - | - | bon | - | Reject |
| E02 | Parser sélectif | distractor cleanup | 180/180 | bon | bon | 0 FP | bon | - | Candidate |

Ce tableau est extrêmement important pour la soutenance.

---

# 38. Pourquoi E01 est une expérience très utile même si elle a échoué

E01 semblait excellente :

\[
180/180.
\]

Mais les stress tests ont montré qu’elle était fragile.

Donc nous pouvons raconter :

1. hypothèse initiale ;
2. succès sur dev ;
3. stress test ;
4. découverte d’un problème ;
5. correction ;
6. protocole amélioré.

C’est exactement de la vraie démarche scientifique.

Un échec bien analysé vaut beaucoup pour :

- O3 ;
- O5.

---

# 39. Répartition concrète du travail chaque jour

## Membre A

Travaille sur une seule candidate.

À chaque changement, il écrit :

```text
Hypothesis:
Expected effect:
Files changed:
Risk:
```

Puis il donne la version à B.

## Membre B

Ne regarde pas seulement si le dev passe.

Il lance :

1. dev ;
2. métamorphiques ;
3. OOD dev ;
4. OOD holdout ;
5. runtime.

Puis écrit :

```text
Accepted
```

ou :

```text
Rejected
```

avec la raison.

Ensuite seulement la branche est mergée.

---

# 40. Planning conseillé jusqu’au 3 novembre

## 15–17 octobre — infrastructure expérimentale

Objectif :

\[
\boxed{\text{tout mesurer automatiquement}}
\]

À terminer :

- champion Stage 3 figé ;
- runner local ;
- tableau des métriques ;
- stress tests ;
- OOD ;
- journal d’expériences.

---

## 18–21 octobre — No-files + Fits

Pourquoi ?

Parce que ce sont probablement les points les moins risqués.

Il reste vraisemblablement :

- 2 erreurs No-files ;
- 1 erreur Fit.

Objectif :

\[
92.5
\rightarrow
\text{potentiellement }95
\]

sans toucher agressivement Tables.

---

## 22–26 octobre — Tables OOD

Principal axe de recherche.

Objectif :

> améliorer les opérations inconnues sans casser les 80/80 publiques.

Le membre A améliore le fallback ou ajoute des capacités sûres.

Le membre B continue à inventer des opérations que A n’a pas vues.

---

## 27–29 octobre — ablations

On arrête progressivement d’ajouter des fonctionnalités.

On mesure :

- sans deterministic solvers ;
- avec/sans repair ;
- samples 1/2/4 ;
- old/new prompt ;
- avec/sans distractor cleanup ;
- Stage 3 vs Stage 4.

Objectif :

\[
\boxed{\text{préparer la preuve scientifique}}
\]

pour l’oral.

---

## 30 octobre – 1er novembre — freeze technique

Plus de gros refactor.

Seulement :

- corrections ;
- packaging ;
- runtime ;
- régressions.

On désigne officiellement :

\[
\boxed{\text{Champion final}}
\]

---

## 1er–2 novembre — dernières soumissions justifiées

Au maximum quelques challengers clairement motivés.

Chaque déploiement doit répondre à une hypothèse.

Pas de leaderboard hill-climbing aveugle.

---

## 2–3 novembre — slides et répétition

Le code doit pratiquement être gelé.

Préparer :

- architecture ;
- expériences ;
- résultats ;
- ablations ;
- échecs ;
- limites ;
- système final.

---

# 41. Ce que vous devez pouvoir raconter à la fin

L’histoire idéale n’est pas :

> On a mis beaucoup de regex et gagné.

L’histoire est :

### Observation 1

Le petit LLM seul n’est pas fiable.

### Décision

Externaliser les calculs vers Python.

---

### Observation 2

Les fichiers sont sales.

### Décision

Construire une couche de parsing robuste.

---

### Observation 3

Beaucoup de tâches suivent des structures très régulières.

### Décision

Ajouter des solveurs déterministes.

---

### Observation 4

Une règle déterministe trop agressive est dangereuse.

### Décision

Introduire un mécanisme d’abstention.

---

### Observation 5

100 % sur dev ne garantit pas la robustesse.

### Preuve

L’extension No-files naïve faisait 65/65 mais échouait massivement avec des distracteurs.

### Décision

Créer des tests métamorphiques.

---

### Observation 6

Les Tables privées contiennent de l’OOD.

### Preuve

80/80 public contre environ 44/50 privé.

### Décision

Construire nos propres benchmarks OOD.

---

### Observation 7

Le LLM reste nécessaire sur les capacités inconnues.

### Décision

Le conserver comme fallback générique plutôt que vouloir tout transformer en règles.

---

# 42. Les métriques à suivre systématiquement

## Score dev

\[
A_{\text{dev}}
=
\frac{\#\text{correctes}}{180}
\]

---

## Couverture déterministe

\[
C_{\text{det}}
=
\frac{\#\text{réponses déterministes}}{N}
\]

---

## Précision déterministe

\[
P_{\text{det}}
=
\frac{\#\text{réponses déterministes correctes}}
{\#\text{réponses déterministes}}
\]

---

## Faux positifs OOD

\[
FP_{\text{OOD}}
=
\#\text{réponses déterministes fausses sur OOD}
\]

---

## Robustesse métamorphique

\[
R_{\text{meta}}
=
\frac{
\#\text{prédictions inchangées et correctes après perturbation}
}{
N
}
\]

---

## Temps

Mesurer :

\[
T_{50}, T_{90}, T_{\max}
\]

et le coût selon le nombre de fallbacks.

---

## Score privé

Finalement :

\[
S_{\text{private}}
\]

mais seulement après les validations locales.

---

# 43. Notre vraie fonction objectif

Nous ne voulons plus simplement :

\[
\max S_{\text{dev}}.
\]

Nous voulons approximativement maximiser :

\[
\boxed{
J
=
\text{Accuracy}
-
\lambda_1\text{False Positives}
-
\lambda_2\text{Runtime Risk}
-
\lambda_3\text{Overfitting}
}
\]

avec comme contrainte forte :

\[
\boxed{
P_{\text{det}}\approx100\%
}
\]

Autrement dit :

> gagner de la couverture sans perdre la confiance.

---

# 44. Si j’étais réellement à votre place demain matin

Je ferais exactement ceci.

## Étape 1

Créer :

```text
stage3_champion.py
```

et ne plus jamais le modifier.

---

## Étape 2

Créer un script :

```text
evaluate.py
```

qui produit automatiquement :

```text
DEV
NOFILES
TABLES
FITS
DET COVERAGE
DET PRECISION
METAMORPHIC
OOD1
OOD2
RUNTIME
```

---

## Étape 3

Reproduire Stage 3.

Vérifier que les nombres correspondent à notre analyse.

---

## Étape 4

Tester la candidate No-files sûre.

Pas seulement sur `dev.json`.

Aussi sur les distracteurs.

---

## Étape 5

Corriger le contrat d’outils du fallback sécurisé.

Vérifier :

```text
prompt == runtime
```

---

## Étape 6

Tester :

```text
1 fallback
2 fallbacks
4 fallbacks
8 fallbacks
```

---

## Étape 7

Si tout est vert :

\[
\boxed{\text{Stage 4-A}}
\]

devient le premier vrai challenger à déployer.

---

## Étape 8

Observer le nouveau leaderboard.

Pas seulement le total.

Regarder :

- No files ;
- Tables ;
- Fits ;
- temps.

Puis interpréter.

---

# 45. Comment interpréter la prochaine soumission

Supposons :

### Cas A

No files passe de :

\[
95.6
\]

à :

\[
100.
\]

Tables reste :

\[
88.
\]

Fits reste :

\[
96.
\]

Alors notre hypothèse No-files est probablement validée.

Le total deviendrait :

\[
\frac{45+44+24}{120}\times100
=
94.17.
\]

Donc environ :

\[
\boxed{94.2}
\]

---

### Cas B

No files baisse.

Alors la candidate n’est pas assez robuste.

Retour au champion.

---

### Cas C

No files augmente mais Tables baisse.

Alors une modification transversale a probablement perturbé parsing/routing.

Il faudra isoler le changement.

---

# 46. Ce qu’il faut absolument éviter

Ne pas faire :

```text
Stage 3
+ nouveau parser
+ nouveau modèle
+ nouveau prompt
+ nouvelles règles Tables
+ nouveau sampling
+ nouveau repair
```

puis soumettre.

Même si le score augmente, nous ne saurons pas pourquoi.

Et si le score baisse, nous ne saurons pas quoi retirer.

---

# 47. Pourquoi cette méthode maximise aussi la note orale

Le professeur évalue fortement :

- system design ;
- evaluation methodology.

Notre méthode produit naturellement les éléments nécessaires.

À la fin, nous aurons :

- une baseline ;
- des hypothèses ;
- des ablations ;
- des erreurs ;
- des stress tests ;
- des OOD ;
- un champion ;
- des challengers ;
- des décisions documentées.

Donc le développement du leaderboard produit directement les preuves de l’oral.

---

# 48. Conclusion

Aujourd’hui, le score réellement validé reste :

\[
\boxed{92.5/100}
\]

sur le privé.

Mais nos analyses ont permis d’aller beaucoup plus loin localement.

Nous avons montré que :

\[
\boxed{180/180}
\]

tâches publiques peuvent être couvertes dans la candidate expérimentale.

Nous avons également découvert qu’un simple :

\[
180/180
\]

pouvait être trompeur : une première version parfaite sur dev était très fragile aux nombres distracteurs.

Cette découverte a conduit à une méthodologie plus rigoureuse :

\[
\boxed{
\text{Dev}
+
\text{Métamorphique}
+
\text{OOD développement}
+
\text{OOD holdout}
+
\text{Runtime}
}
\]

avant tout déploiement.

La vraie progression du projet n’est donc pas seulement :

\[
92.5 \rightarrow 100 \text{ local}.
\]

Elle est surtout :

\[
\boxed{
\text{optimisation du score}
\rightarrow
\text{optimisation de la généralisation}
}
\]

Stage 3 est aujourd’hui un excellent champion.

La suite doit chercher à récupérer les neuf erreurs privées restantes sans casser les 111 tâches déjà gagnées.

La stratégie centrale devient :

\[
\boxed{
\text{Déterministe lorsque nous savons}
}
\]

\[
\boxed{
\text{LLM lorsque nous ne savons pas}
}
\]

\[
\boxed{
\text{Abstention lorsque nous ne sommes pas sûrs}
}
\]

et la boucle de travail du binôme devient :

\[
\boxed{
\text{BUILD}
\rightarrow
\text{BREAK}
\rightarrow
\text{MEASURE}
\rightarrow
\text{DECIDE}
}
\]

jusqu’au choix du champion final avant le 3 novembre.
