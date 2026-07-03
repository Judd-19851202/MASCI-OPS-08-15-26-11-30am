# TRACK 20.3 · Noise · Duplicate · Defect Audit

## Findings and classifications

| Finding                                                                                     | Classification | Rationale                                                                                                             |
|---------------------------------------------------------------------------------------------|:--------------:|-----------------------------------------------------------------------------------------------------------------------|
| Safety Case Workspace (`SafetyCaseWorkspace.jsx`)                                           | KEEP           | Investigation workhorse. Write-capable. Cannot be replaced by a read-only thread.                                     |
| Incidents Dashboard (`IncidentsDashboard.jsx`)                                              | KEEP           | Portfolio triage entry point.                                                                                         |
| Incident Report Viewer (`IncidentReportViewer.jsx`)                                         | KEEP           | Legacy `incidents` read view. Bridged via `/incident-cases/legacy/{id}`.                                              |
| Incident Report (Public) (`IncidentReport.jsx`)                                             | KEEP           | Public intake. Rate-limited.                                                                                          |
| Near-Miss Kiosk (`NearMissKiosk.jsx`)                                                       | KEEP           | Anonymous kiosk. Legally important input path.                                                                        |
| Executive Case Report (`ExecutiveCaseReport.jsx`)                                           | KEEP           | Boardroom-grade brief. Deep-linked from workspace + thread.                                                           |
| Executive Intelligence (`ExecutiveIntelligence.jsx`)                                        | KEEP           | Portfolio-level attention view.                                                                                       |
| Safety Incidents (`SafetyIncidents.jsx`)                                                    | ADAPT          | Safety-centric listing. Consider re-labelling "Cases" to distinguish from legacy incidents; not required for 19.58.   |
| HR Incidents (`HrIncidents.jsx`)                                                            | KEEP           | HR-scoped rollup already redacts appropriately.                                                                       |
| Safety Corrective Actions (`SafetyCorrectiveActions.jsx`)                                   | KEEP           | CAPA queue. Distinct write surface.                                                                                   |
| Safety Reports (`SafetyReports.jsx`)                                                        | KEEP           | Report package browser.                                                                                               |
| Safety Digest (`SafetyDigest.jsx`)                                                          | KEEP           | Digest preview.                                                                                                       |
| Notifications Digest (`NotificationsDigest.jsx`)                                            | KEEP           | Recipient management.                                                                                                 |
| Two incident collections (`incidents` legacy + `incident_cases`)                            | KEEP + BRIDGE  | Legacy compatibility via `/incident-cases/legacy/{id}` is intentional; no reason to force a migration for 19.58.      |
| No shared Universal Thread shell across incident surfaces                                    | PROMOTE        | The Case Workspace expresses the same operational story with a different vocabulary; Track 19.58 solves this.         |
| No shared Guidance Card / Attention Chip / Relationship Graph on incident pages              | PROMOTE        | Track 19.58 renders these via Track 19.54 + 19.55 primitives.                                                          |
| Report package PDF endpoints route by `report_type`                                          | KEEP           | Sound architecture; thread links per report_type as-is.                                                               |
| Duplicate incident detail (would exist if a second detail page were built)                   | REMOVE (prevent)| **Prohibition** — Track 19.58 must be a promotion, not a second detail page.                                          |
| Widget: legacy per-page "recent incidents" cards on portal hubs                              | RESTRICT       | Ensure these link to the promoted thread when clicked, and never to a duplicate detail page.                          |
| Any raw JSON exposure on a portal surface                                                    | RETIRE (if found)| None identified during this audit; if found later, remove.                                                            |
| Generic "recommendation" copy without a `why`                                                | RESTRICT       | The promoted thread must always pair a chip with plain-English narration.                                             |

## Zero-cost changes recommended for Track 19.58 (still optional)
1. Add a "Universal Thread" cross-link to `SafetyCaseWorkspace` (mirrors the Employee / Project / Fleet cross-link pattern).
2. Add a "Case workspace" cross-link on the promoted thread.
3. Ensure the Executive Case Report deep-link is exposed from the thread's Documents section.

## No architectural defect declared
No duplicate ownership, no orphaned collection, no leaking widget was found during this audit. Every incident surface listed above already respects its permission gate and its ownership boundary.
