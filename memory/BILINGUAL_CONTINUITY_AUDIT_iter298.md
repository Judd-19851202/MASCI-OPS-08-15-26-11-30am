# Bilingual Continuity Audit · iter298 (Lane A · visibility-only)

**Date:** 2026-05-20
**Phase:** Operational stabilization · post-iter297
**Discipline:** read-only audit · NO code changes from this deliverable · classifications only · all closures await operator approval

---

## 0 · Method

Read-only sweep of the 8 named operational surfaces against three concrete failure modes:

1. **Hardcoded EN survivors** — JSX text or attributes (`placeholder` · `title` · `alt`) rendering English literally with no `t()` wrapper.
2. **Broken `t()` paths** — `t("English Key")` calls where the matching entry is **missing from the ES dictionary** in `/app/frontend/src/lib/i18n.js`, silently falling back to the EN key in Spanish locale.
3. **Inline `lang === "es" ? ... : ...` ternaries** — i18n-pattern drift (some are legitimate data-side bilingual lookups, others are anti-patterns).

**Stat baselines:**
- i18n.js ES dictionary: **2,310 keys**.
- Total `t()` call sites scanned across the 8 named surfaces: **~1,240 strict-pattern calls**.
- 13 of those surfaces have at least one unresolved key.

---

## 1 · Headline finding

**Spanish-locale silent EN fallback is the single largest bilingual integrity gap on the platform.**

Across 13 named surfaces, **165 unique `t("...")` calls resolve to EN in Spanish locale** because the matching ES key was never authored. The `t()` wrapper exists. The wiring is in place. The translation is just missing.

This is structurally different from "untranslated screens" — these surfaces *look* translated (search box, headers, action chrome work fine), but specific sentences fall back silently. A Spanish operator sees mixed-language UI without realizing some text could be translated.

| Severity tier | Count | Operational meaning |
| --- | ---: | --- |
| 🔴 **Leak** | 137 | Spanish user actually sees this string in EN |
| 🟡 **Awkward** | 23 | Tooltip / alt text / placeholder · low surface |
| 🟢 **Acceptable** | (others) | Intentional bilingual JSX · pre-translated data-side ternaries |

---

## 2 · Per-surface findings

### 2.1 🔴 Fleet / DVIR — **CLEAN**
- `FleetVisibility.jsx` (657 LOC) · `NewFleetDVIR.jsx` (852 LOC) · `FleetDVIRConfirmation.jsx` (249 LOC).
- Zero hardcoded EN text. Zero broken `t()` keys. Zero ternary anti-patterns.
- **Verdict:** ✅ confirmed clean post-iter295. No action needed.

### 2.2 🟢 Guidance Center — **CLEAN (post-iter296)**
- `OperationalGuidanceCenter.jsx` (853 LOC).
- Only "hits" are the intentional bilingual hero block (`lang === "es" ? <ES JSX> : <EN JSX>`) — that's design intent, not drift.
- Two technical "broken keys" (`/guidance/sections` · `/guidance/articles?section=portals`) are **false positives** — these are URL strings inside `api.get()` calls, not `t()` calls. Regex artifact.
- **Verdict:** ✅ clean. iter296 closed the real gap.

### 2.3 🔴 Toolbox / Safety Meetings — **MIXED**
| File | Findings | Severity |
| --- | --- | --- |
| `MeetingsDashboard.jsx` (184 LOC) | **No `useT()` import.** Hardcoded EN: "New Meeting" · "Recent Meetings" · `title="Share Meeting Form"` | 🔴 **Leak** — Toolbox dashboard is the meetings landing surface for foremen |
| `NewMeeting.jsx` (859 LOC) | 2 ternaries — both are pre-translated data lookups (`TOPIC_LIBRARY_ES[key]` / `w.es vs w.en`) | 🟢 **Acceptable** — data-side bilingual |
| `ViewMeeting.jsx` (419 LOC) | `alt="Conductor signature"` | 🟡 **Awkward** — accessibility alt text |
| `SafetyTopicLibrary.jsx` (562 LOC) | 5 ternaries (all data-side: `chip.es / chip.en` · `sev.es / sev.en` · `d.es / d.en`) + **21 unresolved `t()` keys** | 🟢 ternaries acceptable · 🔴 21 keys leak |

