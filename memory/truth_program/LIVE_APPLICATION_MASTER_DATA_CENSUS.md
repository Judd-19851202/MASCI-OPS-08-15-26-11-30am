# MASCI OPS — LIVE APPLICATION MASTER-DATA CENSUS (CLASS B)

Collected: 2026-06 (live snapshot) · Method: legitimate Super Admin browser/API session
against the LIVE production application `https://mascidocs.com`.
Environment proof: `/api/platform/data-truth` → environment=`production`, database=`masci_safety`,
release_commit=`8aa764c69e73`. Direct production MongoDB was NOT used (correctly isolated).
Production business-data writes: **0** (only the normal `/api/auth/multi-login` session POST).

> Numbers below are CURRENT SNAPSHOTS ONLY. The permanent truth is the canonical
> master + governed filter (the "Dynamic contract" column). Tomorrow's totals may differ;
> the contract keeps every consumer correct automatically.

## Session / access proof
- LIVE production frontend reachable: YES (HTTP 200).
- Authenticated Super Admin session valid: YES (all portals minted, no MFA on this account).
- Production READ APIs reachable: YES. Real SPA session/header contract reproduced
  (`X-Admin-Token` + `X-Directory-Token`) — no fabricated headers, no raw token replay.
  (Confirms the TD-0015(A) lesson: equipment reads require admin **and** directory context.)

## LIVE CENSUS TABLE

| Domain | Live snapshot | Production API authority | Business definition | Lifecycle / scope | API total | Independent reconciliation | UI comparison |
|---|---|---|---|---|---|---|---|
| Employees (Master) | **297** | `db.employees` via `/api/admin/employees/status` + `/api/master-lookup/audit` | Every canonical HR employee record, synthetic rows excluded | not soft-deleted (`deleted_at∈{null,""}`), synthetic-excluded; ALL lifecycle statuses | 297 (`count_documents`) | PASS — status.count 297 == master-lookup employees_total 297 | Source-verified: HR dashboards consume these canonical endpoints |
| Employees (Active roster, derived) | **240** | `/api/employees`, `/api/hr/employee-roster` | Active-employable roster used by every picker | active lifecycle only (Active/Pending Hire/Seasonal/LOA; legacy `is_active!=false`) | 240 (`count_documents`, field `total`) | PASS — `/api/employees` count 240 == total 240; == status.active 240 | Source-verified consumer (all field pickers) |
| Equipment / Assets (Master) | **604** | `db.equipment_master` via `/api/equipment-master` + `/api/admin/equipment-master/status` | Canonical fleet/asset master | `ACTIVE_FILTER` (not soft-deleted) + synthetic-exclusion | 604 (`count_documents`) | PASS — list total 604 == status count 604 == master-lookup 604 == Σcategory 604 | Source-verified: `EquipmentMasterPanel` renders `/equipment-master.total` |
| Numbered equipment (subset) | **357** | subset of `equipment_master` with `unit_number` | Equipment carrying an assigned unit number | subset attribute of Equipment Master | 357 | PASS — derived from the 604 master | Governed subset, not a separate list |
| Equipment Parts master | **2** | `db.equipment_parts` via `/api/admin/equipment-parts/status` | Parts sheets keyed by unit_number (distinct collection) | own collection | 2 (`count_documents`) | PASS — status.count | Shop parts surface |
| Trucks (derived) | **96** | derived from Equipment Master truck categories | Trucks in the fleet master | Equipment Master categories ∈ {Dump/Service/Tractor Trailer/Pickup/Water/Misc/Flatbed/Supervisor} | 96 | PASS — Σ truck categories from status board | Governed derivative of Equipment Master |
| Trailers (derived) | **53** | Equipment Master category `Trailers` | Trailers in the fleet master | Equipment Master category filter | 53 | PASS — status board category | Governed derivative of Equipment Master |
| Transport-capable fleet (on-road subset) | **136** | `/api/admin/transportation/fleet/equipment` | MASCI-owned transport-capable subset (trucks+trailers) | Equipment Master ∩ `TRANSPORT_CAPABLE_CATEGORIES`, `is_active!=false` | 136 (`masci_fleet_total`) | PASS — stable at limit 500 and 2000 (not capped); == Σ transport categories | Dispatch/transport surfaces |
| Eligible Drivers (derived) | **40** | `/api/admin/transportation/eligible-hr-cdl-drivers` | CDL-holding, actively-employable, not-yet-linked employees | `db.employees` where `cdl_holder=true` AND lifecycle NOT in {off_roll,terminated,retired,pending} AND not soft-deleted, minus linked `transport_persons` | 40 | PASS — stable at limit 200 and 1000 (not capped) | Dispatch driver selectors |
| Suppliers / Vendors / Subcontractors | **167** | `db.suppliers` via `/api/suppliers` + `/api/admin/suppliers/status` | Single unified business-partner master | `ACTIVE_FILTER` + `is_active!=false` | 167 (`count_documents`) | PASS — public total 167 == admin status count 167 | Supplier picker surfaces |
| Transport Carriers (distinct) | **0** | `db.transport_carriers` via `/api/admin/transportation/carriers` | External haul carriers (transportation overlay) | tenant-scoped | 0 | PASS — empty collection in production | Transportation module (unpopulated in prod) |
| Projects / Jobs (Master) | **35 total / 34 active** | `db.jobs_master` via `/api/jobs-master`, `/api/public/jobs-lookup`, `/api/jobs` | Canonical job/project master | active = `active!=false` AND not soft-deleted | 34 active (`count_documents`), 35 all | PASS — public-lookup total 34 == `/api/jobs` 34; all 35 | Job pickers |
| Users (Directory) | **44** | `db.user_directory` via `/api/admin/directory/k4/stats` | Canonical auth identity directory | all identities (43 mirrored, 1 managed, 0 disabled) | 44 (`count_documents`) | PASS — stats.total 44 == list.total 44 | Admin directory surface |

