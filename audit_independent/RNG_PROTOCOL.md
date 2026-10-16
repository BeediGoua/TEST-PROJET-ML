# RNG / protocol_version — Phase A documentation

## Stage3 `Agent.solve` (production)

Each `solve()` call resets sampling with `torch.manual_seed(0)` before generating
greedy + samples for **that** task. Batches of tasks therefore do **not** share a
single RNG stream across tasks.

## Forced-fallback cache `generations_34d6ece55b3c092a`

`gpu_experiments.generate_cache` (legacy / `protocol_version="v1_seed_once"`):

- calls `torch.manual_seed(seed)` **once** before the entire Table loop;
- then generates greedy/samples in batches of 8 tasks without re-seeding per task.

This cache is **frozen for Phase A** and must not be regenerated. Codes are still
valid for executor agreement and hybrid replays; they are **not** bit-identical to
what Stage3 would emit under per-solve seeding.

## Colab V2 preparation

`generate_cache(..., protocol_version="v2_seed_per_batch")` is reserved:

- included in the config JSON → changes the SHA cache key;
- raises `NotImplementedError` until V2 implements seed-per-batch matching Stage3;
- **must not** silently reopen `generations_34d6ece55b3c092a` under the new protocol.

Default remains `protocol_version="v1_seed_once"` so existing paths keep working
without implying Stage3 RNG parity.
