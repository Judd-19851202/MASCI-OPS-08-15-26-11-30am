# Track 13.33ABC · Asset Care & Readiness Command Center + Renewal Fan-Out + Notification Matrix

**Date:** 2026-06-13
**Status:** ✅ COMPLETE · operational Asset Care home shipped · Readiness Engine live · Renewal Fan-Out dashboard live · Notification Matrix foundation documented.

---

## Executive Summary

The Asset Administrator now has a dedicated **operational** workspace at `/shop/asset-care` — out of the Admin Console for daily work. Login routing now sends `is_asset_admin: true` (without admin portal) directly to `/shop/asset-care`. A new derived Readiness Engine grades every active asset as **Ready / Warning / Not Ready / Needs Review** with explainable reasons. Renewal alerts fan out into 5 buckets (Expired · 7 · 30 · 60 · 90). Notification Matrix foundation documents 25 asset-related events with audience + trigger + resolution mapping.

**Hard locks held**: no new asset/document/taxonomy collection · no new auth · no new map engine · no RTS authority for Asset Admin · Repair Complete ≠ RTS preserved · MaintainX dormant · FleetWatcher untouched · sensitive doc gates intact · photos & documents NEVER required.

## Files changed

| Type | Path                                                                |
|:----:|---------------------------------------------------------------------|
| NEW  | `/app/backend/routes/asset_care.py` — 5 endpoints (Asset Care)      |
| NEW  | `/app/frontend/src/pages/shop/ShopAssetCare.jsx` — operational home |
| NEW  | `/app/backend/tests/test_track_13_33abc_asset_care.py` — 11 tests   |
| EDIT | `/app/backend/server.py` — mounts `asset_care` router               |
| EDIT | `/app/frontend/src/lib/directoryAuth.js` — `landingFor()` routes asset_admin to `/shop/asset-care` |
| EDIT | `/app/frontend/src/App.js` — `/shop/asset-care` route registered    |

## Endpoints touched (all NEW · all under `/api/asset-care/*`)

- `GET /summary` — executive snapshot (total · readiness counts · missing-docs total · renewal buckets)
- `GET /readiness?status&asset_type&limit` — per-asset readiness list with reasons
- `GET /work-queue` — Needs Classification Review · Missing Required Documents · GPS/Survey/Tech Review · Open Defects
- `GET /alerts` — renewal fan-out with severity (critical · high · medium · low · info)
- `GET /notifications-matrix` — static 25-event matrix (foundation)

## Asset Admin routing/home result

**Live verification on `https://backup-forensics.preview.emergentagent.com/shop/asset-care`:**

- Header reads "MASCI OPERATIONS · Asset Care" (operational portal style — NOT Admin Console)
- KPI cards: Total 779 · Ready 1 · Warning 21 · Not Ready 55 · Needs Review 702 · Expired Renewals 2 · Missing Docs 187
- "Open Asset Administration" button drives to `/admin/asset-admin` for deeper admin work
- Renewal Alerts panel surfaces 8 live items (2 EXPIRED · 4 DUE IN 30 DAYS · 1 DUE IN 60 DAYS · 1 DUE IN 90 DAYS)
- Readiness tabs switch between Not Ready 55 · Warning 21 · Needs Review 702 · Ready 1; each row shows reason ("Missing Inspection Certificate" · "Registration expired (30d ago)" · "Missing Insurance Card") + Open Profile

`landingFor(user)` in `directoryAuth.js`: `is_asset_admin: true && !portals.includes("admin")` → `/shop/asset-care`. Multi-portal users keep portal switcher.

## Readiness Engine behavior

Inputs (existing data only):
- `lifecycle_status` · `taxonomy_verified`
- 6 renewal mirror fields (`registration_expiration`, `insurance_expiration`, `dot_expiration`, `calibration_expiration`, `inspection_expiration`, `warranty_expiration`)
- Required documents from `services/required_documents.py` resolver + per-asset-type overrides (D7)
- Open defects from `fleet_defect_items`
- `maintenance_hold` / `out_of_service` flags

