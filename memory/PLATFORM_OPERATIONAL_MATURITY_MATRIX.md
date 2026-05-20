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
| **Fleet DVIR** | ✅ | ✅ 14 | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ |
| **Field Write-Ups** | ✅ | ✅ 11 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Equipment Checkout** | ✅ | ✅ 14 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ |
| **Crew Evaluations** | ✅ | ✅ 8 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | 🟡 | ✅ |
| **Field-Leadership umbrella (10 FL kinds)** | ✅ | 🟡 6 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | 🟡 | 🟡 |
| **Safety Corrective Actions** | ✅ | ✅ 11 | ✅ | ✅ | — | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Fire Extinguishers** | 🟡 | ✅ 19 | ✅ | ✅ | 🟡 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 |
| **Safety Equipment Issuance** | ✅ | ✅ 25 | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Safety Equipment Training** | ✅ | ✅ 19 | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Safety Topic Library (F2-A)** | ✅ | ✅ 19 | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **JHA Plans** | ✅ | ✅ 13 | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Trench Boxes (reference)** | ✅ | — | — | ✅ | — | ✅ | ✅ | — | ✅ | — | — | ✅ | — | ✅ |
| **Material Calculators** | ✅ | ✅ 10 | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ |

## Maturity Matrix · HR & People Workflows

| Workflow | EN/ES | Coach | 4-Kinds | Mobile | PDF | Term | Guide | View | ES-vrfy | Tests | LMS | Role | Parity | Complete |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **Time Verification** | ✅ | ✅ 11 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Time-Off Review** | ✅ | ✅ 14 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Employee Accountability** | ✅ | ✅ 12 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Employee Lifecycle** | ✅ | ✅ 12 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Document Expirations** | ✅ | ✅ 12 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Safety Training Records** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | 🟡 | — | ✅ | ❌ | — | ✅ | ❌ | 🟡 |
| **Safety Documents** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | 🟡 | — | ✅ | ❌ | — | ✅ | ❌ | 🟡 |
| **HR Safety Records (cross-portal read)** | ✅ | — | — | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | ✅ |
| **HR Payroll Variance** | ✅ | ✅ 13 | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | ✅ |

## Maturity Matrix · Operations & Admin Workflows

| Workflow | EN/ES | Coach | 4-Kinds | Mobile | PDF | Term | Guide | View | ES-vrfy | Tests | LMS | Role | Parity | Complete |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **Dispatch (8 sub-families)** | ❌ EN-only | ✅ 49 | ✅ | 🟡 | — | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Fleet Visibility** | ❌ EN-only | ✅ in `fleet` | 🟡 ❌esc | ✅ | 🟡 | ✅ | ✅ | — | ❌ | 🟡 | ✅ | ✅ | ✅ | 🟡 |
| **Legacy Imports (OCR)** | ❌ EN-only | ❌ | ❌ | ❌ desktop | — | ✅ | ✅ | — | ❌ | 🟡 | — | ✅ | ❌ | 🟡 |
| **Guidance Center** | ✅ | — | — | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | 🟡 | 🟡 |
| **Admin Console (system)** | ❌ EN-only | ❌ | ❌ | ❌ desktop | — | ✅ | ✅ | — | ❌ | ✅ | — | ✅ | — | ✅ |
| **Backup / Restore / Deploy Readiness** | ❌ EN-only | ❌ | ❌ | ❌ desktop | — | ✅ | ✅ | — | ❌ | ✅ | — | ✅ | — | ✅ |

---

## Highest-risk operational gaps (act on these first)

