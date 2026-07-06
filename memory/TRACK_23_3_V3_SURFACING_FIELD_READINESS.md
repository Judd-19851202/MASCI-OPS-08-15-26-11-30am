# TRACK 23.3 — V3 DAILY REPORT SURFACING + FIELD RESILIENCY

**Status:** 🟢 SHIPPED · CERTIFIED (2026-02-06)
**Backend:** 18/18 live pytest (agent-authored) + 15/15 lock envelope (main-agent-authored).
**Frontend:** 8/8 UI checks green after P1 fix.
**Regression:** 116/116 across 22.9A · 22.9B · 23.1 · 23.3 · DR-CUTOVER-001/002.

---

## Why V3 wasn't surfacing (root cause)

Track 23.1 seeded `ui_flags.dr_v3` with `tenant_default: false` and only `pilot_users: ['pilot@masci.com']`. No admin UI existed to add real operators — every pilot enrollment required a Mongo `updateOne`. Preview visitors therefore always got V1 (correct fail-closed behavior, but no path to V3 for real testing).

## Fixes shipped

### 1 · Admin pilot control (no Mongo hand-edit)
Five new admin endpoints on `routes/ui_flags.py`, guarded by the server's existing `require_admin` dep:
- `GET /api/admin/dr-v3-flag` — read current pilot state
- `POST /api/admin/dr-v3-flag/pilot-user` `{email}` — idempotent add
- `DELETE /api/admin/dr-v3-flag/pilot-user?email=…` — idempotent remove
- `POST /api/admin/dr-v3-flag/pilot-project` `{project_number}` — idempotent add
- `DELETE /api/admin/dr-v3-flag/pilot-project?project_number=…` — idempotent remove
- `POST /api/admin/dr-v3-flag/tenant-default` `{enabled: bool}` — one-line rollback

Every write uses `$addToSet` / `$pull` (never `$set` on arrays), lowercases emails, and simultaneously removes the email from `denied_users` on add so pilots can't get stuck in split-brain.

### 2 · Session-persisted URL override
`useDailyReportV3Flag` now persists `?dr_v3=1` into `sessionStorage['dr_v3_admin_override']`. Once the operator hits `/daily/new?dr_v3=1` once, every subsequent page load on that tab stays on V3 with no query-string re-type. `?dr_v3=0` explicitly opts back out. `sessionStorage` boundary means closing the tab reverts to V1 (safe default). Rollback still one flag flip.

### 3 · V1-parity field resiliency in V3
V3 shell now composes the exact same shared hooks V1 uses (`@/lib/resiliency`, `@/lib/crewMemory`):

| Behavior | V1 hook | V3 wiring |
|---|---|---|
| Autosave (debounced + pagehide + visibilitychange) | `useFormDraft` | ✅ same hook · same form key `daily-report` |
| Draft restore prompt (pending draft from prior session) | `DraftRestorePrompt` | ✅ `[data-testid=dr-v3-draft-restore-prompt]` |
| Draft archive on successful submit | `commit()` | ✅ called after 2xx |
| Offline queue with idempotency preservation | `enqueueUpload` | ✅ fires when `navigator.onLine === false` |
| Reload-safe idempotency key | `persistIdempotencyKey` + `loadIdempotencyKey` | ✅ IDB-persisted; `Idempotency-Key` header set on online submit |
| Autosave status pill | `DraftStatusPill` | ✅ header slot; idle badge "Autosave on" wraps null return |
| Online/offline chip | `useOnlineStatus` | ✅ `[data-testid=dr-v3-offline-chip]` |

Form key is intentionally shared: a draft written under V1 can be restored in V3 the moment a pilot flag flips, and vice-versa on rollback. One draft, two shells.

