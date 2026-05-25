# PHASE 28.2 · Deployment Survivability
## iter430 · 2026-05-25

## What "survivable" means here
A production failure must:
1. Be **detectable** within minutes (Sentry exception → email/Slack
   inbox configured at the Sentry tenant level).
2. Be **diagnosable without log-diving** (tags reveal portal, role,
   route, device, language, tenant — see
   `PHASE28_2_PRODUCTION_OBSERVABILITY.md`).
3. Be **reversible** (extracted modules land in single commits that
   `git revert` cleanly · backups are nightly + integrity-checked).
4. Be **isolatable** (R2 cold-storage means a Mongo blip never takes
   attachment uploads offline · admin-strict diagnostics never
   require business-hours engineering).

## Tooling shipped this phase
- `/api/admin-strict/diag/persistence-health` → one-curl Atlas + R2
  + backup-drift verification.
- `/api/admin/operational-attachments/storage-summary` → one-curl
  storage breakdown + 90-day projection.
- Sentry operational tag middleware → portal/role/route/device/
  browser/language/tenant on every event.
- Legacy-imports extraction → `server.py` no longer holds inline
  routes (cleaner blast radius for future changes).

## Continuity guarantees (unchanged from Phase 27)
| System            | Guarantee                                                  |
|-------------------|------------------------------------------------------------|
| Mongo Atlas       | Hot copy live · `last_backup_time` exposed via diag        |
| R2 cold-storage   | All 70 op_attachments rows R2-backed · `migrated_pct=100`  |
| Nightly archive   | iter383 scheduler · zip integrity check · log-only on fail |
| Hourly snapshot   | Preserved unchanged                                        |
| Drift watch       | Heartbeat surfaced via persistence-health `drift_watch_active` |

## Operator runbook (paste into a calendar reminder · weekly)
```bash
API_URL="https://mascidocs.com"
TOKEN=$(curl -s -X POST "$API_URL/api/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"password":"…"}' | jq -r '.token')

# 1. Atlas + R2 + backup continuity
curl -s "$API_URL/api/admin-strict/diag/persistence-health" \
  -H "X-Admin-Token: $TOKEN" | jq

# 2. Storage growth check
curl -s "$API_URL/api/admin/operational-attachments/storage-summary" \
  -H "X-Admin-Token: $TOKEN" | jq

# 3. Last 50 admin audit rows (sanity scan)
curl -s "$API_URL/api/admin/legacy-imports/audit?limit=50" \
  -H "X-Admin-Token: $TOKEN" | jq '.items[].action' | sort | uniq -c

# 4. Sentry inbox check
#    → open Sentry; filter the last 7 days by environment=production;
#      every grouped issue should show portal+role+route+device tags.
```

## "Three-buttons survives" thought experiment
If the operator only has 3 admin buttons left, which 3 cover every
production failure mode?
1. **persistence-health** — proves Atlas + R2 + backups are alive
2. **storage-summary** — proves attachments aren't bloating Mongo
3. **legacy-imports/audit** — proves the HR/Safety evidence pipeline
   hasn't silently stopped

If any of those three answer wrong, the operator escalates before
real users notice. Everything else is fast-followers.

## What this phase did NOT add (doctrine restraint)
- ❌ No status page · no monitoring portal
- ❌ No notification system (Sentry's own delivery is enough)
- ❌ No "platform health" UI inside MASCI
- ❌ No retry-storm protection beyond what's already in place
