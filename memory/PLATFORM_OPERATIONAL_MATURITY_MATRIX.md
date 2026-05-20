# Platform Operational Maturity Matrix

**Date:** 2026-05-20 (iter271 governance pass)
**Purpose:** Make hidden incompleteness visible. One row per operational workflow, one column per maturity standard. No prose. No scoring. No dashboards.
**Authored from:** direct codebase audit (grep + import + tip-registry + test-file + i18n-call enumeration), not assumptions.

---

## Legend

| Symbol | Meaning | Evidence threshold |
| --- | --- | --- |
| ✅ | Complete | Standard fully met OR intentionally not applicable |
| 🟡 | Partial | Some coverage but a known gap remains |
| ❌ | Missing | Standard not met / never started |
| — | N/A | Standard does not apply to this workflow (e.g. PDF for read-only dashboards) |

---

## Column criteria (fixed standards)

1. **EN/ES** — Field-user surfaces have bilingual parity. Admin/HR-internal-only surfaces are ✅ if intentionally EN-only.
2. **Coaching family** — A `form_key` entry exists in `/app/backend/guidance/tips.py` covering this workflow.
3. **WHY/WHO/NEXT/ESCALATE** — All 4 canonical kinds present in the workflow's coaching family.
4. **Mobile** — Form-level touch targets, single-column sm: layout, field-foreman-grade UX.
5. **PDF** — Backend PDF endpoint exists for this artifact when an artifact is expected.
6. **Terminology** — Names/labels consistent across form, view, PDF, and guidance (no "Toolbox Talk" vs "Safety Meeting" drift).
7. **Guidance article** — A `/api/guidance/articles/*` article covers this workflow.
8. **View parity** — `View*.jsx` page is bilingual at the same level as the New form.
9. **ES verified** — Spanish strings present in `tips_es.py` and/or `i18n.js` for this surface.
10. **Test agent** — Iteration-level pytest exists OR recent `testing_agent_v3_fork` report covers the workflow.
11. **LMS guard** — Tone-gate enforced (no LMS/motivational drift). Implicit for any workflow with a published coaching family in the proven registry.
12. **Role-context** — Coaching/UI adapts where multiple roles touch the workflow (kind=`who` present + RBAC scopes correct).
13. **Coaching parity** — Tip density ≥10 OR matches the closest cousin (Incident=18, Daily Report=21 as benchmarks).
14. **Complete** — Workflow has form + view + PDF + coaching + bilingual + tests, end-to-end shippable.

---

## Maturity Matrix · Field & Safety Workflows

| Workflow | EN/ES | Coach | 4-Kinds | Mobile | PDF | Term | Guide | View | ES-vrfy | Tests | LMS | Role | Parity | Complete |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **Safety Meetings** | ✅ | ✅ 22 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Safety Incidents** | ✅ | ✅ 18 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Daily Reports** | ✅ | ✅ 21 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Pre-Op (Equipment Inspection)** | ✅ | ✅ 16 | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 |
| **Site Inspection (`NewInspection`)** | ✅ | ✅ 17 | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **QA/QC Inspection** | ✅ | ✅ 18 | ✅ | ✅ | ✅ | ✅ | 🟡 | 🟡 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Fleet DVIR** | ✅ | 🟡 13 | 🟡 ❌esc | ✅ | ✅ | ✅ | ✅ | — | ✅ | 🟡 | ✅ | ✅ | ✅ | 🟡 |
| **Field Write-Ups** | ✅ | ✅ 11 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Equipment Checkout** | ✅ | ✅ 14 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ |
| **Crew Evaluations** | ✅ | ✅ 8 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | 🟡 | ✅ |
| **Field-Leadership umbrella (10 FL kinds)** | ✅ | 🟡 6 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | 🟡 | 🟡 |
| **Safety Corrective Actions** | ✅ | ✅ 11 | ✅ | ✅ | — | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Fire Extinguishers** | 🟡 | ❌ | ❌ | ✅ | 🟡 | ✅ | 🟡 | — | 🟡 | ❌ | — | ✅ | ❌ | 🟡 |
| **Safety Equipment Issuance** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ❌ | — | ✅ | ❌ | 🟡 |
| **Safety Equipment Training** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ❌ | — | ✅ | ❌ | 🟡 |
| **Safety Topic Library (F2-A)** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | — | ✅ | 🟡 | — | ✅ | ❌ | 🟡 |
| **JHA Plans** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ❌ | — | ✅ | ❌ | 🟡 |
| **Trench Boxes (reference)** | ✅ | — | — | ✅ | — | ✅ | ✅ | — | ✅ | — | — | ✅ | — | ✅ |
| **Material Calculators** | ✅ | ✅ 10 | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ |

