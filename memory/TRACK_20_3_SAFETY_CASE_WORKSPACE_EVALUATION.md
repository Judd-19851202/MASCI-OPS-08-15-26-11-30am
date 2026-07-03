# TRACK 20.3 · Safety Case Workspace Evaluation

## Question
Is the Safety Case Workspace (`/app/frontend/src/pages/SafetyCaseWorkspace.jsx` · 629 LOC) already the Incident Operational Thread?

## Structured evaluation
| Universal Thread requirement (Track 19.55) | Present in SafetyCaseWorkspace today?                                       | Notes                                          |
|--------------------------------------------|-----------------------------------------------------------------------------|------------------------------------------------|
| Case Story (one-paragraph narrative)       | ✅ YES · lines 124-131                                                       | "always-visible one-paragraph narrative"        |
| Next Action (clickable)                    | ✅ YES · lines 133-149                                                       | Clickable jump to the resolving tab             |
| Timeline spine                             | ✅ YES · `TimelinePanel` L227-268 · `/incident-cases/{id}/timeline`           | Vertical rail, color-coded by kind              |
| Blockers surfaced                          | ✅ YES · `CaseHealth` L150 · `field_block` / `safety_block` chips             | Clickable to resolving tab                      |
| Evidence                                   | ✅ YES · `EvidencePanel` L269                                                 | Reuses `/incident-cases/{id}/evidence`          |
| Witnesses                                  | ✅ YES · witness tab                                                          | Reuses `/incident-cases/{id}/witnesses`         |
| Medical                                    | ✅ YES · medical tab                                                          | Reuses `/incident-cases/{id}/medical` (restricted) |
| Agency (police / fire / utility)           | ✅ YES · agency tab                                                           | Reuses `/incident-cases/{id}/agency-contacts`   |
| Communications                             | ✅ YES · communications tab                                                   | Reuses `/incident-cases/{id}/communications`    |
| Tasks · CAPA-adjacent                      | ✅ YES · tasks tab                                                            | Reuses `/incident-cases/{id}/tasks`             |
| Health / presence score                    | ✅ YES · `CaseHealth` + `ExecutiveSnapshot`                                   | Reuses `/health` + `/executive-snapshot`        |
| Executive readiness                        | ✅ YES · executive-review action + PDF deep-link (L452-458)                   | Reuses `/executive-report.pdf`                  |
| Audit trail                                | ✅ YES · read via `/incident-cases/{id}/audit`                                | Available in the workspace payload              |
| Cross-links (project / employee / equipment)| ✅ YES · `cross-links` API                                                   | Reuses `/incident-cases/{id}/cross-links`       |
| PDF outputs                                | ✅ YES · deep-linked                                                          | `/executive-report.pdf` + `/reports/{type}.pdf` |
| Universal Thread 10-section shell          | ❌ NO                                                                        | Uses tabbed layout, not Track 19.55 shell       |
| Universal Guidance Card (Track 19.54)      | ❌ NO                                                                        | Case Story + Next Action serve this role today, but do not use the shared primitive |
| Universal AttentionChip / TrendChip        | ❌ NO                                                                        | Blockers are shown via `CaseHealth`, not the shared chip primitives |
| Universal RelationshipGraph                | ❌ NO                                                                        | Cross-links exist but are not rendered as the shared graph primitive |
| Universal Action Queue (max 5)             | ❌ NO                                                                        | Tasks tab shows all tasks, not the shared capped queue |

## Verdict
The Safety Case Workspace **already contains 15 out of 20** Universal Thread requirements. What is missing is not backend or data — it is **presentation harmonisation**. Rendering the same certified payload through the Track 19.55 `OperationalThreadPage` shell (with pure adapters) would make every incident read like every other Operational Thread on the platform. The Case Workspace remains available for full-investigation work; the promoted Incident Thread becomes the "morning read" view that Safety, PM, and Executive share.

## Do not retire the Case Workspace
- Safety investigators actively need the tabbed workspace layout for evidence entry, witness statements, and task work.
- The workspace supports **write** operations (post evidence, patch witness, add task) — the Thread will be **read-only**.
- Both surfaces coexist, exactly like `PmProjectDetail` and `PmProjectThread` do today.
