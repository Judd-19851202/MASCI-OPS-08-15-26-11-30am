# ITER501 · WHITE LABEL BLOCKERS

**Date**: 2026-06-02T21:10 UTC
**Mode**: READ-ONLY synthesis
**Source**: ITER500_WHITELABEL_READINESS_REPORT + Executive Summary (~ 40 % readiness · single-tenant · hardcoded org name)

---

## Bottom line

| Status | Score |
|---|---|
| Today (post-Rank #1 + production deploy) | **~ 40 %** |
| After Customer #2 multi-tenancy work | ~ 65 % |
| After dedicated White Label sprint | **~ 95 %** |

White Label is a **strict superset** of Customer #2 readiness. Every Customer #2 blocker is also a White Label blocker; in addition, White Label requires the **operating company's identity to be fully invisible** to the end customer — including admin UI, email From: lines, support links, documentation, terms of service, and even internal naming conventions in URL paths.

---

## Hard blockers (must clear before pitching as White Label)

| # | Blocker | Where | Effort |
|--:|---|---|---|
| 1 | Every Customer #2 blocker (multi-tenancy, brand parameterization, tenant config, tenant-scoped secrets, seed templatization, tenant-aware scheduler) | platform-wide | ~ 9 wk (see Customer #2 doc) |
| 2 | **MASCI strings in URL slugs and route names** (`/mascidocs.com`, `masci-` prefixes in collection names, `MASCI Operations Platform` in page titles) | frontend + backend | ~ 2 wk |
| 3 | **Email From: address hardcoded** to `@mascigc.com` / `@mascidocs.com` | backend Resend config | needs tenant-scoped sending domains · ~ 1 wk |
| 4 | **Support email / phone / help text** all currently MASCI-internal | platform-wide help-tips, contact-us pages | ~ 1 wk |
| 5 | **Terms of Service / Privacy** pages reference MASCI as the operator | platform-wide | needs tenant-scoped legal docs · ~ 1 wk |
| 6 | **PDF templates** branded MASCI in headers, footers, watermarks | backend PDF service | ~ 1 wk |
| 7 | **MFA app-name issuer** hardcoded to `MASCI Safety Hub` in TOTP enrollment URI | backend MFA | ~ 1 day |
| 8 | **Database name** `masci_safety` / `masci_safety_preview` — these names appear in admin pages and logs | backend + admin UI | ~ 3 days to abstract |
| 9 | **Internal-tooling references** to MASCI in code comments, doctrine docs, certification reports (cosmetic, but a White Label customer auditing the codebase would see them) | repo-wide | ~ 1 wk to redact |
| 10 | **Support agent integration** (Emergent support) routes through Emergent-branded channels — not customizable to a White Label tenant's own support desk | platform-level | requires Emergent product change · out of customer's hands |
| 11 | **Browser title / favicon** hardcoded to MASCI | frontend public/ | ~ 1 day to parameterize |
| 12 | **SEO meta description** mentions "MASCI" | frontend public/index.html | ~ 1 day |
| 13 | **Onboarding emails / welcome flows** branded MASCI | backend templates | ~ 3 days |
| 14 | **Subdomain pattern** today is `mascidocs.com`; White Label needs `{customer}.{platform}.com` or `{customer}.com` CNAME | infrastructure / DNS | ~ 1 wk including Emergent platform support |
| 15 | **Mobile / PWA manifest** branded MASCI | frontend public/manifest.json | ~ 1 day |

**Total effort White Label specific (on top of Customer #2)**: **~ 5 – 6 additional weeks**.

---

## Soft blockers (could be tolerated by a friendly first White Label customer)

| # | Soft blocker | Mitigation |
|---|---|---|
| 1 | Doctrine / certification docs in repo still reference MASCI by name | redact during White Label sprint; non-customer-visible |
| 2 | i18n strings still reference "MASCI" in a few coaching tooltips | string sweep |
| 3 | Default seed data uses MASCI vocabulary | tenant-config override (already part of C#2 work) |
| 4 | Some test-ids include `masci-` prefix | rename at leisure |
| 5 | Some collection names include `masci-` prefix | abstract to env var |
| 6 | Some env var names include `MASCI_` prefix | tolerable as long as they're internal-only |

---

## Strategic question for the operator

White Label has two very different shapes:

* **Shape A · Multi-Tenant Single Deployment** — All customers run on `*.platform.com`, share one MongoDB cluster (partitioned by `customer_id`), one Kubernetes cluster, one shared codebase. Cheaper to operate; harder to isolate failures and data.
* **Shape B · Per-Tenant Deployment** — Each customer gets their own pod, their own DB, their own subdomain. Easier to isolate; more expensive to operate; harder to roll out platform-wide fixes.

The codebase today is closer to **Shape B** than Shape A (single-tenant, hardcoded org name). Pivoting to Shape A is the heavier lift but yields more leverage long-term.

---

## Ranked White Label blocker priority

| Rank | Blocker | Why first |
|---:|---|---|
| 1 | **Decide Shape A vs Shape B explicitly** | Every downstream decision flows from this |
| 2 | **All Customer #2 blockers** | Foundation; ~ 9 wk (see Customer #2 doc) |
| 3 | **Brand parameterization extension** (URL slugs, email domains, MFA issuer, browser title, favicon, manifest, SEO meta, PDF templates, onboarding emails) | ~ 4 wk |
| 4 | **Support / Terms / Privacy parameterization** | Legal exposure if missed; ~ 2 wk |
| 5 | **Subdomain / DNS infrastructure** | ~ 1 wk + Emergent platform support |
| 6 | **Repo / doctrine redaction pass** | ~ 1 wk during freeze before first White Label deploy |

Estimated total: **~ 16 weeks** of focused work to reach 95 % White Label ready (assuming Customer #2 work runs first).

---

## What is NOT a White Label blocker (deliberately excluded)

* **OC-005 JHP** (helpful, not blocking)
* **Universal undo** (helpful, not blocking)
* **Verb harmonization** (helpful, not blocking)
* **Approve/Reject dropdown promotion** (helpful, not blocking)
* Most ITER500 Top 25 (helpful, not blocking)

A White Label customer can ship with the same UX friction MASCI has today, as long as the branding is theirs and the data is theirs. UX polish is desirable but not blocking.

---

## Recommendation

Do **not** pursue White Label until Customer #2 multi-tenancy is shipped and operational. Doing them in parallel risks paying for both costs without proving either model. Sequencing:

1. **Q3 2026** — Customer #2 multi-tenancy work
2. **Q4 2026** — White Label brand-extension layer on top
3. **Q1 2027** — First White Label tenant pitch

---

End of White Label blockers.