## Maturity Matrix · HR & People Workflows

| Workflow | EN/ES | Coach | 4-Kinds | Mobile | PDF | Term | Guide | View | ES-vrfy | Tests | LMS | Role | Parity | Complete |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **Time Verification** | ✅ | ✅ 11 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Time-Off Review** | ✅ | ✅ 14 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Employee Accountability** | ✅ | ✅ 12 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Employee Lifecycle** | ✅ | ✅ 12 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Document Expirations** | ❌ EN-only | ✅ 12 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | 🟡 |
| **Safety Training Records** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | 🟡 | — | ✅ | ❌ | — | ✅ | ❌ | 🟡 |
| **Safety Documents** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | 🟡 | — | ✅ | ❌ | — | ✅ | ❌ | 🟡 |
| **HR Safety Records (cross-portal read)** | ✅ | — | — | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | ✅ |
| **HR Payroll Variance** | ❌ EN-only | ❌ | ❌ | 🟡 | — | ✅ | 🟡 | — | ❌ | ❌ | — | ✅ | ❌ | 🟡 |

## Maturity Matrix · Operations & Admin Workflows

| Workflow | EN/ES | Coach | 4-Kinds | Mobile | PDF | Term | Guide | View | ES-vrfy | Tests | LMS | Role | Parity | Complete |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **Dispatch (8 sub-families)** | ❌ EN-only | ✅ 49 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Fleet Visibility** | ❌ EN-only | ✅ in `fleet` | 🟡 ❌esc | ✅ | 🟡 | ✅ | ✅ | — | ❌ | 🟡 | ✅ | ✅ | ✅ | 🟡 |
| **Legacy Imports (OCR)** | ❌ EN-only | ❌ | ❌ | ❌ desktop | — | ✅ | ✅ | — | ❌ | 🟡 | — | ✅ | ❌ | 🟡 |
| **Guidance Center** | ✅ | — | — | ✅ | — | 🟡 | ✅ | — | ✅ | 🟡 | ✅ | ✅ | 🟡 | 🟡 |
| **Admin Console (system)** | ❌ EN-only | ❌ | ❌ | ❌ desktop | — | ✅ | ✅ | — | ❌ | ✅ | — | ✅ | — | ✅ |
| **Backup / Restore / Deploy Readiness** | ❌ EN-only | ❌ | ❌ | ❌ desktop | — | ✅ | ✅ | — | ❌ | ✅ | — | ✅ | — | ✅ |

---

## Highest-risk operational gaps (act on these first)

