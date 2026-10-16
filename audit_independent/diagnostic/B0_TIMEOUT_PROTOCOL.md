# B0 — Vérification du protocole de référence (timeouts)

**Date:** Phase B pré-requis, avant toute expérience Linux.  
**Stage3 production:** `EXEC_TIMEOUT = 1.5` (`STAGE3_SUBMITTED_92_5.py`).  
**TEST1 production:** `EXEC_TIMEOUT = 5.0` (cold start subprocess).

## Timeouts réellement utilisés en Phase A (local)

| Script | Référence / bras | Timeout | Verdict B0 |
|---|---|---|---|
| `15_realistic_timeout_replay.py` | Stage3 (`E0`) | **1.5 s / programme** (`STAGE3_TO`) | OK = `E0_production` |
| `15_…` | E2 / E2T many | outer **6.5 s** pour le lot entier | Gate TEST1-like, **pas** Stage3 wall-clock |
| `15_…` | E2T per-candidate | **1.5 s** SIGALRM (Linux only) | Aligné Stage3 per-prog |
| `16_hybrid_test1_replay.py` | Stage3 baseline | **1.5 s** | OK production |
| `16_…` | test1 single greedy | **5.0 s** | TEST1, pas Stage3 |
| `16_…` | test1/E2T many | outer **6.5 s** | TEST1-like |
| `08_executor_agreement.py` | `_run_one` défaut | **5.0 s** | **Biais** vs Stage3 1.5 |
| `08_…` | probes SyntaxError | E0 **2.0 s**, many **5.0 s** | **Biais** |
| `14_e2t_probes.py` | E2T many | outer **6.5 s** | probes only |

## Ce que le 97.35 % compare vraiment

Dans `15_realistic_timeout_replay.py` (source du 97.35 %) :

```text
E0  = Stage3.run_code(..., timeout=1.5)   × N programmes indépendants
E2T = run_codes_many(..., outer=6.5)      × 1 child pour tout le lot
      + SIGALRM 1.5 / candidat (Linux; no-op Windows)
```

Donc **E0 n’était pas à 5 s** dans ce script précis — il était déjà à 1.5 s.  
Le biais méthodologique principal n’est **pas** « E0 trop généreux », c’est :

> Stage3 a jusqu’à `N × 1.5 s` de wall-clock séquentiel  
> alors qu’E2T a un **seul** envelope `6.5 s` pour N programmes + cold-start subprocess.

Pour N=5 (greedy+4) : Stage3 pire cas ≈ **7.5 s** de compute pur ; E2T a **6.5 s** tout compris (startup pandas inclus). Gate artificiellement serré → `None` sans mauvaise valeur.

Les scripts **08** (agreement historique / GitHub) restent biaisés à 5.0/2.0 s et ne doivent **pas** servir de référence production.

## Deux références exigées pour Phase B

| Nom | Définition | Sert à |
|---|---|---|
| `E0_semantic` | `stage3.run_code` timeout large (ex. **15 s**) | équivalence numérique pure |
| `E0_production` | `stage3.run_code` timeout **exact 1.5 s** | parité production Stage3 |

Ne jamais comparer E2T@1.5/candidat contre E0@5 et appeler ça une régression de production.

## Métriques séparées (B1.3)

```text
PROGRAM-LEVEL AGREEMENT   — valeur par programme
TASK-LEVEL FINAL VOTE     — réponse finale après Stage3.vote (objectif réel)
```

Phase A a déjà montré : ~97 % programme-level mais **100 % task-level** recovery vs Stage3 sur 80 votes (65/80 = 65/80).

## Re-run focus B0 (local, `17_b0_dual_e0_recalc.py`)

Sur `d_041`, `d_100`, `d_170` uniquement, outer=6.5 :

| Métrique | Résultat |
|---|---|
| agree vs E0_semantic | **10/10 (100 %)** parmi finis |
| agree vs E0_production | **10/10 (100 %)** parmi finis |
| mauvaises valeurs numériques | **0** |
| E2T None alors que E0_prod fini | **0** (sur ce re-run) |

Runtimes E0_production ≪ 1.5 s ; batch E2T ≈ 2.2–3.0 s ≪ 6.5 s.

**DERIVED :** les 7 `None` de Phase A sur ces tâches étaient **non déterministes / charge** (replay 80 tâches d’affilée sous `dsh_compat` Windows), pas une divergence sémantique stable. Cela renforce l’hypothèse « gate outer artificiellement serré / flaky », pas « E2T calcule faux ».

Confirmation Linux + sweep outer = objet de B1 (`colab_phase_b1.ipynb`).
