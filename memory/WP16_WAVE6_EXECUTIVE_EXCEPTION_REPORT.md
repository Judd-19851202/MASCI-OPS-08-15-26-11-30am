# WP16 Wave 6 — Executive Exception Report

Date: 2026-07-30
Wave: 6 — Dispatch & Transportation

## Exception trigger

Continuous certification stop condition encountered:

- **A blocker prevents safe continuation.**

## Blocking issue

- **Issue ID:** `WP16-W6-001`
- **Surface:** `W6-008` Transportation wrapper → dispatch cleanup branch
- **Final classification:** **Shared foundation defect**
- **Observed behavior:**
  - `/transportation-operations`
  - `/transportation-operations/intelligence/cleanup`
  remain non-operational for valid Dispatch users because cleanup data never reaches a successful settled render path.

## Exact failure point

The failure point was traced to the **shared cleanup request/auth lifecycle inside the frontend loader path**, not to route registration and not to backend data generation itself.

### Verified lifecycle trace

1. **Route resolution:** successful
   - Dispatch users can reach `/transportation-operations` and `/transportation-operations/intelligence`.
2. **Route guard:** successful
   - `RequireTransportationPortal` allows valid Dispatch users into the Transportation shell.
3. **Dispatch permission evaluation / session validation:** successful outside the auto-loader path
   - direct curl with `X-Dispatch-Token` to `/api/admin/transportation/intelligence/cleanup-signals?days=30` returns `200`
   - direct browser `fetch()` with explicit `X-Dispatch-Token` from the loaded page also returns `200`
   - negative checks return correct denials: no token `401`, PM token `401`, invalid signal `404`
4. **API request construction during automatic page load:** failing point
   - the automatic cleanup loaders (`TopCleanupOpportunityCard` and `CleanupCompanionPanel`) do not achieve a successful settled authenticated request path during normal browser rendering
   - independent verification captured the cleanup endpoint returning `401 Unauthorized` during the automatic page-load path
   - when the same request is executed manually from the page with an explicit Dispatch token, the backend returns valid data immediately
5. **Backend request receipt / authorization / data retrieval:** healthy when a valid Dispatch-authenticated request arrives
6. **Frontend state update / loading exit:** never receives a successful settled automatic result, so the cleanup UI remains stuck in loading or timeout/error states

### Why this is a shared foundation defect

The defect spans both cleanup surfaces in W6-008 and sits in the shared request/auth lifecycle used by those loaders. It is not isolated to a single list row, a single cleanup signal, or a broken backend serializer.

## Why continuation must pause

The current wave lifecycle is not complete. One dispatch-visible operational workflow remains unresolved, so Wave 6 cannot be locked. Proceeding to Wave 7 would violate the continuous-wave requirement that each wave complete its own certification lifecycle before the next wave begins.

The final focused pass exhausted smallest-safe frontend repairs without restoring truthful automatic behavior. Further continuation would now require deeper auth/request redesign or broader instrumentation beyond the authorized scope.

## What was already completed before pause

- Wave 6 inventory and reconciliation
- Wave 6 full inspection
- controlled repair attempts on verified issues
- independent verification of repaired/public routes
- closure of `WP16-W6-002`

## What remains open

- `WP16-W6-001` only

## Files modified during final focused pass

- `frontend/src/pages/transportation/_shared.jsx`
- `frontend/src/pages/transportation/_views.jsx`
- `frontend/src/pages/transportation/_intelligence.jsx`

## Final verification evidence

- Positive API verification:
  - Dispatch token + curl → cleanup signals `200`
  - Repeat-open invite route `200`
  - Certificate verify route `200`
- Negative API verification:
  - no token → cleanup signals `401`
  - PM token → cleanup signals `401`
  - invalid cleanup signal → `404`
- Independent browser verification:
  - `W6-009` PASS
  - `W6-010` PASS
  - `W6-008` FAIL — cleanup route remains non-operational for Dispatch users

## Recommended Executive direction

Provide exception guidance on one of the following:

1. authorize deeper diagnosis / redesign of the shared cleanup auth-request path, or
2. reclassify / exclude the cleanup branch from the Wave 6 denominator if operationally acceptable.

## Recommendation

**NO-GO FOR WAVE 7 UNTIL WP16-W6-001 IS RESOLVED OR RECLASSIFIED**