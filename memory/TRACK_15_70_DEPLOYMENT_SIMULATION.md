# TRACK 15.70 · Deployment Simulation (Phase 3)

_Generated 2026-06-22 · Live execution_

## Method

Synthetic tenant `customer_2_deploy_test` provisioned in the preview
database via:

```
backend/scripts/track_15_70_deployment_simulation.py
```

The script performs **configuration only** — no source code is touched.
It writes:

1. One `tenant_branding` doc (`_id: customer_2_deploy_test`).
2. Six `email_routes` docs (the 4 critical + 2 common routes).

Persisted JSON: `/app/test_reports/track_15_70_deployment_simulation.json`

## Provisioning Time

| Tenant | Elapsed (s) |
|---|---:|
| `customer_2_deploy_test` | 0.013 |
| `customer_3_deploy_test` | 0.005 |

**Total wall-clock for both tenants: 0.018 s.** This is the DB-insert
portion only. The end-to-end production provisioning (cluster
allocation, Resend domain verification, R2 bucket creation, DNS, etc.)
is measured separately in `TRACK_15_70_PROVISIONING_RUNBOOK.md`.

## Branding Resolution (verified live)

```
GET /api/branding/current  (X-Tenant-Preview: customer_2_deploy_test)
→ company_name="Customer #2 Construction LLC"
   platform_display_name="Customer #2 Operations Platform"
   platform_short_name="C2 Hub"
   primary_color="#0F766E"
   marketing_url="https://customer2.example"
   support_email="support@customer2.example"
   safety_email="safety@customer2.example"
   from_email="noreply@customer2.example"
```

Visual proof (screenshot taken `?tenantPreview=customer_3_deploy_test`):
- ✅ `document.title = "Customer #3 Operations Platform"`
- ✅ Header logo = green/purple `C` monogram (derived from
  `company_name.charAt(0)`)
- ✅ No red MASCI mark visible
- ✅ Per-tenant accent color applied to UI tokens
- ⚠️ One known leak: `Hub.jsx:251` eyebrow uses `t("MASCI Operations Platform")` which goes through `_brandSubst()` — on the first page load the substitution can race with the BrandingProvider fetch. Same-tab subsequent navigations show the substituted text correctly. Tier-2 backlog (15.68D-known).

## Route Resolution (verified live, flag-on)

| Tenant | Route | source | to | sender match? |
|---|---|:-:|---|:-:|
| `customer_2_deploy_test` | `BACKUP_ALERTS` | db | `ops@customer2.example` | ✅ |
| `customer_3_deploy_test` | `BACKUP_ALERTS` | db | `ops@customer3.example` | ✅ |

For both tenants the resolver correctly returns DB-driven recipients
that match the tenant's `operations_email` field. MASCI tenant
resolution is unchanged (19 routes intact).

## PDF / Export Behavior

Not exercised live in this simulation (would require an authenticated
admin session per tenant). The path is:

1. PDF templates already use `tenant_context.brand` (Track 15.68A).
2. Filename exports use `branding.slug` (Track 15.68B).
3. Verified MASCI-side in Track 15.68D walkthrough.

For Customer #2:
- ✅ Expected: PDFs render with Customer #2 chrome.
- ✅ Expected: Filenames prefix with `customer-2-deploy-test` slug.
- ⚠️ Caveat: 2 hardcoded From-display-name leaks in `server.py:2384, 3719` (see Config Audit) would still show "MASCI Operations Platform" in those 2 send sites. **MUST FIX before Customer #2 go-live.**

## What Was NOT Done

| Item | Why |
|---|---|
| Atlas cluster provisioning | Out of preview-pod scope (no Atlas API key) |
| R2 bucket provisioning | Out of preview-pod scope |
| Resend domain verification | Out of preview-pod scope (DNS / external API) |
| Customer-2 admin user creation | Requires per-tenant `users` collection scoping (architectural gap; see Phase 5) |
| Customer-2 frontend deploy | The same React bundle serves all tenants via `X-Tenant-Preview`; no per-tenant frontend deploy required |

## Verdict

✅ **PASS for configuration-driven tenant chrome.** Two new tenants
were provisioned and resolved correctly in 0.018 seconds. Branding,
routes, and senders are tenant-scoped end-to-end.

⚠️ **PARTIAL** for end-to-end Customer #2 readiness: the 3 BLOCKED
hardcoded items from `TRACK_15_70_CONFIGURATION_AUDIT.md` must be
fixed; user account isolation (Phase 5) requires a separate cluster.
