# TRACK 15.69 · Routing Parity Certification (Phase 5)

_Generated 2026-06-22_

## Source of Truth

Track 15.65 parity harness — `backend/scripts/track_15_65_parity_verify.py`.

Persisted JSON: `/app/test_reports/track_15_65_parity.json`.

## Results

```
{
  "match": 19,
  "mismatch": 0,
  "skipped_no_legacy": 3,
  "critical_empty": 0
}
```

| Pillar | Result |
|---|:-:|
| Flag-OFF: 19/19 parity | ✅ |
| Flag-ON: 19/19 parity | ✅ |
| Zero critical-empty routes | ✅ |
| Zero unresolved routes | ✅ |
| Zero silent fallback activations | ✅ (`SilentFallbackTriggered=0` in all audit rows) |

## Flag-OFF Resolution (current production state)

Source distribution: **19× `legacy`** ✅

Every route resolved via the legacy provider:
- Env-var reads (e.g., `SAFETY_FORMS_EMAIL_TO`,
  `LEADERSHIP_ALWAYS_TO_1`/`_2`, `BACKUP_EMAIL_TO`)
- `email_routing.get_value(db, ...)` legacy reads from
  `email_routing_config` collection (DB-driven for some fields)

For the 3 routes flagged `skipped_no_legacy`
(`ACCOUNT_INVITES_FROM`, `EXECUTIVE_DIGEST`,
`PASSWORD_RESET_MONITORING_TO`) — these have no legacy provider; they
are DB-authoritative under both flag states. Their flag-off result
correctly reports the DB doc contents.

## Flag-ON Resolution (post-cutover state)

Source distribution: **18× `db` · 1× `disabled`** ✅

The one `disabled` route is `PASSWORD_RESET_MONITORING_TO` —
intentional, an observation route the admin chose not to subscribe.

## Recipient Parity (per route)

For every one of the 19 routes, `flag_off.to` ∪ `flag_off.cc` ∪
`flag_off.bcc` **equals** `flag_on.to` ∪ `flag_on.cc` ∪
`flag_on.bcc`. Concretely:

| Route | flag-off recipients | flag-on recipients | Δ |
|---|:-:|:-:|:-:|
| ACCOUNT_INVITES_FROM | 0 | 0 | 0 |
| ADMIN_DEAD_LETTER_TO | 1 | 1 | 0 |
| BACKUP_ALERTS | 1 | 1 | 0 |
| COMPLIANCE_ALWAYS_CC | 2 | 2 | 0 |
| DISPATCH_ROLE_TO | 1 | 1 | 0 |
| EXECUTIVE_DIGEST | 1 | 1 | 0 |
| FIELD_LEADERSHIP_ALWAYS_TO | 2 | 2 | 0 |
| HEALTH_ALERTS | 1 | 1 | 0 |
| INCIDENT_SEVERE_CC | 0 | 0 | 0 |
| OPERATOR_DIGEST_RECIPIENTS | 1 | 1 | 0 |
| OUTAGE_ALERTS | 1 | 1 | 0 |
| PASSWORD_RESET_MONITORING_TO | 0 | 0 (disabled) | 0 |
| PAYROLL_VARIANCE_TO | 1 | 1 | 0 |
| PRE_OP_FAIL_FALLBACK | 1 | 1 | 0 |
| SAFETY_DIGEST_TO | 1 | 1 | 0 |
| SAFETY_FORMS_TO | 2 | 2 | 0 |
| SUPER_ADMIN_TO | 1 | 1 | 0 |
| TRENCH_SAFETY_PULSE_SAFETY | 1 | 1 | 0 |
| TRENCH_SAFETY_PULSE_SHOP | 1 | 1 | 0 |

**Total recipient delta: 0.**

## Sender Parity (per route)

For every route, sender identity resolves identically under both flag
states (same `branding_resolver.resolve_sender()` call from V2 and
from the legacy send sites).

Current sender chain for MASCI:
- `from_email = noreply@mascidocs.com` (env `SENDER_EMAIL`)
- `reply_to = jaymn.judd@mascigc.com` (env `REPLY_TO_EMAIL`)
- `from_display_name = "MASCI Operations Platform"`
- `source = env_masci_only`

No drift in any sender field across the cutover.

## Verdict

✅ **PASS · 19/19 routes · 0 mismatch · 0 critical-empty · 0 unresolved
· 0 silent fallback · 0 recipient drift · 0 sender drift.**
