# Daily Report Evolution Plan · Strategic Pivot

_Phase V.1 · 2026-05-29 · master plan for the field-facing Daily Report uplift._

> **Operator directive (verbatim):** _"Stop treating ODR as a
> replacement form. Keep the current Daily Report workflow as the
> field-facing experience. Use the ODR architecture/substrate behind
> the scenes as the Operational Intelligence Layer. Make the existing
> Daily Report system elite without disrupting foremen."_

This document is the master plan that governs every downstream artifact
in the Daily Report Evolution wave. **Planning only. No implementation
until operator approves the exact upgrade scope.**

---

## 0 · Pivot summary (one paragraph)

The previous direction treated ODR as the **replacement form**.
That was wrong for the field. Foremen know "Daily Report." Asking
them to learn "ODR" is asking the wrong people to pay the cost.

The new direction: **Daily Report stays.** Foremen never see the
word ODR. The intelligence shipped between M0.1 and M1 — audience
projection, continuity IDs, photo governance, coaching engine,
public-link redaction, archive bridge, unified records projector,
operational linking, audit footer doctrine — **gets retargeted at
the existing Daily Report substrate** so the form they already use
becomes elite under the hood.

## 1 · 🔴 IMMEDIATE COLLISION · M1 freeze contradicts this pivot

M1 (closed today, before this pivot landed) shipped a hard write
freeze on the Daily Report endpoints:

| Endpoint | M1 state | Pivot need |
|---|---|---|
| `POST /api/daily-reports` | Returns `410 Gone` → redirects to `/odr/new` | ❌ Must be **restored** to working state — foremen file Daily Reports here |
| `DELETE /api/daily-reports/{id}` | Returns `410 Gone` | ✅ **Keep frozen** — historical records remain immutable |

**Recommended action (NOT executed without operator approval):**
Restore `POST /api/daily-reports` to its original working
implementation (the original body is preserved in
`_legacy_create_daily_report_archived` for a clean 4-line revert).
Keep the `DELETE` freeze in place — historical preservation is
still desired.

**Why this matters:** under this pivot, M1's "freeze writes + force
ODR" is operationally incorrect. The freeze must be partially
rolled back **before any foreman tries to file a report.**

Awaiting operator authorization to execute the revert.

## 2 · What we KEEP from existing ODR work (reused as substrate)

These are not thrown away — they get retargeted at the Daily Report
substrate. Each one becomes a **silent enhancement** the foreman
never has to think about.

