# TRACK 20.6 · Inspection Reuse Audit — Fire Protection

**Doctrine:** No new inspection engine. No new inspection workflow. No
duplicate DVIR / Pre-Op / Equipment Inspection system for fire paper.

## Existing inspection surfaces (frozen inventory)

| Surface | Owner | Purpose | Fire-protection role |
|---|---|---|---|
| `db.fire_extinguishers` + `.../inspect` | Safety | Monthly fire-ext inspection lifecycle (last / next / status / notes) | **Authoritative** for fire-ext monthly inspection today. |
| `equipment_inspections` (Pre-Op / DVIR / Equipment) | Fleet / Shop / Safety (structured) | Vehicle & equipment operator inspections. Includes a `fire_extinguishers` line item ("present, charged, accessible") | **Complementary.** Pre-Op line item is a *presence check*, not a service check. No overlap. |
| `safety_forms` — safety-meeting / toolbox / issuance forms | Safety | Safety documentation | **Not applicable.** |
| `equipment_master.onboarding` | Admin | Asset onboarding checklist | **Complementary.** For a new mounted extinguisher, its onboarding step could include "assign to parent vehicle" once Phase B lands. |
| `asset_service_events` | Track 13.26 backbone | Timeline of all asset events (inspections, defects, transfers, etc.) | **Future authority** (Phase B) for extinguisher inspection events. |

## Zero-Drift determination

- **Reuse:** The Safety Portal's `POST /api/safety/fire-extinguishers/{fe_id}/inspect`
  workflow is well-suited to monthly inspections. **Do NOT** reroute
  through `equipment_inspections` — that would be duplication in the
  wrong direction (Equipment Inspections is scoped to operator/DVIR
  checklists, not third-party monthly checks).
- **Adapt (Phase A):** The Asset Thread's `attentionAdapter` reads
  `next_due_date` from `db.fire_extinguishers` when the extinguisher
  is the thread subject. Same rule when it's a truck's mounted
  extinguisher — surface a HIGH attention item on the parent truck's
  thread.
- **Extend (Phase B):** Project the existing inspection log onto
  `asset_service_events` (kind=`inspection`, subtype=`fire_ext`) so the
  Track 13.26 backbone becomes the single history view. The Safety
  Portal continues to be the write side; the backbone projection is
  read-only.
- **Retire (Phase B, later still):** Once the backbone projection is
  proven, the Safety Portal's own history view becomes a thin adapter
  over the backbone.
- **Nothing to REMOVE** today.

## Where Phase A explicitly refuses to intervene

- Does NOT rewrite `SafetyFireExtinguishers.jsx`.
- Does NOT rewrite the inspection dialog `SafetyFireExtManageDialog.jsx`.
- Does NOT touch the fire-ext import path (`SafetyFireExtImport.jsx`).
- Does NOT touch the `fire_extinguishers.py` router.
- Does NOT bind the CA link type `fire_ext` differently.
- Does NOT change the `fire_ext.fail` operational signal.

## Where Phase A adds inspection surface (read-only)

- On the Asset Thread's Timeline section, when the subject is a fire
  extinguisher: fetch the most recent inspections from
  `db.fire_extinguishers` (via a read-side adapter) and map them to
  timeline events with `kind="inspection"`. Same visual rendering as
  every other timeline event. No new UI code.

## Inspection categories mapped

| Inspection kind | Owner | Cadence | Current source |
|---|---|---|---|
| Monthly visual inspection | Safety | Monthly | `POST /inspect` |
| Annual professional service | External vendor + Safety record-keeping | Yearly | Historical Records (`fire_ext_annual_service` in Phase A) |
| Hydrostatic test (pressurized cylinders) | External vendor + Safety record-keeping | 5-yr / 12-yr | Historical Records (`hydrostatic_test_certificate` in Phase A) |
| Post-use recharge | Vendor + Safety | Ad-hoc after discharge | Historical Records (`recharge_service_record` in Phase A) |
| Post-incident inspection | Safety | Ad-hoc after incident | Existing incident-engine link |
| Pre-Op presence check (on vehicle) | Fleet / Shop operator | Daily | `equipment_inspections` (existing `fire_extinguishers` line) |

Six distinct inspection cadences · three current owners · zero
duplicate engines.

## Verdict

The platform already has every inspection engine it needs for fire
protection. Phase A REUSES + ADAPTS (client-side). Phase B EXTENDS
(projects onto backbone). Nothing is retired or removed in either
phase.
