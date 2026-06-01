# User Experience Improvement Roadmap

**Batch:** OMEGA · P2 · Real User Discoverability Audit
**Mode:** Plan only · NOTHING EXECUTED in this batch
**Companion:** `REAL_USER_DISCOVERABILITY_AUDIT.md` · `USER_FRICTION_LOG.md`
**Date:** 2026-06-01

> Roadmap of recommended improvements derived from the friction log. Each item lists the friction it resolves, the journey it improves, estimated implementation effort, and expected ROI. **Nothing is implemented in this batch — operator authorization required for any item.**

---

## 1 · ROI scoring rubric

| ROI level | Definition |
|---|---|
| 🏆 **Very High** | Resolves a 🔴 high-friction journey for ≥10 daily users · saves > 1 hr/week of cross-role time · directly reduces phone-call escalations |
| 🥇 **High** | Resolves 🔴 or 🟡 friction for 5-10 users · saves ~30 min/week |
| 🥈 **Medium** | Resolves 🟡 friction for 3-5 users · saves < 30 min/week |
| 🥉 **Low** | Quality-of-life cosmetic; no measurable time savings |

| Effort level | Definition |
|---|---|
| **S** Small | 1-2 days · single file edit · no backend changes |
| **M** Medium | 3-5 days · 2-4 files · backend touch · standard tests |
| **L** Large | 1-2 weeks · cross-cutting · new collection or migration |
| **XL** Extra Large | 3+ weeks · architectural · multi-portal touch |

---

## 2 · Phase 1 · Quick wins (≤ 1 week each · all 🏆/🥇 ROI)

### Q1 — Payroll Variance row → Time Verification deep-link (F-001)

* **Resolves:** F-001 (Sandy / Per-Day Detail) — 🔴 High
* **What:** Add a "View timecard" link on each variance row in `HrPayrollVariance.jsx`. Link target: `/hr/time-verification?employee={name}&week_ending={iso}&open_detail=daily`. Update `HrTimeVerification.jsx` to read these URL params on mount and auto-expand the per-day detail view for the named employee
* **Effort:** **S** (1 day · 2 files · no backend change · existing API supports `employee` query param)
* **ROI:** 🏆 Very High — Sandy saves ~25 min every Monday × ~50 Mondays/year = ~20 hr/year for one person; same gain for any HR backup
* **Test plan:** Self-test with operator + 1 fake variance row; verify the deep-link lands in the correct employee/day

### Q2 — HrHub copy disambiguation for Time Verification ↔ Payroll Variance (F-002)

* **Resolves:** F-002 (Time Variance confusion) — 🔴 High
* **What:** Rewrite the two tile subtitles in `HrHub.jsx` to make the distinction explicit:
  * Time Verification: *"Spot-check a single employee's timecard for any week"*
  * Payroll Variance: *"Upload a payroll CSV and flag mismatches against tracked time"*
* **Effort:** **S** (1-2 hours · 1 file · no backend change · pure copy edit)
* **ROI:** 🥇 High — Reduces wrong-tool-first taps for every new HR user
* **Test plan:** Operator sanity-check copy

### Q3 — Field Leadership Hub: surface JHA + Asset Transfers (F-004, F-005)

* **Resolves:** F-004 + F-005 — both 🔴 High
* **What:** Add two tiles to `FieldLeadershipHub.jsx`:
  * "Job Hazard Plans" → `/jha`
  * "Asset Transfers" → `/asset-transfers` (read-only for FL users; the PM controls the create flow)