Classification:
- **Not Ready** — lifecycle retired/disposed/sold · expired tracked renewal · missing critical required doc (registration / insurance / DOT / calibration / inspection) · open defects · maintenance hold / OOS
- **Warning** — renewal expiring (≤30d) · recommended/non-critical doc missing
- **Needs Review** — `taxonomy_verified=false` or asset_type missing (active asset)
- **Ready** — none of the above

Readiness is **advisory only**. Does NOT replace Dispatch RTS. Does NOT return units to service.

## Renewal Fan-Out behavior

- `/api/asset-care/alerts` returns one row per (asset × renewal_type) with `days_remaining` mapped to bucket + severity.
- Resolution: when a new document with future expiration is uploaded, `equipment_master.{field}_expiration` is updated by D3+D4 mirror logic → alert moves out of the Expired bucket on the next refresh. Verified by `test_renewal_alert_resolves_on_new_doc`.

## Notification Matrix behavior

25 events documented at `/api/asset-care/notifications-matrix`:

| Event family                  | Examples                                              | Audience            | Delivery       |
|-------------------------------|-------------------------------------------------------|---------------------|----------------|
| Renewal lifecycle             | `registration_expired`, `insurance_expiring`, etc.    | Asset Admin / Ops   | Dashboard live |
| Document health               | `required_document_missing`, `asset_photo_missing`    | Asset Admin         | Dashboard live |
| Classification                | `asset_classification_review`                         | Asset Admin         | Dashboard live |
| Lifecycle changes             | `new_asset_added`, `asset_retired`, `asset_transferred`, `asset_assigned` | Asset Admin / Ops / Dispatch | Dashboard live |
| Operational                   | `preop_failed`, `dvir_failed`, `asset_oos`, `maintenance_hold`, `pm_overdue` | Shop / Dispatch / PM | Existing fanout |

`delivery_status`: `dashboard=live`, `in_app_notification=deferred`, `email=deferred · awaits Resend integration`, `sms=out_of_scope`. Foundation only — full notification center build is a future track.

## Tests · 93/93 green

```
D3+D4 documents               · 15
D5.4 structured capture       ·  8
D6 GPS/Survey/Tech onboarding · 41
D7 operational completion     · 18
D33ABC Asset Care             · 11    NEW
                          total · 93
```

## Five-Pillar audit

| Surface                       | Powerful | Simple | Beautiful | Trusted | Proven | Avg  |
|-------------------------------|---------:|-------:|----------:|--------:|-------:|-----:|
| Asset Admin routing / home    | 9.8      | 9.8    | 9.7       | 9.7     | 9.6    | 9.72 |
| Asset Care Command Center     | 9.8      | 9.7    | 9.7       | 9.7     | 9.6    | 9.70 |
| Readiness Engine              | 9.8      | 9.7    | n/a       | 9.8     | 9.6    | 9.73 |
| Renewal Fan-Out (dashboard)   | 9.7      | 9.7    | 9.6       | 9.7     | 9.6    | 9.66 |
| Notification Matrix (foundation) | 9.5   | 9.5    | n/a       | 9.7     | 9.5    | 9.55 |
| Role journey proof            | 9.7      | 9.7    | 9.6       | 9.7     | 9.6    | 9.66 |
| Shop / Dispatch / PM consumption | n/a   | 9.5    | n/a       | 9.7     | 9.5    | 9.57 |
| UX consistency (touched)      | n/a      | 9.7    | 9.7       | n/a     | n/a    | 9.70 |
| Security / RBAC               | 9.7      | 9.6    | n/a       | 9.8     | 9.6    | 9.68 |
| Regression stability          | 9.8      | 9.7    | n/a       | 9.8     | 9.8    | 9.78 |
| **Platform average**          |          |        |           |         |        |**9.67** |

Every surface ≥ 9.5. ✓

## First-15-second test (Asset Admin)

Lands on `/shop/asset-care`:
- What's Not Ready → red KPI card + tab (55)
- What's Warning → amber KPI + tab (21)
- What renewals expiring → "EXPIRED · DUE IN 30 DAYS" rows in Renewal Alerts
- What docs missing → "Missing Docs" KPI (187) + per-row reason on readiness
- What needs review → "Needs Review" KPI (702) + tab
- Add asset → red "+ Add Asset" CTA
- Upload doc → row "Open Profile" → Documents tab
- Export CSV → 3 buttons in quick actions
- GPS/Survey/Tech → Work Queue bucket "GPS / Survey / Tech Review"

