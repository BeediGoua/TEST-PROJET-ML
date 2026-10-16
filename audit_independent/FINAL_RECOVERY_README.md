# FINAL RECOVERY — un seul Colab

Plus de Phase B1/B2 séparées. **Un notebook :**

[`colab_final_recovery.ipynb`](colab_final_recovery.ipynb)

## Flux

```text
B1 contract Linux (loop [6,None,42,9] + probes)
→ B1 replay cache 400 (task-level ≥ Stage3, bad_numeric=0)
→ B2 vrai Agent.solve Tables forced-fallback (E2T ≥ Stage3, <40s)
→ B2b stress K=1..8 (optionnel)
→ B3 No-files uncovered (E2T ≥ Stage3)
→ B4 static (no exec upload) + bake zip
→ RECOVERY_READY
```

Premier FAIL → `RECOVERY_NOT_READY` + STOP.

## TEST3 si vert

```text
STAGE3_E2T_RECOVERY.zip  →  agent.py + dsh.py
= Stage3 EXACT + executor E2T seulement
```

Soumission **manuelle** ML-Arena (pas auto).

## Fichiers

| Fichier | Rôle |
|---|---|
| `colab_final_recovery.ipynb` | **le** notebook |
| `final_recovery_harness.py` | gates STOP |
| `bake_stage3_e2t_recovery.py` | bake agent/zip |
| `STAGE3_E2T_RECOVERY/` | sortie bake |
| `colab_phase_b1/b2.ipynb` | DEPRECATED stubs |

## Interdit

Qwen3, nouveaux prompts/règles, reject-zero, default=1, BEAT-STAGE3 avant recovery.
