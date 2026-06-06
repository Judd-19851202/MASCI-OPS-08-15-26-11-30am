# TRENCH SAFETY — PHASE 4 ARCHITECTURE LOCK CERTIFICATION

**Date:** 2026-06-06
**Mode:** Read-only certification review · NO CODE CHANGES
**Lock contract:** Public Safety Tile → Field Reference · Safety Portal → Administration · Operations Integration → Assignment / Location / Utilization

**Verdict:** 🟡 **CERTIFIED WITH 4 FIELD-REFERENCE GAPS — CORRECTION REQUIRED BEFORE PHASE 4**

> No administrative function is exposed publicly (the strict failure mode).
> Four allowed field-reference capabilities are MISSING or trapped behind Safety Portal auth. Architecture-locked surfaces are clean in shape but incomplete in coverage.

---

## 1. Current Public Safety Tile (no-auth surface)

### 1.1 Routes / endpoints actually live

| Surface | Path | Status |
|---|---|---|
| Tabulated Data primer + library | `/trench-boxes` (`TrenchBoxes.jsx`) + `GET /api/trench-boxes` + `GET /api/trench-box-files?scope=trench_box` | ✅ live · `adminMode={false}` enforced |
| Mobile QR landing | `/trench-safety/assets/:assetId` + `GET /api/trench-safety/public/assets/{asset_id}` | ✅ live · field-safe projection |
| Public damage-report intake | `POST /api/trench-safety/public/damage-report` | ✅ live · creates pending-shop-review repair, asset NOT auto-moved |

### 1.2 Allowed-list coverage matrix

Per the directive, the following are ALLOWED on the Public Safety Tile:

| Capability | Live publicly? | Notes |
|---|---|---|
| **Trench Safety Dashboard (field view)** | ❌ NO | Dashboard exists only at `/safety/trench-safety` behind Safety token. **GAP-1.** |
| **Trench Box Lookup** | ❌ NO | No public asset-id entry form. User must scan QR or already know `/trench-safety/assets/TB-07`. **GAP-2.** |
| **QR Asset Lookup** | ✅ YES | Per-asset landing live at `/trench-safety/assets/:assetId` |
| **Tabulated Data** | ✅ YES | Primer + library at `/trench-boxes` and re-host inside the Safety Portal at `/safety/trench-safety/tabulated-data` |
| **OSHA References** | ⚠ partial | Embedded inside the primer (`TabulatedDataPrimer.jsx`). No standalone OSHA reference surface. Acceptable for now — flagged. |
| **Manufacturer References** | ✅ YES | Manufacturer-shipped PDFs in the `trench_box` file scope, browsable publicly. |
| **Training** | ❌ NO | Not built — Phase 9 deliverable. **GAP-3** (architecture allows, but no surface exists.) |
| **Asset Information** | ✅ YES | Per-asset via QR landing |
| **Inspection Status Visibility** | ✅ YES | `last_inspection_at`, status pill, on-hold banner all visible in QR landing |
| **Certification Status Visibility** | ✅ YES | `certification_expires_at` field rendered in QR landing |
| **Report Damage** | ⚠ API ONLY | `POST /api/trench-safety/public/damage-report` works, but **no UI button** on the QR landing. **GAP-4.** |
| **Report Unsafe Condition** | ⚠ API ONLY | Same endpoint, same gap. |
| **Report Missing Pins** | ⚠ API ONLY | Same endpoint, same gap. |
| **Report Missing Labels** | ⚠ API ONLY | Same endpoint, same gap. |

### 1.3 NOT-ALLOWED list compliance

| Forbidden publicly | Currently allowed publicly? |
|---|---|
| Asset Creation | ❌ NO — `POST /api/trench-safety/assets` returns 401 anonymous |
| Asset Editing | ❌ NO — `PUT /api/trench-safety/assets/{id}` returns 401 |
| Asset Assignment | ❌ NO — `POST /assets/{id}/assign` returns 401 |
| Asset Retirement | ❌ NO — `POST /assets/{id}/retire` requires Admin token |
| Inspection Administration | ❌ NO — `POST /assets/{id}/inspections` returns 401 |
| Repair Administration | ❌ NO — `POST /assets/{id}/repairs` returns 401 |
| Certification Administration | ❌ NO — no public endpoint exists |
| OCR Administration | ❌ NO — not yet built; no public endpoint |
| QR Administration | ❌ NO — not yet built; no public endpoint |

