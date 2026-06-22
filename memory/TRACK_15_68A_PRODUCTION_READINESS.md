# TRACK 15.68A · Production Readiness

_2026-06-22_

## Gating conditions

| Condition | Verdict |
|---|:--:|
| Customer #2 visual certification passes | ❌ FAIL (filenames + dispatch + training/guidance/admin chrome) |
| MASCI parity passes | ✅ PASS (19/19) |
| Contamination scan passes (zero customer-visible) | ❌ FAIL (464 disallowed) |
| PDF branding passes | ✅ PASS |
| Legal template migration passes (no MASCI legal text on non-MASCI tenant) | ✅ PASS |
| No routing regression | ✅ |
| No live emails sent | ✅ |
| `EMAIL_ROUTING_V2` cutover | ❌ NOT AUTHORISED — out of scope for this track |

## Action authorisation
| Action | Status |
|---|:--:|
| Save / push to git | ⚠️ Allowed — no destructive changes; MASCI parity preserved |
| Backend deploy with `EMAIL_ROUTING_V2=false` | ✅ Allowed |
| Frontend deploy | ⚠️ Cautious — splash + PDFs + legal now clean for Customer #2 but filename + dispatch + long-tail chrome still leak |
| `EMAIL_ROUTING_V2=true` production flip | ❌ NOT AUTHORISED |
| Public Customer #2 onboarding announcement | ❌ NOT AUTHORISED |

## Recommendation
- DO deploy backend + frontend (no MASCI regression).
- DO NOT flip the V2 flag.
- DO NOT promise Customer #2 full white-label until filename + chrome sweeps close the remaining ~100 leaks.

## Rollback
`EMAIL_ROUTING_V2=false` (current default) reverts every Phase 3 + 15.68 + 15.68A code path to legacy MASCI-only behaviour. Frontend tenant-aware components default to MASCI when no tenant is set.
