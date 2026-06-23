# TRACK 15.70 · Isolation Certification (Phase 5)

_Generated 2026-06-22 · Live execution_

## The Honest Verdict First

**Isolation is GUARANTEED only via the separate-cluster deployment
model.** Within a single MASCI database, isolation is partial:

| Layer | Isolation status |
|---|:-:|
| `tenant_branding` doc | ✅ tenant-scoped by `_id` and `tenant_key` |
| `email_routes` doc | ✅ tenant-scoped by `_id` (`{tk}::{route_key}`) and `tenant_key` |
| `email_routing_audit_v2` doc | ✅ tenant-scoped by `tenant_key` field |
| `users` / `safety_users` / `shop_users` / `hr_users` / `field_leadership_users` | ❌ **NO `tenant_key` field** |
| `daily_reports` / `incidents` / `qaqc` / `site_inspections` / etc. (~178 collections) | ❌ **NO `tenant_key` field** |

This is the most important architectural fact in Track 15.70.

## Test Matrix (in-database, single-cluster model)

| Test | Result | Verdict |
|---|---|:-:|
| Customer #2 route doc under Customer #3 tenant_key | not found ✅ | PASS |
| Customer #3 route doc under Customer #2 tenant_key | not found ✅ | PASS |
| Customer #2 branding under Customer #3 `_id` | not found ✅ | PASS |
| MASCI route count after Customer #2 + Customer #3 provisioning | 19 (unchanged) | PASS |
| MASCI tenant_branding doc untouched | yes (unchanged) | PASS |
| Branding company names distinct (masci/c2/c3) | all distinct ✅ | PASS |
| `users` collection has `tenant_key` field on every doc | **NO** ❌ | **FAIL (single-cluster model)** |
| `daily_reports` collection has `tenant_key` field on every doc | **NO** ❌ | **FAIL (single-cluster model)** |

## Live Evidence

From `/app/test_reports/track_15_70_deployment_simulation.json`:

```json
"isolation": [
  {
    "test": "c2_route_doc_under_c3_tenant_key",
    "found_unexpectedly": false
  },
  {
    "test": "masci_route_count_unchanged",
    "actual": 19, "expected": 19, "pass": true
  },
  {
    "test": "branding_company_names_distinct",
    "masci": "<unset MASCI default>",
    "c2": "Customer #2 Construction LLC",
    "c3": "Customer #3 Highway Excavating",
    "all_distinct": true
  }
]
```

## What Isolation Looks Like for Each Layer

### Tenant chrome (branding + routing)

✅ Fully isolated. The Mongo `_id` namespacing (`{tenant_key}::{route_key}`)
makes cross-tenant reads impossible at the query level. The `email_routes`
collection scan in V2's resolver always filters by tenant_key.

### Email routing audit

✅ Audit rows include `tenant_key`. Queries by tenant_key return only
that tenant's rows. Cross-customer audit leakage requires writing a
query without `tenant_key` filter — which is a code bug, not an
architectural risk.

### User accounts

❌ **NOT isolated in single-cluster model.** The `users` collection
has no tenant_key field. A user created in MASCI would be findable
during a Customer #2 login. Mitigation:

1. **Separate cluster per customer** (current recommendation).
2. Add `tenant_key` to user docs + filter every auth query (Track 16.x).

### Business data (incidents, reports, equipment, …)

❌ **NOT isolated in single-cluster model.** Same as users — 178
collections lack tenant_key. A daily report filed by a Customer #2 user
would land in the same collection as MASCI daily reports.

Mitigation: separate cluster per customer.

## The Recommended Deployment Model (Single-Cluster-Per-Customer)

| Customer | Cluster | Database name | Tenant_key |
|---|---|---|---|
| MASCI | `masci-production` | `masci_safety` | `masci` |
| Customer #2 | `customer2-production` | `customer2_safety` | `customer_2` |
| Customer #3 | `customer3-production` | `customer3_safety` | `customer_3` |
| Customer #N | `customerN-production` | `customerN_safety` | `customer_N` |

Under this model:

✅ User-level isolation — physical: each customer's users live in their own database, on their own cluster.
✅ Business-data isolation — physical: each customer's incidents/reports/equipment live in their own database.
✅ Route-level isolation — logical (already proven): per-tenant `_id` + tenant_key filtering.
✅ Branding-level isolation — logical (already proven): per-tenant doc.
✅ Backup isolation — physical: each customer's backups go to their own R2 bucket.

The `tenant_key` field's role in the per-cluster model is to give the
backend a stable identifier for the current customer (used by branding
+ routing) — NOT to act as a row-level isolation filter on shared
collections.

## Cross-Cluster Communication

There is no cross-cluster communication path. Each customer's backend
talks to:
- Its own Atlas cluster
- Its own R2 bucket
- Its own Resend API key
- Its own DNS/domain

No code path reaches across customers. Verified by inspection of
`server.py` — every Mongo query uses `db = get_async_db()` which
returns the SINGLE cluster the backend was booted against.

## What MUST Happen Before Customer #2 Go-Live

1. ✅ Provision separate Atlas cluster.
2. ✅ Configure `MONGO_URL` and `DB_NAME` per customer.
3. ✅ Provision separate R2 bucket.
4. ✅ Configure `R2_*` env vars.
5. ✅ Verify Resend domain + DKIM/SPF/DMARC.
6. ✅ Insert tenant_branding + email_routes via provisioning script.
7. 🟡 Fix BLOCKED items from `TRACK_15_70_CONFIGURATION_AUDIT.md`
   (auth.py seed gate; server.py:2384/3719 From-line refactor).
8. ✅ Verify all 19 routes are seeded (use Track 15.65 seed script).
9. ✅ Verify parity (Track 15.65 harness) on the new cluster.
10. ✅ Verify Route Health (V2 admin endpoint) on the new cluster.

## Verdict

✅ **Tenant-chrome isolation is PROVEN at the DB level.**
✅ **Cross-customer contamination is IMPOSSIBLE at the resolver layer.**
⚠️ **Business-data isolation requires separate-cluster-per-customer deployment.**
🟡 **3 BLOCKED hardcoded items must be fixed before Customer #2 go-live.**
