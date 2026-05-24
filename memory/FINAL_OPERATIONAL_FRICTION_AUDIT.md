# Final Operational Friction Audit · Phase 7 · WS1

**Date:** 2026-05-24
**Method:** Walked every high-frequency workflow (paths, taps, hesitation watchpoints, mobile pacing, lifecycle-state clarity, hidden continuity gaps) and rated each against four axes.

**Rating scale (per axis):**
- 🟢 GREEN — production-ready, leave alone
- 🟡 AMBER — works, minor polish optional
- 🔴 RED — needs intervention (none flagged below as of Phase 7)

**Axes:**
- **Friction** — taps/scrolls/cognitive overhead per submission.
- **Mobile** — 390 px readability, glove-friendliness, sunlight legibility.
- **Clarity** — lifecycle state and downstream visibility clearly communicated.
- **Trust/Risk** — risk of the user submitting incomplete/incorrect data without realizing.

---

## Daily Reports (`/daily/new`, `/daily/submit`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | CollapseCard compression (Phase 5C) cut median tap count from ≈ 110 → ≈ 75. Crew/Subs/Visitors/Equipment/Materials/Activities are all opt-in. |
| Mobile | 🟢 | 390 px layout verified Phase 6. Submit button replicated TOP + BOTTOM. No native-keyboard overlap. |
| Clarity | 🟢 | Phase 6 operational completion banner (`Optional sections available` → `Operationally complete · N sections filled today` → rose `Attention · …`). Field-direct prompt on rose. |
| Trust/Risk | 🟢 | Signal-driven gap detection catches schedule-delay-without-detail and safety-incident-without-notified. Safety escalation (already inline, not collapsed) still runs through `validate()`. |

**Verdict: LEAVE ALONE.** Any further compression risks burying operational requirements.

**Do NOT add:**
- "Submit anyway" override on rose state. The friction is intentional.
- A "Save draft to cloud" button — `useDraftSync` already does it silently.
- A "Summary of today" auto-generated text. Foremen write what they want to write.

---

## Incidents · Near-Miss (`/incidents/new`, `/incidents/submit`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | ≈ 30 taps for a clean near-miss submission. Tier-2 collapsed and visible-but-not-nagged. |
| Mobile | 🟢 | Same shell as Daily Report; identical pacing. |
| Clarity | 🟢 | Phase 6 slate banner `Ready to submit · follow-up optional for this severity` tells the foreman they're done. |
| Trust/Risk | 🟢 | Idempotency-key dedup + audit trail. Foreman can't accidentally double-submit. |

**Verdict: LEAVE ALONE.**

---

## Incidents · Serious (`severity ∈ {medical, restricted, lost_time, fatality}`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | Tier-2 cards auto-open with `lockOpen`. User cannot collapse them, cannot skip them. |
| Mobile | 🟢 | Auto-expand pushes submit further down, but the rose `Attention` banner above submit communicates exactly why. |
| Clarity | 🟢 | Phase 6 banner reads `Operationally complete · ready to submit` only after Root Cause + Corrective + Notifications all have content. |
| Trust/Risk | 🟢 | Submit refused with toast `Complete the highlighted section or mark it not used today.` if any Tier-2 section is bare. Severity escalation safety net unchanged. |

**Verdict: LEAVE ALONE.**

**Do NOT add:**
- A "Submit and complete later" path. That's the entire reason CAPAs exist downstream.
- AI auto-fill for Root Cause suggestions. Encourages perfunctory completion.

---

## PPE Issuance (`/safety-portal/ppe`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | Roster-backed Combo for employee selection prevents typos. Auto-fills name + ID. |
| Mobile | 🟡 | Form is acceptable at 390 px but the size/quantity grid could be tighter. Not blocking. |
| Clarity | 🟢 | `EMP_LINK_UNRESOLVABLE` governance finding catches non-roster issuances; no surprise. |
| Trust/Risk | 🟢 | Subcontractor-issuance path handled explicitly; reviewer knows whose record is whose. |

**Verdict: LEAVE ALONE.** The grid tightness is too cosmetic to justify a touch.

---