**Specific leaks (sample, MeetingsDashboard + SafetyTopicLibrary):**
- `'New Meeting'` · `'Recent Meetings'` · `title="Share Meeting Form"` (MeetingsDashboard — entire file lacks `useT()`)
- `'Generate PDF Pack'` · `'Search by title (EN or ES)…'` · `'English only'` · `'Spanish only'` · `'Both languages (EN page · ES page · per topic)'` · `'No topics match the current filters.'` · `'Clear selection'` · `'Select all visible'` · `'Generating…'` · `'PDF generation failed: '` · `'Select at least one topic before generating a pack.'` · `'Topic Library · MASCI Safety'` (SafetyTopicLibrary)

### 2.4 🟡 Dispatch — **MOSTLY INTENTIONAL EN-FIRST**
| File | Findings | Severity |
| --- | --- | --- |
| `DispatchHub.jsx` (161 LOC) | No `useT()`. "Sign out" hardcoded. `title="Public Hub"` | 🟡 **Awkward** — Dispatch is intentionally EN-first per matrix footnote ⁱⁱⁱ, but "Sign out" is universal chrome that arguably should still translate |
| `DispatchLogin.jsx` (179 LOC) | Clean | ✅ |
| `admin/AdminDispatch.jsx` (772 LOC) | No `useT()`. 7 hardcoded text strings + 4 placeholders (search inputs) | 🟢 **Acceptable** per matrix footnote ⁱⁱⁱ — intentionally EN-only office-internal surface |

**Verdict:** Dispatch matches its documented matrix classification. The one cosmetic question is whether `DispatchHub.jsx` chrome ("Sign out") should translate even on intentional EN-first portals. **Defer to operator.**

### 2.5 🔴 Safety — **HIGHEST LEAK CONCENTRATION**
This is the highest-impact cluster in the entire audit.

| File | Hardcoded attrs | Broken `t()` keys | Severity |
| --- | ---: | ---: | --- |
| `SafetyHub.jsx` (262 LOC) | 1 (`title=`) | **44** | 🔴 **Leak (Safety landing)** |
| `SafetyCorrectiveActions.jsx` (688 LOC) | 2 (titles) | **36** | 🔴 **Leak** |
| `SafetyTopicLibrary.jsx` (562 LOC) | 0 | 21 | 🔴 (counted in §2.3) |
| `SafetyTrainingRecords.jsx` (393 LOC) | 1 (placeholder) | **17** | 🔴 **Leak** |
| `SafetyFireExtinguishers.jsx` (490 LOC) | 1 (placeholder) | **13** | 🔴 **Leak** — recent iter293 closure missed dialog-internal strings |
| `SafetyDocuments.jsx` (254 LOC) | 1 (placeholder) | **10** | 🔴 **Leak** |
| `SafetyIncidents.jsx` (183 LOC) | 0 | 8 | 🔴 **Leak** |
| `NewIncident.jsx` (1,094 LOC) | **18** (placeholders) | 2 | 🔴 **Leak (high-traffic, bilingual witnesses)** |
| `ViewIncident.jsx` (506 LOC) | 2 (titles) | 0 | 🟡 |
| `NewInspection.jsx` (693 LOC) | **13** (placeholders) | 1 | 🔴 **Leak (foreman bilingual surface)** |
| `ViewInspection.jsx` (504 LOC) | 2 (titles) | 0 | 🟡 |
| `SafetyAudits.jsx` (187 LOC) | 0 | 0 | ✅ Clean |

**Highest-impact specific leaks:**

