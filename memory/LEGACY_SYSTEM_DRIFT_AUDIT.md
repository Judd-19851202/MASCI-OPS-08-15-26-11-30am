# LEGACY_SYSTEM_DRIFT_AUDIT.md
**Phase 19 · iter415 · 2026-05-25**

Drift analysis from oldest to newest systems. Drift means: visual rhythm · coaching pattern · vocabulary · translation coverage · LifecycleGuide usage · card chrome.

## Timeline of platform doctrine waves
| Wave | Doctrine introduced |
|---|---|
| **Pre-iter100** (oldest) | Functional forms; minimal coaching; legacy `bg-white p-4 border` chrome |
| **iter100-iter250** | Per-portal authentication; per-user accounts; scope discipline |
| **iter250-iter319** | Operational vocabulary scanner born (iter398); bilingual i18n.js; LifecycleGuide component pattern |
| **iter319-iter392** | LifecycleGuide-pattern coaching adoption; Field Tile + Field Leadership convergence |
| **iter392-iter410** | Dispatch Lifecycle System; 5 haul types; calm Issue Work drawer; restraint scanner enforcement |
| **iter411-iter414** | Dispatch Command IA; health summary; full audit doctrine; 25-point gates; in-flow coaching |

## Per-module drift matrix
| Module | Last modernized | Chrome | Coaching | i18n | LifecycleGuide | Verdict |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Dispatch Hub** | iter411 | ✅ | ✅ | ✅ | ✅ | 🟢 Current |
| **Dispatch Board** | iter392-iter407 | ✅ | ✅ | ✅ | ✅ | 🟢 Current |
| **Assignment Drawer** | iter408+410 | ✅ | ✅ | ✅ | ✅ | 🟢 Current |
| **PM Hub + PM Haul Activity** | iter409 | ✅ | ✅ | ✅ | ✅ | 🟢 Current |
| **Shop Hub + iter396 tile** | iter396 | ✅ | ✅ | ✅ | ✅ | 🟢 Current |
| **Field Tile (`/field`)** | iter403-404 | ✅ | ✅ | ✅ | ✅ | 🟢 Current |
| **FL Portal (per-user)** | iter314+317+319 | ✅ | ✅ | ✅ | ✅ | 🟢 Current |
| **HR Driver Qualification** | iter317+352+353 | ✅ | ✅ | ✅ | ✅ | 🟢 Current |
| **Safety Topic Library** | iter301 | ✅ | ✅ | ✅ | 🟡 | 🟢 Current |
| **Safety Meeting Builder** | iter265-270 | 🟡 | 🟡 | 🟡 | ⚠️ | 🟡 Pre-LifecycleGuide |
| **Safety Documents** | iter120 | 🟡 | 🟡 | 🟡 | ⚠️ | 🟡 Pre-LifecycleGuide |
| **Safety Fire Extinguishers** | iter120 | 🟡 | 🟡 | 🟡 | ⚠️ | 🟡 Pre-LifecycleGuide |
| **Safety Employee Profile** | iter353 | ✅ | ✅ | ✅ | ✅ | 🟢 Current |
| **HR Employee Accountability** | iter353a | ✅ | 🟡 | 🟡 | ✅ | 🟢 Current |
| **HR Time Verification** | pre-iter319 | 🟡 | ⚠️ | 🟡 | ⚠️ | 🟡 Legacy |
| **HR Training Records** | pre-iter319 | 🟡 | ⚠️ | 🟡 | ⚠️ | 🟡 Legacy |
| **HR Payroll Variance** | iter353a | ✅ | 🟡 | 🟡 | ⚠️ | 🟡 Mixed |
| **Inspections (`NewInspection.jsx`)** | pre-iter250 | 🟡 | ⚠️ | 🟡 | ⚠️ | 🟡 Legacy |
| **Daily Report Builder** | pre-iter250 | 🟡 | ⚠️ | 🟡 | ⚠️ | 🟡 Legacy |
| **Equipment Pre-Op** | pre-iter250 | 🟡 | ⚠️ | 🟡 | ⚠️ | 🟡 Legacy |
| **DVIR · Weekly Lead · Weekly Emergency** | pre-iter250 | 🟡 | ⚠️ | 🟡 | ⚠️ | 🟡 Legacy |
| **Incidents (`NewIncident.jsx`)** | pre-iter250 | 🟡 | ⚠️ | 🟡 | ⚠️ | 🟡 Legacy |
| **JHA Plans Admin/Hub/Poster** | pre-iter250 | 🟡 | ⚠️ | 🟡 | ⚠️ | 🟡 Legacy |
| **Meetings Dashboard** | pre-iter250 | 🟡 | ⚠️ | 🟡 | ⚠️ | 🟡 Legacy |
| **Field Safety Cards** | iter333-334 | ✅ | ✅ | ✅ | 🟡 | 🟢 Current |
| **Admin Console + Backups** | iter83-84 | 🟡 | 🟡 | n/a (admin) | n/a | 🟡 Functional but pre-Phase-12 |
| **Admin People/Access Control** | iter349 | ✅ | ✅ | n/a (admin) | n/a | 🟢 Current |
| **Field Leadership (legacy shared `/leadership`)** | iter46-127 | 🟡 | 🟡 | 🟡 | ⚠️ | 🟡 Pre-LifecycleGuide |
| **Safety Forms (Equipment Issuance + Training)** | iter55-iter323 | 🟡 | 🟡 | 🟢 | 🟡 | 🟡 Mixed |
| **Asset Transfers** | iter319+ refresh | ✅ | ✅ | ✅ | ✅ | 🟢 Current |
| **PO Requests** | iter97+ | 🟡 | ⚠️ | 🟡 | ⚠️ | 🟡 Legacy |

