# TRACK 20.4 · Role Lens · Permission Matrix

**High-risk track.** Vendor records touch tax data, contracts, insurance, and financial obligations. The future Vendor Thread must never widen access. HR/Admin owns the master; PM/Safety/Shop/etc. read through role-aware lenses.

## Read visibility by role (proposed lens for Track 19.60 · not enforced by this audit)
| Field / rendering slot          | HR/Admin | Accounting/AP | Admin | Executive | PM      | Safety  | Shop    | Fleet   | Dispatch | Trans   | Field   | Public |
|---------------------------------|:--------:|:-------------:|:-----:|:---------:|:-------:|:-------:|:-------:|:-------:|:--------:|:-------:|:-------:|:------:|
| Vendor name / status            | ✅       | ✅            | ✅    | ✅        | ✅      | ✅      | ✅      | ✅      | ✅       | ✅      | ❌      | ❌     |
| Tax ID / EIN                    | ✅       | ✅            | ✅    | ❌        | ❌      | ❌      | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| W-9 on file (yes/no)            | ✅       | ✅            | ✅    | Summary   | Summary | Summary | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| W-9 document                    | ✅       | ✅            | ✅    | ❌        | ❌      | ❌      | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| COI on file / expiration        | ✅       | ✅            | ✅    | Summary   | ✅ ¹    | ✅ ¹    | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| COI document                    | ✅       | ✅            | ✅    | ❌        | ❌      | Redacted| ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| Business license                | ✅       | ✅            | ✅    | Summary   | ✅ ¹    | ✅ ¹    | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| Contracts                       | ✅       | ✅            | ✅    | Summary   | ✅ ¹    | ❌      | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| Contract value                  | ✅       | ✅            | ✅    | Summary   | Summary | ❌      | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| Purchase orders                 | ✅       | ✅            | ✅    | Summary   | ✅ ² (own PMs) | ❌ | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| Invoices / payments             | ✅       | ✅            | ✅    | Summary   | ❌      | ❌      | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| Contacts                        | ✅       | ✅            | ✅    | Summary   | ✅      | ✅      | ✅      | ✅      | ✅       | ✅      | ❌      | ❌     |
| Projects worked                 | ✅       | ✅            | ✅    | ✅        | ✅ ² (own) | Summary | Summary | Summary | Summary  | Summary | ❌     | ❌     |
| Safety issues / incidents       | ✅       | ❌            | ✅    | Summary   | Summary | ✅      | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| Performance notes               | ✅       | ✅            | ✅    | Summary   | Summary | Summary | Summary | Summary | Summary  | Summary | ❌      | ❌     |
| Do-not-use / restricted flag    | ✅       | ✅            | ✅    | ✅        | ✅      | ✅      | ✅      | ✅      | ✅       | ✅      | ❌      | ❌     |
| Documents (generic list)        | ✅       | ✅            | ✅    | Summary   | Summary | Summary | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |
| Audit                           | ✅       | ❌ ³          | ✅    | ❌        | ❌      | ❌      | ❌      | ❌      | ❌       | ❌      | ❌      | ❌     |

¹ PM / Safety see COI + license + prequalification status because these are operationally required to allow a vendor on a jobsite.
² PM sees POs / projects / contracts only for projects they manage.
³ Accounting sees a scoped payment audit, not the full vendor audit.

## Critical guardrails
- **PM does not own the vendor master** even if they are the primary consumer of vendor data.
- **PM never sees Tax ID / EIN**.
- **HR/Admin retains sole write authority** for master data and document approvals.
- **Do-not-use flag is Admin-only write, everyone reads** — protects the field.
- **Contract value never leaks to Safety / Fleet / Shop / Field**.
- **Every role sees only what their operational job requires.**

## No permission widening
**Track 19.60 (proposed) inherits every source endpoint's existing gate. No new visibility surface. No new leak vector.**
