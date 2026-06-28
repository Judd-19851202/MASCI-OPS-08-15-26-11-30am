# Trust & Metric Audit (Track 18.06)

Every metric must answer the five Trust questions (Design System §21):
**Source · Freshness · Meaning · Action · Confidence.**

## Audit results

| Metric | Surface | Source | Freshness | Meaning | Action | Confidence | Verdict |
|---|---|---|---|---|---|---|:---:|
| Eligible drivers | Mission Control | `transport_eligibility_state` | live | drivers in `eligible` state | dispatch them | 100% (state machine) | 🟢 |
| Eligible trucks | Mission Control | `transport_eligibility_state` | live | trucks in `eligible` state | dispatch them | 100% | 🟢 |
| Eligible carriers | Mission Control | `transport_eligibility_state` | live | carriers in `eligible` state | book load | 100% | 🟢 |
| Drivers pending review | Mission Control | `transport_eligibility_state` | live | drivers awaiting HR review | review | 100% | 🟢 |
| Trucks pending inspection | Mission Control | `transport_eligibility_state` | live | trucks needing inspection | schedule | 100% | 🟢 |
| Documents awaiting review | Mission Control | `transport_documents` | live | docs pending verification | review | 100% | 🟢 |
| Expiring documents 30d | Mission Control | `transport_documents` | live | docs expiring within 30 days | renew | 100% | 🟢 |
| Annual inspections due 30d | Mission Control | `transport_inspections` | live | inspections due within 30 days | schedule | 100% | 🟢 |
| Pending corrections | Mission Control | `transport_inspections` | live | inspection fails awaiting fix | resolve | 100% | 🟢 |
| Compliance score | Mission Control | computed in `transportation_experience.py` | live | weighted readiness % | drill-down | documented in Guidance | 🟢 |
| Active rate | Mission Control | computed | live | dispatched today / available | adjust | documented | 🟢 |
| Right Rail audit count | Right Rail | `audit_events` | live | entity-scoped audit rows | read | 100% | 🟢 |
| HR payroll variance | HR | `payroll_variance` | live | hour delta | review | 100% | 🟢 |

## Findings
- **No decorative numbers detected.**
- Every operational metric has a clear source, freshness signal, and operator action.
- Compliance score formula is documented in the Operational Guidance Center.

## Verdict
**🟢 Trust standard met platform-wide.** No metric exists without context.
