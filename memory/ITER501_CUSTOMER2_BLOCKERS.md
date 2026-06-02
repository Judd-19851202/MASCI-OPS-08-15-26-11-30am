# ITER501 · CUSTOMER #2 BLOCKERS

**Date**: 2026-06-02T21:08 UTC
**Mode**: READ-ONLY synthesis
**Source**: ITER500_CUSTOMER2_READINESS_REPORT + ITER500 Executive Summary (~60% out-of-box · ~85% with 2h onboarding)

---

## Bottom line

| Status | Score |
|---|---|
| Out-of-box (Customer #2 logs in, no prep) | **~ 60 %** |
| With 2-hour structured onboarding | **~ 85 %** |
| With every Customer #2 blocker resolved | **~ 98 %** (the 2 % residual is platform-aesthetic, not blocking) |

The platform IS operable for a second construction-services customer today, but it leaks the first-customer's organizational fingerprints (MASCI branding, MASCI-specific roster, MASCI-specific job-numbering convention, MASCI-specific email templates). A new customer would need to wade through hard-coded MASCI vocabulary and overwrite seeded data before they could trust it as theirs.

---

## Hard blockers (must clear before pitching Customer #2)

| # | Blocker | Where | Effort |
|--:|---|---|---|
| 1 | Hard-coded `MASCI` brand string in many UI surfaces (`MasciLogo`, page titles, copy) | platform-wide | **~ 2 weeks** (parameterize via tenant config) |
| 2 | Hard-coded MASCI email distribution lists in notification templates | backend templates | ~ 3 days |
| 3 | Hard-coded job-number format (`#XXXXX`) in `JobPicker` and downstream surfaces | frontend + schema | ~ 2 days |
| 4 | Seeded `employee_master` rows are MASCI-specific | seed scripts | ~ 1 day to make optional / templatized |
| 5 | Single-tenant `mongo` collections (no `customer_id` partitioning) | backend data model | **~ 4 weeks** for proper multi-tenancy |
| 6 | Hard-coded production domain `mascidocs.com` in some email and webhook templates | backend env / templates | ~ 1 day |
| 7 | Single-tenant `RESEND_WEBHOOK_SECRET` (one secret, one webhook) | backend env | needs tenant-scoped secrets |
| 8 | No tenant-scoped auth (Jaymn Judd is hard-coded super-admin · no concept of "Customer #2 super-admin") | auth layer | ~ 1 week |
| 9 | Single-tenant scheduler — all customers would share the same job cadence | scheduler service | needs tenant-aware scheduling |
| 10 | Reports / PDFs branded MASCI in the header | PDF template | ~ 2 days |

**Total effort for true multi-tenancy**: 6 – 8 weeks of focused engineering.

---

## Soft blockers (operator can paper over with 2-hour onboarding)

| # | Soft blocker | Mitigation |
|--:|---|---|
| 1 | New customer's vocabulary differs (e.g., "Job" vs "Project") | onboarding override · UI string overrides could be parameterized in 1 day |
| 2 | New customer's role names differ (e.g., "Site Boss" vs "Foreman") | onboarding override · already supports custom roles in `field_leadership_users` |
| 3 | Customer's email signature / domain | tenant config |
| 4 | Customer's photo-min thresholds (today: 4 photos for incident, 6 for daily report) | should be tenant-configurable |
| 5 | Customer's compliance frequency cadences (driver-qual, equipment inspections) | tenant config |
| 6 | Customer's safety reporting thresholds | tenant config |
| 7 | Customer's QA/QC checklist library | already extensible but seeded with MASCI-specific items |
| 8 | Hub tile order / grouping (different priorities per customer) | tenant config or per-tenant Hub layout |
| 9 | Custom report templates | extensible but currently no template editor |
| 10 | Customer's notification distribution list | tenant config |

These are real onboarding friction — but they don't block the pitch; they just lengthen the kickoff.

---

## Ranked blocker priority (for Customer #2 readiness work)

| Rank | Blocker | Why first |
|---:|---|---|
| 1 | **Tenant identity layer** (`customer_id` partitioning + tenant-scoped auth) | Foundation for everything else; ~ 4 wk |
| 2 | **Brand parameterization** (logo, copy, email templates, PDF headers) | Visible to every user immediately; ~ 2 wk |
| 3 | **Tenant config layer** (vocabulary overrides, role names, photo thresholds, cadences) | Removes 90% of "but ours is different" objections; ~ 1 wk |
| 4 | **Tenant-scoped secrets + webhooks** (Resend, MFA, future Stripe) | Operational isolation; ~ 1 wk |
| 5 | **Seed-script templatization** (Customer #2 starts from a documented blank state) | Removes embarrassment of MASCI rows showing on first login; ~ 1 day |
| 6 | **Tenant-aware scheduler** (so Customer #2's digests don't fire on MASCI's schedule) | Operational cleanliness; ~ 3 days |
| 7 | **Tenant onboarding playbook** (a documented checklist) | Reduces onboarding time from days to hours; ~ 2 days writing |

Estimated total: **~ 9 weeks** of focused multi-tenancy + onboarding work to reach 98% Customer #2 ready.

---

## What is NOT a Customer #2 blocker (deliberately excluded)

* **OC-005 JHP** (would be helpful, not blocking)
* **Verb harmonization** (helpful, not blocking)
* **Approve/Reject dropdown promotion** (helpful, not blocking)
* **Constraint LifecyclePanel** (helpful, not blocking)
* **Driver-qualification expiring-soon flag** (helpful, not blocking)
* Most ITER500 Top 25 (helpful, not blocking) — Customer #2 can still operate; they'll just hit the same friction MASCI hits

---

## Recommendation

If the operator's goal is **Customer #2 by Q3 2026**, the work order is:

1. Decide explicitly whether to commit to multi-tenancy NOW or to onboard Customer #2 in a parallel-pod single-tenant deployment.
2. If multi-tenancy: rank #1 + #2 above are the critical path (~ 6 weeks)
3. If parallel-pod: rank #2 + #3 + #5 + #7 are the critical path (~ 2 weeks)
4. Either way, do NOT start Customer #2 readiness until the existing P0 lifecycle audits (this ITER501 + the ranks #2/#3 from ITER500) close, or you'll be doing the polish work in production under customer scrutiny.

---

End of Customer #2 blockers.
