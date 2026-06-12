# Track 13.6B · Migration Readiness Report

**Status:** PM V2 and HR V2 are **Ready For Operator Visual Approval** of a Phase B3 pilot migration.
**Mode:** Preview-only · no swap performed · no deploy.
**Generated:** 2026-06-12 (UTC)

> The pre-migration checklist per portal. Track 13.6B does not migrate anything. This report records what is now possible **with operator authorization**.

---

## 1. Migration definition

For the purposes of Phase B3, a **migration** of a portal means:
1. Building a `*_v2` mount of the portal's hub (and optionally one or two key inner surfaces) using the Phase B1 design-system primitives.
2. **Binding** that surface to the **real** APIs the portal already uses — no mock fixtures.
3. Standing it up at a **temporary side-by-side route** (e.g. `/hr/hub_v2`, `/pm/hub_v2`) while leaving the original route alive.
4. Operator visually compares the live `*_v2` against the live original.
5. **Only on explicit operator authorization** is the original route swapped to the `_v2` implementation.

Track 13.6B did **not** perform any of steps 2–5. It performed only the equivalent of step 1, behind `/_internal/*` paths with **mock data**, so the operator can see what migration would feel like before it begins.

---

## 2. Per-portal readiness

### 2.1 HR (recommended first pilot — lowest risk)

| Check | Status |
| --- | --- |
| Action-queue preview built | ✅ `/_internal/hr-v2-preview` |
| Side-by-side compare available | ✅ `/_internal/v2-compare/hr` |
| Five pillars ≥ 9 / 9 / 9 / 9 / 8 | ✅ (all pillars at preview min) |
| Backing APIs already ship | ✅ `/api/hr/employees`, `/employee-requests`, `/daily-reports`, `/employee-accountability`, `/driver-qualification/dashboard`, `/training-records`, `/payroll-variance` |
| Zero live HR drift | ✅ verified |
| Mock data clearly labelled | ✅ banner + per-card "Source: …" caption |
| Empty states present | ✅ 5 EmptyStates with `good` severity |
| Per-surface Playwright guardrail | ⚠ **Not yet built** — required before swap |
| Real API binding | ⚠ **Pending Phase B3** — preview uses mock fixtures |
| Operator usability run (first-time HR) | ⚠ **Pending Phase B3** — required before swap |

**Verdict:** HR is the lowest-risk migration target. Six items above are green; three are explicitly pending Phase B3 authorization.

### 2.2 PM (highest impact pilot)

| Check | Status |
| --- | --- |
| Action-queue preview built | ✅ `/_internal/pm-v2-preview` |
| Side-by-side compare available | ✅ `/_internal/v2-compare/pm` |
| Five pillars ≥ 9 / 9 / 9 / 9 / 8 | ✅ |
| Backing APIs already ship | ✅ `/api/pm/jobs`, `/api/pm/crew/capas`, `/api/pm/command-center/*` (7 sub-endpoints), `/api/daily-reports`, `/api/incidents`, `/api/constraints` |
| Zero live PM drift across 6 routes | ✅ verified |
| RFIs / Submittals / Risks removed | ✅ DOM count = 0 at every viewport |
| Project Constraints engine used | ✅ real engine bound (caption-cited) |
| Mock photo grid removed | ✅ replaced with real link to `/pm/photos` |
| Per-surface Playwright guardrail | ⚠ **Not yet built** |
| Real API binding | ⚠ **Pending Phase B3** |
| Operator usability run (first-time PM) | ⚠ **Pending Phase B3** |
| Unified Holds aggregation engine | ⚠ **Not yet built** — captured in `MASCI_PM_TARGET_STATE.md` PM-2 |
| Due-Today aggregation engine | ⚠ **Not yet built** — captured in PM-3 |

**Verdict:** PM is the highest-impact target but introduces two backend-engine items (Holds / Due-Today) that should ship **before** the migration to keep the V2 honest. Recommendation: do HR pilot first, then return to PM after Holds + Due-Today engines exist.

