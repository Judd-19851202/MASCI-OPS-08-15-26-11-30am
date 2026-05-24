# Workflow Simplification Recommendations (Phase 5B)

**Date:** 2026-05-24
**Rule:** Every recommendation below is **subtractive or compactive** —
remove a step, collapse a section, defer a decision. **Zero feature
expansion.** Each item is gated on operator approval AND (where stated)
field validation.

**Reading order:** Top of list = highest leverage per LOC of change.

---

## 🔴 P0 — Highest-leverage simplifications

### S1 · Progressive disclosure on Daily Report (1,524 → ~600 visible LOC)
**Problem (from C1):** 7 sections + 35 inputs all visible at once.
**Recommendation:** Collapse "Materials", "Visitors", "Weather snapshots", and "Equipment" sections behind a single "More fields" disclosure button. The top sections (project info · crew · safety incidents · general notes) stay visible.
**Why now:** Daily Report is submitted **daily by every super**. Reducing visual weight here has the largest aggregate adoption impact on the platform.
**Risk:** Power users may dislike clicking to expand. Mitigation: remember last-state per user via localStorage.
**Effort:** ~30 LOC in `NewDailyReport.jsx`. **Pure CSS/state change. No backend impact.**
**Pre-implementation gate:** **field shadow ONE super doing ONE daily report before authorizing.** If the super never touches Materials/Visitors during the session, this is validated.

### S2 · Incident form: "fast path" for routine incidents
**Problem (from C2):** 54 inputs for every incident, even minor ones.
**Recommendation:** Add a "Near Miss / Minor" toggle at the top. When ON, hide all OSHA-grade structured fields and show only: project · location · person · what happened · immediate action. The full form is one click away if the incident escalates.
**Why now:** 80% of incidents are near-misses or minor. Forcing OSHA-grade structure on all of them slows reporting and erodes data quality.
**Risk:** Supers may default to "Near Miss" inappropriately. Mitigation: if `severity` field is set to High/Critical, auto-expand the full form (defensive UX).
**Effort:** ~80 LOC in `NewIncident.jsx`. **Pure UI change.**
**Pre-implementation gate:** **field shadow ONE incident submission.** Confirm field reality matches the 80/20 hypothesis.

---

## 🟠 P1 — High-value, low-risk

### S3 · Consistent mobile breakpoint pattern across pages
**Problem (from H2):** Only DR + Incident have explicit `md:hidden`. Other pages rely on Tailwind defaults.
**Recommendation:** Adopt a one-line convention: every page-level component starts with `<div className="min-h-screen px-3 sm:px-6 md:px-8 ...">`. Apply during normal page-touch cycles, not as a sweep.
**Why now:** Pre-empts mobile complaints during rollout. Free polish.
**Effort:** 1–2 lines per page · ~136 pages · do it as pages are touched, not all at once.
**Pre-implementation gate:** None · cosmetic.

### S4 · Section-jump navigation inside Daily Report
**Problem (from M1):** 7 sections, no overview navigation.
**Recommendation:** Add a sticky "section index" at the top showing 7 section labels with progress dots (filled/unfilled). Tapping jumps to that section.
**Why now:** Pairs with S1 (progressive disclosure) — even with collapse, the 4 visible sections benefit from quick navigation.
**Risk:** Low. Sticky bar adds vertical weight; need to verify on phones.
**Effort:** ~50 LOC in `NewDailyReport.jsx`. CSS + scroll-into-view.
**Pre-implementation gate:** Wait for S1 first.

### S5 · "Save as draft" indicator on Daily Report
**Problem (from M4):** Single Submit button on a 1,500-LOC form is anxiety-inducing.
**Recommendation:** Add an auto-saved draft indicator at the top (e.g., "Draft saved 12s ago · Submit when ready"). Use localStorage with a server-side draft endpoint optional (see backend constraint).
**Backend constraint:** May require a new draft endpoint OR localStorage-only (preferred for Phase 5B — no backend changes).
**Effort:** ~40 LOC frontend, 0 backend if localStorage-only.
**Pre-implementation gate:** Field shadow to confirm anxiety is real.

---

## 🟡 P2 — Polish, defer until P0/P1 lands