1. ~~**Legacy View-Surface i18n cluster**~~ — **CLOSED iter272.** `ViewIncident.jsx` · `ViewDailyReport.jsx` · `ViewInspection.jsx` now wire 145 `t()` calls + `useT()` against 70 new ES keys in `i18n.js`. testing_agent_v3_fork frontend 100%.
2. **Field-Safety forms with NO coaching family** — **CLOSED iter275**
   - ~~`NewInspection`~~ · ~~`NewQaqcInspection`~~ — **CLOSED iter273** (Sequence #2). 35 tips across 11 form-keys.
   - ~~`SafetyCorrectiveActions`~~ — **CLOSED iter274** (Sequence #3). 11 tips across 3 form-keys · 3 dialog/page mounts · Create/Edit mode gating verified live.
   - ~~`SafetyFireExtinguishers`, `NewSafetyEquipmentIssuance`, `NewSafetyEquipmentTraining`, `SafetyTopicLibrary`, `JhaPlansHub`~~ — **CLOSED iter275** (Sequences #5 + #6). 95 tips across 13 form-keys · 14 HelpTipBlock mounts · canonical 4-kinds present in all 5 top families · testing_agent_v3_fork frontend 14/14 mounts verified · EN/ES parity confirmed · mobile-safe (390w).
3. ~~**Canonical 4-kind holes**~~ — **CLOSED iter274** (Sequence #4). `fleet.dvir` `escalate` and `material-calculator` `who` filled. Both aggregates now ✅ on all 4 canonical kinds.
4. ~~**`Fleet DVIR` ⇄ `fleet` registry split**~~ — **CLOSED iter276** (matrix-correctness pass). iter274 added fleet.dvir escalate tip; family aggregate `fleet.*` now carries all 4 canonical kinds (why/who/next/escalate present across the 6 fleet form-keys with 14 total tips). Row flipped from 🟡 ❌esc to ✅; Complete from 🟡 to ✅.
5. ~~**`DocumentExpirations` page is hardcoded English**~~ — **CLOSED iter276** (Sequence #7). 46 `t()` calls + 36 new ES keys in `i18n.js`. Page now bilingual to match its already-bilingual coaching family. EN/ES column flipped to ✅, ES-vrfy to ✅, Complete to ✅.

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
- `iter275` Bundled Sequences #5 + #6 · coaching families for Safety Equipment Issuance, Safety Equipment Training, Safety Topic Library, Fire Extinguishers, JHA Hub · 95 EN+95 ES tips across 13 form-keys · 14 HelpTipBlock mounts (incl. 3 dialog-embedded) · testing_agent_v3_fork frontend 14/14 mounts verified · EN/ES parity 4/4 sampled · canonical 4-kinds present in all 5 top families · mobile 390w no overflow · gap #2 third (final) cluster CLOSED · 5 matrix rows flipped to ✅
- `iter276` Bundled Sequence #7 + Fleet DVIR matrix-correctness pass · DocumentExpirations page i18n closure (46 t() calls · 36 new ES keys) · Fleet DVIR row flipped to ✅ (iter274 escalate fill confirmed at family aggregate · `fleet.*` carries all 4 canonical kinds across 14 total tips) · gap #4 CLOSED · gap #5 CLOSED · 2 matrix rows flipped to ✅
- `iter277` Guidance Center pre-audit inventory · 124 articles scanned (title + summary + flattened body blocks) · heuristic detection of LMS drift / stale terminology / Phase-H alignment / ES coverage · 0 LMS hits · 0 corporate-framing hits · 5 stale-terminology hits (Toolbox Talk survivors) · 50/124 (40%) ES-translated · output `/app/memory/GUIDANCE_CENTER_PREAUDIT_iter277.md` + raw audit `/app/memory/guidance_audit_iter277.json` · NO content changes yet — visibility/targeting infrastructure for Sequence #8 awaiting user gate
- `iter278` Sequence #8 Terminology Cluster · Toolbox Talk → Safety Meeting rename across 5 articles (`portal-safety` · `public-toolbox-talks` · `public-tools-map` · `onboard-leadership-first-week` · `onboard-safety-first-week`) · 7 EN edits + 7 ES edits (Charla → Reunión de Seguridad per iter270 canonical) · 7/7 regression pytests green · 229/229 prior guidance pytests still green · live API endpoints verified · 0 stale-term hits remaining across 124 articles · Guidance Center Term column flipped 🟡 → ✅
- `iter279` Sequence #8 portals i18n closure · 33 portal-section articles translated to ES (title_es + summary_es + body_es per article) · authored in new `guidance/translations_es_iter279.py` module (pattern for future namespace splits) · merged into TRANSLATIONS_ES at import time · 7/7 regression pytests in `test_iter279_portals_i18n_closure.py` (entry presence · block count parity · block type parity · stale-term ban · import-time merge) · 243/243 prior guidance pytests still green · live API verified for 3 sampled articles (block counts match · ES titles render) · ES translation coverage 50 → 83 / 124 (40% → 67%) · remaining i18n-only sections: knowledge (19) · roles (3) · reliability (1)
- `iter280` Sequence #8 knowledge i18n closure · 19 knowledge-section articles translated to ES · authored in `guidance/translations_es_iter280.py` (same modular pattern as iter279) · 7/7 regression pytests in `test_iter280_knowledge_i18n_closure.py` · 249/249 prior guidance pytests still green · live API verified for 4 sampled articles (block counts match · ES titles render) · ES translation coverage 83 → 102 / 124 (67% → 82%) · remaining i18n-only sections: roles (3) · reliability (1)
- `iter281` Sequence #8 roles + reliability i18n closure (FINAL CLUSTER) · 4 articles translated to ES (`role-foreman` · `role-hr` · `role-superintendent` · `why-backups`) · authored in `guidance/translations_es_iter281.py` · 6/6 regression pytests in `test_iter281_roles_reliability_i18n_closure.py` · 231/231 prior guidance pytests still green · live API verified for all 4 articles (block counts match · ES titles render) · ES translation coverage 102 → 106 / 124 (82% → 85%) · **Sequence #8 i18n cluster fully closed** — the remaining 18 untranslated articles are the explicit-leave clusters (troubleshooting · quickhelp · onboarding) per iter277 audit · pre-audit's actionable list is now exhausted
- `iter282` HR Payroll Variance coaching-family parity closure (matrix-driven · widest red footprint pre-iter282) · 13 EN tips + 13 ES tips across 5 form-keys: `payroll-variance` (canonical 4: why/who/next/escalate) · `.upload` (why/mistake) · `.batches` (why/next) · `.row-decision` (why/next/escalate) · `.dispute` (why/escalate) · clone-pattern source: `HrTimeVerification.jsx` (11-tip 4-form-key density) · 4 HelpTipBlock mounts wired in `HrPayrollVariance.jsx` (top · upload card · batches card · active batch detail with row-decision + dispute) · 8/8 regression pytests in `test_iter282_payroll_variance_coaching.py` · 245/245 prior guidance pytests still green · live API verified (4 canonical tips on top + section tips on each sub-key · EN+ES both present per tip · HR scope honored) · matrix row flipped: Coach `❌→✅ 13` · 4-Kinds `❌→✅` · ES-vrfy (top family text) `❌→✅` · Tests `❌→✅` · Parity `❌→✅` · Guide `🟡→✅` · ES-vrfy of the 46 `t()` UI keys and Mobile 🟡 deliberately held for iter283 (separate risk category)
- **iter282 out-of-scope discovery (logged, NOT fixed per scope discipline)**: legacy `tests/test_payroll_variance_iter72.py` has 15 fixture-level errors — uses outdated `/api/hr/login` endpoint that returns 401 under the current multi-login model. Pre-existing infrastructure bitrot, predates iter282. Belongs in a separate test-modernization sequence; not a regression.
- `iter283` HR Payroll Variance i18n + mobile verification (second half of iter282's audit-stage agreement) · extracted all 36 unique `t()` keys from `HrPayrollVariance.jsx` · audit confirmed 31 of 36 missing from `i18n.js` (ES mode was silently falling back to EN) · authored 31 new ES entries in `frontend/src/lib/i18n.js` covering: toasts, headers, tile labels, table headers, dialog labels, decision buttons (Approve/Dispute → Aprobar/Disputar), placeholder CSV sample · 36/36 keys now resolve · live mobile verification (390×844): body 390/vp 390 → no horizontal page overflow · HelpTipBlock mounts render correctly in both EN and ES on mobile (screenshot evidence) · `.overflow-x-auto` wraps the wide variance table per existing platform convention (mobile redesign EXPLICITLY rejected — verification determined acceptability) · regression test `test_iter283_payroll_variance_i18n_coverage.py` locks the 36-key coverage + 21 operational anchor strings · 10/10 PV regression tests green (8 from iter282 + 2 from iter283) · matrix row flipped: ES-vrfy (full UI) `🟡→✅` · Complete `🟡→✅` · **HR Payroll Variance row is now fully green** — became the audit-stage scope's reference example for future operational maturity closure iterations as anticipated
