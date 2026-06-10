# MASTER ASSET GOVERNANCE ARCHITECTURE
**ForgedOps · Source-of-Truth Contract for Every Asset Class**
**Date:** 2026-02-10 · **Status:** Architecture-locked · audit-only deliverable · no code changes

> Pairs with `FORGEDOPS_MASTER_OPERATIONS_AUDIT_001.md` §14. This document is the standalone, operator-shareable asset spine that downstream integrations (Motive, MaintainX, FleetWatcher, Accounting) must comply with.

---

## §1 · DOCTRINE (one paragraph)

**Anything an operator can hold in their hand and decide to keep, sell, or retire is ForgedOps-canonical.** Anything a vendor measures, scans, or generates from telemetry is vendor-canonical with a ForgedOps mirror. ForgedOps writes the asset identity; vendors validate, observe, and enrich.

---

## §2 · SOURCE OF TRUTH (per class)

| Asset class | Examples | Canonical store | Mirrored to |
|---|---|---|---|
| **Trucks · semis · trailers** | T-42 truck, ST-7 semi, TR-12 trailer | ForgedOps `equipment_master` | Motive (GPS), MaintainX (WO), FleetWatcher (haul cycles) |
| **Heavy equipment** | excavators, dozers, loaders, mills, pavers | ForgedOps `equipment_master` | Motive (when ELD-equipped), MaintainX |
| **Attachments** | buckets, breakers, sweepers, brooms | ForgedOps `equipment_master` (parent_id → equipment) | MaintainX |
| **Shop assets** | toolboxes, jacks, stands | ForgedOps `equipment` (light schema) | none |
| **Portable assets** | cones, plates, fans, light towers | ForgedOps `equipment` (or domain-specific) | none |
| **Trench-safety assets** | TB-01..TB-07 boxes, plates, shields | ForgedOps `trench_safety_assets` (domain-canonical) | none |
| **GPS sensors / ELDs** | Motive devices, Geotab, Samsara | **Motive (vendor)** | ForgedOps `asset_mappings` |
| **MaintainX work orders** | repair WOs, PM WOs | **MaintainX (vendor)** | ForgedOps `fleet_defects`, `equipment_parts` |
| **FleetWatcher production tickets** | haul tickets, plant tickets | **FleetWatcher (vendor)** | ForgedOps `haul_cycles`, `daily_reports.production[]` |

---

## §3 · OWNERSHIP & PERMISSION MODEL

| Action | Admin | Fleet Mgr (planned) | Shop Mgr | Dispatcher | PM | Safety | HR | Driver |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Create asset | ✅ | ✅ | partial (shop assets only) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Edit identity (model, serial, type) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Edit operational fields (assigned-to, status hints) | ✅ | ✅ | ✅ | ✅ (truck OOS only) | partial | ❌ | ❌ | ❌ |
| Deactivate / retire | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Archive | ✅ only | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| View asset profile | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | partial | partial |
| Map asset to Motive | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Map asset to MaintainX | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**Enforcement:** existing per-portal auth dependencies (`require_admin`, `require_any_portal`, etc.) already implement most of this. The Fleet Manager role is **planned** — for today, that role is folded into Admin.

---

## §4 · AUDIT TRAIL MODEL

Every asset write produces:

1. **In-document audit fields**: `updated_at` (UTC ISO), `updated_by` (operator id/email/role).
2. **`admin_audit_log` row** when the change came through an admin endpoint (action, target collection, target id, before/after delta, operator, ip, timestamp).
3. **`audit_events` row** for cross-portal operational events (e.g. equipment moved to OOS, asset retired).
4. **`master_history` row** (in `AdminMasterHistory.jsx`) for asset-identity-level changes.
5. **Provenance fields** for backfilled rows: `metadata_backfilled_from`, `metadata_backfilled_at` (already in `PRODUCTION_ASSET_METADATA_POLICY.md`).

**Visibility:** Per-asset audit history must be surfaced inside `AssetProfile.jsx` (one tab). Today the data is queryable but not yet rendered per-asset — composition build.

---

