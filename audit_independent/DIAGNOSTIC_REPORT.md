# Rapport diagnostic — pourquoi Stage3 n’a pas été battu

Pack exécuté : `projects/audit_independent/diagnostic/` (voir `GO_NOGO.md` pour la décision).

## 1. Verdict

**NO-GO** pour une nouvelle soumission privée.

Le local n’a jamais battu Stage3 (92.5) sur le protocole ML-Arena. Le « 180/180 » est une couverture de **règles seules** sur `dev.json`. Les challengers soumis (TEST1 86.7, V10 81.7, TEST2 77.5) ont tous régressé, surtout en **Tables**.

## 2. Faits mesurés

| Agent | Privé | Tables privé | Tables local covered |
|---|---:|---:|---:|
| Stage3 | 92.5 | 88 | 80/80 |
| TEST1 | 86.7 | 80 | 80/80 |
| V10 | 81.7 | 68 | 80/80 |
| TEST2 | 77.5 | 52 | 80/80 |

Les 80 Tables publiques sont entièrement absorbées par les règles → le fallback LLM Tables n’est **jamais** scoré en local. Détail : `diagnostic/results/FACTS.md`.

## 3. Contrat d’exécution (MEASURED)

Programme témoin `import pandas as pd; answer = sum(...)` :

| Agent | Résultat |
|---|---|
| Stage3 (`exec`) | PASS |
| TEST1 samples (`run_codes_many`) | FAIL `UnboundLocalError` |
| TEST2 batch | FAIL même erreur |
| TEST2 + alias `__dsh_pd` | PASS |
| Faithful (1 child / sample) | PASS |

SyntaxError : TEST1 perd les 4 samples ; TEST2 isole. Voir `EXECUTOR_CONTRACT.md`.

## 4. Forced-fallback proxy (12/80 Tables)

Taux d’exécution `import_pandas` : Stage3 1.00, TEST1 0.00, TEST2 0.00, TEST2-fix 1.00, faithful 1.00.  
TEST2 mappe les échecs sur **default=1**.  
**Qwen GPU : NOT RUN** (pas de CUDA ici).

## 5. Ablation règles (MEASURED)

Sur les 80 Tables publiques : historique / extensions / reject-zero → toujours **80/80 correct**, shadow `same:80`.  
Les extensions ne changent pas la métrique publique qui masquait le LLM.  
`calc_safe_v2` : No-files 25 → 65.

## 6. Timing (MEASURED, Windows)

- TEST1/TEST2 : 8 programmes en ~4 s (un enfant), mais `import_pandas` → **0/8 ok**.
- Faithful : 8/8 ok mais **~36 s** — trop cher pour 40 s + Qwen.
- Conclusion : le prochain candidat doit être **alias `__dsh_pd` dans un batch un enfant**, pas N sous-processus.

## 7. Chaîne causale

1. Optimisation de la mauvaise métrique (180/180).
2. Passage `exec` → wrappers `dsh` qui cassent `import pandas`.
3. TEST2 amplifie (greedy+repair+samples + default 1 + plus d’abstentions).
4. Gisement restant pour battre 92.5 = fallback LLM sur les abstentions Stage3 (~9 tâches), **après** restauration du contrat.

## 8. Prochaine hypothèse (une seule)

Stage3 rules/vote + exécuteur TEST1 avec **`__dsh_pd`** (+ isolation SyntaxError) seulement.  
Falsification : Tables privé ≤ 80% ⇒ chercher fidelity/timing/prompt, pas de nouvelles regex.

## 9. Pré-TEST3 (H1–H6)

Harness livré — voir [`PRETEST3_STATUS.md`](PRETEST3_STATUS.md) et `diagnostic/07`…`12`.  
**NO-GO** tant que le cache Qwen réel (Colab) n’a pas verdit les gates REQUIRED.

Artefacts : `diagnostic/results/`, `experimental/test1_alias_dsh.py`, `colab_forced_fallback.ipynb`.
