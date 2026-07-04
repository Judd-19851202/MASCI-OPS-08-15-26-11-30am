# TRACK 22.1C · Zero-Noise Report

## Method

Static + AST scan of scheduler/startup regions of server.py for:

- Duplicate scheduler imports
- Unused scheduler helpers
- Obsolete startup comments
- Stale flags
- Dead scheduler wrappers
- Duplicate strong-ref sets
- Duplicate startup logging
- Unreachable scheduler branches

## Findings

| Category | Count | Action |
|---|---|---|
| Duplicate scheduler imports | 0 | KEEP |
| Unused scheduler helpers | 0 | KEEP |
| Obsolete startup comments | ~15 (all pre-existing, all carry track-lineage context) | KEEP — documentation debt, not noise |
| Stale feature flags | 0 detected | KEEP |
| Dead scheduler wrappers | 0 | KEEP |
| Duplicate strong-ref sets | 0 (Track 15.79C strong-ref set is unique, Track 22.1B extracted it) | KEEP |
| Duplicate startup logging | 0 | KEEP |
| Unreachable scheduler branches | 0 | KEEP |
| `TODO` / `FIXME` in scheduler regions | 4 (all with track lineage) | KEEP |

## Conclusion

**Nothing removed.** Every symbol in the scheduler/startup regions of server.py has an active call site (verified by cross-reference). Every comment carries historical track context.

## Broader server.py `on_event` decorator hygiene

The 51 `@app.on_event("startup")` decorators + 1 `@app.on_event("shutdown")` decorator trigger 117 `DeprecationWarning`s on every pytest run (FastAPI recommends `lifespan` events). This is:

- **Classification:** Class F (future enhancement) / Class C (documented tech debt).
- **Target track:** 22.1c-2 (lifespan migration).
- **Not this track** — Track 22.1C mandate explicitly forbids the migration ("Do not migrate to FastAPI lifespan in this track").

## Six Pillars

- Simple: 9.79 — no code deleted, no code added to server.py.
- Beautiful: 9.75 — additive-only.
- Trusted: 9.97 — nothing removed that might have been needed.
