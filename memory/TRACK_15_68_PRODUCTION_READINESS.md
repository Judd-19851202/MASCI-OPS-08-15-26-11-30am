# TRACK 15.68 · Production Readiness

_2026-06-22_

## Authorisations granted by Track 15.68

| Action | Status |
|---|:--:|
| Save / push to git | ⚠️ Allowed — no destructive backend changes; MASCI parity preserved |
| Backend deploy with `EMAIL_ROUTING_V2=false` | ✅ Allowed |
| Frontend deploy | ✅ Allowed — splash + PDF + legal still leak MASCI but no MASCI regression |
| `EMAIL_ROUTING_V2=true` production flip | ❌ **NOT AUTHORISED** |
| Real Customer #2 onboarding | ❌ **NOT AUTHORISED** — visual chrome not yet white-label |
| Live email blasts | ❌ **NOT AUTHORISED** — was never in scope |

## Gating conditions
| Condition | Verdict |
|---|:--:|
| MASCI parity passes | ✅ 19/19 |
| Customer #2 visual certification passes | ❌ FAIL (splash leak) |
| Contamination scan passes (zero customer-visible) | ❌ 491 disallowed |
| No operational routing regression | ✅ |
| No email blast | ✅ |
| No production flag flip | ✅ |

## Recommendation
**DO** deploy backend + frontend if the operator wants the Phase 3 governance work live behind `EMAIL_ROUTING_V2=false`. MASCI users see no change.

**DO NOT** flip the V2 flag.

**DO NOT** announce Customer #2 onboarding capability publicly until Bucket A is closed.

## Rollback plan
Setting `EMAIL_ROUTING_V2=false` (the current default) reverts every Phase 3 + 15.68 code path to legacy MASCI-only behaviour at the routing layer. Frontend tenant-aware components default to MASCI when `tenant_key === "masci"` so a rollback is invisible to MASCI users.
