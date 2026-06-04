# MAINTAINX · EQUIPMENT HEALTH INTEGRATION MASTER PLAN

**Date:** 2026-06-04 19:10 UTC
**Directive:** OMEGA — MaintainX Equipment Defect Pipeline Audit & Integration Plan
**Mode:** READ-ONLY PLANNING (no writes, no MaintainX traffic, no deploys)

This is the single source of truth tying together Phases 1–8 produced this sprint. The mission was explicit: **verify MaintainX integration coverage for ALL equipment-defect sources, not DVIR only.**

---

## 1 · Required-question final answers

### Q1 · Is Fleet DVIR covered?
**NO — not at the MaintainX boundary.**
- Internal DVIR lifecycle (intake → defect → repair → RTS) is **fully live** inside ForgedOps (`fleet_ops.py`, `fleet_defects`, `fleet_unit_status`).
- The placeholder field `external_refs.maintainx_work_order_id` exists but is **never populated** by any code path.
- There is no WO push from DVIR.

### Q2 · Is Heavy Equipment Pre-Op covered?
**NO — not at the MaintainX boundary.**
- Pre-Op submission (`POST /api/equipment-inspections`) writes to `equipment_inspections` and fans out to `asset_holds` + `tasks` + `notifications` (internal).
- The MaintainX stub `create_work_order_from_failed_preop(...)` returns `{ok:false, status:"stub"}`.
- Heavy iron (Dozer, Excavator, Loader, Grader, Roller, Paver, Mill, Broom, Skid-steer) is structurally identical in shape (checklist + failed_count + photos) but is **not** wired to MaintainX.
- This is the most material gap surfaced by the audit — DVIR alone is the wrong scope.

### Q3 · Is Equipment Inspection (non-Pre-Op) covered?
**NO.** Shares the `equipment_inspections` collection but has no MaintainX wiring.

### Q4 · Is Shop issues covered?
**NO.** Shop-flagged OOS (via the Dispatch manual-OOS endpoint or admin hold creation) writes to `fleet_defects` / `asset_holds` only; no MaintainX call.

### Q5 · Is Dispatch breakdowns covered?
**NO.** Manual OOS flip by Dispatch creates an internal `fleet_defects` row; no MaintainX WO.

### Q6 · Is RTS covered?
**NO** at the MaintainX boundary. ForgedOps RTS (`/clear` for fleet, `/release` for holds) is fully implemented internally but does **not** check the linked MaintainX WO status before clearing. Today nothing is linked.

### Q7 · What must be built next?
1. **Phase 3 canonical defect payload module** (`services/maintainx_defect_payload.py`) — pure builder, zero-write, unit-testable in isolation.
2. **Phase 8 duplicate-protection module** — must be built BEFORE any push code, never after, to guarantee idempotency from line one.
3. **Phase 3 dry-run WO preview** (Stage 3 of the Build Sequence) — admin can inspect generated payloads with zero risk.
4. **Phase 5 RTS gate enforcement** wired behind a kill-switch but coded ahead of Stage 7 production pilot.
5. **Webhook handler upgrade** (Phase 5 §7) — mirror MaintainX WO status into `external_refs.maintainx_wo_status`; never auto-close.

### Q8 · What cannot be certified until MaintainX API key is available?
- End-to-end `MaintainxClient.test_connection()` against the real tenant.
- Real asset-pull results (currently 0 in the dry-run because the key is unset).
- The exact MaintainX field name set used by the tenant (`externalId` query support, attachment endpoint shape, webhook signature algorithm).
- Whether MaintainX rate-limit headers carry `X-RateLimit-Remaining` (needed for Phase 8 §3 caps).
- Tenant priority labels (Critical / High / Medium / Low → may differ).

### Q9 · What must never auto-write without operator approval?
- **MaintainX writes** — `POST /v1/work-orders`, `PATCH`, `DELETE`, attachment POSTs, comment POSTs.
- **`equipment_master` writes** — pipeline READS only.
- **`fleet_defects` / `equipment_inspections` / `asset_holds` core lifecycle changes** — the WO push module may ONLY stamp `external_refs.*` fields, never touch `status` / `severity` / repair fields.
- **`asset_mappings` writes** — admin only via existing Mappings Wizard.
- **DVIR / RTS / Shop / Dispatch operational lifecycle** — gate logic adds READ checks against MaintainX, never new write semantics.
- **Production deployments** — operator must redeploy explicitly per the standing OMEGA rule.
- **Toggling `MAINTAINX_WRITE_ENABLED` to `true`** — operator-only, per-environment, per-source-type.

---

## 2 · State today (single page recap)

| Layer | Status |
| --- | --- |
| MaintainX API client (read-first, masked, kill-switches) | ✅ LIVE (P0-A) |
| Asset pull + matching + duplicate-risk analyser | ✅ LIVE (P0-B) |
| Admin Integration Center "Read-First" UI | ✅ LIVE |
| Defect Source Inventory (Phase 1) | ✅ DOCUMENTED |
| Source → WO Matrix (Phase 2) | ✅ DOCUMENTED |
| Canonical Defect Payload (Phase 3) | 📋 DESIGN — not implemented |
| WO Mapping (Phase 4) | 📋 DESIGN — not implemented |
| RTS Gate (Phase 5) | 📋 DESIGN — not implemented |
| Gap Register (Phase 6) | ✅ DOCUMENTED |
| Build Sequence (Phase 7) | ✅ DOCUMENTED |
| WO Duplicate Protection (Phase 8) | 📋 DESIGN — not implemented |
| Real `MAINTAINX_API_KEY` provisioned | ❌ Not set |
| Real MaintainX traffic generated | ❌ Zero |
| WOs created in MaintainX | ❌ Zero |
| ForgedOps operational rows mutated | ❌ Zero |