| ODR asset | How it powers Daily Reports going forward |
|---|---|
| `operational_links` substrate | Daily Report ↔ photo ↔ constraint ↔ activity cross-references |
| Operational timeline | "All recent project records" timeline (already mixed-substrate via unified projector) |
| Audience projection (M0.4) | Daily Report PDF audience modes (foreman / pm / executive / external) |
| Public/external PDF redaction | DR external PDFs strip foreman_uid / GPS / device meta (currently DR PDFs leak some of this) |
| Continuity IDs (`DR-YYYY-NNNNN`) | Already in place; no change |
| Photo governance (job_photos library) | DR photos remain indexed there; new linkage adds tag/context |
| Archive system | Past signed DRs treated as canonical; archive badge already designed |
| Unified operational records projector | One dashboard already exists at `/operational-records` |
| Role-aware visibility | Same `FLL` verb dispatch can adorn the existing DR list |
| Low/no signal support | Existing Phase J idempotent submit + photo upload retry |
| Device recognition | Existing device-fingerprint already on file |
| Auto-save | Existing Daily Report draft auto-save; strengthen but do not replace |
| Draft recovery | Existing recover-on-mount logic; strengthen |
| Offline queue foundation | Existing photo retry queue; document the contract |
| Coaching / guidance engine (OGC 14 keys) | Retargeted at DR sections — same EN/ES coaching, new form |
| PDF SHA / audit footer doctrine | Backported to the DR PDF renderer (currently no SHA footer on DR PDFs) |
| Platform inheritance doctrine (Lock #2) | Governs every DR-side change going forward |
| Simplicity doctrine (Lock #1) | Same field test applies — "mud, gloves, 5:30 PM" |

**Net:** ~16 substrate assets get reused. Almost nothing is thrown away.

## 3 · What we ADD to the Daily Report form

Only what the current report is genuinely missing. Every addition is
governed by the Simplicity Test — if it makes the report harder, it
moves to PM/Super or auto-populates.

| # | Capability | Current state | New state |
|---|---|---|---|
| 1 | **Production Quantities** | Free-text `activities[].quantity` (rare) | Structured rows: closed `unit` ∈ {LF_pipe, CY_concrete, tons_asphalt, SY_grading, SY_milling, LF_curb, custom} + station_range + notes |
| 2 | **Constraint / Delay Tracking** | `schedule_delays: "Yes"/"No"` string | Structured rows: closed `delay_type` ∈ 11 types + hours_lost + description |
| 3 | **Activity / Work Area Tracking** | Free-text `activities[]` | Structured rows: `work_activity` + station/location + status ∈ {started, continued, completed} + affected crew + affected equipment |
| 4 | **RFI-ready flag** | Absent | Boolean `may_require_rfi` (advisory only — no RFI creation yet) |
| 5 | **Schedule-impact flag** | Absent | Boolean `may_affect_schedule` (advisory only — no schedule work yet) |
| 6 | **Better photo linkage** | `photos[]` → strings | Each photo gets `linked_to ∈ {production_row_id, constraint_row_id, activity_row_id, general}` + tag |

**Detail for each gap lives in:**
- `DAILY_REPORT_PRODUCTION_TRACKING_DESIGN.md`
- `DAILY_REPORT_CONSTRAINT_TRACKING_DESIGN.md`
- (Activity tracking is documented inside the production design doc; constraint and activity share many shape patterns)

## 4 · The field-facing flow MUST stay this exact shape

Per directive, the foreman experience MUST remain:

```
Project → Crew → Equipment → Production → Photos → Issues/Delays → Safety → Sign → Submit
```

| Step | Foreman action | Substrate intelligence in background |
|---|---|---|
| Project | One tap (auto-detected from device + last shift) | Continuity ID stays consistent |
| Crew | One tap (last-used roster · editable) | Crew-type inference for coaching |
| Equipment | One tap (last-used set · editable) | Equipment lookup from dispatch |
| **Production** | Pick a unit + enter qty + optional station | OGC coaching loads for unit type |
| Photos | Tap, voice-caption, done | Auto-link to nearest production/constraint row |
| **Issues/Delays** | Tap a chip (weather, utility, MOT…) + hours + free-text | Constraint type maps to operational_links semantics |
| Safety | "Any incident today?" → Y/N + brief notes | Same as current |
| Sign | Standard signature pad | Same as current |
| Submit | One tap | Idempotent + offline queue + audit footer |

The form has **9 steps** (the current ceiling per Simplicity Doctrine).
We are not adding a 10th. Every "ADD" in §3 lands inside an existing
step, not as a new step.

## 5 · Target completion time

| Bound | Value | Current measured | After elite upgrade target |
|---|---|---|---|
| Stretch goal | < 3 min | not measured at scale | < 3 min held |
| Target | < 5 min | ~5 min (sample n=8) | < 5 min held |
| Hard ceiling | 7 min | not breached | not breached |

**The platform may become more intelligent. The foreman experience
must become simpler.** This is the same compounding rule from
Doctrine Lock #1. Every release of the elite upgrade must hold or
reduce foreman completion time.

## 6 · Low / no signal contract (must work · no pilot without it)

| Capability | Status today | Elite target |
|---|---|---|
| Auto-save (per field) | Present | Strengthen · 2 s debounce · per-step JSON snapshot |
| Draft recovery | Present | Strengthen · resume from last step · show "you left off here" |
| Idempotent submit | Present (Phase J) | Document the contract |
| Photo retry queue | Present | Document with retry policy + max age + UI surface |
| Device recognition | Present | Document the device fingerprint flow |
| Offline POST queue | Partial | Document end-to-end contract + recovery UI |
| No lost report after crash | Partial | Test with browser kill mid-step |
| No lost report after weak signal | Partial | Test with throttled network |

Detail in `DAILY_REPORT_OFFLINE_RECOVERY_PLAN.md`.

## 7 · What we DO NOT do (per directive)

| Forbidden | Status |
|---|---|
| Replace Daily Reports with a separate ODR form | ❌ NEVER |
| Migrate historical reports | ❌ |
| Rewrite signed reports | ❌ |
| Make foremen dual-enter | ❌ |
| Add dashboard bloat | ❌ |
| Start RFI | ❌ |
| Start Schedule | ❌ |
| Start P6 | ❌ |
| Start production deploy | ❌ |

## 8 · Implementation readiness · pre-build checklist

Before the operator gives the green light to build, the following
artifacts must all be ✅ and reviewed:

| Artifact | Status |
|---|---|
| `DAILY_REPORT_EVOLUTION_PLAN.md` (this) | ✅ |
| `DAILY_REPORT_FIELD_SIMPLICITY_CERTIFICATION.md` | ✅ |
| `DAILY_REPORT_PRODUCTION_TRACKING_DESIGN.md` | ✅ |
| `DAILY_REPORT_CONSTRAINT_TRACKING_DESIGN.md` | ✅ |
| `DAILY_REPORT_OFFLINE_RECOVERY_PLAN.md` | ✅ |
| `ODR_SUBSTRATE_REUSE_MAP.md` | ✅ |
| `DAILY_REPORT_ELITE_UPGRADE_OPERATOR_REVIEW.md` | ✅ |
| Operator approval of M1 freeze partial-revert (POST only) | ⏳ awaiting |
| Operator approval of build scope (which of the 6 ADDs in §3 to ship in wave 1) | ⏳ awaiting |
| Operator approval of low/no-signal contract | ⏳ awaiting |

## 9 · Stop condition

🛑 **HALTED at end of planning.**

Per directive: _"Stop after planning and implementation-readiness
review. Do not begin build until operator approves the exact upgrade
scope."_

The 7 docs are the complete planning surface. Awaiting operator
review and the build authorization that names which capabilities
ship in the first upgrade wave.

---

_End of DAILY_REPORT_EVOLUTION_PLAN.md._
