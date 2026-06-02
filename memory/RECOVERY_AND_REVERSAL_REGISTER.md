# RECOVERY & REVERSAL REGISTER

**Authority**: FOCP MASTER PROGRAM · Phase 7
**Mode**: READ-ONLY · source-direct
**Date verified**: 2026-06-02

---

## Per-workflow recovery scaffolding

| Workflow | Undo last change | Reopen | Restore (deleted) | Reactivate | Reverse (rollback) | Amend |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Incident | ❌ (TR-0002) | ✅ LifecyclePanel | ✅ soft-delete | n/a | ❌ (TR-0002) | ✅ edit pre-close |
| Daily Report | ❌ (TR-0002) | 🟡 needs verify | ✅ | n/a | ❌ | ✅ |
| QA/QC | ❌ (TR-0002) | ✅ + Rework | ✅ | n/a | ❌ | ✅ |
| Site Inspection | ❌ (TR-0002) | ✅ + Rework | ✅ | n/a | ❌ | ✅ |
| Constraint | ❌ (TR-0002) | ❌ (doctrine, TR-0007) | ✅ | n/a | ❌ | ✅ |
| Employee Lifecycle | ❌ (TR-0002) | ✅ status change | ✅ | ✅ Reactivate / Rehire | ❌ | ✅ |
| PO Request | ❌ (TR-0002) | n/a | ✅ | n/a | ❌ | ✅ clarify |
| Time-Off Request | ❌ (TR-0002) | ✅ status change | ✅ | n/a | ❌ | ✅ |
| Asset Transfer | ❌ (TR-0002) | ✅ | ✅ | n/a | ❌ | ✅ |
| Payroll Variance | ❌ (TR-0002) | ✅ | ✅ | n/a | ❌ | ✅ |
| Dispatch | ❌ (TR-0002) | ✅ | ✅ | n/a | ❌ | ✅ reassign |
| Equipment | ❌ (TR-0002) | ✅ | ✅ | n/a | ❌ | ✅ |
| Driver Qualification | ❌ | n/a | ✅ | n/a | ❌ | ✅ |
| FleetDVIR | ❌ | 🟡 (TR needs ID) | ✅ | n/a | ❌ | 🟡 amend gap |
| Sub/Vendor | ❌ | ❌ (no archive, TR-0003) | ✅ | n/a | ❌ | ✅ |
| JHP / JHA | n/a (not built) | n/a | n/a | n/a | n/a | n/a (TR-0001) |
| Field Leadership record | ❌ | ✅ | ✅ | n/a | ❌ | ✅ |
| Notifications digest | n/a | n/a | n/a | n/a | n/a | n/a |
| MFA / Auth | n/a | n/a | ✅ recovery codes | ✅ re-enable | n/a | n/a |
| Backups | n/a | n/a | ✅ restore flow | n/a | ❌ | n/a |

## Coverage summary

| Recovery capability | Coverage |
|---|---|
| **Undo last change** | ❌ ~0% — universal undo verb missing across all workflows (TR-0002) |
| **Reopen** | 🟢 ~85% — present on all lifecycle-bearing workflows except Constraint (doctrine) and Sub/Vendor (build gap) |
| **Restore (soft-delete recovery)** | 🟢 ~100% — every collection supports soft-delete + restore via audit-log replay |
| **Reactivate (employee-specific)** | 🟢 ~100% — `HrEmployees.jsx` lifecycle-status mechanism |
| **Reverse (rollback prior state machine)** | ❌ ~0% — not designed into the platform; reverse = (delete event + create new with prior state). Equivalent to TR-0002. |
| **Amend (edit-after-submit)** | 🟢 ~90% — present on most workflows · gap on FleetDVIR (needs TR ID) |

## Closure of recovery gaps

| Gap | TR ID | Effort |
|---|---|---|
| Universal undo / status-reversal verb | TR-0002 | ~ 2 weeks (cross-workflow design + per-collection wiring + audit-log integration) |
| Sub/Vendor archive + restore | TR-0003 | ~ 1 week |
| Constraint reopen | TR-0007 | product-decision pending |
| FleetDVIR amend | new TR (TR-0009 candidate) | ~ 3 days |

## Architectural note

The platform's recovery doctrine is centered on **soft-delete + audit-log replay + reopen-by-state-transition** rather than a per-workflow undo button. This is a defensible choice for compliance-heavy domains (HR / Safety / Payroll) where every state change must be auditable. A universal undo verb (TR-0002) does NOT replace the soft-delete + audit-log substrate; it adds a one-tap operator affordance on top of it.

---

End of Recovery & Reversal Register.
