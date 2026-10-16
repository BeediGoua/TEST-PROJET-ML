# Executor contract

## Results

| Agent | fix | Probe | OK |
|---|---|---|---|
| stage3 | False | control | True |
| stage3 | False | import_pandas | True |
| stage3 | False | import_numpy | True |
| stage3 | False | syntax_error | True |
| stage3 | False | one_syntax_error_four_programs | True |
| test1 | False | control | True |
| test1 | False | import_pandas | False |
| test1 | False | import_numpy | True |
| test1 | False | syntax_error | True |
| test1 | False | one_syntax_error_four_programs | False |
| test2 | False | control | True |
| test2 | False | import_pandas | False |
| test2 | False | import_numpy | True |
| test2 | False | syntax_error | True |
| test2 | False | one_syntax_error_four_programs | True |
| test2 | True | control | True |
| test2 | True | import_pandas | True |
| test2 | True | import_numpy | True |
| test2 | True | syntax_error | True |
| test2 | True | one_syntax_error_four_programs | True |
| faithful | False | control | True |
| faithful | False | import_pandas | True |
| faithful | False | import_numpy | True |
| faithful | False | syntax_error | True |
| faithful | False | one_syntax_error_four_programs | True |

## Contract verdict

- `stage3` alias_fix=False: **PASS** on import_pandas
- `test1` alias_fix=False: **FAIL** on import_pandas
- `test2` alias_fix=False: **FAIL** on import_pandas
- `test2` alias_fix=True: **PASS** on import_pandas
- `faithful` alias_fix=False: **PASS** on import_pandas

**MEASURED:** Stage3 and faithful pass import_pandas; TEST1 samples and TEST2 batch fail;
TEST2 + wrapper alias fix passes. Syntax isolation: TEST2/stage3/faithful keep siblings; TEST1 does not.
