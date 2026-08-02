# WP17D Auth + Daily Recheck · 2026-08-02

## Shared auth root cause
- `portalAuthScope.js` did not scope `/integrations/maintainx/defect-coverage` to the active portal, so shared authenticated widgets could issue unauthenticated requests after login.
- `FieldMemoryGlance.jsx` bypassed the shared portal-auth bundle instead of using `buildPortalAuthHeaders()`, which created inconsistent token forwarding and console auth noise.

## Shared files changed
- `frontend/src/lib/portalAuthScope.js`
- `frontend/src/components/field_memory/FieldMemoryGlance.jsx`
- `frontend/src/lib/__tests__/portalAuthScoping.test.js`
- `frontend/src/components/DailyReportLifecyclePanel.jsx`
- `frontend/src/pages/ViewDailyReport.jsx`
- `frontend/src/lib/i18n.js`
- `frontend/src/pages/PmOperationalIntelligence.jsx`
- `frontend/src/pages/ExecutiveIntelligence.jsx`
- `frontend/src/pages/FieldSafetyCards.jsx`
- `frontend/src/pages/SafetyFormsLogin.jsx`

## Blocked-set movement
- Classification ledger blocker set: 54 previously `BLOCKED_CREDENTIALS` routes re-opened in browser proof.
- Runtime expansion proof: 70/70 blocked runtime routes passed authenticated login, refresh, and deep-link checks in `/app/test_reports/iteration_107.json`.
- Shared-auth blocker remaining: 0 routes still blocked by the original credential/session defect.

## Daily closure evidence
- Public Daily submit proved with GPS weather refresh, camera-path photo upload, attachment upload, approved summary, signature capture, and successful outcome route (`/thank-you`).
- Admin Daily detail proved with ES route content, 6 photos, 1 attachment, signature surface, no horizontal overflow at 390px, and canonical `%PDF` artifact generation via `/api/daily-reports/{id}/pdf` async job.
- Remaining Daily certification risk: shared admin shell chrome still shows English labels in ES mode, so route-content proof is complete but full shell-wide Spanish certification still depends on shared shell localization work.

## Audited-defect movement
- Confirmed/fixed in this run:
  - `/safety/cards` ES route content localized through shared Safety Cards copy.
  - `/safety/executive-intelligence` now mounts inside a governed shell without broken auth noise.
  - `/pm/operational-intelligence` no longer exposes a raw 401 to the user.
  - `/safety/forms/login` now uses the governed hero icon shell.
- Remaining audited-defect family work still to disposition: `/admin/transportation`, `/admin/photos`, `/admin/executive-overview`, `/admin/platform-readiness`, plus any shell-wide ES defects shared across admin surfaces.