## Drift patterns (catalogued · NOT executed)
### Pattern 1 · Pre-card-rhythm chrome
- **Old**: `bg-white p-4 border border-slate-200 rounded` (functional, but flat).
- **New (Phase 12+ standard)**: `bg-white rounded-2xl border border-slate-200 p-5 sm:p-6` + colored top-stripe + section icon.
- **Affected**: Daily Report · Inspections · Incidents · Meetings · JHA · HR Time/Training/Payroll · Safety Documents/Fire Ext · `/leadership` shared.
- **Grep evidence**: 0 hits of legacy chrome literal in `pages/` — drift is not in `bg-white p-4` strings but in section/card composition.

### Pattern 2 · Pre-LifecycleGuide coaching
- **Old**: Header `<h1>` + paragraph subtitle. No "Why · Signal · Next" structure.
- **New**: 4-section `LifecycleGuide` component with explicit What/Why/Signal/Next.
- **Affected**: Same module list as Pattern 1.

### Pattern 3 · Translation coverage gaps in validation
- **Old**: Required-field error messages in English regardless of `masci.lang`.
- **New (iter319+)**: Wrapped in `useT()`.
- **Affected**: Daily Report · Inspections · Incidents · Equipment Pre-Op · DVIR · older Safety/HR forms.

### Pattern 4 · Form-density legacy
- **Old**: Compact label-input pairs · no `min-h-[48px]` tap-target spacing.
- **New (iter402+)**: SearchableSelect with 56px+ tap targets.
- **Affected**: Same module list as Pattern 1.

### Pattern 5 · Pre-vocabulary-scanner phrasing
- **Old**: Occasional ERP-flavored words ("manage", "track", "configure", "modules").
- **New (iter398+)**: Operational vocabulary scanner blocks T2/T3 hits.
- **Status**: Permanent guardrail running. **0 T2/T3 hits today** ✅. So this pattern is contained.

## Drift NOT present (verified clean)
- ❌ No old role-creep reintroduced (Safety leaking DLS, etc.) — grep clean
- ❌ No old write surfaces masquerading as read-only — verified
- ❌ No dashboard sprawl reintroduced — `OPERATIONAL_DOCTRINE_DRIFT_REPORT.md` confirms
- ❌ No hardcoded English-only labels in Phase 12-17 critical paths

## Why we are NOT modernizing in Phase 19
Restraint doctrine: **legacy modules are operationally correct.** They submit data correctly. They flow downstream correctly. They're just visually less polished than Phase 12+ surfaces.

The Day-1 debrief will tell us:
- Did anyone hesitate at Daily Report? → No fix.
- Did Spanish-preferring crew get stuck on Inspections validation? → P1 i18n sweep.
- Did Incidents form confuse a new FL? → P2 LifecycleGuide insertion.
- etc.

## Recommended modernization recipe (when triggered)
1. **Card rhythm**: `bg-white rounded-2xl border border-slate-200 p-5 sm:p-6` + colored top-stripe matching role family.
2. **Section header**: kicker (uppercase tracking · slate-500) + `<h1>` + 1-line subtitle.
3. **Coaching**: drop in a `LifecycleGuide` 4-section explainer.
4. **Comboboxes**: replace `<select>` → `SearchableSelect` from iter402.
5. **Bilingual**: wrap every string in `useT()` + add EN/ES keys.

Each module would be a ~150-300 LOC pickup. **Do not batch all at once** — pick the module Day-1 names.

## Verdict
**Legacy aesthetic drift acknowledged, scoped, and held.** Operations runs Day-1, files debrief, surgical pickup follows.
