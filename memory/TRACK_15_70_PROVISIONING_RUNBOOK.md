# TRACK 15.70 · Provisioning Runbook (Phase 7)

_Generated 2026-06-22_

## Honest End-to-End Time

**Target: 30 minutes or less.**
**Reality: 4–8 hours for a brand-new customer** (excluding DNS
propagation wait time, which can be hours-to-overnight).

The 30-minute target is achievable only for the **DB-insert portion**
(branding + routes). The full pipeline includes cluster allocation,
domain verification, and frontend deploy — those are external
dependencies on third-party services with their own latency.

This runbook is honest about both numbers.

## Phase A · Cluster & Service Allocation (operator hands-on ~30-60 min, third-party wait ~30-180 min)

### A1 · MongoDB Atlas cluster

```
1. Atlas console → Create cluster → tier per Customer SKU
2. Region: customer-chosen (default us-east-1)
3. Allowlist: ForgedOps deploy region IPs
4. Backup: enable continuous + PIT
5. Capture: MONGO_URL (with embedded creds)
```

⏱️ Operator: ~15 min · Atlas provisioning: ~5-15 min.

### A2 · Cloudflare R2 bucket

```
1. R2 console → Create bucket → customerN-backups
2. Create token: read+write on this bucket only
3. Capture: R2_ACCOUNT_ID, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_KEY
```

⏱️ Operator: ~5 min.

### A3 · Resend domain + DNS

```
1. Resend dashboard → Add domain → customer.example
2. Add SPF, DKIM, DMARC records to customer's DNS
3. Wait for verification (5 min - overnight depending on DNS TTL)
4. Capture: RESEND_API_KEY (or share existing)
```

⏱️ Operator: ~10 min · DNS wait: ~30 min - overnight.

### A4 · Frontend deploy (per-customer)

```
1. Deploy the same React bundle to customerN.example
2. Set REACT_APP_BACKEND_URL=https://api.customerN.example
3. No code change — the same bundle serves any tenant
```

⏱️ Deploy: ~5-10 min.

### A5 · Backend deploy (per-customer)

```
1. Deploy the same backend container/code
2. Set MONGO_URL, DB_NAME, EMAIL_ROUTING_V2=true, RESEND_API_KEY, etc.
3. Same code — only env differs
```

⏱️ Deploy: ~5-10 min.

## Phase B · Tenant Configuration (operator hands-on ~10 min)

### B1 · Insert tenant_branding

```bash
python3 backend/scripts/track_15_70_deployment_simulation.py
# (manifest-driven version — adapt for production by editing the
#  CUST2/CUST3 dicts to the real customer's data, or pass via JSON)
```

Or directly:

```python
db.tenant_branding.update_one({"_id": "customer_2"}, {"$set": {
    "_id": "customer_2",
    "tenant_key": "customer_2",
    "slug": "customer-2",
    "company_name": "...",
    "platform_display_name": "...",
    "platform_short_name": "...",
    "primary_color": "#...",
    "accent_color": "#...",
    "logo_url": "https://...",
    "marketing_url": "https://...",
    "support_email": "...",
    "safety_email": "...",
    "hr_email": "...",
    "operations_email": "...",
    "from_email": "noreply@customer.example",
    "reply_to": "support@customer.example",
    "sender_name": "...",
}}, upsert=True)
```

⏱️ ~2 min.

### B2 · Seed 19 email_routes

```bash
# Adapt track_15_65_seed_email_routes.py to read a per-customer manifest
# (currently MASCI-only) OR run a small wrapper that copies the route
# bundle from track_15_70_deployment_simulation.py expanded to all 19.
TENANT_KEY=customer_2 python3 scripts/track_15_70_seed_per_customer_routes.py --apply
```

⏱️ ~2 min.

### B3 · Verify route health

```bash
curl -s https://api.customer.example/api/admin/email-routing/v2/routes \
  -H "X-Admin-Token: $ADMIN_TOK"
```

Expect: 19 routes, 0 red critical, 0 amber critical.

⏱️ ~2 min.

### B4 · Validate branding render

Visit `https://customer.example/` in a browser; verify:
- Tenant logo / monogram (not red MASCI mark)
- Title bar shows customer's `platform_display_name`
- Footer shows customer's company name
- Email envelope From: shows customer's `from_email` (manual probe send)

⏱️ ~3 min.

### B5 · Validate parity

```bash
python3 scripts/track_15_65_parity_verify.py --allow-prod
```

Expect: 19/19 match.

⏱️ ~1 min.

### B6 · Admin user creation

Create the customer's super-admin user via the admin signup endpoint
or by direct insert into `users` (with role=owner).

⏱️ ~5 min.

## Phase C · Go-Live Checklist

| ✓ | Step |
|:-:|---|
| ☐ | Atlas cluster provisioned, backup verified |
| ☐ | R2 bucket created, write access verified |
| ☐ | Resend domain verified (DKIM/SPF/DMARC) |
| ☐ | Backend deployed with per-customer env vars |
| ☐ | Frontend deployed at customer URL |
| ☐ | `tenant_branding` doc inserted |
| ☐ | 19 `email_routes` docs seeded |
| ☐ | Parity verify 19/19 |
| ☐ | Route Health 0 red critical |
| ☐ | Branding visually verified (3+ screens) |
| ☐ | Probe send (controlled inbox) succeeded |
| ☐ | Super-admin user created |
| ☐ | Customer admin trained on Admin → Branding + Routing UI |
| ☐ | Cutover communications sent to customer |

## Time Budget

| Phase | Operator hands-on | External wait |
|---|---:|---:|
| A · Allocation | 30-60 min | 30 min – overnight (DNS) |
| B · Configuration | 10 min | — |
| C · Go-live | 10 min | — |
| **Total** | **~50-80 min hands-on** | **+ DNS propagation** |

This is the honest number. **The directive's 30-minute target is
achievable only for repeat customers** where Atlas / R2 / Resend infra
is reusable (e.g., same Resend domain). For a truly fresh customer
with their own domain, 4-8 hours of elapsed time is realistic, of
which only ~50-80 minutes is hands-on work.

## What Would Make It Truly 30 Minutes

1. **Atlas pre-provisioning automation**: pre-create clusters for the next
   3-5 customers via Atlas API.
2. **Resend "ForgedOps" parent domain**: customers use `customer.forgedops.com`
   subdomains until their custom domain is ready (avoids DNS wait).
3. **Provisioning manifest format**: a single YAML file (`customer.yaml`)
   that drives a one-shot script:
   ```yaml
   tenant_key: customer_2
   company_name: ...
   modules: [core, safety, pm]   # for when 16.x ships
   admin_users:
     - email: ...
       role: owner
   ```
4. **Module gating** (Track 16.x).
5. **Backend schema rename** for the 3 BLOCKED items (Track 16.x).

Once those are in place, 30 minutes is realistic for repeat customers
on a shared Resend parent domain.

## Verdict

⚠️ **PARTIAL** — runbook is complete and operator-executable.
End-to-end time is **4-8 hours per fresh customer** (most is external
service wait). The directive's 30-minute target requires the four
follow-up items above and is achievable in Track 16.x.
