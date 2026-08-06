# WP18DB Field Auth Contract Certification

## Scope

This certification covers the reopened field-report auth contract for the Incident workflow and the related session-handling path used by the field submission UI.

## Certified actor matrix

| Actor / header set | Expected result | Certified result |
|---|---|---|
| No auth | deny | `401` |
| `X-Directory-Token` only | deny | `401` |
| `X-Directory-Token` + `X-FL-Token` | allow field create / patch / evidence / submit | `200 / 200 / 200 / 200` |
| `X-Directory-Token` + `X-PM-Token` | do not allow field create if not explicitly authorized | `403` |
| `X-Directory-Token` + `X-Safety-Token` | preserve safety read gate | `200` on list/read path used in proof |

## Certified backend contract

### Entry gate

- field reporting routes now accept Field Leadership through `make_require_safety_admin_pm_or_field(...)`
- Field Leadership acceptance still requires the existing async FL token validation and active session activity check

### Authority source of truth

- accepted field users are normalized to `role="field"`
- write authority remains governed by the existing incident capability matrix (`role_can(...)`)
- PM-only create remains denied

### Non-field workspace protection preserved

- broader incident workspace routes remain behind the original Safety/Admin/PM review gate unless explicitly wired to the narrow field gate

## Certified frontend contract

File: `frontend/src/lib/incidentReportApi.js`

- Incident Report requests now use the shared `api` client
- scoped headers now include `field_leadership`
- shared session/auth-failure handling is no longer bypassed by a separate standalone client

## Draft preservation / continuity proof

### Bounded preview proof executed

Route: `/incidents/report`

Proof steps:

1. open Incident Report
2. pick an incident type
3. enter step data
4. confirm draft keys appear in browser storage
5. reload the page
6. confirm the same draft keys remain and the draft indicator is still present

Observed draft keys before and after reload:

- `masci.incident_report.draft.v1.__index__`
- `masci.incident_report.draft.v1.dr_msi5nony_7lew3e`

Observed after reload:

- `incident-report-draft-indicator` present
- entered step state restored on the same draft shell

## Session-failure handling conclusion

The reopened repair removed the custom Incident axios bypass and returned the Incident flow to the platform’s governed shared API/session path. Combined with the existing per-keystroke draft persistence, this closes the reopened data-loss risk where a field reporter could hit auth failure and lose work-in-progress state.

## Certification result

**CERTIFIED IN PREVIEW:** the field auth contract now accepts the real Field Leadership token family on the intended incident-report surfaces, preserves denials for unauthorized / directory-only / PM-only create attempts, and retains draft continuity across reload/interruption on the Incident shell.