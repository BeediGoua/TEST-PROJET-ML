# FAITS — ce qui est prouvé / ce qui a été confondu

## Verdict

**MEASURED :** aucun score local du dépôt n'est un score privé ML-Arena.
Le « dépassement » de Stage3 est un **180/180 déterministe sur `dev.json`**,
pas un score > 92.5 sous lots de 8 / 40 s / Qwen.

## Scores privés (rapportés) vs couverture locale (audit stub)

| Agent | Privé total | Privé Tables | Local Tables covered/correct | Local No-files covered |
|---|---:|---:|---:|---:|
| stage3 | 92.5 | 88.0 | 80/80 | 25 |
| test1 | 86.7 | 80.0 | 80/80 | 25 |
| v10 | 81.7 | 68.0 | 80/80 | 65 |
| test2 | 77.5 | 52.0 | 80/80 | 65 |
| minimal | — | — | 80/80 | 25 |

## Confusion centrale

- Local Tables **80/80 pour tous** → le fallback LLM Tables n'est **jamais** scoré sur le public.
- Prive Tables : Stage3 88 -> TEST1 80 -> V10 68 -> TEST2 52.
- Fits restent à 96 partout → la régression n'est pas dans Fits.
- V10/TEST2 couvrent plus de No-files en local ; V10 **perd** des No-files en privé vs Stage3.

## Protocoles

| Protocole | LLM | batch8 | 40s | Prédit le privé ? |
|---|---|---|---|---|
| local_deterministic_core | no | no | no | no |
| audit_real_solve_stub | no | no | no | no |
| metamorphic_ood_rules | no | no | no | partial_abstention_risk_only |
| runtime_smoke | no | smoke | no | no |
| executor_probes | no | no | no | mechanism_only |
| ml_arena_private | yes | yes | yes | yes_is_the_target |

## Artefacts hashés

- `STAGE3_SUBMITTED_92_5.py` : 130431 octets, sha256 `00bfd0d2ef05c055…`
- `TEST1_SUBMITTED_86_7.py` : 147257 octets, sha256 `a83da219d907b327…`
- `TEST2_SUBMITTED_77_5.py` : 200878 octets, sha256 `aa3a2fd0af579bad…`
- `TEST2_MINIMAL_NOT_SUBMITTED.py` : 148416 octets, sha256 `71ff3b5cdde4d916…`
- `V10_SUBMITTED_81_7.py` : 152153 octets, sha256 `0f5491050434ec2b…`
- `dsh_official.py` : 15301 octets, sha256 `391b22c491c25d27…`
- `dev.json` : 923286 octets, sha256 `7e06aeeafa086bc7…`

## Niveau de preuve

- Scores privés : **MEASURED_reported** (agrégés utilisateur ; pas de détail tâche-par-tâche).
- Couverture locale 80/80 Tables : **MEASURED** (`dev_summary.csv` / `audit.py`).
- Claim 180/180 = battre 92.5 : **RÉFUTÉ** (métriques différentes).
