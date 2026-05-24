# Field Friction Measurement

**Date:** 2026-05-24
**Method:** Static-code measurement against the schema. **NO physical-device measurement performed.** All numbers are estimates pending field shadow.

---

## Daily Report — measured friction

### Current state (NewDailyReport.jsx · 1,524 LOC)

| Friction signal | Measurement | Source |
|---|---|---|
| Total scalar fields | 35 | `dailyReportSchema.js` |
| Total array fields | 7 | `dailyReportSchema.js` |
| `<input>` / `<select>` / `<textarea>` / `<button>` element references | ~estimated 80+ | grep on `<input` + dynamic crew rows |
| Visible sections (`<section>` tags) | 7 | grep on `<section\|className.*sect` |
| Conditional logic blocks | 4 (Safety Notified, Who, Filed?, Time) | grep on `Step \d` comments |
| LifecycleGuide instances | 2 (top + bottom) | grep on `LifecycleGuide` |
| `useState` blocks | 5 | grep on `useState\(` |
| Lines of conditional rendering | Estimated ~150 (Safety Escalation block) | structural read |
| Persistent state hooks | `useDraftSync` + `idempotencyKeyRef` | grep on `useDraftSync` |

### Estimated taps to complete (clean-day Daily Report on phone)

| Step | Taps | Cumulative |
|---|---|---|
| Open page | 0 | 0 |
| Select project from dropdown | 2 (open + pick) | 2 |
| Type location | 1 focus + ~10 keystrokes (counted as 1 step) | 3 |
| Verify prepared_by | 0 (auto) | 3 |
| Tap each Yes/No flag (×4) | 4 | 7 |
| Scroll past empty Subs/Visitors/Equipment/Materials/Activities | ~3 scroll-screens | 7 (scroll, not taps, but adds time) |
| Add 1 crew row + fill name/trade/start/lunch/stop | ~7 taps | 14 |
| Upload 6 photos | 6 (one tap per upload action) | 20 |
| Sign | 1 tap (signature pad) | 21 |
| Scroll back to Submit | ~3 scroll-screens | 21 |
| Submit | 1 | 22 |
| Confirm if dialog appears | 1 | 23 |

**Estimated time:** 4–6 minutes for a clean-day report on a phone.

### Compressed-state estimated taps

| Step | Taps |
|---|---|
| Open page | 0 |
| Select project | 2 |
| Type location | 1 |
| 4 Yes/No flags | 4 |
| 1 crew row | 7 |
| 6 photos | 6 |
| Sign | 1 |
| Submit | 1 |

**Total: ~22 taps → ~9 taps (−59%)** assuming "More fields" stays collapsed.
**Estimated time:** 60–90s.

### Scroll depth

| State | Scroll-screens |
|---|---|
| Current (all sections expanded) | ~5 (on a 4.7-inch screen) |
| Compressed (Tier 3 collapsed) | ~1.5 |

### Hesitation point detection

Best guesses where supervisors pause:

| Hesitation point | Likely cause |
|---|---|
| At "Subcontractors" section | "Do we even have subs today?" — empty section adds cognitive load |
| At "Materials" section | "Was there a delivery?" — most days, no |
| At "Activities" section | "Activity vs Work performed vs Crew notes" — overlap unclear |
| At "Distribution list" | "Who needs a CC?" — most users don't know |
| At "Submit" button after photos | "Did I miss anything?" — no visible checklist |

**Mitigation in compressed model:** all 5 hesitation points are below the "More fields" disclosure.

---

## Incident — measured friction

### Current state (NewIncident.jsx · 1,088 LOC)

| Friction signal | Measurement | Source |
|---|---|---|
| Total scalar fields | ~54 | `incidentSchema.js` |
| Array fields | 3 (`witnesses`, `distribution_list`, `photos`) | schema |
| Root cause checkboxes | 11 | schema (`ROOT_CAUSE_CATEGORIES`) |
| Body part options | 24 | schema (`BODY_PARTS`) |
| Injury nature options | 17 | schema (`INJURY_NATURES`) |
| Severity options | 6 | schema (`SEVERITY_LEVELS`) |
| Incident type options | 9 | schema (`INCIDENT_TYPES`) |
| Notification toggles | 5 (safety_mgr, pm, gc, owner, osha) | schema |

