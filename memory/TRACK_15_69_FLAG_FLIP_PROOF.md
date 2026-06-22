# TRACK 15.69 · Flag Flip Proof

_Generated 2026-06-22_

## Status — DEFERRED · Awaiting Operator Authorization

🛑 **The `EMAIL_ROUTING_V2 = true` flag flip was NOT performed.**

## Why

Per the directive's hard rules:

1. The production flag flip must occur in the production deploy (where
   `APP_ENV = production`, `DB_NAME = masci_safety`). This pod is
   `APP_ENV = preview`, `DB_NAME = masci_safety_preview`. Flipping the
   flag here would have zero effect on the production deploy.
2. The directive requires explicit operator authorization wording —
   "Proceed with production cutover", "Flip EMAIL_ROUTING_V2",
   "Authorize Track 15.69 cutover", or "Go live with V2 routing" — and
   none of those phrases appeared in the session.

## Pre-Conditions Verified (ready when operator is)

| Pre-condition | Status |
|---|:-:|
| Phase 1 production env safety check | ✅ |
| Phase 2 seed verification | ✅ (19/19 in preview; production must mirror) |
| Phase 3 flag-off parity | ✅ 19/19 |
| Phase 4 V2 dry-run parity | ✅ 19/19 |
| Phase 5 Route Health | ✅ 18 green / 0 amber / 0 red / 1 disabled |
| Phase 6 controlled send | 🟡 DEFERRED (operator-gated) |
| Phase 7 rollback runbook | ✅ ≤ 5 min |
| Phase 8 cutover decision gate | ✅ READY |

## Operator Flip Procedure

When authorized, the operator performs the following in the production
deploy environment-variable management UI:

```
1.  Confirm: APP_ENV=production · DB_NAME=masci_safety · current EMAIL_ROUTING_V2=false (or unset)
2.  Set:     EMAIL_ROUTING_V2=true
3.  Save.   The platform restarts the backend automatically (or operator triggers manual restart).
4.  Wait:   ~30s for backend to come up.
5.  Verify: curl -s https://mascidocs.com/api/health  → HTTP 200
6.  Verify: curl -s https://mascidocs.com/api/health/full | jq .   → db+scheduler healthy
7.  Verify: tail the next outbound email's audit row — expect source=db.
```

Total time at the operator's hands: ~2 minutes.

## Audit Trail After Flip

After Step 2, the next outbound email from any of the 19 routes will
write an `email_routing_audit_v2` row with:
- `tenant_key: "masci"`
- `source: "db"` (was `"legacy"` pre-flip)
- `status: "sent"` (was `"dry_run"` during pre-flight)

This single audit row IS the flag-flip proof.

## Verdict

🟡 **DEFERRED — awaiting operator authorization.** Pre-flight is GO.
The flag flip itself takes ≈ 2 minutes when the operator is ready.
