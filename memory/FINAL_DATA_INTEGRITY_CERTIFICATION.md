# FINAL Data Integrity Certification

**Verdict:** 🟢 **PASS** — persistence contract preserved, historical records immutable, Trust Spine intact.

## Persistence contract

| Data | Storage | Immutability |
|---|---|---|
| Field Incident Report (original submit) | `incident_cases.field_block` (dict, `extra="allow"`) | Immutable after submit — Track 19.16 phase B contract |
| Case state transitions | `incident_case_events` timeline collection | Append-only |
| Evidence uploads | `incident_case_evidence` + Cloudflare R2 object storage | Withdrawal state visible, original preserved |
| Witnesses | `incident_case_witnesses` | Append-only |
| Statements | `incident_case_statements` | Append-only |
| Medical entries | `incident_case_medical` | Append-only |
| Police / Agency | `incident_case_agency` | Append-only |
| Root Cause | `incident_case_rca` (single doc per case) | Versioned |
| Corrective Actions | `incident_case_capa` | Owner, due, status tracked |
| Communications | `incident_case_communications` | Append-only |
| Notifications sent | `email_routing_audit_v2` | Append-only |
| Photos | Cloudflare R2 + metadata in `incident_case_evidence` | Original bytes preserved |
| GPS | Embedded in field_block + evidence metadata | Preserved |
| Reporter identity | `field_block.reporter_name` + case actor identity | Preserved |
| Trust Spine audit hash | Where applicable per doctrine | Preserved |

## Verified

- **`extra="allow"`** on Pydantic case models — dynamic field_block capture works for all 17 incident branches without schema changes.
- **`_id` → `id` mapping** via `PyObjectId` + `BaseDocument` pattern (MongoDB adherence).
- **`datetime.now(timezone.utc)`** used consistently (never `datetime.utcnow()`).
- **State machine** enforces valid transitions — see `incident_engine/state_machine.py`.
- **Case_service closeout summary** captures the final immutable disposition.

## Immutable original field report doctrine

The Foreman's original submission is stored verbatim in `incident_cases.field_block`. Safety's investigation ADDS additional collections (`incident_case_rca`, `incident_case_evidence`, etc.) — it never MUTATES the original field_block.

Result: If a Foreman reports 12 field observations at 14:22 and Safety later determines the incident was actually 3 separate events, the field_block still contains the Foreman's exact original report. Safety may create separate cases or add investigation context, but the original narrative is immutable.

## No silent data loss

- Autosave writes to localStorage every keystroke.
- Submit writes to backend with `{trace_id}` for correlation.
- Backend event emission is fire-and-forget with retry queue (Track 15.65 audit).
- Photo uploads chunked with resumability (Track 19.16 UX Hardening).

## Trust Spine

- All state transitions emit audit events.
- Every `resolve_and_audit(...)` call in `email_routing_v2` writes an append-only audit row.
- `event_hash_chain` (where applicable) protects sequential integrity — no Track 19.18 changes.

## Historical Record

- Historical incidents in the legacy `/api/incidents` collection are UNTOUCHED (Zero-Drift Doctrine).
- The new `incident_cases` collection is additive — legacy cases remain in their original form.
- Any future migration will be a deliberate, one-time, auditable operation.

## Verdict

🟢 **No data loss. No silent mutation. Trust Spine intact. Historical immutability preserved.**
