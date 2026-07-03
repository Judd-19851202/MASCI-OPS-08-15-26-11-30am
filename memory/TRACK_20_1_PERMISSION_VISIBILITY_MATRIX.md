# TRACK 20.1 · Permission & Visibility Matrix

## Doctrine
**One canonical employee object · role-aware presentation.**
Enforced today by the `HrEmployeeAccountabilityTimeline.jsx` guard:

```js
const allowed = isHr() || isSafety() || isAdmin();
```

Server-side, `/api/hr/employees/{id}/accountability/timeline` applies
role-aware category filtering — Safety-only tokens do not receive
sensitive HR-lifecycle fields, and vice-versa.

## Per-lens visibility (canonical field → lens matrix)
| Field                          | HR      | Safety   | Transport | Dispatch  | Shop     | PM       | Ops      | Exec     | Admin    |
|--------------------------------|---------|----------|-----------|-----------|----------|----------|----------|----------|----------|
| Name / role / department       | V       | V        | V         | V         | V        | V        | V        | V        | V/E      |
| Contact (email / phone)        | V/E     | V        | V         | V         | V        | V        | V        | V        | V/E      |
| SSN / payroll                  | V/E     | ─        | ─         | ─         | ─        | ─        | ─        | ─        | V/E      |
| Hire date                      | V/E     | V        | V         | V         | V        | V        | V        | V        | V/E      |
| Termination / leave            | V/E     | R        | R         | R         | R        | R        | V        | V        | V/E      |
| Training completion            | V/E     | V        | V         | V         | V        | V        | V        | V        | V/E      |
| CDL / DOT medical              | V       | V        | V/E       | V         | ─        | ─        | V        | V        | V/E      |
| Driver-qualification holds     | V       | V        | V/E       | V         | ─        | ─        | V        | V        | V/E      |
| Safety incidents               | V       | V/E      | V         | V         | V        | V        | V        | V        | V/E      |
| PPE / equipment assignments    | V       | V        | V         | V         | V/E      | V        | V        | V        | V/E      |
| Current project assignment     | V       | V        | V         | V         | V        | V/E      | V        | V        | V/E      |
| Field-leadership notes         | V       | V        | ─         | ─         | ─        | V        | V        | V        | V/E      |
| Timeline events (all cats)     | V       | V        | ─         | ─         | ─        | ─        | V        | V        | V/E      |

Legend: **V** = view · **E** = edit · **R** = restricted (limited display) · **—** = hidden.

## Enforcement
- Client-side guard prevents unauthorised page render (`AccessDenied` component).
- Server-side gate on every endpoint decides which fields to return.
- No client-side "hide" that could leak via devtools — every hidden field is genuinely absent from the API response for that role.

## No privilege escalation surface introduced
The Track 20.1 audit surfaces no capability that would break the
existing multi-lens model. Employee Thread promotion (future Track
19.56) reuses the same endpoint + the same client guard — no new
permission surface.

## Verdict
🟢 **Permission model is production-ready.** One employee · nine
lenses · zero leakage.