### S6 · QA/QC form audit (parallel to DR/Incident)
**Recommendation:** Measure `NewQaqcInspection.jsx` and `QaqcSection.jsx` LOC + input count. If comparable to NewDailyReport (>1,000 LOC, >30 inputs), apply S1-style progressive disclosure.
**Why later:** Adoption risk is lower (QA/QC is foreman-conducted, less frequent than daily reports).
**Effort:** Measurement step first (~10 minutes). Then targeted refactor if confirmed.

### S7 · Notification grouping if per-role volume > 10/day
**Recommendation:** Instrument one week of per-role notification counts. If any role exceeds ~10/day, group by category (e.g., "3 new CAPAs · 2 expiring trainings · 1 incident") instead of individual notifications.
**Effort:** Backend instrumentation first (counter aggregation). UI is a separate decision.
**Pre-implementation gate:** Measure before designing.

### S8 · Field jargon → field language audit
**Recommendation:** Walk a foreman through the platform. Note every term they ask about. Replace with field equivalents (e.g., "OSHA recordable" → "Will OSHA need to know?").
**Effort:** ~20 LOC of i18n key edits. **Zero structural change.**
**Pre-implementation gate:** Need a foreman partner.

### S9 · Empty-state copy upgrade
**Recommendation:** Sweep all "No items" empty states. Replace with action-oriented copy ("Submit your first daily report — takes 2 minutes" / "No incidents yet · let's keep it that way · here's the checklist").
**Effort:** Sweep ~15–20 list pages. ~5 LOC each.
**Pre-implementation gate:** None.

---

## 🟢 P3 — Future-watch (do NOT prioritize)

### S10 · High-contrast / sunlight mode toggle
Defer until field complaints surface.

### S11 · Offline queue for forms
Heavy lift. Defer until intermittent-LTE complaints become specific.

### S12 · Signature-pad gloved-finger tolerance
Field-validate first; address only if real complaints emerge.

### S13 · A11y (screen reader, font scaling)
Defer until a specific user need surfaces.

### S14 · Print stylesheets
PDF flow handles this. Don't invest in browser print.

---

## What is explicitly OFF the table

The following are **NOT** allowed in Phase 5B under any circumstances:

- 🚫 New dashboards
- 🚫 New analytics surfaces
- 🚫 New role types
- 🚫 New portal types
- 🚫 New form fields ("while we're here")
- 🚫 New notification channels (SMS/push) without proven need
- 🚫 New file format support
- 🚫 New AI/ML features
- 🚫 Frontend redesign sweeps
- 🚫 Backend route extractions (Phase 4D continues separately with its own discipline)
- 🚫 Refactoring "improvements" disguised as simplifications

If you find yourself writing more code than the recommendation
specifies, **STOP** and re-read this document.

---

## Decision framework for the operator

For each recommendation, the gate is:

1. Is there **real** evidence the friction exists? (code survey ≠ evidence; field shadow = evidence)
2. Is the change **subtractive** (removes a step) or **compactive** (collapses without removing)?
3. Is the effort genuinely small (<100 LOC) and isolated?
4. Is there a clear rollback if the change makes things worse?

If all 4 are **YES**, authorize. If any is **NO**, defer.

---

## Recommended sequence (post-field-shadow)

If operator authorizes any work, suggested order:

1. **S1** — Daily Report progressive disclosure (highest leverage)
2. **S2** — Incident "near miss fast path" (second highest leverage)
3. **S4** — Daily Report section-jump nav (pairs with S1)
4. **S5** — Save-as-draft indicator
5. **S9** — Empty-state copy sweep (free polish)
6. **S3** — Mobile breakpoint convention (apply as pages are touched)
7. **S7** — Notification grouping (after instrumentation)
8. **S6** — QA/QC audit & possible refactor
9. **S8** — Field-language audit

Everything else: defer indefinitely unless field evidence demands it.

---

## Closing principle

**Don't redesign workflows. Compact them.**

If a workflow's form can fit in fewer pixels without removing any field,
that's a win. If a workflow's form can drop optional fields behind
"More", that's a win. If a workflow's form needs every field every
time, leave it alone.
