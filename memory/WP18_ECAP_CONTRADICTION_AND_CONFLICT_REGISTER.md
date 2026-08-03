# WP18 ECAP Contradiction and Conflict Register

Date: 2026-08-03

## Register purpose

**Proof label:** `DOCUMENTED_ONLY`

Track the key contradictions surfaced across WP-18A/B/BR/BR2/BR3 and record the accepted ECAP resolution.

## Register

| Conflict ID | Conflict | Resolution | Proof label | Blocking? |
|---|---|---|---|---|
| C01 | BR2 treated enterprise hierarchy as likely missing; BR3 found stronger governance hierarchy evidence | ECAP accepts `EXTEND`, not `BUILD_NEW`, for enterprise hierarchy propagation | `SOURCE_VERIFIED` + `DOCUMENTED_ONLY` | No |
| C02 | BR2 no-go vs BR3 go-with-required-amendments | ECAP resolves this by accepting all blocking amendments into one final contract and authorizing WP-18C with conditions | `DOCUMENTED_ONLY` | No |
| C03 | Financial-adjacent surfaces existed but no budget owner existed | ECAP preserves upstream finance-adjacent value and creates a net-new Budget Hierarchy | `SOURCE_VERIFIED` + `INFERENCE` | No |
| C04 | Schedule / Daily Reports are strongly connected but risk silent overwrite | ECAP requires governed review queue and non-overwrite law | `SOURCE_VERIFIED` + `DOCUMENTED_ONLY` | No |
| C05 | Multiple executive readers risk duplicate meaning | ECAP refactors reporting hierarchy in place and retires the legacy digest lane | `SOURCE_VERIFIED` + `DOCUMENTED_ONLY` | No |

## Register result

No unresolved blocking contradiction remains in the ECAP packet.