## §5 · NEW ASSET ONBOARDING WORKFLOW

```
T-0  Purchase decision (Operator / Accounting)
T+0d Asset arrives in the yard
T+0d Admin creates equipment_master row via AdminEquipment.jsx
       └─ fields: unit_number, kind, year, make, model, serial,
                  vin (if applicable), capacity, parent_id (if attachment),
                  active=true, source=ADMIN_ENTERED,
                  metadata_state=VERIFIED_INVENTORY|NEEDS_VERIFICATION
T+0d Asset visible to Dispatch (filterable: active=true, kind in PICKABLE)
T+24h GPS install — Motive provisioning
       └─ Motive webhook fires → asset_mapping_proposals row created
T+24h Admin reviews proposal in AdminAssetMapping.jsx
       └─ Approve / Reassign / Reject
       └─ On Approve: asset_mappings row + audit event
T+now Asset visible to Shop (via fleet_status), PM (via per-project assignment),
       Drivers (via dispatch pickers), Safety (via violation scope)
```

**Pillar fit:** Simple — Admin does one create + one approve. Trusted — full audit trail.

---

## §6 · ASSET RETIREMENT WORKFLOW

```
Operator decides to retire (sold, totaled, end-of-life)
       │
       ▼
Admin opens AssetProfile.jsx → "Retire" action
       │
       ▼
equipment_master.active = false
equipment_master.retired_at = NOW()
equipment_master.retired_by = operator_id
audit_events row created (type=ASSET_RETIRED)
asset_transfers row created (type=RETIRE, from=last_location, to=null)
       │
       ▼
Downstream effects (immediate):
  • Dispatch pickers exclude (filter active=true)
  • PM rollups exclude (filter active=true)
  • Shop fleet_defects retain history but new defects can't be filed
  • Motive mapping preserved for historical lookup; not used for new events
  • MaintainX mapping closed when activated
```

---

## §7 · ASSET RECONCILIATION WORKFLOW

Already implemented in `routes/asset_mapping_recon.py`:

| Endpoint | Purpose |
|---|---|
| `POST /api/admin/asset-mapping/scan` | Run a full Motive ↔ ForgedOps scan |
| `GET  /api/admin/asset-mapping/queue` | Pending proposals |
| `POST /api/admin/asset-mapping/{id}/approve` | Approve a proposal |
| `POST /api/admin/asset-mapping/{id}/reject` | Reject a proposal |
| `POST /api/admin/asset-mapping/{id}/reassign` | Move proposal to different asset |
| `POST /api/admin/asset-mapping/bulk-approve` | Bulk approve a curated subset |
| `GET  /api/admin/asset-mapping/coverage` | % coverage of fleet ↔ Motive |
| `GET  /api/admin/asset-mapping/audit` | Audit trail of mapping decisions |
| `GET  /api/admin/asset-mapping/top-unmapped` | The largest unmapped assets first |
| `GET  /api/admin/asset-mapping/impact-preview/{id}` | What changes if we approve this |
| `GET  /api/admin/asset-mapping/operational-impact` | Cross-portal effect summary |
| `GET  /api/admin/asset-mapping/executive-summary` | Executive briefing |

**Recommendation:** schedule a nightly `/scan` job; emit a digest of the queue depth + top unmapped to the Admin notification stream. No new endpoints required.

---

## §8 · DETECTION WORKFLOWS (new, recommended)

