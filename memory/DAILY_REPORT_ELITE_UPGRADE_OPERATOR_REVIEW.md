# Daily Report Elite Upgrade · Operator Review

_Phase V.1 · 2026-05-29 · implementation-readiness gate._

> Read top-to-bottom in ~5 minutes. By the end of §8 you have
> everything needed to authorize (or hold) the elite upgrade build.

This guide consolidates the 6 planning artifacts produced today
under the **Daily Report Evolution Pivot Directive** into a single
review surface.

---

## 1 · The pivot in one paragraph

Daily Report stays the field-facing experience. ODR becomes the
backend intelligence layer. Every ODR asset built between M0.1 and M1
gets retargeted at the existing Daily Report substrate. Foremen
never see the word "ODR." The form they already know becomes elite
underneath.

## 2 · 🔴 IMMEDIATE COLLISION · M1 freeze contradicts this pivot

M1 (closed earlier today) shipped this:

| Endpoint | M1 state | Pivot need |
|---|---|---|
| `POST /api/daily-reports` | Returns `410 Gone` redirecting to `/odr/new` | ❌ Must be **restored** to working state |
| `DELETE /api/daily-reports/{id}` | Returns `410 Gone` | ✅ Keep frozen (historical preservation still desired) |

**Recommended (NOT executed without operator approval):**

A 4-line revert restores `POST /api/daily-reports` to its original
working implementation. The original body is preserved verbatim in
`_legacy_create_daily_report_archived` for an instant, clean revert.
`DELETE` stays 410 — historical immutability still wanted.

**Without this revert, the elite upgrade cannot ship.** No foreman
can submit a Daily Report while POST is 410.

🛑 **Awaiting operator authorization to execute the partial revert.**

## 3 · Planning artifacts produced

| # | Artifact | Purpose |
|---|---|---|
| 1 | `DAILY_REPORT_EVOLUTION_PLAN.md` | Master pivot plan · §3 lists every "ADD" · §7 lists every "DO NOT" · §8 implementation-readiness checklist |
| 2 | `DAILY_REPORT_FIELD_SIMPLICITY_CERTIFICATION.md` | Doctrine Lock #1 applied to every proposed ADD · approval block template for every PR in this wave |
| 3 | `DAILY_REPORT_PRODUCTION_TRACKING_DESIGN.md` | Closed enum (7 units) · structured rows · station range · activity inference (no separate step) · ~1.5–2 dev-days |
| 4 | `DAILY_REPORT_CONSTRAINT_TRACKING_DESIGN.md` | 11-type taxonomy · chip selector · advisory RFI / schedule flags (pure signal) · ~1–1.5 dev-days |
| 5 | `DAILY_REPORT_OFFLINE_RECOVERY_PLAN.md` | Low/no signal contract · ~2.5 dev-days of strengthening + tests · 7 acceptance criteria before pilot |
| 6 | `ODR_SUBSTRATE_REUSE_MAP.md` | ~16 substrate assets reused · backend + frontend + probes inventory · reuse mental model diagram |
| 7 | `DAILY_REPORT_ELITE_UPGRADE_OPERATOR_REVIEW.md` (this) | Review consolidation + approval gate |

## 4 · What is on the table for wave-1 build (operator picks)

The pivot directive lists 6 capability ADDs. Each is independently
shippable. Operator may approve any subset for wave 1.

| # | Capability | Foreman impact | Time estimate |
|---|---|---|---|
| A | Production tracking (7 units · structured rows) | +15–20 s per row · 1–3 rows typical | 1.5–2 dev-days |
| B | Constraint tracking (11 types · chip selector) | +10–15 s per constraint · 0–1 typical | 1–1.5 dev-days |
| C | Activity inference (derived from A) | 0 s · no foreman action | included in A |
| D | RFI-ready flag (advisory only) | 0 s typical · one optional checkbox | 0.25 dev-day |
| E | Schedule-impact flag (advisory only) | 0 s typical · one optional checkbox | 0.25 dev-day |
| F | Better photo linkage | 0 s typical · one optional pin tap | 0.5 dev-day |
| G | Offline / recovery strengthening + tests | 0 s · invisible | 2.5 dev-days |
| H | Audit footer + audience projection on DR PDFs | 0 s · backend only | 0.5–1 dev-day |
| I | M1 partial revert (restore `POST /api/daily-reports`) | 0 s · backend only | 0.1 dev-day |

