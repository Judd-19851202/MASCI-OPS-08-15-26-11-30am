# MAINTAINX · CANONICAL DEFECT PAYLOAD  (Phase 3)

**Date:** 2026-06-04 19:10 UTC
**Directive:** OMEGA — MaintainX Equipment Defect Pipeline Audit & Integration Plan
**Mode:** READ-ONLY PLANNING (no writes)

This document defines the single internal payload that every defect-originating workflow MUST emit before any MaintainX Work Order push is considered. The payload is shaped to be MaintainX-agnostic — Phase 4 explains how it maps onto MaintainX-specific WO fields.

The canonical payload will live in a future module:

```
backend/services/maintainx_defect_payload.py
```

(NOT BUILT IN THIS SPRINT.)

---

## 1 · Schema

```python
class CanonicalDefectPayload(TypedDict, total=False):
    # ── Source provenance ─────────────────────────────────────────
    source_type:              Literal[
        "fleet_dvir",
        "equipment_preop",
        "equipment_inspection",
        "shop_issue",
        "dispatch_issue",
        "manual_request",
    ]
    source_record_id:         str           # primary key of the originating row
    source_kind:              str           # subtype, e.g. "pre_op" / "weekly_lead" / "weekly_emergency" / "dvir" / "manual_oos"

    # ── Asset identity (canonical) ────────────────────────────────
    equipment_id:             str           # equipment_master.id (UUID)
    unit_number:              str           # e.g. "TRK-12" / "EX-1"
    equipment_name:           str           # display_label / make_model
    equipment_type:           str           # "Tractor Trailer Truck" / "Excavator" / etc.
    make:                     str
    model:                    str
    year:                     str
    serial_number:            str
    vin:                      str

    # ── Where + who ───────────────────────────────────────────────
    project_name:             Optional[str]
    project_number:           Optional[str]
    location:                 Optional[str]
    reported_by_employee_id:  Optional[str]
    reported_by_name:         str
    reported_by_role:         Literal["driver","operator","shop","dispatch","admin","field_leadership"]
    reported_at:              str           # ISO 8601 UTC

    # ── The defect itself ─────────────────────────────────────────
    defect_title:             str           # short title (≤120 chars)
    defect_description:       str           # full text (≤4000 chars); may include bulleted list
    failed_items:             list[FailedItem]   # one per checklist line that failed

    # ── Risk + routing ────────────────────────────────────────────
    severity:                 Literal["oos","monitor","attn","low","medium","high","critical"]
    safety_critical:          bool          # derived: True when severity in {oos, critical}
    out_of_service_recommended: bool        # mirror of out_of_service=Yes on header

    # ── Media ─────────────────────────────────────────────────────
    photos:                   list[MediaRef]     # R2 keys + optional pre-signed URLs
    attachments:              list[MediaRef]     # any non-photo attachments (PDF / sketch / weight ticket)

    # ── MaintainX correlation (read-only until push exists) ──────
    maintainx_asset_id:       Optional[str]  # from asset_mappings.maintainx.asset_id
    maintainx_work_order_id:  Optional[str]  # populated after a successful push only
    maintainx_url:            Optional[str]  # convenience deep-link

    # ── Lifecycle on our side (NOT mutated by canonical builder) ─
    sync_status:              Literal[
        "pending",       # canonical built, push not attempted yet
        "queued",        # in maintainx_sync_pending for retry
        "pushed",        # WO id captured
        "skipped",       # duplicate or rule said no-WO
        "failed",        # last push attempt failed
        "manual",        # admin marked manually-handled
    ]
    sync_error:               Optional[StructuredError]
    correlation_id:           str           # UUID v4 — used as MaintainX `externalId` + ForgedOps audit key
```

### Sub-types

