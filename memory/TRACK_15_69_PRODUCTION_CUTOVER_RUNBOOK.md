# TRACK 15.69 · Production Cutover Runbook (Phase 8)

_Generated 2026-06-22_

## Pre-Flight Checklist (operator must complete BEFORE flipping flag)

```
[ ] (Sec 1) Production environment safety check passed
[ ] (Sec 2) Atlas snapshot < 6 hours old confirmed in Atlas console
[ ] (Sec 3) R2 off-site snapshot < 24 hours old confirmed in Cloudflare R2
[ ] (Sec 4) Production seed verify run: 19 routes, 0 errors
[ ] (Sec 5) Production flag-off parity: 19/19 match
[ ] (Sec 6) Production V2 dry-run parity: 19/19 match
[ ] (Sec 7) Route Health green for all 4 critical routes
[ ] (Sec 8) Controlled-send Variant A executed OR Variant B documented
[ ] (Sec 9) Rollback drill executed on preview: 0.033s recovery
[ ] (Sec 10) Operator authorization phrase recorded in session
[ ] (Sec 11) Emergency contact list confirmed
[ ] (Sec 12) No concurrent deployment scheduled in next 48 hours
[ ] (Sec 13) No current outage / amber state in any monitoring system
```

## Operator Commands (production)

### Section 1 · Environment confirm

```bash
# At the production console (NOT the preview pod):
echo "APP_ENV=$APP_ENV"        # expect: production
echo "DB_NAME=$DB_NAME"        # expect: masci_safety
echo "EMAIL_ROUTING_V2=$EMAIL_ROUTING_V2"   # expect: false (or unset)

curl -s https://mascidocs.com/api/health
curl -s https://mascidocs.com/api/health/full
```

Halt if any output is unexpected.

### Section 2-3 · Backup verification

Open MongoDB Atlas console → Backup → confirm:
- Latest snapshot < 6 hours old.
- Continuous backup enabled.
- PIT recovery window covers cutover + 48 hours.

Open Cloudflare R2 → confirm latest mascidocs snapshot < 24 hours.

### Section 4 · Seed verify

```bash
cd /app/backend
python3 scripts/track_15_65_seed_email_routes.py --dry-run --allow-prod
# Compare output to TRACK_15_69_PRODUCTION_SEED_VERIFICATION.md expected shape.

python3 scripts/track_15_65_seed_email_routes.py --apply --allow-prod
# Expect: created=0, updated≤18 (cache-bust only), unchanged≥0, errors=0

python3 scripts/track_15_65_seed_email_routes.py --verify --allow-prod
# Expect: total_routes=19, 0 critical-empty, 0 duplicate
```

Halt if `created > 0` (missing routes discovered).
Halt if `errors > 0`.
Halt if `total_routes != 19`.

### Section 5-6 · Parity verification

```bash
python3 scripts/track_15_65_parity_verify.py --allow-prod
```

Expect: `match=19 · mismatch=0 · critical_empty=0`.

Halt if mismatch ≥ 1 or critical_empty ≥ 1.

### Section 7 · Route Health

```bash
TOK=<production_admin_token>
curl -s https://mascidocs.com/api/admin/email-routing/v2/routes \
  -H "X-Admin-Token: $TOK" \
  | jq '[.routes[] | {route_key, critical, health: .summary.health}]'
```

Expect: 0 red entries, 0 amber critical entries.

### Section 8 · Controlled send (Variant A)

```bash
# Operator MUST designate a safe inbox first.
SAFE_INBOX="ops-probe@mascigc.com"   # or operator-chosen
TOK=<production_admin_token>

curl -X POST \
  https://mascidocs.com/api/admin/email-routing/v2/routes/SUPER_ADMIN_TO/test \
  -H "X-Admin-Token: $TOK" \
  -H "Content-Type: application/json" \
  -d "{\"recipient_override\": \"$SAFE_INBOX\", \"subject_prefix\": \"[15.69 PROBE]\"}"
```

Expect: response includes `provider_message_id`, `status: sent`,
`source: db`, `route_key: SUPER_ADMIN_TO`, `to: [\"$SAFE_INBOX\"]`.
Operator confirms inbox received the probe.

OR Variant B: rely on the 20 dry-run audit rows already proving V2
path (skip live send entirely).

### Section 9 · Final cutover

```bash
# In the production env-var console:
# Set EMAIL_ROUTING_V2=true
# Save → platform auto-restarts backend
```

Wait 30 seconds, then verify:

```bash
curl -s https://mascidocs.com/api/health
curl -s https://mascidocs.com/api/health/full
```

Expect: HTTP 200, mongo healthy, scheduler healthy.

### Section 10 · Post-flip verification

```bash
# Within 2 minutes of flip:
curl -s https://mascidocs.com/api/admin/email-routing/v2/routes \
  -H "X-Admin-Token: $TOK" \
  | jq '[.routes[].summary.last_send_source] | unique'
# Expect: ["db"] only.

python3 scripts/track_15_65_parity_verify.py --allow-prod
# Expect: 19/19 match.

# Watch the first audit row from a real send:
curl -s "https://mascidocs.com/api/admin/email-routing/v2/audit?since=10m" \
  -H "X-Admin-Token: $TOK" \
  | jq '.rows[] | {route_key, source, status, ts}'
# First non-dry_run row with source=db = cutover-success signal.
```

### Section 11 · Activate 48-hour monitoring

Per `TRACK_15_69_48_HOUR_MONITORING_PLAN.md`.

## Rollback Trigger Conditions

Per `TRACK_15_69_ROLLBACK_CERTIFICATION.md` and
`TRACK_15_69_ROLLBACK_RUNBOOK.md`. Triggers (any one):

- Any critical route fails to resolve
- Any wrong recipient appears
- Any sender identity mismatch
- Route Health flips any critical route to red
- Resend rejection rate spikes ≥ 5%
- Backend `/api/health` red for ≥ 5 consecutive samples
- Operator cannot view V2 audit drawer
- User reports a missing critical alert
- Dead-letter route receives unexplained traffic

## Emergency Contacts

| Role | Person | Channel |
|---|---|---|
| Super Admin | jaymn.judd@mascigc.com | Email + phone |
| Operations Manager | jaymn.judd@mascigc.com | Email + phone |
| Safety Lead | safety@mascigc.com | Email |
| MongoDB Atlas escalation | Atlas support portal | Atlas console |
| Resend escalation | support@resend.com | Resend dashboard |

(Operator should update these with current escalation contacts in
production before executing the runbook.)

## Success Criteria (at T+48h)

| Criterion | Target |
|---|---|
| All routes resolve via `db` | 100% |
| Audit rows with `status=failed/error` | 0 |
| Wrong-recipient reports | 0 |
| Sender-mismatch reports | 0 |
| Resend rejection rate | < 1% |
| Backend `/api/health` uptime | 100% |
| Dead-letter inbox traffic | 0 |
| User regressions | 0 |

If all 8 met at T+48h → issue Executive Certification (Phase 10) and
close Track 15.69.

## Verdict

✅ **Runbook complete. Operator-executable. Reversible. Time-budgeted.**
