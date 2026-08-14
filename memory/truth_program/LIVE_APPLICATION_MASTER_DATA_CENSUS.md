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

## 766 / 951 RECONCILIATION (retired as preview fixtures)
- `766` = today's **preview** `equipment_master` synthetic-excluded total (proven live: preview
  `/api/equipment-master` returned 766; add→767, soft-delete→766 — dynamically derived, never hard-coded).
- `951` = the preview **status-board** figure (status board applies `ACTIVE_FILTER` only, WITHOUT synthetic
  exclusion → it counted ~185 extra preview synthetic/certification rows).
- **PRODUCTION reality:** Equipment Master list total = **604** AND Equipment Status Board count = **604** —
  identical. **Classification: `SAME_LIVE_POPULATION` (604).** The two endpoints read the same
  `db.equipment_master` with `ACTIVE_FILTER`; the only governed difference is synthetic-row exclusion, which
  has zero effect in production (no synthetic rows). Labels are NOT misleading: in production both surfaces
  describe the same population.
- `766` and `951` are **NON-AUTHORITATIVE preview test data** and must never be cited as MASCI counts.

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
