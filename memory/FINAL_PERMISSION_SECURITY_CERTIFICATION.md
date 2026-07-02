# FINAL Permission / Security Certification

**Verdict:** 🟢 **PASS** — role gates enforced. Legacy hardening intact. Preview safety on.

## Access model

| Surface | Access | Enforced by |
|---|---|---|
| `/incidents/report`, `/daily/submit`, `/equipment/submit`, `/fleet/dvir/new`, `/meetings/submit`, `/near-miss` | **Public (no login)** — field forms | Router registration in `App.js` |
| `/admin/*` | Admin only | `A(...)` wrapper in `App.js` |
| `/transportation-operations/*` | Transportation role | `TX(...)` wrapper |
| `/safety/*` (workspace, cases, exec intel) | Safety / Admin / PM | Backend `require_actor` dependency |
| `/api/incident-cases/*` | Safety / Admin / PM | `Depends(get_current_actor)` |
| `/api/incident-cases/*/pdf/*` | Safety / Admin / PM | Same |
| Legacy `/api/incidents` (untouched) | 401 UNAUTH (hardened) | Auth middleware |
| Legacy `/api/admin/login` (retired) | 410 GONE | Deprecation gate |

## Verified in this gate

- Public forms remain accessible without login (screenshotted and confirmed by testing agent).
- Backend `Safety, Admin, or PM login required` message returned on `/api/incident-cases/*/vocabulary` — verified in Track 19.17 stabilization pass.
- Legacy endpoint deprecation returns 410 GONE — verified today at code + test level.
- HR Source-of-Truth (`/api/hr/*` endpoints) remain protected via role gates — no changes in Track 19.18.
- No raw sensitive data (SSN, DOB, wage) is exposed by field forms. Field forms collect operational data only.
- Incident reports do NOT expose restricted Safety-only information to field users (Safety-only tabs are gated at the Safety Case Workspace level, not on the Field submit form).
- PDFs are audience-labeled — Client Package doesn't include OSHA-only appendices, and vice-versa.

## Preview environment safety

- Persistent orange band `⚠ PREVIEW ENVIRONMENT · DB: MASCI_SAFETY_PREVIEW · DO NOT ENTER REAL OPERATIONAL DATA` on every screen.
- Preview DB isolated from production (`MASCI_SAFETY_PREVIEW`).
- SMTP is either disabled or points to a preview relay in this env (no production email risk during preview walkthrough).

## No permission drift

- No new endpoints registered in Track 19.17 or Track 19.18 that bypass role checks.
- All new incident-engine endpoints inherit `Depends(get_current_actor)` from `incident_engine/routes.py`.
- Safety Case Workspace client-side does not enable actions above the caller's role (client-side hides + server-side enforces).

## Verdict

🟢 **No permission drift. No credential leak. No public-form exposure of restricted data.**
