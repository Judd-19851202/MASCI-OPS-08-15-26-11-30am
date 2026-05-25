# LEGACY_MODERNIZATION_MATRIX.md
**Phase 18 · iter414 · 2026-05-25**

## Verdict
**No modernization work executed in Phase 18 itself.** Matrix is captured to enable surgical pickup once the Day-1 debrief names which legacy modules cost real operational time.

## Per-module matrix
| Module | Path(s) | Doctrine align | Card rhythm | Coaching | Translation | LifecycleGuide | Mobile | Priority |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Daily Report Builder** | `pages/NewDailyReport.jsx` · `pages/DailyReportsDashboard.jsx` | ✅ correct flow | ⚠️ pre-card | ⚠️ paragraph | ⚠️ partial | ❌ absent | ✅ usable | 🟠 P2 |
| **Inspections (Pre-Op)** | `pages/EquipmentDashboard.jsx` + form pages | ✅ correct | ⚠️ form-density | ⚠️ minimal | ⚠️ partial | ❌ absent | ✅ usable | 🟠 P2 |
| **Incidents** | `pages/IncidentsDashboard.jsx` | ✅ correct | ⚠️ pre-card | ⚠️ minimal | ⚠️ partial | ❌ absent | ✅ usable | 🟠 P2 |
| **Safety detail pages** | `pages/safety/*` | ✅ doctrine-quiet on DLS | ⚠️ pre-Phase-12 | ⚠️ paragraph | ⚠️ partial | ❌ absent | ✅ usable | 🟠 P2 |
| **HR Qualification screens** | `pages/HrDriverQualificationDashboard.jsx` · `pages/HrDriverQualificationImport.jsx` | ✅ correct scope | ⚠️ table-style | ⚠️ minimal | ⚠️ partial | ❌ absent | ✅ usable | 🟠 P2 |
| **HR Employee Accountability** | `pages/HrEmployeeAccountability*.jsx` | ✅ correct | ⚠️ pre-card | ⚠️ minimal | ⚠️ partial | ❌ absent | ✅ usable | 🔵 P3 |
| **HR Time Verification** | `pages/HrTimeVerification.jsx` | ✅ correct | ⚠️ table-style | ⚠️ minimal | ⚠️ partial | ❌ absent | ✅ usable | 🔵 P3 |
| **HR Training Records** | `pages/HrTrainingRecords.jsx` | ✅ correct | ⚠️ table-style | ⚠️ minimal | ⚠️ partial | ❌ absent | ✅ usable | 🔵 P3 |
| **Meetings dashboard** | `pages/MeetingsDashboard.jsx` | ✅ correct | ⚠️ pre-card | ⚠️ minimal | ⚠️ partial | ❌ absent | ✅ usable | 🔵 P3 |
| **JHA Plans** | `pages/JhaPlansHub.jsx` · `JhaPlansAdmin.jsx` | ✅ correct | ⚠️ pre-card | ⚠️ minimal | ⚠️ partial | ❌ absent | ✅ usable | 🔵 P3 |
| **Field Safety Cards** | `pages/FieldSafetyCards.jsx` | ✅ correct | ⚠️ pre-card | ⚠️ minimal | ⚠️ partial | ❌ absent | ✅ usable | 🔵 P3 |
| **Asset Transfers (list)** | embedded in DispatchHub via iter411 | ✅ aligned | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| **Field Tile `/field`** | `pages/FieldSection.jsx` (iter403/404) | ✅ aligned | ✅ | ✅ | ✅ via iter319 + iter404 | n/a | ✅ | — |
| **Public Forms `/forms/*`** | iter392+ unaffected | ✅ aligned for DLS | ⚠️ legacy chrome | ⚠️ form-instructional | ⚠️ partial | ❌ absent | ✅ usable | 🔵 P3 |
| **Field Leadership pages** | `pages/leadership/*` | ✅ aligned via iter319 + iter396 | ✅ | ✅ | ✅ | ✅ via iter396 | ✅ | — |

## Visual drift patterns identified (catalogued, NOT fixed)
1. **Pre-card-rhythm chrome** — `bg-white p-4 border` without colored left-stripe convention (Phase 12+ standard: `bg-white rounded-2xl border border-slate-200 p-5 sm:p-6` + colored top-stripe or icon).
2. **Form-density legacy** — older forms use compact label-input pairs without the `min-h-[48px]` searchable-combobox pattern (iter408-era standard).
3. **Pre-LifecycleGuide coaching** — explanation lives in paragraph headers rather than the 4-section `LifecycleGuide` pattern.
4. **Translation-coverage gaps** — form validation messages and rare tooltips still English-only when `masci.lang=es`.

## Why we are NOT executing modernization in Phase 18
**Phase 17 directive (re-affirmed by Phase 18 doctrine):**
> "DO NOT fix everything immediately. FIRST find ALL gaps. THEN prioritize surgically based on REAL operational feedback."

> "Build from repeated hesitation · repeated confusion · repeated translation failures — NOT from imagination, brainstorming, or wishlist."

The Day-1 debrief (`/app/memory/DLS_DAY1_LIVE_OPS_DEBRIEF.md`) is the gating signal. Without it, modernization risks:
- Visual churn on modules operations is comfortable with
- Doctrine drift (touching legacy code without operational justification)
- Wasted effort on modules low-frequency users hit
- Restraint violation (we'd be panic-building)

## Recommended P2 modernization template (when ready)
For each module pulled into a future iter, apply this **5-step recipe**:
1. **Card rhythm**: convert `bg-white p-4 border` → `bg-white rounded-2xl border border-slate-200 p-5 sm:p-6` with a colored top stripe (slate · amber · rose · cyan to match role family).
2. **Section header**: replace `<h1>` only chrome with the Phase 12 pattern: kicker + h1 + 1-line subtitle.
3. **Coaching**: add a `LifecycleGuide`-pattern explainer (What · Why · Signal · What next · Who depends).
4. **Comboboxes**: replace `<select>` dropdowns with the iter402 `SearchableSelect` pattern where appropriate.
5. **Bilingual sweep**: wrap every string in `useT()` and add EN/ES keys to `i18n.js`.

## Backlog priority order
**P2** (operational-friction-likely if Day-1 names them):
- 🟠 Daily Report Builder
- 🟠 Inspections (Pre-Op)
- 🟠 Incidents
- 🟠 Safety detail pages
- 🟠 HR Driver Qualification screens

**P3** (low operational frequency · defer indefinitely):
- 🔵 HR Employee Accountability / Time Verification / Training
- 🔵 Meetings dashboard · JHA Plans · Field Safety Cards
- 🔵 Public Forms `/forms/*`

## Verdict
**Matrix locked. No code changes shipped this phase.** Operations runs Day-1, files debrief, surgical pickup follows.
