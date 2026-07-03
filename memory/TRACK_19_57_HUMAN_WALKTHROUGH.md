# TRACK 19.57 · Human Walkthrough

Every persona is asked: **can they answer the 10 golden questions in
15 seconds using only the Project Thread?**

| Persona            | Answered in ≤ 15s? | Notes                                                                                       |
|--------------------|:------------------:|---------------------------------------------------------------------------------------------|
| Project Manager    | ✅                 | Mission facts + OI health + Attention items + cross-link back to classic detail.            |
| Superintendent     | ✅                 | Recent superintendent visible in Mission; today's crew / equipment in Relationships; action queue calls out missing DR / missing proof. |
| Foreman            | ✅                 | Sees recent crew + equipment (from smart-prefill source) + today's asset arrivals in Timeline. |
| Safety Manager     | ✅                 | Section 6 lists JHAs directly with a working `download` deep-link.                          |
| Operations Manager | ✅                 | Section 8 OI (score + trend + top driver) answers "is it getting better or worse?"           |
| Executive          | ✅                 | Mission + Attention + OI. No noise. No decorative widgets.                                  |
| Dispatcher         | ✅                 | Section 4 Timeline shows today's haul cycles from material-movement.                        |
| Fleet Manager      | ✅                 | Equipment relationships + today's asset arrivals in Timeline.                               |
| HR                 | ✅                 | Read-only relationship view of PM + Superintendent + recent crew. No HR-private data leaks. |
| Accounting         | ✅ (via link)      | Financial data is out of scope for this thread — Accounting deep-links to P&L from the classic detail page. Not duplicated here. |

## Delete test
Every card / section was tested against: **"If this disappeared tomorrow,
would someone make a worse operational decision?"** All 10 sections
answer YES → all 10 sections are retained. Photos / History / Audit
render honest empty states because filling them with fake rows would
violate the mandate.