```python
class FailedItem(TypedDict):
    section:   str         # e.g. "Brakes"
    item:      str         # e.g. "Brake pads"
    status:    Literal["fail"]
    severity:  Literal["oos","monitor","attn"]
    note:      Optional[str]

class MediaRef(TypedDict):
    storage:    Literal["r2","local","external"]
    key:        str        # R2 key or URL
    mime_type:  Optional[str]
    bytes:      Optional[int]
    captured_at: Optional[str]

class StructuredError(TypedDict, total=False):
    code:     str           # "unauthorized" / "rate_limited" / "timeout" / "unmapped_asset" / …
    status:   int           # HTTP status (0 for transport / config errors)
    message:  str
    retry_after: Optional[float]
    occurred_at: str
```

---

## 2 · Required-vs-Optional matrix

| Field | Required? | Default if absent |
| --- | --- | --- |
| `source_type` | YES | — must be provided by the originating writer |
| `source_record_id` | YES | — |
| `equipment_id` | YES (canonical) | resolved from `unit_number` via `equipment_master` lookup; pipeline rejects payload if unresolved |
| `unit_number` | YES | — |
| `equipment_name` | optional | `make + " " + model` fallback |
| `equipment_type` | YES | required for MaintainX taxonomy alignment |
| `make` / `model` / `year` / `serial_number` / `vin` | optional | `""` |
| `project_name` / `project_number` / `location` | optional | `""` |
| `reported_by_*` | YES | — drives audit + WO assignment hint |
| `reported_at` | YES | use server-side `datetime.now(timezone.utc).isoformat()` if caller omits |
| `defect_title` | YES | — |
| `defect_description` | YES | — |
| `failed_items` | YES (≥1) | — empty array means caller should not have produced a payload |
| `severity` | YES | derived from `failed_items[*].severity` (worst wins) |
| `safety_critical` | derived | `True` if `severity ∈ {oos,critical}` |
| `out_of_service_recommended` | YES | derived; defaults to `safety_critical` |
| `photos` / `attachments` | optional | `[]` |
| `maintainx_asset_id` | YES at push time | If unresolved → reject push, enqueue as `unmapped_asset` |
| `correlation_id` | YES | server-generated UUID v4 |
| `sync_status` | initial value `pending` | — |
| `sync_error` | optional | only populated on failure |

---

## 3 · Provenance of every field — source-by-source map

