# WHITE-LABEL EFFORT ESTIMATE

**Phase 14 deliverable.** Three customer-2 deployment models compared.

## Model 1 — Manual Clone Deploy
**"Fork the repo, find-replace MASCI, deploy."**

| Dimension | Estimate |
|-----------|----------|
| Engineering effort | ~3 weeks for Customer #2 (manual rebrand + smoke test) |
| Risk | HIGH — divergent codebases, no shared bug-fix pipeline |
| Timeline to first customer | 3 weeks |
| Cost complexity | LOW one-time, HIGH ongoing |
| Support complexity | HIGH — each clone drifts |
| Data isolation risk | LOW (per-customer everything) |
| White-label fit | MEDIUM (gets a working product but doesn't scale) |
| Recommended use case | Emergency single one-off if revenue justifies and customer is patient |

**Pros**: Fastest path to "Customer #2 has a working platform."
**Cons**: Every future MASCI bug fix must be re-applied manually to each clone. Within 3 customers this model collapses.

**Verdict**: ❌ NOT RECOMMENDED. Use only if business need is desperate.

## Model 2 — Config-Driven Single-Tenant Template ⭐ RECOMMENDED
**"One codebase, BrandConfig per deploy, separate Atlas DB per customer."**

| Dimension | Estimate |
|-----------|----------|
| Engineering effort | ~10 weeks total (Phase 1-5 of roadmap) |
| Per-new-customer effort after Phase 5 | ~4 days |
| Risk | LOW — defaults preserve MASCI behavior, no architectural change |
| Timeline to first customer | 10 weeks (then 4 days each thereafter) |
| Cost complexity | MEDIUM (1 deploy per customer; per-customer infra cost) |
| Support complexity | LOW — single codebase serves all customers |
| Data isolation risk | LOW (same primitives as preview/prod) |
| White-label fit | HIGH |
| Recommended use case | 2-20 customers · MASCI continues to own infra |

**Pros**: Single codebase. Per-customer infra mirrors RC1's already-proven preview/prod isolation. Onboarding becomes 4 days after Phase 5. Reversible later to Model 3.

**Cons**: Per-customer Kubernetes deploy cost scales linearly with customer count.

**Verdict**: ✅ RECOMMENDED for Customer #2 and #3-20.

## Model 3 — True Multi-Tenant SaaS
**"Shared app, `tenant_id` on every row, dynamic brand resolved per request."**

| Dimension | Estimate |
|-----------|----------|
| Engineering effort | ~10 weeks for Phase 1-4 (same as Model 2) PLUS ~12-16 weeks for SaaS conversion |
| Per-new-customer effort after launch | ~hours (self-serve onboarding portal) |
| Risk | HIGH — every read/write path must be tenant-aware · single bug = cross-tenant leak |
| Timeline to first customer | 24-30 weeks |
| Cost complexity | LOW (single shared deploy, marginal cost per customer near zero) |
| Support complexity | LOW |
| Data isolation risk | MEDIUM (depends on engineering discipline) |
| White-label fit | HIGH |
| Recommended use case | 20+ customers · MASCI selling SaaS at scale |

**Pros**: Lowest per-customer marginal cost. Self-serve. Scales to hundreds of customers.

**Cons**: Highest engineering risk. Easy to leak data between tenants if one query forgets `tenant_id`. Requires audit log + notifications + backups all tenant-aware.

**Verdict**: ⏸ DEFER. Only worth the engineering investment when customer count hits ~20 or per-deploy cost exceeds Atlas + R2 + Resend + Sentry combined ($75-150/customer/month).

## Comparison summary

| Model | Time to Customer #2 | Customer #20 cost trajectory | Engineering risk |
|-------|---------------------|------------------------------|------------------|
| 1 | 3 weeks | catastrophic (20 codebases) | high |
| 2 ⭐ | 10 weeks | manageable (20 deploys × infra) | low |
| 3 | 24+ weeks | excellent | high during conversion |

## Recommended sequence

1. **Now** (after RC1 stabilizes 7+ days): nothing — let production breathe.
2. **Track 17 (Phase 1)**: 2 weeks · centralize top-20 brand surfaces.
3. **Track 18 (Phases 2-4)**: 4 weeks · BrandConfig + email/PDF parameterization.
4. **Track 19 (Phase 5)**: 1 week · onboarding runbook + automation.
5. **Track 20 (Phase 6)**: 1 week · first real customer pilot.
6. **Track 21 (Phase 7)**: 2 weeks · repeatable onboarding hardening.
7. **Decision point**: at ~10 customers, evaluate Model 3 SaaS migration. Do NOT promise SaaS before that.

## Cost summary

| Model | Engineering cost (one-time) | Per-customer marginal cost (monthly) |
|-------|-----------------------------|---------------------------------------|
| 1 | ~3 wk × 1 dev × Customer = scales linearly | $75-150/customer (infra) |
| 2 | ~10 wk × 1 dev (one-time only) | $75-150/customer (infra) |
| 3 | ~24 wk × 1 dev | ~$5-15/customer (shared infra amortized) |

## Bottom line

🟢 **Recommend Model 2** for Customer #2 through #20. Defer Model 3 until forced by scale.
