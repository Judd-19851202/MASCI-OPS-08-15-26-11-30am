# R2 Lifecycle Activation — Operator Runbook

> Last updated: 2026-02-XX · Status: **READY for operator-initiated rollout**
> Scope: enable a 90-day auto-expiration rule on Cloudflare R2 — scoped ONLY to the new `backups/auto-90d/` sub-prefix. Legacy backups under `backups/*.zip` are untouched.
> Reading time: ~5 minutes. Execution time: ~10 minutes including Cloudflare UI.

This is your turn-by-turn guide. Follow the steps in order; do not skip ahead. Every command is copy-pasteable.

---

## 1. What you are approving (TL;DR)

After this runbook is complete:
- New backups (written hourly to `backups/auto-90d/<file>`) will **auto-delete after 90 days**.
- The R2 bucket footprint will reach a steady-state of **~90 GB** instead of growing forever.
- **No legacy backup is deleted.** The 482 objects already in `backups/*.zip` (about 19 GB) are NOT subject to this rule and survive untouched.
- The lifecycle rule is **idempotent** — applying it twice produces the same result.

If anything goes wrong, see § 9 "Rollback" below. Nothing in this runbook is irreversible.

---

## 2. What is already done (no operator action needed)

| Item | Status |
|---|---|
| Backend writes new backups to `backups/auto-90d/<file>` | ✅ Implemented in `server.py` (since 2026-02-XX) |
| Script `r2_lifecycle_apply.py` | ✅ Implemented & idempotent |
| Sentinel-based verify command (`--verify`) | ✅ Implemented |
| Legacy backups left under bare `backups/*.zip` | ✅ NOT in lifecycle scope |
| Bucket usage probe (`r2_usage_check.py`) | ✅ Implemented; warn at 45 GB, alert at 50 GB |

You do not need to write any code, edit the script, or change any prefix configuration. Your only inputs are: rotate the token → paste credentials → run two commands.

---

## 3. Rotate your Cloudflare R2 token

The current R2 token has `Object Read & Write` permission, which lets the backend upload backups but does **NOT** let it configure the bucket's lifecycle rules. You need a token with one extra permission: **Workers R2 Storage = Edit**.

### Step 3a — Open Cloudflare API Tokens

1. Go to **https://dash.cloudflare.com**
2. Sign in
3. Top-right → click your profile icon → **My Profile**
4. Left sidebar → **API Tokens**
5. Click the blue **Create Token** button (top-right of the table)

### Step 3b — Use the right template

You'll see a list of templates. Scroll to the bottom and click **Create Custom Token** → **Get started**.

(Do NOT use the prebuilt "Read and Write to R2 Storage" template — that's what you already have, and it doesn't include lifecycle:write.)

### Step 3c — Configure the custom token

On the "Create Custom Token" page:

1. **Token name:** `masci-r2-lifecycle-edit` (or anything memorable)
2. **Permissions** — click "+ Add more" until you have exactly **one** row:
   - First dropdown: **Account**
   - Second dropdown: **Workers R2 Storage**
   - Third dropdown: **Edit**
3. **Account Resources:**
   - Dropdown: **Include** → select your specific Cloudflare account (the one containing the `masci-backups` bucket). Do NOT use "All accounts".
4. **Client IP Address Filtering:** leave blank (skip)
5. **TTL:** leave as the default ("No expiry" or pick a 1-year window — your call; the script only needs the token until the lifecycle rule is applied)

Click **Continue to summary** at the bottom.

### Step 3d — Confirm and create

The summary screen should show one permission line:
```
Account · Workers R2 Storage · Edit
```

Click **Create Token**.

### Step 3e — Copy the credentials

Cloudflare shows the token **exactly once**. You'll see:

- An **Access Key ID** (looks like `a1b2c3d4e5f6g7h8`)
- A **Secret Access Key** (longer string, ~40 chars)

If Cloudflare shows you a single long token string instead of an Access Key ID / Secret pair, scroll down on the same page — there's a separate "Show keys for S3 clients" section. **You need the S3-compatible keys, not the bearer token.**

**Copy both values right now.** If you close this page without copying, you'll have to create another token.

---

## 4. Paste the credentials into the backend env

Open this file:
```
/app/backend/.env
```

Find these two lines (they exist already):
```
S3_ACCESS_KEY=<old read-write key>
S3_SECRET_KEY=<old read-write key>
```

Replace the values **after the `=`** with the new keys you just copied:
```
S3_ACCESS_KEY=<NEW Access Key ID from Step 3e>
S3_SECRET_KEY=<NEW Secret Access Key from Step 3e>
```

**Do not change:**
- `S3_ENDPOINT_URL`
- `S3_BUCKET`
- `S3_REGION`

Save the file.

