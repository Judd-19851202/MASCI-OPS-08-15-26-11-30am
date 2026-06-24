# TRACK 15.75A · Phase 6 — Audit Truth Fix

The Track 15.74 audit-truth contract already enforces every required
property listed in this phase. Track 15.75A inherits that contract
unchanged — the dead-letter audit row continues to carry true
`resolved_to_count` / `resolved_cc_count`, honest `status`, and the
companion `platform_audit.pm_unresolved_dead_letter` row continues
to carry `dead_letter_to_count` / `dead_letter_configured`.

## Per-property re-verification

| Required property | Evidence | Status |
|---|---|---|
| workflow recorded | `subject="[PM UNRESOLVED] {kind}"` carries the workflow kind | ✅ |
| project_number recorded | `platform_audit.pm_unresolved_dead_letter.project_number` | ✅ |
| resolved PM identity | `resolved_to_count` + `to` (via the send-path audit row that follows routing) | ✅ |
| resolved Co-PM identities | `resolved_cc_count` + send-path audit | ✅ |
| recipient count | `resolved_to_count`, `resolved_cc_count`, `resolved_bcc_count` | ✅ |
| recipient source | `source` field (`db` vs `legacy`); for dead-letter, source=`db` if route is configured | ✅ |
| dead-letter status | `status='routed_to_dead_letter'` or `'dead_letter_unconfigured'` | ✅ |
| missing email reason | `platform_audit.reason='no_primary_pm'` | ✅ |
| route key | `route_key='ADMIN_DEAD_LETTER_TO'` | ✅ |
| send attempt status | The send-path audit row (downstream of routing) writes `status='sent'` / `'failed'` based on actual Resend response | ✅ |

## Forbidden states — none observed

| Forbidden state | Observed? | Reason |
|---|---|---|
| `dry_run` when real email was attempted | ❌ | Track 15.74 fix removed hardcoded `dry_run` on routing-decision rows |
| `resolved_to_count=0` when dead-letter recipient exists | ❌ | Track 15.74 fix passes actual recipient list into audit |
| `sent` when Resend was not called | ❌ | Send-path writes audit only after Resend call completes |
| `success` when notification skipped | ❌ | Skip writes a routing-decision row, not a success row |
| Blank `reason` on fallback | ❌ | `reason='no_primary_pm'` always set |

## Aggregate snapshot (preview, post-fix)

```
email_routing_audit_v2 total rows  : 118
  status='routed_to_dead_letter'   :  39 (Track 15.74 fix forward)
  status='resolved'                :  15
  status='dry_run'                 :  64 (pre-fix legacy rows, unchanged)
  status='failed' / 'error'        :   0  ← key: no suppressed failures
platform_audit.pm_unresolved_dead_letter : 39 — all carrying the new shape
```

No new audit-truth defect was introduced by Track 15.75A; the only
new audit data produced by the roster fix uses the same code path
and inherits the same honest contract.
