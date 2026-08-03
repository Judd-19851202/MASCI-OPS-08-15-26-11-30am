# WP18C2 · Project Pay Item and Work Type Model

## Constitutional Separation Implemented

WP-18C2 implemented **two distinct governed layers** and kept them separate in both storage and operator authority:

1. **Enterprise Work Types**
   - Collection: `enterprise_work_type_registry`
   - Admin route: `/api/admin/governance/project-controls/work-types`
   - Current runtime count: **16**
   - Purpose: reusable MASCI-wide classification for cross-project analysis, reporting, forecasting readiness, and future AI assistance.

2. **Project Pay Items**
   - Collection: `project_pay_item_registry`
   - PM route: `/api/pm/project-controls/projects/{project_number}/pay-items`
   - Current runtime count: **1** certified sample record
   - Purpose: customer / contract / project operational truth.

3. **Governed Mappings**
   - Collection: `project_pay_item_work_type_mappings`
   - PM route: `/api/pm/project-controls/projects/{project_number}/mappings`
   - Current runtime count: **1** approved mapping
   - Purpose: connect project-specific contractual truth to enterprise classification without collapsing the layers together.

## Implemented Enterprise Work Type Shape

Stored fields include:

- `work_type_id`
- `code`
- `name`
- `description`
- `category`
- `keywords[]`
- `status`
- `governance_owner = enterprise_work_type_registry`
- `effective_start`, `effective_end`
- `created_at`, `created_by`, `updated_at`, `updated_by`

Seeded WP18C2 standards include:

- Clearing
- Earthwork
- Drainage
- Asphalt
- Milling
- Base
- Concrete Curb
- Sidewalk
- Pipe
- Structures
- Striping
- MOT
- Electrical
- Landscaping
- Concrete Flatwork
- Runtime Test Work Type (QA-created during certification)

## Implemented Project Pay Item Shape

Stored fields include:

- `pay_item_id`
- `project_number`
- `customer_pay_item_number`
- `description`
- `unit`
- `contract_quantity`
- `contract_unit_price`
- `contract_value`
- `contract_id`
- `phase_id`
- `work_package_id`
- `schedule_activity_id`, `schedule_activity_name`
- `status`
- `effective_start`, `effective_end`
- `billing_relevance`, `production_relevance`, `schedule_relevance`
- `source`, `source_record`, `provenance`, `confidence`
- `created_at`, `created_by`, `updated_at`, `updated_by`

## Implemented Mapping Shape

Stored fields include:

- `mapping_id`
- `project_number`
- `pay_item_id`
- `customer_pay_item_number`
- `primary_work_type_id`
- `secondary_work_type_ids[]`
- `confidence`
- `source`
- `status`
- `mapper`, `approver`
- `matched_terms[]`
- `effective_start`, `effective_end`
- `explanation`
- `created_at`, `created_by`, `updated_at`, `updated_by`

## Human-Control Boundary

- PMs can manage **project pay items only inside their assigned project scope**.
- PMs can approve mappings for those same assigned projects.
- Admin governs enterprise work types.
- AI / deterministic matching can suggest a likely work type, but **cannot approve or silently apply the mapping**.
- A review queue record is created/resolved to preserve human approval evidence.

## Runtime Evidence

Certified PM sample project:

- Project: `ZZ-RUNTIME-CERT-2026`
- Pay item: `CERT-001`
- Description: `Asphalt runtime certification pay item`
- Approved mapping: `work-type:asphalt`
- Mapper / approver: `cert.pm@example.com`
- Review queue evidence: mapping-required item created then resolved by human approval.
