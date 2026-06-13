# TRACK 13.31B-D2 — Asset Admin UI + AssetProfile Extension

**Status:** CLOSED · 2026-06-13
**Mode:** Controlled implementation · Day-2 only · UI for the Day-0/Day-1 spine · NO doc vault · NO CSV/PDF · NO new collections · NO deploy · NO GitHub · NO merge.
**Authorizes:** 13.31B-D3 (Document Vault) to fork against this surface.

---

## 1 · Executive Summary

Day-2 of the Asset Administration Spine shipped cleanly:

* **New operator page** `/admin/asset-admin` — verified, MASCI-native review queue + legacy crosswalk panel.
* **AssetProfile** gained an **Admin** tab — surfaces every canonical taxonomy + 13 administrative fields, with an in-place Edit→Save form gated by the existing admin-only route guard.
* **Backend additive tweaks** only:
  * `taxonomy_verified_at` + `taxonomy_review_reason` added to the PATCH legal-key whitelist.
  * `update_asset()` auto-stamps `taxonomy_verified_at` (and clears the review reason) when the verified flag flips to `True` without explicit caller value.
* **7 new pytests** for D2 (60/60 cumulative on Track 13.31 + 13.30 suites · zero regression).
* **No new collection.** No duplicate spine. `equipment_master` remains canonical.
* Live preview proven: queue surfaces 200 review-needed assets, PATCH stamps canonical class/type, and the next reload removes the row from the queue.

---

## 2 · UI Surfaces Delivered

### `/admin/asset-admin` — Asset Administration

**Header**
* Spine version chip (`v1.0.0`)
* Title + 1-sentence operator copy.
* Refresh button.

**KPIs (4 cards)**
* Active Assets · 612 (from `/asset-spine/health`).
* Needs Review · 200 (live count from the review queue).
* Asset Classes · 13 (closed set length).
* Asset Types · 92 (behaviour-matrix derived).

**Tabs**
1. **Review Queue** — one card per `needs_review` asset:
   * Unit number + legacy fields (`category` / `preop_equipment_type` / `type`).
   * Conflict reason chip when crosswalk found a mismatch.
   * Asset Class + Asset Type selectors driven by `/asset-spine/taxonomy` enums.
   * Verify & Save → PATCH `/asset-spine/assets/{id}` → optimistic row removal.
   * "Open profile" deep-link to `/admin/assets/{id}` for full context.
2. **Legacy Crosswalk** — bulk action:
   * Dry-run preview → counts (scanned · would_verify · would_need_review).
   * Stamp canonical → confirm dialog → POST `apply-legacy-crosswalk?dry_run=false`.

### `/admin/assets/:assetId` — AssetProfile · "Admin" tab

Added as the 8th tab. Reads from `/asset-spine/assets/{id}` + `/asset-spine/taxonomy`. Six cards:

| Card | Fields |
|---|---|
| Canonical Taxonomy | `asset_class`, `asset_type`, `asset_subtype`, "Mark as verified" checkbox, inherited behaviour matrix chips, legacy field footprint. |
| Lifecycle & Title | `lifecycle_status`, `title_status`, `warranty_expiration`. |
| Registration | `registration_number`, `registration_state`, `registration_expiration`. |
| Insurance | `insurance_carrier`, `insurance_policy_number`, `insurance_expiration`. |
| Organization | `division`, `region`, `normalized_company` (from canonical company set), `supervisor_id`. |
| Identifiers & Devices | `vin`, `license_plate`, `gps_device_id`, `motive_vehicle_id`, `maintainx_asset_id`, `fleetwatcher_asset_id`. |

Edit toggle keeps the surface read-only until the operator presses **Edit**; Save PATCHes the spine and refreshes the projection. Cancel discards. RBAC: the entire `/admin/*` route family is admin-gated (existing `A()` guard), so unauthorized roles cannot reach this tab.

### `data-testid` coverage

Every interactive node carries a stable testid:
* Page roots: `asset-admin-page`, `ap-admin`, `ap-tab-admin`.
* KPIs: `aa-stat-total`, `aa-stat-review`, `aa-stat-classes`, `aa-stat-types`.
* Queue: `aa-queue`, `aa-queue-empty`, `aa-row-{id}`, `aa-row-class-{id}`, `aa-row-type-{id}`, `aa-row-verify-{id}`, `aa-row-open-{id}`.
* Crosswalk: `aa-crosswalk`, `aa-crosswalk-dryrun`, `aa-crosswalk-apply`, `aa-crosswalk-preview`, `aa-crosswalk-confirm`, `aa-crosswalk-cancel`, `aa-crosswalk-confirm-apply`.
* Edit form: `ap-admin-edit`, `ap-admin-save`, `ap-admin-cancel`, `ap-admin-verified-checkbox`, plus one testid per field (`ap-admin-asset-class`, `ap-admin-lifecycle`, `ap-admin-reg-number`, …).

---

## 3 · Backend Δ (additive, minimal)

`services/asset_spine.py::update_asset()`:
* `legal_keys` set extended with `taxonomy_verified_at` and `taxonomy_review_reason`.
* When `patch["taxonomy_verified"] is True` and the caller didn't supply `taxonomy_verified_at`, the service stamps the current ISO timestamp.
* Same path clears `taxonomy_review_reason` when manual verification lands.

No route signatures changed. No new collection. No mock data.

---

## 4 · Hard-Lock Verification