### NOT human-visible (excluded from human census)
- **Fleet units** `/api/fleet/units` = 149 — `/api/fleet/_meta` declares "Phase A · backend foundation only ·
  no frontend, no dashboards, no public tile yet." Backend-only foundation; NOT a human-visible population.
- **Dispatch eligible-drivers** `/api/dispatch/transportation/eligible-drivers` = 0 — requires linked
  `transport_persons` records (empty in prod). Distinct concept from the HR-CDL eligible list (40).

## 766 / 951 RECONCILIATION — CORRECTED (finalization: GOVERNED_DISTINCT)
> CORRECTION: my first pass mis-mapped "Equipment Status Board" to
> `/api/admin/equipment-master/status` (a status panel OVER equipment_master = 604)
> and wrongly concluded SAME_LIVE_POPULATION. The HUMAN-VISIBLE "Equipment Status Board"
> card (`EquipmentStatusBoard.jsx`) actually reads `/api/equipment-status-board`. The live
> visual proof caught this.

- **Equipment Master** = `/api/equipment-master` → `db.equipment_master` (ACTIVE_FILTER + synthetic-excl)
  → production **604**. Canonical asset/fleet master (every owned asset, numbered or not).
- **Equipment Status Board** = `/api/equipment-status-board` → `db.equipment_units` ∪ units referenced by
  `db.equipment_inspections` (distinct `equipment_type||unit_label` keys) → production **509**
  (out_of_service 5, never_inspected 474, stale 508). The INSPECTION-tracked unit population.
- **Classification: `GOVERNED_DISTINCT_LIVE_POPULATIONS`.** Different collections, different business
  concept (asset master vs inspection-unit tracking). UI labels are distinct
  ("MASCI Equipment Master Fleet" vs "Equipment Status Board") → not misleading.
- Preview values `766` (equipment-master) and `951` (status-board) were the SAME two distinct concepts
  measured on preview synthetic data — **NON-AUTHORITATIVE**. Proven dynamic in preview (766→767→766).

## DYNAMIC CONTRACTS — permanent truth (not the snapshot)
Every human-visible population above is derived at runtime via `count_documents(<governed filter>)` over a
single canonical collection (or a governed derivative of one). Verified:
- **No hard-coded business totals** — repo scan for census values (604/297/167/44/40/136/34/35/240/357/766/951)
  in served `backend/` + `frontend/src/` found **zero** literals used as populations (only string/char limits
  and severity thresholds — non-business config).
