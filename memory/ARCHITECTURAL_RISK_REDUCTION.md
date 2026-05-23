# ARCHITECTURAL RISK REDUCTION
**Phase 4D · iter369**
**Status:** Inventory complete · no extraction performed.

The MASCI backend architecture has accumulated organic risk over 369 iterations. This document catalogs the risks and proposes a careful, regression-locked reduction plan. **Nothing in this document is being executed yet.**

---

## Risk inventory

### R1 · `server.py` is 12,217 lines
- **Risk level:** MEDIUM (no immediate behavior risk; high future maintenance risk)
- **Impact:** Any change requires loading 12k+ lines of context; refactor blast radius is huge; new contributors take days to find anything.
- **Recommendation:** Extract by **vertical slice**, never by horizontal "all routes" — i.e., pull out one self-contained portal at a time (e.g., `pm_portal.py` extraction was mentioned in earlier handoffs).
- **Risk-free extraction candidates** (based on grep):
  - `/api/pm/*` routes (~500 LOC) — already partially isolated
  - `/api/dispatch/*` routes (~400 LOC) — small surface, well-tested
  - `/api/shop/*` routes (~300 LOC) — small surface
  - `/api/leadership/*` routes (~600 LOC) — FL portal, distinct
- **Risky extraction candidates** (avoid first):
  - Auth gate definitions (23 functions cross-referenced everywhere) — wait until iter370-374 finish
  - MongoDB collection setup (`db.collection.create_index` calls scattered) — concentrate first
- **First proposed step:** Extract `pm_portal.py` (~iter380+ after auth consolidation stabilizes)

### R2 · 49 backend route files but many cross-import from `server.py`
- **Risk level:** LOW (works fine, but cleanup helps maintainability)
- **Impact:** Some route files require `server.py` to be loaded first; not strictly modular.
- **Recommendation:** No action this phase. Note for post-Phase-4.

### R3 · 24 admin pages (`/app/frontend/src/pages/admin/`) with copy-pasted shell code
- **Risk level:** LOW
- **Impact:** Adding a new admin page requires copy-pasting the AdminShell wrapper; minor inconsistency drift possible.
- **Recommendation:** Existing `AdminShell` component is already shared; further consolidation would over-engineer. Leave.

### R4 · Test directory has 215+ test files (one per iter)
- **Risk level:** LOW
- **Impact:** Test suite takes 30+ seconds to run all; some tests probe legacy endpoints.
- **Recommendation:** Periodically archive completed-arc tests (e.g., iter1-iter100 governance tests) into a `tests/legacy/` folder; only run the modern set on every commit. **Not blocking.**

### R5 · MongoDB collections (~60+) without a central schema registry
- **Risk level:** MEDIUM (governance detector queries become brittle if collection naming drifts)
- **Impact:** A future "rename `employees` to `employee_master`" would require touching dozens of files.
- **Recommendation:** Centralize collection name constants in `/app/backend/routes/_collections.py`. **Schedule for iter400+** (post-auth consolidation).

### R6 · No automated preview→prod parity smoke
- **Risk level:** LOW (manual playbook exists in POST_REDEPLOY_SMOKE_RESULTS.md)
- **Impact:** Operator does ~5 min of manual checks per deploy.
- **Recommendation:** Build a `scripts/prod_smoke.sh` wrapper that runs iter363+iter364+iter368+iter369 pytest with `BASE_URL=https://mascidocs.com`. ~30 min of work. **Cheap quick win** if operator wants it.

### R7 · ADMIN_PASSWORD env-var escape hatch
- **Risk level:** HIGH if misconfigured in prod (auth bypass!)
- **Impact:** `require_admin_strict` returns `True` if `ADMIN_PASSWORD` env var is empty (dev mode). If prod somehow ships with an empty admin password, all admin routes are wide open.
- **Recommendation:** **Audit prod env vars before next deploy.** If `ADMIN_PASSWORD` is set in prod, this is fine. If not, set it.
- **Hardening (future iteration):** Replace the "empty = allow" escape hatch with "empty = explicit 503 with 'admin password not configured'". Forces operators to be deliberate.

---

## What we did NOT find

These were searched for and found CLEAN:
- ❌ Duplicate FastAPI app instances (good — one app, one entry point)
- ❌ Hardcoded secrets in code (good — all in .env)
- ❌ Hardcoded URLs (good — all from REACT_APP_BACKEND_URL / MONGO_URL)
- ❌ Shadow governance systems (good — one detection engine, 16 rules)
- ❌ Duplicate accountability schemas (good — one `employees` collection, one canonical id)
- ❌ Conflicting auth flows (good — clear hierarchy of 23 gates)

---

## Risk-reduction roadmap (sequenced for safety)

```
iter370-374 ──── P4A auth consolidation (depends on iter369 regression lock)
                        │
                        ▼
iter375-377 ──── P4D-1 server.py extraction · pm_portal.py first
                        │
                        ▼
iter378-380 ──── P4D-2 dispatch_portal.py, shop_portal.py, fl_portal.py
                        │
                        ▼
iter381+ ──────── P4B MFA + portal governance (after auth and refactor settle)
                        │
                        ▼
iter385+ ──────── R5 collection registry · R6 prod smoke automation
```

---

## Stop conditions

Halt all architectural work and revert if:
- Cumulative pytest regression drops below 81 PASS (current baseline)
- Any of the iter369 regression-lock tests fail
- Any production smoke check fails after deploy
- Operator reports a field-side workflow break in production

---

## Verdict

Architectural risk is **manageable**. No emergency refactoring needed. The R7 (ADMIN_PASSWORD escape hatch) is the only item worth fast-tracking — recommend the operator verify prod env vars before the next deploy.