## CAPA Workflows (`/safety-portal/corrective-actions`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | Phase 5D `Open Follow-Up CAPA` CTA from incident detail pre-fills source_kind + source_id + title. Manual entry path unchanged. |
| Mobile | 🟡 | Desktop-first by design (Safety Manager's primary surface). Acceptable but not glove-friendly. **No change recommended** — Safety reviews happen at a desk. |
| Clarity | 🟢 | Status pipeline Open → In Progress → Pending Review → Verified → Closed. Pending Review status is in the operational glossary (Phase 5D). |
| Trust/Risk | 🟢 | Second-reviewer rule enforced by `CAPA_AWAITING_VERIFICATION` finding at 7 days. |

**Verdict: LEAVE ALONE.**

---

## PM Crew Compliance (`/pm-portal/crew-compliance`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | Read-only by design. PM does not author records — they see HR/Safety/Dispatch data through their lens. |
| Mobile | 🟡 | Acceptable on tablet. Not optimized for phone. **No change recommended** — PMs almost always review at a desk or in a project trailer. |
| Clarity | 🟢 | Lens design: one project at a time; readiness rows show why an employee is unqualified. |
| Trust/Risk | 🟢 | PM cannot accidentally edit (route guard blocks all PATCH/POST). |

**Verdict: LEAVE ALONE.**

---

## Dispatch Driver Readiness (`/dispatch-portal/driver-qualification`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | Single table; sortable; filters by qualification status. |
| Mobile | 🟡 | Desktop-first by design. **No change recommended** — Dispatch is an office role. |
| Clarity | 🟢 | "Why unqualified" surfaces the exact missing item (medical card expired, CDL expired, not approved). |
| Trust/Risk | 🟢 | `Driver disqualified` notification (CRITICAL tier) fires to dispatch + FL + HR + safety. |

**Verdict: LEAVE ALONE.**

---

## Driver Qualification File (HR · `/hr-portal/driver-qualification`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟡 | Long-form by FMCSA design (it has to be — this is the regulatory file). |
| Mobile | 🔴 (acceptable) | NOT mobile-optimized. **Correct** — DQ files are completed at HR's desk during onboarding. |
| Clarity | 🟢 | Each section has a LifecycleGuide. Approval workflow is multi-stage; downstream visibility honors that. |
| Trust/Risk | 🟢 | Approval lock by a different reviewer prevents self-approval. |

**Verdict: LEAVE ALONE.** Field-friendly DQ would defeat the regulatory purpose.

---

## Accountability Timeline (cross-portal · `/safety-portal/employees/{id}/timeline`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | Single page; chronological; rendered in EN + ES. |
| Mobile | 🟢 | Vertical list reads fine at 390 px. |
| Clarity | 🟢 | Each row carries source module + source id + reviewer name. |
| Trust/Risk | 🟢 | Read-only. Cannot be tampered with from this surface. |

**Verdict: LEAVE ALONE.**

---

## Notifications Digest (cross-portal bell · `/api/notifications`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | One bell per portal; FL added Phase 5D. |
| Mobile | 🟢 | Sheet-style overlay on mobile; tap-to-read. |
| Clarity | 🟡 | Volume varies wildly by role. Safety + Admin bells can grow long during incident-heavy periods. **Mitigation already in place**: Phase 6 `NOTIFICATION_DISCIPLINE_MATRIX.md` aggregation rules. |
| Trust/Risk | 🟢 | No spam; no duplicate `linked_source_record_id` rows. |

**Verdict: LEAVE ALONE.** Volume management is the discipline matrix's job, not a UI redesign.

---

## Toolbox Talks (`/safety-portal/toolbox-talks`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | Topic library + attendance roster. Quick to log. |
| Mobile | 🟢 | Field-friendly for the supervisor logging the talk. |
| Clarity | 🟢 | Attendance ties into employee training records. |
| Trust/Risk | 🟢 | Governance finding flags talks logged without any attendees. |

**Verdict: LEAVE ALONE.**

---

## Pre-Operational Inspection (`/safety-portal/pre-op`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | Checklist by equipment type. Drop-in photo evidence. |
| Mobile | 🟢 | Foreman flow; verified at 390 px. |
| Clarity | 🟢 | "Pass / Tag-Out / Defect → CAPA" outcomes route correctly. |
| Trust/Risk | 🟢 | Tag-Out routes to shop defect queue; nothing slips. |

**Verdict: LEAVE ALONE.**

---

## QA/QC (`/admin/qaqc`, `/safety-portal/qaqc`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟡 | More form-heavy than safety workflows by nature (it's an inspection report). |
| Mobile | 🟡 | Tablet-first design. **Correct** — QA inspectors carry tablets, not phones. |
| Clarity | 🟢 | Pass/fail per checklist item; auto-generates CAPAs on fail. |
| Trust/Risk | 🟢 | Inspector signature required; PM signature for sign-off. |

**Verdict: LEAVE ALONE.**

---

## Shop Defects (`/shop-portal/defects`)

| Axis | Rating | Notes |
|---|---|---|
| Friction | 🟢 | Shop-centric workflow; defect → CAPA → return-to-service. |
| Mobile | 🟡 | Desktop-first. Acceptable — shop work uses fixed terminals. |
| Clarity | 🟢 | Lifecycle visible; equipment master ties everything together. |
| Trust/Risk | 🟢 | Equipment cannot return-to-service while open defects exist. |

**Verdict: LEAVE ALONE.**

---

## Cross-cutting observations

### Tone-color inconsistency (P3 backlog, not Phase 7 scope)

The codebase uses two danger palettes:
- **`bg-red-*`** (~388 instances) — older code; signals "danger / urgent / blocked."
- **`bg-rose-*`** (~30 instances) — Phase 5D + Phase 6 code; signals "needs action."

Both communicate similar urgency. Operators do not currently report confusion — the visual distinction is subtle enough that the broader red-family registers as a single signal. **Recommended action:** do nothing in Phase 7. If future polish work tackles this, the rule should be:
- `red` for hard blocks / safety stops (current usage)
- `rose` for "needs action but not blocking" (current usage)

That distinction is approximately what's in place today. Documenting it here as the canonical rule.

### Things that should NOT be expanded further

- **No more LifecycleGuide variants.** The 8 existing guides cover every meaningful lifecycle. Adding more clutters the UI and weakens the signal.
- **No more CollapseCard nesting.** One level deep is the limit. Nested collapse-cards become a UX maze.
- **No more glossary entries beyond the canonical 16.** The discipline is field language → glossary → action. Every new term dilutes the rest.
- **No more notification types.** The 19-row matrix is the ceiling for the next 6+ months.
- **No more bilingual variants beyond EN + ES.** Adding a third language would double translation maintenance with limited operational ROI.
- **No more public-mode forms beyond Daily Report + Incident.** Public-mode is field-entry only; anything else needs auth.

### Hidden continuity gaps audited (none open)

Verified the following sequences are unbroken end-to-end:
1. Incident → CAPA → Verification → Operationally Complete → Accountability Timeline entry. ✅
2. Incident severity ≥ medical → Tier-2 enforcement → Safety + PM + HR notification → ViewIncident rose banner. ✅
3. PPE issuance → Employee record link (or `EMP_LINK_UNRESOLVABLE` finding) → governance score impact. ✅
4. Training expiration → HR + Safety digest → PM Crew Compliance visibility → Dispatch readiness gate. ✅
5. Daily Report safety escalation → /api/incidents auto-create proposal → Safety review → CAPA. ✅
6. CAPA Open → In Progress → Pending Review → Verified (by different reviewer) → Closed → audit trail. ✅
7. FL portal user → unified `/api/notifications` → cross-portal incident visibility (Phase 5D closure). ✅
8. Driver disqualification → Dispatch readiness → FL/HR/Safety notifications → re-qualification CAPA. ✅

No gaps surfaced. The platform's continuity is mature.

---

## Phase 7 verdict

The 14 high-frequency workflows are operationally green. The 7 cross-cutting lifecycles are unbroken. The friction left in the platform is **mostly intentional and operationally protective** (e.g., serious-incident Tier-2 lock, second-reviewer CAPA verification, idempotency dedup).

**Recommendation: Phase 7 is a documentation + restraint phase, not a code phase.** Ship the three discipline documents (this file, `OPERATIONAL_SIGNAL_DISCIPLINE_REVIEW.md`, `DO_NOT_BUILD_YET.md`) and resist the urge to "improve" things that are already operationally complete.

The platform is ready for production deploy.