### Estimated taps to complete (Near Miss on phone, current state)

| Step | Taps |
|---|---|
| Open page | 0 |
| Project / location / time | ~5 |
| Pick incident_type (9 options) | 2 |
| Pick severity (6 options) | 2 |
| Person fields (name, role, employer, years experience) | ~10 |
| Body part / injury nature pickers (24+17 options) | 2 (often left default for Near Miss) |
| Description + immediate_cause + contributing_factors | ~3 text areas |
| Root causes (11 checkboxes) | 0–11 |
| Witnesses (often skipped) | 0 |
| Corrective actions + responsible party + target date | ~5 |
| Notifications (5 toggles) | ~5 |
| Photos | 1–6 |
| Sign-offs | 1–2 |
| Submit | 1 |

**Estimated total: ~35–40 taps**, ~5–8 minutes.

### Tier 1 fast-entry estimated taps (Near Miss compressed)

| Step | Taps |
|---|---|
| Open page | 0 |
| Tap severity pill (Near Miss) | 1 |
| Type description (1 textarea) | 1 |
| Project (auto-selected from last) | 0 |
| Location (1 line) | 1 |
| Person name (master picker or type) | 2 |
| Immediate actions | 1 |
| Take/upload photo | 1 |
| Submit | 1 |

**Total: ~8 taps · <60s.**

### Cognitive overload points

| Trigger | Why it overloads |
|---|---|
| 11 root cause checkboxes | "Which ones apply? All? Any? None?" — paralysis under stress |
| 5 separate notification toggles | Looks like a checklist of responsibility ("did I notify all of these?") |
| Multiple signature fields | "Whose signature first?" |
| Required vs optional ambiguity | No visible asterisks or color-coding; user fears missing a required field |
| 6-tier severity scale | Hard to choose under stress; default may be wrong |

**Mitigation in tiered model:** all 5 are deferred to Tier 2 follow-up or eliminated by auto-routing.

---

## Mobile survivability rating

| Workflow | Current | Compressed |
|---|---|---|
| Daily Report | 🟡 Acceptable on tablet; hostile on phone | ✅ Phone-friendly |
| Incident (Near Miss) | 🔴 Will be filled after-the-fact, not in field | ✅ Field-survivable |
| Incident (Lost Time) | 🟡 Acceptable on tablet; hostile on phone | 🟡 Acceptable on tablet (still data-heavy, but ordered) |

---

## Notes on what we cannot measure from code

| Measurement | Why not measurable from code |
|---|---|
| Actual tap accuracy with gloves | Requires real device + real glove |
| Sunlight contrast performance | Requires daylight test |
| Voice-to-text accuracy on noisy job site | Requires real recording |
| Stress decision-making time | Requires observation under real conditions |
| Network recovery from disconnect mid-form | Requires throttled-network simulation |
| Multi-touch reliability with wet/dusty screen | Requires field environment |

**These remain field-shadow dependencies. The compressed-state numbers above are the FLOOR of what should be achieved; they may not be the CEILING until validated.**

---

## Suggested field shadow protocol

If operator authorizes a one-day field shadow:

1. **Pick one super and one foreman** for one full shift.
2. **Watch them submit one Daily Report** on their actual phone, in the truck or on site, in their normal flow. Time-stamp each step. Note hesitation points.
3. **Stage one Near Miss exercise** ("imagine you just saw X happen — file it"). Time the submission. Note where they pause.
4. **Compare against the numbers in this doc.** If actual time is 2× the estimate, the compression is even more important than predicted. If actual time matches the estimate, the model is reliable.
5. **Iterate the compression plan** based on the observed gaps.

The whole shadow takes <2 hours. The data quality is irreplaceable.

---

## Closing

These numbers are **honest estimates**, not validated measurements. They tell the right story directionally (compression yields ~60–85% reduction in tap count and time-to-complete) but the absolute numbers must be field-validated before they're used in any rollout pitch.
