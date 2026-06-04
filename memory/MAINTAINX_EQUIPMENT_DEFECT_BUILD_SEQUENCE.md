# MAINTAINX · EQUIPMENT DEFECT BUILD SEQUENCE  (Phase 7)

**Date:** 2026-06-04 19:10 UTC
**Directive:** OMEGA — MaintainX Equipment Defect Pipeline Audit & Integration Plan
**Mode:** READ-ONLY PLANNING (no writes, no MaintainX traffic)

This is the safe staged build sequence. Each stage is **gated by operator approval** and must NOT be skipped. Stages 6+ are explicitly off-limits without separate explicit authorisation per source type.

---

## Stage 1 — Read-only Asset Mapping  ✅ ALREADY BUILT

**Status:** DONE in P0-A/P0-B sprint.

- `MaintainxClient` (read-first httpx client)
- `services/maintainx_asset_sync.run_asset_dryrun(...)` (read pipeline)
- 4 admin-strict P0 routes
- Admin Integration Center "MaintainX · Read-First" tab
- 13/13 unit tests passing

**Output collection:** `db.maintainx_dryrun_reports` (audit only, opt-in)

---

## Stage 2 — Defect Source Inventory + Canonical Payload  📋 DESIGN COMPLETE · CODE NOT BUILT

**What:** Implement `services/maintainx_defect_payload.py` providing pure builder functions:
- `build_from_fleet_defect(defect, equipment_master_row) → CanonicalDefectPayload`
- `build_from_equipment_inspection(insp, failed_items, equipment_master_row) → …`
- `build_from_asset_hold(hold, equipment_master_row) → …`
- `build_from_manual_oos(defect_row, equipment_master_row) → …`

**Writes:** Pure functions; no DB writes; no MaintainX calls.

**Tests required:** Round-trip tests for each source — assert canonical shape; assert `correlation_id` is uuid4; assert severity derivation matches the existing `_iter_failures` / SEVERITY_TABLE_VERSION truth.

**Operator approval needed before starting:** YES (small, but explicit Go).

---

## Stage 3 — Dry-Run WO Generation (Display-only)

**What:** Implement `services/maintainx_wo_dryrun.py` providing:
- `dryrun_wo_payload(canonical_defect) → dict` — produces the exact MaintainX POST body that *would* be sent, plus the `customFields` block, plus pre-signed attachment URLs.
- Admin endpoint: `POST /api/admin/maintainx/p0/wo-dryrun?source=fleet_dvir&id={defect_id}`
- Admin UI: new "WO Preview" drawer in the Read-First tab.

**Writes:** None to MaintainX, none to operational rows. The dry-run output is rendered to the admin and may optionally be saved to `db.maintainx_wo_dryruns` (NEW · audit-only).

**Operator approval needed before starting:** YES.

---

## Stage 4 — Operator Review of Generated WO Payloads

**What:** Operator opens the Admin UI, picks one DVIR defect and one Pre-Op defect, hits "Generate WO Preview", inspects the JSON in the drawer, exports as a markdown report.

**Outcome:** Operator certifies the payload shape, severity mapping, priority mapping, and attachment plan.

**Writes:** None.

**Operator approval needed before next stage:** YES.

---

## Stage 5 — Write-Disabled Admin Preview (Preview Tenant Only)

**What:**
- `MAINTAINX_WRITE_ENABLED` remains `false`.
- Add a SHADOW write path: `services/maintainx_wo_push.push_shadow(canonical_defect)` — builds the payload, queries MaintainX `GET /v1/work-orders?externalId=…` (read-only) to check duplicates, but does NOT POST.
- Records the *intended* outcome in `db.maintainx_wo_push_attempts` (NEW · audit-only).

**Writes:** Only to the new audit collection. No MaintainX writes. No operational-row writes.

**Operator approval needed before next stage:** YES.

---

## Stage 6 — Enable Controlled WO Create (Preview Only)

