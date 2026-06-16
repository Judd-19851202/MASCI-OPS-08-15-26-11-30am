# WHITE-LABEL · INTEGRATION MATRIX

**Phase 10 deliverable.** Per-customer integration ownership.

| Integration | Today | Per-customer requirement |
|-------------|-------|---------------------------|
| **MongoDB Atlas** | Single MASCI cluster · two databases (`masci_safety_preview` · `masci_safety`) · two Atlas users (`masci_preview_user` · `masci_prod_user`) with credential-scoped isolation | Customer #2 gets its own Atlas DB(s) + scoped user. Same isolation pattern. **Cost**: ~$25-100/month per customer depending on tier. |
| **Cloudflare R2 (`S3_BUCKET=masci-hub`)** | Single bucket shared preview + production · env-tagged key prefixes · 90-day lifecycle | Customer #2 gets its own R2 bucket OR shared bucket with strict per-customer prefix. **Per-customer bucket strongly recommended** for clean isolation. **Cost**: ~$5/month base + storage. |
| **Resend (`RESEND_API_KEY`)** | Single MASCI Resend account · sender domain `mascigc.com` | Customer #2 needs OWN Resend account (own verified domain). NOT a shared API key. **Cost**: $20/month base + send volume. |
| **Sentry (`SENTRY_DSN`)** | Single MASCI Sentry project · service tag `masci-hub` | Customer #2 needs OWN Sentry project. **Cost**: ~$26/month per project. |
| **Motive (fleet telematics)** | Per-deploy env credential (if customer uses) | Each customer owns their Motive credentials. **Per-customer cost**: theirs. |
| **FleetWatcher** | Per-deploy env credential | Same — customer owns. |
| **MaintainX** | Per-deploy env credential (`services/maintainx_asset_sync.py` has MASCI-specific tag logic, 67 hits) | Customer owns the account · tag mapping needs to be parameterized away from MASCI-specific tag names. |
| **DNS / domain** | `mascidocs.com` (production) · `safety-audit-mobile-1.preview.emergentagent.com` (preview) | Customer #2 needs OWN domain + DNS records. CNAME to Emergent infra. **Cost**: domain + DNS provider. |
| **SSL** | Emergent-managed | Customer #2 inherits Emergent SSL for their CNAME. |
| **Backups (R2 + email)** | Hourly R2 + nightly email | Customer #2 backups land in their R2 bucket + go to their `BACKUP_EMAIL_TO`. Already env-driven. |

## Per-customer integration ownership model

- **Platform-shared (Emergent infra)**: Kubernetes pod · supervisor · CDN · SSL termination
- **Per-customer (each customer pays)**: Atlas DB · R2 bucket · Resend account · Sentry project · domain · their own Motive/FleetWatcher/MaintainX
- **Configuration-only**: every per-customer integration credential lives in that customer's `.env`

## Integration tag/mapping leakage

`services/maintainx_asset_sync.py` (67 MASCI hits) has hardcoded MASCI-specific tag prefixes, location names ("Massey Yard", "Port Orange"), and category mappings. Customer #2 cannot use this file as-is; it would either need:
- A per-customer mapping config file, OR
- A new abstraction (`AssetSyncProvider`) that reads tag rules from BrandConfig

**Recommendation**: When adding Customer #2, leave MASCI's MaintainX sync intact; build a new file `bobs_maintainx_asset_sync.py` for customer #2 (clone-rebrand model). Later (Model C SaaS), abstract.

## Verdict

Integration layer is **per-customer-credential ready** (env-driven) for everything except MaintainX tag mappings. The mapping issue is contained and can be solved per-customer at deploy time.