### 4 · Smart Crew Memory (Restore Yesterday Setup)
V3 shows a calm, opt-in offer when `localStorage` has a prior crew setup snapshot and there's no pending draft (so we never silently overwrite mid-flight work). The offer surface (`[data-testid=dr-v3-crew-setup-offer]`) shows crew + equipment counts and two testids for the actions: `dr-v3-crew-setup-use` / `dr-v3-crew-setup-dismiss`. The `applySetupSnapshotToData` helper only restores `masci_crews[]` + `equipment[]` — never restores hours, production, safety, delays, photos, signature, or AI summary. A lock test in `test_track_23_3_v3_field_readiness.py` (`test_v3_never_restores_dangerous_fields_from_yesterday`) freezes this invariant.

## Certification snapshot

- **V3 preview**: `/daily/new?dr_v3=1` → V3 shell renders with "V3 Pilot" label
- **V1 fallback**: `/daily/new` (no query, no pilot enrollment) → V1 shell renders (verified live)
- **Rollback**: `POST /api/admin/dr-v3-flag/tenant-default {enabled:false}` — one API call
- **Admin pilot control**: `curl -X POST -H "X-Admin-Token: …" /api/admin/dr-v3-flag/pilot-user -d '{"email":"chris@masci.com"}'`
- **Field resiliency**: autosave verified on reload · draft restore prompt appears · idempotency key persists · offline chip visible when browser offline · restore-yesterday populates crew/equipment only
- **Cost codes**: still hidden when absent (unchanged from Track 23.1)
- **AI summary**: single card unchanged (Track 22.9A)
- **Photo intel**: async pipeline unchanged (Track 22.9B)
- **Notifications / ODS / Trust Spine / PDF / email**: byte-identical (V3 posts to `/api/daily-reports`)

## P1 bug fixed inline

- **DraftStatusPill wiring mismatch** (agent-found): V3 passed `savedAt={…}` + `data-testid=…` but the shared pill component reads `lastSavedAt={…}` + `testId=…`. Two-line fix + an "Autosave on" idle badge wrapper so the pill is visible even before the first save.

## Rollout runbook

```bash
API=$REACT_APP_BACKEND_URL
TOKEN=$ADMIN_TOKEN

# Add a pilot operator
curl -X POST "$API/api/admin/dr-v3-flag/pilot-user" \
  -H "X-Admin-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"email":"chris@masci.com"}'

# Pilot an entire project
curl -X POST "$API/api/admin/dr-v3-flag/pilot-project" \
  -H "X-Admin-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"project_number":"25-21"}'

# Flip tenant-wide (final rollout)
curl -X POST "$API/api/admin/dr-v3-flag/tenant-default" \
  -H "X-Admin-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"enabled":true}'

# Emergency rollback
curl -X POST "$API/api/admin/dr-v3-flag/tenant-default" \
  -H "X-Admin-Token: $TOKEN" -d '{"enabled":false}'
```

Ad-hoc admin URL override for anyone (no admin token needed):
```
/daily/new?dr_v3=1   # V3 for this browser tab
/daily/new?dr_v3=0   # revert to V1 for this browser tab
```

## Files changed

- **Modified**: `backend/routes/ui_flags.py` (added 5 admin endpoints + accept `require_admin` dep param), `backend/server.py` (pass `require_admin` to registration), `frontend/src/pages/NewDailyReportV3.jsx` (autosave + draft restore + offline queue + crew memory + fixed pill wiring), `frontend/src/lib/dailyReportV3Flag.js` (sessionStorage persistence of admin URL override).
- **New**: `backend/tests/test_track_23_3_v3_field_readiness.py` (15 lock tests), `backend/tests/test_track_23_3_v3_surfacing.py` (agent-authored, 18 live tests), `/app/memory/TRACK_23_3_V3_SURFACING_FIELD_READINESS.md`.

## Deferred

- **🔵 Track 22.9C** — PDF/email/PM screen read of `ai_accepted_summary` + photo observations (still the highest ROI gap from Track 23.0).
- **🟡 Track 23.2** — Admin UI (React) for the pilot control endpoints — currently curl-only.
- **🟡 Track 23.4** — Cost-code seeding admin UI so PMs can populate `jobs_master.cost_codes[]` without dev help.
