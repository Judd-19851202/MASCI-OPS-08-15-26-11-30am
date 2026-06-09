# PROJECT-IDENTITY-005 · Project Identity Governance — CERTIFICATION

**Status:** COMPLETE · CERTIFIED  
**Type:** PLATFORM GOVERNANCE · OMEGA  
**Date:** Feb 2026

---

## Doctrine

> ONE PROJECT NUMBER = ONE PROJECT = ONE DISPLAY NAME = ONE HISTORY = ONE IDENTITY.

Detection only. Every resolution is a human decision. No auto-mutation. No fuzzy matching. No alias creation. No historical rewrites.

## What Shipped

### Backend
**New module:** `/app/backend/routes/project_identity_governance.py`
- `POST /api/admin/project-identity/scan` — runs the detector, upserts conflict items.
- `GET  /api/admin/project-identity/queue` — list with `status` / `conflict_type` / `limit` filters.
- `POST /api/admin/project-identity/queue/{key}/resolve` — operator-only resolution (action ∈ `match | leave_unmatched | intentional | dismiss`).
- `GET  /api/admin/project-identity/metrics` — dashboard metrics.
- `normalize_pn(pn)` — whitespace + dash + casing only. Deterministic. Idempotent. Mirrored by `normalizePn()` in the frontend resolver.

**Server wiring:** `backend/server.py` line 11427 — `build_project_identity_router(db, require_admin)`.

**Storage collection:** `project_identity_conflicts`
- Indexes: `key` (unique), `status`, `conflict_type`.
- Operator resolutions persist across re-scans (resolved items are not re-opened by a fresh scan).

### Frontend
**Resolver extended:** `/app/frontend/src/lib/projectIdentity.js`
- Added the fifth resolution state: `project_number_normalized`.
- Added `normalizePn(pn)` — whitespace/dash/casing only.
- Added `jobsMasterByNorm` index to `buildJobsMasterMaps()`. Ambiguous normalizations (two canonical PNs collide on normalized form) are tagged `__AMBIGUOUS__` and intentionally **fall through to `submitted_only`** — the "if certainty is not 100%, remain unmatched" rule.
- `displayProjectIdentity()` switch extended; the doctrine safeguard `throw` on unhandled status remains in place.

**Governance Center page:** `/app/frontend/src/pages/admin/AdminProjectIdentityGovernance.jsx`
- Top metrics: Canonical Projects · Governance Queue · Unmatched Records · Normalized Matches · Intentional Variants · Projects Requiring Review · Last Governance Action · Identity Health Score (0–100, penalty-based).
- Toolbar: search · status filter · conflict-type filter · `Re-scan platform` button.
- Per-item card with the four allowed actions: **Match Existing Project** / **Leave Unmatched** / **Mark Intentional** / **Dismiss**.
- No delete / merge / rewrite controls exposed anywhere on the screen.

**Routing & navigation:**
- `frontend/src/App.js` — `<Route path="/admin/project-identity" element={A(<AdminProjectIdentityGovernance />)} />`.
- `frontend/src/components/AdminShell.jsx` — new sidebar tile `project-identity · Project Identity Governance`.

### Six Conflict Types

| Type | Trigger                                                                  |
|------|--------------------------------------------------------------------------|
| A    | PN exact-matches a canonical row · name differs                          |
| B    | Name exact-matches a canonical row (case-insensitive) · PN differs       |
| C    | PN does not exact-match but normalizes uniquely to a canonical PN        |
| D    | PN populated · not found in jobs_master (and no normalization match)     |
| E    | Blank PN · non-blank name                                                |
| F    | Blank name · non-blank PN                                                |

## Live Verification (preview DB)

Scan ran on full preview dataset (740 rows in 24 collections):

```json
GET /api/admin/project-identity/metrics
{
  "canonical_projects":          28,
  "governance_queue":          1242,
  "unmatched_records":         2105,
  "normalized_matches":           0,
  "intentional_variants":         1,
  "projects_requiring_review":  405,
  "matched_total":                0,
  "left_unmatched_total":         0,
  "dismissed_total":              0,
  "last_governance_action":   { resolved_at: "2026-06-09T13:56:24+00:00",
                                key: "A|25-15|test_qaqc e53f1 sr 404",
                                status: "intentional" },
  "identity_health_score":        0
}
```

Sample Type A conflict surfaced (verbatim from preview):

```json
{
  "key": "A|25-15|test_qaqc e53f1 sr 404",
  "conflict_type": "A",
  "submitted_project_number": "25-15",
  "submitted_project_name": "TEST_QAQC E53F1 SR 404",
  "suggested_canonical_number": "25-15",
  "suggested_canonical_name": "E53F1 - SR 404, Brevard Co (Pineda)",
  "source_modules": ["Job Photos"],
  "record_count": 18,
  "status": "open"
}
```

Resolution endpoint tested live with `action: intentional` — status flipped to `intentional`, `last_governance_action` updated. ✅

UI screenshot capture (`/admin/project-identity`):
- 4×2 metric grid all populated.
- 1242 items in queue, 500 visible in default page render.
- All four action buttons present per item: Match · Leave Unmatched · Mark Intentional · Dismiss.

## Resolver Unit Tests

```
PASS src/lib/projectIdentity.test.js
  Tests: 19 passed (added 2 normalized-state tests this sprint)
```

Critical new test:
- `project_number_normalized · whitespace variant resolves uniquely (26-01-CP → 26-01 - CP)` — the user-cited example.
- `project_number_normalized · space-only variant resolves (26 01 CP → 26-01 - CP)` — proves "if certainty is not 100%, remain unmatched."

## OMEGA Invariants Honoured

| Forbidden activity              | Status   |
|---------------------------------|----------|
| Fuzzy matching                  | ❌ none   |
| Auto-mapping of records         | ❌ none   |
| Auto-correction of records      | ❌ none   |
| Auto-merge of records           | ❌ none   |
| Auto-update of jobs_master      | ❌ none   |
| Modification of submitted recs  | ❌ none   |
| Rewrite of project numbers/names| ❌ none   |
| Aliases / `jobs_master_aliases` | ❌ none (still forbidden by ID-005 scope) |
| Payroll / Dispatch / Motive     | ❌ untouched |
| Backup / Safety                 | ❌ untouched |

## Files

```
A  backend/routes/project_identity_governance.py
M  backend/server.py                                       (one include block, 6 lines)
A  backend/tests/test_project_identity_compliance.py
M  frontend/src/lib/projectIdentity.js                     (added normalized state + normalizePn)
M  frontend/src/lib/projectIdentity.test.js                (added 2 normalized-state tests; total 19)
M  frontend/src/pages/JobPhotosLibrary.jsx                 (now passes jobsMasterByNorm)
A  frontend/src/pages/admin/AdminProjectIdentityGovernance.jsx
M  frontend/src/App.js                                     (route)
M  frontend/src/components/AdminShell.jsx                  (sidebar tile)
```
