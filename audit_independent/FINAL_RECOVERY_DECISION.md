# FINAL RECOVERY — verdict corrigé (Colab)

**`RECOVERY_NOT_READY`**

Le message `RECOVERY_READY` imprimé par B4 est **invalide** : la cellule B4 a tourné alors que le gate B3 No-files avait déjà échoué. Ne pas soumettre TEST3.

## Gates

| Gate | Résultat | Détail |
|---|---|---|
| B1 loop `[6,None,42,9]` | PASS | MEASURED |
| B1 cache replay | PASS | program_agree=1.0, task_vote=1.0, acc 63/80 = 63/80 |
| B2 Tables `Agent.solve` forced-fallback | PASS* | 80/80 = 80/80 (*temps batch ~0.36 s suspects — à ne pas sur-interpréter) |
| B2b stress K | PASS | tous ≪ 40 s |
| **B3 No-files uncovered** | **FAIL** | Stage3 **0.975** (39/40) vs E2T **0.900** (36/40) |
| B4 static no `exec` | PASS | mismatch_count=3 = héritage Stage3 prompt (pas bloquant upload) |

## Pertes B3 (Stage3 OK, E2T → 0.0)

`0.0` = défaut `solve()` quand aucun candidat fini (vote vide), pas une mauvaise maths E2T.

| id | gold | Stage3 | E2T |
|---|---:|---:|---:|
| d_026 | 13.0 | 13.0 | 0.0 |
| d_065 | 6.0 | 6.0 | 0.0 |
| d_076 | 16.0 | 16.0 | 0.0 |
| d_143 | 8.9 | 8.9 | 0.0 |

## Décision

```text
RECOVERY_NOT_READY
```

**Ne pas uploader** `STAGE3_E2T_RECOVERY.zip` sur ML-Arena.

Cause : sur les No-files hors `calc_rules`, l’exécuteur dsh/E2T laisse **4 tâches sans aucune valeur finie** alors que Stage3 historique (`exec`) les résout. Tables recovery est encourageante ; No-files bloquent la recovery globale.

## Suite (ciblée, pas une nouvelle phase d’audit)

1. Rejouer uniquement ces 4 objectifs sous Stage3 vs E2T `run_code` (nofile sandbox / sympy).
2. Corriger le sandbox No-files si bug contractuel ; sinon documenter écart structurel.
3. Re-run B3 seulement → si E2T ≥ Stage3, alors B4 + bake + soumission.
