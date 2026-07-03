# TRACK 19.57 · Zero Duplication Matrix

For every project-related capability, one authoritative owner.

| Capability                        | Owner                                                                            | Duplicated? | Notes                                    |
|-----------------------------------|----------------------------------------------------------------------------------|:-----------:|------------------------------------------|
| Project record (name · client · location · PM) | Admin/PM · `/api/pm/jobs`, `/api/admin/jobs/*`, `jobs_master`      | ❌ No        | Reused verbatim                          |
| Recent crew · equipment · superintendent      | PM · `/api/jobs/{pn}/recent-context`                              | ❌ No        | Reused verbatim                          |
| Per-day asset events                          | Ops · `/api/operational-events/project-day/{pn}/{date}`           | ❌ No        | Reused verbatim                          |
| Material movement · haul cycles · scale tickets | Materials · `/api/material-movement/daily/{pn}/{date}`          | ❌ No        | Reused verbatim                          |
| Project JHA / documents                       | Safety · `/api/job-hazard-files/by-project/{pn}`                  | ❌ No        | Reused verbatim; deep-link to `.../download` |
| Operational Intelligence signal               | OI engine · `project_intelligence` in `/summary`                  | ❌ No        | Consumed verbatim                        |
| Guidance Card                                 | Track 19.54 primitive                                             | ❌ No        | Consumed verbatim                        |
| Timeline rendering                            | Track 19.54 `OperationalThread` primitive                         | ❌ No        | Consumed verbatim                        |
| Relationship graph                            | Track 19.55 `RelationshipGraph` primitive                         | ❌ No        | Consumed verbatim                        |
| 10-section shell                              | Track 19.55 `OperationalThreadPage` primitive                     | ❌ No        | Consumed verbatim                        |
| Attention chip · Trend chip                   | Track 19.54 primitives                                            | ❌ No        | Consumed verbatim                        |
| Classic project detail (PmProjectDetail)      | PM · `PmProjectDetail.jsx`                                        | ❌ No        | Untouched · now offers cross-link to Thread |
| Job Photos Library                            | PM · `JobPhotosLibrary.jsx`                                       | ❌ No        | Deep-linked in the nav, not re-implemented |
| Auth gate                                     | Client `isPm()` / `isAdmin()` + `RequirePm` wrapper               | ❌ No        | Identical to PmProjectDetail             |

## Zero-duplication statement
Nothing was duplicated. The Project Thread is a **presentation layer**
built entirely from adapters over 6 certified project endpoints and
the Track 19.54/19.55 shared primitives.

## What was NOT built (mandate compliance)
- Not built: another project profile page.
- Not built: another project timeline framework.
- Not built: another project-relationship engine.
- Not built: another photo / document / PO / dispatch / safety surface.
- Not built: another PDF export.
- Not built: another guidance / recommendation / scoring engine.
- Not built: another permission surface.
- Not built: another backend endpoint / module / database / audit collection.
