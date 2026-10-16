
from pathlib import Path
import re, pandas as pd

def inspect_agent_source(path):
    path=Path(path); text=path.read_text(encoding='utf-8')
    # Current challenge upload scan rejects exec(...). Historical Stage 3 is retained only as the measured champion.
    exec_violation = bool(re.search(r'(?<![A-Za-z_])exec\s*\(', text))
    sympy_advertised = bool(re.search(r'"nofile"\s*:\s*"[^\n]*sympy',text,re.I))
    many_start=text.find('def run_codes_many')
    many=text[many_start:many_start+9000] if many_start>=0 else ''
    sympy_runtime = bool(re.search(r'\b(?:import sympy|from sympy)\b',many))
    sympy_mismatch = bool(sympy_advertised and not sympy_runtime)
    onehot_claim = 'automatically one-hot encode' in text.lower()
    onehot_runtime = bool(re.search(r'get_dummies|OneHotEncoder|ColumnTransformer',many))
    onehot_mismatch = bool(onehot_claim and not onehot_runtime)
    no_imports = 'no imports, at most 12 lines' in text.lower()
    # look only in the examples region to avoid imports in implementation code
    ex0=text.find('EXAMPLES ='); ex1=text.find('FEWSHOTS',ex0) if ex0>=0 else -1
    examples=text[ex0:ex1 if ex1>ex0 else ex0+5000] if ex0>=0 else ''
    example_import = bool(re.search(r'\\nimport\s+math|"import\s+math',examples))
    example_import_mismatch = bool(no_imports and example_import)
    return {
        'agent_file':path.name,
        'exec_upload_violation':exec_violation,
        'sympy_prompt_runtime_mismatch':sympy_mismatch,
        'onehot_prompt_runtime_mismatch':onehot_mismatch,
        'no_imports_example_mismatch':example_import_mismatch,
        'prompt_runtime_mismatch_count':int(sympy_mismatch)+int(onehot_mismatch)+int(example_import_mismatch),
    }

def inspect_many(paths):
    return pd.DataFrame([inspect_agent_source(p) for p in paths])
