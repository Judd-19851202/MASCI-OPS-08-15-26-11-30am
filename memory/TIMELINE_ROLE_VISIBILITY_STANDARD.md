# TIMELINE ROLE VISIBILITY STANDARD

_Phase ODR-Governance Extension · Timeline Visibility Contract · 2026-05-29_

This document defines, per FLL, what events appear on the
Operational Timeline and Timeline Sidecar.

**Architecture only. No implementation.**

---

## 1 · Three failure modes the standard prevents

| Failure | What it looks like |
|---|---|
| **Timeline overload** | Hundreds of low-signal events ("JHA signed" · "photo uploaded") drown the operationally important ones |
| **Permission leakage** | A role sees events from data they cannot see in raw form (e.g., FLL-1 sees a constraint event for a constraint they cannot view) |
| **Operational noise** | Events irrelevant to a role's mission appear and degrade signal-to-noise |

The standard binds each event class to one or more FLLs and
defines the strictest visibility per role.

---

## 2 · Event class inventory

Events the timeline may carry (drawn from
`OPERATIONAL_TIMELINE_FOUNDATION.md` + Wave 1 substrate + ODR
addenda):

| Event class | Source |
|---|---|
| `odr_created` / `odr_submitted` / `odr_returned` / `odr_approved` | ODR lifecycle |
| `odr_amended` | Super+ amendment |
| `constraint_logged` / `constraint_recurring_flag` | Constraints substrate |
| `delay_logged` | ODR Section 7 |
| `extra_work_logged` | ODR Section 8 |
| `safety_event` | ODR Section 10 + Safety incidents |
| `inspection_completed` | Inspections module |
| `photo_uploaded` | ODR Section 12 |
| `material_event` | ODR Section 5.5 |
| `equipment_maintenance_flag` | ODR Section 4 |
| `dispatch_change` | Dispatch board |
| `weather_event` | NOAA / OpenWeather pull |
| `rfi_created` / `rfi_answered` | Future RFI |
| `schedule_change` | Future Schedule |
| `cost_exposure_flag` | Future PM cost overlay |
| `meeting_held` | Meetings |
| `training_completed` | Training |
| `pm_review_action` | Section 16 |

---

## 3 · Visibility matrix · per event × per FLL

Verbs: **show** · **scoped** · **summary** · **hide**.

| Event class | FLL-1 | FLL-2 | FLL-3 | FLL-4 | FLL-5 | FLL-6 |
|---|---|---|---|---|---|---|
| `odr_created` | scoped (own) | scoped (own crews) | show | show | hide | summary |
| `odr_submitted` | scoped (own) | scoped (own crews) | show | show | show | summary |
| `odr_returned` | scoped (own) | scoped (own crews) | show | show | show | summary |
| `odr_approved` | scoped (own) | scoped (own crews) | show | show | show | summary |
| `odr_amended` | scoped (own · only own amendments visible) | scoped (own crews) | show | show | show | summary |
| `constraint_logged` | scoped (own work area) | scoped (own crews' areas) | show | show | show | summary |
| `constraint_recurring_flag` | scoped (relevant to own work) | scoped | show | show | show | summary |
| `delay_logged` | scoped (own) | scoped (own crews) | show | show | show | summary |
| `extra_work_logged` | hide (claims discipline) | scoped (own crews) | show | show | show | summary |
| `safety_event` | scoped (own crew · today) | scoped (own crews) | show | show | show | summary |
| `inspection_completed` | scoped (own work area) | scoped (own crews) | show | show | show | summary |
| `photo_uploaded` | scoped (own ODR only) | scoped (own crews) | show | show | hide (low signal) | hide |
| `material_event` | scoped (own ODR) | scoped (own crews) | show | show | show | summary |
| `equipment_maintenance_flag` | scoped (own assets) | scoped (own crews) | show | show | show | summary |
| `dispatch_change` | scoped (today/tomorrow · own crew) | scoped (3-day · own crews) | show | show | show | summary |
| `weather_event` | show (own project) | show (own crews' projects) | show | show | show | summary |
| `rfi_created` (future) | hide | scoped (related to own work) | show | scoped (regional) | show | summary |
| `rfi_answered` (future) | hide | scoped (related to own work) | show | scoped (regional) | show | summary |
| `schedule_change` (future) | scoped (today/tomorrow only) | scoped (3-day) | show | scoped (regional resource conflicts) | show | summary |
| `cost_exposure_flag` (future) | hide | hide | hide | hide | show | summary |
| `meeting_held` | scoped (own meetings) | scoped (own crews) | show | show | show | summary |
| `training_completed` | scoped (own certs) | scoped (own crews) | show | show | hide | summary |
| `pm_review_action` | scoped (own ODR review only) | scoped (own crews' ODRs) | show | show | show | summary |

### Verb semantics

- **show** — event renders on the timeline with its standard text.
- **scoped** — event renders only when it pertains to the role's
  scope (own crew · own work area · own project · etc.).
- **summary** — events of this class roll up into a count / trend
  surface; individual rows do not appear.
- **hide** — event does not appear at all on this role's timeline.

---

## 4 · Density / loudness inheritance

The Wave 1.1A `timeline_calmness_probe.py` continues to enforce:

- `accent_class_ratio ≤ 0.0` (no enterprise colours)
- `badge_density ≤ 0.0` (no badges)
- `red_usage ≤ 1` (single-red rule)

Filtering by FLL **reduces** density, never increases it. The
calmness probe runs after the filter, so a denser-than-allowed
timeline is impossible.

---

## 5 · Implementation guidance (architectural, not code)

- Timeline reads are routed through a per-FLL **event filter
  function** at the projector layer.
- The filter is **pure** (event → bool per FLL · static rule set).
- A second function reduces "scoped" events to the role's row scope.
- The UI sidecar does not render events the filter rejected; it
  also does not show "(2 hidden events)" — silence is the contract.

---

## 6 · Doctrine anchors

| Doctrine | Anchor |
|---|---|
| V9 timeline 3 failures prevented | § 1 + § 3 matrix |
| V5 no cross-role leakage | § 3 strict per-FLL verb |
| V8 foreman today + tomorrow | § 3 dispatch_change + schedule_change rows |
| V11 SUMMARY never per-foreman | § 4 + FLL-6 summary verb |

_End of Timeline Role Visibility Standard._