- **No first-page-length-as-total** — list endpoints return `count` (page) AND `total` (`count_documents`).
- **No silent query caps** — canonical population guards `GD-0014`/`GD-0015` (`lib/truth_population_guard.py`)
  and truth-surface guard: **0 violations**. Picker endpoints (eligible-drivers, transport-fleet-equipment)
  reconciled stable across `limit=200/1000` and `500/2000` respectively (not truncated).
- **No shadow populations** — same-concept consumers read the canonical master or an explicitly governed
  derivative (e.g. trucks/trailers/transport-fleet all derive from `equipment_master`; drivers derive from
  `employees`).
- **Dynamic propagation PROVEN (preview, Class-A):** equipment total 766 → add synthetic → 767 → soft-delete
  → 766. The total tracks the canonical master live.

## SUMMARY
- Production populations reconciled: **12 / 12** human-visible domains (+2 correctly excluded as non-human-visible).
- Preview-derived business-count claims retired: 766, 951, and the preview reconstructions (454 employees /
  336 carriers / 267 eligible) — all reclassified Class-A behavior evidence (see EVIDENCE_AUTHORITY_MODEL.md).
- Live contradictions discovered: **0**.
- Production business-data writes: **0**. Save: **NO**. Deploy: **NO**.
- Source repairs required: **NO** (guards clean, no hard-coded totals, all populations dynamic).
- Candidate fingerprint (unchanged; no tracked source edited this run):
  `dcf-b9da31c9836191f9a40984f007f15ac1baa9ba4690fba77a8a8209426b97e3aa` (deterministic ×2).

## FINALIZATION (owner directive — close before re-Save)

### 1. Permanent dynamic-population guard — DONE (GD-0033)
Extended the ONE canonical guard `backend/lib/truth_population_guard.py` with
`CANONICAL_POPULATION_AUTHORITIES` (12 registered human-visible authorities) + `scan_authority_registry`,
wired into `gate_violations` (so the pre-Save release gate + `verify_release_identity.py` enforce it).
It fails the release if a registered authority: (a) stops reading its canonical `db.<collection>` handle
(shadow population), (b) stops deriving its total via `count_documents`/`$count` (count_documents authorities),
or (c) hard-codes a literal population total. Tests: `backend/tests/test_gd0033_dynamic_population_authority.py`
(registry coverage, source-drift, self-tests for hard-coded-total and shadow-collection, + env-gated PREVIEW
propagation add→N+1→soft-delete→N which PASSED live). GD-0014/GD-0015 (cap/first-page/filter-drift) and the
truth-surface guard remain the sibling enforcers — no competing framework added.

### 2. 149 vs 136 — GOVERNED_DISTINCT_POPULATIONS (zero unexplained delta)
- **Truck/Trailer Master = 149** = every `equipment_master` truck category (96) + Trailers (53).
- **Transport-Capable Fleet = 136** = `equipment_master` ∩ `TRANSPORT_CAPABLE_CATEGORIES`
  {Dump, Tractor Trailer, Service, Water, Misc, Flatbed Trucks, Trailers}.
- **Exact excluded delta = 13**: `Pickup Trucks` (11) + `Supervisor / Mgmt Trucks` (2) — light-duty /
  management vehicles that are NOT dispatchable haul assets, governed out of the transport fleet by design.
- Both derive from the same canonical Equipment Master (registered `transport_fleet` in GD-0033), so they
  can never silently diverge into shadow populations. Labels are distinct → no conflation.

### 3. Numbered 357 / Parts 2 — precise definitions
- **Equipment Master: 604** — `db.equipment_master` (ACTIVE_FILTER + synthetic-excl); canonical asset master.
- **Numbered / Parts-Eligible Equipment: 357** — equipment_master rows carrying an assigned `unit_number`
  (parts sheets are keyed by unit_number, so numbered == parts-eligible). Governed subset attribute of the master.
- **Equipment Parts Catalog Sheets: 2** — `db.equipment_parts` records (`/api/admin/equipment-parts/status`).
  This is a COUNT OF PARTS-CATALOG SHEETS uploaded (only 2 units have a parts sheet), NOT a population of
  parts-eligible equipment. RENAMED here so the two are never confused again.

### 4. Fingerprint reconciliation
- Prior repaired-candidate fingerprint `dcf-80253472a2127fb54560731abe2e5a38480ba006e422fafc745c1318de9cc146`
  was RESTORED exactly after moving my read-only census helper scripts out of the fingerprint-scoped
  `scripts/` root into `memory/truth_program/census_tools/` (memory is excluded). This proved the transient
  `dcf-b9da31c9...` reported mid-census was caused SOLELY by non-deployable investigation scripts, not app source.
