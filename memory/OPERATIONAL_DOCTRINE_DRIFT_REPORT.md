# OPERATIONAL_DOCTRINE_DRIFT_REPORT.md
**Phase 19 · iter415 · 2026-05-25**

Audits the platform for ANY drift toward ERP behavior · analytics behavior · dashboard sprawl · software terminology · management-suite behavior · surveillance behavior · role creep · operational clutter.

## Verdict
**🟢 ZERO doctrine drift detected.** Every restraint dimension holds.

## Drift dimensions audited

### 1. ERP behavior drift
**Sought**: workflow-engine chrome · approval-chain UIs · multi-step wizards · "Submit for approval" buttons everywhere · finance/accounting features.
**Found**: NONE. The platform is workflow-aware (assignment → lifecycle → cycle) but never workflow-engine. No approval chains. No "Wait for manager sign-off" gates. No invoicing. No PO workflow trees.
**Evidence**: 0 hits in scanner for "approval", "workflow engine", "wizard step", etc. PO Requests exists but is operationally minimal (request · admin acts manually).
**Status**: ✅ **No drift**

### 2. Analytics behavior drift
**Sought**: charts · graphs · KPI dashboards · trend lines · year-over-year comparisons · executive scorecards.
**Found**: NONE. The platform shows counts (e.g., `loads_completed_today`) but NEVER scores, percentages, or trends.
**Evidence**: zero `<canvas>` or chart libraries in `package.json`. iter412 health summary uses 3 words (quiet/flowing/attention), not numbers, as primary signal.
**Status**: ✅ **No drift**

### 3. Dashboard sprawl drift
**Sought**: 10+ tiles per portal · metric overload · "More stats" sub-tabs · executive overview pages.
**Found**: NONE. iter411 Dispatch Command portal capped at 7 sections. PM hub: 2 tiles (iter409 + iter396). Shop: 1 DLS tile. Each portal is bounded.
**Evidence**: grep `<Tile` / `<Stat` density per page · all within bounds.
**Status**: ✅ **No drift**

### 4. Software terminology drift
**Sought**: "module", "feature", "configure", "manage", "settings", "preferences", "instance", "tenant" leaking into user-facing UI.
**Found**: 0 T2/T3 hits from the operator vocabulary scanner.
**Evidence**: scanner permanent guardrail. 16 T1 hits today (all `iter###` source-comments · expected).
**Status**: ✅ **No drift**

### 5. Management-suite behavior drift
**Sought**: org-chart features · employee-rating chrome · performance-review wizards · 360-feedback features.
**Found**: NONE. HR has accountability timeline (factual record) but NO ratings, NO scores, NO performance reviews.
**Evidence**: HrEmployeeAccountability collects events; no `rating`/`score`/`performance_score` fields exist.
**Status**: ✅ **No drift**

### 6. Surveillance behavior drift
**Sought**: GPS-driven state changes · auto-clock-in via location · driver-tracking maps · idle-time scoring · "productivity scores".
**Found**: NONE. Motive integration architecture is documented in `MOTIVE_INTEGRATION_STRATEGY.md` as **validate-don't-surveil** doctrine; not activated. DLS state is driver-tap-authored only.
**Evidence**: `dispatch_state_events` has no GPS field. Driver lifecycle UI requires manual taps. No employee-location collections exist.
**Status**: ✅ **No drift**

### 7. Role creep drift
**Sought**: Safety touching DLS · PM gaining dispatch writes · HR gaining safety incidents · Shop gaining payroll.
**Grep evidence**:
```
grep -r "DispatchLifecycleTile" pages/safety/ → 0 hits ✅
grep -r "DispatchLifecycleTile" pages/Hr*.jsx → 0 hits ✅
grep -r "AssignmentCreateDrawer" pages/pm/ → 0 hits ✅
grep -r "PmHaulActivityTile" pages/safety/ → 0 hits ✅
```
**Status**: ✅ **No drift** (confirmed by `ROLE_DISCIPLINE_LOCK_AUDIT.md`)

### 8. Operational clutter drift
**Sought**: too many tiles · too many CTAs per page · too many sub-navigation items.
**Found**: iter411 reduced Dispatch portal from N pre-Phase-16 tiles to 7 sections. Each section bounded. CTA hierarchy clear (primary · secondary · footer link). No floating action buttons stacking.
**Evidence**: iter411 portal-IA audit, testing-agent verification, mobile sweep clean.
**Status**: ✅ **No drift**

## Anti-pattern absence list (verified empirically · all PASS)
- ❌ No "Welcome wizard" on first login
- ❌ No 5-step onboarding modal walkthrough
- ❌ No "Tour the dashboard" tooltips
- ❌ No animated chart loading skeletons
- ❌ No "Last 7 days" / "Last 30 days" range pickers
- ❌ No "Export to PDF/Excel" buttons everywhere (selective exports only)
- ❌ No employee-of-the-week chrome
- ❌ No gamification (badges · points · leaderboards)
- ❌ No customizable user dashboards (each role has ONE doctrine-driven layout)
- ❌ No notification spam (iter357 digest is restrained)
- ❌ No "Quick actions" floating menus
- ❌ No live cursor / presence indicators

## Areas where restraint was actively chosen (decisions documented)
| Decision | Where | Why restraint |
|---|---|---|
| No KPI/score on health summary | iter412 | Operational honesty · ops leadership reads words not numbers |
| No GPS-driven auto-transitions | iter392/393 doctrine | Validate-don't-surveil · drivers author truth |
| No PM dispatch writes | iter409 | PM is production-awareness only · doctrine restraint |
| No Safety DLS tile | doctrine | Safety stays quiet on DLS · 14-day post-live-ops review |
| No HR DLS tile | doctrine | HR canonical for qualifications · not DLS consumer |
| No analytics on cycle data | iter392+ | Counts > scores · field-honest |
| No customizable layouts | system-wide | One doctrine-driven layout per role |
| No notifications spam | iter357 | Digest is restrained · daily cadence |

## What the platform CAREFULLY DOES NOT DO (preserved across 19 phases)
1. Dashboards (operational tiles only)
2. Analytics (counts only · no scores)
3. AI dispatch (no auto-assignment)
4. Maps (no driver-tracking maps)
5. Route optimization (no GPS-driven routing)
6. Payroll (HR accountability timeline only)
7. ERP workflows (no approval chains)
8. Productivity scoring (no employee scores)
9. Telematics (Motive validate-don't-surveil only)
10. Surveillance systems (driver-tap-authored only)
11. Giant admin systems (each admin page bounded)
12. Tutorial systems (in-flow coaching only)
13. Modal walkthroughs (Phase 18.1 doctrine)
14. AI assistant overlays (none)
15. Help dashboards (Guidance Center is searchable, not curated dashboard)

## Verdict
**The MASCI Operations Platform has maintained absolute doctrine integrity across 19 development phases.** Zero T2/T3 vocabulary drift · zero role creep · zero ERP/analytics/dashboard/surveillance leakage. Every restraint dimension holds today.

This audit is the strongest evidence that the platform deserves the descriptor: **ONE calm operational operating system.**
