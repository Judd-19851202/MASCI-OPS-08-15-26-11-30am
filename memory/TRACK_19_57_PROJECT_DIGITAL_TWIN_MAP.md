# TRACK 19.57 · Project Digital Twin Map

## Golden questions the thread must answer in ≤ 15 seconds
| # | Question                                | Answered by section(s) |
|---|-----------------------------------------|------------------------|
| 1 | Is this project healthy?                | 1 Mission (Health chip · "Why: …") + 8 OI (Attention + Trend + Top driver) |
| 2 | Is it getting better or worse?          | 8 OI TrendChip (from `project_intelligence.trend_direction` + `trend_percent`) |
| 3 | What needs attention today?             | 2 Attention (top 5) + Action queue |
| 4 | What changed recently?                  | 4 Timeline (today's arrivals · haul cycles · JHAs · last DR) |
| 5 | Who owns the issue?                     | 2 Attention (`owner` field on each item) + 5 Relationships (PM · Superintendent) |
| 6 | What is blocking production?            | 2 Attention (verification / missing proof / missing DR) + 8 OI top driver |
| 7 | Are there safety issues?                | 2 Attention (JHA + OI safety drivers) + 6 Documents (JHA files) |
| 8 | Are there project / PO / constraint issues? | 2 Attention + 4 Timeline (project-day + material-movement) |
| 9 | What evidence supports this?            | 4 Timeline + 6 Documents (JHA files with `download` deep-link) |
| 10 | Where do I click next?                 | 2 Attention `deep_link` + 5 Relationships clickable nodes + "Classic project view" cross-link |

## Certified sources consumed
| Source                                                                    | Owner       | Consumed by section |
|---------------------------------------------------------------------------|-------------|---------------------|
| `GET /api/pm/jobs`                                                        | PM/Admin    | 1 Mission · 5 Relationships |
| `GET /api/jobs/{pn}/recent-context`                                       | PM (public) | 1 Mission · 4 Timeline · 5 Relationships · Action queue |
| `GET /api/operational-events/project-day/{pn}/{date}`                     | Ops         | 4 Timeline           |
| `GET /api/material-movement/daily/{pn}/{date}`                            | Materials   | 2 Attention · 4 Timeline · Action queue |
| `GET /api/job-hazard-files/by-project/{pn}`                               | Safety      | 6 Documents · 4 Timeline · Action queue |
| `GET /api/operational-intelligence/summary` → `project_intelligence`      | OI engine   | 1 Mission (Health) · 2 Attention · 3 Guidance · 8 OI |

## Six Pillars mapping
- **Powerful** — 6 certified backends in parallel, one screen.
- **Simple** — 10 sections · immutable order · fixed shell.
- **Beautiful** — universal typography and spacing inherited from the Track 19.55 shell.
- **Trusted** — every field is sourced from a certified endpoint; honest empty states everywhere else.
- **Proven** — 15 lock assertions in `test_track_19_57_project_thread_promotion.py`.
- **Operational** — golden questions answered in a single scroll on desktop, iPad, and mobile.
