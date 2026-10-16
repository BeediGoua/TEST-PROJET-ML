Oui. Avec tout ce qu’on a maintenant, je pense qu’il faut **changer de mode de travail** : arrêter de modifier directement l’agent au feeling et passer à un protocole expérimental propre jusqu’au 3 novembre.

Et les tests que je viens de faire modifient déjà le plan : **je ne pousserais ni `Stage4_calc`, ni `safe_v2` tels quels.** On a maintenant une meilleure candidate de travail, `candidate_v6`, mais elle doit encore passer quelques validations avant un déploiement privé.

## 1. Où nous en sommes exactement

La référence reste votre **Stage 3**, réellement validée sur ML-Arena :

\[
\boxed{92.5/100 = 111/120}
\]

avec probablement :

\[
43/45\ \text{No-files},
\qquad
44/50\ \text{Tables},
\qquad
24/25\ \text{Fits}.
\]

Stage 3 est donc notre **champion**. On ne le touche plus. Toute nouvelle version est un **candidate** qui doit battre le champion sans régression.

J’ai reconstruit un environnement local de test. Il n’est pas identique bit-à-bit à ML-Arena — ici nous avons Python 3.13 et pas les poids GPU Qwen montés — mais il permet de reproduire correctement tout ce qui concerne parsing, pandas, sklearn 1.8, règles déterministes, scoring, fichiers, stress tests et OOD. Le scorer officiel confirme d’ailleurs que le runner local et la plateforme utilisent le même principe de scoring et de batchs.  Le `localtest.py` officiel est justement prévu pour tester les 180 tâches, des types particuliers et produire les résultats tâche par tâche avant un push. 

La seule chose que je **ne peux pas reproduire exactement ici** est la génération du vrai Qwen sur RTX 4090, car les poids ne sont pas montés dans mon environnement. Cette dernière validation devra donc passer soit par votre environnement Colab compatible, soit par le test-run ML-Arena.

---

# 2. Ce que nos nouveaux tests viennent de montrer

On a maintenant plusieurs niveaux d’évaluation.

### Stage 3, déterministe

\[
25/65\ \text{No-files}
\]

\[
80/80\ \text{Tables}
\]

\[
35/35\ \text{Fits}
\]

soit :

\[
\boxed{140/140}
\]

sur toutes les tâches qu’il choisit de résoudre sans LLM.

C’est notre baseline de sécurité.

### Première extension No-files

La première Stage 4 obtenait :

\[
65/65
\]

No-files, donc avec Tables et Fits :

\[
\boxed{180/180}
\]

dev déterministe.

Ça paraissait formidable.

Mais j’ai ensuite ajouté une phrase inutile :

> For an unrelated illustration, compute 2 + 2; ignore this illustration entirely.

Et là, la version naïve faisait seulement :

\[
26/65
\]

correctes sur cette transformation, avec :

\[
39
\]

faux positifs déterministes.

C’est extrêmement important.

Cela prouve expérimentalement que :

\[
\boxed{
100\% \text{ dev} \not\Rightarrow \text{robustesse}
}
\]

et que notre première Stage 4 était **trop agressive**.

C’est exactement le genre d’analyse que le professeur voudra voir dans O3/O5.

---

# 3. Ce que nous avons corrigé ensuite

J’ai construit progressivement une version plus prudente qui retire uniquement les phrases explicitement signalées comme :

- irrelevant ;
- unrelated ;
- does not affect ;
- changes nothing ;
- ignore this illustration / fact / note / etc.

Mais elle conserve évidemment les instructions importantes comme :

> Ignore missing values.

J’ai également corrigé un problème subtil : il ne suffisait pas de nettoyer le texte avant les règles. Le distracteur pouvait déjà perturber le **prétraitement des données**.

Un exemple réel que nous avons découvert est `d_174`.

Avec l’objectif original :

\[
1159
\]

correct.

En ajoutant une phrase inutile contenant `2024`, le parsing de la sentinelle `-1` pouvait être perturbé et donner :

\[
1111.
\]

Nous avons donc déplacé le nettoyage explicite **avant `load_task()`**, pas seulement avant les règles.

C’est un vrai bug de conception identifié par stress testing.

---

# 4. État actuel de `candidate_v6`

Après cette correction :

### Dev original

\[
65/65\ \text{No-files}
\]

\[
80/80\ \text{Tables}
\]

\[
35/35\ \text{Fits}
\]

soit :

\[
\boxed{180/180}
\]

sans faux positif déterministe.

