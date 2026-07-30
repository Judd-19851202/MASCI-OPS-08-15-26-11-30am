# WP16 Wave 5 — Executive Repair Summary

Date: 2026-07-30

## Executive scope statement

- Wave: **5 — Safety Certification**
- Phase executed: **Phase 3 — Authorized Repair Pass**
- Authorized issues only:
  - `WP16-W5-001`
  - `WP16-W5-002`
- Production changes made: **Yes — limited to the two authorized issue IDs**
- Unauthorized issues repaired: **None**
- Wave 6 work started: **No**
- WP-17 work started: **No**

## Phase 0 — Shared root cause analysis

### Shared-foundation determination

Both authorized issues were confirmed to belong to the **same authentication/session-management domain**, but they did **not** reduce to one identical code defect.

- **Common category:** hidden/detail route auth-contract drift from the current Safety portal session model
- **Shared foundations reviewed:**
  - Safety portal session handling
  - authentication header generation
  - token lookup / parsing
  - shared API request utilities
  - hidden/detail route authorization behavior
  - shared authentication helpers

### Result

- **Common domain confirmed:** Yes
- **Single shared code root cause confirmed:** No

### Why it was not a single repair

1. **WP16-W5-001** originated in the shared API request-scoping foundation. `/api/safety-forms/*` was not classified as a Safety-session-capable namespace, so the generic API client did not forward `X-Safety-Token` for Safety Portal operators.
2. **WP16-W5-002** originated in two hidden/detail report viewers that bypassed current auth helpers and read obsolete token storage keys (`safety_token`, `admin_token`, `pm_token`) instead of the active namespaced portal session contract.

Because one patch could not safely fix both defects, the repair pass applied the **smallest safe repair at each actual faulty auth layer**:

- one shared request-scope repair for `WP16-W5-001`
- one shared viewer-auth contract repair pattern for `WP16-W5-002`

## Root cause and repair details

### WP16-W5-001 — CLOSED

- **Issue:** Safety Forms detail/return routes failed for valid Safety Portal sessions
- **Impacted experiences:** `W5-004`, `W5-005`, `W5-007`
- **Root cause:** `frontend/src/lib/portalAuthScope.js` did not classify `/api/safety-forms/*` as a shared API namespace for the active portal, so the shared `api` client never attached `X-Safety-Token` on those requests unless a legacy Safety Forms token also existed.
- **Smallest safe repair:**
  - added `/safety-forms` to the shared API scope list in `portalAuthScope.js`
  - updated the `api.js` 401 cleanup branch for `safety-forms` namespace requests so Safety/Admin session cleanup stays aligned with the headers now being sent

### WP16-W5-002 — CLOSED

- **Issue:** Incident report viewers failed for valid Safety Portal sessions
- **Impacted experiences:** `W5-018`, `W5-019`
- **Root cause:** `frontend/src/pages/IncidentReportViewer.jsx` and `frontend/src/pages/ExecutiveCaseReport.jsx` used stale localStorage keys instead of shared auth helpers, so valid `masci.safety.token` sessions were invisible to those pages.
- **Smallest safe repair:**
  - replaced obsolete token lookup logic with `buildScopedPortalAuthHeaders(["safety", "admin", "pm"])`
  - replaced unauthenticated PDF open flows with authenticated blob-download flows using the same scoped headers so the route and its download action use one consistent auth contract

## Files modified

1. `frontend/src/lib/portalAuthScope.js`
2. `frontend/src/lib/api.js`
3. `frontend/src/pages/IncidentReportViewer.jsx`
4. `frontend/src/pages/ExecutiveCaseReport.jsx`

## Shared foundations affected

- **Shared API auth scoping:** affected by `WP16-W5-001`
- **Shared request-session cleanup behavior:** affected by `WP16-W5-001`
- **Shared portal auth-header generation contract:** used to repair `WP16-W5-002`
- **Hidden/detail report viewer auth behavior:** affected by `WP16-W5-002`

## Verification evidence

### Self-verification

- Browser replay with a valid Safety session confirmed:
  - `W5-004` now loads the issuance detail route
  - `W5-005` now loads the issuance return route
  - `W5-007` now loads the training detail route
  - `W5-018` now loads the incident report viewer route
  - `W5-019` now loads the executive report route
- Authenticated browser download verification confirmed:
  - Safety Forms PDF download succeeds
  - Incident report PDF download succeeds
  - Executive report PDF download succeeds
- Curl verification with a valid Safety token confirmed `200` on:
  - `/api/safety-forms/equipment-issuances/98a864ae-f12c-4e81-bb33-21632af29767/pdf`
  - `/api/incident-cases/e0f08d0f-daf3-4306-b7f1-3cd118ef4d01/reports/executive_summary.pdf`
  - `/api/incident-cases/e0f08d0f-daf3-4306-b7f1-3cd118ef4d01/executive-report.pdf`

### Independent verification

- Independent frontend verification agent result:
  - repaired routes: **5 / 5 PASS**
  - regression routes: **4 / 4 PASS**
  - session continuity: **PASS**
  - conclusion: both `WP16-W5-001` and `WP16-W5-002` appear closed from the frontend perspective

## Regression testing results

### Mandatory repaired-route regression

- `W5-004` — PASS
- `W5-005` — PASS
- `W5-007` — PASS
- `W5-018` — PASS
- `W5-019` — PASS

### Additional unrelated Safety workflow regression

- `/safety-portal/forms-records` — PASS
- `/safety-portal/incidents/71477b5c-13fe-4f25-9ba0-d156bf47912c` — PASS
- `/safety-portal/meetings/00f1f93d-f76f-4224-8ebb-75fca4dd7be1` — PASS
- `/safety-portal/inspections/67555b86-7201-4eb3-806c-0a1c43823f25` — PASS

## Final disposition by authorized issue

- **Total authorized issues:** `2`
- **Closed issues:** `2`
  - `WP16-W5-001`
  - `WP16-W5-002`
- **Remaining authorized issues:** `0`

## Final operational assessment

The authorized Wave 5 repair scope is complete. Both approved defects were reproduced, root-caused, repaired at the smallest safe layer, and re-verified. The repaired hidden/detail Safety routes now honor the active Safety session correctly, authenticated PDF/download actions work again, and limited unrelated Safety regressions remained healthy after the fixes. Based on the authorized scope and completed verification evidence, Wave 5 is operationally ready for executive lock.

## Executive recommendation

**READY FOR EXECUTIVE LOCK**