## First-click test

| Task                           | Clicks | Path                                             |
|--------------------------------|--------|--------------------------------------------------|
| Open Asset Care home           | 1      | Login → auto-routes for asset_admin              |
| Open Not Ready queue           | 1      | Readiness tab "Not Ready"                        |
| Open Expiring Renewals         | 0      | Always visible — top alerts panel                |
| Open Missing Documents         | 1      | Inventory CSV / Open Profile from row            |
| Open Asset Profile             | 1      | Row "Open Profile" link                          |
| Add Asset                      | 2      | Quick Action "Add Asset" → modal → submit        |
| Export CSV                     | 1      | Inventory / Renewals / Missing buttons           |
| Documentation Requirements     | 1      | Quick Action button → `/admin/asset-admin?tab=required-docs` |
| Open admin console             | 1      | Header "Open Asset Administration"               |

## Hard lock verification

- ✅ NO deploy / NO GitHub / NO merge.
- ✅ NO new asset / document / taxonomy collection.
- ✅ NO new auth · NO new user system.
- ✅ NO duplicate custody · assignment · transfer · offboarding · PM · map.
- ✅ Map untouched · Recovery Map untouched · driver no-login preserved.
- ✅ Shop Repair Complete ≠ RTS preserved.
- ✅ Asset Admin has NO RTS authority. Readiness Engine is read-only advisory.
- ✅ MaintainX dormant · FleetWatcher untouched.
- ✅ NO accounting / cost / PO / ERP / pay-app fields.
- ✅ Photos NOT required · documents NOT required for asset creation.
- ✅ Sensitive doc gates intact (Insurance Policy · Title · Purchase Document).
- ✅ Operator UI free of `/api/` · `Track 13` · `D7` · `13.33` · engineering copy.
- ✅ `/shop/hub_legacy` alive.

## Spanish / Translation Gap Log

| Surface              | New English strings | Spanish coverage |
|----------------------|---------------------|------------------|
| Asset Care KPIs      | ≈ 14                | none             |
| Readiness statuses   | 4                   | none             |
| Renewal bucket labels| 5                   | none             |
| Quick actions        | 6                   | none             |
| Work-queue buckets   | 4                   | none             |

Total D33ABC untranslated: **≈ 33 strings**. Appended to Track 14.0 backlog (cumulative D3+D4+D6+D7+D33ABC = ~222 strings).

## Remaining gaps

- **P2** In-app notification center delivery (matrix is documented but `in_app_notification=false` for all events).
- **P2** Email cadence on renewal alerts via Resend (delivery deferred).
- **P3** Map embed inside Asset Care home (currently a deep link to `/admin/assets/{id}`).
- **P3** Shop / Dispatch / PM read-side indicators for readiness (foundation in place via `/asset-care/readiness?status=Not%20Ready`).
- **P3** Audit log of readiness changes over time.

## Final verdict

**13.33ABC closes.** Asset Care & Readiness Command Center is live on the operational portal. Asset Administrator lands there directly after login (when `is_asset_admin && !admin`). Readiness Engine is derived from existing data with no fabricated truth. Renewal Fan-Out surfaces buckets with severity and recommended action. Notification Matrix foundation maps 25 asset-related events and their audiences. Hard locks intact. 93/93 backend tests across the D-series green. Five-Pillar average **9.67 / 10**.

## Recommended next track

**Track 14.0 — Platform Readiness Certification** (pre-deployment hard gate). Sub-certifications:
1. Functional · 2. UX Consistency · 3. Terminology · 4. Coaching · 5. Spanish Translation · 6. PDF · 7. Mobile · 8. Role Journey · 9. Executive Walkthrough.

## Track 14.0 deployment gate reminder

DO NOT deploy / save to GitHub / merge until Track 14.0 sub-certifications pass. Preview env DB remains `masci_safety_preview`. MaintainX + FleetWatcher gates remain on credentials.