**Suggested wave-1 scope** (recommended bundle, operator may
modify): **I + A + B + D + E + G + H** = ~5–6 dev-days end-to-end,
parallelizable to ~4 calendar days. F and C are included by virtue
of A.

**Conservative wave-1 scope** (lowest risk): **I + G + H** = ~3
dev-days. Production / constraint structured tracking lands in
wave-2 after offline + audit hardening is proven in pilot.

## 5 · What is explicitly NOT on the table (per directive)

| Forbidden | Status |
|---|---|
| Replace Daily Reports with a separate ODR form | ❌ NEVER |
| Migrate historical reports | ❌ |
| Rewrite signed reports | ❌ |
| Make foremen dual-enter | ❌ |
| Add dashboard bloat | ❌ |
| Start RFI | ❌ |
| Start Schedule integration | ❌ |
| Start P6 integration | ❌ |
| Start production deploy | ❌ |
| Add a 10th wizard step | ❌ (Doctrine Lock #1) |

## 6 · Doctrine compliance · planning artifacts

| Doctrine | Status |
|---|---|
| Doctrine Lock #1 (Simplicity Test) | ✅ Applied to every ADD in `DAILY_REPORT_FIELD_SIMPLICITY_CERTIFICATION.md` |
| Doctrine Lock #2 (Platform Inheritance) | ✅ Reuse map proves we are not building parallel components |
| Operational Calmness | ✅ All ADDs are calm chips / optional fields / advisory signals |
| Cross-Portal Coaching Standard | ✅ OGC engine reused · same EN/ES corpus |
| Operational Linking Rules | ✅ DR ↔ photo / constraint / production links use existing semantics |
| Audience Projection Doctrine | ✅ External DR PDFs adopt the same redaction matrix |

## 7 · Implementation-readiness checklist

- [ ] Operator approves the M1 partial revert (`POST /api/daily-reports` restored, `DELETE` stays 410)
- [ ] Operator picks the wave-1 scope from §4 (suggested · conservative · or custom)
- [ ] Operator approves the offline contract from `DAILY_REPORT_OFFLINE_RECOVERY_PLAN.md` §2
- [ ] Operator approves the production unit closed enum (7 values from `DAILY_REPORT_PRODUCTION_TRACKING_DESIGN.md` §1)
- [ ] Operator approves the constraint type closed enum (11 values from `DAILY_REPORT_CONSTRAINT_TRACKING_DESIGN.md` §1)
- [ ] Operator approves the RFI/schedule advisory-only semantics (no RFI creation, no schedule mutation)
- [ ] Operator decides on the optional shared-module refactor (`ODR_SUBSTRATE_REUSE_MAP.md` §3) — in-place reuse for v1 vs. refactor first
- [ ] Operator confirms no pilot until offline contract acceptance criteria are met (`DAILY_REPORT_OFFLINE_RECOVERY_PLAN.md` §7)

## 8 · Stop condition

🛑 **HALTED at end of planning.**

Per directive: _"Stop after planning and implementation-readiness
review. Do not begin build until operator approves the exact upgrade
scope."_

When the operator returns the **8 checklist items in §7** with a
chosen wave-1 scope from §4, build can begin under the same calm
governance cadence (small batches, tests after each, no production
deploy until pilot approval).

---

_End of DAILY_REPORT_ELITE_UPGRADE_OPERATOR_REVIEW.md._
