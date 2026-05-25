# SERVER_PY_MODULARIZATION_ROADMAP.md
## `server.py` Phased Extraction Plan
## iter430 · 2026-05-25

---

## Current state (real measurement)

| Metric | Value |
|---|---|
| `/app/backend/server.py` size | **11,583 LOC** |
| Already-modularized route files in `/app/backend/routes/` | 60+ |
| Total backend Python LOC | 45,090 |
| `server.py` share of backend LOC | ~26 % |

**Diagnosis:** Strong existing modularization. `server.py` is still the largest single file but contains a calmly identifiable set of remaining route groups, helpers, and bootstrap code. Extraction is mechanical, low-risk, and parity-lock-protected.

---

## Doctrine for this roadmap

| Rule | Why |
|---|---|
| **NO behavior changes** | every extracted module must produce identical HTTP responses |
| **NO API changes** | URL paths, payload shapes, headers, auth — all preserved |
| **NO schema changes** | Mongo collections untouched |
| **NO feature work** | this is pure maintainability |
| **Parity-lock required** | every extraction must run the full Phase 24-27 parity-lock subset green |
| **One extraction per session** | resist the urge to bundle |
| **Rollback strategy** | git revert is always one command away · each extraction is a single commit |

---

## Likely extraction order (from `server.py`)

### Phase 1 (FIRST · low-risk · ~300 LOC out)

**Target: `/api/legacy-imports/*` routes**

- Currently lives in `server.py` around the legacy-imports admin section
- Self-contained: own request/response shapes, no shared state with other server.py routes
- Test coverage: `test_iter238_legacy_imports.py` (already exists)
- Risk: **LOW**
- Estimated: 0.5 session
- New file: `/app/backend/routes/legacy_imports.py`

### Phase 2 (SECOND · low-risk · ~400 LOC out)

**Target: backup / archive helpers**

- Currently: `_run_complete_archive_to_r2`, `_run_scheduled_backup`, `_emergency_prune_backups`, `_backup_drift_watch`, `_disk_pct_used`, `_orphan_age_sec`, etc. — ~400 LOC scattered through server.py
- Self-contained: pure helpers + scheduler hooks
- Test coverage: iter425/iter426/iter427 (13 tests)
- Risk: **LOW**
- Estimated: 0.5 session
- New file: `/app/backend/lib/backup_pipeline.py` (helpers) + thin scheduler glue stays in `server.py`

### Phase 3 (THIRD · medium-risk · ~600 LOC out)

**Target: diagnostic / admin-only endpoints**

- `/api/admin/health-bus`, `/api/admin/system/db-host`, `/api/admin/debug-*`, etc.
- Self-contained but admin-token gated
- Test coverage: spread across admin pytest files
- Risk: **MEDIUM** (some endpoints touch multiple subsystems)
- Estimated: 1 session
- New file: `/app/backend/routes/admin_diagnostics.py`

### Phase 4 (verify · NOT extracting)

**Verify auth/passkey routing is already modularized**

- `routes/passkeys.py` ✅ already extracted (iter422)
- `routes/auth_directory_routes.py` ✅
- `routes/mfa_routes.py` ✅
- `routes/admin_directory_k4.py` ✅
- **No extraction needed for auth.** Just confirm in this phase.

### Phase 5 (verify · NOT extracting)

**Verify DLS routes already partially modularized**

- `routes/dispatch_lifecycle.py` ✅ (1,200 LOC)
- `routes/dispatch_continuity.py` ✅
- `routes/dispatch_governance.py` ✅
- `routes/dispatch_driver.py` ✅
- `routes/dispatch_day1_debrief.py` ✅
- `routes/dispatch_exports.py` ✅
- `routes/dispatch_portal_auth.py` ✅
- **DLS is well-extracted.** Just confirm.

### Phase 6 (final · medium-risk · ~500 LOC out)

**Target: guidance / help / coaching routes (if still in server.py)**

- Need to grep `server.py` for `/api/guidance/*` and `/api/help/*` patterns
- Likely already partially extracted to `routes/` but may have stragglers
- Risk: **MEDIUM**
- Estimated: 0.5-1 session

---

## Total reachable extraction (estimate)

| Phase | LOC out of server.py | Cumulative remaining server.py LOC |
|---|---|---|
| Today | — | 11,583 |
| After Phase 1 | 300 | 11,283 |
| After Phase 2 | 400 | 10,883 |
| After Phase 3 | 600 | 10,283 |
| After Phase 6 | 500 | 9,783 |
| **Net achievable in 4 sessions** | **~1,800** | **~9,800** |

Going below ~8,000 LOC starts to fight diminishing returns — the remaining code is genuinely the request-router glue + startup hooks. Stop there.

---

## Rollback strategy

Every extraction is a single git commit:

```
[iter431] extract /api/legacy-imports/* to routes/legacy_imports.py
```

If parity-lock fails or a regression is detected:

```
git revert <commit-sha>
git push to preview-branch
```

The extracted code is `import`-mounted in `server.py` via `app.include_router()` — reverting puts the code back inline, no DB migrations to undo.

---

## Parity-lock guard requirement

Before any extraction commits:

```
cd /app/backend && python -m pytest \
  tests/test_iter417_operational_attachments.py \
  tests/test_iter418_breakdown_proof.py \
  tests/test_iter419_continuity_events.py \
  tests/test_iter420_shop_recovery.py \
  tests/test_iter422_passkeys.py \
  tests/test_iter423_shop_recovery_grouping.py \
  tests/test_iter424_recovery_inline_transition.py \
  tests/test_iter425_backup_auto_discovery.py \
  tests/test_iter426_restore_drift_watcher.py \
  tests/test_iter427_legacy_backup_prune.py \
  --tb=line -q
```

**Must show 84+ passed.** If anything fails, the extraction is rejected.

---

## What this roadmap is NOT

- ❌ Not a forced timeline
- ❌ Not a deadline
- ❌ Not gated to other work
- ❌ Not a feature track
- ❌ Not a complete rewrite

Extraction happens **opportunistically** — when an engineering session has spare context budget, an extraction is a satisfying low-risk warmup. Until then, server.py stays as it is and operations continue calmly.

---

## Acceptance criteria

After each phase:

| Check | Pass condition |
|---|---|
| Parity-lock test count unchanged | 84+ tests still green |
| No new lint errors | ruff + eslint clean |
| `/api/health` 200 | service running |
| Each affected portal sign-in still works | manual smoke |
| Live admin / dispatch / shop endpoints respond identically | curl diff against pre-extraction snapshot |

---

## Status

📋 **ROADMAP COMPLETE · phases execute opportunistically**

Recommended **first extraction** when context budget allows: Phase 1 (legacy-imports). Pure mechanical move. ~0.5 session. Risk: LOW.

---

End of server.py Modularization Roadmap.