✅ **PASS on every forbidden item.** Public surface is correctly walled off from administration.

---

## 2. Current Safety Portal (authenticated administration)

### 2.1 Routes / endpoints live

| Surface | Path | Auth | Status |
|---|---|---|---|
| Hub / Dashboard | `/safety/trench-safety` + `GET /api/trench-safety/dashboard` | Safety+ | ✅ Phase 3 |
| Asset list (filterable roster) | `/safety/trench-safety/assets` + `GET /api/trench-safety/assets` | Safety+ | ✅ Phase 3 |
| Asset detail (read-only) | `/safety/trench-safety/assets/:assetId` + `GET /api/trench-safety/assets/{ident}` | Safety+ | ✅ Phase 3 |
| Tabulated Data (admin re-host) | `/safety/trench-safety/tabulated-data` | Safety+ | ✅ Phase 3 |
| Asset Create | `POST /api/trench-safety/assets` | Safety + Admin | ✅ API live · ❌ UI deferred (Phase 8) |
| Asset Edit | `PUT /api/trench-safety/assets/{ident}` | Safety + Admin (`asset_id` immutable) | ✅ API live · ❌ UI deferred (Phase 8) |
| Asset Status Change | `POST /api/trench-safety/assets/{ident}/status` | Safety + Admin | ✅ API live · ❌ UI deferred (Phase 6/8) |
| Asset Retire | `POST /api/trench-safety/assets/{ident}/retire` | Admin only | ✅ API live · ❌ UI deferred (Phase 8) |
| Inspection submit | `POST /api/trench-safety/assets/{ident}/inspections` | Safety + Admin | ✅ API live · ❌ UI deferred (Phase 6) |
| Inspection list | `GET /api/trench-safety/assets/{ident}/inspections` | any portal | ✅ Phase 2 |
| Repair Open / Patch / Complete | various | Shop + Admin | ✅ API live · ❌ UI deferred (Phase 6) |
| Deployment / Assign / Return | `POST /assets/{id}/assign|return` | any portal | ✅ API live · ❌ UI deferred (Phase 4) |
| Audit Log | `GET /api/trench-safety/assets/{ident}/audit` | any portal | ✅ API live · ❌ Safety-Portal UI page deferred (Phase 8) |
| Photos upload | not yet exposed | — | ❌ deferred (Phase 7) |
| Certification management | not yet exposed | — | ❌ deferred (Phase 6/8) |
| OCR review | not yet exposed | — | ❌ deferred (Phase 10) |
| QR PNG label generator | not yet exposed | — | ❌ deferred (Phase 7) |
| Reporting | not yet exposed | — | ❌ deferred (Phase 9) |
| Deployment History | shown in detail page (3 latest) | Safety+ | ✅ Phase 3 |

### 2.2 Architecture alignment

The Safety Portal **owns** every administrative capability the directive lists. None of them is split off to another surface. Phase 3 shipped only the read-only slice on purpose; the remaining write UIs are scheduled in Phases 4 / 6 / 7 / 8 / 9 / 10. **No drift.** Every administrative endpoint lives under `/safety/trench-safety/*` (UI) and `/api/trench-safety/*` with Safety / Admin gating (server).

### 2.3 Tabulated Data — dual exposure analysis

The same Tabulated-Data content surfaces in two places:

| Surface | Route | Audience | Purpose |
|---|---|---|---|
| Public | `/trench-boxes` (`TrenchBoxes.jsx`) | Field crews scanning a poster | **Field reference** — read-only library + primer |
| Authenticated | `/safety/trench-safety/tabulated-data` | Safety personnel | **Same content, native chrome** for admin-side workflows |

