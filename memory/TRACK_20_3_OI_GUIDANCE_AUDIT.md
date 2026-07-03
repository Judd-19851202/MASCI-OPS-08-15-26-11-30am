# TRACK 20.3 · Operational Intelligence · Guidance Audit

## Existing OI products relevant to incidents
| Product ID                    | Scope           | Owner          | Feeds                             |
|-------------------------------|-----------------|----------------|-----------------------------------|
| `safety_morning_digest`       | Portfolio       | Safety         | Incidents · CAPA · digest         |
| `executive_operations_brief`  | Portfolio       | Executive      | Incidents (summary)               |
| `corporate_intelligence`      | Portfolio       | Executive      | Incidents (rollup)                |
| `weekly_operations_digest`    | Portfolio       | Operations     | Incidents (weekly rollup)         |
| `project_intelligence`        | Per-project     | PM             | Incidents (per-project rollup)    |

## Existing incident-scoped intelligence endpoints
| Endpoint                                                    | Scope           | Purpose                                          |
|-------------------------------------------------------------|-----------------|--------------------------------------------------|
| `GET /incident-intelligence/home`                           | Portfolio       | Incident intelligence landing                    |
| `GET /incident-intelligence/root-causes`                    | Portfolio       | Root-cause distribution                          |
| `GET /incident-intelligence/corrective-actions`             | Portfolio       | CAPA distribution                                |
| `GET /incident-intelligence/projects`                       | Portfolio       | Per-project incident distribution                |
| `GET /incident-intelligence/fleet`                          | Portfolio       | Per-fleet-unit incident distribution             |
| `GET /incident-intelligence/learning`                       | Portfolio       | Learning / trend surface                         |
| `GET /incident-intelligence/heatmap`                        | Portfolio       | Heatmap                                          |
| `GET /incident-intelligence/brief`                          | Portfolio       | Executive brief                                  |
| `GET /incident-intelligence/portfolio-attention`            | Portfolio       | Attention ranking                                |
| `GET /incident-intelligence/safety-priority`                | Portfolio       | Prioritised safety actions                       |
| `GET /incident-intelligence/pm-project-cases`               | Per PM          | Cases in PM's projects                           |
| `GET /incident-intelligence/morning-digest/preview{,.json}` | Portfolio       | Morning digest preview                           |
| `GET /incident-intelligence/digest/weekly{,.pdf}`           | Portfolio       | Weekly digest                                    |

## Per-case "signal" already available
- `GET /incident-cases/{id}/health` — readiness_level + blockers + score
- `GET /incident-cases/{id}/presence-score` — presence score
- `GET /incident-cases/{id}/executive-snapshot` — executive-grade summary
- `GET /incident-cases/{id}/executive-intelligence` — executive intelligence payload

## Does an `incident_intelligence` OI product exist?
**No — and none should be created.** Incident signals already feed the portfolio-level `safety_morning_digest` product. Per-case attention derives from **case-level** endpoints (`health` + `presence-score` + `executive-snapshot`), not from a new OI product. This is exactly the pattern the Fleet Unit Thread (Track 19.55) and the Project Thread (Track 19.57) use — per-entity metrics feed the Attention chip; a portfolio-level product feeds the Guidance card.

## Feed plan for Track 19.58 (proposed)
| Universal section | Feed                                                                                                              |
|-------------------|-------------------------------------------------------------------------------------------------------------------|
| Mission health    | `case.health.readiness_level` + plain-English "Why:" derived from `health.blockers[]`                              |
| Attention (chip)  | `case.severity` + `case.health.readiness_level`                                                                    |
| Trend (chip)      | `safety_morning_digest.trend_direction` + `.trend_percent` (portfolio proxy — labelled explicitly as portfolio)   |
| Guidance card     | `/incident-intelligence/brief` per-case snippet **OR** `safety_morning_digest.recommendations[]`                   |
| OI section        | `safety_morning_digest` product row (score · attention · trend · top driver · deep-link to OI cockpit)             |
| History           | `GET /operational-intelligence/history/safety_morning_digest`                                                      |

## Certification
**Zero new OI product will be created for Track 19.58. Zero new score model. Zero new attention scoring. Every signal is already ranked, scored, and shipped by the existing certified engine.**
