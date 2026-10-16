# Rapport complet — Projet DS-Harness

## 1. Contexte général

Le projet du cours **Machine Learning en pratique** repose sur un challenge unique : **DS-Harness**.

L’objectif n’est pas simplement d’utiliser un LLM pour répondre à des questions de data science. Il faut partir d’un **petit modèle de langage volontairement limité** — environ 1,5 milliard de paramètres — et construire autour de lui un système suffisamment intelligent et fiable pour résoudre automatiquement des tâches de data science qu’il ne pourrait pas résoudre seul.

Le projet porte donc avant tout sur la **conception du système autour du LLM**, autrement dit le *harness*.

Ce système doit notamment décider :

- comment lire l’objectif ;
- comment lire et nettoyer les fichiers ;
- comment reconnaître le type de problème ;
- quelles informations transmettre au LLM ;
- quels outils lui fournir ;
- comment exécuter son code ;
- comment détecter et réparer les erreurs ;
- comment vérifier la réponse ;
- comment utiliser efficacement le budget de calcul.

Le principe fondamental du challenge peut être résumé ainsi :

$$
\boxed{
\text{Performance du système}
\neq
\text{Performance brute du LLM}
}
$$

Le véritable problème est donc :

$$
\boxed{
\text{Comment transformer un petit LLM peu fiable en data scientist autonome fiable ?}
}
$$

---

# 2. Ce qui est évalué

La note finale comporte deux parties.

| Élément | Poids |
|---|---:|
| Leaderboard | 25 % |
| Soutenance orale | 75 % |

La soutenance est elle-même divisée en cinq critères :

| Critère | Contenu | Poids dans l’oral |
|---|---|---:|
| O1 | Problème et méthodologie | 20 % |
| O2 | Design du système | 30 % |
| O3 | Méthodologie d’évaluation | 30 % |
| O4 | Meilleure solution clairement identifiée | 10 % |
| O5 | Analyse des échecs et améliorations | 10 % |

Les critères O2 et O3 représentent ensemble 60 % de l’oral.

Comme l’oral représente 75 % de la note finale :

$$
0.75 \times (0.30 + 0.30) = 0.45
$$

Ainsi :

