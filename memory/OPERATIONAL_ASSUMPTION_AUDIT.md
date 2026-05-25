# OPERATIONAL_ASSUMPTION_AUDIT.md
**Phase 19 · iter415 · 2026-05-25**

Surfaces where the platform assumes operational knowledge the user may not have. Closing these assumptions is a P2-grade win — not P0, because no surface is broken, just leaning on prior context.

## High-risk assumption inventory

### 1. Wait states
**Surfaces affected**: Driver lifecycle UI · Dispatch board wait-state rendering · governance findings.
**Assumption made**: User knows `WAIT_ON_PLANT` vs `WAIT_ON_DUMP` vs `BREAKDOWN` vs `WAITING_OTHER` and when each applies.
**Coaching status**: ✅ iter414 `dls-lifecycle-states` article explains all 4 + the canonical-not-free-text doctrine. In-flow link from DispatchHub Operational Attention reaches it via `dls-operational-attention` related-article.
**Risk**: Medium. Driver picking the wrong wait reason quietly corrupts governance.
**Closure**: Article is searchable EN+ES (verified iter414). **No fix needed.**

### 2. Tanker continuity
**Surfaces affected**: Drawer Tanker mode (iter410) · health summary · PM tile.
**Assumption made**: User knows what `liquid_product` field is for, and that selecting a tanker terminal vs a plant matters operationally.
**Coaching status**: ✅ iter414 `dls-haul-types` article carries Tanker bullet · Drawer has inline coaching strip.
**Risk**: Low. The 27-item catalog dropdown is self-documenting via category badges.
**Closure**: **No fix needed.**

### 3. Reassignment logic
**Surfaces affected**: Dispatch board (when dispatch needs to change driver/truck on an active assignment).
**Assumption made**: User knows dispatch can reassign by walking the state machine back; cannot in-place edit assignment fields.
**Coaching status**: ⚠️ Not explicitly coached. The directive iter392 doctrine doc covers it but operators may not have read it.
**Risk**: Medium. Could cause hesitation if a dispatcher wants to swap drivers mid-haul.
**Closure recommendation**: 🟠 **P2** — Add 1-line note in DispatchHub Command bullets: "Reassignments walk the state machine — don't in-place edit." Or add a guidance article `dls-reassignment`. Defer until Day-1 names it.

### 4. Lifecycle states
**Surfaces affected**: Driver lifecycle UI · board rendering.
**Assumption made**: User knows ASSIGNED → ENROUTE_TO_LOAD → AT_LOAD → ENROUTE_TO_DUMP → AT_DUMP → COMPLETE.
**Coaching status**: ✅ iter414 `dls-lifecycle-states` explains every state. Bilingual.
**Risk**: Low. State buttons in driver UI are big and labeled clearly.
**Closure**: **No fix needed.**

### 5. PM haul visibility
**Surfaces affected**: PM hub PmHaulActivityTile (iter409).
**Assumption made**: PM understands they see ONLY their assigned projects + the tile is read-only.
**Coaching status**: ✅ iter414 `dls-haul-activity-tile` article + iter409 tile carries "production awareness · read-only" pill + iter414 in-flow link.
**Risk**: Low.
**Closure**: **No fix needed.**

### 6. Breakdown continuity
**Surfaces affected**: Driver BREAKDOWN tap · Shop tile · Dispatch Operational Attention · PM tile.
**Assumption made**: User knows tapping BREAKDOWN fans out to 3 portals simultaneously.
**Coaching status**: ✅ `dls-lifecycle-states` covers it · `dls-operational-attention` repeats it · `dls-haul-activity-tile` mentions breakdown_impacts.
**Risk**: Low.
**Closure**: **No fix needed.**

### 7. Operational Attention
**Surfaces affected**: DispatchHub iter411 section.
**Assumption made**: Dispatcher knows what counts as "attention" vs "normal".
**Coaching status**: ✅ iter414 `dls-operational-attention` article + iter414 in-flow link.
**Risk**: Low.
**Closure**: **No fix needed.**