| Canonical field | Fleet DVIR (`fleet_defects` row) | Heavy Equipment Pre-Op (`equipment_inspections` row) | Manual OOS / Shop / Dispatch | `asset_holds` row |
| --- | --- | --- | --- | --- |
| `source_type` | `"fleet_dvir"` | `"equipment_preop"` | `"shop_issue"` / `"dispatch_issue"` | `"manual_request"` |
| `source_record_id` | `defect.id` (per-line); rolled up to `inspection_id` for consolidation | `inspection.id` | `defect.id` | `hold.id` |
| `equipment_id` | resolve `truck_unit_number` (or trailer) → `equipment_master.id` | resolve `equipment_unit` → `equipment_master.id` | already in row | `hold.asset_id` |
| `unit_number` | `defect.truck_unit_number` ?? `defect.trailer_unit_number` | `insp.equipment_unit` | `unit_number` (route param) | derived from `equipment_master` |
| `equipment_name` | `equipment_master.display_label` | `insp.equipment_make + " " + insp.equipment_model` | derived | derived |
| `equipment_type` | from `equipment_master.preop_equipment_type` or `category` | `insp.equipment_type` | derived | derived |
| `make / model / year / serial_number / vin` | from `equipment_master` | from `insp.*` (operator-entered) | from `equipment_master` | from `equipment_master` |
| `project_name / project_number / location` | absent on the DVIR (use truck's last project) | `insp.project_name / project_number / location` | optional, defaults to "—" | absent unless caller supplies |
| `reported_by_employee_id` | `defect.reported_by_employee_id` | `insp.operator_employee_id` (if present) | `payload.actor_employee_id` | admin actor |
| `reported_by_name` | `defect.reported_by_name` | `insp.operator_name` | `payload.actor_name` | admin actor |
| `reported_by_role` | `"driver"` | `"operator"` | `"shop"` / `"dispatch"` | `"admin"` |
| `reported_at` | `defect.reported_at` | `insp.inspection_date + inspection_time` (UTC normalized) | `now` | `hold.created_at` |
| `defect_title` | `"{kind} defect — {item_text}"` | `"Failed pre-op — {equipment_unit} ({fail_count} items)"` | `"Manual OOS — {unit_number}"` | `hold.reason` |
| `defect_description` | `item_text + "\n\n" + note` | bulleted list of all failed items + `deficiency_notes` | `payload.notes` | `hold.notes` |
| `failed_items` | `[{section: defect.category, item: defect.item_text, status:"fail", severity:defect.severity}]` | derive from `insp.checklist` walk (per `_iter_failures`) | one synthetic entry | `[]` (whole hold is the item) |
| `severity` | `defect.severity` (`oos`/`monitor`) | worst of `failed_items[*].severity` | `"oos"` (manual OOS by intent) | `hold.severity` |
| `safety_critical` | `severity == "oos"` | `severity == "oos"` | `True` | `severity in {"high","critical"}` |
| `out_of_service_recommended` | `insp.out_of_service == "Yes"` OR severity oos | `insp.out_of_service == "Yes"` | `True` | mirrors `severity` |
| `photos` | `defect.photos[]` | `insp.photos[]` | `payload.photos[]` | `hold.photos[]` (if present) |
| `attachments` | none today | none today | none today | none today |
| `maintainx_asset_id` | lookup `asset_mappings` by `equipment_id` | same | same | same |
| `correlation_id` | NEW uuid v4 | NEW uuid v4 | NEW uuid v4 | NEW uuid v4 |
| `sync_status` | initial `"pending"` (or `"skipped"` if dedupe matches an open WO) | same | same | same |

---

## 4 · Persistence

The canonical payload itself is **not a new MongoDB document type**. It lives in two places:

1. **In-flight**: built on demand by a future `services/maintainx_defect_payload.build_from_*` family of pure functions, fed into the WO push path. No DB row is created for the canonical envelope by itself.
2. **At-rest correlation**: when (and only when) a push is later authorized and a WO is created, the originating row (`fleet_defects` OR `equipment_inspections` OR `asset_holds`) has `external_refs.maintainx_work_order_id`, `external_refs.maintainx_url`, and `external_refs.correlation_id` written **in place**. No new collection is required for the success path.
3. **Pending / failure queue**: a new dedicated collection `db.maintainx_sync_pending` will store failed/queued canonical payloads with retry metadata (see Phase 6 / 7). Out of scope for this read-only sprint.

---

## 5 · Why we need this canonical layer (and not direct field passes)

- **De-duplication** — every source can be uniquely identified by `(source_type, source_record_id, equipment_id)`; building this consistently is the only safe way to enforce the duplicate-WO checks in Phase 8.
- **Provider portability** — the canonical envelope is MaintainX-agnostic. A future Motive or in-house CMMS push uses the same payload, mapped differently.
- **Audit + replay** — the `correlation_id` doubles as the MaintainX `externalId`, so admins can reconcile WOs to ForgedOps source rows even if the rest of the data drifts.
- **Field shape** — DVIR / Pre-Op / Shop / Dispatch / Manual rows all have slightly different field names today. Without the canonical layer, every consumer would have to handle six near-identical shapes.

---

## 6 · Out of scope for this sprint

- The actual `services/maintainx_defect_payload.py` module is **not built**.
- No source row is modified.
- No new MongoDB collection is created.
- No WO is pushed.

This Phase 3 document is the design contract that the next sprint will implement against, with explicit operator authorisation.

— End of Phase 3 canonical payload —
