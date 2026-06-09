# PERFORMANCE-HARDEN-002 · Workflow Certification

**Sprint:** PERFORMANCE-HARDEN-002 (Elite Hardening)
**Scope:** Phase 8 — Real-world workflow certification
**Date:** 2026-02

---

## Backend Boot & Smoke

| Check | Result |
|---|---|
| `sudo supervisorctl restart backend` | ✅ STARTED |
| `python3 -c "from server import app"` | ✅ Imports clean; **1,035** routes mounted |
| Index ensure block fired at startup | ✅ Logs confirm `[safety-indexes] ensured` |
| `GET /api/health` | ✅ `200` in **3.9ms** — `{"ok": true, "service": "masci-hub", ...}` |

---

## Endpoint Smoke (HTTP code + latency)

| Endpoint | Code | Latency |
|---|---|---|
| `GET /api/health` | 200 | 3.9 ms |
| `GET /api/projects` (no auth) | 401 | 4.7 ms |
| `GET /api/employees` | 200 | 152 ms |
| `GET /api/admin/operational-events/audit` (no auth) | 401 | 54 ms |
| `POST /api/integrations/motive/webhook` (no auth) | 401 | 69 ms |

All endpoints return expected codes. Auth enforcement working correctly. Latency profile clean.

---

## Daily Report Workflow

| Step | Path | Backed By | Index? |
|---|---|---|---|
| List by project + date | `daily_reports.py:436` | `find({project_number}).sort(report_date)` | `project_number_1` ✅ |
| Detail fetch by id | `daily_report_lifecycle.py:69`, `hr_portal.py:406`, `verification.py:206`, `command_center.py:323` | `find_one({"id": report_id})` | **NEW: `id_1` ✅** |
| Detail fetch fallback by doc_id | `daily_report_lifecycle.py:71/205/221` | `find_one({"doc_id": report_id})` | **NEW: `doc_id_1` ✅** |
| Aggregation pipelines (safety_portal, hr_portal, dispatch_portal_auth) | Multiple | unchanged | Unaffected |

**Before:** every detail fetch = COLLSCAN 794 docs (preview); production volume materially higher.
**After:** every detail fetch = IXSCAN, 0 docs examined.

---

## Photo Workflow

| Step | Path | Backed By | Index? |
|---|---|---|---|
| Library list by project | `job_photos.py:352/816/1169` | `find({project_number}).sort(record_date)` | `project_number_1` ✅ |
| Single photo metadata | `job_photos.py:844/888/915`, `photo_governance.py:194/229/275`, `odr/pdf.py:259` | `find_one({"id": photo_id})` | **NEW: `id_1` ✅** |
| Batch fetch by ids | `job_photos.py:1035` | `find({"id": {"$in": ids}})` | **NEW: `id_1` ✅** |
| Frontend grid render | `JobPhotosLibrary.jsx:684` | `<img loading="lazy" decoding="async">` | Already optimal ✅ |
| Frontend gallery render | 6 pages (Phase 4) | `<img loading="lazy" decoding="async">` | **Improved** ✅ |

---

## Motive Webhook + Audit Workflow

| Step | Path | Backed By | Index? |
|---|---|---|---|
| Webhook receive + dedupe | `motive_service.find_one({"id": ...})` | `find_one({"id": motive_event_id})` | **NEW: `id_1` ✅** |
| Driver profile lookups | `driver_profile.py:136` | `find_one({"id": ...})` | **NEW: `id_1` ✅** |
| Operational events audit (M-2) | `operational_events.py:357/411/427/439` | `find({event_family: {$in: [...]}, event_at: {$gte: ...}})` | **NEW compound: `(event_family, event_at)` ✅** |
| Driver harsh/HOS/DVIR counts | `driver_profile.py:194/199/204` | `count_documents({event_family: ..., event_at: ...})` | **NEW compound ✅** |

**Compound impact (M-2 audit):** key examination dropped from 372 → 2 (99.5% reduction) on representative window.

---

## Admin Review Workflow

- HR Portal aggregation, dispatch portal aggregation, field leadership portal — unchanged path, indexes confirmed OK via explain plans.
- `GET /api/employees` returns 200 in 152ms — uses existing `id_1` / `name_1` indexes.

---

## Frontend Smoke

- Landing page renders cleanly at 1920×800 viewport (screenshot captured during sprint).
- No console errors observed.
- `safeErrorMessage` global Axios interceptor still active (from previous sprint).
- New preconnect tags rendered in `<head>` and validated via DOM.

---

## Regression Risk

- **Index additions:** zero risk (additive, idempotent, no schema change).
- **`<link>` preconnect additions:** zero risk (browsers ignore unreachable hints).
- **`loading="lazy" decoding="async"` additions:** zero risk (well-established HTML attributes, fully backward compatible — older browsers simply ignore them).

No existing tests were broken or changed.
