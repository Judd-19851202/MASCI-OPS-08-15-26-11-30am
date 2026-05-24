# Phase 5C · Workflow Compression Plan (Master)

**Date:** 2026-05-24
**Status (post Phase 5C.1 — Smart Operational Disclosure · 2026-05-24):**
✅ **Visible-but-collapsed pattern implemented on both target forms.**
The "hide everything behind one button" approach from Phase 5C Iter 1/3
was evolved into Smart Operational Disclosure per operator directive:
every optional section remains VISIBLE as a `CollapseCard` with an
operational status badge ("3 entered" / "Optional" / "Required" /
"No entries today"). Users always know what sections exist; only the
expanded form body collapses. Severity auto-expansion + lock on incident
Tier-2 preserved exactly.

**Mode:** EXECUTION COMPLETE for all Phase 5C iterations + Phase 5C.1 refinement.

---

## Phase 5C.1 execution log (2026-05-24)

### ✅ New primitive: `<CollapseCard>` (90 LOC)
File: `frontend/src/components/CollapseCard.jsx`
Single small UI helper. Props: `title`, `statusLabel`, `statusTone`
(slate/emerald/amber/rose), `defaultOpen`, `forceOpen`, `lockOpen`,
`testId`. Used 5× on Daily Report + 4× on Incident.

### ✅ Daily Report — 5 named CollapseCards
Replaced the single "Show all fields" button with 5 visible cards:
- Subcontractors on Site → "3 entered" / "No subs today"
- Site Visitors → "2 entered" / "No visitors today"
- Equipment Log → "1 entered" / "Optional"
- Material Deliveries → "4 entered" / "No deliveries today"
- Activity / Production Log → "2 entered" / "Optional"

Tone rules: emerald when entries present, slate when empty. All 35 + 7
schema fields preserved. Rich field configs (`supplier-combo`,
`employee-combo`, `ticket_photos`, `attachment_note`) intact.

### ✅ Incident — 4 named CollapseCards with severity lock
Replaced the single "Add follow-up" button with 4 visible cards for
sections 05–08:
- Root Cause Analysis · status reflects checkbox count
- Witnesses · status reflects array length / Recommended for serious
- Corrective Actions & Follow-Up · status reflects content / Required for serious
- Notifications Made · status reflects toggle count / "Platform notifies automatically on submit"

**Severity safety net preserved exactly:** when `severity ∈ {medical,
restricted, lost_time, fatality}`, all 4 cards auto-open (`forceOpen`)
and the toggle is locked (`lockOpen`). Rose banner displays:
*"Severity is Medical or higher — follow-up sections are open and
required before submit."*

For Near Miss / First Aid: cards collapsed by default, status badges
clearly communicate what each section is for.

### Trust + accountability preservation (verified)
- ✅ ZERO backend changes
- ✅ ZERO schema/field deletions
- ✅ `useDraftSync` autosave (DR) — untouched
- ✅ `idempotencyKeyRef` (both forms) — untouched
- ✅ Existing Safety Escalation conditional (DR) — untouched
- ✅ Existing `isInjury` conditional (Incident Section 03) — untouched
- ✅ Severity auto-expansion + lock (Incident) — preserved exactly
- ✅ All 11 root cause checkboxes still rendered when card open
- ✅ All distribution list / fan-out logic untouched
- ✅ ESLint on all 3 changed files: clean
- ✅ Frontend bundle 200 OK · no compile errors

---

## Phase 5C original execution log (kept for history · 2026-05-24)

### Iter 1 — Daily Report Tier-3 (superseded by 5C.1)
First implementation used a single "Show all fields" toggle. Replaced
by 5 named CollapseCards in Phase 5C.1 per operator directive (users
need to see what sections exist, not just that "more fields" exist).

### Iter 2 — Daily Report Tier-1 reorder
No code change needed. Original section order is already correct.

