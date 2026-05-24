# Phase 11 · Dispatch Lifecycle System (DLS) — Iteration Tracker

Authoritative index of the DLS iteration program. The 10 architecture
documents in `/app/memory/` (see `DISPATCH_LIFECYCLE_ARCHITECTURE.md`)
define WHAT we are building. This file tracks HOW it has shipped, what
is next, and which dev-only tools support the work.

---

## iter392 · Backend Foundation · ✅ SHIPPED 2026-05-24

**Scope:** lifecycle persistence + state machine + tenant-ready
collections + RBAC. Backend only. No UI, no analytics.

**Collections (3) — hybrid model approved by operator**

| Collection | Purpose |
|---|---|
| `dispatch_assignments` | Operational current truth · current_state + embedded `state_history[]` |
| `dispatch_state_events` | Append-only audit/analytics truth · one row per transition (mirror) |
| `haul_cycles` | Derived cycle summary truth · materialized on COMPLETE |

Every record carries `tenant_id` (default `masci`, future-ready).

**Endpoints (10) — prefix `/api/dispatch`**

| Method | Path | Gate |
|---|---|---|
| POST | `/assignments` | dispatch + admin |
| GET  | `/assignments` | any portal token |
| GET  | `/assignments/board` | any portal token |
| GET  | `/assignments/{id}` | any portal token |
| POST | `/assignments/{id}/transition` | dispatch + admin |
| POST | `/assignments/{id}/cancel` | dispatch + admin |
| POST | `/assignments/{id}/reassign` | dispatch + admin |
| GET  | `/state-events` | any portal token |
| GET  | `/haul-cycles` | any portal token |
| GET  | `/lifecycle/states` | any portal token (meta) |

**Lifecycle validation contract**

- **Forgiving mode.** Any `to_state` accepted.
- `classify_transition()` tags non-preferred transitions with
  `warning_tag="NON_STANDARD_TRANSITION"` and unknown destinations
  with `UNKNOWN_STATE`. CANCEL writes `CANCELLED`; REASSIGN writes
  `REASSIGNED`.
- `state-events?non_standard_only=true` is the query hook for
  future governance work (iter395).

**Files shipped**
- `backend/dispatch_lifecycle.py` (pure state machine)
- `backend/routes/dispatch_lifecycle.py` (router factory + writers)
- `backend/tests/test_iter392_dls_foundation.py` (23 tests, all PASS)
- `backend/server.py` (+30 LOC wiring)

**Test result:** 23 / 23 PASS in ~3.4 s.

---

## DEV-ONLY TOOLS

### `dls_seed_demo` · iter392 follow-up

Dev/local/preview-only seed helper for iter393 / iter394 development.
**Never auto-runs.** Production tenant (`masci`) is hard-blocked.

**Invocation**

```bash
# From /app/backend
cd /app/backend
python -m scripts.dls_seed_demo --reset-demo

# Direct file run (works from anywhere)
python /app/backend/scripts/dls_seed_demo.py --reset-demo
```

**Flags**

| Flag | Purpose |
|---|---|
| `--reset-demo` | Wipe demo rows before re-seeding (idempotent re-runs). |
| `--only-reset` | Wipe demo rows and exit. |
| `--tenant-id ID` | Override demo tenant (default `dls-demo`). Refuses `masci`. |
| `--base-url URL` | Override `REACT_APP_BACKEND_URL`. |
| `--admin-password PW` | Override `ADMIN_PASSWORD`. |
| `--delay SECS` | Inter-transition pause (default 0.25 s). |

**Output (default invocation)**

- 3 demo trucks (`DEMO-T-001` / `DEMO-T-002` / `DEMO-T-003`)
- Truck 1: full happy path → `COMPLETE` → 1 haul_cycles row
- Truck 2: walks to `WAITING` with `wait_reason=WAITING_ON_PLANT` and
  stays there (gives iter394 dispatch-board devs a live row to render)
- Truck 3: non-standard jump `ENROUTE_TO_LOAD → COMPLETE` → 1
  haul_cycles row + tagged `NON_STANDARD_TRANSITION` event
- All data lives under `tenant_id=dls-demo`, isolated from `masci`.

**Verification commands**

```bash
TOKEN=$(curl -sS -X POST "$URL/api/admin/login" \
  -H 'Content-Type: application/json' \
  -d "{\"password\":\"$ADMIN_PASSWORD\"}" | jq -r .token)

# 1 active row (DEMO-T-002 at WAITING)
curl -sS "$URL/api/dispatch/assignments/board" \
  -H "X-Admin-Token: $TOKEN" -H "X-Tenant-Id: dls-demo"

# 16 mirrored events
curl -sS "$URL/api/dispatch/state-events?limit=200" \
  -H "X-Admin-Token: $TOKEN" -H "X-Tenant-Id: dls-demo"

# 2 completed haul cycles
curl -sS "$URL/api/dispatch/haul-cycles" \
  -H "X-Admin-Token: $TOKEN" -H "X-Tenant-Id: dls-demo"

# 1 non-standard event (governance preview)
curl -sS "$URL/api/dispatch/state-events?non_standard_only=true" \
  -H "X-Admin-Token: $TOKEN" -H "X-Tenant-Id: dls-demo"
```

**Discipline guarantees**
- Uses the iter392 HTTP API for every transition — does NOT bypass the
  lifecycle engine.
- Refuses to run with `--tenant-id masci`.
- No scheduler, no startup hook, no auto-seed of any kind.
- `--reset-demo` is the only mutator outside the API surface; it scopes
  deletes by `tenant_id` exclusively.

---

## Roadmap (deferred)

| Iter | Title | Status | Notes |
|---|---|---|---|
| iter392 | Backend Foundation | ✅ shipped 2026-05-24 | This entry. |
| iter393 | Driver Mobile Experience | ✅ shipped 2026-05-24 | Magic-link auth (HMAC mirror of pm_auth) + revokable sessions + 7 driver endpoints (`/api/dispatch/driver/*`) + 2 driver routes (`/d/:token`, `/driver`) + 13 tests. Tap-and-work surface live in preview. |
| iter394 | Dispatch Operational Board | ⏳ planned | Live board UI consuming `/api/dispatch/assignments/board`. Uses `dls-demo` tenant for dev. |
| iter395 | Governance + Notifications + CSV | ⏳ planned | `ASSIGNMENT_STUCK`, `WAIT_THRESHOLD_EXCEEDED` detectors; 3 CSV endpoints. |
| iter396 | Coaching + Glossary + ES | ⏳ planned | 22 glossary entries + 4 LifecycleGuide instances + 2 training modules + EN/ES. |