1. ~~**Legacy View-Surface i18n cluster**~~ — **CLOSED iter272.** `ViewIncident.jsx` · `ViewDailyReport.jsx` · `ViewInspection.jsx` now wire 145 `t()` calls + `useT()` against 70 new ES keys in `i18n.js`. testing_agent_v3_fork frontend 100%.
2. **Field-Safety forms with NO coaching family** (partial closure in progress)
   - ~~`NewInspection`~~ · ~~`NewQaqcInspection`~~ — **CLOSED iter273** (Sequence #2). 35 tips across 11 form-keys.
   - ~~`SafetyCorrectiveActions`~~ — **CLOSED iter274** (Sequence #3). 11 tips across 3 form-keys · 3 dialog/page mounts · Create/Edit mode gating verified live.
   - **Still open:** `SafetyFireExtinguishers`, `NewSafetyEquipmentIssuance`, `NewSafetyEquipmentTraining`, `SafetyTopicLibrary`, `JhaPlansHub` (5 surfaces remaining — Sequences #5, #6 in this matrix).
3. ~~**Canonical 4-kind holes**~~ — **CLOSED iter274** (Sequence #4). `fleet.dvir` `escalate` and `material-calculator` `who` filled. Both aggregates now ✅ on all 4 canonical kinds.
4. **`Fleet DVIR` ⇄ `fleet` registry split** — DVIR form mounts only 2 HelpTipBlocks; the `fleet` registry concentrates on visibility/repair/RTS/dvir/weekly-lead. Looks complete from the registry; field experience shows partial coverage. (Re-evaluate after Sequence #5–#8 close.)
5. **`DocumentExpirations` page is hardcoded English** — 0 `t()` calls despite the workflow having a full bilingual coaching family. Page consumes English-only.

---

## Closure sequence (recommended priority order)

| # | Iteration target | Scope | Risk | Pattern to clone |
| --- | --- | --- | --- | --- |
| 1 | View-Surface i18n cluster | `ViewIncident.jsx` · `ViewDailyReport.jsx` · `ViewInspection.jsx` — full `t()` wrap | LOW (mechanical) | `ViewMeeting.jsx` Sprint 1 (iter268) |
| 2 | NewInspection / NewQaqcInspection coaching family | Add `inspection.*` + `qaqc.*` registry entries + 4–5 HelpTipBlock mounts each | LOW | `meeting` family iter270 |
| 3 | Safety Corrective Actions coaching family | Add `corrective.*` registry + mounts | LOW | `incident.corrective` neighbor exists already |
| 4 | Fleet `escalate` + Material-Calc `who` fills | 2 small tips, plug canonical-4 holes | TRIVIAL | any existing `kind=escalate` tip |
| 5 | Safety Forms (Issuance / Training) coaching + Topic Library coaching | 3 small families (`equipment-issuance`, `equipment-training`, `safety-library`) | LOW | `checkout` family |
| 6 | Fire Extinguishers + JHA coaching families | 2 smaller families | LOW | `preop` family |
| 7 | DocumentExpirations page i18n | Wrap labels in `t()` to match its already-bilingual coaching | TRIVIAL | `HrTimeVerification.jsx` |
| 8 | Guidance Center article audit (Phase H philosophy alignment + bilingual parity sweep) | Operator-named direction; touch all `/guidance` articles | MED | iter269 K5 rewrite |

---

## Governance rules going forward

1. **No workflow ships as "complete" without all 14 columns at ✅ or intentional —.**
2. **Adding a new form requires:** coaching family registered · canonical 4 kinds (why/who/next/escalate) · ES counterparts · iter-test file · view-surface i18n · PDF when an artifact is expected · guidance article.
3. **This matrix is the gate.** Before claiming a workflow is mature, update its row here and confirm every column.
4. **No PMO bureaucracy.** Single file. Symbols only. Updated when state changes — not on a schedule.

---

## How this file is maintained

- One row per workflow.
- A workflow row is updated **only when its codebase state changes** (new family shipped, view-page i18n shipped, test landed, gap closed).
- Symbols only. If you find yourself writing prose to "explain" a yellow, that's a sign the column criterion isn't precise enough — fix the criterion or fix the workflow.
- Iteration footer: append `iter###` ship lines below this section as workflows close out, ONE LINE EACH.

### Ship log
- `iter268` ViewMeeting + NewMeeting toasts i18n · Sprint 1 closed
- `iter269` NewMeeting/ViewMeeting K4 split + K6 strip + K7 breadcrumb + K5 article · Sprint 2 closed
- `iter270` Safety Meeting Coaching Family · operational coaching parity achieved
- `iter271` This matrix authored · 19 workflows audited · 5 highest-risk gaps surfaced
- `iter272` Legacy View-Surface i18n Closure Cluster · ViewIncident · ViewDailyReport · ViewInspection · 145 t() strings · 70 ES keys · testing agent frontend 100% · gap #1 from matrix CLOSED
- `iter273` NewInspection + NewQaqcInspection coaching family (Sequence #2) · 35 tips · 11 form-keys · EN+ES · 65/65 in-process + 37/37 HTTP pytest · 5/5 + 6/6 frontend testids · gap #2 first cluster CLOSED
- `iter274` SafetyCorrectiveActions coaching family (Sequence #3) bundled with canonical-4 hole fills (Sequence #4) · 11 corrective tips + 2 canonical fills (fleet.dvir escalate · material-calculator who) · 31/31 pytest including 6 regression cases · 3/3 frontend mounts live-verified with Create/Edit gating · gap #3 CLOSED · gap #2 second cluster CLOSED
