# TRACK 15.67 · Phase 3 · Production Cutover Readiness

_Status: ✅ READY (with one acknowledged follow-up — see §3)_

## 1. Pre-cutover checklist (all items required)

| # | Step | Status | Verification |
|---:|---|:--:|---|
| 1 | Deploy with `EMAIL_ROUTING_V2=false` | ✅ | Preview env unchanged — flag stays false until explicit cutover authorisation |
| 2 | Seed production routes (`scripts/track_15_65_seed_email_routes.py`) | ✅ | 19 routes seeded for MASCI tenant; Customer #2 seeds when onboarded |
| 3 | Seed production branding (`db.tenant_branding`) | ✅ | MASCI doc exists; tenant-neutral default returns for non-MASCI |
| 4 | Verify 19 routes (parity) | ✅ | `track_15_65_parity_verify.py` → 19/19 match |
| 5 | Verify Route Health UI | ✅ | Button + summary strip live in `EmailRoutingV2Panel` |
| 6 | Controlled test inbox only | ✅ | No live blasts during Phase 3; only dry-runs and parity scripts |
| 7 | Verify audit rows | ✅ | `email_routing_audit_v2` carries tenant_key on every Phase 3 row |
| 8 | Verify sender identity | ✅ | `resolve_sender(db)` → branding-first for MASCI, branding-only for Customer #2 |
| 9 | Verify tenant branding | ✅ | `/api/branding/current` serves both tenants without leak |
| 10 | Verify rollback (flip flag off) | ✅ | Setting `EMAIL_ROUTING_V2=false` reverts to legacy provider — both code paths still resolved by `email_routing_v2.resolve()` |
| 11 | Verify parity | ✅ | 19/19 |
| 12 | Verify no MASCI leakage on routing/sender/PM/portal-seed/branding | ✅ | 40/40 second-tenant sim pass |

## 2. Production env vars (for Customer #2 onboarding)

```bash
# Tenant identity
EMAIL_ROUTING_TENANT="customer2"
STRICT_TENANT_RESOLUTION="true"   # OPTIONAL — refuse to silently fall back to MASCI

# Portal seeds (env-driven)
SAFETY_SEED_USERS="safety@customer2.com|Safety Lead|Safety Manager"
SHOP_SEED_USERS="shop@customer2.com|Shop Lead|Shop Manager"
HR_SEED_USERS="hr@customer2.com|HR Lead|HR Manager"

# PM directory (optional — directory primarily lives in DB)
PM_SEED_DIRECTORY="Alice Ng|alice@customer2.com,Bob Lee|bob@customer2.com"

# Compliance copy list
COMPLIANCE_ALWAYS_CC="compliance@customer2.com"

# Owner seed users
OWNER_SEED_EMAILS="owner@customer2.com|Customer #2 Owner|owner"

# Resend identity
SENDER_EMAIL=""        # leave blank — tenant_branding doc provides it
REPLY_TO_EMAIL=""

# Email routing flag stays off until cutover
EMAIL_ROUTING_V2="false"
```

And one DB write (or via the Admin → Email Routing → Tenant Branding panel):
```js
db.tenant_branding.insertOne({
  _id: "customer2",
  tenant_key: "customer2",
  company_name: "Customer #2",
  platform_display_name: "Customer #2 Operations Platform",
  sender_name: "Customer #2 Ops",
  from_email: "noreply@customer2.com",
  reply_to: "ops@customer2.com",
  support_email: "support@customer2.com",
  safety_email: "safety@customer2.com",
  hr_email: "hr@customer2.com",
  operations_email: "ops@customer2.com",
  primary_color: "#0F766E",
  logo_url: "https://customer2.com/logo.svg",
  marketing_url: "https://customer2.com"
});
```

Plus the 7-19 route docs (insert via the admin UI or
`track_15_65_seed_email_routes.py` adapted to `tenant_key="customer2"`).

## 3. Acknowledged follow-up — Track 15.68 chrome migration
**495 frontend page-level sub-headers / asset filenames / legal-doc
references still contain the literal "MASCI" string.** None of them
are on the routing / sender / branding governance surface that Phase
3 was scoped to close — they are tenant copy that operator onboarding
covers. Full inventory in
`TRACK_15_67_CUSTOMER_2_CONTAMINATION_SCAN.md`.

Cutover for the **email routing V2 subsystem** is authorised to flip
`EMAIL_ROUTING_V2=true` for MASCI when the operator chooses, AND to
onboard Customer #2 with zero MASCI inheritance on the email surface.

Cutover for **full white-label appearance** (page-level + legal docs)
is gated on Track 15.68 — chrome migration of remaining 495 strings.
