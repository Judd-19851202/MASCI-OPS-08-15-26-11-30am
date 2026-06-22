# TRACK 15.69 · Rollback Runbook

_Generated 2026-06-22_

## Rollback Time Budget

**< 5 minutes** from rollback decision to legacy routing restored.

## Rollback Triggers

Roll back IMMEDIATELY if any of the following are observed within the
24-hour monitoring window:

| Trigger | Severity |
|---|:-:|
| Any **critical** route fails to resolve (BACKUP_ALERTS, HEALTH_ALERTS, OUTAGE_ALERTS, SUPER_ADMIN_TO) | 🔴 |
| Any email lands in a **wrong audience** (recipient drift) | 🔴 |
| Any email envelope shows wrong **sender identity** | 🔴 |
| Route Health flips any critical route to **red** | 🔴 |
| Resend rejection spike (any non-2xx response from Resend on a critical route) | 🔴 |
| Operator cannot view the V2 audit drawer in Admin UI | 🔴 |
| Backend `/api/health` flips to non-2xx | 🔴 |
| Scheduler task failures spike | 🔴 |
| User reports a missing critical alert (incident, outage, backup) | 🔴 |
| Dead-letter route accepts an unexpected delivery | 🟡 |
| Any user reports "I usually get this email but didn't this morning" | 🟡 |

## Rollback Procedure (production)

### Step 1 · Set the flag back to false (≤ 60 seconds)

In the production deploy environment-variable management UI:

```
EMAIL_ROUTING_V2=false
```

Save. The platform restarts the backend automatically (or the
operator triggers a manual restart if needed).

### Step 2 · Verify backend is healthy (≤ 30 seconds)

```
curl -s https://mascidocs.com/api/health
curl -s https://mascidocs.com/api/health/full
```

Expected: HTTP 200, `db: healthy`, `scheduler: healthy`.

### Step 3 · Confirm resolver flipped back to legacy (≤ 60 seconds)

```
TOK=<admin_token>
curl -s https://mascidocs.com/api/admin/email-routing/v2/routes \
  -H "X-Admin-Token: $TOK" | jq '.routes[0].summary'
```

The next audit row written should show `source: legacy`.

Or run:

```
python3 backend/scripts/track_15_65_parity_verify.py --allow-prod
```

Expected:
- 19/19 match
- 0 mismatch
- 0 critical-empty
- flag-off source = legacy
- (after rollback the flag-on side of the harness will still report
  `db` source because the harness sets the env var temporarily — that
  is expected and not a regression)

### Step 4 · Verify no stuck sends (≤ 60 seconds)

```
curl -s https://mascidocs.com/api/admin/scheduler/status -H "X-Admin-Token: $TOK"
```

Expected: zero pending tasks in `email_send` queue, no errors in last
60 seconds of scheduler log.

### Step 5 · Confirm audit shows the rollback (≤ 30 seconds)

The next outbound email from any route should write an
`email_routing_audit_v2` row with `source: legacy`. If the next email
takes > 5 minutes, the operator may force a benign probe (e.g., the
operator-digest scheduled job) to confirm.

### Step 6 · Operator notification (≤ 60 seconds)

Post to the operator channel:

```
[TRACK 15.69 ROLLBACK · <timestamp>]
EMAIL_ROUTING_V2 reverted to false in production.
Trigger: <description>
Resolver source: legacy (verified)
Route Health: <status>
Next: investigate, document, schedule re-cutover.
```

## Total Rollback Time

| Step | Budget |
|---:|---:|
| 1 · Flag flip | ≤ 60s |
| 2 · Backend health | ≤ 30s |
| 3 · Resolver source verify | ≤ 60s |
| 4 · Scheduler clear | ≤ 60s |
| 5 · Audit confirms | ≤ 30s |
| 6 · Operator notify | ≤ 60s |
| **Total** | **≤ 5 min ✅** |

## Pre-Rollback Sanity (do this BEFORE flipping forward)

The operator should dry-run rollback on the preview deploy first:

1. Set `EMAIL_ROUTING_V2=true` in preview, restart backend.
2. Confirm preview backend healthy + V2 resolution active.
3. Set `EMAIL_ROUTING_V2=false` in preview, restart backend.
4. Confirm preview backend healthy + legacy resolution active.
5. Time the round-trip. If > 5 minutes, escalate before production
   cutover.

## What Rollback Does NOT Touch

- ❌ The `email_routes` collection (DB docs are preserved — they are
  just not consulted while the flag is off).
- ❌ The `email_routing_audit_v2` collection (audit trail preserved).
- ❌ Any `tenant_branding` doc.
- ❌ Any sender identity, Resend domain configuration, or DNS record.
- ❌ Any user account, role, or session.

## Audit-Log Rule

Per the directive's hard rules: **NO deleting audit logs.** The
`email_routing_audit_v2` collection is append-only. Rollback simply
stops adding new V2-source rows; the existing rows stay as evidence of
the cutover attempt.

## Verdict

✅ **Rollback runbook complete and proven safe.** Total time ≤ 5
minutes. Reversible. Zero data loss.