* **Effort:** **S** (1 day · 1 file · `/jha` already public-readable, `/asset-transfers` needs auth check — if FL users can't view today, this becomes M)
* **ROI:** 🏆 Very High — directly cuts the most common "call the office" pattern for supers
* **Test plan:** Verify each tile lands and the underlying data renders for an FL portal user

### Q4 — Disable instead of show hard-delete buttons for unprivileged roles (F-014)

* **Resolves:** F-014 — 🟢 Low (cosmetic but visible)
* **What:** In `HrSafetyRecords.jsx` and similar surfaces, replace the always-visible delete button with a disabled state for HR + a tooltip "Hard-delete is reserved for Safety/Admin"
* **Effort:** **S** (half day · 1-3 files)
* **ROI:** 🥈 Medium — eliminates a wear point

### Q5 — Replace "Photo data unavailable or corrupt" with retry-able copy (F-017 lingering)

* **Resolves:** F-017 cosmetic gap
* **What:** In `JobPhotosLibrary.jsx` lightbox, replace static error with `"Photo failed to load. [Retry]"` and re-fire `ensureFullSrc(id)` on click
* **Effort:** **S** (half day · 1 file)
* **ROI:** 🥈 Medium — user empowerment + reduces support pings if any future transient failure occurs

**Phase 1 total:** ~3-4 days of agent time. Resolves 4 of 6 🔴 high-friction items.

---

## 3 · Phase 2 · Backend-touching improvements (1-2 weeks · 🏆/🥇 ROI)

### P2-A — In-app PO digest replay surface (F-003)

* **Resolves:** F-003 — 🔴 High
* **What:**
  1. Add `po_digest_runs` collection (paired with the dedup work from `PO_DIGEST_REMEDIATION_OPTIONS.md` Option C)
  2. New endpoint `GET /api/admin/po-digest/history?limit=20` and `GET /api/admin/po-digest/history/{slot_key}` → return the saved HTML payload
  3. New page `PoDigestHistory.jsx` (admin-readable, PM + HR can see their own entries)
* **Effort:** **M** (3-5 days · 1 backend file + 1 frontend file + new collection)
* **ROI:** 🏆 Very High — every PM/HR can self-serve historical context · also enables audit and forensic visibility
* **Sub-benefit:** This work also delivers the dedup remediation in `PO_DIGEST_REMEDIATION_OPTIONS.md` Option C as a side-effect

### P2-B — Soft-delete viewer for Incidents (F-013)

* **Resolves:** F-013 — 🟡 Medium
* **What:** Add a "Show deleted" toggle on `/safety/incidents` (Safety + Admin only) that surfaces rows with `deleted_at != null`. Read-only.
* **Effort:** **S-M** (1-2 days · 1 frontend file + small backend predicate change)
* **ROI:** 🥇 High for safety auditors

### P2-C — PmProjectDetail elevated to top-level PmHub tile (F-009)

* **Resolves:** F-009 — 🟡 Medium
* **What:** New PmHub tile "Project Drilldown" that opens a project picker → drops user into `PmProjectDetail`. Surface a recently-viewed-projects shortcut on PmHub.
* **Effort:** **S-M** (1-2 days · PmHub + a small project-picker component)
* **ROI:** 🏆 Very High — exposes the platform's strongest cross-domain view to every PM by default

### P2-D — Safety officer manual-fire of safety digest (F-012)

* **Resolves:** F-012 — 🟡 Medium
* **What:** Add a "Send digest now" button inside the Safety Portal (`SafetyHub.jsx`). Backend: relax `Depends(require_admin)` on `/api/admin/digest-settings/send-now` to also accept a `Depends(require_safety_strict)` gate
* **Effort:** **M** (2-3 days · 1 backend file + 1 frontend file + RBAC review)
* **ROI:** 🥇 High — eliminates admin-handoff for routine safety operations

### P2-E — Project Health tile rename + better preview (F-010)

* **Resolves:** F-010 — 🟡 Medium
* **What:** Rename tile to "Project Health (Budget · Schedule · Friction)" and surface the first KPI on the tile face. Backend already exposes counts via the existing endpoint
* **Effort:** **S** (1 day · 1 file + a small counts endpoint already in place per `ProjectHealth.jsx`)
* **ROI:** 🥈 Medium

**Phase 2 total:** ~10-15 days of agent time. Combines well with the P1 PO digest dedup remediation Option C.

---

## 4 · Phase 3 · Cross-cutting / architecture (2-4 weeks · 🏆/🥇 ROI)

### P3-A — Unified Monday Executive Briefing (F-016)

* **Resolves:** F-016 — 🟡 Medium → 🏆 ROI because it touches executives
* **What:** A new combined `operator_executive_digest` that aggregates: PO open count + open incident count + safety meeting count + project health top 3 + photo activity. Replace Leo/Leticia/Jay's three Monday emails with one. Reuse the existing renderers
* **Effort:** **L** (1-2 weeks · 1 new file in `lib/` + small wiring · share Resend infrastructure)
* **ROI:** 🏆 Very High for executives

### P3-B — Global breadcrumb component + consistent layout (F-015)

* **Resolves:** F-015 — 🟡 Medium · everyone
* **What:** A `<Breadcrumbs>` component computed from the React Router location + a canonical mapping of route segments to friendly names. Hook into every hub's page shell
* **Effort:** **L** (1-2 weeks · 1 new component + integration touches across 10 hubs · low risk per touch)
* **ROI:** 🥇 High — improves every user's sense of place

### P3-C — Consolidate parallel training surfaces (F-007)

* **Resolves:** F-007 — 🟡 Medium
* **What:** Make `/safety/training-records` the system-of-record. Make `/hr/training-records` a read-only view of the same data with HR-specific filters. Document in `<HelpTipBlock>` that HR cannot author here; instead HR uses the Employee Lifecycle flow
* **Effort:** **M** (3-5 days · backend RBAC review + 1-2 frontend files)
* **ROI:** 🥈 Medium

### P3-D — Consolidate dispatch surfaces (F-008)

* **Resolves:** F-008 — 🟡 Medium
* **What:** Move all dispatcher-controllable surfaces under `/dispatch-portal`. Leave `/admin/dispatch` only for admin-locked super-controls (e.g. mass reassignment after a weather day)
* **Effort:** **L** (1-2 weeks · cross-portal navigation audit + several files)
* **ROI:** 🥈 Medium

### P3-E — Unify `/daily/submit` and `/daily/new` (F-011)

* **Resolves:** F-011 — 🟡 Medium
* **What:** Auto-detect auth state on `NewDailyReport.jsx` and toggle the public-mode UI. Keep the legacy redirect for `/daily/submit` for QR-code links
* **Effort:** **S-M** (1-2 days · 1 file)
* **ROI:** 🥈 Medium

**Phase 3 total:** ~5-8 weeks of agent time.

---

## 5 · Prioritized 90-day plan (recommended sequence)

| Week | Item | Rationale |
|---|---|---|
| 1 | Q1 (Sandy deep-link) + Q2 (HrHub copy) | Highest-friction · lowest effort · Sandy's request line goes quiet |
| 1 | Q3 (FL Hub surfaces) | Same week · highest visibility for supers · ROI compounds with Q1 |
| 2 | Q4 (button greying) + Q5 (photo error copy) | Polish the recently-active areas (Sprint 1C + Sprint 1G) |
| 2-3 | P1-B (PO digest dedup, Option B from `PO_DIGEST_REMEDIATION_OPTIONS.md`) | Eliminates the duplicate-fire root cause for ALL schedulers |
| 3-4 | P2-A (PO digest replay surface + dedup audit table) | Combines naturally with P1-B; ships the new `po_digest_runs` collection once |
| 5 | P2-B (soft-delete viewer) + P2-C (PmProjectDetail elevation) | Mid-effort high ROI |
| 6 | P2-D (safety self-fire) + P2-E (Project Health tile) | Round out medium-friction backlog |
| 7-10 | P3-A (executive briefing unification) | Major executive-facing change · needs design sign-off |
| 11-12 | P3-B (breadcrumb) + P3-E (daily-report URL unify) | Ship together as a layout/UX pass |
| 13+ | P3-C + P3-D | Lower-priority consolidation work · only if Phase 1-2 outcomes are healthy |

---

## 6 · ROI matrix

| ID | Item | Severity | Effort | ROI |
|---|---|---|---|---|
| Q1 | Sandy deep-link | 🔴 | S | 🏆 Very High |
| Q2 | HrHub copy disambig | 🔴 | S | 🥇 High |
| Q3 | FL Hub surfaces (JHA + transfers) | 🔴 | S | 🏆 Very High |
| Q4 | Disable unprivileged buttons | 🟢 | S | 🥈 Medium |
| Q5 | Photo error retry copy | 🟢 | S | 🥈 Medium |
| P2-A | PO digest replay + dedup table | 🔴 | M | 🏆 Very High |
| P2-B | Soft-delete viewer | 🟡 | S-M | 🥇 High |
| P2-C | PmProjectDetail elevation | 🟡 | S-M | 🏆 Very High |
| P2-D | Safety self-fire digest | 🟡 | M | 🥇 High |
| P2-E | Project Health tile rename | 🟡 | S | 🥈 Medium |
| P3-A | Unified executive briefing | 🟡 | L | 🏆 Very High |
| P3-B | Global breadcrumb | 🟡 | L | 🥇 High |
| P3-C | Training surface consolidation | 🟡 | M | 🥈 Medium |
| P3-D | Dispatch surface consolidation | 🟡 | L | 🥈 Medium |
| P3-E | Unify /daily/submit + /daily/new | 🟡 | S-M | 🥈 Medium |

---

## 7 · What's intentionally NOT proposed

Per the OMEGA out-of-scope list:

* ❌ No white-label / multi-tenant work
* ❌ No ForgedOps portal expansion
* ❌ No new dashboards (the proposed surfaces all enhance existing views; nothing creates a brand-new dashboard)
* ❌ No production changes (everything above requires explicit operator authorization in a future Batch)

Also explicitly out of this audit's scope (could be a separate batch):

* Telemetry instrumentation (no click-tracking proposed)
* Mobile-native app (the web is already responsive)
* AI-assisted summaries (e.g., "explain this incident")
* Notification reorder / batching beyond P3-A

---

## 8 · Pre-execution gate (per OMEGA)

🛑 **NOTHING IN THIS ROADMAP HAS BEEN EXECUTED.** All items remain documented · awaiting operator authorization.

When ready, the operator may authorize:

* `OMEGA BATCH · UX Phase 1 (Q1+Q2+Q3+Q4+Q5)` — recommended first batch · ~4 days · 5 of 6 high-friction items addressed
* `OMEGA BATCH · UX Phase 2 (P2-A through P2-E)` — recommended second batch · ~2 weeks
* `OMEGA BATCH · UX Phase 3` — architectural · ~5-8 weeks
* `OMEGA BATCH · individual items by ID (e.g. Q1 only)` — for surgical pickups

Until then: 🛑 STOPPED.
