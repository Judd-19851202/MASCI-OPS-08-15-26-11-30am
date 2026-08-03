# WP18C2 · Daily Report Work Block Contract

## Objective

WP-18C2 preserved the existing Daily Report architecture and operator journey, then **extended it additively** with governed work-block behavior.

## Operator Experience Evidence

Implemented UI surfaces:

- Daily Report V3 preview card with `data-testid="dr-v3-work-block-preview-card"`
- Daily Report detail section with `data-testid="dr-view-work-blocks"`

The preview card explains that the system will preserve field entries and build governed work blocks from:

- production rows
- cost-code quantities
- crews
- equipment
- materials
- constraints

## Persisted Contract

Daily Reports now support:

- `work_blocks[]`
- `work_block_summary`
- `work_blocks_version = wp18c2.v1`
- `work_blocks_governed_at`
- `work_blocks_backfill_mode` (used for safe historical compatibility stamping when no safe derived linkage exists)

## Normalized Work Block Shape

Implemented block fields include:

- `work_block_id`
- `title`
- `contract_id`
- `phase_id`
- `work_package_id`
- `pay_item_id`
- `customer_pay_item_number`
- `cost_code`
- `primary_work_type_id`
- `work_type_ids[]`
- `schedule_activity_id`, `schedule_activity_name`
- `installed_quantity`, `unit`
- `location`, `work_area`
- `field_notes`
- `labor_entries[]`
- `equipment_entries[]`
- `material_entries[]`
- `subcontractor_entries[]`
- `constraint_entries[]`
- `photo_refs[]`
- `attachment_refs[]`
- `qaqc_refs[]`
- `safety_refs[]`
- `schedule_actual_proposal_status = proposed_only`

## Backfill and Compatibility Evidence

- Total Daily Reports at closeout: **3367**
- Reports carrying `work_blocks_version = wp18c2.v1`: **3367**
- Reports already normalized before final compatibility stamp: **644**
- Reports compatibility-stamped with zero-block summary to avoid fabrication: **2723**

### Why zero-block compatibility stamping was used

For untouched historical records where a safe derived work-block connection could not be guaranteed inside the runtime closeout window, WP-18C2 followed the user’s binding rule:

- do not guess
- do not silently normalize
- do not fabricate relationships
- preserve the original record

Therefore those records were stamped with the governed contract fields and zero-block summary **without inventing contractual or schedule links**.

## Schedule Authority Guardrail

Every normalized work block stores `schedule_actual_proposal_status = proposed_only`.

This enforces the constitutional rule that Daily Reports may inform PM review but must **not silently overwrite schedule truth**.
