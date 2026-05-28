# Phase V-Prelude Implementation Plan

_Phase V-Prelude · Master sequencing doc · 2026-05-28._

## Mission

Translate the 9 V-Prelude doctrine docs into 4 sequenced waves.
Each wave is independently shippable, independently reversible,
and gated by the same OPS-1 + probe + regression discipline that
got us here.

**This plan is operator-paced.** No wave begins without explicit
"start V-Prelude wave N" command.

## Doctrine constraints (recap)

- 🚫 PREVIEW ONLY · no production deploy without operator hand
- 🚫 NO RFI / Schedule / CPM work in this phase
- 🚫 NO enterprise dashboard bloat
- 🚫 NO AI features
- 🚫 NO new colors / fonts / icons beyond the existing palette
- 🟢 Every change individually reversible
- 🟢 Every change governance-protected (probe + tests)
- 🟢 OPS-1 stays GREEN throughout
- 🟢 Calm > clever

## Waves

### Wave 1 — Substrate (Constraints + Timeline + Photo Gov)
**Priorities covered:** #1 (Constraints) · #3 (Photo Gov) · #8 (Timeline substrate)
**Code surface:**
- Backend: `routes/constraints.py` · `routes/photos.py` extensions ·
  `routes/timeline.py` · `routes/operational_links.py`
- Frontend: `pages/Constraints.jsx` · `pages/ConstraintDetail.jsx` ·
  Photo group view extension · Chronology panel component
- Capability primitives: `constraintCapabilities.js` ·
  `photoCapabilities.js` · `timelineCapabilities.js`
**Estimated LOC:** ~1,800 (backend) · ~1,400 (frontend) ·
~400 (tests).
**Gates:**
- 🟢 Authority Mismatch Probe clean (new primitives allowlisted)
- 🟢 Timestamp Doctrine Probe clean
- 🟢 OPS-1 page green (3 new surfaces register in trust_surfaces)
- 🟢 Capability tests: 4/4 per primitive

### Wave 2 — Discovery (Search + Field Memory)
**Priorities covered:** #2 (Search) · #7 (Field Memory)
**Code surface:**
- Backend: `routes/search.py` · Mongo text-index migration ·
  `routes/field_memory.py`
- Frontend: search overlay component · field-memory panel
  component
- Capability primitive: `searchCapabilities.js`
**Estimated LOC:** ~1,000 (backend) · ~800 (frontend) ·
~300 (tests).
**Gates:**
- 🟢 Search p95 < 200 ms with 5,000 records per collection
- 🟢 `_id` leak contract still passes (10/10)
- 🟢 Field memory endpoint returns 0 PII (regression test)

### Wave 3 — Resilience (Offline Drafts + Mobile Polish)
**Priorities covered:** #4 (Offline Resilience) · #5 (Mobile UX)
**Code surface:**
- Backend: extends existing draft-telemetry endpoint to count
  new draft kinds
- Frontend: extends `lib/idbDraft.js` to support constraint +
  field-note kinds; applies the 10 polish items from the audit
**Estimated LOC:** ~400 (frontend mostly) · ~150 (tests).
**Gates:**
- 🟢 TRUST-1 final hardening suite still 6/6
- 🟢 Draft Health admin tile shows all draft kinds
- 🟢 Mobile audit re-run: 12/12 surfaces still 🟢

### Wave 4 — Self-Healing (5 new probes)
**Priorities covered:** #9 (Self-Healing) · also closes the
governance loop for waves 1-3
**Code surface:**
- `scripts/terminology_doctrine_probe.py` (P1)
- `scripts/ops1_drift_sentinel.py` (P5)
- `scripts/token_scope_leak_probe.py` (P4)
- `scripts/contamination_probe.py` (P2)
- `scripts/hierarchy_validation_probe.py` (P3)
- All 5 wired into `pre_deploy_check.sh`
**Estimated LOC:** ~1,100 (probes) · ~500 (tests).
**Gates:**
- 🟢 Each probe sub-3-second
- 🟢 Each probe has a regression test in `tests/pw_suite/`
- 🟢 OPS-1 stanza for P1 / P2 / P4

## Total scope estimate

- **Backend:** ~3,000 LOC
- **Frontend:** ~2,600 LOC
- **Tests:** ~1,500 LOC
- **Doctrine docs:** already shipped (this batch)

## Sequencing rules

1. Wave 1 MUST land first (substrate · others depend on it).
2. Wave 2 can land in parallel with Wave 3 IF operator approves.
3. Wave 4 lands LAST so it gates the new code Wave 1-3 added.
4. Each wave is its own deploy. No multi-wave deploys.

## Per-wave doctrine checklist (each wave must satisfy ALL)

- [ ] Preview-only · no production mutation
- [ ] Authority Mismatch Probe stays at 0 new violations
- [ ] Timestamp Doctrine Probe stays at 0 new violations
- [ ] OPS-1 page stays GREEN
- [ ] All new operator-facing timestamps use `dateUtils.js` helpers
- [ ] All new capability primitives have explicit FL lockdown
- [ ] All new surfaces register in `trust_surfaces.json`
- [ ] All new surfaces register in `SHARED_SURFACE_CONTEXT_MATRIX.json`
- [ ] All new endpoints exclude Mongo `_id`
- [ ] All new endpoints admin-authenticated where appropriate
- [ ] Mobile audit (12 surfaces) still 🟢 at 390 × 844
- [ ] Capability primitive regression tests pass
- [ ] Field walks dry-run on at least the FL checklist

## Stop condition

This plan is the master sequence. No wave begins without explicit
"start V-Prelude wave N" command from the operator.

## Phase V handoff

Phase V.1 RFI MVP begins after **all four V-Prelude waves
complete + 72-h post-V4-deploy observation closes clean**. The
operator-paced gate is the same as the original V.1 unlock
gate, now extended by the V-Prelude waves.

## Approval needed (operator)

Per the directive: "STOP after Phase V-Prelude deliverables and
implementation planning. Await operator review before major
implementation begins."

Pending operator decisions:
1. 🔵 Approve / amend the 4-wave sequence above
2. 🔵 Decide whether Waves 2 + 3 ship in parallel or strictly
   sequential
3. 🔵 Decide which Wave 4 probes are required vs nice-to-have
4. 🔵 Choose preview observation window length between waves
   (recommended: 24 h)
5. 🔵 Confirm the Phase V.1 RFI unlock gate is still bound to
   72-h post-V4 observation

Once approved, the agent begins Wave 1 on explicit "start
V-Prelude wave 1" command in a fresh chat.
