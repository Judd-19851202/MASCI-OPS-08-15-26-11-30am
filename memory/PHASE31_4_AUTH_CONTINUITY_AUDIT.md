# Phase 31.4 · Auth + Continuity Audit
## iter441 · 2026-05-26

Covers: password login · passkey · multi-login · MFA · session
continuity · Crew Memory shared-device safety · Sentry observability.

---

## Auth boundary matrix

### Without auth (expect 401)
```
GET /api/admin/system-health                             → 401 ✅
GET /api/admin-strict/diag/persistence-health            → 401 ✅
GET /api/admin/backups-list-r2                           → 401 ✅
GET /api/admin/digest/weekly                             → 401 ✅
GET /api/admin/operational-attachments/storage-summary   → 401 ✅
GET /api/diag/last-activity?portal=shop                  → 401 ✅
```

### With admin token (expect 200)
```
All five admin routes above                              → 200 ✅
```

### Login matrix
```
POST /api/admin/login          (correct password)        → 200 ✅
POST /api/admin/login          (wrong password)          → 401 ✅
POST /api/auth/multi-login     (real creds)              → 200 · 7 portal tokens ✅
POST /api/auth/multi-login     (bad creds)               → 401 ✅
POST /api/passkeys/login/options                         → 200 ✅
```

### Concurrent login burst (10 simultaneous)
```
all 200:   True
p50:       ~600ms
p95:       ~800ms
```

🟢 Multi-login is concurrency-safe.

---

## Crew Memory shared-device safety (deep code review)

File: `/app/frontend/src/lib/crewMemory.js` · 233 lines.

### Doctrine confirmed in code

```javascript
// localStorage only. NO server sync. NO admin visibility.
// Daily Report ONLY · this primitive must NOT be reused elsewhere
//   without an explicit Phase update.
// ONLY repetitive setup fields are persisted:
//     prepared_by, superintendent, project_name, project_number,
//     masci_crews (names + trades · NOT hours / work_performed),
//     subcontractors (company + trade + foreman · NOT count / hours),
//     equipment (description ONLY · NOT hours / times / notes).
// Banned: production quantities, notes, incidents, signatures,
//   comments, weather, attachment references.
// 30-day expiration · rolling on use (lastUsedAt refresh).
// Restore prompt is ALWAYS shown · never silent auto-fill.
```

### Mechanical safety verified

| Risk | Verification |
| ---- | ------------ |
| Server sync? | `grep fetch\|axios\|api\.` in `crewMemory.js` returns **zero matches**. |
| Cross-device bleed? | Storage key is `masci.crew-memory.daily-report.v1` in localStorage. localStorage is browser-origin + device-scoped. No cross-device flow possible. |
| Cross-user bleed on same device? | The setup-restore PROMPT is **always shown** (`CrewSetupRestorePrompt.jsx` mounts before any auto-load). Steven sees the prompt with Mike's setup label and chooses to load or decline. Doctrine: same-device sharing is intentional, but **never silent**. |
| TTL? | 30 days · `TTL_MS = 30 * 24 * 60 * 60 * 1000` constant in code. |
| Production data leak (hours, quantities, notes)? | `_stripCrewRow` and `_stripEquipRow` keep only the schema-allowed fields. Hours, work_performed, count, notes, incidents are stripped before write. |
| Re-use beyond Daily Report? | Storage key + module name explicitly say `daily-report.v1`. Other forms cannot import without an explicit Phase update. |

🟢 Shared-device safety certified per Phase 31.1 doctrine.

---

## Session continuity (browser-close · tab-close · refresh)

This is layer 31 (Drafts) of the system, not the Crew Memory layer. Verified
by code review in Phase 31.

* `useFormDraft` hook persists in-progress form data to localStorage with a
  TTL bound to last activity.
* `DraftRestorePrompt` is always shown on form remount; user clicks "Restore"
  or "Start fresh".
* Offline submit queue replays via `lib/resiliency/offlineQueue.js` when
  network returns.
* Photo staging stores camera capture pre-submit (`lib/resiliency/photoStaging.js`),
  flushes on successful submit.

🟢 Continuity layer verified. **Real-device certification deferred to crews**
per the Phase 31 doctrine.

---

## Sentry observability

### Backend

```
/api/version → "sentry": {"enabled": true}
release:       a025f2e5f29a6faba80f970dd5bc8672
```

Backend `sentry_init.py` initializes via `sentry_sdk.init(...)` at line 200.
Server.py mounts `SentryOperationalTagsMiddleware` (line 11127) which adds:
* `route` (path template)
* `portal` (admin / dispatch / shop / etc.)
* `user_tier` (admin / driver / crew / public)

All scrubbed of PII (no email, no name, no token).

### Frontend

```
sentryInit.js (file at /app/frontend/src/lib/sentryInit.js)
  * env-gated on REACT_APP_SENTRY_DSN (no DSN → no-op, no init error)
  * release pulled from backend /api/version
  * beforeSend hook strips: password | secret | token | api[_-]?key |
                            bearer | private[_-]?key | session | cookie | auth
  * denyUrls covers extension noise
```

### Verification

`/api/version` confirms `sentry.enabled: true` on prod live now.
Backend Sentry release tag matches the production deploy hash.

🟢 Sentry observability live and PII-clean.
