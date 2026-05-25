# PHASE19_FINAL_REMEDIATION_PRIORITY.md
**Phase 19 · iter415 · 2026-05-25 · Final Ranked Backlog**

The final prioritized remediation list across all 14 sibling Phase 19 audit deliverables. Restraint-first prioritization.

## Priority schema
- **P0 — operational risk** (the platform doesn't work for someone today)
- **P1 — cognition risk** (real ops can't figure out what to do · likely to slow work)
- **P2 — continuity drift** (gap that won't break ops but compounds over weeks)
- **P3 — cleanup / refactor only** (zero operational consequence)

**Every P0/P1 item is also gated on the Day-1 debrief actually naming it.** Phase 19 doctrine prohibits speculation-driven prioritization.

---

## 🚨 P0 · OPERATIONAL RISK · 0 items
**No P0 items found.** Platform passes Day-1 readiness. ✅

---

## 🟡 P1 · COGNITION RISK · 1 item (with caveat)

### P1.1 — Day-1 Live Ops Debrief filing
**Source**: Doctrine itself.
**Risk**: Without the debrief filed same-day, every P2/P3 item below becomes speculation-driven and loses doctrine grounding.
**Owner**: Operations leadership (not engineering).
**Effort**: 10 questions · ~30 min · template at `/app/memory/DLS_DAY1_LIVE_OPS_DEBRIEF.md`.
**Action**: Run Day-1 · capture answers · file as `DLS_DAY1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md`.

---

## 🟠 P2 · CONTINUITY DRIFT · 9 items (all gated on Day-1 demand)

### P2.1 — Add `dls-assignment-cancel` guidance article + in-flow link
**Source**: `HELP_SEARCH_COVERAGE_GAPS.md`
**Risk**: Dispatchers needing to cancel/undo an issuance have no guidance.
**Effort**: 1 article (EN + ES) + 1 in-flow link on DispatchHub.
**Pattern**: same as iter414 article shipping.

### P2.2 — Add `dls-magic-link-help` guidance article
**Source**: `HELP_SEARCH_COVERAGE_GAPS.md`
**Risk**: Drivers losing their magic-link have no self-help path.
**Effort**: 1 public-scope article (EN + ES).

### P2.3 — Add coaching for mid-shift reassignment
**Source**: `OPERATIONAL_ASSUMPTION_AUDIT.md` item #3 · `OPERATIONAL_COGNITION_HEATMAP.md` rank #1
**Risk**: Dispatcher hesitates when needing to swap driver/truck mid-haul.
**Effort**: 1 DispatchHub bullet (1-line) OR add to `dls-assignment-issuance` article + new in-flow link.

### P2.4 — "Add temporary" memory-feedback tooltip
**Source**: `OPERATIONAL_ASSUMPTION_AUDIT.md` item #12
**Risk**: Dispatcher worries about creating master records when typing once.
**Effort**: 1-line tooltip on SearchableSelect "Add temporary" affordance.

### P2.5 — DispatchBoard row-tap drawer in-flow help link
**Source**: `OPERATIONAL_COGNITION_HEATMAP.md` rank #6 · `PHASE18_1_INFLOW_COACHING_LOG.md` deferred item
**Risk**: Dispatcher staring at a stuck truck has no quick "what does this mean?" link.
**Effort**: 1 HelpLink insertion in AssignmentDrawer.jsx → `/guidance/dls-lifecycle-states`.

### P2.6 — Legacy form validation ES wrap
**Source**: `BILINGUAL_OPERATIONAL_MEANING_AUDIT.md` Gap 1
**Risk**: Spanish-preferring crew gets stuck on EN-only required-field error messages.
**Modules**: Daily Report · Inspections · Incidents · Equipment Pre-Op · DVIR · Weekly Lead · Weekly Emergency.
**Effort**: `useT()` wrap on ~30 validation strings + add to `i18n.js`.

### P2.7 — Translate 3 high-frequency `task-*` ES articles
**Source**: `TRAINING_SYSTEM_AUDIT.md` Gap 2
**Articles**: `task-submit-incident` · `task-upload-photos` · `task-verify-time`.
**Effort**: extend `translations_es_iter414.py` (or new iter file) with 3 article entries.

### P2.8 — Legacy chrome modernization (one module at a time)
**Source**: `LEGACY_SYSTEM_DRIFT_AUDIT.md`
**Risk**: Pre-Phase-12 chrome on Daily Report · Inspections · Incidents · Safety detail · HR Time/Training.
**Effort**: ~150-300 LOC per module · 5-step recipe documented.
**Gate**: **DO NOT batch.** Pick the module Day-1 names. Don't speculate.

### P2.9 — Stale `dispatch_driver_sessions` reaper
**Source**: `OPERATIONAL_DEAD_END_RECHECK.md` (iter413) carried forward
**Risk**: Forgotten driver sign-out leaves stale sessions in `active_shifts` count.
**Effort**: Nightly script + admin "Reaped sessions" log entry.
**Gate**: Defer until Day-1 surfaces frequency.

---

## 🔵 P3 · CLEANUP / REFACTOR ONLY · 7 items

### P3.1 — Translate 5 `role-*` stub articles to ES
**Effort**: extend ES iter file.

### P3.2 — Translate 3 `tshoot-*` edge-path articles to ES
**Effort**: extend ES iter file.

### P3.3 — Close 9 `role-*` articles missing "what next" closing block
**Effort**: add `{"type": "next", ...}` to each.

### P3.4 — Add `dls-operational-memory` guidance article
**Effort**: 1 article (EN + ES).

### P3.5 — `DispatchHub.jsx` (559 LOC) + `AssignmentCreateDrawer.jsx` (806 LOC) component extraction
**Risk**: Pure maintainability · zero operational risk.
**Effort**: extract sub-components into `/components/dispatch/hub/parts/` and `/components/dispatch/drawer/parts/` with behavior-preserving guarantee.

### P3.6 — `server.py` Phase 4D extractions
**Effort**: Move `/api/legacy-imports/*` (16 occurrences) into dedicated module.
**Risk**: Pure maintainability.

### P3.7 — 233 inherited pytest isolation failures
**Effort**: `conftest.py` teardown audit · fixture state-leakage hunt.
**Risk**: None for production · CI hygiene only.
**Gate**: Lowest priority · explicit user directive to defer.

### P3.8 — Reassignment-during-WAITING UX shortcut
**Source**: `OPERATIONAL_DEAD_END_RECHECK.md`
**Risk**: One-tap "reassign while waiting" UX would be nicer than walking the state machine.
**Effort**: medium · backend + UI.
**Gate**: Defer until Day-1 surfaces friction.

---

## Items explicitly NOT on this backlog (anti-scope)
- ❌ Adding dashboards / charts / analytics / KPIs anywhere
- ❌ Adding maps / GPS / route optimization
- ❌ Activating Motive surveillance
- ❌ Building onboarding wizards / tutorial systems
- ❌ Expanding Safety/HR/FL DLS visibility (held until 14-day post-live-ops review)
- ❌ Adding any new write surfaces to PM
- ❌ Adding scoring / ratings / performance metrics

---

## Phase 19 verdict
- **🟢 Platform is Day-1 ready.**
- **9 P2 items** all gated on Day-1 demand · doctrine-aligned.
- **7 P3 items** are pure cleanup · execute when convenient.
- **0 P0 / 1 P1 (the debrief itself)** — no operational risk shipping the platform now.

**Run Day-1. File debrief same-day. Surgical pickup follows.**
