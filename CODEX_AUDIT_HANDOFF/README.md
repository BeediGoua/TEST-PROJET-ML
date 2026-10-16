# CODEX_AUDIT_HANDOFF

Artefacts préparés pour audit indépendant du challenge DS-Harness.

## Fichiers

| Fichier | Rôle | Taille (octets) | SHA-256 |
|---|---|---:|---|
| `STAGE3_SUBMITTED_92_5.py` | champion historique | 130431 | `00bfd0d2ef05c055cc53c8814cc317ec05f3d10c08dfdedb14ddd6ff30e93aa7` |
| `V10_SUBMITTED_81_7.py` | v10 privé 81.7 | 152153 | `0f5491050434ec2b71c0dc72b676f8d77e1004e1e00069f366049c66657021c6` |
| `TEST1_SUBMITTED_86_7.py` | recovery utilisé pour TEST1 | 147257 | `a83da219d907b327b5fe76b28b3b769f429b41e7b8ad08815800c931753bdf28` |
| `TEST2_SUBMITTED_77_5.py` | gros candidat utilisé pour TEST2 | 200878 | `aa3a2fd0af579bada2efff0fcc4c7cc379fbccb397a4633bb2550b972db7a66e` |
| `TEST2_MINIMAL_NOT_SUBMITTED.py` | ablation executor prévue mais non soumise | 148416 | `71ff3b5cdde4d91686d3f0d77b4fe3f6f99550b20899f76888eb2893d9a2f29e` |
| `dsh_official.py` | helper officiel | 15301 | `391b22c491c25d276adacb6162ff86a65f968a1273f8d816a3d158210ac27a7c` |
| `dev.json` | 180 tâches publiques | 923286 | `7e06aeeafa086bc7e93180e9f66073be3569c32ef073df81f9c56824515ee289` |

## Provenance / niveau de certitude

- **Stage3** : artefact exact conservé et hashé.
- **TEST2** : l'artefact `FINAL_BEST_SUBMISSION/agent.py` fait 200878 octets, soit ~196.2 KiB comme l'UI ML-Arena. Le texte recopié depuis la soumission est identique après normalisation des fins de ligne.
- **TEST1** : l'artefact `stage3_recovery_submission/agent.py` fait 147257 octets, soit ~143.8 KiB comme l'UI ML-Arena, et correspond au fichier fourni immédiatement avant ce run. **Si ML-Arena permet de télécharger le code de TEST1, vérifier le SHA-256 pour lever toute ambiguïté résiduelle.**
- **TEST2_MINIMAL_NOT_SUBMITTED** : ne jamais le confondre avec le TEST2 privé à 77.5.

## Point méthodologique critique

Les scores agrégés n'identifient pas les tâches réussies. Deux agents ayant le même sous-score peuvent échouer sur des exemples différents. Toute conclusion tâche-par-tâche doit donc provenir d'un corpus où les golds sont disponibles ou d'un replay officiel donnant les identités.
