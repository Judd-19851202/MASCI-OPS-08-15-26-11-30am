# PHASE 29 · Production Survivability
## iter431 · 2026-05-25

## After-this-phase survivability surface
A failure must be (1) detectable, (2) diagnosable, (3) reversible,
(4) isolatable. Phase 29 extends the Phase 28.2 baseline with:

- **Operational Moments Rail** — operators can now see, per
  assignment, exactly which moments fired in what order. This
  shortens diagnosis time when a continuity event "didn't behave"
  in the field.
- **Stability governance** — TTL indexes + sweeper API. Stale
  artifacts no longer accumulate silently. Operational truth is
  protected from accidental cleanup by an explicit allow-list.
- **Weekly digest** — passive operator situational awareness without
  building a monitoring portal.

## Quick-curl verification matrix (operator-runnable)
```bash
API_URL="https://mascidocs.com"
TOKEN=$(curl -s -X POST "$API_URL/api/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"password":"…"}' | jq -r '.token')

# 1. Liveness
curl -s "$API_URL/api/health" | jq

# 2. Atlas + R2 + backup continuity (admin-strict)
curl -s "$API_URL/api/admin-strict/diag/persistence-health" \
  -H "X-Admin-Token: $TOKEN" | jq

# 3. Storage governance state
curl -s "$API_URL/api/admin/operational-attachments/storage-summary" \
  -H "X-Admin-Token: $TOKEN" | jq

# 4. Weekly digest (live render)
curl -s "$API_URL/api/admin/digest/weekly" \
  -H "X-Admin-Token: $TOKEN"

# 5. Stability dry-run (admin-strict · NEVER deletes)
curl -s -X POST "$API_URL/api/admin-strict/stability/sweep?dry_run=true" \
  -H "X-Admin-Token: $TOKEN" | jq

# 6. Operational Moments rail (pick any live assignment id)
ASGN="$(curl -s ... | jq -r '.items[0].id')"
curl -s "$API_URL/api/dispatch/operational-moments/by-assignment/$ASGN" \
  -H "X-Admin-Token: $TOKEN" | jq

# 7. Evidence audit pulse
curl -s "$API_URL/api/admin/legacy-imports/audit?limit=10" \
  -H "X-Admin-Token: $TOKEN" | jq '.items[].action' | sort | uniq -c
```

## Continuity guarantees (unchanged + extended)
| System                  | Guarantee                                                  |
|-------------------------|------------------------------------------------------------|
| Mongo Atlas             | Live · `persistence-health` exposes mongo_version + collections + drift status |
| R2 cold-storage         | All op_attachments rows R2-backed · proof in `storage-summary.migrated_pct` |
| Nightly archive         | iter383 scheduler · zip integrity logged                  |
| Hourly snapshot         | Preserved                                                  |
| Drift watcher           | Heartbeat surfaced via persistence-health `drift_watch_active` + digest `drift_warnings` |
| Operational truth       | Protected by stability governance allow-list              |
| Operator awareness      | Weekly digest delivered Mondays                           |

## Phase 29 made survivability… more legible
- Survivability artifacts (last backup time, mongo version, atlas
  state, drift heartbeat) used to live in 3 different endpoints and
  no human-readable summary. Now there's a one-paragraph weekly
  email AND a chronological per-assignment rail.
- Cleanup is now explicit, allow-listed, dry-run by default —
  reducing the chance of operational truth being lost to a careless
  janitorial pass.

## Verified this phase
- ✅ `/api/health` (preview)
- ✅ `/api/admin-strict/diag/persistence-health` returns full field set live
- ✅ `/api/admin/operational-attachments/storage-summary` returns expanded fields
- ✅ `/api/admin/digest/weekly` renders the doctrine plaintext
- ✅ `/api/admin-strict/stability/sweep?dry_run=true` returns counts; no rows deleted
- ✅ `/api/dispatch/operational-moments/by-assignment/{id}` returns merged chronology
- ✅ 73/73 parity-lock tests pass (Phase 28 + 29 suites combined)
- ✅ All Phase 28.2 endpoints still respond (no regression from
  fleet-deps and passkey-mint factory moves)

## Operator-owned remaining checks
- Real-device matrix (`PHASE29_REAL_DEVICE_CERTIFICATION.md`)
- Sentry inbox tag verification (`PHASE29_OBSERVABILITY_VALIDATION.md`)
- First weekly digest email lands Monday — confirm delivery
- Production `MONGO_URL` rotation in deploy dashboard (carried from
  Phase 28.1 — still pending)