### Iter 3 — Incident tiered fast entry (superseded by 5C.1)
First implementation used a single "Add follow-up" toggle. Replaced
by 4 named CollapseCards with per-card status. Same severity safety
net preserved.

### Iter 4 — Incident Tier-2 follow-up via PATCH
Zero new code required. Existing `/api/incidents/{id}` PATCH path
supports follow-up enrichment from the incident detail page.

### Iter 5 — UX polish
Folded into 5C.1 implementation (mobile-friendly Tailwind classes baked
into `CollapseCard`).

---

## Targets and current state

**Targets:** `NewDailyReport.jsx` (1,524 LOC · ~35 inputs · 9 sections) and `NewIncident.jsx` (1,088 LOC · ~54 inputs · 9 sections).
**Hard constraint:** **No reduction in accountability, downstream visibility, lifecycle continuity, or compliance.** Compression is **visual & sequencing**, not data-model deletion.

**Companion docs:**
- `/app/memory/DAILY_REPORT_COMPRESSION_MAP.md` — field-by-field matrix
- `/app/memory/INCIDENT_FAST_ENTRY_STRATEGY.md` — tiered entry strategy
- `/app/memory/FIELD_FRICTION_MEASUREMENT.md` — taps/scroll/timing baseline + targets
- `/app/memory/OPERATIONAL_ADOPTION_PROTECTION_PLAN.md` — guardrails so compression doesn't break governance

---

## Headline strategy

**One sentence:** Stop showing every field at once. Show the operationally
critical fields first; progressively disclose the rest; preserve every
data field in the model.

**Hard rules:**
1. **No field is deleted from the data model.** Every field that exists today still exists after compression — it may just be **hidden behind a disclosure** or **defaulted**.
2. **No backend changes.** Endpoints, validation, lifecycle hooks, fan-out routing all remain identical.
3. **No new dashboards, no new portals, no new role types.** Compression only touches the two target pages.
4. **Reversible.** A "Show all fields" toggle is always available so power users can opt out of compression.
5. **Continuity-preserving.** Anything tied to governance, accountability, or downstream visibility stays in Tier 1 (always-visible).

---

## What we already have (do NOT rebuild)

Discovered during audit — these are **already implemented** and must be preserved:
- ✅ **`useDraftSync` hook** on Daily Report (Phase J · iter unknown). Autosaves drafts, recovers on remount, toast offers Discard. This means S5 from Phase 5B is **already done** — we don't need to add save-as-draft.
- ✅ **`idempotencyKeyRef`** on Daily Report. Re-submits return cached response.
- ✅ **GPS auto-capture** (`gps_lat`, `gps_lng`, `gps_accuracy`) on both forms.
- ✅ **Auto weather fetch** on Daily Report (calls weather API after GPS).
- ✅ **Auto report-number sequencing** (`/api/daily-reports/next-number`) on Daily Report.
- ✅ **Auto hours computation** on each crew row (start/lunch/stop → hours).
- ✅ **Existing severity gating** in Daily Report Safety Escalation section: when `safety_incidents_today==Yes` OR `injuries_reported==Yes`, the 4 safety-notify fields become required. **This is already conditional disclosure done right.** Use this pattern as the template.

The platform is more sophisticated than the previous audit gave it credit for. Compression work should **lean into existing patterns**, not reinvent.

---

## Strategy by workflow

### Daily Report
**Target experience:** A super in the field at 4:30pm completes a clean-day report in **under 90 seconds**, end-to-end on phone.
**Strategy:**
1. **Tier 1 — Always visible:** project info · crew (one tap per worker) · 6+ photos · safety incidents Yes/No · sign-off
2. **Tier 2 — Auto-expand on signal:** Safety escalation block (already conditional — preserve), schedule_delays_notes (only if `schedule_delays==Yes`)
3. **Tier 3 — "More fields" disclosure (collapsed by default):** Subcontractors · Visitors · Equipment · Materials · Activities · Distribution list · Weather snapshots
4. **Persistent UX:** the "More fields" disclosure state is remembered per-user via localStorage.