Both call the **same** `TabulatedDataPrimer` + `TrenchBoxTabulatedLibrary` component with `adminMode={false}`. The admin uploader UI lives separately at `/admin/trench-boxes`. **No duplication of administrative function**, no field-reference trapped behind auth, no admin function exposed publicly.

✅ Architecture-compliant.

---

## 3. Current Operations Integration

### 3.1 Routes / endpoints live

| Capability | Path | Status |
|---|---|---|
| Equipment Master mirror | `db.equipment_master` (category="Trench Safety") | ✅ 7/7 mirrored, indexed |
| Asset Transfer state machine | `/api/asset-transfers/*` (existing, untouched) | ✅ ready to accept Trench Safety mirror rows |
| Supervisor job-equipment picker | (no Trench Safety wire-up yet) | ❌ deferred (Phase 4 build) |
| Project dashboard Trench Safety section | (no surface yet) | ❌ deferred (Phase 4 build) |
| Dispatch visibility / movement | (no Trench Safety overlay yet) | ❌ deferred (Phase 5 build) |
| Utilization tracking | data captured in `trench_safety_deployments` collection | ✅ stored · ❌ UI deferred (Phase 9) |
| Location tracking | `current_location` + `current_project_*` fields | ✅ stored · synced via assign/return |

### 3.2 Architecture alignment

The locked architecture assigns the Operations Integration surface three concerns: **assignment, location, utilization.** The Phase 2 backend already persists every field needed (`current_project_id`, `current_project_name`, `current_location`, `assigned_to_*`, `trench_safety_deployments`); the equipment_master mirror is in place. Phase 4 is the wire-up to existing PM/dispatch surfaces — **that is exactly the lock contract**.

✅ Architecture-compliant. No surface duplication; everything routes through the existing equipment_master + asset_transfers SOT.

---

## 4. Architecture violations found

### 4.1 Strict-failure violations (would have been NO-GO)

- ✅ **None.** No administrative function is exposed publicly. The hard rule is intact.

### 4.2 Field-reference gaps (4 capability GAPs — correction required before Phase 4)

| GAP | Description | Severity | Recommended fix |
|---|---|---|---|
| **GAP-1** | **No public field-view Dashboard** — the existing Dashboard at `/safety/trench-safety` requires a Safety token. Field crews have no anonymous "fleet at a glance" surface. | MEDIUM | Build a stripped public `/trench-safety` landing page that shows: fleet count, count on Inspection Hold (red banner), count Available, count Assigned, link to Lookup, link to Tabulated Data, link to Report Damage. No PII, no per-asset table. |
| **GAP-2** | **No public Trench Box Lookup** — without a QR poster, a foreman cannot anonymously type "TB-07" into a search box. | LOW | Add a public lookup card on the field-view dashboard: input box + "Look up" button → navigates to `/trench-safety/assets/<id>`. Already-deployed backend handles the GET. |
| **GAP-3** | **No standalone OSHA References / Training** — partially embedded in the primer, but the directive's allowed-list calls them out independently. | LOW | Phase 9 OSHA references + Phase 9 Training are the right home; verify the architecture explicitly assigns these to the Public Safety Tile when those phases build. |
| **GAP-4** | **No Report Damage UI** — backend endpoint live, but the QR landing has no "Report Damage / Unsafe / Missing Pins / Missing Labels" button. Anonymous reporters can only POST via raw API. | MEDIUM | Add a one-tap "Report a problem" button to the QR landing (and to the public dashboard) that opens a typed-form modal: kind = Damage / Unsafe / Missing Pins / Missing Labels, description, optional contact. Calls the existing `/api/trench-safety/public/damage-report` endpoint. |

### 4.3 Capability completeness (no architecture violation — just deferred build)

The following ALLOWED capabilities are not built yet, but their architectural home is correct:

