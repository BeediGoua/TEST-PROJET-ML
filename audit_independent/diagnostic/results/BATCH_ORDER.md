# H4 — Batch order sensitivity

**Platform:** Windows-11-10.0.26200-SP0

**Codes:** placeholder/synthetic codes

**Orders tested:** 22 (forward, reverse, 20 perms)

**Tasks with order-sensitive answers:** 0 / 8

## Verdict

- No answer divergence across orders on this corpus (still forbid inter-task batch in TEST3-recovery by policy).

- **NOTE:** not Linux official alarm semantics; re-run on Colab/Linux for GO gate.

- **NOTE:** codes not from real Qwen cache — treat as structural probe only.


## Per-task

- `d_001`: distinct=1 sensitive=False forward=780.0 reverse=780.0
- `d_005`: distinct=1 sensitive=False forward=253.0 reverse=253.0
- `d_006`: distinct=1 sensitive=False forward=16136.0 reverse=16136.0
- `d_009`: distinct=1 sensitive=False forward=243090.0 reverse=243090.0
- `d_011`: distinct=1 sensitive=False forward=119153.0 reverse=119153.0
- `d_015`: distinct=1 sensitive=False forward=270465.0 reverse=270465.0
- `d_016`: distinct=1 sensitive=False forward=283878.0 reverse=283878.0
- `d_021`: distinct=1 sensitive=False forward=175325.0 reverse=175325.0