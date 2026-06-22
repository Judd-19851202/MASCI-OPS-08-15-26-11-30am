# TRACK 15.69 · 24-Hour Monitoring Plan

_Generated 2026-06-22_

## Window

**T+0 → T+24 hours** from the moment Phase 9 (flag flip) completes.

## Owner

Production operator (jaymn.judd@mascigc.com per current
`SUPER_ADMIN_EMAIL` config).

## What to Watch

### A · Email Routing Audit (`email_routing_audit_v2`)

Every send during the window writes a row. The healthy distribution is:

| Field | Healthy Value |
|---|---|
| `source` | 100% `db` (zero `legacy` rows) |
| `status` | mostly `sent`, occasional `dry_run` (admin route-test); zero `failed`/`error` |
| `tenant_key` | 100% `masci` |
| `route_key` | only the 19 known route keys |

Monitor query (run hourly):

```
TOK=<admin_token>
curl -s "https://mascidocs.com/api/admin/email-routing/v2/audit?since=1h" \
  -H "X-Admin-Token: $TOK" \
  | jq '{by_source: (.rows | group_by(.source) | map({source: .[0].source, count: length})), failures: ([.rows[] | select(.status=="failed" or .status=="error")] | length), last_failure: ([.rows[] | select(.status=="failed" or .status=="error")] | first)}'
```

### B · Critical Routes (must-not-fail list)

| Route | Watch |
|---|---|
| `BACKUP_ALERTS` | At least 1 row per 6h (backup runs); status=sent |
| `HEALTH_ALERTS` | At least 1 row per 1h (health monitor); status=sent |
| `OUTAGE_ALERTS` | Zero rows expected unless an outage occurs; if a row appears, status=sent and recipient is `jaymn.judd@mascigc.com` |
| `SUPER_ADMIN_TO` | Variable cadence; status=sent on every send |

If ANY critical route writes a `failed`/`error` row → ROLLBACK.

### C · Resend API Errors

Monitor Resend dashboard (or API):

```
curl -s "https://api.resend.com/emails?limit=100" \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  | jq '[.data[] | select(.last_event != "delivered" and .last_event != "sent")] | length'
```

Healthy: ≤ 1% non-delivered (transient mailbox issues are normal).
Unhealthy: ≥ 5% rejection rate or any 4xx/5xx domain reputation
indicator → ROLLBACK.

### D · Backend Health

```
curl -s https://mascidocs.com/api/health/full | jq '.status, .checks'
```

Watch every 5 minutes:
- `mongo: healthy`
- `scheduler: healthy`
- `resend: configured`
- `email_routing_v2: enabled` (post-flip)

Any degradation for ≥ 2 consecutive samples → INVESTIGATE; ≥ 5
samples → ROLLBACK.

### E · Scheduler

`/api/admin/scheduler/status` should show:
- 0 stuck tasks (> 30 min running)
- 0 dead-letter queue growth
- Email-send queue empty between scheduled jobs

### F · User Reports (qualitative)

The operator should monitor the operator inbox + ops chat for any
user-reported regression:
- "I usually get the safety digest at 6 AM but didn't today"
- "An incident report didn't go to the safety team"
- "I got a backup alert that should have gone to operations"

ANY single confirmed wrong-recipient report → ROLLBACK.

### G · Dead-Letter Route

`ADMIN_DEAD_LETTER_TO` should receive **zero** rows during the
24-hour window. Any traffic here means the resolver could not place
an email — investigate and rollback if pattern persists.

## Success Criteria (T+24h)

| Metric | Target |
|---|---|
| Audit rows with `source = legacy` | **0** ✅ |
| Audit rows with `status = failed/error` | **0** ✅ |
| Critical-route empty events | **0** ✅ |
| Wrong-recipient reports | **0** ✅ |
| Sender-mismatch reports | **0** ✅ |
| Resend rejection rate | **≤ 1%** ✅ |
| Backend `/api/health` | 100% green ✅ |
| Dead-letter inbox traffic | **0** ✅ |
| Operator subjective sense ("MASCI users notice nothing") | YES ✅ |

If ALL targets met at T+24h → close Phase 12 (post-cutover
certification).

## Failure Criteria — Trigger Immediate Rollback

ANY ONE of:
- ≥ 1 critical-route failure
- ≥ 1 wrong recipient
- ≥ 1 sender mismatch
- ≥ 5% Resend rejection rate spike
- ≥ 1 user-reported missing critical alert
- backend `/api/health` red for ≥ 5 consecutive samples
- audit drawer in Admin UI unavailable
- dead-letter route receives unexplained traffic

→ Execute `TRACK_15_69_ROLLBACK_RUNBOOK.md`.

## Monitoring Cadence

| Frequency | Activity |
|---|---|
| Continuous | Backend `/api/health` (alertmanager / uptime monitor) |
| Every 5 min | Resend rejection scan |
| Every 15 min | Audit-row sample (`source = db` confirm) |
| Every 1 h | Critical-route last-send sweep |
| Every 6 h | Wide audit summary + dead-letter check |
| T+24 h | Final certification decision |

## Reporting Cadence

| Time | Owner | Format |
|---|---|---|
| T+1h | Operator | "✅ V2 stable · 0 failures · audit OK" or "⚠️ <issue>" |
| T+6h | Operator | Mid-day status |
| T+12h | Operator | Overnight summary |
| T+24h | Operator | Final certification or rollback decision |

## Verdict

🟡 **DEFERRED — activates the moment Phase 9 (flag flip) completes.**
The plan is complete and ready for execution.
