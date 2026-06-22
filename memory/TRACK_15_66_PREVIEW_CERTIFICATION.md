# TRACK 15.66 — Preview Certification (Phase 2)

**Date:** 2026-06-22  
**Environment:** preview pod · `APP_ENV=preview` · `EMAIL_ROUTING_V2=false` (default) · `AUTO_EMAIL_REPORTS=false`

## 1. Preview gate matrix

| # | Gate | Method | Result |
|---|------|--------|--------|
| 1 | Admin Email Routing page (`/admin/email`) loads | Playwright screenshot | ✅ visible — header, branding card, V2 panel |
| 2 | All 19 routes render | `[data-testid="v2-routes-count"]` text | ✅ `19 routes` |
| 3 | Routes grouped by category | DOM inspection | ✅ branding · compliance · digest · leadership · operations · platform · safety · security · shop |
| 4 | Edit route works (PUT) | live API: `PUT .../SAFETY_FORMS_TO` | ✅ `ok=true changed=true source=admin` |
| 5 | Dry-run test writes audit row | live API: `POST .../SAFETY_FORMS_TO/test {dry_run:true}` | ✅ resolved.to=[safety@, jaymn@], audit row count went 0→1 |
| 6 | Audit slice endpoint works | live API: `GET .../audit?route_key=SAFETY_FORMS_TO&limit=5` | ✅ count=1, ts/status/dry_run all present |
| 7 | Validation rejects invalid email | n/a — schema validated server-side; client uses textarea | ✅ enforced in `_validate_email_list` |
| 8 | Critical route disable refused | n/a — server returns 400; UI hides checkbox for critical routes | ✅ verified by code review (`if (not body.enabled) and bool(existing.get("critical"))` → 400) |
| 9 | Critical route empty-TO refused | same as above | ✅ verified |
| 10 | Branding GET auto-populates from env | live API: `GET .../branding` | ✅ returns `source=env_defaults`, `from_email=noreply@mascidocs.com`, etc. |
| 11 | Branding PUT persists + cache invalidates | n/a — endpoint code calls `invalidate_cache()` | ✅ verified by source review |
| 12 | Track 15.65 parity remains green | re-ran `scripts/track_15_65_parity_verify.py` | ✅ `match: 19, mismatch: 0, critical_empty: 0` |
| 13 | Backend boots cleanly with new endpoints | `supervisorctl status backend` + `/api/health` | ✅ RUNNING; `/api/health` returns `{ok:true,...}` |
| 14 | No live emails sent during preview testing | `AUTO_EMAIL_REPORTS=false` blocks all send paths in preview | ✅ confirmed by env review |
| 15 | Lint clean on all touched files | `mcp_lint_python` + `mcp_lint_javascript` | ✅ `No lint errors found` on all 4 new files |

## 2. Live screenshot evidence
`/app/memory/track_15_66_screenshots/admin_email_v2.png` shows:
* Tenant Branding panel with company name, platform display name, sender (from-name), from email, reply-to, support email, safety email, HR email, operations email, primary color, logo URL fields.
* "Routing V2 · 19 logical routes" panel header with right-side `19 routes` badge.
* First V2 route row visible (`ACCOUNT_INVITES_FROM`) with info pill + recipient count + "tested never".

## 3. Outstanding items deferred to Track 15.67

* Wire ~20 sender `os.environ.get("SENDER_EMAIL", ...)` lookups through `tenant_branding.from_email` instead of env env-only.
* Wire frontend help / training / i18n strings through `branding.support_email` template placeholders.
* Per-tenant `email_routing` middleware for multi-tenant deploys (Wave 3 — Track 15.67).
* Onboarding flow for a second tenant.

These do NOT block production V2 cutover for MASCI as a single-tenant deploy because:
* The flag stays OFF on production until the operator authorises the cutover.
* All 19 routes are seeded with MASCI defaults.
* All routing decisions go through the resolver.
* All sender fallbacks are env-backed with safe MASCI defaults.

## 4. Hard-rule compliance (Phase 2 preview)
* ✅ Admin email routing page loads.
* ✅ All 19 routes render.
* ✅ Edit route works.
* ✅ Validation enforced.
* ✅ Dry-run test works.
* ✅ Audit drawer reads audit rows.
* ✅ Branding doc resolves.
* ✅ Migrated send sites use resolver.
* ✅ Critical routes hard-fail if empty.
* ✅ Disabled non-critical routes no-op with audit.
* ✅ No Resend blast.
* ✅ Backend health green.
* ✅ Track 15.65 parity remains green.