| Lock | Verified by |
|---|---|
| One asset · one record · one source of truth (`equipment_master`) | `test_equipment_master_remains_canonical` + read-back projection test |
| MAP STAYS | No code touched MapLibre / fleet_status / dispatch_assignments |
| Repair Complete ≠ RTS · PM Completion ≠ RTS | Tracks 13.28 + 13.31 untouched |
| No new collection introduced | Pytest unchanged from D0D1; D2 added no new persistence module |
| `asset_spine.py` still anchors to `equipment_master` | Pytest greps the service docstring contract |
| No costs · POs · accounting · ERP · pay-app fields | `test_no_cost_or_accounting_fields_exposed` still green |
| `/shop/hub_legacy` rollback alive | Untouched |
| Tracks 13.30/13.30C/13.30D/13.31/13.31B-D0D1 regression | 53/53 prior pytests still pass |
| Operator UI · no engineering copy | Hero subline reads "Canonical Taxonomy · Spine v1.0.0" — operator language; no Track 13 prefix, no `/api/` text |
| RBAC | Entire `/admin/*` namespace gated by `A()`; PATCH endpoint gated by `require_admin_dep` |

---

## 5 · Tests Run

```
tests/test_track_13_31b_d2_asset_admin_ui.py    7/7  pass   (new)
tests/test_track_13_31b_d0d1_taxonomy_spine.py 14/14 pass
tests/test_track_13_30_service_truck_reconciliation.py 12/12 pass
tests/test_track_13_30c_shop_intel.py           7/7  pass
tests/test_track_13_30d_parts_workload.py       5/5  pass
tests/test_track_13_31_pm_engine.py            15/15 pass
                                                ─────────────
TOTAL                                          60/60 pass
```

D2 test coverage:
1. PATCH applies canonical taxonomy + auto-stamps `taxonomy_verified=true · source=manual`.
2. PATCH accepts all 13 administrative fields and round-trips them through `project_asset`.
3. GET `/assets/{id}` projection surfaces every D0+D1+D2 field the UI hydrates.
4. Review queue requires admin auth (401 without token).
5. Review queue rows carry both the legacy footprint and a `suggested` mapping.
6. `apply-legacy-crosswalk` is dry-run by default — operator must explicitly POST `dry_run=false` to persist.
7. `/taxonomy` enums + behaviour matrix shape is stable for UI selectors.

---

## 6 · Live Preview Smoke (with admin token)

```
GET /api/asset-spine/health             → 612 active · 13 classes · 92 types
GET /api/asset-spine/taxonomy/review-needed → 200 rows need review
GET /api/asset-spine/assets/{id}         → full projection (taxonomy + admin)
PATCH /api/asset-spine/assets/{id}       → stamped class/type/verified=true
GET /api/asset-spine/taxonomy/review-needed → row removed from queue
```

Screenshots captured (in /tmp): `asset_admin.png`, `asset_admin_tab.png`, `asset_admin_edit.png`, `admin_home.png`. All five-pillar visual checks green:
* Powerful · 13 admin fields + canonical taxonomy editable inline · live review queue.
* Simple · one source of truth · one queue · one Save.
* Beautiful · MASCI native cards + chips + monospace labels · zero white-page drift.
* Trusted · pytest-asserted contract · no fabrication · operator-controlled verification.
* Proven · 60/60 pytests green + live PATCH round-trip verified on TB-01.

---

## 7 · Five-Pillar Score (this slice)

| Pillar | Score | Notes |
|---|---:|---|
| Powerful | 9.7 | Review queue + Admin tab + bulk crosswalk delivered; document vault still D3, CSV/PDF still D4. |
| Simple | 9.8 | One taxonomy. One queue. One Save. Bare-minimum surface area on the new page. |
| Beautiful | 9.6 | Native MASCI styling end-to-end · chips · monospace labels · red accent for destructive · no engineering copy. |
| Trusted | 9.8 | Auto-stamp + auto-clear review reason on verification · dry-run-by-default · existing RBAC unchanged. |
| Proven | 9.7 | 7 new + 53 regression. Live API round-trip on TB-01. |
| **Avg** | **9.72** | Clears the 9.5 bar. |

---

## 8 · Files Touched

| File | Change |
|---|---|
| `backend/services/asset_spine.py` | `update_asset` legal_keys extended; auto-stamp + clear-on-verify added |
| `backend/tests/test_track_13_31b_d2_asset_admin_ui.py` | **NEW** · 7 tests |
| `frontend/src/pages/admin/AdminAssetAdmin.jsx` | **NEW** · 514 lines · operator review queue + crosswalk |
| `frontend/src/pages/admin/AssetProfile.jsx` | Added Admin tab + `AdminSection` (canonical taxonomy + 13 admin fields · edit/save) |
| `frontend/src/components/AdminShell.jsx` | Added "Asset Administration" nav entry under Equipment |
| `frontend/src/App.js` | Lazy-imported + routed `/admin/asset-admin` |

No collection created. No route renamed. No legacy surface deprecated.

---

## 9 · Remaining Gaps (intentional · deferred)

| Item | Where |
|---|---|
| `operational_attachments.host_kind="asset"` adoption + asset doc types | Day-3 |
| `POST/GET /api/asset-spine/assets/{id}/documents` | Day-3 |
| `/api/asset-admin/renewals/upcoming(.csv)` | Day-4 |
| Asset Profile PDF renderer | Day-4 |
| Asset Admin role flag on `hr_users` + token issuance | Backlog (super-admin satisfies today) |
| Platform-wide consumer updates (pre-op dropdown · PM templates · fleet_status.unit_kind derivation · safety_equipment_issuances item_type · asset_transfers.equipment_type · equipment_inspections.equipment_type) | Day-5 |
| Final Five-Pillar audit + first-15-seconds + first-click | Day-5 |

---

## 10 · Final Verdict

**Track 13.31B-D2 — CLOSED.** Asset Admin surface locked. Five-Pillar 9.72 / 10.
Next fork picks up at Day-3 (Document Vault) against this verified contract.

**Read · Verified · Stopping.**

---

**Track 13.31B-D2 — CLOSED.**
