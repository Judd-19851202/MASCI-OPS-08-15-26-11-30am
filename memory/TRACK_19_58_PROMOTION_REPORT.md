# TRACK 19.58 · Promotion Report

## Route
`/safety/incidents/:caseId/thread` — inherits the same Safety JWT the
`SafetyCaseWorkspace` already uses (via `caseWorkspaceApi.js`). Page-
level guard: `isSafety() || isAdmin()` → `<AccessDenied>` otherwise.

## Section-by-section wiring
| # | Section                  | Adapter                | Source                                                          |
|---|--------------------------|------------------------|-----------------------------------------------------------------|
| 1 | Mission Overview         | `missionAdapter`       | `getCase()` + `getHealth()` + `getExecutiveSnapshot()`           |
| 2 | Attention                | `attentionAdapter`     | `case.severity` + `health.blockers[]` + `safety_morning_digest`  |
| 3 | Operational Guidance     | shell (unchanged)      | `safety_morning_digest` product row                              |
| 4 | Timeline                 | `timelineAdapter`      | `listTimeline()` — `/incident-cases/{id}/timeline`               |
| 5 | Relationships            | `relationshipAdapter`  | `case.project_number` + `involved_employees[]` + `equipment_units[]` + `witnesses[]` (text-only) + evidence count |
| 6 | Documents                | `documentsAdapter`     | Executive Report PDF deep-link + non-image evidence items        |
| 7 | Photos                   | shell empty            | Honest empty — evidence photo previews live in the workspace     |
| 8 | Operational Intelligence | shell (unchanged)      | `safety_morning_digest` product row                              |
| 9 | History                  | shell empty            | Honest empty — links to OI history via cockpit                   |
|10 | Audit                    | shell empty            | Honest empty — case audit lives in the workspace                 |

## Universal Action Queue (max 5)
Composed from `health.blockers[]` (up to 3) + open `tasks[]` (up to 3)
+ `safety_morning_digest.top_attention_label` (up to 1). Auto-capped
at 5 by the shell. Every entry uses a specific verb (Complete /
Upload / Finalize / Approve / Verify) — no "monitor / review /
watch".

## Evidence Readiness (replaces "Chain of Custody")
Four buckets: **Excellent · Good · Needs Attention · Incomplete**.
Derived from `health.readiness_level` + `health.blockers.length`.
No percentages · no legal conclusions · no compliance claims.

## Cross-links
- Workspace → Thread: `data-testid="safety-case-open-thread-link"` on `SafetyCaseWorkspace`.
- Thread → Workspace: `data-testid="safety-incident-thread-workspace-link"` on the promoted thread.