---

## 3 · Deliverables produced this sprint

All in `/app/memory/`:

| File | Phase |
| --- | --- |
| `MAINTAINX_DEFECT_SOURCE_INVENTORY.md` | 1 |
| `MAINTAINX_SOURCE_TO_WO_MATRIX.md` | 2 |
| `MAINTAINX_CANONICAL_DEFECT_PAYLOAD.md` | 3 |
| `MAINTAINX_WORK_ORDER_MAPPING.md` | 4 |
| `MAINTAINX_RTS_GATE_PLAN.md` | 5 |
| `MAINTAINX_DEFECT_PIPELINE_GAP_REGISTER.md` | 6 |
| `MAINTAINX_EQUIPMENT_DEFECT_BUILD_SEQUENCE.md` | 7 |
| `MAINTAINX_WO_DUPLICATE_PROTECTION_PLAN.md` | 8 |
| `MAINTAINX_EQUIPMENT_HEALTH_INTEGRATION_MASTER_PLAN.md` | This document |

Together they form the complete blueprint that the next sprint will implement against — incrementally and operator-gated.

---

## 4 · Hard invariants for every future stage

These hold regardless of which stage is being built:

1. **Read-first stays read-first**: `MaintainxClient.{create,update,delete}_*` methods raise `MaintainxWriteDisabled` until Stage 6, and even then only when `MAINTAINX_WRITE_ENABLED=true`.
2. **The canonical defect payload is the only path** to a WO push — no inline payload construction inside route handlers.
3. **Idempotency key is `correlation_id`** for the lifetime of the defect group; never rotated.
4. **Severity authority** remains `lib/fleet_defect_severity.SEVERITY_TABLE_VERSION` for fleet and `MAJOR_OOS_SET` in `routes/equipment.py` for heavy equipment.
5. **RTS gate is a READ check** against MaintainX status; never an inverse write.
6. **Operational collections** (`fleet_defects` / `equipment_inspections` / `asset_holds`) get **only** `external_refs.*` writes from this integration; their lifecycle columns are untouched.
7. **Photos** push via R2 pre-signed URLs only (`safety_doc_storage.presign_get`); no bytes through the backend.
8. **Per-source enablement** — DVIR-OOS first, then expand one at a time with a fresh GO/NO-GO doc.
9. **Production deploys** require explicit operator redeploy step.

---

## 5 · Final classification

```
================================================================
  MAINTAINX EQUIPMENT HEALTH INTEGRATION
================================================================
  DVIR coverage at MaintainX boundary           : 0 %
  Heavy Equipment Pre-Op coverage at MX boundary: 0 %
  Equipment Inspection coverage                 : 0 %
  Shop / Dispatch / Manual coverage             : 0 %
  RTS coverage                                  : 0 %
  Read-first asset matching                     : 100 %  (P0-A/P0-B live)
  Documented integration plan                    : 100 % (this sprint)
================================================================
                          STATUS
        🟡 PLAN COMPLETE — IMPLEMENTATION NOT STARTED
                  (READ-FIRST LAYER LIVE)
================================================================
```

### What this status means
- The plan is complete and operator-reviewable.
- Nothing was built that risks any operational system.
- The next sprint can begin Stage 2 (canonical builder code) on operator authorisation.

### What this status does NOT authorise
- Any code change to defect-originating routes (`fleet_ops.py`, `equipment.py`, `operations.py`, `dispatch_*`).
- Any MaintainX write call.
- Any RTS gate enforcement code.
- Any production env-var change.
- Any deployment.

---

## 6 · One-line direct answers to the 9 required final-answer items

1. **DVIR covered?** No — internal lifecycle only; zero MaintainX wiring; placeholder field unused.
2. **Heavy Equipment Pre-Op covered?** No — full internal fan-out; MaintainX stub returns `{status:"stub"}`.
3. **Equipment Inspection covered?** No — same shared collection; no MaintainX wiring.
4. **Shop issues covered?** No — internal manual OOS only.
5. **Dispatch breakdowns covered?** No — internal manual OOS only.
6. **RTS covered?** No — internal `/clear` and `/release` work; no MaintainX status check.
7. **What must be built next?** Phase 3 canonical builder + Phase 8 duplicate protection → Phase 3 dry-run preview → Stage 5 shadow push → Stage 6 preview-only write enable → Stage 7 production DVIR-OOS pilot → Stage 8 phased per-source expansion → Stage 9 RTS gate.
8. **What cannot be certified until the API key is available?** Real `test_connection`, real asset-pull numbers, tenant-specific `externalId` query support, real webhook signature algorithm, real priority labels.
9. **What must never auto-write without operator approval?** MaintainX POST/PATCH/DELETE, `equipment_master` mutations, lifecycle-column edits on `fleet_defects`/`equipment_inspections`/`asset_holds`, `asset_mappings` writes outside the existing Wizard, flipping `MAINTAINX_WRITE_ENABLED=true`, and production deployments.

— End of MaintainX Equipment Health Integration Master Plan —