Restart the backend so it picks up the new credentials:
```bash
sudo supervisorctl restart backend
```

Wait ~5 seconds. Confirm the backend is healthy:
```bash
curl -s "$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)/api/version" | python3 -c "import sys,json; print('release:', json.load(sys.stdin).get('release'))"
```

You should see a `release:` line with a 32-char hex string. If you see an error, see § 9 "Rollback".

---

## 5. Dry-run the lifecycle rule first

Always dry-run before applying. The dry-run prints exactly what would be sent to Cloudflare without making any change.

```bash
python3 /app/scripts/r2_lifecycle_apply.py --dry-run
```

**Expected output:**
```
Bucket            : masci-backups
Rule ID           : masci-backups-auto-90d
Filter prefix     : backups/auto-90d/
Expiration (days) : 90
Rules before      : 0
Rules after       : 1
------------------------------------------------------------
Will PUT:
[
  {
    "ID": "masci-backups-auto-90d",
    "Status": "Enabled",
    "Filter": { "Prefix": "backups/auto-90d/" },
    "Expiration": { "Days": 90 },
    "AbortIncompleteMultipartUpload": { "DaysAfterInitiation": 7 }
  }
]
------------------------------------------------------------
DRY-RUN — no changes applied.
```

**What to check before continuing:**
- ✅ `Bucket` matches your actual bucket name
- ✅ `Filter prefix` is exactly `backups/auto-90d/` (NOT bare `backups/`)
- ✅ `Expiration (days)` is `90`
- ✅ Last line says `DRY-RUN — no changes applied.`

If `Rules before` is greater than 0, the script will preserve any non-MASCI rules it finds — they will appear in the `Will PUT` list alongside ours. That's normal and intentional.

If you see `❌ FAIL: AccessDenied`, see § 9 "Rollback".

---

## 6. Apply the lifecycle rule

When the dry-run looks correct, apply for real:

```bash
python3 /app/scripts/r2_lifecycle_apply.py
```

**Expected output:**
```
Bucket            : masci-backups
Rule ID           : masci-backups-auto-90d
Filter prefix     : backups/auto-90d/
Expiration (days) : 90
Rules before      : 0
Rules after       : 1
------------------------------------------------------------
Will PUT:
[... same JSON as in § 5 ...]
------------------------------------------------------------
✅ Lifecycle applied.
✅ Verified — rule 'masci-backups-auto-90d' present (Status=Enabled).
```

The two final `✅` lines are what you're looking for. If both appear, the rule is live in Cloudflare's bucket configuration.

---

## 7. Run the sentinel verification

This is the round-trip integrity check. It writes a 1-line sentinel object under the lifecycle-scoped prefix, reads it back, confirms the rule is active, then cleans the sentinel up.

```bash
python3 /app/scripts/r2_lifecycle_apply.py --verify
```

**Expected output:**
```
Bucket : masci-backups
Key    : backups/auto-90d/_sentinel.txt
------------------------------------------------------------
✅ Step 1 — wrote sentinel object
✅ Step 2 — read-back matches
✅ Step 3 — lifecycle rule active · Status=Enabled Prefix=backups/auto-90d/ Days=90
✅ Step 4 — sentinel cleaned up
```

**All four steps must show `✅`.** If any line shows `❌` or `⚠️`, see § 8 "Failure response".

---

## 8. Failure response (by exit code)

The verify command returns specific exit codes. Run `echo $?` immediately after the verify if you need to check.

| Exit code | What happened | What to do |
|---|---|---|
| **0** | All four steps passed | ✅ Done. Go to § 10 "Sign-off". |
| **2** | Missing env vars (`S3_BUCKET`, `S3_ACCESS_KEY`, etc.) | You skipped Step 4 or pasted the wrong value. Re-check `/app/backend/.env`. |
| **4** | Step 1 failed (could not write sentinel) | Token rotation didn't work. Most likely cause: pasted the bearer token instead of the S3 Access Key / Secret pair. Re-do Step 3e — look for the "Show keys for S3 clients" section. |
| **5** | Step 2 failed (sentinel content mismatch) | R2 storage anomaly. Rare. Re-run verify. If it fails twice, open a Cloudflare support ticket. |
| **6** | Step 3 — rule NOT found in bucket config | The apply step in § 6 did not persist. Re-run `python3 /app/scripts/r2_lifecycle_apply.py` (apply, not verify). |
| **7** | Step 3 — rule found but misconfigured (wrong prefix or wrong days) | Someone else has edited the bucket config. Run `python3 /app/scripts/r2_lifecycle_apply.py --show` to inspect; re-run apply to re-assert our rule. |

For exit codes 4–7, **do not skip ahead**. The lifecycle is not safe until verify exits 0.

---

## 9. Rollback path

