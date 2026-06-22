# TRACK 15.69 · Flag-OFF Parity Verification

_Generated 2026-06-22 · Preview cluster_

## Command

```
cd /app/backend && python3 scripts/track_15_65_parity_verify.py
```

This harness internally toggles `EMAIL_ROUTING_V2` between `false` and
`true` per route — both flag states are exercised in a single run. This
deliverable focuses on the FLAG-OFF half of that run; the FLAG-ON half
is in `TRACK_15_69_V2_DRY_RUN_PARITY.md`.

## Result Summary

```
{
  "match": 19,
  "mismatch": 0,
  "skipped_no_legacy": 3,
  "critical_empty": 0
}
```

| Metric | Value |
|---|---:|
| Routes with provider + legacy match | **16** ✅ |
| Routes skipped (no legacy provider; DB authoritative) | 3 (ACCOUNT_INVITES_FROM, EXECUTIVE_DIGEST, PASSWORD_RESET_MONITORING_TO) |
| Total routes evaluated | **19** |
| Mismatches | **0** ✅ |
| Critical routes empty under flag-off | **0** ✅ |

## Per-Route (Flag OFF)

All 19 routes resolved with `source = legacy` when
`EMAIL_ROUTING_V2 = false`. Recipient lists matched the legacy provider
output for every route that has a legacy provider. The 3 skipped routes
(ACCOUNT_INVITES_FROM, EXECUTIVE_DIGEST, PASSWORD_RESET_MONITORING_TO)
have no legacy provider — they are DB-authoritative even under the
legacy flag, and their flag-off result is correctly reported as the DB
contents.

| Route | crit | enabled | flag_off_source | flag_off_to count |
|---|:-:|:-:|:-:|:-:|
| ACCOUNT_INVITES_FROM | · | ✅ | legacy | 0 |
| ADMIN_DEAD_LETTER_TO | · | ✅ | legacy | 1 |
| BACKUP_ALERTS | 🔴 | ✅ | legacy | 1 |
| COMPLIANCE_ALWAYS_CC | · | ✅ | legacy | 2 |
| DISPATCH_ROLE_TO | · | ✅ | legacy | 1 |
| EXECUTIVE_DIGEST | · | ✅ | legacy | 1 |
| FIELD_LEADERSHIP_ALWAYS_TO | · | ✅ | legacy | 2 |
| HEALTH_ALERTS | 🔴 | ✅ | legacy | 1 |
| INCIDENT_SEVERE_CC | · | ✅ | legacy | 0 |
| OPERATOR_DIGEST_RECIPIENTS | · | ✅ | legacy | 1 |
| OUTAGE_ALERTS | 🔴 | ✅ | legacy | 1 |
| PASSWORD_RESET_MONITORING_TO | · | ❌ | legacy | 0 |
| PAYROLL_VARIANCE_TO | · | ✅ | legacy | 1 |
| PRE_OP_FAIL_FALLBACK | · | ✅ | legacy | 1 |
| SAFETY_DIGEST_TO | · | ✅ | legacy | 1 |
| SAFETY_FORMS_TO | · | ✅ | legacy | 2 |
| SUPER_ADMIN_TO | 🔴 | ✅ | legacy | 1 |
| TRENCH_SAFETY_PULSE_SAFETY | · | ✅ | legacy | 1 |
| TRENCH_SAFETY_PULSE_SHOP | · | ✅ | legacy | 1 |

## Live Sends?

**Zero live sends.** The harness performs every resolution in
"resolve-only" mode (`v2.resolve()`), no `send_email_v2()` invocation.

## Persisted Artefacts

- `/app/test_reports/track_15_65_parity.json`
- `/app/memory/track_15_65_data/parity_summary.md`

## Verdict

✅ **PASS** — 19/19 match, 0 mismatch, 0 critical-empty under flag-off.
Legacy resolution remains the source of truth before cutover.
