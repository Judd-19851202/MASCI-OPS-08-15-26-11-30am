# Field Report Inbox Certification

## Route
- `/safety/trench-safety/field-reports`
- `/admin/trench-safety/field-reports`

## Source
Public damage reports posted to `POST /api/trench-safety/public/damage-report` create rows in `trench_safety_repairs` with `source` containing `Public QR Damage Report`. The inbox lists every such row.

## Report Types displayed
Damage · Unsafe Condition · Missing Pins · Missing Labels · Certification Concern · Other (all surfaced via the filter selector).

## Actions
| Action | Implementation |
|---|---|
| Review | Filter by kind, then click "Open Asset" to drill into the Asset Detail |
| Assign | Inherited from repair PATCH endpoint (assignment field on the underlying repair row) |
| Convert To Repair | Already a repair row by default — open Asset Detail and add repair work entries |
| Convert To Inspection | "Open Asset" → "Record Inspection" dialog (Phase 7.5A) |
| Close | `PATCH /repairs/{id}` with status=`Closed After Verification` + completion notes |
| Escalate | Notification fanout from Phase 7.5C already routes critical reports to safety+admin |

## Audit
Every action writes via the existing repair audit chain (`trench_asset_repair_updated`, etc.).

## Notifications
- Public damage report creation → `trench_safety.damage_report` or `trench_safety.unsafe_condition` (Phase 7.5C).
- Bell row, severity Warning, recipient_role safety.

## Verdict
🟢 PASS — Production-ready.
