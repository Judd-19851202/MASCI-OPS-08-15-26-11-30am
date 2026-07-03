# TRACK 20.1 · Gap Analysis

## Genuine gaps found (all cosmetic · all optional · none blocking)
| Gap                                                              | Severity | Fix scope           | Recommendation      |
|------------------------------------------------------------------|:--------:|---------------------|---------------------|
| Accountability page not wrapped in Track 19.55 `OperationalThreadPage` shell | LOW | Frontend adapter only | Promote in Track 19.56 |
| No OI Attention Strip on Accountability page                       | LOW      | Frontend mount only | Promote in Track 19.56 |
| No universal `RelationshipGraph` visual for supervisor / project / crew / unit | LOW | Frontend adapter    | Promote in Track 19.56 |
| No Guidance Card entry from Attention items on the timeline        | LOW      | Frontend adapter    | Promote in Track 19.56 |
| Section 8 OI card not surfaced inline with the timeline            | LOW      | Frontend mount only | Promote in Track 19.56 |

## Non-gaps (things that appeared to be gaps but aren't)
- The Employee Thread endpoint appears missing → **it exists** as `/api/hr/employees/{id}/accountability/timeline`.
- The Employee current-state readiness object appears missing → **it exists** as `current_state` on the same payload.
- The Employee PDF export appears missing → **it exists** as `/api/hr/employees/{id}/accountability/brief.pdf`.
- The multi-lens permission model appears missing → **it exists** (HR + Safety + Admin share one endpoint with server-side filtering).

## No backend gaps
The audit did not surface a single genuine backend gap. Every field
required for the Universal Employee Thread already exists inside the
platform under a certified endpoint.

## No permission gaps
The current HR + Safety + Admin gating already provides the
role-aware presentation mandated by Track 20.1.

## No data-ownership gaps
Every field has exactly one owner. No duplicated storage exists.

## Deferred (not gaps · out of Track 20.1 scope)
- Employee Thread promotion → Track 19.56.
- Project Thread adoption → Track 19.57.
- Incident Thread adoption → Track 19.58.
- Legacy vocabulary sweep across older pages → non-blocking.