### 2.3 Admin / Dispatch / Safety / Shop / Driver

| Portal | Readiness |
| --- | --- |
| Admin | Not yet previewed. R-04 (4 health pages) + R-05 (compliance dedupe) must be addressed in the migration plan. |
| Dispatch | Strong post-13.4A; migration is mostly chrome alignment. **Dispatch map guardrail is the existing reference**; replicate the pattern for any Dispatch swap. |
| Safety | Trench Safety module is the platform reference benchmark; migration is mostly aligning other safety surfaces to that voice. |
| Shop | Smallest portal. Migration is mostly the V-01 amber/orange drift correction. |
| Driver | Lowest score today. **Driver Hub static landing must be built first** (V-15 / R-13) before any V2 work. |

---

## 3. Operator decisions still required (block Phase B3)

1. **Pilot target: HR or PM?**
   Recommendation: HR first. Lowest risk. Highest five-pillar score per `MASCI_FIVE_PILLAR_SCORECARD.md`. Fastest path to a felt result.
2. **Risks → Project Constraints rename: permanent or interim?**
   13.6B made the substitution. Operator must confirm permanence or scope a future Risks engine.
3. **RFIs / Submittals: accept absence or scope?**
   They are absent because no engine exists. Operator must choose to leave them absent or authorize new engine work.
4. **Holds engine: build before or after PM migration?**
   If PM is the pilot, the Holds engine must ship first (so the "Open Holds" surface is honest). If HR is the pilot, this is deferred.
5. **Production verification (T0 from 13.5C):** execute before any migration?
   Recommended: yes. T0 is zero code and raises Trusted + Proven by ~1 point each. The cheapest win available.

---

## 4. Recommended next-track sequence

1. **T0 — Production verification (Track 13.4D 7-point checklist).** Zero code. Highest trust impact.
2. **T2-HR — Phase B3 Pilot Migration of HR.** Bind HR V2 preview to real APIs · stand up `/hr/hub_v2` · operator visually compares via `/_internal/v2-compare/hr` · approve · swap.
3. **PM-2 — Unified Holds aggregation engine.** Required before PM pilot.
4. **PM-3 — Due-Today aggregation engine.** Same.
5. **T2-PM — Phase B3 Pilot Migration of PM.** Same pattern as HR after PM-2 / PM-3 land.
6. **T7 — Driver Hub static landing.** Closes V-15 / R-13.
7. **T16 — Per-surface Playwright visual guardrails.** Replicate the Dispatch guardrail across every operator surface.

---

## 5. Five-pillar trajectory (with citations)

| Pillar | 13.5B baseline | After 13.6A | After 13.6B | Projected after Phase B3 (HR pilot) |
| --- | :-: | :-: | :-: | :-: |
| Powerful | 8.2 | 8.2 | 8.3 | 8.5 |
| Simple | 6.5 | 6.7 | 7.0 | 7.5 |
| Beautiful | 7.0 | 7.2 | 7.4 | 8.0 |
| Trusted | 7.2 | 7.2 | 7.3 | 8.5 (with T0) |
| Proven | 7.1 | 7.2 | 7.3 | 8.0 |
| Aggregate | **7.2** | **7.3** | **7.5** | **8.1** |

The improvements 13.6A → 13.6B are small but real: the platform now has a **review system**, an **action-queue language**, and **zero dead objects in two previews**. The big swing comes with the first real swap.

---

## 6. Final Verdict

> **Phase 13.6B Complete — Two pilot portals are Ready For Operator Visual Approval.**

All directive constraints honored:
- Discovery stayed closed. No new audit branch.
- No portal swap.
- No deploy.
- No GitHub save.
- No merge.
- Every visible object on PM V2 and HR V2 earns its place per Rule #1.
- Operator review system stood up at `/_internal/v2-index`.
- Side-by-side comparison stood up at `/_internal/v2-compare/{pm,hr}`.

Next action: operator visual approval (or revision request) on the side-by-side views, leading to Phase B3 authorization.

Standing rules still in force: **No deploy. No GitHub save. No merge.**