**What:**
- Flip `MAINTAINX_WRITE_ENABLED=true` in **preview only**.
- Implement `services/maintainx_client.create_work_order(payload)` (replaces the current `MaintainxWriteDisabled` raise).
- Implement `services/maintainx_wo_push.push(canonical_defect)` — performs the externalId pre-check, POSTs the WO, stamps the source row's `external_refs.*`.
- Restrict to ONE source type at a time (start with `fleet_dvir`).
- Hard caps:
  - `MAINTAINX_PUSH_DAILY_CAP=10` (env-var) — refuses to push beyond this.
  - `MAINTAINX_PUSH_PER_ASSET_CAP=2/day` — guards against runaway loops.
  - Every push is logged to `db.integration_sync_logs`.

**Writes:** Yes — MaintainX WOs (preview tenant only). Yes — `fleet_defects.external_refs.*` on the source row.

**Operator approval needed before next stage:** YES — must inspect the first 10 preview WOs in person.

---

## Stage 7 — Production Pilot for One Source Type (DVIR-OOS only)

**What:**
- After ≥ 1 week of clean preview operation, request operator authorisation to flip `MAINTAINX_WRITE_ENABLED=true` in production for **only** `severity=oos` fleet DVIR defects.
- Daily/per-asset caps retained.
- Auto-rollback on > 3 failed pushes in 1 hour (kill-switch flips back to `false`).
- Daily digest email to admin distribution list summarising pushes.

**Operator approval:** REQUIRED before flipping production env var.

---

## Stage 8 — Expand to All Approved Defect Sources (one at a time)

In order (each step requires operator sign-off):

1. DVIR Monitor (severity=monitor)
2. Heavy Equipment Pre-Op OOS
3. Heavy Equipment Pre-Op Monitor
4. Manual OOS (Shop)
5. Manual OOS (Dispatch)
6. Manual Maintenance Request (Admin)

Each step:
- Implements the per-source canonical builder
- Runs a stage-5 shadow week first
- Operator certifies via a per-source GO/NO-GO doc

---

## Stage 9 — MaintainX Completion → ForgedOps RTS Gate

**What:**
- Implement the Phase 5 RTS gate (server-side check before `/clear` and `/release`).
- Wire `services/maintainx_client.get_work_order(wo_id)` (read-only) to power the check.
- Implement webhook handler enrichment to mirror `wo.status` → `external_refs.maintainx_wo_status` on the source row.

**Writes:**
- READ ONLY against MaintainX.
- Mirrors WO status into ForgedOps source row (`external_refs.maintainx_wo_status`).
- Does NOT auto-close WOs in MaintainX.

**Operator approval needed:** YES — flips RTS behaviour for the entire fleet.

---

## Stage-by-stage write surface summary

| Stage | Writes to MaintainX | Writes to ForgedOps operational rows | Writes to NEW audit collection |
| --- | --- | --- | --- |
| 1 | NONE | NONE | `maintainx_dryrun_reports` (opt-in) |
| 2 | NONE | NONE | NONE |
| 3 | NONE | NONE | `maintainx_wo_dryruns` (opt-in) |
| 4 | NONE | NONE | NONE |
| 5 | NONE | NONE | `maintainx_wo_push_attempts` |
| 6 | YES (preview only) | `external_refs.*` only | `integration_sync_logs` |
| 7 | YES (production, DVIR-OOS only) | `external_refs.*` only | `integration_sync_logs` |
| 8 | YES (per-source phased) | `external_refs.*` only | `integration_sync_logs` |
| 9 | NONE (read + webhook ingestion) | `external_refs.maintainx_wo_status` only | `integration_sync_logs` |

---

## Operator approval gates summary

| Gate | Required for |
| --- | --- |
| GO-1 → GO-2 | Stage 2 (canonical builder code) |
| GO-3 | Stage 3 (dry-run WO preview module + UI) |
| GO-4 | Stage 4 (operator certifies output) |
| GO-5 | Stage 5 (shadow push in preview) |
| GO-6 | Stage 6 (real WO create in preview) |
| GO-7 | Stage 7 (production DVIR-OOS pilot) |
| GO-8a..f | Stage 8 (each source type individually) |
| GO-9 | Stage 9 (RTS gate enforcement) |

Each gate produces its own markdown report in `/app/memory/` (mirroring the pattern used for P0-A/P0-B and the Admin Integration Center). No stage is built without its prerequisite gate.

— End of Phase 7 Build Sequence —
