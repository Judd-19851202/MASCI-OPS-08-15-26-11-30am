# Workflow Friction Report (Phase 5B)

**Date:** 2026-05-24
**Method:** Static code survey + cross-reference against
FINAL_OPERATIONAL_COMMUNICATION_VERIFICATION.md.
**Priority:** CRITICAL > HIGH > MEDIUM > LOW · `🔴 🟠 🟡 🟢`.
**Rule:** Every item below is a friction observation, NOT a fix plan.
Recommendations live in `WORKFLOW_SIMPLIFICATION_RECOMMENDATIONS.md`.

---

## 🔴 CRITICAL — adoption blockers if unaddressed

### C1 · Daily Report submission is too heavy
**Surface:** `/app/frontend/src/pages/NewDailyReport.jsx` (1,524 LOC, ~35 inputs, 7 sections).
**Friction:**
- Supervisors submit this **daily** — every extra click compounds across hundreds of users.
- 7 sections mean horizontal/vertical scrolling on phones.
- Fields like "weather_snapshots", "materials", "visitors" are needed sometimes but always present, adding cognitive load.
- No visible "save as draft" indicator → fear of losing progress mid-shift.
**Field reality:**
- A super at 4:55pm Friday in 95°F sun cannot tolerate a 5-minute form.
- Expect supervisors to start delegating this or skipping detail.
**Effect:** Reduces data quality. Erodes trust in "the platform tracks what we do."

### C2 · Incident report has 54 fields in one page
**Surface:** `/app/frontend/src/pages/NewIncident.jsx` (1,088 LOC).
**Friction:**
- OSHA-grade fields (root cause, contributing factors, body part, treatment, etc.) are mandatory-feeling even when not legally required.
- No progressive disclosure — supervisors see all 54 fields at once.
- Incident reporting is **stress-driven** (something bad just happened). Heavy forms compound stress.
**Field reality:**
- Supervisors will either underreport (skip fields → poor data) or over-narrate in `description` and skip structure entirely.
**Effect:** Hurts OSHA compliance over time. Hurts incident root-cause data quality.

---

## 🟠 HIGH — adoption amplifiers

### H1 · QA/QC forms likely carry the same heavy-form pattern
**Surface:** `/app/frontend/src/pages/NewQaqcInspection.jsx`, `/app/frontend/src/pages/QaqcSection.jsx` (sizes not measured in this pass).
**Friction:** QA/QC inspections are field-conducted by foremen/supers. Same constraints as DR/Incident apply.
**Recommendation:** measure LOC + input count; if comparable to NewDailyReport, treat as a third critical.

### H2 · Mobile breakpoint inconsistency across pages
**Surface:** only `NewDailyReport.jsx` and `NewIncident.jsx` carry explicit `md:hidden`/`sm:hidden` directives. Other pages rely on Tailwind defaults.
**Friction:**
- Sidebar/admin panels (`AdminShell`, `AdminJobMasterPanel`, `AdminPMPanel`) likely require horizontal scroll on phones.
- The new Phase 5 P1 W3/W5/W8 endpoints don't have UI yet — but when added, the same risk applies.
**Field reality:** Supers and FL leads use phones. Admins use desktops. Today's UI mostly assumes desktop.

### H3 · Toolbox-talk (safety meeting) entry friction
**Surface:** Safety meeting form (size not measured).
**Friction:** Operators host toolbox talks **once per day per crew**. Sign-in capture is the most-clicked step. If signature capture requires multiple modals or page reloads, adoption drops.
**Recommendation:** confirm signature-capture is single-step (one finger draw → save).

### H4 · Notification overload risk
**Surface:** `/api/notifications` accepts any portal token. Every form submission fires a notification fan-out.
**Friction risk:** If the digest contains 20+ items per role per day, operators will stop reading it.
**Currently:** unmeasured. No data on per-role daily notification volume.
**Recommendation:** instrument a single-week sample of notification counts per role; flag any role above ~10 / day for digest grouping.

---

## 🟡 MEDIUM — polish items

### M1 · Daily Report "section headers" inside the form
**Friction:** Tab/section navigation inside the form is not visible at a glance. Supers may jump to wrong section.
**Code signal:** 7 `<section>` blocks in NewDailyReport.jsx; no obvious section-jump navigation observed.

### M2 · Field jargon may not match field language
**Friction:** Terms like "OSHA recordable", "root cause", "contributing factors" are correct legally but unfamiliar to foremen. Field language audit would surface lower-friction wording.

### M3 · Confirmation fatigue (admin destructive actions)
**Surface:** `AdminPasswordConfirm` modal fires on backup-delete, restore, re-seed.
**Friction:** Appropriate for destructive admin work. NOT appropriate if it spreads to non-destructive flows.
**Currently:** scoped correctly (only destructive); LEAVE AS-IS.

### M4 · Inconsistent "Save" semantics
**Friction:** Some forms have one Save button (Daily Report); others have multiple (Save Draft / Submit / Submit + Print). Inconsistency between forms = cognitive load.

### M5 · LifecycleGuide content quality (not breadth — content)
**Surface:** `/app/frontend/src/components/LifecycleGuide.jsx` infrastructure is good.
**Friction risk:** if the per-page sections become "walls of text", supers will dismiss permanently.
**Currently:** sections are short. LEAVE AS-IS but monitor.

### M6 · Empty-state copy quality
**Friction risk:** Lists with zero items may show "No items" instead of "Submit your first daily report — takes 2 minutes". Empty-state design materially affects new-user confidence.
**Currently:** unmeasured.

---

## 🟢 LOW — cosmetic / future-watch

### L1 · Color/contrast in sunlight conditions
**Currently:** unmeasured. Tailwind defaults are fine; the platform doesn't use exotic palettes.

### L2 · Accessibility (screen readers, font size)
**Currently:** unmeasured. Heavy lift to retrofit; defer until/unless a specific user need surfaces.

### L3 · Long lists without pagination
**Surface:** some admin lists limit to 1000 records. Operationally fine today (one-company scale). Future-watch only.

### L4 · Print stylesheets
**Currently:** PDF exports exist for accountability brief, ops manual, training packets. Direct browser print is unstyled. Low priority — operators use the PDF flow.

---

## Cross-cutting observations

### Strong patterns to PRESERVE
- **Portal isolation**: each portal sees its scoped data. No cross-portal leakage.
- **Auto-email fan-out**: invisible, reliable, fire-and-forget.
- **Idempotent submission** (incidents): re-POST with same Idempotency-Key returns cached response. Critical for spotty LTE.
- **Backend gates fail closed**: anon → 401, wrong portal → 401. Verified in W1–W8 audits.

### Anti-patterns NOT detected (good)
- No multi-step wizards
- No config sprawl
- No menu nesting >2 deep
- No marketing copy in empty states
- No "advanced settings" tabs

---

## Friction priority summary

| Priority | Count | Where |
|---|---|---|
| 🔴 CRITICAL | 2 | DR entry · Incident entry |
| 🟠 HIGH | 4 | QA/QC weight · mobile consistency · toolbox-talk signature · notification overload risk |
| 🟡 MEDIUM | 6 | Section nav · field jargon · save semantics · etc. |
| 🟢 LOW | 4 | Sunlight contrast · a11y · pagination · print css |

**Total observations:** 16
**Adoption-blockers requiring action before scaling adoption:** 2 (C1, C2)
**Items requiring field validation before any fix:** all of CRITICAL + HIGH

**Companion:** see `WORKFLOW_SIMPLIFICATION_RECOMMENDATIONS.md` for the
ranked **subtractive** action list.
