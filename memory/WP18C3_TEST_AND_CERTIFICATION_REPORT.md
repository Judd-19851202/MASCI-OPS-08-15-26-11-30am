# WP18C3 Test and Certification Report

Date: 2026-08-03

## Test inventory

### 1. Backend unit tests
- file: `/app/backend/tests/test_wp18c3_project_budget_foundation.py`
- result: `4 passed`

Validated:
- source-row normalization
- review-required suggestion behavior
- PDF line parsing
- budget-line kind detection

### 2. Live API certification flow

Executed against preview/runtime project `ZZ-RUNTIME-CERT-2026`:
- PM login: passed
- work-type lookup: passed
- governed CSV import 1: passed
- row approval 1: passed
- activation 1: passed
- governed CSV import 2: passed
- row approval 2: passed
- activation 2: passed
- PM overview after activation: passed
- PM budget export CSV: passed
- PM comparison export CSV: passed
- admin overview: passed
- direct service backfill verification: passed

### 3. Frontend smoke screenshot
- tool: Playwright screenshot smoke
- route: `/pm/project-controls/budget?project_number=ZZ-RUNTIME-CERT-2026`
- result: page loaded and screenshot captured successfully after PM login

### 4. Specialist testing agent
- report: `/app/test_reports/iteration_112.json`
- backend success: `100% (10 passed, 5 skipped due to session auth)`
- frontend success: `100%`

Verified by the agent:
- PM Budget Authority page
- admin Budget Authority page
- governed import workflow presence
- constitutional guardrail messaging
- trust-line separation
- non-blocking backfill button behavior
- regressions for existing C2 project-controls routes

## Certification verdict

WP-18C3 is certified as implemented for the approved scope:
- additive budget authority
- governed import / review / activation
- dual cost-code architecture preservation
- versioned budget history
- commitment / actual-cost foundation
- governed export / distribution logging
- admin + PM UI under WP-17 shells

## Residual note

The advisory suggestion stage is deterministic/rules-based reuse of existing C2 matching logic. It is non-authoritative and still requires PM approval, which remains constitutionally acceptable for C3.