| Capability | Belongs to | Phase that delivers |
|---|---|---|
| Inspection / Repair / Certification Admin UI | Safety Portal | 6 / 8 |
| Photos uploader | Safety Portal | 7 |
| QR PNG label printer | Safety Portal | 7 |
| OCR review | Safety Portal | 10 |
| Reports | Safety Portal | 9 |
| Project dashboard Trench Safety section | Operations Integration | 4 |
| Dispatch / Transport movement | Operations Integration | 5 |

---

## 5. Any administrative functions exposed publicly?

**NO.** All 9 administrative capabilities verified 401 anonymous (see §1.3). Public surface returns only the field-safe projection on the asset endpoint and the static tabulated-data library. No write surface, no admin metadata leak, no user PII.

## 6. Any field-reference functions trapped behind Safety Portal authentication?

**YES — 2 functional gaps:**

1. The **operational dashboard** (KPIs, condition mix, hold count, alerts) is only at `/safety/trench-safety`. Field crews need a stripped-down field-view dashboard publicly.
2. **Asset lookup form** (type ID, see asset) lives only inside Safety Portal.

(GAP-3 OSHA References and GAP-4 Report Damage UI are not "trapped" — they simply don't exist anywhere yet. Both belong in the Public Safety Tile when built.)

---

## 7. Correction plan before Phase 4 begins

To honor the directive ("If violations exist: Document and correct before continuing"), I propose a **Phase 3.5 — Public Safety Tile completion** mini-sprint (estimated ~250 LOC, all frontend, no backend changes — the endpoints already exist):

### Phase 3.5 scope

| Deliverable | LOC | Backend impact |
|---|---|---|
| `/trench-safety` — public field-view dashboard (fleet count, hold count, available count, today's alerts strip, "look up" search box, "tabulated data" tile, "report a problem" tile) | ~120 lines (1 component) | None — calls existing `/api/trench-safety/public/assets/*` and a new lightweight aggregate the backend can derive client-side from existing data |
| `/trench-safety/lookup` — public asset-id entry form → redirect to `/trench-safety/assets/:id` | ~40 lines | None |
| Public **Report Damage / Unsafe / Missing Pins / Missing Labels** modal — wired to the existing `POST /api/trench-safety/public/damage-report` (add `kind` field) | ~80 lines + ~5 backend lines (extend the schema with a `kind` enum) | Minimal — single schema field |
| Add tile entries on `/` home for the public Trench Safety surface | ~10 lines | None |
| Spanish parity for the new strings | ~30 i18n entries | None |

This is a small, contained backfill — NOT a Phase 4 build — that brings the Public Safety Tile to full architectural coverage before Operations Integration begins.

### Alternative: defer the Public Safety Tile gaps

If the operator prefers, the 4 gaps can be tracked as a documented Phase 9 backlog item (when Training & OSHA References are also built) and Phase 4 can begin immediately on the Operations Integration side. The hard NO-GO rule (no admin exposed publicly) is already satisfied.

---

## 8. Verdict

🟡 **CERTIFIED WITH FINDINGS — PROCEED ONLY WITH OPERATOR DIRECTION.**

| Lock rule | Status |
|---|---|
| Public Safety Tile owns field reference only | ✅ (no admin exposed) · ⚠ underbuilt (4 capability gaps) |
| Safety Portal owns administration | ✅ (everything administrative is under `/safety/trench-safety` + Safety/Admin tokens) |
| Operations Integration owns assignment / location / utilization | ✅ (mirror in place; Phase 4 is the next wire-up) |
| No drift | ✅ (no duplicated systems; equipment_master is the single SOT for cross-portal visibility) |
| No admin exposed publicly | ✅ (9/9 forbidden capabilities walled off) |

**Two acceptable paths forward — operator chooses:**

- **(A) Phase 3.5 first** — close GAP-1 / GAP-2 / GAP-4 with a tight ~250-LOC public-tile completion before starting Phase 4. Recommended.
- **(B) Begin Phase 4 now** — Operations Integration build; track Public Safety Tile gaps as a documented backlog item to be addressed in Phase 9.

🛑 **STOP per directive.** Awaiting operator direction.