You have two layers of rollback. Use the gentler one first.

### Rollback A — Revert credentials to the old token
If anything looks wrong after the token swap (Step 4) — backend won't start, backups stop uploading, `/api/version` errors out — restore the previous values:

1. Open `/app/backend/.env`
2. Put the OLD `S3_ACCESS_KEY` and `S3_SECRET_KEY` back
3. `sudo supervisorctl restart backend`
4. Confirm `/api/version` returns 200

The platform is now back to its pre-runbook state. The lifecycle rule (if it was applied) is unaffected by which token the backend uses — once written to the bucket config, it lives there independent of the API token that wrote it.

### Rollback B — Remove the lifecycle rule entirely
If you decide you don't want the 90-day expiration after all:

1. Cloudflare dashboard → **R2** → click your bucket → **Settings** → **Object Lifecycle Rules**
2. Find the rule named `masci-backups-auto-90d`
3. Click **Delete**

Or programmatically:
```bash
# Inspect current rules
python3 /app/scripts/r2_lifecycle_apply.py --show

# Manual removal requires temporarily editing the script's
# desired_rule() to return None — easier to use the dashboard
```

**No backup is lost by removing the rule.** It just means new backups stop auto-expiring after 90 days and the bucket resumes growing.

### What rollback does NOT undo
- Objects that have already been deleted by an earlier lifecycle sweep are gone. **However, on day 0 of activation, no object is yet 90 days old in the `backups/auto-90d/` prefix** (the prefix is brand new as of 2026-02-XX). So removing the rule within the first 90 days of activation has zero data impact.

---

## 10. Sign-off

When § 7 returns exit 0 and all four verify steps show `✅`, append a row to the table below. A row in this table is the canonical record that R2 lifecycle is live.

| Date | Operator | Bucket | Rule ID | Verify exit | Notes |
|---|---|---|---|---|---|
| 2026-05-17 | E1 agent (operator-directed) | `masci-hub` | `masci-backups-auto-90d` | 0 (all 4 steps ✅) | Existing "Default Multipart Abort Rule" preserved. Initial token `masci-r2-lifecycle-s3` was used to apply, then immediately rotated due to public screenshot exposure. New long-lived token `masci-r2-backend` (Admin Read & Write) is now in `/app/backend/.env`; re-verify against the live rule passed all 4 steps. |

---

## 11. What happens AFTER activation

You don't need to do anything. The lifecycle rule runs on Cloudflare's side, asynchronously, on a sweep schedule (typically every 24h).

- New backups written today survive **90 days from their `LastModified`** timestamp.
- Day 91, Cloudflare's lifecycle sweeper deletes any object under `backups/auto-90d/` older than 90 days.
- Deletes are silent (no email, no alert) — the existing scheduler's daily `backup_health` Mongo row provides forensic evidence the deleted backups ever existed.
- Bucket usage probe (`r2_usage_check.py`) continues to run alongside the lifecycle — if a misconfiguration ever caused growth above the 45 GB warn / 50 GB alert thresholds, you'd see it surface in the scheduler logs.

**Monitor for the first 24–48h:** run `python3 /app/scripts/r2_lifecycle_apply.py --verify` once a day. All four `✅` lines should still appear. If they don't, see § 8.

---

## 12. Quarterly maintenance

- [ ] Re-run `python3 /app/scripts/r2_lifecycle_apply.py --verify` — confirm rule still present
- [ ] Run `python3 /app/scripts/r2_usage_check.py` — confirm bucket footprint is in the expected ~90 GB steady-state range
- [ ] Review whether the 90-day window is still right for your compliance posture (see `/app/memory/R2_RETENTION_AUDIT.md` § "Recommended retention policy" for the tradeoff table)

---

## 13. Honest residual notes

- **Cloudflare R2 lifecycle does not support tag-based filters as of 2026-02.** This is why the rule is scoped by prefix (`backups/auto-90d/`) rather than by a `retain=90d` tag. If Cloudflare adds tag filters later, we may revisit.
- **Lifecycle sweeps are eventually-consistent, not real-time.** A 91-day-old object may survive an extra few hours before the sweeper picks it up. This is fine for retention — not fine if you ever rely on hard guarantees of deletion at exactly 90.0 days. We don't.
- **The token from § 3 is now stored in `backend/.env`.** It has `Workers R2 Storage = Edit` which is broader than the old `Object Read & Write` token. Treat it like any other production credential. If you ever want to scope it back down after the rule is applied, you can issue a second, narrower token and rotate again — the lifecycle rule survives the swap.
- **The script preserves non-MASCI lifecycle rules.** If you (or someone else) ever adds another rule directly in the Cloudflare dashboard with a different `ID`, our script will keep it intact on the next `apply`.
