# TRACK 15.70 · Revenue Readiness (Phase 8)

_Generated 2026-06-22_

## The Three Sales Questions

| Question | Answer | Evidence |
|---|:-:|---|
| Can Customer #2 be sold today? | 🟡 **YES with caveats** | Tenant chrome READY, isolation via separate cluster READY, 3 BLOCKED hardcoded items need ~1-2 days fix |
| Can Customer #3 be sold tomorrow? | 🟡 **YES with caveats** | Same as #2 — provisioning is repeatable (Phase 4 proved this) |
| Can Customer #5 be sold next week? | 🟡 **YES with caveats** | Per-customer infra still 4-8 hour pipeline (Phase 7) |
| Without developer intervention? | ❌ **NO** | 3 BLOCKED items require a developer to apply ~30 LOC of fixes. Once those land, ongoing customer provisioning is operator-only. |

## The Honest Sales Pitch (today)

ForgedOps can credibly sell Customer #2 the **MASCI Suite** today
with the following commitments:

1. **Branding**: customer logo, company name, color scheme, custom
   sender domain — all DB-configurable, no code changes per customer.
2. **Email routing**: 19 production-grade routes, per-tenant
   recipients, audit trail, dead-letter handling, critical-route
   guard rails. All DB-configurable.
3. **Isolation**: separate Atlas cluster per customer — physically
   impossible for customers to see each other's data.
4. **Operational continuity**: same proven backend that runs MASCI;
   no V3 / no architectural rewrite.
5. **Provisioning time**: 4-8 hours per new customer (most is third-party wait).
6. **Module bundle**: full suite (Core + PM + Safety + Shop + Dispatch + HR).
   Tiered SKUs (Safety-only, PM-only, etc.) require Track 16.x.

## Blockers to Address Before Customer #2 Production Go-Live

1. 🔴 `auth.py:59-63` MASCI owner seed — gate by env / tenant_key (~10 LOC).
2. 🔴 `server.py:2384` From-line — switch to `format_from_field()` (~6 LOC).
3. 🔴 `server.py:3719` From-line — switch to `format_from_field()` (~6 LOC).

Total: **~22 LOC, ~1-2 days dev work** including test + verify.

## Blockers to Address Before Tiered-SKU Sales

1. 🟡 Module-gate framework (~270 LOC across backend + frontend).
   Track 16.x — NOT 15.70 scope.

## Pricing-Model Compatibility

| Pricing Model | Ready today? |
|---|:-:|
| Full-suite annual contract (e.g., $50k/yr/customer) | ✅ |
| Per-user MRR (e.g., $25/user/month) | ✅ (no enforcement, but billable via Atlas user count) |
| Tiered SKU ($X for Safety-only, $Y for full suite) | ❌ (need module gating) |
| Per-module add-on ($X base + $Y per module) | ❌ (need module gating) |
| Usage-based (e.g., $X per 1000 emails) | ✅ (Resend per-customer metering) |

## Sales Confidence Levels

| Customer profile | Sales-ready confidence | Required prep |
|---|:-:|---|
| Customer #2 — full suite, same vertical as MASCI | 🟢 **HIGH** (90%) | Fix 3 BLOCKED items + ~4 hour provisioning |
| Customer #3 — full suite, similar vertical | 🟢 **HIGH** (90%) | Same as #2 |
| Customer #5 — full suite, adjacent vertical (e.g., HVAC, demolition) | 🟡 **MED** (70%) | Same + customer-specific copy review |
| Customer #N — Safety-only tier | 🔴 **LOW** (40%) | Requires 16.x module gating before close |
| Customer #N — large enterprise (~10x MASCI volume) | 🟡 **MED** (60%) | Capacity planning + Atlas tier sizing |

## Verdict

🟡 **PARTIAL YES — revenue-ready for full-suite sales with ~2 days dev prep.**

ForgedOps can credibly engage Customer #2 in sales conversations
today. The platform is technically sound (15.65/15.68 family closed,
15.69 cutover ready). Three small developer fixes (~22 LOC) close
the customer-visible-leak gap. Per-customer provisioning takes 4-8
hours of operator time, mostly external service wait.

**For tiered SKU sales, Track 16.x (module gating) is required and is
not in 15.70 scope.**