**Net visual reduction:** ~35 inputs visible → ~12 inputs visible (66% reduction). All fields remain submittable.

### Incident
**Target experience:** A super reports a Near Miss in **under 60 seconds**. A stress-driven serious incident captures the critical witness/photo/severity data in **under 2 minutes**, then enters a "Tier 2" follow-up enrichment flow that can be completed back at the truck/office.
**Strategy:**
1. **Tier 1 — Fast Entry (always visible):** who · what · where · severity · immediate action · photos
2. **Tier 2 — Follow-Up Enrichment (post-save, optional, prompted via notification):** witnesses · root cause checklist · contributing factors · OSHA fields · medical facility · notifications acknowledged
3. **Tier 1 → Tier 2 path:** initial submit creates the incident record with `tier=1`. A notification routes to Safety. The reporter (or Safety) opens the incident later from the existing detail view and completes Tier 2 fields **without re-submitting** — same record, additional data.
4. **Auto-escalation safety net:** if `severity` ∈ {medical, restricted, lost_time, fatality}, Tier 2 fields surface immediately in the **same** submit page (no second visit allowed for serious incidents).

**Net effect:** the typical Near Miss drops from 54 inputs to ~8. Serious incidents still capture full data, but in a flow that respects the field reality.

---

## What this plan explicitly does NOT do

| ❌ Not in scope | Why |
|---|---|
| Delete any data field | Compliance retention requires the schema stays whole |
| Touch any backend route | Phase 5C is UX-only |
| Introduce a wizard | Wizards add clicks; we're removing them |
| Add animations / transitions | Visual fluff slows mobile |
| Change visual theme | The platform's construction-direct look must stay |
| Add a "feature toggle" UI | Power users already have "Show all fields"; that's enough |
| Build a new mobile app | This is a responsive-web compression, period |
| Re-architect the form | We collapse and reorder, we don't refactor |

---

## Execution gates

**Phase 5C is a planning phase only.** No code may move until:

1. ✅ All 5 Phase 5C docs are landed (this is happening now).
2. ⏸️ Operator reviews the 5 docs and authorizes specific items.
3. ⏸️ **A real superintendent is observed using the current Daily Report and Incident forms on their actual phone, in actual conditions, end-to-end.** Field shadow validates the compression hypotheses.
4. ⏸️ Operator green-flags individual compression items.

**Suggested implementation order if authorized:**
1. Daily Report Tier 3 disclosure (~30 LOC) — biggest visual impact
2. Daily Report Tier 1 reorder (~20 LOC) — improves first-glance clarity
3. Incident Tier 1 fast entry (~80 LOC) — biggest stress-day impact
4. Incident Tier 2 follow-up flow (~120 LOC) — completes the tiered model
5. Cosmetic touchups (~50 LOC) — section anchors, "Show all fields" toggle

**Total estimated effort if all items authorized:** ~300 LOC across 2 files. **All frontend. Zero backend.**

---

## Trust preservation guardrails (see `OPERATIONAL_ADOPTION_PROTECTION_PLAN.md` for detail)

- Tier 1 → Tier 2 path is **clearly indicated** ("Tier 2 follow-up pending — Safety has been notified").
- Tier 2 fields appear in the existing incident detail page so Safety doesn't have to chase the reporter.
- Notification routing fires on Tier 1 submit (Safety gets immediate alert).
- Lifecycle status on the incident record reflects tier state (e.g., `tier_1_only` vs `tier_2_complete`).
- "More fields" disclosure on Daily Report does **not** affect required-field validation — if a Tier 3 field is required by backend rules, it still blocks submit.

---

## Closing principle

Compression is not subtraction of data. It's subtraction of **simultaneous visual demand**. Every byte the form captures today, it still captures after compression. Every governance hook still fires. Every notification still routes. The supervisor just sees fewer things at once.