- Then TWO REAL deployable source changes were made and tested:
  `backend/lib/truth_population_guard.py` (GD-0033 guard) and `frontend/src/lib/portalAuthScope.js` (TD-0015 fix).
- **New candidate deployable fingerprint = `dcf-31b64c8d2ffbca14b628d67cc0208e4cf16bc07c2d718ed4d8d59f10246059ee`**
  (deterministic ×2). It differs from `dcf-80253472...` BY DESIGN (two intended, tested source repairs).
  The word "unchanged" no longer applies — this is a genuinely new, tested candidate.

### 5. Live visual proof — executed (read-only production Super Admin browser)
- Logged into `https://mascidocs.com/admin/login` as Super Admin, navigated to `/admin/equipment`.
- **Equipment Status Board card rendered "509 units tracked"** (matches `/api/equipment-status-board` = 509). MATCH.
- **MASCI Equipment Master Fleet panel rendered "0 UNITS IN FLEET / Fleet is empty"** while the API returns 604.
  → **LIVE UI/API CONTRADICTION (deployed production defect).**

### 6. LIVE UI/API CONTRADICTION → ROOT CAUSE → REPAIR (in preview; production untouched)
- **Defect:** Equipment Master panel shows a FALSE "0 units / Fleet is empty" (API total 604).
- **Root cause:** `/equipment-master` (a `_require_any_portal_read` endpoint needing portal token + directory)
  was MISSING from every scope list in `frontend/src/lib/portalAuthScope.js`, so `api.get("/equipment-master")`
  attached NO auth tokens → 401 → the panel rendered the failure as a genuine empty fleet.
- **Repair (preview):** added `/equipment-master` to `SHARED_API_PREFIXES` so it inherits the active portal
  token + directory token (mirrors `/employees`, same gate). Verified deterministically:
  `inferPortalsForApiPath('/equipment-master','admin'|'pm'|'shop')` → `['admin']|['pm']|['shop']`; the public
  `/public/equipment-master-lookup` correctly stays `[]` (no regression). Regression test added to
  `frontend/src/lib/__tests__/portalAuthScoping.test.js`. Production was NOT modified. Browser confirmation of
  the FIX is deferred to post-reSave because the preview frontend correctly fail-closes on the (expected)
  provenance mismatch until the owner re-Saves — do NOT weaken that guard.

**Result:** Source repairs required = **YES** (1 frontend fix + 1 new guard). Live contradictions discovered = **1**
(deployed Equipment Master panel false-empty) — root-caused and repaired in preview. New fingerprint
`dcf-31b64c8d...`. Save NO · Deploy NO.

## HUMAN-LABEL CLOSURE (final pre-reSave)
- Equipment labels REPAIRED: `EquipmentStatusBoard.jsx` now reads "N inspection units tracked" + scope-note
  "Inspection / status units — distinct from the Equipment Master (all assets)"; `EquipmentMasterPanel.jsx`
  total label now "assets · Equipment Master (all assets)"; `AdminEquipment.jsx` intro states the two are
  distinct governed populations (604 all-assets vs 509 inspection units). UI contract test added:
  `components/__tests__/equipmentPopulationLabels.contract.test.js` (static; CONTRACT PASS). No calculation
  semantics changed.
- Transport labels VERIFIED PASS (no change): the 136 tile is already labeled "MASCI fleet (transport-capable)"
  in `pages/transportation/_lists.jsx`; the 149 truck+trailer master is not shown adjacently → no conflation.
- Vendor subtyping: NOT activated. Current governed business model recorded as UNIFIED 167-record supplier/
  vendor/subcontractor master; subtype activation is a future product decision, not Truth & Trust closure.
- GD-0033 dynamic-population contracts preserved; live snapshots remain observations only (no hard-coding).
- Final candidate deployable fingerprint = `dcf-2ecd62ba6931cf66ab0f7dc17c4f62e819a157a0a9ca61509292eef346f9d4cb`
  (deterministic ×2; reflects the 3 label edits — not preserved artificially). Regression PASS, strict verifier
  ok=True (pop_gate + surface_gate PASS). Production writes 0 · Save NO · Deploy NO.
