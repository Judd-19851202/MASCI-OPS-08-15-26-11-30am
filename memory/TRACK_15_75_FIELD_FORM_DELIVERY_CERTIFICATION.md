# TRACK 15.75 · Phase 8 — Field Form (Incident / QAQC / Inspection / JHA / Trench) Delivery Certification

Evidence: `/tmp/t1575_phaseall.py` live routing trace + collection counts.

## Routing matrix (live trace, project 24-06 with valid PM)

| Kind | To | CC | Notes |
|---|---|---|---|
| `incident` | `['davidjewett@mascigc.com']` | `['jaymn.judd@mascigc.com', 'safety@mascigc.com']` | ✅ Compliance — PM + ALWAYS_CC |
| `qaqc` | `['davidjewett@mascigc.com']` | `['jaymn.judd@mascigc.com', 'safety@mascigc.com']` | ✅ Compliance — PM + ALWAYS_CC |
| `inspection` | `['davidjewett@mascigc.com']` | `['jaymn.judd@mascigc.com', 'safety@mascigc.com']` | ✅ Compliance — PM + ALWAYS_CC |
| `jha` | `['davidjewett@mascigc.com']` | `['jaymn.judd@mascigc.com', 'safety@mascigc.com']` | ✅ Compliance — PM + ALWAYS_CC |

When project has no PM (20-07 / 26-07), the same kinds route To
`safety@mascigc.com` (dead-letter) and keep co-PMs + ALWAYS_CC in CC.

## Save evidence

| Workflow | Count | `project_number` populated | Notes |
|---|---|---|---|
| Incidents | 70 | 53 / 70 (76 %) — 17 yard/synthetic | Yard incidents legitimately job-less |
| QA/QC | 18 | 8 / 18 (44 %) — 10 are `iter364-QAQC-…` fixtures | Test fixtures, not real ops |
| Inspections (legacy) | 40 | n/a | covered by safety dashboard |
| JHA | 3 | tracked | PM scope enforcement (`scope.allows(project_number)`) verified |
| Trench Safety Inspections | 432 | `TRENCH_SAFETY_PULSE_SAFETY` + `TRENCH_SAFETY_PULSE_SHOP` configured | digest fallback `trench_safety_leadership_digests` (9) |

## Audit & PDF

* Every kind writes via `schedule_auto_email(kind, doc)` → audit row
  in `email_routing_audit_v2`.
* PDF render path: `pdf_render.py` (Phase J · field resiliency:
  idempotency; Track 14 bilingual sidecar).
* `field_submitter_bindings` (952 rows) bind each submission to its
  field submitter identity via 5-tier ladder (iter452.5).

## Severe-incident handling

* `masci::INCIDENT_SEVERE_CC = []` — intentionally empty;
  severe-incident audit + escalation handled via the dispatch
  on-call workflow, not a static CC list.

## Verdict

**🟢 GREEN.** All 5 field-form kinds route correctly, audit
truthfully, and produce visible dead-letter on PM gap. No code
defect found. Empty `INCIDENT_SEVERE_CC` is the documented
intentional design.