**SafetyHub.jsx (44 unresolved):** entire portal-landing dashboard chrome is t()-wrapped but missing from ES dict — `'Audits & Inspections'` · `'Awaiting close-out'` · `'CA · Open'` · `'CA · Overdue'` · `'Change Password'` · `'Could not load metrics. Sign out and back in.'` · `'Cross-portal accountability engine...'` · `'Employee Safety Profiles'` · `'Equipment Accountability'` · `'Incidents (Total)'` · `'Last 30 days'` · `'Last 7 days'` · `'Loading metrics…'` · etc. (38 more).

**NewIncident.jsx placeholders (18):** Spanish-speaking witnesses/foremen filling out incidents see EN placeholders:
- `'Specific location on site (station, lane, structure...)'`
- `'Your name'`
- `'Search by name / email / employee ID'`
- `'Select body part...'`
- `'First aid given, EMS called, transported by...'`
- `'Clinic / hospital, if applicable'`
- `'What was the unsafe act or condition that triggered the event?'`
- `'Weather, fatigue, training, equipment condition, schedule pressure...'`
- `'What they saw, in their words.'`
- `'What was done immediately to make the area safe?'`
- `'Training, procedure changes, engineering controls...'`
- `'Who owns the follow-up?'`
- `'Insurance, EAP, family...'`
- + 5 more (employee/equipment search placeholders, role/employer fields)

**NewInspection.jsx placeholders (13):** Same pattern — foreman bilingual surface:
- `'Address, intersection, station, or GPS'`
- `'Type or pick inspector'`
- `'Type or pick foreman / supervisor'`
- `'List crew members or crew lead'`
- `'Company / activity / manpower'`
- `'Sunny 78°F, light wind…'`
- `'Earthwork, pipe, paving, concrete, MOT setup, etc.'`
- `'Optional notes for this section'`
- `'Describe issue, location, immediate action taken, and follow-up required.'`
- + 4 more

### 2.6 🔴 Daily Reports — **TWO REAL LEAKS**
| File | Findings | Severity |
| --- | --- | --- |
| `NewDailyReport.jsx` (1,464 LOC) | 1 placeholder `'Earthwork, Concrete, MOT...'` + 4 unresolved `t()` keys (`'This report has'` · `'photo(s) attached (≈'` · `' estimated).'` · the size-warning sentence) | 🔴 **Leak** — size-warning composite string visible to Spanish foremen on large reports |
| `ViewDailyReport.jsx` (666 LOC) | 3 attrs: `title="Sign-Off"` + 2 signature `alt=""` | 🟡 **Awkward** |
| `DailyReportsDashboard.jsx` (229 LOC) | 2 attrs (technical) | 🟢 |

### 2.7 🔴 Corrective Actions — **HIGH LEAK COUNT**
- `SafetyCorrectiveActions.jsx` (688 LOC): **36 unresolved `t()` keys** + 2 title-attr.
- Visible leaks: `'New Corrective Action'` · `'Edit corrective action'` · `'Filter by linked employee/equipment'` · `'Linked employee'` · `'Linked equipment'` · `'Assigned to (name)'` · `'Assigned to (email)'` · `'Due date'` · `'Completion notes'` · `'Employee acknowledgment'` · `'Any employee'` · `'Any equipment'` · `'Filter by title, project, assignee, description…'` · etc.
- 🔴 **Leak** — Safety Coordinator opens this surface daily.

