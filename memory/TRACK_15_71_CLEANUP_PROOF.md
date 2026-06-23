# TRACK 15.71 · Cleanup Proof

_2026-06-23_

## Production Cluster — Untouched

This deploy ships **zero data mutations** to production:
- Zero schema migrations
- Zero backfills
- Zero test inserts into the production cluster
- Zero `tenant_branding` docs created in production (the 2 synthetic tenants are preview-only)
- Zero `email_routes` docs created in production
- Zero test users
- Zero test emails sent to live distros
- Zero leftover synthetic records in production

## Preview Cluster — Tracked Artifacts (NOT production)

The preview cluster contains some pre-flight artifacts. They are
clearly named and isolated; they do NOT ship to production:

| Artifact | Location | Action |
|---|---|---|
| `customer_2_deploy_test` | `tenant_branding._id=customer_2_deploy_test` | Preview only. Optionally cleanable. |
| `customer_3_deploy_test` | `tenant_branding._id=customer_3_deploy_test` | Preview only. Optionally cleanable. |
| 6 `email_routes` docs per test tenant | `tenant_key in [customer_2_deploy_test, customer_3_deploy_test]` | Preview only. Optionally cleanable. |
| 20+ dry-run audit rows | `email_routing_audit_v2` (preview cluster) | Preview only. Append-only — DO NOT delete per directive's audit-preservation rule. |
| `track_15_68_tenant_test_delete` | legacy synthetic tenant from 15.68 | Preview only. Leave or clean — operator's choice. |

## Cleanup Path (preview, if desired)

```python
# Synthetic deploy-test tenants
await db.tenant_branding.delete_many({"_id": {"$in": ["customer_2_deploy_test", "customer_3_deploy_test"]}})
await db.email_routes.delete_many({"tenant_key": {"$in": ["customer_2_deploy_test", "customer_3_deploy_test"]}})

# Audit rows: DO NOT delete per directive's audit-preservation rule.
```

Recommended: **leave them in preview** as dress-rehearsal fixtures.

## No Customer #2 Active in MASCI Production UI

Verification path:
- `tenant_context.default_tenant()` returns `masci` (hardcoded default).
- Production has no `customer_2*` doc in `tenant_branding`.
- Production frontend served from `mascidocs.com` → no `?tenantPreview=` query param → always resolves to masci.

A MASCI production user has zero way to see Customer #2 chrome. The synthetic tenants are visible only to:
- Preview-pod URL with explicit `?tenantPreview=customer_2_deploy_test` query param.
- Operator with admin access to the preview DB.

## Verdict

✅ **Production cluster CLEAN · zero test data · zero synthetic tenants · zero Customer #2 active in MASCI UI.**
✅ **Preview cluster contains expected pre-flight fixtures — clearly suffixed `_deploy_test`, isolated from production.**
