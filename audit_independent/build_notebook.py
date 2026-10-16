"""Create and execute the reporting cells of the single audit notebook."""
from pathlib import Path
import contextlib, io, json, os, traceback

HERE=Path(__file__).resolve().parent
cells=[]
def md(text):cells.append(dict(cell_type='markdown',metadata={},source=text.splitlines(True)))
def code(text):cells.append(dict(cell_type='code',metadata={},source=text.splitlines(True),execution_count=None,outputs=[]))

md('# DS-Harness — audit indépendant reproductible\n\nAgents immuables ; expériences CPU mesurées ; expériences GPU explicitement non exécutées. Lire REPORT.md pour le rapport initial et la hiérarchie des hypothèses. Aucun score privé inventé. Les programmes des contre-exemples sont écrits à la main, pas générés par Qwen.')
md('## 00 — Setup et reproductibilité\nExécuter depuis ce dossier, projects, ou la racine du workspace. RERUN_CPU rejoue les mesures ; RUN_GPU lance une expérience hors budget de génération et replay, sur Linux/CUDA seulement. Aucun accès au leaderboard.')
code('''from pathlib import Path
import sys, json, hashlib, platform
import pandas as pd
candidates=[Path.cwd(),Path.cwd()/'audit_independent',Path.cwd()/'projects/audit_independent']
AUDIT=next(p for p in candidates if (p/'audit.py').exists()).resolve()
sys.path.insert(0,str(AUDIT)); sys.path.insert(0,str(AUDIT.parent))
from audit import inventory, reproduce, OUT, HANDOFF, FILES
RERUN_CPU=False
RUN_GPU=False
print('Python',sys.version)
print('Platform',platform.platform())
print('Inputs',HANDOFF)
''')
md('## 01 — Artefacts et hashes\nMEASURED : comparaison des octets locaux au manifeste fourni. L’identité avec une soumission téléchargée demeure une question distincte.')
code('''manifest,changes=inventory()
print(pd.DataFrame(manifest).to_string(index=False))
print(pd.DataFrame(changes).query("symbol != 'Agent'").to_string(index=False))
''')
md('## 02 — Reproduction du public\nHypothèse : les Tables publiques ne traversent pas le fallback. Méthode : vrai solve, modèle remplacé par un témoin qui signale une demande de génération. Les réponses par défaut ne sont pas comptées comme règles réussies.')
code('''if RERUN_CPU:
    reproduce()
print(pd.read_csv(OUT/'dev_summary.csv').to_string(index=False))
''')
md('## 03 — Cartographie règle / fallback et fidélité de l’évaluateur\nLes appels aux règles sont conservés par tâche dans real_solve_dev.csv. Comparaison à l’ancien évaluateur : les 40 écarts de couverture TEST2 sont des No-files, pas des Tables.')
code('''real=pd.read_csv(OUT/'real_solve_dev.csv')
legacy=pd.read_csv(OUT/'legacy_dev.csv')
paired=real.merge(legacy,on=['agent','id'],suffixes=('_solve','_legacy'))
diff=paired[paired.covered_solve != paired.covered_legacy]
print(diff.groupby(['agent','family_solve']).size().to_string())
print(real[['agent','id','calls']].head().to_string(index=False))
''')
md('## 04 — Forced fallback Tables\nNON EXÉCUTÉ avec Qwen sur cet hôte : CUDA absent et aucun poids Qwen en cache. Le module gpu_experiments prépare les 80 prompts avec le prétraitement Stage3 et appelle Agent.generate, y compris son préfixe Python. Cette expérience isole la génération hors délai ; elle ne remplace pas un solve complet en lots mixtes.')
code('''import torch
from huggingface_hub import constants
print('torch',torch.__version__,'CUDA',torch.cuda.is_available())
print('Cache models',[p.name for p in Path(constants.HF_HUB_CACHE).glob('models--*')])
from gpu_experiments import generate_cache,replay_cache,summarize_replay
cache=None
if RUN_GPU:
    cache=generate_cache()
else:
    print('NOT RUN: forced fallback Qwen')
''')
md('## 05 — Cache des générations\nLa clé inclut modèle, révision, seed, hash agent, hash dev et paramètres de génération. Chaque ligne conserve prompt, texte et code. Le replay ne régénère jamais. Les fichiers partiels portent .partial.json ; ils ne doivent pas être utilisés comme résultats complets.')
code("print('Caches complets disponibles:',[p.name for p in OUT.glob('generations_*.json') if '.partial.' not in p.name])")
md('## 06 — Exécuteurs A/B/C : contre-exemples et ablation\nMEASURED : collision pd et compilation collective. Windows utilise un shim POSIX uniquement pour les programmes finis ; aucune inférence de timeout/mémoire Linux. L’ablation de portée exécute le vrai solve avec code fixe et budgets relâchés.')
code('''if RERUN_CPU:
    import probes,ablation
    probes.run(); ablation.run()
probes_df=pd.read_csv(OUT/'executor_probes.csv')
print(probes_df[['agent','probe','result']].to_string(index=False))
ab=pd.read_csv(OUT/'wrapper_ablation.csv')
print(ab[['agent','wrapper_alias_fix','answer','correct']].to_string(index=False))
''')
md('## 07 — Replay réel et modèle Coder vs Qwen3\nÀ exécuter sous Linux/CUDA : créer deux caches, changer seulement model. Même prompt Stage3, 500 tokens, greedy + quatre samples. Séparer l’effet modèle de l’effet prompt. La comparaison reste hors budget ; les temps seront à mesurer dans les lots officiels ensuite.')
code('''if RUN_GPU and cache:
    replay=replay_cache(cache)
    print(summarize_replay(replay).to_string())
    # Deuxième bras séparé, à lancer quand le premier est inspecté :
    # qwen3_cache=generate_cache(model='Qwen/Qwen3-1.7B')
else:
    print('NOT RUN: executor replay on Qwen cache / model comparison')
''')
md('## 08 — Greedy, samples, oracle et vote\nLe replay calcule oracle_samples_at4 (les quatre samples seulement), oracle_greedy_plus4 et vote_accuracy séparément. Ne pas appeler cinq programmes « oracle@4 ». Un écart oracle-vote est une borne de potentiel, pas un gain réalisable garanti. Résultats Qwen : non disponibles.')
md('## 09 — Repair\nExpérience restante : journaliser le vrai solve sous Linux, avec puis sans DSH_NO_REPAIR, mêmes tâches, seeds et budget. Mesurer les transitions correct/faux et secondes par gain net ; les erreurs du wrapper doivent être corrigées avant de juger le modèle. Le témoin pd a montré un repair inutile, sans mesurer son rendement sur Qwen.')
md('## 10 — Prompts\nStage3 et TEST1 ont les mêmes fonctions/prompts initiaux selon le diff. Une ablation du prompt impose de nouvelles générations, puis un replay identique ; conserver le même code empêcherait de mesurer l’effet du prompt.')
md('## 11 — Shadow rules\nExpérience restante : TEST2 original versus extensions désactivées en mémoire, puis ablation distincte des garde-fous stat/filter. Conserver suggestions, décisions et désaccords par tâche. Sur le dev actuel, les règles historiques absorbent déjà toutes les Tables : ce corpus seul ne mesure pas la valeur des extensions privées.')
md('## 12 — No-files et Fits\nMEASURED : 65/65 No-files déterministes TEST2, contre 25/65 Stage3/TEST1 ; 35/35 Fits publics partout. L’égalité des agrégats privés ne permet aucune conclusion sur l’identité des erreurs. Aucun changement Fits en production proposé.')
md('## 13 — Robustesse et coût par lot\nExpérience Linux restante : 1, 4, 8 fallbacks, lots mixtes, permutations d’ordre, limites 40 s / RAM. Les timeouts collectifs peuvent perdre les résultats déjà calculés. Le coût d’une tâche influence les sept autres ; les mesures tâche par tâche hors budget ne suffisent pas.')
md('## 14 — Construction du challenger\nAucun agent de production modifié. L’alias pandas corrigé n’existe que dans le transport expérimental ablation.py. Candidat de contrôle proposé : règles et prompts Stage3, exécuteur individuel conforme, puis batch après validation du contrat et du budget. Pas de nouvelle règle avant comparaison au fallback.')
md('## 15 — Rapport GO / NO-GO\nNO-GO pour soumission privée. Défauts d’exécuteur prouvés ; incidence privée, oracle Qwen, repair, p95 GPU et capacité de généralisation non mesurés. Lire le rapport détaillé ci-dessous.')
code("print((AUDIT/'REPORT.md').read_text(encoding='utf-8'))")

ns={};old=os.getcwd();os.chdir(HERE)
try:
    count=0
    for cell in cells:
        if cell['cell_type']!='code':continue
        count+=1;cell['execution_count']=count
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(''.join(cell['source']),f'audit_notebook_cell_{count}','exec'),ns)
        if output.getvalue():cell['outputs']=[dict(output_type='stream',name='stdout',text=output.getvalue().splitlines(True))]
finally:os.chdir(old)
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python',version=platform.python_version()) if False else dict(name='python')),cells=cells)
for i,c in enumerate(cells):c['id']=f'audit-{i:03d}'
(HERE/'DS_HARNESS_AUDIT.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=2),encoding='utf-8')
print('Created executed reporting notebook with',count,'code cells; GPU sections explicitly skipped.')