### 2.8 🟡 Onboarding / Help — **SCATTERED**
| File | Findings | Severity |
| --- | --- | --- |
| `Hub.jsx` (588 LOC) | 1 attr (long English tooltip on multi-portal sign-in) + 1 intentional bilingual JSX ternary | 🟡 attr awkward · 🟢 ternary acceptable |
| `SignIn.jsx`, `SafetyFormsLogin.jsx`, `SafetyFormsHub.jsx`, `FieldLeadershipHub.jsx` | Clean | ✅ |
| `ShopHub.jsx` (407 LOC) | 1 attr + 4 unresolved `t()` keys (`'Change password'` · `'Fleet Repair Queue · grouped by truck'` · `'Guides'` · `'Integrations'`) | 🔴 small Leak |
| `HrHub.jsx` (194 LOC) | 1 attr + 4 unresolved `t()` keys (`'Driver Safety Events (HR Review)'` · `'Employee Records & Accountability'` · `'OPEN →'` · `'Read-only HR access · ...'`) | 🔴 small Leak |
| `PmHub.jsx` (148 LOC) | **No `useT()`.** 1 attr `title="Overview"` | 🟡 entire surface EN-only · low operational impact (PM users are office-side and bilingual) |
| `FieldLeadershipHub.jsx` (418 LOC) | 1 unresolved `'Guides'` | 🟡 minor |

---

## 3 · Severity rollup