### 8. Governance findings
**Surfaces affected**: `/api/dispatch/governance/findings` consumers · iter411 Attention cards.
**Assumption made**: User knows findings are computed, not authored — they cannot manually clear one.
**Coaching status**: ✅ Findings only disappear when the underlying state changes. Coached in iter395 doc but not in-flow.
**Risk**: Low. Findings auto-clear is intuitive.
**Closure**: **No fix needed.**

### 9. Health Summary
**Surfaces affected**: Admin-only `/api/admin/dls/health-summary`.
**Assumption made**: Ops leadership knows what `quiet`/`flowing`/`attention` mean and the 3-call cadence (morning · 11 AM · EOD).
**Coaching status**: ✅ iter414 `dls-health-summary` article documents it + Day-1 Debrief doc references it.
**Risk**: Low.
**Closure**: **No fix needed.**

### 10. Shift start doctrine
**Surfaces affected**: `/shift` · QR sticker.
**Assumption made**: Driver understands no-password, no-app, no-enrollment is intentional (not a missing feature).
**Coaching status**: ✅ ShiftStart has subtitle + iter414 in-flow link to `dls-driver-shift-start`. QR sticker prints bilingual instructions.
**Risk**: Low.
**Closure**: **No fix needed.**

### 11. Assignment issuance
**Surfaces affected**: DispatchHub Issue Work · Drawer.
**Assumption made**: Dispatcher knows truck is required, driver optional.
**Coaching status**: ✅ Drawer carries inline orange coaching strip · iter414 link to `dls-assignment-issuance`.
**Risk**: Low.
**Closure**: **No fix needed.**

### 12. Temporary operational records
**Surfaces affected**: Drawer "Add temporary" affordance · ShiftStart "Add temporary driver/truck".
**Assumption made**: User knows typing custom values isn't an admin asset-creation event — it's operational memory that surfaces in the next assignment.
**Coaching status**: 🟡 Drawer says "Add temporary" but doesn't explain the memory-feedback loop.
**Risk**: Medium. Dispatcher may worry about creating master records vs typing once.
**Closure recommendation**: 🟠 **P2** — Add 1-line tooltip on the SearchableSelect "Add temporary" affordance: "Surfaces as 'history' next time. No admin record created." Or add to inline coaching. Defer until Day-1.

### 13. Operational memory
**Surfaces affected**: Lookups feeding drawer dropdowns.
**Assumption made**: Dispatchers know the platform learns from past assignments.
**Coaching status**: 🟡 Implicit · not documented for end-users.
**Risk**: Low. The feature works without users needing to understand it.
**Closure**: **No fix needed.**

### 14. Follow-through doctrine
**Surfaces affected**: DispatchHub Follow-Through section (transfers + holds).
**Assumption made**: Dispatcher knows when to use HOLD vs TRANSFER (covered in iter411 portal-dispatch article).
**Coaching status**: ✅ `dispatch-holds-transfers` article in guidance · iter411 sub-tabs.
**Risk**: Low.
**Closure**: **No fix needed.**

## Additional assumptions discovered during audit

### 15. Cross-portal token isolation
**Where**: Multi-portal directory + admin token vs Dispatch/PM/Shop/Safety/HR tokens.
**Assumption**: Admin sees everything; per-portal tokens do not cross-grant.
**Coaching**: ✅ `portal-admin` + multi-portal sign-in helpers · `EnforcePortalScope` clears tokens on route change.
**Risk**: Low.

### 16. Safety doctrine-quietness on DLS
**Where**: Safety pages don't show DLS tiles.
**Assumption**: Safety leadership understands this is intentional, not missing.
**Coaching**: 🟡 Documented in `ROLE_DISCIPLINE_LOCK_AUDIT.md` but not in `portal-safety` article.
**Risk**: Low. Safety doesn't notice what they don't see.
**Closure**: **No fix needed pre-Day-1.** Revisit at 14-day post-live-ops review.

## Verdict
**14 of 16 operational assumptions are well-coached.** 2 are partially coached and surfaced as P2 backlog (`reassignment logic` + `temporary operational records`). Neither blocks Day-1.
