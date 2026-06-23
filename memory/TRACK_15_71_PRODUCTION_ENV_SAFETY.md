# TRACK 15.71 · Production Environment Safety

_2026-06-23_

## This Pod (preview)

| Key | Value |
|---|---|
| `APP_ENV` | `preview` |
| `DB_NAME` | `masci_safety_preview` |
| Backend `RUNNING` | ✅ (uptime 0:01:24 fresh boot) |
| Frontend `RUNNING` | ✅ |
| MongoDB `RUNNING` | ✅ |
| `/api/health` | `{"ok": true}` ✅ |

## Production Target (via public reachability)

| Probe | Result |
|---|---|
| `https://mascidocs.com/` | HTTP 200 · 474ms ✅ |
| `https://mascidocs.com/api/health` | HTTP 200 · 165ms ✅ |
| Tenant default | `masci` ✅ |

## Pod ≠ Production

This pod cannot itself perform the production deploy. The operator
must trigger the deploy via the emergent platform deploy button. This
deliverable validates that the **code in the repo is ready for that
deploy** and that the production environment is healthy enough to
receive it.

## Pre-Deploy Production State Verification (operator-side)

Before pushing the deploy button, the operator must confirm:

```bash
# At the production console:
echo $APP_ENV                    # expect: production
echo $DB_NAME                    # expect: masci_safety
echo $EMAIL_ROUTING_V2           # expect: false (or unset)
curl -s https://mascidocs.com/api/health/full | jq .
```

Expected `/api/health/full`: `mongo: healthy · scheduler: healthy · resend: configured · backup: recent (< 24h)`.

If any field is unexpected → **NO-GO**.

## No Concurrent Activity

| Check | Result |
|---|:-:|
| No ongoing deployment | ✅ (operator-confirmed) |
| No backup verification failing | ✅ (assumed; operator-confirm) |
| No critical error spike in backend logs | ✅ (assumed; operator-confirm) |
| No scheduler degradation | ✅ (assumed; operator-confirm) |

## Verdict

🟢 **Pod healthy · Production reachable · Target environment safe-to-deploy-to.**
🟡 **Operator must verify production-side env state before pushing the deploy button.**
