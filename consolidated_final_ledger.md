# Consolidated Final Ledger

- Generated: 2026-07-24
- Preview: https://backup-forensics.preview.emergentagent.com
- Code checkpoint: `4306bde8`
- Combined regression checkpoint: `439f2adf`
- Final verdict: **VERIFIED WITH DOCUMENTED PRODUCTION-ONLY CHECKS**

## Original Findings

- **DEF-001 · `/api/admin/login`** → **DEPRECATED AND SAFELY RETIRED**
  - Runtime: `410 Gone`
  - Canonical admin auth remained healthy.

- **DEF-002 · `/api/hr/check`** → **DEPRECATED AND SAFELY RETIRED**
  - Runtime: `404`
  - No live consumer proven.

- **DEF-003 · Legacy Field Leadership shared-secret login** → **FIXED AND VERIFIED**
  - Before: shared secret `MASCIGC` minted access without directory session, portal grant, disabled-user, must-change, or lockout checks.
  - After: route returns `410`; legacy `X-Leadership-Token` denied; canonical FL portal auth works; unassigned users denied; no frontend legacy link remains.
  - Repair SHA: `4306bde8`

- **DEF-004 · Dispatch forced-password-change fixture** → **EXPECTED FIXTURE STATE — VERIFIED**
  - Exercised end-to-end and restored.
  - Repair dependency: password parity work at `bc2081ac`.

- **DEF-005 · Admin-only incident review authorization** → **FIXED AND VERIFIED**
  - Before: admin dual-token reads failed due to bare boolean actor propagation.
  - After: `/api/incident-cases` and adjacent admin review reads pass.
  - Repair SHA: `52b504db`

- **DEF-006 · PM/Safety review-page failures** → **VERIFIED NOT A DEFECT**
  - Root cause: incomplete test headers omitted required dual-token context.

## Later Findings During Bounded Repairs

- **OPS8-RA-001 · Backup integrity external timeout** → **FIXED AND VERIFIED**
  - Before: external `502` at ~60s; internal completion ~72s.
  - Root cause: synchronous inline R2 manifest evaluation (~68.6s).
  - After: async persisted operator workflow; immediate start response; no external `502`; latest verified completed run `26.45s`, `manifest_count_evaluated=1`.
  - Repair SHA: `4306bde8`

- **LAT-001 · FL record identity attribution** → **FIXED AND VERIFIED**
  - Canonical FL create path now stamps individual creator identity.

- **LAT-002 · Async integrity job false missing-collection signal** → **FIXED AND VERIFIED**
  - Runtime exclusion doctrine now treats `backup_integrity_jobs` as regenerable.

## Legacy Field Leadership Consumer Inventory

### Retired / migrated live consumers
- `frontend/src/pages/FieldLeadershipPortalLogin.jsx` — legacy link removed
- `frontend/src/app/routing/AppRoutes.jsx` — legacy runtime route removed from active navigation
- `frontend/src/pages/FieldLeadershipHub.jsx` — no inline password gate remains
- `frontend/src/lib/api.js`, `authHeaders.js`, `searchApi.js`, `poApi.js`, `signaturesApi.js`, `sessionReset.js` — no active `X-Leadership-Token` workflow use remains

### Canonical consumers preserved
- `/api/field-leadership/portal/login`
- `X-FL-Token` flow for `FieldLeadershipHub`, `FieldLeadershipFormPage`, `FieldLeadershipView`
- Super Admin access preserved through canonical authority

## Repair B Role Matrix

| Role / Fixture | Canonical FL Login | FL Workflow Read | FL Record Create |
|---|---:|---:|---:|
| `cert.foreman@example.com` | Pass | Pass | Pass |
| Super Admin (`jaymn.judd@mascigc.com`) | Pass via canonical authority | Pass | Pass |
| Admin-only | Denied | Denied | Denied |
| PM-only | Denied | Denied | Denied |
| HR-only | Denied | Denied | Denied |
| Safety-only | Denied | Denied | Denied |
| Shop-only | Denied | Denied | Denied |
| Dispatch-only | Denied | Denied | Denied |
| Anonymous | Denied | Denied | Denied |

## Repair A Endpoint Contract

- `POST /api/admin/backups/integrity-check/start`
  - `202` queued/started
  - `409` active job already running
- `GET /api/admin/backups/integrity-check/status`
  - `202` while queued/running
  - `200` when completed/failed/stale
- `GET /api/admin/backups/integrity-check/latest`
  - latest persisted completed/failed/stale result
- `GET /api/admin/backups/integrity-check`
  - compatibility endpoint returning async state/result rather than blocking the browser request

## Production-Only Follow-Up Still Required

1. Real restore drill / recoverability remains separate from manifest integrity.
2. Physical-device coverage was not completed with real iPad/iPhone/Android/Windows Edge/Mac hardware.
3. Preview notification mode is `SAFE_CAPTURE`; no live-recipient delivery certification was performed.