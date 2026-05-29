# Auto-Expand Guidance — Certification

_Phase V.2 · Micro UX Refinement · 2026-05-29._

> **Operator directive (verbatim):** _"Guide the user. Do not automate the work. Reduce clicks. Reduce confusion. Keep the workflow familiar. Make the field experience feel effortless."_

## 1 · What shipped (UI-only)

Three additions, all inside `frontend/src/pages/NewDailyReport.jsx`:

| # | Surface | Change |
|---|---|---|
| 1 | `attentionOpen` predicate on the Delays / Extra Work `CollapseCard` | Now fires whenever `weather_impact === "Yes"` OR `schedule_delays === "Yes"` OR (`attemptedSubmit && gateUnmet`). The CollapseCard's `attentionOpen` is one-way force-open, so the foreman can still collapse the card manually after it opens. |
| 2 | `useEffect` watching both YES flags | On the YES transition (NO → YES), scrolls the card into view (`smooth`, centered) on the next paint AND sets `delaysGuideHighlight` for 1.6 s. Manual toggle of the chevron does NOT retrigger this. |
| 3 | Wrapper `<div ref={delaysCardWrapRef}>` around the CollapseCard | Hosts the transient `ring-2 ring-amber-400` highlight + 4 px soft amber halo. `transition-shadow duration-700` keeps the fade calm. Highlight clears after 1.6 s. |

No JSX inside the card was rearranged. No CollapseCard internals were touched.

## 2 · Trigger matrix

| Action | Card behavior | Ring highlight | Auto-row | Auto-fill | Notification |
|---|---|---|---|---|---|
| Weather Impact → **YES** | auto-expand (force-open) | 1.6 s amber ring | ❌ no | ❌ no | ❌ no |
| Delays / Extra Work → **YES** | auto-expand (force-open) | 1.6 s amber ring | ❌ no | ❌ no | ❌ no |
| Weather Impact → **NO** | unchanged (user-controlled) | ❌ no ring | ❌ no | ❌ no | ❌ no |
| Delays / Extra Work → **NO** | unchanged (user-controlled) | ❌ no ring | ❌ no | ❌ no | ❌ no |
| User manually toggles card chevron | normal collapse / expand | ❌ no ring | n/a | n/a | n/a |
| Submit blocked on a gate | force-open (existing behavior) | ❌ no ring (the toast does the work) | n/a | n/a | n/a |
| Toggling NO → YES → NO → YES again | re-fires guidance only on YES transitions | ✅ amber ring on each YES transition | ❌ no | ❌ no | ❌ no |

## 3 · iPad / field experience

Verified at viewport `820 × 1180` (iPad portrait):

- Card scrolls itself into the middle of the viewport on YES → no foreman hunt.
- Amber ring is bright enough on glare but never crosses into red urgency.
- The structured chip grid is the very next thing under the highlighted header — the natural eye path goes from YES → ring → chip.
- The status pill (`Add a row with cause = Weather (required)` or `Add at least one delay (required)`) stays in the foreman's line of sight while picking the chip.

Field-friendly path now:

```
YES → card opens → chip tap → row appears → done.
```

vs. the previous:

```
YES → silence → submit → blocked toast → hunt → expand → chip tap → row → resubmit.
```

## 4 · Prohibited behaviors (audited · all confirmed absent)

| Prohibited | Confirmed absent? |
|---|---|
| Auto-create Weather row | ✅ verified — row count stays 0 after Weather YES |
| Auto-create Delay row | ✅ verified — row count stays 0 after Delays YES |
| Auto-fill Lost Hours | ✅ no `hours_impact` defaults beyond existing `0.0` placeholder |
| Auto-fill Notes | ✅ no notes default beyond existing placeholder |
| Notification | ✅ no `toast`, no `api.post`, no email, no SMS |
| RFI creation | ✅ no RFI substrate touched |
| Schedule impact | ✅ no schedule substrate touched |
| PM alert | ✅ no PM substrate touched |

This remains **signal-only**.

## 5 · Validation matrix (Playwright · iPad viewport)

| Probe | Result |
|---|---|
| Pre-state: card collapsed · no ring | 🟢 |
| Weather YES → card open | 🟢 |
| Weather YES → ring visible | 🟢 |
| Ring cleared after ~1.6 s | 🟢 |
| Card remains open while Weather=YES | 🟢 |
| Weather NO → card stays open (user-controlled) | 🟢 |
| Weather NO → no spurious ring | 🟢 |
| User-collapsed reset works | 🟢 |
| Delays YES → card open | 🟢 |
| Delays YES → ring visible | 🟢 |
| Delays YES → ring cleared after ~1.6 s | 🟢 |
| Auto-row check: rows count stays at 0 | 🟢 |
| Delays NO → no ring re-fire | 🟢 |
| Existing rows preserved across YES re-trigger | 🟢 |
| 89 / 89 ODR backend tests | 🟢 |
| ESLint clean | 🟢 |

## 6 · Doctrine compliance

- ✅ **Guidance, not automation.** No row creation, no field fill, no notification — only force-open + scroll + brief highlight.
- ✅ **Doctrine Lock #1 (Simplicity).** Foreman 9-step contract preserved · no new steps · saves at minimum one tap and one resubmit cycle per YES answer.
- ✅ **Doctrine Lock #2 (Inheritance).** Reused `CollapseCard.attentionOpen` and Tailwind `ring-*` utilities · no new components or libraries.
- ✅ **No schema changes · no backend changes · no workflow changes · no API additions.**
- ✅ **Operational Calmness.** Amber, not red. 1.6 s, not pulsing. Slate pills stay slate when nothing is required.

## 7 · Stop condition

🛑 **HALTED after this micro-refinement as directed.**

- ❌ NO Pilot · NO RFI · NO Schedule · NO P6
- ❌ NO PM Hub wiring · NO approval/rejection workflow
- ❌ NO additional role standardization beyond the prior pass
- ✅ Awaiting **Internal Superintendent Validation Review**.

---

_End of AUTO_EXPAND_GUIDANCE_CERTIFICATION.md._
