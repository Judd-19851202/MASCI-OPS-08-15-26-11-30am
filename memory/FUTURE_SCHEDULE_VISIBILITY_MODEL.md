# FUTURE SCHEDULE VISIBILITY MODEL

_Phase ODR-Governance Extension · Future-Schedule Per-FLL Contract · 2026-05-29_

This document locks the per-FLL visibility model for the future
Schedule / P6 integration **before** Schedule implementation
begins.

**Architecture only. No implementation.**

---

## 1 · Schedule object inventory

The future schedule system carries:

- **Activities** (work items) with planned + actual start / finish
- **Look-ahead windows** (1-day · 3-day · 2-week · monthly)
- **Critical path** (computed)
- **Resource assignments** (crews / equipment / materials)
- **Float / slack**
- **Schedule changes** (revisions · baselines)
- **Cost loading** (P6 integration)
- **Milestones** (contractual)
- **Resource conflicts** (cross-project)

---

## 2 · Per-FLL visibility · Schedule

| Schedule capability | FLL-1 Foreman | FLL-2 GF | FLL-3 Super | FLL-4 Sr Super | FLL-5 PM | FLL-6 Ops Leader |
|---|---|---|---|---|---|---|
| See today's activities (own work) | FULL (today) | LIMITED (today · own crews) | FULL | FULL | FULL | SUMMARY |
| See tomorrow's activities (own work) | FULL (tomorrow) | LIMITED (tomorrow · own crews) | FULL | FULL | FULL | SUMMARY |
| 3-day lookahead | LIMITED (own crew) | FULL (own crews) | FULL | FULL | FULL | SUMMARY |
| 2-week lookahead | LIMITED (project-level summary) | LIMITED | FULL | FULL (regional) | FULL | SUMMARY |
| Monthly view | NONE | LIMITED | FULL | FULL | FULL | SUMMARY |
| Critical path | NONE | NONE | LIMITED (operational impact only) | LIMITED | FULL | SUMMARY |
| Float / slack | NONE | NONE | LIMITED | LIMITED | FULL | SUMMARY |
| Resource assignments (own crew) | FULL | FULL (own crews) | FULL | FULL | FULL | SUMMARY |
| Resource assignments (other crews) | NONE | LIMITED (own coordination) | FULL | FULL | LIMITED | SUMMARY |
| Schedule changes / revisions | LIMITED (own work) | LIMITED (own crews) | FULL | FULL | FULL | SUMMARY |
| Cost loading (P6) | NONE | NONE | NONE | NONE | FULL | SUMMARY |
| Milestones (contractual) | LIMITED (today/tom relevant) | LIMITED | FULL (project) | FULL | FULL | SUMMARY |
| Resource conflicts (cross-project) | NONE | NONE | LIMITED (alerted only) | FULL | LIMITED (per project) | SUMMARY |
| Schedule health KPIs | NONE | LIMITED | FULL | FULL | FULL | SUMMARY |

---

## 3 · Five Schedule doctrine rules

| # | Rule |
|---|---|
| SCH-V1 | **Foreman sees today + tomorrow.** Operationally, that is the actionable horizon. Anything past tomorrow is doctrinally out of scope per V8. |
| SCH-V2 | **GF sees 3-day lookahead.** Coordination horizon — what's coming, what's about to arrive, what to pre-stage. |
| SCH-V3 | **Super owns project lookahead.** Super is the project command center; their schedule view is full project scope. |
| SCH-V4 | **Senior Super sees regional resource conflicts.** When projects compete for the same crew / equipment / material, Sr Super arbitrates. |
| SCH-V5 | **PM owns the schedule-as-contract.** PM sees critical path, float, cost loading, milestones — the financial / contractual lens. |

---

## 4 · ODR ↔ Schedule integration

- **Plan vs Actual** (ODR Section 14) directly feeds Schedule
  variance.
- **Tomorrow Plan** (ODR Section 13) seeds Schedule's 3-day
  lookahead at GF level.
- **Production segments** (ODR Section 6) match station-limit
  intersections with Schedule activities for FLL-5 critical-path
  view.
- **Delays / Extra Work** (ODR Sections 7-8) feed Schedule impact
  computation.

Visibility of these ODR-sourced schedule signals follows the FLL
matrix above — not the original ODR matrix. (E.g., a foreman who
can see their own delay row may NOT see how that delay propagates
through Schedule's critical path computation.)

---

## 5 · Resource conflict surfacing

Cross-project resource conflicts (a crew assigned to two projects ·
equipment double-booked) are:

- Computed at the Schedule layer.
- Surfaced to **FLL-4 Senior Super FULL** (their primary lens).
- Surfaced to **FLL-3 Super LIMITED** (alert-only — "your crew is
  also assigned to Project X tomorrow").
- Surfaced to **FLL-5 PM LIMITED** (per their project's exposure
  only).
- Not surfaced to FLL-1 / FLL-2.

---

## 6 · Public-link surface

Public link (foreman's anonymous data-collection surface) sees
**only today's project + crew assignment** via the same FLL-1 lens.
No look-ahead, no critical path, no other crews.

---

## 7 · Doctrine anchors

| Doctrine | Anchor |
|---|---|
| V8 foreman today + tomorrow | § 3 SCH-V1 |
| V14 Schedule by horizon | § 2 matrix + § 3 SCH-V1 to V5 |
| V16 Sr Super = regional optimization | § 3 SCH-V4 + § 5 |
| V6 PM ≠ MORE | § 3 SCH-V5 (cost / critical path are PM-only, not Super-extension) |

_End of Future Schedule Visibility Model._
