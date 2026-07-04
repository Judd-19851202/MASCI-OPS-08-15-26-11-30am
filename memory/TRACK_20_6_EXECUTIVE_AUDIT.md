# TRACK 20.6 · Fire Protection & Life Safety Asset — Executive Audit

**Track type:** Forensic audit · docs-only · zero code changes · zero live email.
**Question answered:** Should Fire Protection assets become another certified
Asset Class inside the Universal Asset architecture?

## Executive verdict

**PROMOTE + EXTEND (medium).** In two disciplined phases.

Fire Protection **is not yet on** the certified Universal Asset spine.
It runs on a **pre-Universal-Asset system**: `db.fire_extinguishers`
collection + `/api/safety/fire-extinguishers/*` routes + a Safety Portal
UI + a digest KPI. Extinguishers were half-bound to the asset spine in
iter138 via `equipment_master_id` — but the **canonical identity still
lives outside `equipment_master`**, and Fire Protection is **not**
present in `services/asset_taxonomy.py` v1.0.0.

This is a duplicate asset system by the letter of the Track 20.5 doctrine.

### Why not "already supported"

- The canonical asset taxonomy has 13 classes; **none of them is Fire
  Protection**. Fire extinguishers are also not under Safety Equipment
  (which currently lists Harness · Gas Monitor · Confined Space
  Equipment · Respirator · Fall Protection · Other).
- `db.fire_extinguishers` is a separate collection with its own
  identity, inspection log, and lifecycle — parallel to
  `equipment_master` + `equipment_inspections` + `asset_service_events`.
- The Asset Thread (Track 19.61) cannot render fire extinguishers today
  because the resolver reads `equipment_master` only.

### Why not "small extension"

- The taxonomy extension itself is small (1 asset_class + 5-7 asset_types).
- The Asset Thread adapter to READ `db.fire_extinguishers` is small.
- **But** a full migration (retire the duplicate collection, move
  fields into `equipment_master`, update the Safety Portal UI to write
  through the spine, keep the digest KPI + CA link type + operational
  signal working) is medium-sized and must be sequenced carefully.

### Why not "BUILD NEW"

Absolutely not. A new fire-protection system is unequivocally forbidden
by Zero-Drift. The whole point of this audit is to declare that the
existing system MUST be promoted, not replaced.

## Two-phase promotion (proposed, NOT executed here)

### Phase A — Track 19.62 · Read-side promotion (small)

- Extend `services/asset_taxonomy.py` v1.0.0 → v1.1.0 with a new closed-
  set `Fire Protection` asset_class and the extinguisher asset_types.
- Add a **read-side adapter** on the Asset Thread that looks up an
  extinguisher by `unit_id` from `db.fire_extinguishers` when the
  Universal Asset Identifier Resolver returns 404 on
  `equipment_master`. Same UI shell. Zero writes into the legacy
  collection from the thread.
- Extend Historical Records `entity_kind="asset"` catalog with fire-
  specific record_types: `hydrostatic_test_certificate`,
  `recharge_service_record`, `fire_ext_annual_service`,
  `fire_ext_manufacturer_doc`, `fire_ext_retirement_record`. Additive
  slugs; no behavior change.
- **No writes**, no migration, no changes to the Safety Portal UI or
  its endpoints. The Safety inspection workflow keeps running exactly
  as today.
- Estimated budget: ≤ 200 backend LOC · ≤ 200 frontend LOC · 1 lock file.

### Phase B — Later track · Write-side consolidation (medium)

- Data migration: for every row in `db.fire_extinguishers`, create or
  update a matching `equipment_master` row with
  `asset_class="Fire Protection"`, and store the extinguisher's
  inspection log on `asset_service_events` (same backbone as trucks/
  equipment).
- Update the Safety Portal write path to POST/PATCH through
  `/api/asset-spine/*` while keeping the existing
  `/api/safety/fire-extinguishers/*` responses as a **backwards-compat
  view** over the spine (dual-read for the transition window).
- Retire `db.fire_extinguishers` writes once the backwards-compat view
  is stable across at least one Safety digest cycle.
- Keep the digest KPI `fire_extinguishers_overdue`, the CA link type
  `fire_ext`, and the operational signal `fire_ext.fail` — all three
  are consumer-side and continue working without change.

## What must NOT ship in Track 19.62

- No new fire-protection collection.
- No new inspection module.
- No new PDF renderer.
- No email workflow of any kind.
- No new OI product (see OI Integration Audit).
- No new PPE or Safety Equipment sub-module.
- No changes to `SafetyFireExtinguishers.jsx` behavior or endpoints.
- No permission widening (Safety still owns inspection; Admin still
  owns the asset master).

## Six pillars alignment (with the proposed phase-A promotion)

| Pillar | Evidence |
|---|---|
| Powerful | Fire protection joins the same Universal Thread everyone already uses. |
| Simple | One asset philosophy — one class in the taxonomy, one thread route. |
| Beautiful | Reuses `OperationalThreadPage`, `RelationshipGraph`, `GuidanceCard`, `AttentionChip`. |
| Trusted | Every fact points to a certified surface — `db.fire_extinguishers` in phase A, `equipment_master` in phase B. |
| Proven | The Asset Thread (19.61) is live and lock-tested. |
| Operational | Shop / Fleet / Safety / PM / Superintendent / Executive all get one page for an extinguisher, just like any other asset. |

## Final call

**PROMOTE + EXTEND (medium). Two phases.**
Phase A (Track 19.62) is the smallest correct next step. Phase B
follows once Phase A is proven.
