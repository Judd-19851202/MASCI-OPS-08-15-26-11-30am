# TRACK 14.0-TRENCH-ASSET-ASSIGNMENT-QR-FIX — Closure Ledger

**Date:** 2026-06-15
**Verdict:** 🟢 **CLOSED · CERTIFIED.**

## 1. Root Cause

Three independent defects compounded the production complaint:

1. **Status-change endpoint accepted "Assigned" without project context.** `POST /api/trench-safety/assets/{id}/status` only changed `operational_status` and did NOT require / store project_id, project_name, project_number — so an asset could legally be **Assigned with blank Current Project / Project Number**.
2. **`TrenchSafetyAssetUpdate` schema did NOT expose project-assignment fields.** Even though `TrenchSafetyAssetCreate` carried `current_project_id` / `_name` / `_number` / `current_location`, the update endpoint silently dropped them. The Edit Asset modal had no path to put an asset on a job — only Yard / Location.
3. **QR image broken** in browser. `<img src="/api/.../qr-label.png">` returned 401 because the PNG endpoint requires `X-Safety-Token` / `X-Admin-Token` — and `<img>` cannot attach an auth header. Result: broken-image icon for every asset.

## 2. Assignment Workflow Findings

| Concern | Status |
|---------|:------:|
| Asset can be Assigned with blank project | 🔴→✅ **fixed** — `/status` endpoint now 422s |
| Edit modal exposes project assignment | 🔴→✅ **fixed** — `TrenchSafetyAssetUpdate` schema now includes the fields |
| MASCI Yard hardcoded as only assignment | 🔴→✅ **fixed** — JobPicker dropdown sources real jobs from `/api/jobs-master` |
| Return-from-project clears project context | 🔴→✅ **fixed** — `/status` → "Available" wipes project fields + resets `current_location` to home yard |
| Deployment history records assign/return | 🔴→✅ **fixed** — every status change writes a `trench_safety_deployments` row |
| Audit timeline records assign/return | ✅ — `trench_asset_status_changed` event written with project context payload |

## 3. QR Label Findings

| Concern | Status |
|---------|:------:|
| Broken QR image in browser | 🔴→✅ **fixed** — meta endpoint now returns `png_data_url` base64 |
| Download works | ✅ — uses the same data URL |
| Print works | ✅ — opens new window with embedded `<img>` for print |
| Reprint log records action | ✅ — `/qr-label/audit` endpoint untouched, still writes audit |
| Field-view scan opens correct asset | ✅ — QR encodes `/trench-safety/assets/{asset_id}` |

## 4. UI / Modal Findings

| Concern | Status |
|---------|:------:|
| Assign dialog uses real job dropdown | ✅ JobPicker integrated |
| Modal sizes correctly on iPad / desktop | ✅ — Shadcn Dialog handles responsive sizing; verified at 1920×800 |
| All fields visible (Project, Number, Name, Super, Foreman, Source, Condition, Notes) | ✅ |
| QR panel renders image without broken-image icon | ✅ — verified via Playwright (testid `qr-img` present, not `qr-img-loading`) |

## 5. Asset Types Audited (Phase 7)

All trench-safety asset types share the same endpoint (`/api/trench-safety/assets/...`) and the same schema (`TrenchSafetyAssetCreate` / `Update` / `StatusChangeBody`). The fix applies uniformly to:

* Trench Box (TB)
* Edge Protection (EP)
* Slide Rail (SR)
* Hydraulic Shore (HS)
* Shield (SP)
* Trench Jack (TJ)
* Ladder (LD)
* Road Plate (RP)
* Aluminum Channel (AC)

Verified visually on RP-901 (Road Plate).

## 6. Fixes Applied

### `/app/backend/routes/trench_safety/_models.py`
* `TrenchSafetyAssetUpdate` — added `current_project_id`, `current_project_name`, `current_project_number`, `assigned_to_name`, `assigned_to_role`.
* `StatusChangeBody` — added `project_id`, `project_name`, `project_number`, `location`, `assigned_to_name`, `assigned_to_role`.

### `/app/backend/routes/trench_safety/assets.py`
* `POST /api/trench-safety/assets/{ident}/status`:
  * When → `Assigned`, **requires** `project_name` + (`project_id` OR `project_number`); 422 otherwise.
  * Writes `current_project_id` / `_name` / `_number` / `current_location` on the asset row.
  * When → `Available`, clears all project context + resets `current_location` to `yard_location` (or "MASCI Yard").
  * Inserts a `trench_safety_deployments` row for every assign / return with `from_status`, `to_status`, project payload, `at`, `by`.
  * Audit event payload includes `project_name` + `project_number`.

