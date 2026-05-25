# PHASE18_OPERATIONAL_UNIFICATION_TRACKER.md
**Phase 18 · iter414 · 2026-05-25**

## Mission
Surgical operational refinement and convergence lock after the Phase 17 audit series. The platform shall feel like **ONE operational operating system** — same look, sound, teach, and flow across every portal.

This is **NOT** a build phase. This is a coherence-lock phase.

## 25-point Pre-implementation Gate (Phase 18 directive)
All 25 criteria verified for every surgical fix proposed in this phase. **Any "no" answer → redesign before code.**

| # | Criterion | Status |
|---:|---|:---:|
| 1  | Preserve operational calmness | ✅ |
| 2  | Preserve operational trust | ✅ |
| 3  | Preserve role discipline | ✅ |
| 4  | Preserve downstream continuity | ✅ |
| 5  | Preserve platform convergence | ✅ |
| 6  | Preserve bilingual integrity | ✅ |
| 7  | Preserve visual consistency | ✅ |
| 8  | Preserve operational cognition | ✅ |
| 9  | Avoid ERP behavior | ✅ |
| 10 | Avoid analytics drift | ✅ |
| 11 | Avoid dashboard sprawl | ✅ |
| 12 | Avoid feature creep | ✅ |
| 13 | Preserve mobile-first usability | ✅ |
| 14 | Preserve low cognitive load | ✅ |
| 15 | Improve operational clarity | ✅ |
| 16 | Strengthen operational flow | ✅ |
| 17 | Preserve operational honesty | ✅ |
| 18 | Preserve assignment continuity | ✅ |
| 19 | Preserve operational memory | ✅ |
| 20 | Preserve cross-portal awareness | ✅ |
| 21 | Preserve guidance consistency | ✅ |
| 22 | Preserve help-search continuity | ⚠️ → Phase 18 fix (no DLS articles in guidance) |
| 23 | Preserve LifecycleGuide continuity | ✅ |
| 24 | Would operations instantly understand? | ✅ |
| 25 | Align with foundational doctrine | ✅ |

## Hard-evidence baseline (captured 2026-05-25)
| Signal | Measurement |
|---|---|
| Backend parity-lock | **130 / 130 PASS** |
| Operator vocabulary scanner | 16 T1 (all `iter###` source-comments · expected) · **0 T2/T3** |
| Touch-target audit | **Clean** |
| ESLint / Ruff | Clean across Phase 12-17 files |
| Frontend routes | 234 |
| i18n keys | 3,526 EN→ES |
| DispatchHub.jsx LOC | 559 (refactor candidate) |
| AssignmentCreateDrawer.jsx LOC | 806 (refactor candidate) |
| server.py LOC | 11,246 · 16 `/api/legacy-imports/*` occurrences |
| Guidance articles for Phase 14-17 DLS surfaces | **0** (gap surfaced) |

## Phase 18 surgical scope (priority-ordered)

### P0 — **Help-search continuity (criterion #22)**
Phase 14-17 introduced 7 new operational surfaces with **zero** corresponding Guidance Center articles. Search for "tanker haul", "equipment move", "QR shift start", "haul activity", "health summary", "operational attention", "DLS lifecycle" returns nothing. **Fix scope**: add DLS article slugs to `guidance/content.py` + EN/ES translation packs. **Non-destructive.** Captured in `HELP_SEARCH_AND_GLOSSARY_LOCK.md`.

### P1 — **Legacy chrome alignment for top-friction forms**
Daily Report Builder + Inspections + Incidents + Equipment Pre-Op retain pre-Phase-12 chrome. Per Phase 17 directive: **defer until Day-1 debrief names which actually cost ops time**. Phase 18 captures the modernization matrix but does NOT execute it pre-debrief. Captured in `LEGACY_MODERNIZATION_MATRIX.md`.

### P1 — **EN ↔ ES gap closure on legacy validation messages**
Form validation error strings on older Safety/HR forms surface in English regardless of `masci.lang`. ~30 untranslated strings identified. **Fix scope**: add i18n keys + wrap legacy form validators in `useT()`. Captured in `EN_ES_HARDENING_MATRIX.md`.

### P2 — **Component extraction (DispatchHub.jsx + AssignmentCreateDrawer.jsx)**
Both files exceed 500 LOC. Extract sub-components into `/components/dispatch/hub/parts/` and `/components/dispatch/drawer/parts/` **with behavior-preserving guarantee** (same imports, same testids, same DOM tree).

### P3 — **server.py Phase 4D extractions**
`/api/legacy-imports/*` (16 occurrences) extract to dedicated module. Pure refactor.

### P3 — **`dispatch_driver_sessions` reaper** (Phase 17 dead-end audit observation #1)
Stale session reaper script for forgotten driver sign-out. Defer until Day-1 actually surfaces frequency.

## Restraint discipline locked
- ❌ No new collections
- ❌ No new write endpoints
- ❌ No new dashboards / charts / analytics / maps / GPS / route optimization
- ❌ No payroll · ERP · productivity scoring · telematics · surveillance
- ❌ No giant admin systems
- ❌ No role expansion (Safety/FL/HR stay quiet on DLS)
- ❌ No Motive activation (validate-don't-surveil future architecture)

## Required outputs (this phase)
- ✅ `PHASE18_OPERATIONAL_UNIFICATION_TRACKER.md` (this file)
- ✅ `LEGACY_MODERNIZATION_MATRIX.md`
- ✅ `EN_ES_HARDENING_MATRIX.md`
- ✅ `ROLE_DISCIPLINE_LOCK_AUDIT.md`
- ✅ `OPERATIONAL_DEAD_END_RECHECK.md`
- ✅ `CROSS_PORTAL_CONTINUITY_RECHECK.md`
- ✅ `MOBILE_FIRST_LOCK_REPORT.md`
- ✅ `HELP_SEARCH_AND_GLOSSARY_LOCK.md`

## Success condition
Phase 18 will be COMPLETE when:
1. All 8 audit memos above ship with evidence.
2. The P0 help-search gap is closed (DLS articles searchable EN+ES).
3. Parity-lock remains 130/130 PASS.
4. Vocabulary scanner remains 0 T2/T3.
5. Touch-target audit remains clean.
6. Lint remains clean.
7. The Day-1 debrief mechanism is unblocked (drivers run, dispatch issues, PM sees, debrief filed).

## Verdict
**Phase 18 in progress — see siblings for per-axis evidence.**
