# TRACK 15.69 · 48-Hour Monitoring Plan (Phase 9)

_Generated 2026-06-22_

## Window

**T+0 → T+48 hours** from cutover.

This is **doubled** vs. the previous Track 15.69 plan (was 24h). The
extra 24 hours gives every scheduled job time to fire at least once:
- Backup verification (daily) → 2 cycles
- Safety digest (daily) → 2 cycles
- Operator digest (hourly) → 48 cycles
- Health monitor (per minute) → ~2880 cycles
- Trench pulse digest (daily) → 2 cycles
- Executive digest (daily) → 2 cycles

## Owner

Production operator (jaymn.judd@mascigc.com).

## Threshold Definitions

| Color | Definition |
|:-:|---|
| 🟢 Green | All metrics within target. No action. |
| 🟡 Amber | One metric outside target but not in failure range. Investigate, don't rollback. |
| 🔴 Red | Any one metric in failure range. **ROLLBACK NOW** per `TRACK_15_69_ROLLBACK_CERTIFICATION.md`. |

## Metrics & Thresholds

### M1 · Audit-Row Health

| Metric | Green | Amber | Red |
|---|:-:|:-:|:-:|
| % audit rows with `source = db` | 100% | 95-99% | < 95% |
| % audit rows with `status = sent` (of non-dry_run) | ≥ 99% | 95-98% | < 95% |
| `status = failed/error` row count | 0 | 1-2 | ≥ 3 |
| Audit rows with unexpected `route_key` | 0 | 0 | ≥ 1 |

Sample query (run every 15 min):

```bash
curl -s "https://mascidocs.com/api/admin/email-routing/v2/audit?since=1h" \
  -H "X-Admin-Token: $TOK" \
  | jq '{by_source: (.rows | group_by(.source) | map({source: .[0].source, count: length})),
         by_status: (.rows | group_by(.status) | map({status: .[0].status, count: length})),
         failures:  ([.rows[] | select(.status=="failed" or .status=="error")] | length),
         unknown_routes: ([.rows[] | select(.route_key | IN("ACCOUNT_INVITES_FROM","ADMIN_DEAD_LETTER_TO","BACKUP_ALERTS","COMPLIANCE_ALWAYS_CC","DISPATCH_ROLE_TO","EXECUTIVE_DIGEST","FIELD_LEADERSHIP_ALWAYS_TO","HEALTH_ALERTS","INCIDENT_SEVERE_CC","OPERATOR_DIGEST_RECIPIENTS","OUTAGE_ALERTS","PASSWORD_RESET_MONITORING_TO","PAYROLL_VARIANCE_TO","PRE_OP_FAIL_FALLBACK","SAFETY_DIGEST_TO","SAFETY_FORMS_TO","SUPER_ADMIN_TO","TRENCH_SAFETY_PULSE_SAFETY","TRENCH_SAFETY_PULSE_SHOP") | not)] | length)}'
```

### M2 · Critical Route Coverage

| Critical Route | Expected Cadence | Green | Amber | Red |
|---|---|:-:|:-:|:-:|
| `BACKUP_ALERTS` | ≥ 1 row per 24h (backup runs daily) | ≥ 2 in 48h | 1 in 48h | 0 in 48h |
| `HEALTH_ALERTS` | ≥ 1 row per 1h (health monitor) | ≥ 24 in 48h | 1-23 in 48h | 0 in 48h |
| `OUTAGE_ALERTS` | 0 expected (unless outage) | 0 ✅ | row appears but `sent` | row appears with `failed` |
| `SUPER_ADMIN_TO` | Variable | any `sent` rows | rare amber | any `failed` row |

If ANY critical route writes a `failed`/`error` row → ROLLBACK.

### M3 · Resend API Errors

| Metric | Green | Amber | Red |
|---|:-:|:-:|:-:|
| Non-delivered rate (4xx/5xx + bounced + spam_complaint) | < 1% | 1-3% | ≥ 5% |
| Hard bounce on critical route | 0 | n/a | ≥ 1 |

Query:

```bash
curl -s "https://api.resend.com/emails?limit=100" \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  | jq '{
      total: (.data | length),
      delivered: ([.data[] | select(.last_event == "delivered")] | length),
      bounced:   ([.data[] | select(.last_event == "bounced")] | length),
      complained: ([.data[] | select(.last_event == "complained")] | length)
    }'
```

### M4 · Backend Health

| Metric | Green | Amber | Red |
|---|:-:|:-:|:-:|
| `/api/health` HTTP 200 rate over 5-min window | 100% | 95-99% | < 95% |
| Scheduler health | healthy | degraded ≤ 5 min | degraded ≥ 5 min |
| Mongo health | healthy | latency spike | unreachable |

### M5 · Scheduler & Dead-Letter

| Metric | Green | Amber | Red |
|---|:-:|:-:|:-:|
| Stuck tasks (running > 30 min) | 0 | 1 | ≥ 2 |
| Dead-letter (`ADMIN_DEAD_LETTER_TO`) row count in window | 0 ✅ | 1 | ≥ 2 |

### M6 · User Reports (qualitative)

| Report Type | Green | Red |
|---|:-:|:-:|
| "I didn't receive [critical alert]" | 0 reports | ≥ 1 confirmed report |
| "I got an email I shouldn't have" | 0 reports | ≥ 1 confirmed report |
| "Wrong sender / wrong reply-to" | 0 reports | ≥ 1 confirmed report |

ANY confirmed wrong-recipient or missing-critical-alert report →
ROLLBACK.

## Monitoring Cadence

| Frequency | Activity | Owner |
|---|---|---|
| Continuous | Backend `/api/health` (uptime monitor) | Automated |
| Every 5 min | Resend rejection scan | Automated or operator script |
| Every 15 min | Audit-row sample (M1) | Operator |
| Every 1 h | Critical-route sweep (M2) | Operator |
| Every 6 h | Wide audit summary + dead-letter (M5) | Operator |
| Every 12 h | User-report sweep (M6) | Operator + ops channel |
| T+48 h | Final certification decision | Operator → Phase 10 |

## Reporting Cadence

| Time | Status format |
|---|---|
| T+1h | `🟢 V2 stable · 0 failures · audit OK` or `⚠️ <issue>` |
| T+6h | Mid-day status (M1-M6) |
| T+12h | Overnight summary |
| T+24h | Halfway report (must hit all green to continue) |
| T+36h | Pre-final report |
| T+48h | Final certification or rollback decision |

## Rollback Triggers (any one → ROLLBACK)

Per `TRACK_15_69_ROLLBACK_CERTIFICATION.md`:

- Any 🔴 in any metric above
- Operator subjective judgement that something is wrong
- ≥ 1 user-confirmed missing critical alert
- ≥ 1 user-confirmed wrong recipient

Recovery time: ≤ 5 minutes (proven).

## Success Criteria (T+48h)

ALL of:

- 🟢 across all 6 metrics for the full 48 hours
- Audit rows with `source=legacy` = 0 (no silent fallback)
- Audit rows with `status=failed/error` = 0
- Critical-route empty events = 0
- Wrong-recipient reports = 0
- Sender-mismatch reports = 0
- Resend rejection rate ≤ 1%
- Backend `/api/health` 100% green
- Dead-letter row count = 0
- Operator subjective: "MASCI users notice nothing" = YES

If ALL targets met at T+48h → close with `TRACK_15_69_EXECUTIVE_CERTIFICATION.md`.

## Verdict

✅ **48-hour monitoring plan complete and activate-able at Phase 9
completion.**