$$
\boxed{
45\% \text{ de la note finale dépend directement du design et de l'évaluation du système.}
}
$$

Il ne suffit donc pas d’obtenir un bon leaderboard.

Il faut aussi pouvoir montrer :

- pourquoi chaque composant existe ;
- quelle faiblesse il corrige ;
- comment son apport a été mesuré ;
- quelles expériences ont été réalisées ;
- quelles limites subsistent.

La bonne logique expérimentale est :

$$
\boxed{
\text{Hypothèse}
\rightarrow
\text{Modification}
\rightarrow
\text{Expérience}
\rightarrow
\text{Résultat}
\rightarrow
\text{Décision}
}
$$

---

# 3. Contrat exact du challenge

La plateforme appelle :

```python
Agent.solve(tasks)
```

avec une liste de **8 tâches**.

Une tâche ressemble à :

```python
{
    "id": "p_042",
    "objective": "...",
    "files": [...]
}
```

L’agent reçoit uniquement :

- l’identifiant ;
- l’objectif en anglais ;
- les chemins des fichiers disponibles.

Il **ne reçoit pas** :

- le type de tâche ;
- la réponse attendue ;
- la tolérance ;
- la famille réelle.

Il doit donc reconnaître lui-même le problème.

La sortie doit être de la forme :

```python
[
    {"id": "p_042", "answer": 0.437},
    ...
]
```

Chaque réponse doit être **un seul nombre**.

Des réponses comme :

```text
41.07
-3
1e-3
```

sont valides.

En revanche :

```text
12 kg
1,200
None
[12]
```

produisent une erreur de format.

Votre Stage 3 obtient actuellement :

$$
\boxed{
120/120 \text{ tâches répondues}
}
$$

et :

$$
\boxed{
0 \text{ erreur de format}
}
$$

Cette partie du problème est donc déjà très bien maîtrisée.

---

# 4. Fonction de score exacte

Le scorer attribue à chaque tâche un score binaire.

Pour une tâche \(i\) :

$$
s_i =
\begin{cases}
1, & \text{si } |\hat y_i-y_i| \leq \text{tol}_i \\
0, & \text{sinon}
\end{cases}
$$

Le score total est :

$$
\boxed{
\text{Score}
=
100\times\frac{1}{N}\sum_{i=1}^{N}s_i
}
$$

Il n’existe **aucun crédit partiel**.

Une réponse légèrement hors tolérance rapporte exactement autant qu’une réponse complètement fausse :

$$
0.
$$

Lorsque la réponse doit être arrondie à \(n\) décimales :

$$
\boxed{
\text{tolérance}
=
1.5\times10^{-n}
}
$$

Pour une réponse entière :

$$
\boxed{
\text{tolérance}
=
10^{-6}
}
$$

---

# 5. Conséquence sur votre score actuel

Le privé contient :

$$
N=120
$$

tâches.

Une seule tâche vaut donc :

$$
\frac{100}{120}
=
0.8333\ldots
$$

point de leaderboard.

Votre score est actuellement :

$$
92.5.
$$

Cela correspond exactement à :

$$
92.5\times\frac{120}{100}
=
111.
$$

Donc :

$$
\boxed{
111/120 \text{ tâches privées sont actuellement correctes.}
}
$$

Et seulement :

$$
\boxed{
9 \text{ tâches sont encore incorrectes.}
}
$$

À ce niveau, notre problème n’est donc plus de construire entièrement un nouvel agent.

Notre problème devient :

$$
\boxed{
\text{Identifier les quelques capacités manquantes sans casser les 111 réponses déjà correctes.}
}
$$

---

# 6. Les trois grandes familles de tâches

Le benchmark contient trois familles.

## 6.1. No files

Toutes les informations sont données directement dans l’objectif.

Les types publics sont notamment :

```text
calc.arithmetic
calc.stats_inline
calc.percent
calc.growth
calc.functions
calc.dates
calc.integer
calc.word
calc.probability
```

Ils couvrent par exemple :

- arithmétique ;
- moyenne, médiane, variance ;
- pourcentages ;
- croissance ;
- logarithmes ;
- racines ;
- dates ;
- problèmes de nombres entiers ;
- problèmes verbaux ;
- probabilités.

---

## 6.2. Tables

Une ou deux tables CSV doivent être lues puis manipulées.

Les cinq types publics présents dans `dev.json` sont :

```text
table.stat
table.filter
table.group
table.join
table.derive
```

Cela correspond principalement à :

$$
\text{statistique}
$$

$$
\text{filtrage}
$$

$$
\text{groupby / agrégation}
$$

$$
\text{jointure}
$$

$$
\text{colonne dérivée}
$$

Les données sont volontairement difficiles.

On peut rencontrer :

- séparateur `;` ;
- virgules décimales ;
- différentes représentations des valeurs manquantes ;
- unités dans les cellules ;
- doublons ;
- dates ambiguës ;
- clés avec préfixes ;
- casse différente ;
- codes opaques ;
- colonnes inutiles ;
- colonnes introduisant une fuite d’information.

---

## 6.3. Fits

Il faut reproduire exactement une procédure de régression.

Les types publics sont :

```text
fit.linear
fit.logistic
```

L’objectif peut demander :

- une prédiction ;
- une probabilité ;
- un coefficient ;
- un intercept ;
- un \(R^2\) ;
- le nombre de lignes effectivement utilisées.

Le problème ne consiste donc pas simplement à écrire :

```python
model.fit(X, y)
```

Il faut également déterminer correctement :

- la cible ;
- les prédicteurs ;
- les lignes admissibles ;
- les variables interdites ;
- la régularisation ;
- le filtre temporel éventuel ;
- la ligne de test demandée.

---

# 7. Composition du jeu public

Nous disposons désormais du `dev.json` complet.

Il contient :

$$
\boxed{
180 \text{ tâches publiques}
}
$$

réparties ainsi :

| Famille | Nombre |
|---|---:|
| No files | 65 |
| Tables | 80 |
| Fits | 35 |
| **Total** | **180** |

Ainsi :

$$
65+80+35=180.
$$

---

# 8. Composition du jeu privé

Le dataset privé contient :

| Famille | Nombre |
|---|---:|
| No files | 45 |
| Tables | 50 |
| Fits | 25 |
| **Total** | **120** |

Donc :

$$
45+50+25=120.
$$

---

# 9. Particularité fondamentale du privé : l’out-of-distribution

C’est probablement l’information la plus importante du challenge.

Le privé n’est pas simplement un nouveau tirage parfaitement identique au dev.

La documentation officielle précise que certaines tâches Tables du privé utilisent des **types qui ne sont pas présents dans `dev.json`**.

Le courseware indique plus précisément que, parmi les 50 tâches Tables privées :

$$
\boxed{
20
}
$$

proviennent de types **private-only**.

On peut donc approximativement penser le privé Tables comme :

$$
50
=
30 \text{ tâches proches des types connus}
+
20 \text{ tâches issues de types inconnus}.
$$

C’est essentiel.

Le challenge teste volontairement :

$$
\boxed{
\text{la généralisation hors distribution}
}
$$

et pas seulement :

$$
\text{la capacité à reproduire les templates publics}.
$$

---

# 10. Autre particularité du benchmark : les réponses proches de zéro

Le générateur officiel redessine les tâches dont la réponse gold serait trop proche de zéro.

Ainsi, retourner :

```python
answer = 0.0
```

peut être utile comme mécanisme de sécurité pour éviter une exception, mais ce n’est presque jamais une stratégie permettant de gagner accidentellement le point.

Le fallback `0.0` doit donc être compris comme :

$$
\boxed{
\text{sécurité d'exécution}
}
$$

et non comme :

$$
\text{stratégie de prédiction}.
$$

---

# 11. Contraintes de temps

L’initialisation :

```python
Agent()
```

dispose de :

$$
60\text{ s}.
$$

Chaque appel :

```python
solve(8_tasks)
```

dispose de :

$$
40\text{ s}.
$$

Le run privé comporte :

$$
15
$$

appels de 8 tâches.

Donc :

$$
15\times8=120.
$$

Le code officiel confirme :

```python
BATCH_SIZE = 8
CALL_TIMEOUT_S = 40.0
LOAD_TIMEOUT_S = 60.0
```

La véritable contrainte est donc :

$$
\boxed{
40 \text{ secondes pour résoudre un batch de 8 tâches.}
}
$$

---

# 12. Ressources matérielles

La machine fournit :

- RTX 4090 ;
- 24 GiB de VRAM ;
- 3 CPU ;
- 3 GiB de RAM ;
- `/tmp` limité à 128 MB ;
- aucun réseau.

Les modèles autorisés sont :

```text
Qwen/Qwen2.5-0.5B-Instruct
Qwen/Qwen2.5-1.5B-Instruct
Qwen/Qwen2.5-Coder-1.5B-Instruct
deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B
Qwen/Qwen3-1.7B
```

Les principales bibliothèques disponibles comprennent :

```text
PyTorch
Transformers
NumPy
Pandas
SciPy
scikit-learn
SymPy
```

---

# 13. Architecture générale de votre Stage 3

Votre Stage 3 n’est pas un simple agent LLM.

Son principe peut être résumé par :

> Le LLM n’écrit que du code ; le système fait le reste.

L’architecture est approximativement :

```text
                 ┌─────────────────┐
                 │      Task       │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │     Router      │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Lecture / clean │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Solveur détermin│
                 └────────┬────────┘
                          │
                 réponse sûre ?
                    /           \
                  oui           non
                   │             │
                   ▼             ▼
                réponse     LLM coder
                                 │
                                 ▼
                           Exécution Python
                                 │
                           succès ?
                           /       \
                         oui       non
                          │         │
                          │         ▼
                          │      Repair
                          │         │
                          └────┬────┘
                               ▼
                         Sampling / vote
                               │
                               ▼
                            Réponse
```

Le système suit donc une philosophie hybride :

$$
\boxed{
\text{solveurs déterministes}
+
\text{LLM de secours}
}
$$

---

# 14. Le routeur

Le routage grossier repose sur une règle très simple.

### Aucun fichier

$$
\Rightarrow
\text{No files}
$$

### Présence de `train.csv`

$$
\Rightarrow
\text{Fit}
$$

### Sinon

$$
\Rightarrow
\text{Table}
$$

C’est une décision très importante.

Le système ne demande pas au LLM :

> Quel est le type de cette tâche ?

alors que l’information peut être déterminée presque parfaitement par Python.

Cela illustre l’un de nos principes fondamentaux :

$$
\boxed{
\text{Ne jamais demander au LLM ce que le programme peut déterminer de manière fiable.}
}
$$

---

# 15. Lecture robuste des CSV

L’agent commence par normaliser les données.

Il détecte automatiquement le séparateur parmi :

```text
,
;
\t
|
```

Il traite notamment les représentations suivantes comme valeurs manquantes :

```text
""
na
n/a
nan
null
none
-
--
?
missing
.
n.a.
#n/a
unknown
```

Il interprète également des nombres comme :

```text
1 234,5 kg
1,234.5
3,14
```

et peut les convertir correctement en valeurs numériques.

---

# 16. Les instructions de l’objectif servent aussi à parser les données

L’objectif n’est pas uniquement la question finale.

Il contient souvent les règles de lecture.

Par exemple :

> Missing values are written 'nd'.

ou :

> Value -1 means not recorded.

Votre agent essaie de reconnaître ces instructions et transforme les valeurs correspondantes en :

```python
NaN
```

avant la résolution.

C’est un point méthodologique très important :

$$
\boxed{
\text{Objective}
=
\text{Question}
+
\text{Spécification du traitement des données}
}
$$

---

# 17. Gestion des doublons

Lorsque l’objectif indique que certaines observations apparaissent plusieurs fois, Stage 3 recherche un identifiant plausible puis applique une déduplication.

Cela évite de dépendre du LLM pour une instruction aussi déterministe.

---

# 18. Le dictionnaire de données est central

Les noms de colonnes sont volontairement opaques.

Par exemple :

```text
amt_k
dpt
PX
readm30
```

L’objectif parlera pourtant de :

> amount billed

ou :

> department.

Le système doit donc effectuer :

$$
\text{expression naturelle}
\rightarrow
\text{description du dictionnaire}
\rightarrow
\text{code de colonne}.
$$

Cette résolution sémantique est une capacité fondamentale du challenge.

---

# 19. Principe d’abstention

Si deux colonnes semblent également plausibles, votre résolveur peut retourner :

```python
None
```

plutôt que de choisir arbitrairement.

C’est très important.

Une règle déterministe incorrecte est dangereuse car elle empêche ensuite le LLM de corriger la tâche.

Le bon principe est donc :

$$
\boxed{
\text{Une règle déterministe doit être très précise, même si elle couvre moins de tâches.}
}
$$

ou encore :

$$
\boxed{
\text{Abstention fiable}
>
\text{Réponse automatique douteuse}
}
$$

---

# 20. Jointures

Les jointures sont volontairement difficiles.

Une table peut contenir :

```text
SITE-S02
```

et l’autre :

```text
S02.
```

Stage 3 essaie plusieurs représentations :

- original ;
- minuscules ;
- normalisation Unicode ;
- suppression d’accents ;
- suppression de ponctuation ;
- retrait de préfixes ;
- variantes numériques.

L’objectif est d’identifier une transformation des clés qui maximise les correspondances sans introduire d’ambiguïté.

---

# 21. Première couche de résolution : déterministe

Avant d’utiliser le LLM, Stage 3 appelle différents solveurs.

### No files

```python
calc_rules(...)
```

### Tables

```python
table_stat_rule(...)
table_group_rule(...)
table_join_rule(...)
table_derive_rule(...)
table_filter_rule(...)
```

### Fits

```python
fit_rules(...)
```

Si une règle retourne un résultat fiable :

$$
\boxed{
\text{le LLM n'est pas appelé}
}
$$

pour cette tâche.

C’est probablement la décision architecturale qui explique la majeure partie du score actuel.

---

# 22. Pourquoi cette stratégie fonctionne

Un petit LLM est relativement mauvais pour :

- effectuer exactement des calculs ;
- parcourir des centaines de lignes ;
- respecter précisément une procédure sklearn ;
- gérer les valeurs manquantes ;
- faire des jointures complexes ;
- toujours respecter le format.

À l’inverse, Python est excellent pour ces opérations.

Le LLM est donc réservé aux problèmes où une compréhension plus flexible est nécessaire.

La bonne séparation est :

$$
\boxed{
\text{Python calcule}
}
$$

et :

$$
\boxed{
\text{le LLM interprète lorsque l'interprétation déterministe ne suffit pas.}
}
$$

---

# 23. Les règles Tables

Les règles Tables possèdent déjà une logique importante.

Elles savent notamment gérer :

- statistiques simples ;
- comptages ;
- valeurs uniques ;
- filtres ;
- statistiques d’ordre ;
- groupby ;
- minimum / maximum ;
- moyenne / médiane ;
- variance / écart-type ;
- ratios ;
- jointures.

Par exemple, une requête comme :

> second highest score

est traitée sur les **valeurs distinctes**.

Une tâche du type :

> Consider the debt-to-income ratio...

est transformée en :

$$
r_i=
\frac{\text{debt}_i}
{\text{income}_i}
$$

puis l’agrégation demandée est appliquée sur les \(r_i\).

---

# 24. Les règles Fits

Pour Fits, le système essaie de reproduire précisément les modèles demandés.

Pour une logistique sans régularisation, Stage 3 utilise notamment une configuration du type :

```python
penalty = None
solver = "lbfgs"
tol = 1e-9
```

avec un nombre important d’itérations.

Cela est important car une petite différence numérique peut faire sortir la prédiction de la tolérance.

Le système gère également des cibles textuelles telles que :

```text
yes
y
true
1
```

et les transforme en classe positive.

---

# 25. Le LLM devient un fallback

Lorsque toutes les règles déterministes s’abstiennent, Stage 3 construit un prompt pour :

```text
Qwen/Qwen2.5-Coder-1.5B-Instruct
```

Le modèle n’a pas pour mission de répondre directement au problème.

Il doit écrire un court programme Python.

Le prompt lui impose notamment :

- uniquement du code ;
- une variable finale `answer` ;
- aucune explication ;
- aucune lecture de fichier ;
- aucun import ;
- pas d’arrondi manuel ;
- utilisation des DataFrames déjà préparés.

Ainsi, le problème du LLM devient beaucoup plus petit :

$$
\boxed{
\text{objectif naturel}
\rightarrow
\text{petit programme Python}
}
$$

---

# 26. Réduction de l’espace de décision du modèle

Au lieu de lui envoyer les fichiers bruts, le système peut lui fournir :

- les dimensions des tables ;
- les noms exacts des colonnes ;
- les types ;
- les missing rates ;
- quelques lignes ;
- le dictionnaire ;
- des hints de jointure ;
- l’objectif ;
- un exemple few-shot.

On passe donc de :

$$
\text{« Comprends tout le dataset »}
$$

à :

$$
\text{« Choisis quelques opérations Python dans un environnement déjà préparé »}.
$$

Cette réduction de l’espace de décision est l’une des clés du succès.

---

# 27. Génération GPU par batch

Les tâches encore confiées au LLM sont générées ensemble.

Cette stratégie est beaucoup plus efficace que huit appels séquentiels.

Elle exploite correctement le GPU et préserve le budget de 40 secondes.

---

# 28. Première génération gloutonne

Le système commence avec :

$$
T=0
$$

c’est-à-dire une génération déterministe.

Cette première proposition a une priorité élevée.

Ensuite seulement viennent :

- reprise des générations tronquées ;
- réparation ;
- échantillonnage supplémentaire.

---

# 29. Réparation des programmes tronqués

Lorsque la génération atteint sa limite de tokens avant la fin du programme, Stage 3 mémorise le texte partiel.

Une seconde génération reprend ensuite le programme à partir de là.

Le nombre maximal de nouveaux tokens a été porté à :

$$
500.
$$

Cette correction répond directement à un mode d’échec observé.

---

# 30. Boucle de réparation

Si le programme généré plante, Stage 3 conserve :

- le code ;
- l’exception ;
- les colonnes ;
- l’état des DataFrames.

Puis une nouvelle requête est envoyée au modèle.

La boucle devient :

$$
\boxed{
\text{Code}
\rightarrow
\text{Erreur}
\rightarrow
\text{Feedback}
\rightarrow
\text{Correction}
}
$$

Par exemple, après une `KeyError`, le modèle reçoit les véritables noms de colonnes.

Après une mauvaise jointure, il peut recevoir une instruction explicite lui demandant de merger les tables avant de filtrer.

Cette capacité transforme le système d’un générateur *one-shot* en agent capable de réagir au résultat de ses actions.

---

# 31. Sampling et vote

Lorsque suffisamment de temps reste, plusieurs programmes supplémentaires sont générés avec approximativement :

$$
T=0.5
$$

et :

$$
\text{top-p}=0.95.
$$

Stage 3 utilise par défaut :

$$
4
$$

échantillons.

Les différentes réponses sont ensuite combinées par vote.

---

# 32. Vote adaptatif

Une optimisation importante consiste à ne pas continuer à échantillonner une tâche lorsque plusieurs réponses précédentes sont déjà d’accord.

Ainsi :

$$
\text{tâche facile}
\Rightarrow
\text{peu de compute}
$$

et :

$$
\text{tâche incertaine}
\Rightarrow
\text{davantage de compute}.
$$

C’est une allocation adaptative du budget.

---

# 33. Budget utilisé par Stage 3

Même si le serveur autorise :

$$
40\text{ s},
$$

Stage 3 utilise volontairement :

$$
\boxed{
29\text{ s}
}
$$

comme budget interne.

Il garde donc environ :

$$
40-29=11\text{ s}
$$

de marge.

Les logs privés montrent des batches allant approximativement de :

$$
5.9\text{ s}
$$

à :

$$
23.7\text{ s}.
$$

Cette marge réduit fortement le risque de timeout.

---

# 34. Initialisation optimisée

Pendant les 60 secondes accordées à `Agent()`, Stage 3 :

- charge le LLM ;
- importe les grosses librairies ;
- initialise sklearn ;
- initialise scipy ;
- initialise sympy ;
- effectue un warm-up du modèle.

Le coût d’initialisation n’est donc pas payé pendant les 40 secondes critiques d’un `solve()`.

---

# 35. Résultat actuel du leaderboard

Votre Stage 3 est actuellement :

$$
\boxed{
\text{rang }1
}
$$

avec :

$$
\boxed{
92.5/100
}
$$

Les sous-scores sont :

| Famille | Score |
|---|---:|
| No files | 95.6 |
| Tables | 88.0 |
| Fits | 96.0 |
| **Total** | **92.5** |

Le système de référence A2 obtient seulement :

$$
40.8.
$$

L’écart est donc :

$$
92.5-40.8=51.7.
$$

C’est énorme.

---

# 36. Reconstruction probable des performances privées

Les pourcentages correspondent exactement aux fractions suivantes.

### No files

$$
\frac{43}{45}\times100
=
95.56\%.
$$

Donc probablement :

$$
\boxed{
43/45
}
$$

### Tables

$$
\frac{44}{50}\times100
=
88\%.
$$

Donc :

$$
\boxed{
44/50
}
$$

### Fits

$$
\frac{24}{25}\times100
=
96\%.
$$

Donc :

$$
\boxed{
24/25
}
$$

Au total :

$$
43+44+24=111
$$

et :

$$
\frac{111}{120}\times100
=
92.5.
$$

Le scénario le plus probable est donc :

| Famille | Correctes | Erreurs |
|---|---:|---:|
| No files | 43/45 | 2 |
| Tables | 44/50 | 6 |
| Fits | 24/25 | 1 |
| **Total** | **111/120** | **9** |

---

# 37. Audit déterministe de Stage 3

Nous avons ensuite utilisé le `dev.json` pour tester les solveurs déterministes indépendamment du LLM.

Résultat :

| Famille | Total dev | Résolues déterministiquement | Correctes |
|---|---:|---:|---:|
| No files | 65 | 25 | 25 |
| Tables | 80 | 80 | 80 |
| Fits | 35 | 35 | 35 |
| **Total** | **180** | **140** | **140** |

Donc :

$$
\boxed{
140/140
}
$$

des tâches que Stage 3 décide de résoudre déterministiquement sont correctes sur le dev.

Cela signifie :

$$
\boxed{
100\% \text{ de précision sur le domaine d'abstention déterministe observé.}
}
$$

C’est un résultat extrêmement important.

---

# 38. Tables publiques : résultat parfait

Sur les Tables publiques :

$$
\boxed{
80/80
}
$$

sont déjà résolues déterministiquement.

Cela signifie que les familles :

```text
table.stat
table.filter
table.group
table.join
table.derive
```

sont maîtrisées sur les 80 cas publics.

Or le score privé n’est que :

$$
88\%.
$$

Cela conduit à une conclusion très forte :

$$
\boxed{
\text{Le principal problème Tables n'est plus le dev connu.}
}
$$

Il s’agit vraisemblablement de la capacité à généraliser vers les **types privés absents du dev**.

---

# 39. Hypothèse sur les 20 Tables private-only

Supposons, uniquement pour raisonner, que Stage 3 réussisse les 30 tâches appartenant à des familles proches du dev.

Le score global Tables est :

$$
44/50.
$$

Il resterait donc :

$$
44-30=14
$$

bonnes réponses sur les 20 types privés.

Ainsi :

$$
\frac{14}{20}
=
70\%.
$$

Cette estimation n’est pas une mesure réelle, car nous ne voyons pas le privé.

Mais elle est cohérente avec :

$$
100\%\text{ sur Tables dev}
$$

et :

$$
88\%\text{ sur Tables privées}.
$$

---

# 40. Pourquoi optimiser encore les cinq types publics est risqué

Nous avons déjà :

$$
80/80.
$$

Ajouter encore des règles spécifiquement destinées aux cinq familles connues pourrait :

- augmenter la complexité ;
- créer des faux positifs ;
- empêcher le fallback LLM ;
- ne résoudre aucune erreur privée supplémentaire.

Le dev n’est donc plus suffisant comme unique benchmark de progrès.

---

# 41. Analyse des No files de Stage 3

Stage 3 ne résolvait déterministiquement que :

$$
25/65
$$

des tâches No-files publiques.

Les :

$$
40
$$

autres étaient laissées au LLM.

Ces tâches comprenaient pourtant de nombreux problèmes parfaitement déterministes :

- dates ;
- moyennes ;
- médianes ;
- logarithmes ;
- racines ;
- TVA ;
- combinaisons ;
- pourcentages ;
- conversions ;
- probabilités simples.

C’est un usage inutilement risqué du LLM.

---

# 42. Extension No-files développée

Nous avons donc développé une couche déterministe supplémentaire couvrant notamment :

### Arithmétique

- addition ;
- soustraction ;
- multiplication ;
- division ;
- modulo.

### Statistiques

- moyenne ;
- médiane ;
- écart-type ;
- moyenne pondérée.

### Pourcentages

- hausse ;
- baisse ;
- TVA ;
- changement relatif.

### Fonctions

- logarithme naturel ;
- logarithme base 10 ;
- racine ;
- puissance ;
- exponentielle.

### Probabilités

- espérance ;
- combinatoire simple.

### Dates

- différence entre deux dates ;
- jours inclusifs ;
- ajout de jours ;
- jour de la semaine.

### Croissance

- intérêts composés ;
- dépréciation.

### Conversions

- unités simples.

---

# 43. Résultat de l’extension No-files

Après plusieurs corrections :

$$
\boxed{
65/65
}
$$

tâches No-files publiques sont résolues correctement de manière déterministe.

La couverture est passée de :

$$
25/65
$$

à :

$$
65/65.
$$

---

# 44. Conséquence : 180/180 déterministe sur le dev

En combinant :

$$
65/65 \text{ No files}
$$

avec :

$$
80/80 \text{ Tables}
$$

et :

$$
35/35 \text{ Fits},
$$

nous obtenons :

$$
65+80+35=180.
$$

Donc :

$$
\boxed{
180/180
}
$$

tâches publiques peuvent maintenant être résolues sans appel au LLM dans notre candidate expérimentale.

C’est un résultat remarquable.

Mais il faut être très prudent.

---

# 45. Pourquoi 180/180 n’est pas synonyme de victoire

Le score dev devient désormais un critère insuffisant.

Nous avons :

$$
\text{Score dev}=100\%.
$$

Mais nous savons explicitement que le privé contient des opérations absentes du dev.

Notre véritable objectif n’est donc plus :

$$
\max \text{Score}_{dev}.
$$

Il devient :

$$
\boxed{
\max \text{Performance}_{private}
}
$$

sous la contrainte :

$$
\text{aucune régression sur les capacités déjà maîtrisées}.
$$

---

# 46. Le nouveau problème scientifique : généralisation

Nous devons maintenant nous demander :

> Une règle fonctionne-t-elle parce qu’elle a appris une capacité générale ou simplement parce qu’elle reconnaît les formulations du dev ?

C’est la distinction entre :

$$
\boxed{
\text{generalization}
}
$$

et :

$$
\boxed{
\text{template overfitting}.
}
$$

---

# 47. Construction d’un benchmark OOD

Puisque les véritables tâches privées sont cachées, nous avons commencé à créer notre propre benchmark de stress.

Nous avons généré :

$$
\boxed{
80 \text{ tâches Tables synthétiques}
}
$$

sur dix familles inventées :

```text
table.ood_covariance
table.ood_date_delta
table.ood_group_diff
table.ood_iqr
table.ood_join_derive
table.ood_membership
table.ood_share
table.ood_string
table.ood_topk
table.ood_weighted_mean
```

Ces familles **ne sont pas** les véritables familles privées.

Nous ne connaissons pas les types privés.

Elles sont uniquement conçues pour tester des capacités plausibles absentes du dev.

---

# 48. Pourquoi ce benchmark OOD est important

Si une modification donne :

$$
16/16
\rightarrow
16/16
$$

sur une famille publique, nous n’apprenons pratiquement rien.

Mais si une modification conserve :

$$
180/180
$$

sur le dev et fait passer un benchmark OOD, par exemple, de :

$$
40/80
$$

à :

$$
60/80,
$$

alors nous avons une preuve beaucoup plus crédible de généralisation.

Notre objectif devient donc :

$$
\boxed{
\text{Dev parfait}
+
\text{OOD meilleur}
}
$$

plutôt que simplement :

$$
\text{Dev parfait}.
$$

---

# 49. Versions expérimentales Stage 4

Plusieurs candidats ont déjà été créés :

```text
agent_stage4_calc.py
agent_stage4_ood.py
agent_stage4_safe.py
agent_stage4_safe_v2.py
agent_stage4_safe_v3.py
```

Nous avons également conservé :

```text
deterministic_audit.csv
ood_table_benchmark.json
stage3_to_stage4_candidate.diff
```

La logique est progressive.

### `Stage 4 calc`

Ajoute principalement la couverture déterministe No-files.

### `Stage 4 OOD`

Explore davantage de capacités Tables.

### Versions `safe`

Cherchent à augmenter la généralisation tout en maintenant des conditions strictes d’abstention.

---

# 50. Important : Stage 4 n’est pas encore validé

La dernière analyse s’est interrompue pendant la comparaison des différentes versions.

Ainsi :

$$
\boxed{
\text{Stage 3 reste la référence réellement validée sur ML-Arena.}
}
$$

Et :

$$
\boxed{
\text{Stage 4 reste expérimental.}
}
$$

Il ne faut pas confondre :

$$
\text{candidate locale}
$$

et :

$$
\text{meilleure soumission prouvée}.
$$

---

# 51. Analyse Fits

Le score privé est probablement :

$$
24/25.
$$

Et le dev donne :

$$
35/35.
$$

Il ne reste donc vraisemblablement qu’un seul Fit problématique.

Le problème vient probablement d’un cas limite :

- filtre particulier ;
- colonne ambiguë ;
- catégorie textuelle ;
- valeur manquante ;
- type de sortie ;
- procédure sklearn légèrement différente.

Il serait dangereux de réécrire entièrement cette partie pour récupérer un seul point.

Le bon principe est :

$$
\boxed{
\text{corriger les edge cases sans modifier le comportement nominal.}
}
$$

---

# 52. Analyse No files privée

Le score privé est probablement :

$$
43/45.
$$

Il reste donc seulement :

$$
2
$$

erreurs.

La nouvelle extension No-files est particulièrement intéressante parce que, contrairement à Tables, les mêmes familles de générateurs sont utilisées sur dev et privé.

La probabilité de généralisation est donc relativement élevée.

Cette amélioration est potentiellement :

$$
\boxed{
\text{faible risque}
+
\text{gain réel}
}
$$

---

# 53. Analyse Tables privée

C’est aujourd’hui le principal réservoir de points.

Il reste probablement :

$$
6
$$

erreurs Tables.

Ces six erreurs représentent :

$$
6\times\frac{100}{120}
=
5
$$

points de leaderboard.

Même n’en récupérer que trois donnerait :

$$
3\times0.8333
\approx
2.5
$$

points supplémentaires.

---

# 54. Scores potentiels

Score actuel :

$$
\frac{111}{120}\times100
=
92.5.
$$

Si nous récupérons 2 No-files et 1 Fit :

$$
\frac{114}{120}\times100
=
95.0.
$$

Si nous récupérons ensuite 3 Tables :

$$
\frac{117}{120}\times100
=
97.5.
$$

Si nous montons à 118 tâches correctes :

$$
\frac{118}{120}\times100
\approx
98.33.
$$

Il n’est donc pas nécessaire de résoudre absolument chaque cas privé pour atteindre un score extrêmement élevé.

---

# 55. Le principal risque à 92.5

Lorsque le système vaut 40, presque toute amélioration est intéressante.

À 92.5, le problème change.

Une nouvelle règle peut faire :

$$
+2
$$

sur de nouvelles tâches mais :

$$
-4
$$

sur des tâches précédemment correctes.

Le risque principal devient :

$$
\boxed{
\text{la régression}
}
$$

et non le manque d’idées.

---

# 56. Méthodologie de développement nécessaire

Chaque future modification devrait passer trois barrières.

## Barrière 1 — Dev

$$
\boxed{
180/180
}
$$

doit idéalement être conservé.

## Barrière 2 — OOD

La modification doit améliorer ou au minimum préserver les tests hors distribution.

## Barrière 3 — Runtime

Le système doit rester suffisamment rapide et robuste pour respecter :

$$
40\text{ s par batch}.
$$

On peut donc écrire :

$$
\boxed{
\text{Candidate acceptée}
\iff
\text{Dev OK}
\land
\text{OOD meilleur}
\land
\text{Runtime sûr}
}
$$

---

# 57. Le concept de confiance

Le problème devient progressivement un problème de **confiance**.

Pour chaque tâche :

> Le système déterministe comprend-il suffisamment bien la tâche pour répondre ?

Si oui :

$$
\text{solveur déterministe}.
$$

Sinon :

$$
\text{fallback LLM}.
$$

Le système idéal ressemble donc davantage à :

$$
\boxed{
\text{routing basé sur la confiance}
}
$$

qu’à un simple routing par famille.

---

# 58. Architecture cible conceptuelle

La structure vers laquelle nous nous dirigeons est :

```text
                         TASK
                           │
                           ▼
                 Robust preprocessing
                           │
                           ▼
                Semantic interpretation
                           │
                           ▼
                High confidence ?
                   /             \
                 YES             NO
                  │               │
                  ▼               ▼
          Deterministic        LLM coder
             solver               │
                  │               ▼
                  │          Python execution
                  │               │
                  │          Valid result ?
                  │            /       \
                  │          YES       NO
                  │           │         │
                  │           │         ▼
                  │           │       Repair
                  │           │         │
                  └───────────┴─────────┘
                              │
                              ▼
                        Validation / vote
                              │
                              ▼
                           ANSWER
```

---

# 59. Principe central pour gagner

L’idée la plus importante de tout notre travail est :

$$
\boxed{
\text{Python calcule ce qui peut être calculé exactement.}
}
$$

$$
\boxed{
\text{Le LLM intervient lorsque l'interprétation devient réellement nécessaire.}
}
$$

Et surtout :

$$
\boxed{
\text{Le système s'abstient lorsqu'il n'est pas suffisamment sûr.}
}
$$

En combinant les trois :

$$
\boxed{
\text{Déterminisme précis}
+
\text{abstention}
+
\text{fallback génératif}
}
$$

---

# 60. Pourquoi votre solution est déjà scientifiquement intéressante

La performance obtenue ne vient pas d’un modèle plus gros.

Le système de référence est autour de :

$$
40.8.
$$

Votre système atteint :

$$
92.5.
$$

Pourtant, le modèle reste un petit Qwen d’environ 1,5 milliard de paramètres.

La différence provient principalement de :

$$
\text{parsing}
+
\text{routage}
+
\text{outils}
+
\text{solveurs}
+
\text{exécution}
+
\text{feedback}.
$$

Le message scientifique peut donc être :

$$
\boxed{
\text{System design}
\gg
\text{raw LLM capability}
}
$$

dans le cadre de DS-Harness.

---

# 61. Une manière forte de raconter le projet à l’oral

L’histoire peut être présentée comme une succession d’échecs corrigés.

### Étape 1 — LLM seul

Problème :

- erreurs de calcul ;
- mauvais format ;
- aucune lecture fiable des données.

### Étape 2 — Exécution Python

Idée :

> le LLM écrit le programme mais ne fait pas lui-même les calculs.

### Étape 3 — Prétraitement robuste

Problème :

- CSV sales ;
- séparateurs ;
- NA ;
- unités ;
- dates.

Solution :

> le système nettoie les données avant le LLM.

### Étape 4 — Solveurs déterministes

Observation :

> beaucoup de tâches suivent des structures reconnaissables.

Solution :

> les résoudre sans LLM.

### Étape 5 — Repair

Observation :

> du code généré peut planter.

Solution :

$$
\text{erreur}
\rightarrow
\text{feedback}
\rightarrow
\text{correction}.
$$

### Étape 6 — Sampling et vote

Observation :

> le LLM reste stochastique.

Solution :

> plusieurs propositions et vote lorsque le budget le permet.

### Étape 7 — OOD

Observation :

$$
80/80 \text{ Tables dev}
$$

mais :

$$
44/50 \text{ Tables privées}.
$$

Conclusion :

> le nouveau problème est la généralisation.

Cette histoire répond directement aux critères de l’oral.

---

# 62. Ce qu’il ne faut surtout pas faire

## Ne pas remplacer Stage 3 par un agent générique

Stage 3 possède déjà énormément de garanties.

## Ne pas optimiser uniquement `dev.json`

Nous savons déjà atteindre :

$$
180/180.
$$

## Ne pas ajouter des regex agressives

Une mauvaise règle déterministe peut bloquer un bon fallback LLM.

## Ne pas utiliser davantage le LLM par défaut

Cela augmente :

- la variance ;
- le temps ;
- les risques d’erreurs.

## Ne pas changer de modèle sans benchmark

Un modèle légèrement meilleur en génération peut être plus lent et dégrader le système global.

## Ne pas utiliser le leaderboard comme seule validation

Un score privé global ne permet pas de savoir quelles tâches ont été gagnées ou perdues.

---

# 63. Forces actuelles

### Performance

$$
92.5/100
$$

et première place actuelle.

### Robustesse de sortie

$$
120/120
$$

réponses et zéro format error.

### Architecture claire

Séparation entre :

- parsing ;
- solveurs ;
- LLM ;
- exécution ;
- réparation ;
- vote.

### Très forte précision déterministe

$$
140/140
$$

pour Stage 3 sur le domaine public pris en charge.

### Tables publiques

$$
80/80.
$$

### Fits publics

$$
35/35.
$$

### Nouvelle extension No files

$$
65/65.
$$

---

# 64. Faiblesses actuelles

La principale faiblesse est :

$$
\boxed{
\text{la généralisation Tables hors distribution}
}
$$

La deuxième est la complexité croissante du code.

La troisième est que notre benchmark OOD et nos variantes Stage 4 n’ont pas encore terminé leur phase de validation comparative.

---

# 65. Ce que nous pouvons déjà affirmer

## A. Le déterminisme apporte énormément

Stage 3 résout correctement :

$$
140/140
$$

tâches publiques sans LLM lorsque ses règles se déclenchent.

## B. Le dev n’explique plus entièrement le privé

Tables :

$$
80/80 \text{ public}
$$

contre :

$$
44/50 \text{ privé}.
$$

## C. Il existe réellement de l’OOD

La documentation du challenge indique explicitement des types Tables absents du dev.

## D. Les No files peuvent être encore fortement déterminisés

Nous avons expérimentalement obtenu :

$$
25/65
\rightarrow
65/65.
$$

## E. Le LLM n’est pas le cœur de la performance

Le cœur est :

$$
\boxed{
\text{l'orchestration}
}
$$

autour de lui.

---

# 66. Ce que nous ne savons pas

Nous ne connaissons pas :

- les six Tables privées ratées ;
- les deux No-files privées ratées ;
- le Fit privé raté ;
- les véritables familles private-only ;
- les golds privés ;
- l’effet réel sur le privé des candidates Stage 4.

Ces éléments doivent rester clairement séparés de ce que nous avons mesuré.

---

# 67. La frontière scientifique actuelle

Notre problème n’est plus principalement :

> Comment résoudre les tâches ?

Il est devenu :

> Comment étendre les capacités du système sans augmenter son taux de faux positifs ?

On peut formaliser cela comme :

$$
\boxed{
\max \text{couverture}
\quad
\text{sous contrainte}
\quad
\text{précision très élevée}.
}
$$

---

# 68. Ce que devrait être la contribution principale du projet

Le projet peut défendre l’idée suivante :

> Avec un petit LLM, la meilleure stratégie ne consiste pas à augmenter sans cesse la complexité du prompting. Elle consiste à décomposer le problème entre composants déterministes fiables et raisonnement génératif utilisé uniquement lorsque nécessaire.

En résumé :

$$
\boxed{
\text{LLM-centric}
\rightarrow
\text{System-centric}
}
$$

---

# 69. Message central

La phrase qui résume probablement le mieux votre approche est :

> **Nous n’avons pas essayé de rendre le petit LLM plus intelligent. Nous avons réduit la quantité de choses sur lesquelles il devait être intelligent.**

Les calculs simples lui sont retirés.

Le parsing lui est retiré.

Le format lui est retiré.

Les Fits connus lui sont retirés.

Les opérations Tables connues lui sont retirées.

Il conserve principalement :

$$
\boxed{
\text{les cas réellement nouveaux ou ambigus}.
}
$$

---

# 70. Rôle idéal du LLM

Le LLM ne doit pas devenir :

$$
\text{une calculatrice}
$$

ou :

$$
\text{un parser CSV}.
$$

Il doit devenir :

$$
\boxed{
\text{un synthétiseur de programmes}
}
$$

capable de transformer un objectif inhabituel en quelques opérations Python fiables.

---

# 71. Score potentiel et stratégie

Aujourd’hui :

$$
111/120
=
92.5\%.
$$

Il reste seulement :

$$
9
$$

points binaires à récupérer.

La stratégie n’est donc pas de tout reconstruire.

Elle est de chercher successivement :

1. les gains très sûrs ;
2. les edge cases ;
3. les capacités OOD ;
4. les améliorations LLM uniquement si nécessaire.

---

# 72. Objectif leaderboard et objectif oral doivent rester liés

Une amélioration idéale doit apporter simultanément :

$$
\text{meilleur score}
$$

et :

$$
\text{meilleure compréhension scientifique}.
$$

Par exemple :

> Nous avons observé que toutes les Tables du dev étaient déjà résolues, mais seulement 88 % du privé. Nous avons donc cessé d’optimiser les templates publics et construit un benchmark OOD indépendant.

C’est beaucoup plus fort à l’oral que :

> Nous avons ajouté vingt regex et gagné deux points.

---

# 73. État actuel exact

## Version réellement validée sur ML-Arena

$$
\boxed{
\text{Stage 3}
}
$$

## Score privé

$$
\boxed{
92.5/100
}
$$

## Rang

$$
\boxed{
1^{er}
}
$$

## Réponses

$$
\boxed{
120/120
}
$$

## Format errors

$$
\boxed{
0
}
$$

## Audit déterministe Stage 3

$$
\boxed{
140/140
}
$$

## Tables publiques

$$
\boxed{
80/80
}
$$

## Fits publics

$$
\boxed{
35/35
}
$$

## No-files déterministes Stage 3

$$
\boxed{
25/65
}
$$

## Extension No-files expérimentale

$$
\boxed{
65/65
}
$$

## Couverture déterministe candidate sur l’ensemble du dev

$$
\boxed{
180/180
}
$$

## Benchmark OOD construit

$$
\boxed{
80 \text{ tâches}
}
$$

## Stage 4

Plusieurs candidats existent, mais aucun n’est encore considéré comme définitivement validé pour le leaderboard.

---

# 74. Conclusion générale

DS-Harness n’est pas véritablement un concours visant à découvrir le meilleur modèle de langage.

C’est un problème de **conception de système**.

Votre Stage 3 a progressivement transformé :

```text
Question
   ↓
LLM
   ↓
Réponse
```

en :

```text
Question
   ↓
Parsing robuste
   ↓
Routage
   ↓
Interprétation
   ↓
Solveur déterministe si possible
   ↓
LLM si nécessaire
   ↓
Exécution Python
   ↓
Feedback / repair
   ↓
Sampling / vote
   ↓
Réponse contrôlée
```

Cette architecture permet actuellement :

$$
\boxed{
92.5/100
}
$$

sur le privé, soit vraisemblablement :

$$
\boxed{
111/120
}
$$

tâches correctes.

Elle répond aux :

$$
120/120
$$

tâches sans aucune erreur de format.

Sur le dev, Stage 3 possède une précision déterministe de :

$$
\boxed{
140/140
}
$$

sur les tâches qu’il prend en charge.

Les Tables publiques sont déjà à :

$$
\boxed{
80/80
}
$$

et les Fits à :

$$
\boxed{
35/35.
}
$$

Notre extension No-files a permis de passer de :

$$
25/65
$$

à :

$$
65/65,
$$

ce qui rend possible une résolution déterministe des :

$$
\boxed{
180/180
}
$$

tâches publiques.

Mais ce résultat révèle justement le véritable problème restant :

$$
\boxed{
\text{la généralisation hors distribution}.
}
$$

Le privé contient des types Tables absents du dev, et cette particularité explique probablement une grande partie de l’écart entre :

$$
100\% \text{ sur les Tables publiques}
$$

et :

$$
88\% \text{ sur les Tables privées}.
$$

Notre objectif n’est donc plus d’ajouter aveuglément des règles.

Il est de construire un système capable de décider :

$$
\boxed{
\text{« je sais »}
}
$$

lorsqu’une résolution déterministe est sûre,

et :

$$
\boxed{
\text{« je ne suis pas suffisamment sûr »}
}
$$

lorsqu’il vaut mieux déléguer au LLM.

La philosophie générale de la solution peut ainsi être résumée par :

$$
\boxed{
\text{Déterministe lorsque nous savons}
}
$$

$$
\boxed{
\text{LLM lorsque nous ne savons pas}
}
$$

$$
\boxed{
\text{Abstention lorsque nous ne sommes pas sûrs}
}
$$

C’est cette combinaison entre **performance**, **robustesse**, **généralisation**, **explicabilité** et **méthodologie expérimentale** qui doit permettre de viser non seulement la meilleure place possible sur le leaderboard, mais également une excellente note à la soutenance.