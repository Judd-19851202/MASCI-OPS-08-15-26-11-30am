# TRACK 20.2 · Relationship / Ownership / Permission / Reuse Matrix (composite)

## Relationship graph (every project relationship)
```
Project (job_number)
├── Employees      ← daily reports · team roster · PmProjectStaffing
├── Equipment      ← daily reports · dispatch job board · operational events
├── Fleet          ← dispatch · fleet visibility (per-day project view)
├── Daily Reports  ← /api/daily-reports/*
├── Photos         ← JobPhotosLibrary
├── POs            ← operational events feed (per-day)
├── Dispatches     ← JobBoard (dispatch cockpit)
├── Safety         ← job-hazard-files/by-project
├── QA/QC          ← (limited surface today)
├── Survey         ← (limited surface today)
├── Documents      ← JobFolderList
├── OI             ← project_intelligence in /operational-intelligence/summary
├── History        ← OI history filtered by product_id
└── Audit          ← OI audit + admin jobs audit
```
Nothing inferred. Every node exists in a certified location today.

## Ownership Matrix (one owner per category)
| Category             | Owner                                                | Duplicated? |
|----------------------|------------------------------------------------------|:-----------:|
| Project record        | Admin/PM (`/api/admin/jobs/*`, `/api/projects/{id}`) | ❌ No        |
| Daily reports         | PM (`/api/daily-reports/*`)                         | ❌ No        |
| Team roster           | PM (`/api/projects/{id}/members`)                   | ❌ No        |
| Equipment on project  | Ops/Fleet (via daily reports + dispatch)             | ❌ No        |
| Materials & haul      | Materials (`/api/material-movement/daily/*`)         | ❌ No        |
| Dispatch              | Dispatch (`/api/dispatch/*`)                         | ❌ No        |
| Safety (JHAs)         | Safety (`/api/job-hazard-files/by-project/*`)        | ❌ No        |
| Photos                | Field/QA (JobPhotosLibrary + attachments)            | ❌ No        |
| OI signal             | OI engine (`project_intelligence`)                   | ❌ No        |
| History               | OI history                                           | ❌ No        |
| Audit                 | OI audit + admin jobs audit                          | ❌ No        |

Every category has exactly one authoritative owner. **No duplicate storage detected.**

## Permission Matrix (per lens)
| Field                    | PM   | Superint. | Foreman | Safety | Dispatch | Ops  | Exec | Admin |
|--------------------------|------|-----------|---------|--------|----------|------|------|-------|
| Project record            | V/E  | V         | V       | V      | V        | V/E  | V    | V/E   |
| Contract value / P&L      | V    | ─         | ─       | ─      | ─        | V    | V    | V/E   |
| Daily reports             | V/E  | V/E       | V/E     | V      | V        | V    | V    | V/E   |
| Team roster               | V/E  | V         | V       | V      | V        | V    | V    | V/E   |
| Equipment on project      | V    | V         | V       | V      | V/E      | V    | V    | V/E   |
| Materials & haul          | V    | V         | V       | R      | V        | V    | V    | V/E   |
| Safety (JHAs)             | V    | V         | V       | V/E    | R        | V    | V    | V/E   |
| Photos                    | V    | V/E       | V/E     | V      | V        | V    | V    | V/E   |
| OI signal                 | V    | V         | V       | V      | V        | V    | V    | V/E   |
| Audit                     | R    | R         | R       | R      | R        | R    | V    | V/E   |

Legend: **V** view · **E** edit · **R** restricted · **—** hidden.

## Reuse Matrix (Universal Thread section → source)
| Section                       | Source (existing)                                                       | Reuse quotient        |
|-------------------------------|-------------------------------------------------------------------------|-----------------------|
| 1 Mission Overview             | `/api/projects/{id}` + `admin/projects/list`                            | 100 % reuse           |
| 2 Attention                    | Derived from `project_intelligence` + operational-events                 | 100 % via adapter     |
| 3 Operational Guidance         | Track 19.54 GuidanceCard consuming `project_intelligence`               | 100 % reuse           |
| 4 Timeline                     | Operational events + daily reports + dispatch entries                    | 100 % via adapter     |
| 5 Relationships                | Team roster + equipment on project + current unit(s)                     | 100 % via adapter     |
| 6 Documents                    | `JobFolderList` + job-hazard-files                                       | 100 % via adapter     |
| 7 Photos                       | `JobPhotosLibrary`                                                       | 100 % via adapter     |
| 8 Operational Intelligence     | `project_intelligence` in `/summary`                                     | 100 % reuse           |
| 9 History                      | `/operational-intelligence/history?product_id=project_intelligence`      | 100 % reuse           |
| 10 Audit                       | `/operational-intelligence/audit` filtered                               | 100 % reuse           |

## Composite
Every section is reachable from existing endpoints. Zero backend gaps.
