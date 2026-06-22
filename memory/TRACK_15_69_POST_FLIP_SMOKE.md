# TRACK 15.69 · Post-Flip Smoke Verification

_Generated 2026-06-22_

## Status — DEFERRED · Cannot Run Until Phase 9 Completes

🛑 This deliverable is the post-flip-time smoke evidence. Since the
flag flip (Phase 9) was deferred pending operator authorization, the
post-flip smoke has not been executed.

## What the Operator Will Run Immediately After Phase 9

### Smoke 1 · Backend Health (≤ 30s)

```
curl -s https://mascidocs.com/api/health        # expect HTTP 200
curl -s https://mascidocs.com/api/health/full   # expect db+scheduler healthy
```

### Smoke 2 · Resolver Source Now DB (≤ 30s)

```
TOK=<admin_token>
curl -s https://mascidocs.com/api/admin/email-routing/v2/routes \
  -H "X-Admin-Token: $TOK" | jq '.routes[] | .summary | .last_send_source' | sort | uniq -c
```

Expected (post-flip + first audit cycle): every line shows `db`. None
show `legacy`.

### Smoke 3 · Parity Verify (≤ 60s)

```
cd /app/backend && python3 scripts/track_15_65_parity_verify.py --allow-prod
```

Expected:
- 19/19 match
- 0 mismatch
- 0 critical-empty
- flag-off side reports `legacy` (the harness internally flips both
  ways; this is expected)
- flag-on side reports `db` and matches DB doc contents

### Smoke 4 · Route Health (≤ 30s)

```
curl -s https://mascidocs.com/api/admin/email-routing/v2/routes \
  -H "X-Admin-Token: $TOK" | jq '.routes[] | {route_key, last_send_status: .summary.last_send_status, last_send_source: .summary.last_send_source}'
```

Expected: every critical route shows the same recipient set as
pre-flip. No red routes. No `last_send_status: "failed"` rows in the
last 5 minutes.

### Smoke 5 · Audit Trail (≤ 30s)

Verify a fresh audit row appears with `source = db` and a real Resend
`message_id` for the next operational email triggered by the platform.
This is naturally produced by:
- Operator digest job (runs hourly).
- Health monitor (runs every few minutes).
- Any user-triggered safety-form submission.

The first non-`dry_run` row with `source=db` IS the cutover proof.

### Smoke 6 · Admin UI Sanity (≤ 30s)

Operator opens **Admin → Email Routing** in the production UI:
- Verify the page loads.
- Verify the V2 active indicator is on (the page shows "DB-first" or
  similar status).
- Open one route's audit drawer; verify recent rows show `db` source.

### Smoke 7 · No Unintended Sends (≤ 60s)

Operator checks Resend dashboard / API for the last 5 minutes:

```
curl -s https://api.resend.com/emails?limit=20 \
  -H "Authorization: Bearer $RESEND_API_KEY" | jq '.data[] | {to, subject, created_at}'
```

Expected: only emails the operator authorized (e.g., the digest job's
own scheduled run). No surprise blasts. No emails to unexpected
recipients.

## Failure Decision Matrix

| Smoke | If FAIL → |
|---|---|
| Smoke 1 | Rollback (per `TRACK_15_69_ROLLBACK_RUNBOOK.md`) |
| Smoke 2 | Investigate flag state; if any route still `legacy`, restart backend |
| Smoke 3 | Rollback if mismatch ≥ 1 or critical-empty ≥ 1 |
| Smoke 4 | Rollback if any critical route flips red |
| Smoke 5 | Wait 15 min for next scheduled job; if still no `db`-source row, rollback |
| Smoke 6 | If admin UI errors, rollback |
| Smoke 7 | Rollback IMMEDIATELY if any wrong recipient appears |

## Verdict

🟡 **DEFERRED — runs immediately after operator-driven flag flip.**