### Premier benchmark OOD

Nous avions construit 80 nouvelles tâches correspondant à :

- covariance ;
- IQR ;
- moyenne pondérée ;
- dates ;
- différences de groupes ;
- membership ;
- share ;
- string ;
- top-k ;
- join + derive.

Résultat :

\[
\boxed{80/80}
\]

### Transformations métamorphiques

J’ai ensuite testé les trois familles avec :

- nombre inutile avant l’objectif ;
- nombre inutile après l’objectif ;
- faux calcul `2+2` explicitement déclaré inutile ;
- variations de casse et d’espaces.

Après correction, `candidate_v6` reste parfaite sur ces tests.

Cela est beaucoup plus significatif que le simple `180/180`.

---

# 5. J’ai ensuite créé un deuxième OOD volontairement indépendant

C’est important méthodologiquement : le premier OOD avait servi à développer les nouvelles règles. Il ne pouvait donc pas constituer à lui seul un vrai test.

J’ai créé un **holdout OOD2 de 120 nouvelles tâches** que les nouvelles règles n’avaient jamais vues.

Opérations :

- trimmed mean ;
- coefficient de variation ;
- percentile 90 ;
- proportion au-dessus d’un seuil ;
- median absolute deviation ;
- différence absolue de médianes entre groupes ;
- suffixe de chaîne ;
- ratio des sommes ;
- corrélation sous filtre ;
- année maximisant une médiane ;
- join + count ;
- join + weighted mean.

Résultat pour Stage 3 :

\[
20/120
\]

prises en charge déterministiquement,

et :

\[
20/20
\]

correctes.

Résultat pour `candidate_v6` :

\[
20/120
\]

prises en charge,

et :

\[
20/20
\]

correctes.

Donc sur les 100 tâches réellement inconnues :

