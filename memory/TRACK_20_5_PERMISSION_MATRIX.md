# TRACK 20.5 · Permission Matrix — Asset / Equipment Thread

**Rule:** No role may gain any read/write it does not already have on the
underlying certified surfaces. The thread is a **view layer**, not a
permission expansion.

Role tokens used below (matching prior 20.x tracks):
**HR/Admin · Admin · Executive · Shop · Fleet · Dispatch · Trans ·
Transportation · Safety · PM · Field · Public.**

| Section / Data | HR/Admin | Admin | Executive | Shop | Fleet | Dispatch | Trans | Transportation | Safety | PM | Field | Public |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Asset identity (unit / VIN / serial / class · type) | R | R/W | R | R | R | R | R | R | R | R | R | — |
| Assignment (employee · project · crew) | R | R/W (via transfers) | R | R | R | R | R | R | R | R | R (own crew) | — |
| Location / GPS | — | R | R | R | R/W | R/W | R | R | R | R | R (own) | — |
| Defects / Work orders | — | R | R | R/W | R | R | — | — | R | R | R | — |
| Maintenance status · PM schedule | — | R | R | R/W | R | R | — | — | R | R | R | — |
| Inspections (Pre-Op · DVIR · Equipment) | — | R | R | R | R | R | R (own) | R | R/W | R | R/W (own) | — |
| Defect / OOS / Safety hold | — | R | R | R/W (repair) | R (view) | R/W (OOS) | R | R | R/W (safety) | R | R | — |
| Incident links | — | R | R | R | R | R | R | R | R/W | R | R | — |
| Documents (native, asset_documents) | R (HR paper) | R/W | R | R | R | R | R | R | R | R | R (own crew) | — |
| Documents (legacy paper, `entity_kind="asset"`) | R/W | R/W | R | R | R | R | R | R | R | R | R (own crew) | — |
| Photos | — | R/W | R | R/W | R/W | R | R | R | R/W | R/W | R/W (own crew) | — |
| Issued-to history (PPE · phone · iPad) | R | R | R | R | R | R | — | — | R/W | R | R (own crew) | — |
| Transfers | — | R/W (approve) | R | R (request) | R (request) | R (request) | R | R | R | R (request) | R (request own) | — |
| PO / Vendor link | — | R | R | R (view) | R | R | — | — | R | R (view) | — | — |
| Audit trail (Section 10) | R | R | R | R | R | R | R | R | R | R | R | — |

Legend: **R** = read · **R/W** = create/update in own lane · **—** = no
access.

## Non-expansion certification

- **PM lens** already reads asset data through PM Engine and PmDashboard.
  Thread does not open any new field to PM.
- **Safety lens** already reads inspections + issued equipment. Thread
  does not expose defect authoring to Safety (still Shop-authored).
- **Field / Superintendent lens** is scoped to own-crew asset assignment
  (already enforced by daily reports and PM engine). Thread inherits the
  same scoping.
- **Transportation lens** is currently DOT-focused. Thread limits its
  view to DOT-relevant fields for trucks/trailers (already the case).
- **Public** has zero access. No public asset URL. No public form.

## Hold matrix (three legitimate hold owners)

| Hold class | Owner | Cleared by |
|---|---|---|
| Out-of-Service (OOS) | Dispatch (fleet_ops) | Dispatch |
| Safety hold | Safety | Safety |
| Repair hold | Shop | Shop |

Three owners, three clearances — declared architecture, not a defect.

## Documents lens

- **HR / Admin** can upload legacy paper for assets via Historical
  Records once the `entity_kind="asset"` lane ships (19.61).
- **Admin (Asset Admin)** authors native documents in `asset_documents`.
- **Shop / Fleet / Safety / PM** read the fused view; they do not upload
  from the thread (they upload from their existing surfaces).

## Executive / Leadership lens

- Executive sees the fused thread read-only. No editorial rights.
- Executive PDF reuses `asset_documents.py`'s existing renderer — no new
  PDF pipeline.

## Verdict

**No permission widening required.** All access already exists on the
underlying surfaces. The thread renders them; it does not grant them.
