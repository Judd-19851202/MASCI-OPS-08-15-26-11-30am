# Track 19.15 · 11 · Redesign Protection Matrix

Every existing field classified. **No schema deletion.** Fields can be hidden from the field UI, moved to the Safety case workspace, moved to an audit appendix, or removed from the PDF display — but the underlying schema key is preserved for historical record continuity.

## Classification

| Field | Class | Future disposition |
|---|---|---|
| `project_name` / `project_number` / `location` | FIELD FACT · MUST PRESERVE | Field UI Step 2 |
| `incident_date` / `incident_time` | FIELD FACT · MUST PRESERVE | Field UI Step 2 |
| `incident_type` | FIELD FACT · MUST PRESERVE | Field UI Step 1 (icon grid) |
| `severity` | FIELD FACT (initial) + SAFETY INVESTIGATION (final) · MUST PRESERVE | Field enters observed; Safety confirms |
| `osha_recordable` | REGULATORY · CAN MOVE TO SAFETY CASE | Removed from field UI; Safety case Step 5 |
| `root_cause_categories` | SAFETY INVESTIGATION · CAN MOVE TO SAFETY CASE | Removed from field UI; Safety case Step 3 |
| `corrective_actions` | SAFETY INVESTIGATION + MANAGEMENT · CAN MOVE TO SAFETY CASE | Field UI shows "immediate actions taken" instead; Safety case Step 6 |
| `witnesses[]` + `witness_count` | FIELD FACT · MUST PRESERVE | Field UI Step 7 |
| `incident_classifications` | SAFETY INVESTIGATION · CAN MOVE TO SAFETY CASE | Field can flag; Safety confirms in Step 2 |
| `reporter_signature` | FIELD FACT (audit) · MUST PRESERVE | Field UI Step 8 |
| `supervisor_signature` | FIELD FACT (audit) · MUST PRESERVE | Field UI Step 8 |
| Attachments (photos / videos / statements) | FIELD FACT + SAFETY EVIDENCE · MUST PRESERVE | Field UI Step 6 + Safety case Step 4 |
| Insurance fields | INSURANCE · CAN MOVE TO SAFETY CASE | Safety case Step 5 |
| Workers comp fields | LEGAL · CAN MOVE TO SAFETY CASE | Safety case Step 5 |
| Police report / agency notification | REGULATORY · CAN MOVE TO SAFETY CASE | Safety case Step 5 |
| Internal record IDs / timestamps | AUDIT ONLY · CAN MOVE TO APPENDIX | PDF section 14 (audit appendix) |
| System flags (`_internal_*`) | AUDIT ONLY · CAN REMOVE FROM PDF DISPLAY ONLY | Not rendered in any PDF |

## Business decisions required (NEEDS BUSINESS DECISION)

1. **How long is a case allowed to remain open?** Recommend 90-day SLA with escalation.
2. **Who is the default Safety investigator per project?** Route based on `email_routing_v2` project scope.
3. **Which incident types auto-escalate to Executive on submit?** Recommend: fatal injury, workplace violence with weapon, high-visibility public injury, fire, environmental spill > 25 gal.
4. **Retention period per incident type?** Default 7 years (OSHA), 10 years for utility strikes (Sunshine 811), 3 years for near-miss.

## Enforcement in future tracks

- Track 19.17 pytest asserts field UI does NOT render REGULATORY / SAFETY-INVESTIGATION fields.
- Track 19.18 pytest asserts Safety case workspace exclusively owns those fields.
- Track 19.19 pytest asserts audit appendix contains AUDIT-ONLY fields and that they don't leak into sections 1–13.