| Severity | Count | Recommended posture |
| ---: | ---: | --- |
| 🔴 **Leak** (real Spanish user impact) | **137** key/string sites across **9 surfaces** | Bounded closure work warranted, but DEFERRED to operator approval. Cluster by surface for bounded micro-closes. |
| 🟡 **Awkward** (low-surface · accessibility · intentional EN-first edge cases) | **23** sites | Mostly acceptable as-is. Only fix when revisiting the surface for other work. |
| 🟢 **Acceptable** (intentional bilingual JSX · data-side ternaries · matrix-classified EN-first) | (~30 ternary hits + AdminDispatch's 11 EN strings) | NO action. Documented governance. |

---

## 4 · Terminology consistency findings

Sampled the 165 unresolved keys for terminology drift against canonical vocabulary:

- ✅ "Daily Report" / "Reporte Diario" — consistent
- ✅ "Corrective Action" / "Acción Correctiva" — consistent (when translated)
- ✅ "Incident" / "Incidente" — consistent
- ⚠ "Safety Meeting" vs "Toolbox Talk" — **no Toolbox survivors** in the 13 surfaces sampled (iter278 closure intact)
- ✅ "Fire Extinguisher" / "Extintor" — consistent
- ⚠ **"Sign out"** appears un-translated on `DispatchHub.jsx` — minor chrome drift; rest of platform uses "Cerrar sesión"
- ⚠ "Open" → "OPEN →" (HrHub.jsx) — formatting+text not translated; rest of platform uses "Abrir"

No content-side machine-translation awkwardness detected. The Spanish translations in the existing 2,310-key dictionary read as written-by-an-operator, not machine-generated.

---

## 5 · Operational impact assessment

**Who's hit hardest by the 137 leaks?**

1. **Safety Coordinator (Spanish-speaking)** — `SafetyHub.jsx` landing (44 leaks) is the daily entry surface. Reading "Audits & Inspections" / "CA · Open" / "Awaiting close-out" in English while the rest of the platform is Spanish breaks operational trust.
2. **Spanish-speaking foreman filing an incident** — 18 EN placeholders in `NewIncident.jsx` while typing. The labels above the placeholders translate; the prompts inside the boxes don't. Confusing for high-stress incident filing.
3. **Spanish-speaking foreman running a site inspection** — same pattern on `NewInspection.jsx` (13 placeholders).
4. **Spanish-speaking safety officer reviewing CA queue** — 36 leaks on the CA list/filter/dialog chrome.

**Who's not impacted?**
- Dispatch and Admin Console users — intentionally EN-first per matrix governance.
- Fleet/DVIR users — surfaces already fully translated (iter295).
- Guidance Center readers — surfaces already fully translated (iter296+iter297).
- HR Payroll Variance users — fully translated (iter282/iter283).

---

## 6 · Proposed bounded closures (DEFERRED to operator approval)

Listed by operational impact, NOT by file size. Each is independently shippable. **None of these are recommended for autonomous execution — the audit's job ends here.**

| # | Scope | Severity | Footprint | Risk |
| --- | --- | :-: | --- | :-: |
| A | `SafetyHub.jsx` ES dict population (44 keys) | 🔴 | i18n.js only | TRIVIAL |
| B | `SafetyCorrectiveActions.jsx` ES dict (36 keys) | 🔴 | i18n.js only | TRIVIAL |
| C | `SafetyTopicLibrary.jsx` ES dict (21 keys, but 8 are dialog chrome) | 🔴 | i18n.js only | TRIVIAL |
| D | `SafetyTrainingRecords.jsx` + `SafetyDocuments.jsx` + `SafetyFireExtinguishers.jsx` ES dict (~40 keys) | 🔴 | i18n.js only | TRIVIAL |
| E | `NewIncident.jsx` placeholder t()-wrap pass (18 attrs) + ES dict | 🔴 | JSX + i18n.js | LOW |
| F | `NewInspection.jsx` placeholder t()-wrap pass (13 attrs) + ES dict | 🔴 | JSX + i18n.js | LOW |
| G | `SafetyIncidents.jsx` ES dict (8 keys) | 🔴 | i18n.js only | TRIVIAL |
| H | `MeetingsDashboard.jsx` `useT()` install + small ES dict (2 keys) | 🔴 | JSX + i18n.js | LOW |
| I | `HrHub.jsx` + `ShopHub.jsx` ES dict (8 keys) + `FieldLeadershipHub.jsx` (1 key) | 🟡 | i18n.js only | TRIVIAL |
| J | `NewDailyReport.jsx` size-warning composite (4 keys + 1 placeholder) | 🔴 | JSX + i18n.js | TRIVIAL |
| Z | `DispatchHub.jsx` "Sign out" + `PmHub.jsx` `useT()` install | 🟡 | optional · matches stated EN-first intent | LOW |

**Recommended order if operator approves any:**
1. **First:** A + B + C + D + G + I + J — all are pure i18n.js dictionary additions, zero JSX changes, single regression test per cluster, can be bundled into ONE iteration (iter299 candidate).
2. **Second:** E + F — placeholder `t()` wrapping passes on the high-traffic incident/inspection forms. Single JSX file edit each plus dict adds. (iter300/301 candidates.)
3. **Third:** H + Z — small structural additions.

Total work envelope: **~160 ES dictionary entries** + **~31 placeholder `t()` wraps across 2 JSX files**. All low-risk · all mechanical · all parallel-safe with `mcp_search_replace`.

---

## 7 · What the audit explicitly does NOT recommend

Per operator phase-shift discipline, this audit does **NOT** propose:

- 🚫 Re-translating any already-translated string ("our Spanish is fine — the gap is missing entries, not bad entries").
- 🚫 Restructuring i18n.js (current dictionary-of-strings is operationally simple — splitting by surface adds bureaucracy without operational value).
- 🚫 Adding lint rules / CI checks for `t()` coverage (would be useful but the user already deferred F2 in PRD until post-stabilization).
- 🚫 Auto-translation pipelines (would compromise operational tone discipline).
- 🚫 Touching AdminDispatch / Admin Console / Backup-Restore EN strings (intentional EN-first per matrix footnote ⁱⁱⁱ).
- 🚫 Manufacturing a "complete bilingual coverage 100%" goal (existing 91% article coverage + 2,310 ES UI keys is operationally sufficient; the gap is *targeted* leaks, not coverage gaps).

---

## 8 · Confidence level

- **High** for the 137 🔴 Leak count — derived from strict regex against the live ES dict.
- **High** for the surface-by-surface attribution — every count is reproducible by re-running the audit script.
- **Medium** for the operational-impact ordering — based on usage-frequency assumptions (SafetyHub > NewIncident > CA, etc.); the real ordering depends on which roles speak Spanish in your actual user population.

This audit is the **gate** for any iter299+ bilingual closure work. No surface should be touched without referencing back to its row above. The closure work, if approved, is mechanical and parallel-safe; the audit was the hard part.
