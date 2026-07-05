# ODS-001 · Backward Compatibility

## What was proven

| Surface | Proof |
| --- | --- |
| V1 Daily Reports POST | still 200 (curl-tested) — route unchanged |
| V1 Daily Reports GET | still 200 — route unchanged |
| V1 PDF path | untouched — no code path in this track imports `pdf_generator` |
| V1 Email routing | untouched — no code path in this track imports `email_router` |
| HR time entries | untouched — no writes to `hr_time_entries` |
| Payroll variance | untouched — no writes to `payroll_variance_records` |
| Safety gates (excavation JHA, trench, silica) | untouched — no writes to safety collections |
| Job Photos mirror | untouched — spine `photo_evidence_fact` only READS photo refs |
| DR-V2 shell + feature flag | still renders; feature-flag semantics unchanged |
| DR-V2 AI synthesis | still returns 3 agent outputs, evidence-cited, confidence-scored |
| DR-V2 approval + audit log | still works; approval-accept now also emits `intelligence_fact` |
| OpenAPI paths | 1264 → 1270 → 1277 (exact +6 DR-V2 · +7 ODS) — no V1 paths removed |
| Route count | 1441 → 1447 → 1455 (exact +6 DR-V2 · +8 ODS handler methods) |
| Method count | 1445 → 1451 → 1459 |
| Frontend V1 route | still renders "Daily Job Report" title; 0 `dr-v2-*` selectors leak |

## Guards

- `test_dr_v2_never_writes_to_daily_reports` — forbids V1 collection access from DR-V2 route.
- `test_ods_never_writes_to_daily_reports` — forbids V1 collection access from ODS routes and ingestors.
- `test_backend_runtime_parity_intact` — locks route/method/openapi counts.
- `test_backend_lifecycle_and_email_safety_unchanged` — locks EMAIL_SAFETY_MODE=strict.
- `test_dr_v2_phase_c_routes_mounted` — verifies additive DR-V2 mount.
- `test_ods_routes_are_mounted` — verifies additive ODS mount.

## Feature flags default state

- `ODS_ENABLED` — default OFF
- `DR_V2_SPINE_EMISSION_ENABLED` — default OFF
- `DR_V2_AI_ENABLED` — default OFF
- `AI_GATEWAY_ENABLED` — default OFF
- `dr_v2_optin` (localStorage) — default absent → V1 users see nothing new

Preview environment has all four ON for demo. Production rollout is a per-tenant flip.
