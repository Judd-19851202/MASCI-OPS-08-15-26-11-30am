# WP18C2 · PM Project Authority Evidence

## Implemented PM Routes

WP-18C2 added project-scoped PM authority routes under `/api/pm/project-controls/*`:

- `/overview?project_number=...`
- `/work-types`
- `/projects/{project_number}/pay-items`
- `/projects/{project_number}/mappings`
- `/projects/{project_number}/lookahead`
- `/projects/{project_number}/lifecycle`
- `/projects/{project_number}/archive`
- `/projects/{project_number}/restore`
- `/projects/{project_number}/crew-intelligence`
- `/projects/{project_number}/work-ledger`

## Scope Enforcement Evidence

Verified runtime behavior:

- Assigned PM project `ZZ-RUNTIME-CERT-2026` returns **200** for PM project-controls overview.
- Unassigned PM project request returns **403** with `project scope denied`.
- Testing agent report `iteration_111.json` marked PM scope enforcement **PASS**.

## Practical PM Authority Implemented

### Project pay items

Verified PM-created sample:

- `customer_pay_item_number = CERT-001`
- `description = Asphalt runtime certification pay item`
- `unit = TON`
- `contract_quantity = 125.5`
- `created_by = cert.pm@example.com`

### Governed mappings

Verified PM-approved sample:

- Pay item `CERT-001`
- Primary work type `work-type:asphalt`
- Status `approved`
- Approver `cert.pm@example.com`

### Two-week lookahead

Verified PM-published sample:

- `lookahead_id = lookahead:ZZ-RUNTIME-CERT-2026:current`
- `status = published`
- `version = 2`
- Task `CERT-ACT-1 / Certification prep`
- Constraint note `Awaiting city confirmation`

### Lifecycle and archive authority

Verified PM actions:

- Lifecycle update to `Active`
- Archive action with retained history
- Restore action with retained history

### Crew authority

Verified PM confirmation:

- Confirmed crew `Runtime Crew`
- Human confirmation actor `cert.pm@example.com`

## UI Evidence

PM page implemented at:

- Route: `/pm/project-controls`
- File: `/app/frontend/src/pages/PmProjectControlsAuthority.jsx`

Visible sections verified by testing agent:

- project picker
- summary cards
- pay items form
- governed mappings form
- two-week lookahead
- lifecycle/archive section
- crew intelligence
- work ledger

## Constitutional Boundary Preserved

PM authority in WP18C2 is **project scoped and practical**, but does not allow PMs to:

- alter enterprise work-type standards globally
- modify other projects outside scope
- convert Daily Reports into schedule truth
- implement budget hierarchy or earned value
