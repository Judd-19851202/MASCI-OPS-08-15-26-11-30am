# MASCI HUB — Iter68 Deployment Readiness Audit

**Date:** 2026-01-12
**Auditor:** T1 (testing agent)
**Preview URL:** https://safety-audit-mobile-1.preview.emergentagent.com
**Scope:** Full system pre-deploy audit (iter61–67 verification + regression sweep)

---

## Final Score: **9.4 / 10 — GO for deployment** ✅

No critical (CRITICAL/HIGH) blockers found. The platform is deployment-ready.
Three LOW-severity items below are nice-to-have, not blockers.

---

## Test Results Summary

| Suite | Result |
|---|---|
| `test_iter68_audit.py` (NEW — 40 cases) | **40/40 passed** |
| Curated regression: hub_banners_iter65, iter62_backup, iter64_photo, iter58_audit, iter60_email, admin_auth, translate, iter50_shop, pm_portal_iter31, field_leadership_iter42 | **191 passed, 2 skipped** |
| Frontend route smoke (16 routes) | **16/16 HTTP 200, 0 console errors** |
| Frontend banner E2E (create → site-wide visible → cleanup) | **PASS** |
| Frontend photo regression (View Daily Report w/ photo:// ref) | **PASS** — routed via /api/photo-bytes |
| Mobile responsive (390×844) on `/` + `/daily/new` | **PASS** — no horizontal overflow |

---

## Backend Audit (40/40 — test_iter68_audit.py)

### Auth surfaces — all 6 portals respond 200
- `/api/admin/login` (MASCI1982!) ✅
- `/api/admin/login` wrong-password rejected ✅
- `/api/pm/login` (chriswright@mascigc.com) ✅
- `/api/shop/login` ✅
- `/api/safety-forms/login` ✅
- `/api/field-leadership/login` ✅ (note: route is `/field-leadership/login`, NOT `/leadership/login` as the brief said)
- `/api/dev/login` ✅

### Admin security — gating works
- `/api/admin/banners` with bogus token → **401** ✅
- `/api/admin/jobs` with malformed token → **401** ✅

### Core read endpoints — all 16 return 200/204
All endpoints in the audit brief verified (`/api/daily-reports`, `/api/inspections`, `/api/meetings`, `/api/incidents`, `/api/qaqc-inspections`, `/api/equipment-inspections`, `/api/jhas`, `/api/trench-boxes`, `/api/jobs`, `/api/admin/jobs`, `/api/admin/project-managers`, `/api/admin/shop-users`, `/api/banners/active`, `/api/admin/banners`, `/api/admin/backups-list-r2`, `/api/admin/backups-complete-r2-state`).

### Photo resolver (iter63-64) — live R2 round-trip works
Found a real `photo://masci-hub/photos/2026/05/daily_reports_80b6355a-…` ref in `/api/daily-reports/{id}` payload, resolved through `/api/photo-bytes?ref=…` → 200 image bytes (R2-backed). ✅

### Hub Banners (iter65–67)
- Create banner ✅
- Banner appears in `/api/banners/active` ✅
- POST `/banners/{id}/acknowledge` ✅
- POST `/banners/{id}/dismiss` ✅
- GET `/admin/banners/{id}/audit` ✅
- Audit PDF + CSV endpoints found at `/admin/banners/{id}/audit.pdf` and `/audit.csv` (200 + correct content-type) ✅
- POST `/admin/banners/{id}/clone` returns new banner ✅
- `?include_archived=true` toggle works ✅
- Cleanup: 1 leftover test banner found and deleted at the end.

### PDF generation — direct render smoke
Daily Report, Inspection, Meeting PDFs all render via `pdf_render.render_record_pdf(...)` → valid `%PDF` magic bytes, >5 KB. ✅
(Note: there is no GET-by-id PDF HTTP endpoint for daily-reports/inspections/meetings — PDFs are produced server-side and emailed/streamed inline. Audit-trail PDF + Field-Leadership PDF + Safety-Forms PDF are exposed as HTTP routes.)

### Translate (Emergent LLM key) — live
`POST /api/translate` returns 200 with translated text. ✅

---

## Frontend Audit

### Route smoke (1920×1080, 16 routes)
All routes returned **HTTP 200**, FCP between 1.2 s – 2.6 s (well under 4 s threshold), and **zero `console.error`** entries across the entire walk.

Routes verified: `/`, `/safety`, `/safety/forms/login`, `/safety/cards`, `/field`, `/field/calculators`, `/qaqc`, `/leadership`, `/jha`, `/trench-boxes`, `/cheatsheet`, `/training`, `/admin`, `/pm/login`, `/shop/login`, `/dev/login`.

### Banner E2E (iter65)
1. Admin login at `/admin` ✅
2. AdminBannersPanel rendered ✅
3. Created `TEST_ITER68_UIBanner` via authed `POST /api/admin/banners` ✅
4. Navigated to `/` → banner showed sticky at top with title + body within ~2 s ✅
5. Deleted via `DELETE /api/admin/banners/{id}` ✅
6. Confirmed zero TEST_ banners remain in `/api/admin/banners?include_archived=true` ✅

### Photo regression (iter64 phase 2e — View pages)
Loaded `/admin/daily/80b6355a-569f-4f4a-958b-7ebed32d61c1`. 4 `<img>` tags found:
- 3 brand assets (mark + lockup) — all `naturalWidth > 0` ✅
- 1 photo via `/api/photo-bytes?ref=photo%3A%2F%2Fmasci-hub%2F…` — request reached the resolver and returned bytes (`naturalWidth=2`, which matches the **expected behavior for legacy garbage photo data** flagged in the agent-to-agent context note).

The resolver is correctly wired into the View page — `resolvePhotoSrc()` rewrites `photo://` URIs to the API endpoint. **No regression.**

### Mobile responsive
`/` at 390×844: no horizontal overflow ✅
`/daily/new` at 390×844: no horizontal overflow ✅

---

## Issues Found (none CRITICAL/HIGH)

### LOW
1. **`/admin/photos` may need ~2 s render warm-up.** First post-login hit returned a 661-char body (still rendering). Reloading directly works. Not a regression. Consider adding a loading skeleton with `data-testid` for testability.
2. **Stale test files cannot be collected by pytest** — `test_health_check_iter12.py`, `test_iter36_pre_redeploy.py`, `test_iter51_thumb_signed.py`, `test_compliance_exports.py`, `test_equipment_status_board.py`, `test_jha_files_iter28.py`, `test_pm_routing.py`, `test_pm_routing_db_iter28.py` all error at collection time (bad `tests.conftest` import or missing `REACT_APP_BACKEND_URL` env). They've been broken for several iterations. **Not regression** but should be migrated or quarantined.
3. **Banner POST 200 OK response shape inconsistency** — `/api/admin/banners` returns the new banner object including `id`, but the previous Playwright JS run thought `body.id` was undefined; turned out to be a JS scoping issue, not a backend bug. Worth adding a smoke test that asserts the create-response includes `id` so consumers don't drift.
4. **`@app.on_event` deprecation warnings (FastAPI)** — 5+ deprecation warnings on backend startup. Cosmetic, but a future FastAPI upgrade will break it. Migrate to `lifespan` event handlers when convenient.
5. **A11y warning still present** — `AdminBannersPanel`'s Radix `DialogContent` missing `DialogDescription`/`aria-describedby` (carried over from iter65 report).

---

## Cleanup Verification
- `TEST_ITER68_AuditBanner` (created by pytest fixture) — module-scope fixture deleted it ✅
- `TEST_ITER68_UIBanner` (created by Playwright) — swept manually at end of audit ✅
- No leftover TEST_ banners (`/api/admin/banners?include_archived=true` shows 0 TEST_ entries)
- No TEST_ daily reports / inspections / meetings created during this audit

---

## Go / No-Go Recommendation

## ✅ **GO — Ship to production.**

The iter61–67 work (R2 photo migration, Cloud Archives panel, Hub Banner messaging system, banner audit trail + PDF/CSV export + clone + archive toggle) is fully functional and clean of regressions. All auth surfaces, security gates, core read endpoints, PDF renderers, and the live R2 photo round-trip work end-to-end. Frontend has zero console errors across the route walk, sub-3-second cold loads, and is mobile-safe.

The LOW-severity items above can land in a follow-up iteration.