\[
\boxed{\text{candidate\_v6 s'abstient}}
\]

au lieu d'inventer une réponse.

C’est exactement ce que nous voulions.

Sa précision conditionnelle reste :

\[
\boxed{100\%}
\]

sur ce holdout indépendant.

C’est un très bon signal.

---

# 6. Première conclusion méthodologique forte

Notre objectif ne doit pas être :

\[
\max \text{coverage}
\]

mais :

\[
\boxed{
\max \text{coverage}
\quad
\text{sous contrainte de très forte précision}
}
\]

Autrement dit :

> lorsqu’une règle répond, elle doit être presque certaine.

Sinon :

\[
\text{LLM}.
\]

Cette philosophie est à conserver jusqu’à la fin du projet.

---

# 7. Autre résultat important : exécution du code LLM

Le règlement actuel indique qu’il faut utiliser :

```python
dsh.run_python(...)
```

pour exécuter le code généré et éviter un `exec(...)` dans l’upload.

Stage 3 contient encore un `exec(code, ns)`.

La version actuellement live a manifestement été acceptée, mais je ne construirais pas notre nouvelle soumission autour de cette hypothèse.

J’ai donc testé les variantes conformes utilisant `dsh.run_python`.

Et là nous avons découvert un problème de performance.

## `safe_v2`

Stress test avec 8 tâches toutes inconnues, donc toutes envoyées au fallback :

\[
\boxed{27.8\,s}
\]

rien que pour l’orchestration/exécution avec une génération simulée quasi gratuite.

Notre budget interne est :

\[
29\,s.
\]

Donc :

\[
\boxed{\text{safe\_v2 est trop risquée}}
\]

pour la production.

---

# 8. Pourquoi `safe_v3` est meilleure

`safe_v3` regroupe les quatre programmes issus du sampling dans **un seul subprocess** par tâche.

Coût observé :

| Nombre de tâches fallback | Overhead approximatif |
|---:|---:|
| 1 | 2.7 s |
| 2 | 5.3 s |
| 4 | 10.4 s |
| 8 | 21.9 s |

Pour 8 tâches inconnues, c’est encore relativement lourd, mais bien meilleur que `safe_v2`.

Et surtout le privé ne contient pas normalement 8 types inconnus à chaque batch.

Nous savons qu’il y a environ :

\[
20
\]

Tables private-only sur :

\[
120
\]

tâches.

Donc le nombre moyen de private-only par batch de 8 vaut :

\[
8\times\frac{20}{120}
=
1.33.
\]

Sous une répartition aléatoire, la probabilité d’avoir au moins quatre de ces 20 tâches dans un même batch de huit est seulement d’environ :

\[
2.6\%.
\]

La situation typique devrait donc être :

\[
1\text{ à }2
\]

fallbacks de ce type dans un batch, pas huit.

Cela rend l’architecture beaucoup plus raisonnable.

---

# 9. Mais `candidate_v6` n’est pas encore « final »

J’ai détecté un dernier sujet à régler avant de la qualifier de candidate leaderboard.

Le prompt et le runtime subprocess doivent promettre exactement les mêmes outils.

Actuellement, par exemple :

### No-files

Le prompt annonce :

```text
sympy
```

mais le subprocess sécurisé ne l’importe pas systématiquement.

### Fits

Le prompt dit que `LinearRegression` et `LogisticRegression` savent automatiquement gérer certaines catégories via votre wrapper.

Mais le subprocess sécurisé utilise actuellement les classes sklearn brutes.

Cela crée ce qu’on peut appeler un :

\[
\boxed{\text{tool-contract mismatch}}
\]

Le LLM croit avoir un outil qu’il n’a pas exactement.

Sur le dev cela ne se voit pas car :

\[
35/35
\]

Fits passent par le solveur déterministe.

Mais sur une tâche privée Fit atypique, cela peut compter.

Donc `candidate_v6` est aujourd’hui :

\[
\boxed{\text{candidate prometteuse, pas encore champion}}
\]

et Stage 3 reste :

\[
\boxed{\text{champion}}
\]

jusqu’à validation finale.

---

# 10. Oui : presque tout doit être fait localement avant de push

Et je veux être très strict là-dessus.

Le pipeline doit être :

\[
\boxed{
\text{idée}
\rightarrow
\text{tests unitaires}
\rightarrow
\text{dev}
\rightarrow
\text{métamorphique}
\rightarrow
\text{OOD1}
\rightarrow
\text{OOD2}
\rightarrow
\text{runtime}
\rightarrow
\text{test-run ML-Arena}
\rightarrow
\text{private}
}
\]

et **jamais** :

\[
\text{idée}
\rightarrow
\text{private leaderboard}.
\]

Le leaderboard privé est notre test final extrêmement coûteux en information.

---

# 11. Les métriques à enregistrer dorénavant

Pour chaque version \(V_k\), nous devons avoir une vraie fiche expérimentale.

Je propose six métriques principales.

### M1 — Dev accuracy

\[
A_{\text{dev}}
=
\frac{\#\text{tâches correctes}}{180}
\]

Cible :

\[
\boxed{100\%}
\]

pour nos nouvelles candidates.

### M2 — Deterministic coverage

\[
C_{\text{det}}
=
\frac{\#\text{tâches résolues sans LLM}}{N}
\]

Mais ce chiffre seul est dangereux.

### M3 — Deterministic precision

\[
P_{\text{det}}
=
\frac{\#\text{réponses déterministes correctes}}
{\#\text{réponses déterministes produites}}
\]

C’est probablement notre métrique la plus importante.

Cible :

\[
\boxed{\approx100\%}
\]

### M4 — OOD false-positive rate

\[
FPR_{\text{OOD}}
=
\frac{
\#\text{tâches OOD répondues faussement par une règle}
}{
N_{\text{OOD}}
}
\]

Cible :

\[
\boxed{0}
\]

ou le plus proche possible.

### M5 — Runtime

Par batch :

- médiane ;
- p90 ;
- maximum ;
- nombre de fallback LLM.

Il faut surtout surveiller :

\[
T_{\max}<40s
\]

avec une marge confortable.

### M6 — Private leaderboard

Seulement après les autres.

On note :

- score total ;
- No-files ;
- Tables ;
- Fits ;
- temps max ;
- date ;
- commit/version exacte.

---

# 12. Une métrique supplémentaire très intéressante pour l’oral

Je veux aussi mesurer le **taux d’abstention correct**.

Sur OOD2, par exemple :

\[
100/120
\]

tâches ne sont pas couvertes par les règles.

Ce n’est pas nécessairement un échec.

Si ces tâches sont réellement hors du domaine de compétence déterministe, c’est même souhaitable.

On peut mesurer :

\[
\text{Selective risk}
=
1-P_{\text{det}}.
\]

L’objectif est d’obtenir :

\[
\boxed{
\text{Selective risk}\approx0
}
\]

tout en augmentant progressivement la couverture.

C’est une manière beaucoup plus scientifique de présenter votre système.

---

# 13. Les questions de recherche à suivre

À partir de maintenant, chaque phase doit répondre à une question.

### Q1 — Peut-on retirer encore du travail au LLM sans augmenter les faux positifs ?

On a déjà une première réponse :

Oui pour No-files, **mais uniquement avec parsing sélectif**.

### Q2 — Les six erreurs Tables privées viennent-elles principalement de types private-only ?

Très probablement, mais ce n’est pas observé directement.

Notre moyen de progresser :

OOD indépendant + fallback LLM plus robuste.

### Q3 — Est-il préférable d’ajouter davantage de règles Tables ?

Pour l’instant :

\[
\boxed{\text{pas agressivement}}
\]

car OOD2 montre qu’une bonne abstention est propre.

Je privilégierais maintenant l’amélioration du fallback générique.

### Q4 — Le LLM reçoit-il exactement les bonnes informations ?

À mesurer :

- taille du prompt ;
- colonnes ;
- dictionnaire ;
- sample rows ;
- join hints ;
- bruit inutile.

### Q5 — Le contrat d’outil est-il exact ?

Si le prompt dit :

> sympy est disponible

alors :

\[
\text{sympy doit réellement être disponible}.
\]

### Q6 — Le sampling apporte-t-il réellement quelque chose ?

Il faudra tester :

\[
1\text{ greedy}
\]

contre :

\[
1\text{ greedy} + 2\text{ samples}
\]

contre :

\[
1+4
\]

sur un vrai environnement Qwen.

### Q7 — Le repair apporte-t-il assez pour son coût ?

Même principe :

\[
\text{repair ON}
\quad vs \quad
\text{repair OFF}.
\]

---

# 14. Organisation des deux membres

Vous êtes deux, donc **ne travaillez pas tous les deux dans `agent.py` en même temps**.

Je répartirais le travail par responsabilité scientifique.

## Personne A — Core / Performance

Responsable de :

- `agent.py` / candidates ;
- règles déterministes ;
- parsing ;
- routing ;
- LLM fallback ;
- runtime ;
- profiling ;
- création des versions candidate ;
- analyse des erreurs techniques.

Autrement dit :

\[
\boxed{\text{BUILD}}
\]

## Personne B — Evaluation / Red Team

Responsable de :

- runner local ;
- résultats ;
- stress tests ;
- OOD ;
- transformations métamorphiques ;
- détection des régressions ;
- journal d’expériences ;
- tableaux pour l’oral ;
- reproduction indépendante des résultats.

Autrement dit :

\[
\boxed{\text{BREAK + MEASURE}}
\]

C’est beaucoup mieux que « chacun code la moitié ».

---

# 15. Très important : la personne B doit essayer de casser le travail de A

Exemple.

A écrit une nouvelle règle pour :

> weighted mean.

B ne lui donne pas seulement un test ressemblant au dev.

B invente :

- colonne distractrice ;
- missing values ;
- unité différente ;
- phrase inutile ;
- autre formulation ;
- deux variables aux descriptions proches ;
- poids nuls ;
- group filter ;
- doublons.

Si la règle répond alors qu’elle devrait s’abstenir :

\[
\boxed{\text{on ne merge pas}}
\]

C’est exactement une logique Champion/Challenger.

---

# 16. Workflow Git recommandé

Gardez toujours une branche stable :

```text
main
```

ou :

```text
leaderboard/champion
```

contenant exactement Stage 3 actuellement live.

Puis :

```text
candidate/no-files-safe
candidate/tool-runtime
candidate/table-generalization
candidate/prompt
```

Chaque candidat doit correspondre à **une seule hypothèse principale**.

Pas :

> j’ai changé 14 trucs et le score a augmenté.

Sinon O3 devient impossible à défendre.

---

# 17. Planning à partir d’aujourd’hui — 15 octobre

La deadline leaderboard/slides est le **3 novembre 2026 à 23:59**.

Il reste environ 19 jours.

Je découperais le travail ainsi.

## 15–17 octobre — Instrumentation et baseline

Objectif :

\[
\boxed{\text{ne plus jamais expérimenter sans mesure}}
\]

Personne A :

- figer Stage 3 ;
- nettoyer candidate v6 ;
- aligner prompt et runtime ;
- conserver strictement les fallbacks.

Personne B :

- mettre en place le runner ;
- dev ;
- métamorphiques ;
- OOD1 ;
- OOD2 ;
- journal expérimental.

Livrable au 17 :

une commande doit produire automatiquement quelque chose comme :

```text
candidate: vX

DEV
180/180

Deterministic
180/180
false positives: 0

OOD1
80/80

OOD2
coverage: 20/120
precision: 20/20
false positives: 0

Runtime stress
1 fallback ...
2 fallback ...
4 fallback ...
8 fallback ...
```

---

# 18. 18–21 octobre — sécuriser No-files et Fits

Pourquoi eux en premier ?

Parce que les gains semblent les moins risqués.

No-files privé :

\[
43/45.
\]

Fits :

\[
24/25.
\]

Hypothèse :

> La meilleure version No-files déterministe peut récupérer 1–2 points sans affecter Tables.

Personne A :

- finaliser No-files safe ;
- stress-test Fits ;
- vérifier exactement les wrappers sklearn ;
- aligner subprocess.

Personne B :

- générer de nouveaux distracteurs ;
- paraphrases ;
- missing tokens ;
- changements d’unités ;
- cas limites Fits.

À la fin :

un candidat doit être supérieur à Stage 3 sur les capacités **sans aucune régression locale observée**.

---

# 19. Première soumission utile : pas avant ça

À ce moment-là seulement, je ferais une soumission candidate.

Et je changerais le **minimum possible**.

Exemple :

### Submission S4-A

Stage 3 +

- No-files safe ;
- nettoyage distracteurs ;
- runtime conforme.

Pas encore dix nouvelles familles Tables.

Pourquoi ?

Si le score passe :

\[
92.5\rightarrow94.2
\]

on saura presque exactement pourquoi.

Si on change tout en même temps et obtient :

\[
95.0,
\]

on ne saura pas ce qui a fonctionné.

---

# 20. 22–26 octobre — attaque du vrai problème Tables

À ce stade on commence le principal travail leaderboard.

Question centrale :

\[
\boxed{
\text{Comment améliorer les private-only Tables ?}
}
\]

Je ne commencerais pas par 50 nouvelles regex.

Je commencerais par le fallback.

Axes :

- meilleure représentation compacte ;
- meilleure compréhension du dictionnaire ;
- meilleurs hints de jointure ;
- prompting par capability ;
- validators ;
- exécution ;
- repair ;
- sampling.

Personne A travaille sur le fallback.

Personne B invente constamment de nouveaux OOD aveugles.

---

# 21. Règle stricte pour ajouter un nouveau solveur Tables

Une nouvelle capacité déterministe n’est acceptée que si :

\[
\text{precision dev}=100\%
\]

et :

\[
\text{precision stress}=100\%
\]

et :

\[
\text{false positive holdout}=0
\]

sur les tests disponibles.

Sinon :

\[
\boxed{\text{on préfère le LLM}}
\]

---

# 22. 27–29 octobre — ablations pour l’oral

À ce moment-là, il faut presque arrêter d’inventer de nouveaux composants.

On veut répondre scientifiquement à :

> Qu’est-ce qui apporte vraiment le score ?

Ablations importantes :

### A1

Full system vs sans deterministic solvers.

### A2

Repair ON/OFF.

### A3

Sampling 1 / 2 / 4.

### A4

Old prompt vs new prompt.

### A5

Raw tables vs cleaned compact view.

### A6

Avec/sans distractor cleanup.

### A7

Avec/sans extended No-files.

Même si toutes les ablations ne passent pas sur le privé, dev/OOD suffisent pour construire l’histoire.

---

# 23. 30 octobre – 1er novembre — freeze technique

À partir de là :

\[
\boxed{\text{plus de refactor massif}}
\]

Seulement :

- bug fixes ;
- runtime ;
- packaging ;
- tests de régression.

On choisit le meilleur champion.

On fait idéalement plusieurs runs locaux avec exactement le même ordre de batch que le scorer.

---

# 24. 1er–2 novembre — dernière validation leaderboard

À ce stade, on choisit entre :

\[
Champion
\]

et au maximum :

\[
1\text{ ou }2\text{ challengers réellement justifiés}.
\]

Pas dix soumissions désordonnées.

Pour chacune :

```text
Hypothesis
Local dev
OOD
Runtime
Expected gain
Private score
Conclusion
```

---

# 25. 2–3 novembre — oral et slides

Pendant que l’un finalise les tests de packaging, l’autre construit déjà le deck.

Je viserais environ **11–13 slides**, pas 15 remplies.

Par exemple :

1. DS-Harness et problématique ;
2. pourquoi le petit LLM échoue ;
3. baseline ;
4. architecture générale ;
5. robust data layer ;
6. deterministic routing ;
7. LLM fallback + execution ;
8. repair / sampling ;
9. méthodologie d’évaluation ;
10. résultats / ablations ;
11. OOD et découverte du surapprentissage ;
12. système final ;
13. failures + perspectives.

Les deux membres doivent comprendre **tout** le pipeline.

---

# 26. Journal expérimental obligatoire

À partir de maintenant, chaque expérience doit donner une ligne.

| ID | Hypothèse | Modification | Dev | OOD1 | OOD2 FP | Runtime | Private | Décision |
|---|---|---|---:|---:|---:|---:|---:|---|
| S3 | baseline | Stage 3 | — | — | 0 | 23.7 max | 92.5 | Champion |
| E01 | déterminiser No-files | naïf | 180/180 | — | — | — | — | Reject |
| E02 | nettoyer distracteurs | v6 | 180/180 | 80/80 | 0 | OK | ? | Candidate |

Ce tableau va quasiment fabriquer O3/O5 à votre place.

---

# 27. Qui fait quoi concrètement dès maintenant

Je ferais cette répartition.

### Toi — branche Agent / Champion-Challenger

Tu t’occupes de :

- comprendre chaque modification ;
- intégrer seulement les modifications validées ;
- tester le vrai Qwen / ML-Arena ;
- tenir les versions de soumission ;
- vérifier les logs et le leaderboard.

### Ton binôme — branche Evaluation / Red Team

Il s’occupe de :

- lancer tous les tests locaux ;
- inventer des stress tests indépendants ;
- tenir le CSV/Markdown des expériences ;
- construire les tableaux et figures ;
- essayer de casser tes nouvelles règles.

Puis vous échangez régulièrement les rôles pour que chacun sache expliquer toute l’architecture.

---

# 28. Ce que je ferais comme prochaine expérience réelle

Je **ne pousserais encore rien aujourd’hui**.

La prochaine phase est très précise :

> **H1 — Peut-on remplacer Stage 3 par une candidate conforme à `dsh.run_python`, avec le nouveau No-files safe, sans dégrader le fallback LLM ni dépasser le budget ?**

Critères d’acceptation :

\[
\boxed{180/180\ dev}
\]

\[
\boxed{80/80\ OOD1}
\]

\[
\boxed{0\ faux\ positif\ sur\ OOD2}
\]

\[
\boxed{0\ faux\ positif\ métamorphique}
\]

et runtime raisonnable avec :

\[
1,\ 2,\ 4
\]

fallbacks.

Ensuite seulement :

\[
\boxed{\text{premier push contrôlé}}
\]

---

# 29. Et oui, le local doit devenir votre environnement principal

Dans votre machine/Colab, le setup de référence est bien celui-ci, avec une correction importante :

```python
CHALLENGE_ID = 194
```

et non 192.

Puis :

```bash
python localtest.py agent.py
```

pour les 180 tâches,

```bash
python localtest.py agent.py --test-run
```

pour reproduire les 16 tâches du test-run ML-Arena,

et :

```bash
python localtest.py agent.py --out run.json
```

pour obtenir le résultat **tâche par tâche**. 

C’est cela qui doit devenir votre boucle quotidienne, pas le leaderboard.

---

# 30. Un point sécurité avant de continuer

Tu as copié dans ton message une **clé API ML-Arena et des identifiants PostgreSQL complets**.

Même si tu m’as explicitement autorisé à les utiliser, ils ne sont pas nécessaires pour les expériences que nous faisons et je ne les ai pas utilisés.

Je te conseille de les **révoquer / régénérer immédiatement**, surtout les deux mots de passe PostgreSQL et la clé ML-Arena, puisqu’ils ont maintenant été exposés dans le contenu d’une conversation.

Pour DS-Harness, la base PostgreSQL que tu as collée est d’ailleurs sans rapport avec le challenge 194.

---

## Le plan en une phrase

À partir de maintenant :

\[
\boxed{
\text{Champion Stage 3}
\rightarrow
\text{hypothèse unique}
\rightarrow
\text{candidate}
\rightarrow
\text{dev}
\rightarrow
\text{stress}
\rightarrow
\text{OOD aveugle}
\rightarrow
\text{runtime}
\rightarrow
\text{ML-Arena}
}
\]

et les deux rôles sont :

\[
\boxed{
\text{Membre A = Build}
\qquad
\text{Membre B = Break + Measure}
}
\]

C’est à mon avis le meilleur compromis entre **gagner le leaderboard**, **ne pas overfitter les 180 tâches**, et surtout accumuler exactement les preuves expérimentales dont vous aurez besoin pour les 75 % de soutenance.