| Detection | Source | Trigger | Surface |
|---|---|---|---|
| **Missing asset** (Motive has, ForgedOps doesn't) | `asset_mapping_proposals` (already exists) | Nightly digest | Admin notification |
| **Duplicate asset** (two equipment_master rows for same VIN / serial) | nightly job (new — read-only check) | Nightly digest | Admin notification + AdminMasterHistory |
| **Retired-but-active asset** (active=false but Motive events arriving < 72 h) | nightly job (new — read-only check) | Nightly digest | Admin notification |
| **Orphaned asset** (active=true but zero events in 30 days + zero yard records in 30 days) | nightly job (new — read-only check) | Nightly digest | Admin notification |
| **Unsynced asset** (active=true but no Motive mapping) | `asset_mapping_recon.coverage` | Daily digest | Operations Center tile |
| **Conflicting asset** (identity drift in `project_identity_conflicts`) | existing job | already surfaces | AdminProjectIdentityGovernance |

The three nightly jobs marked "new" are read-only and produce digest-only output. **They are not new asset stores; they are reports.** No collection schema change.

---

## §9 · ASSET HEALTH DASHBOARD (per-asset)

`AssetProfile.jsx` becomes the canonical single-asset view. Recommended composition:

```
┌───────────── ASSET: T-42 · 2022 Mack TerraPro · VIN 1M2…42 ─────────────┐
│ Status: ACTIVE · Assigned: 25-21 SJR2C · Driver today: Carlos R.        │
├─────────────────────────────────────────────────────────────────────────┤
│ HEALTH (last 30 days)                                                   │
│  Hours: 168 · Idle %: 9 · DTC events: 2 · DVIR fails: 0                  │
├─────────────────────────────────────────────────────────────────────────┤
│ TIES                                                                    │
│  Motive  : ✓ mapped (asset_id 113 · last seen 12 min ago)                │
│  MaintainX: — (no key) · FleetWatcher: — (not started)                   │
├─────────────────────────────────────────────────────────────────────────┤
│ AUDIT (latest 5)                                                        │
│  2026-02-09 · Admin · changed location: 25-21 ← 25-31                    │
│  2026-02-08 · Shop  · cleared defect F-119 (DPF light)                  │
│  …                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

All data already retrievable from existing endpoints. **Composition build, no new routes.**

---

## §10 · ASSET SYNCHRONIZATION DASHBOARD (fleet-wide)

A single tile on the Operations Center:

```
┌─ ASSET SPINE HEALTH ─────────────────────────────────────┐
│ Total ForgedOps assets   : 589                            │
│ Motive coverage          : 96.8% (570 / 589)              │
│ Unmapped to review       : 14                             │
│ Newly arrived (queue)    : 5                              │
│ Retired-but-active alarm : 0                              │
│ Duplicate-VIN warnings   : 0                              │
│ Conflict tickets         : 2  → AdminProjectIdentityGov    │
│ Last scan                : 2026-02-10 02:00 UTC           │
└──────────────────────────────────────────────────────────┘
```

Sourced from existing `coverage` + the three new nightly detection jobs (§8). One tile, composition only.

---

## §11 · PILLAR FIT

| Pillar | Evidence |
|---|---|
| **Powerful** | Single canonical spine ; reconciliation surface is already production-grade ; supports Motive ↔ MaintainX ↔ FleetWatcher ↔ Accounting expansion without doctrine change |
| **Simple** | One rule: ForgedOps owns identity, vendors validate. One AssetProfile per asset, one queue, one coverage tile. |
| **Beautiful** | Per-asset health card; per-fleet health tile; cross-link from every portal. No new admin sprawl. |
| **Trusted** | Per-document audit fields + `admin_audit_log` + `audit_events` + `master_history` + provenance tags. All actions producible from the asset's own page. |
| **Proven** | The reconciliation surface (§7) has been operated against the live Motive integration; it ships today; this document promotes it from "scaffolding" to "platform contract" |

---

## §12 · WHAT THIS CONTRACT FORBIDS

* Motive may **not** create or retire ForgedOps assets.
* MaintainX may **not** create or retire ForgedOps assets.
* FleetWatcher may **not** create or retire ForgedOps assets.
* The Dispatcher role may **not** create assets.
* The Shop role may create only shop-domain assets (toolboxes, jacks), not trucks/equipment.
* No collection is allowed to be a "secondary canonical" store for trucks, semis, trailers, heavy equipment, or attachments. `equipment_master` is the only one.

---

## §13 · STOP CONDITION

This document is the **architecture contract**. The next authorised step is operator-chosen — either the nightly reconciliation digest (read-only ops job), or wiring AssetProfile cross-links from every portal (UI composition). No production data is touched by this document.

*Audit complete. Pillars validated. Awaiting operator authorisation.*
