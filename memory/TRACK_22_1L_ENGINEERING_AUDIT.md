# TRACK 22.1L · Engineering Audit

Executed under the Relentless Ownership pillar during the command-center cutover.

## Findings

### F1 · `regex=` DeprecationWarnings (Pydantic v2)
- **Where:** `backend/routes/verification.py` L324 and ~1 other module (Query/Path param declarations).
- **Symptom:** `DeprecationWarning: regex has been deprecated, use pattern instead` fires on every request in preview.
- **Impact:** Warning-only in Pydantic v2; will become a hard error in Pydantic v3.
- **Classification:** **C — Engineering Debt** (mechanical migration).
- **Owner:** Backend team.
- **Target track:** **22.3** (Pydantic v2 hygiene sweep — batch across all routes with grep).
- **Action taken in 22.1L:** Documented only. Fixing here would require touching 2 unrelated route files; outside surgical scope.

### F2 · Orphan coroutine warning at pytest shutdown
- **Where:** `backend/routes/job_photos.py` L497 — `_ensure_thumb_cache_indexes` coroutine.
- **Symptom:** `RuntimeWarning: coroutine '_ensure_thumb_cache_indexes' was never awaited` occasionally at pytest teardown.
- **Impact:** Non-blocking; no correctness impact — the coroutine object was created but never scheduled in a test-fixture context.
- **Classification:** **C — Engineering Debt** (test lifecycle hygiene).
- **Owner:** Backend team.
- **Target track:** **22.1K** (shutdown migration will formalize the cleanup path).
- **Action taken in 22.1L:** Documented only.

### F3 · `_startup` closure was silently swallowing all exceptions
- **Where:** `backend/routes/command_center.py` L967 (pre-migration).
- **Symptom:** `try: await _seed_defaults(db) except Exception: pass`. If seeding fails at boot, there is no log line — silent failure.
- **Impact:** Command-center endpoints self-heal (they call `_seed_defaults` again on first hit), so no user impact. But the boot log is quiet on failure.
- **Classification:** **E — Intentional Design** (silent-on-error was explicit per the pre-migration comment: `# silent: not blocking app boot if seeding fails`).
- **Owner:** Backend team.
- **Target track:** Not scheduled — the self-heal path is sufficient.
- **Action taken in 22.1L:** Preserved silent-on-error semantics verbatim in `_command_center_seed_defaults` to maintain zero-drift. Bytecode fingerprint locked.

### F4 · Two `regex=` warnings could cascade to Pydantic v3 boot failures
- **Where:** Same as F1.
- **Classification:** **C — Engineering Debt** (already tracked under F1).

### F5 · `routes.command_center._seed_defaults` still exposed publicly
- **Where:** `backend/routes/command_center.py` L948.
- **Symptom:** Module-level function is imported both by the endpoint bodies (correct) and now by `server.py::_command_center_seed_defaults` (new consumer).
- **Impact:** Not a defect — clean API surface.
- **Classification:** **D — False Positive** (this is intentional export).
- **Owner:** N/A.
- **Action taken:** None.

### F6 · No `TRACK_22_1K_*` deliverables yet
- **Where:** `memory/`.
- **Symptom:** Shutdown migration deliverables not yet created.
- **Impact:** Expected — that track hasn't started.
- **Classification:** **F — Future Enhancement**.
- **Owner:** Backend team.
- **Target track:** **22.1K**.

## Summary
| Class | Count | Notes |
|---|---:|---|
| A · Fix Now | 0 | — |
| B · Blocks Deployment | 0 | — |
| C · Engineering Debt | 2 | F1 (regex→pattern), F2 (orphan coroutine) |
| D · False Positive | 1 | F5 |
| E · Intentional Design | 1 | F3 (silent-on-error) |
| F · Future Enhancement | 1 | F6 (Track 22.1K) |
| **Total** | **5 findings, all classified** | |

No unclassified findings. Nothing hidden. Nothing deferred without an owner.
