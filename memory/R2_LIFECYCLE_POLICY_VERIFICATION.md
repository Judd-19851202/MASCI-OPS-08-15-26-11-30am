# R2_LIFECYCLE_POLICY_VERIFICATION.md
## Cloudflare R2 Bucket Lifecycle Verification + Sign-Off
## iter430 · 2026-05-25

---

## Why this matters

Without a Cloudflare R2 bucket-level lifecycle rule, every hourly + nightly archive stays in R2 forever. At 89.5 MB per archive × 24 / day × 30 days = **~64 GB / month** of permanent growth. Within 5 months you'd cross the 10 GB free tier and start paying $0.015/GB-mo. Within 18 months you'd be at $30/mo for backup storage alone — entirely avoidable.

With a 30-day delete rule, R2 stays at ~64 GB **steady-state** = $0.96/mo at most.

---

## Required policy

| Field | Value |
|---|---|
| **Bucket name** | `masci-hub` |
| **Rule name** | `backup-30day-purge` |
| **Prefix filter** | `backups/auto-90d/` |
| **Action** | Delete |
| **After** | 30 days |
| **Expected steady-state storage** | ~64 GB |
| **Expected monthly cost** | < $1.00 |

---

## Operator verification steps

### Step 1 · Navigate to the bucket settings

1. Sign in to https://dash.cloudflare.com
2. Select your account
3. Left sidebar → **R2 Object Storage**
4. Click the **masci-hub** bucket
5. Top tab → **Settings**

### Step 2 · Check existing lifecycle rules

Scroll to **Object lifecycle rules**.

| State you find | Action |
|---|---|
| No rules exist | Go to Step 3 — create the rule |
| A rule exists matching the table above | Skip to Step 4 — verify it's enabled |
| A rule exists but with WRONG prefix or wrong day count | Edit the rule to match the table above |

### Step 3 · Create the lifecycle rule (if none exists)

1. Click **Add lifecycle rule**
2. Name: `backup-30day-purge`
3. Apply to: **objects with prefix** → `backups/auto-90d/`
4. Action: **Delete objects** → after **30 days**
5. Save

### Step 4 · Verify it's enabled

1. Confirm the rule is **active** (toggle on)
2. Confirm prefix shows `backups/auto-90d/`
3. Confirm action shows `Delete objects after 30 days`

### Step 5 · Take a verification screenshot

Capture a screenshot of the lifecycle rules panel showing:
- Bucket name `masci-hub`
- Rule name `backup-30day-purge`
- Status `active`
- Prefix `backups/auto-90d/`
- Action `Delete after 30 days`

Save to your secured ops folder. Optional: drop the screenshot back here in chat — I'll log it in `/app/memory/R2_LIFECYCLE_POLICY_SCREENSHOT_<date>.md`.

### Step 6 · Forecast verification

After 30+ days of operations, verify by:

1. Cloudflare R2 → bucket `masci-hub` → metrics
2. **Storage** should hover around ~64 GB (varies with archive size)
3. **Object count** should be ~720 (≈ 24 archives/day × 30 days)
4. **Class A ops** should match scheduler cadence
5. If storage exceeds 100 GB and is still growing, the rule didn't take effect — re-verify

---

## Verification matrix

| Check | Status |
|---|---|
| Lifecycle rule exists on `masci-hub` bucket | ☐ |
| Rule prefix is `backups/auto-90d/` | ☐ |
| Rule retention is 30 days | ☐ |
| Rule status is **active** | ☐ |
| Screenshot captured + filed | ☐ |
| After 30+ days, R2 storage stable at ~64 GB | ☐ (re-check Q3 2026) |

---

## What happens without this rule

| Month | R2 storage if no rule | R2 monthly cost |
|---|---|---|
| Today (1 month live) | ~64 GB | $0 (under free 10 GB) — wait, this is already over · so $0.80/mo at $0.015/GB-mo |
| Month 3 | ~192 GB | $2.88/mo |
| Month 6 | ~384 GB | $5.76/mo |
| Year 1 | ~768 GB | $11.52/mo |
| Year 3 | ~2.3 TB | $34.50/mo |
| Year 5 | ~3.8 TB | $57/mo |

With the rule: **steady-state ~64 GB at ~$0.96/mo indefinitely.**

---

## Sign-off

Date set up: _______________________
Operator: ______________________________
Screenshot location: _______________________
Lifecycle rule status: ☐ active ☐ not yet set

After 30 days, re-verify retention is working as expected. Then this doc can be marked closed.

---

## Companion docs

- `PHASE26_2_BACKUP_CONTINUITY_CERTIFICATION.md` — covers the operational pipeline
- `RESTORE_RUNBOOK.md` — covers how to restore from R2 archives
- `HIDDEN_COST_AND_SCALING_RISK_REPORT.md` § 5 — covers why this rule exists

---

End of R2 Lifecycle Policy Verification.
