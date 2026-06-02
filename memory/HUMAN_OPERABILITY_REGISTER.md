# HUMAN OPERABILITY REGISTER

**Authority**: FOCP MASTER PROGRAM · Phase 3
**Mode**: READ-ONLY · source-direct portion only (human-validation portion deferred to Phase 12)
**Date verified**: 2026-06-02

---

## Caveat (read first)

Phase 3 asks six human-validation questions: *Can users find it · understand it · complete it · recover · trust it · operate without Jaymn?* Three of those (understand · trust · operate without Jaymn) can only be answered by interviewing actual users (Phase 12). What I CAN do here is verify the **source-side scaffolding** that makes each answer possible:

* **Find** → presence of nav entries, hub tiles, search hits, breadcrumb breadcrumbs
* **Complete** → presence of explicit submit / save affordances · sticky-footer pattern · top-level verbs
* **Recover** → presence of undo / reopen / restore / amend paths
* **Understand** (proxy) → presence of help-tips, coaching text, in-page guidance
* **Trust** (proxy) → presence of audit-trail / state-events / chronology surfaces
* **Without Jaymn** (proxy) → presence of LifecycleGuide / in-app explainer / documentation links

Deeper "user actually understands" / "user actually trusts" requires Phase 12 interviews.

---

## Source-side scaffolding inventory

| Workflow | Findable | Completable | Recoverable | Help-tip | Audit-trail | Self-explanatory |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Incident | ✅ Hub · sidebar · search | ✅ Rank #1 sticky footer | ✅ Reopen via LifecyclePanel | ✅ HelpTip + LifecycleGuide | ✅ state-events endpoint | ✅ |
| Daily Report | ✅ Hub · "Today in the Field" group | ✅ Rank #1 sticky footer + targeted correction | 🟡 reopen path needs deeper verify (TR-0008-related) | ✅ HelpTip | ✅ state-events | ✅ |
| QA/QC | ✅ Hub · search | ✅ pre-existing sticky bar | ✅ Reopen + Rework via LifecyclePanel | ✅ | ✅ | ✅ |
| Site Inspection | ✅ | ✅ Rank #1 sticky | ✅ Reopen + Rework | ✅ | ✅ | ✅ |
| Constraint | ✅ | ✅ inline | 🟡 no reopen (by doctrine) | 🟡 needs doctrine doc link | ✅ ChronologyPanel | 🟡 |
| Employee Lifecycle | ✅ HR sidebar | ✅ HR sticky-drawer footer | ✅ status reversal via HR | ✅ | ✅ status_history | ✅ |
| PO Requests | ✅ | ✅ panel-anchored buttons | ✅ amend / clarify | ✅ | ✅ audit array | ✅ |
| Time-Off | ✅ | ✅ HR Decision dialog | ✅ status changes | ✅ | ✅ | ✅ |
| Asset Transfers | ✅ | ✅ state-action map | ✅ | ✅ | ✅ | ✅ |
| Driver Qualification | ✅ | ✅ | ✅ | ✅ expiring-soon flag | ✅ | ✅ |
| FleetDVIR | ✅ | ✅ | 🟡 amend path | ✅ | ✅ | 🟡 |
| Sub/Vendor | ✅ list | ✅ create / edit | ❌ no archive (TR-0003) | ✅ | ✅ | ✅ |
| JHP / JHA | 🟡 | 🟡 | ❌ no ack path (TR-0001) | 🟡 | 🟡 | 🟡 |
| Dispatch | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Payroll Variance | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Equipment | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Notifications digest | ✅ | ✅ | n/a | ✅ | ✅ | ✅ |
| MFA / Auth | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Backups | ✅ admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| Field Leadership | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Operational Timeline (read-only surface) | ✅ | n/a | n/a | ✅ | ✅ | ✅ |

## Source-side Human Operability score

**~ 79 %** (no change from `REVISED_ITER501_ROADMAP.md`).

Gaps mapped to Truth Register:
* JHP / JHA scaffolding deficit → TR-0001
* Sub/Vendor archive → TR-0003
* Constraint reopen / doctrine link → TR-0007
* Universal undo (cross-workflow) → TR-0002
* FleetDVIR amend → needs new TR

## What this register CANNOT tell us

Whether users **actually find** these surfaces under field conditions. Whether they **actually understand** the status vocabulary. Whether they **actually trust** the audit trail. Those require Phase 12 interviews (`OPERATIONAL_REALITY_VALIDATION.md`).

Therefore the answer to "Can users operate without Jaymn?" remains **provisionally YES on source-scaffolding grounds, INCONCLUSIVE without Phase 12 evidence**.

---

End of Human Operability Register.
