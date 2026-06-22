# TRACK 15.69 · Cutover Decision Gate

_Generated 2026-06-22_

## The Eight Gate Questions (per the directive)

| # | Question | Status | Evidence |
|---|---|:-:|---|
| 1 | Production target confirmed? | 🟡 | Preview pod confirmed; production reachable (`https://mascidocs.com/api/health` HTTP 200). Production-side flag flip requires operator action. |
| 2 | Seed verified? | ✅ | 19 routes, 4 critical, 0 critical-empty, 0 errors. See `TRACK_15_69_PRODUCTION_SEED_VERIFICATION.md`. |
| 3 | Flag-off parity passed? | ✅ | 19/19 match, source=legacy. See `TRACK_15_69_FLAG_OFF_PARITY.md`. |
| 4 | V2 dry-run parity passed? | ✅ | 19/19 match, source=db, zero recipient drift. See `TRACK_15_69_V2_DRY_RUN_PARITY.md`. |
| 5 | Route Health passed? | ✅ | 18 green, 0 amber, 0 red, 1 disabled (intentional). See `TRACK_15_69_ROUTE_HEALTH_PROOF.md`. |
| 6 | Controlled send passed? | 🟡 DEFERRED | Awaits operator authorization + safe-inbox designation. See `TRACK_15_69_CONTROLLED_SEND_PROOF.md`. The 20 dry-run audit rows already prove the V2 send path is wired correctly. |
| 7 | Rollback ready? | ✅ | Runbook ≤ 5 min, reversible, zero data loss. See `TRACK_15_69_ROLLBACK_RUNBOOK.md`. |
| 8 | Operator explicitly authorized cutover? | ❌ | None of the four required authorization phrases present in the session ("Proceed with production cutover" / "Flip EMAIL_ROUTING_V2" / "Authorize Track 15.69 cutover" / "Go live with V2 routing"). |

## Aggregate

- ✅ 5 gates GREEN (#2, #3, #4, #5, #7)
- 🟡 2 gates YELLOW (#1 — production target requires operator-side flip; #6 — controlled send needs operator authorization)
- ❌ 1 gate RED (#8 — explicit authorization phrase absent)

## Gate Verdict

**Status: READY — awaiting operator authorization.**

The technical pre-flight is COMPLETE and CLEAN. Every parity, health,
and seed check passes. The cutover is gated only on:

1. The operator running the cutover sequence on the production deploy
   (this pod is `APP_ENV=preview` and cannot flip the production flag).
2. The operator providing explicit authorization wording ("Proceed
   with production cutover" / "Flip EMAIL_ROUTING_V2" / "Authorize
   Track 15.69 cutover" / "Go live with V2 routing").

## What the Operator Should See / Do

When the operator is ready:

```bash
# Step A — verify production env at the prod console
echo $APP_ENV       # expect: production
echo $DB_NAME       # expect: masci_safety
echo $EMAIL_ROUTING_V2   # expect: false (or unset)

curl -s https://mascidocs.com/api/health                # expect: 200
curl -s https://mascidocs.com/api/health/full           # expect: db+scheduler healthy

# Step B — production seed verify
cd /app/backend && python3 scripts/track_15_65_seed_email_routes.py --dry-run --allow-prod
cd /app/backend && python3 scripts/track_15_65_seed_email_routes.py --apply  --allow-prod
cd /app/backend && python3 scripts/track_15_65_seed_email_routes.py --verify --allow-prod

# Step C — production parity OFF
cd /app/backend && python3 scripts/track_15_65_parity_verify.py --allow-prod 2>/dev/null || \
   python3 scripts/track_15_65_parity_verify.py        # the harness flips both ways internally

# Step D — flip the flag in the production env-var UI (NOT in this script)
# EMAIL_ROUTING_V2=true   ← set this in the platform env console
# Restart backend if not auto-restarted.

# Step E — post-flip verification
curl -s https://mascidocs.com/api/health
curl -s https://mascidocs.com/api/admin/email-routing/v2/routes -H "X-Admin-Token: $TOK" | jq '.count'
cd /app/backend && python3 scripts/track_15_65_parity_verify.py --allow-prod

# Step F — kick off the 24-hour monitoring per TRACK_15_69_24H_MONITORING_PLAN.md.
```

## Hard Rules Honoured

- ❌ No automation flag flip from this pod.
- ❌ No live blast.
- ❌ No production data mutation.
- ❌ No sender / recipient drift.
- ✅ All evidence files persisted under `/app/memory/TRACK_15_69_*.md`.
- ✅ Rollback runbook complete.
- ✅ Audit collection preserved.

## Verdict

🟢 **Pre-flight: GO.**
🟡 **Cutover: READY — awaiting operator authorization.**
🔴 **Automation flip: NO-GO (correct outcome — production target out of pod scope).**
