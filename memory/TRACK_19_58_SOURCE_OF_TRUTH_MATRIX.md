# TRACK 19.58 · Source-of-Truth Matrix

Every field the thread renders traces back to exactly one certified endpoint.

| Field / rendering slot          | Certified endpoint                                              | Adapter                | Duplicated? |
|---------------------------------|-----------------------------------------------------------------|------------------------|:-----------:|
| Case number · title · severity · status · project · reporter · investigator · location · opened | `GET /incident-cases/{id}` | `missionAdapter` | ❌ |
| Readiness level · blockers      | `GET /incident-cases/{id}/health`                               | `missionAdapter` · `attentionAdapter` · `actionQueueAdapter` · Evidence Readiness | ❌ |
| Snapshot headline               | `GET /incident-cases/{id}/executive-snapshot`                   | `missionAdapter`       | ❌          |
| Investigation timeline          | `GET /incident-cases/{id}/timeline`                             | `timelineAdapter`      | ❌          |
| Evidence items · documents      | `GET /incident-cases/{id}/evidence`                             | `documentsAdapter` · Relationships evidence count | ❌ |
| Witnesses (text-only pills)     | `GET /incident-cases/{id}/witnesses`                            | `relationshipAdapter`  | ❌          |
| Open tasks                      | `GET /incident-cases/{id}/tasks`                                | `actionQueueAdapter`   | ❌          |
| Portfolio signal (Attention · Trend · Guidance) | `GET /operational-intelligence/summary` → `safety_morning_digest` | `attentionAdapter` · shell | ❌ |
| Executive Report deep-link      | `GET /incident-cases/{id}/executive-report.pdf`                 | `documentsAdapter`     | ❌          |

## Sections that render honest empty per Track 20.3
| Section          | Reason                                                              |
|------------------|---------------------------------------------------------------------|
| Photos           | Photo previews live in the workspace's `EvidencePanel`              |
| History          | OI history for `safety_morning_digest` is deep-linked, not embedded |
| Audit            | Case audit is Safety+Admin only — never fetched to avoid 403 leak    |
| Medical (implicit)| Never fetched by the thread                                        |
| Agency (implicit)| Never fetched by the thread                                        |
| Communications (implicit)| Never fetched by the thread                                |

## Zero-duplicate statement
Every rendered field originates from exactly one certified endpoint.
The thread never rewrites a value, never recomputes a score, and
never introduces a parallel truth source.
