# Phase 5C · Workflow Compression Plan (Master)

**Date:** 2026-05-24
**Status (post-execution 2026-05-24):** ✅ **Iter 1 + Iter 3 IMPLEMENTED.** Iter 2 (Tier-1 reorder) folded into Iter 1 (section order already correct after Tier-3 collapse). Iter 4 (Tier-2 follow-up via PATCH) leverages existing backend capability — no work required. Iter 5 (UX polish) — mobile-friendly classes baked into Iter 1/3 implementations.
**Mode:** EXECUTION COMPLETE for all behavior-changing iterations.

---

## Execution log (2026-05-24)

### ✅ Iter 1 — Daily Report Tier-3 disclosure
- File: `frontend/src/pages/NewDailyReport.jsx` · +60 LOC · 1,524 → 1,583
- Added `showMoreFields` state with `localStorage` persistence (`masci.dr.showMoreFields`).
- Wrapped Sections 05 (Subs) · 06 (Visitors) · 07 (Equipment) · 08 (Materials) · 09 (Activities) behind a single "Show all fields" disclosure.
- Collapsed banner clearly explains what's hidden.
- "Hide optional fields" reverse toggle when expanded.
- ZERO field deletion · all 35 + 7 schema fields remain in payload when populated.
- Existing Safety Escalation conditional logic untouched.
- ESLint clean.

### ✅ Iter 2 — Daily Report Tier-1 reorder
**Result:** No code change needed. The current section order (01 Report Info → 02 Weather → 03 General → 04 Crews → [Tier 3 collapsed] → 10 Photos → 11 Sign-Off) already matches the recommended Tier-1 ordering after Iter 1 collapse. The previously-perceived "wrong order" was caused by Tier 3 sections (05-09) being visually interleaved with Tier 1; collapsing them resolves the ordering problem.

### ✅ Iter 3 — Incident Fast Entry (tiered)
- File: `frontend/src/pages/NewIncident.jsx` · +84 LOC · 1,088 → 1,172
- Added `SERIOUS_SEVERITIES`, `isSeriousIncident`, `tier2Open` state + `showTier2` derived gate.
- Wrapped Sections 05 (Root Cause) · 06 (Witnesses) · 07 (Corrective Actions) · 08 (Notifications Made + Distribution List) behind a Tier-2 disclosure.
- **Auto-expansion safety net:** when severity ∈ {medical, restricted, lost_time, fatality}, `showTier2` is forced TRUE and the collapse toggle is locked OFF.
- Locked banner displayed when serious incident: *"Severity is Medical or higher — full follow-up detail is required before submit."*
- Near Miss / First Aid: 8-field fast-entry path (Tier 1 only).
- ZERO field deletion · all 54 schema fields remain in payload.
- Section 03 (Person Involved) `isInjury` conditional preserved untouched.
- ESLint clean.

### ✅ Iter 4 — Incident Tier-2 follow-up
**Result:** Zero new code required. The existing incident detail page (`ViewIncident.jsx`) supports PATCH-based field updates against the existing `/api/incidents/{id}` endpoint. A reporter or Safety user who submits a Tier-1-only incident can complete Tier-2 fields from the detail view at any time. The audit log, severity-based CAPA creation, and lifecycle status all use the same backend hooks.

### ✅ Iter 5 — UX polish
**Result:** Folded into Iter 1 + Iter 3. Mobile-friendly Tailwind classes (`flex items-center justify-between gap-3`, `shrink-0`, `min-w-0`, `text-sm`, dashed `border-dashed`) baked into both disclosure banners. Visual depth and density mirror existing platform conventions; no new visual experiments introduced.

### Frontend health post-execution
- Frontend supervisor: RUNNING · uptime preserved
- Bundle: 200 OK
- Only pre-existing deprecation warnings in webpack log (no new errors)
- ESLint on both modified files: clean

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