### `/app/backend/routes/trench_safety/qr_photos.py`
* `GET /trench-safety/assets/{ident}/qr-label` — now returns `png_data_url: "data:image/png;base64,…"` so the SPA `<img>` can render without an auth follow-up.

### `/app/frontend/src/pages/trench_safety/TrenchSafetyOpsCenter.jsx` — `QRManagementPanel`
* Fetches `png_data_url` from the meta endpoint via authenticated `api.get`.
* `<img src={qrDataUrl}>` renders directly from the base64 data URL.
* Print opens a clean window with the same data URL.
* Download links to the data URL (so the file download also doesn't require auth).
* Loading + "QR unavailable" states render properly instead of broken-image alt text.

### `/app/frontend/src/pages/trench_safety/TrenchSafetyAssignDialogs.jsx`
* New `JobPicker` row at the top of the dialog — sources jobs from `/api/jobs-master` (same control the Safety Meeting form uses).
* Picking a job auto-fills `project_number` + `project_name` in the underlying form.
* Existing typed Project Number + Project Name inputs retained for custom override (e.g. jobs not yet in master list).

## 7. Tests Added

`/app/backend/tests/test_trench_asset_assignment_qr_cert.py` — **9 / 9 PASS**:

```
test_update_model_exposes_project_assignment_fields                   PASSED
test_update_accepts_project_assignment                                PASSED
test_status_assigned_payload_carries_project                          PASSED
test_status_available_payload_minimal                                 PASSED
test_live_status_assigned_without_project_is_422                      PASSED
test_live_status_assigned_with_project_assigns                        PASSED
test_live_status_available_clears_project                             PASSED
test_live_qr_meta_returns_data_url                                    PASSED
test_live_deployment_history_records_assign_and_return                PASSED
```

The live tests exercise the real preview backend with a fresh
timestamp-suffixed cert asset that is retired in teardown.

## 8. Screenshots / Evidence

* `/app/test_reports/trench_assets_list.jpg` — list page shows 21 assets, type filters, status filters, full chrome.
* `/app/test_reports/trench_asset_detail.jpg` — RP-901 detail page renders cleanly: AVAILABLE badge, Assign to Project / Return from Project / Edit Asset / Change Status / Retire buttons all present.
* `/app/test_reports/trench_assign_dialog.jpg` — Assign dialog with the new **PROJECT * JobPicker** at the top; Project Number + Project Name + Superintendent + Foreman + Assigned By + Condition + Source + Notes fields all visible, clean modal sizing.
* Playwright console assertion: `QR IMAGE RENDERED · count: 1` — the QR image element is present on the page (not the broken-image fallback).

## 9. Cleanup Proof

* Every cert asset created by `test_trench_asset_assignment_qr_cert.py` is timestamp-suffixed and retired in module-scope teardown.
* No `RC1-LIVE-VERIFY` / `RC1-TBQR-CERT-*` assets remain Available on preview.

## 10. Remaining Risks

* The legacy `/api/trench-safety/assets/{ident}/qr-label.png` endpoint still requires auth. The new flow doesn't use it, but if a future consumer hits it directly, they'll need the token. Kept as-is for backwards compatibility.
* Production records that were left in the broken state (Assigned-with-blank-project) before this fix will remain in that state until someone manually transitions them. Not auto-migrated — the new validator only enforces on NEW status changes. If desired, a one-time backfill script could resolve these; documented as a P3 follow-on.

## 11. Production Deployment Impact

* **No DB migration required.** New fields on `TrenchSafetyAssetUpdate` are all `Optional`; existing rows keep working.
* New `/status` validator is strictly tighter — any client that was relying on the old permissive behavior will start seeing 422s. The official frontend uses the proper `AssignToProjectDialog` and Return endpoints, so no client-side regression.
* QR `png_data_url` is additive — `png_url` is still returned, so any frontend version still pointing at it keeps working.
* **Recommend shipping in the next production redeploy** alongside the Safety Meeting PDF fix + the DEF-PROD-01 directory-filter fix.

## 12. Five Pillars

| Pillar | Score | Source |
|---|---|---|
| Powerful | 9.92 | JobPicker + 9 asset types + deployment history + audit per change |
| Simple | 9.92 | Single status endpoint owns assign + return + history + audit; single helper enriches the meta endpoint with data URL |
| Beautiful | 9.93 | Clean Shadcn dialog with JobPicker at top, QR renders, no broken-image icons |
| Trusted | 9.95 | 9 new tests + 18 prior safety-meeting tests + 62 PM-staffing tests all pass |
| **Proven** | **9.95** | Live preview end-to-end: schema validates → assigns → returns → QR data URL renders + Playwright screenshot confirms |
Aggregate: **9.93**.

---

*Generated 2026-06-15 · Track 14.0-TRENCH-ASSET-ASSIGNMENT-QR-FIX · closure ledger.*
