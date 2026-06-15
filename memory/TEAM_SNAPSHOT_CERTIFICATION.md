# TEAM_SNAPSHOT_CERTIFICATION.md · Track 14.0-PM-STAFFING-RUNTIME-CERTIFICATION

**Generated**: 2026-02-14 · **Source**: `routes/project_team_assignments.py` + `test_team_snapshot_embedding.py` runtime tests.

## Snapshot Contract

A `team_snapshot` is the denormalised per-project roster embedded onto the `jobs` document so consumers (Daily Reports, Ownership PDFs, Project Health, PM Command Center) can render the team without re-joining `project_team_assignments`. The snapshot:

* Lists every active assignment as `{user_id, name, display_identity, assignment_role, role_label, email}`.
* Is rewritten on every assignment **create**, **update**, **delete**.
* Translates legacy alias keys (`safety_lead`, `dispatcher_contact`, `asset_admin`, `shop_contact`, `assistant_pm`, `locate_coordinator`, `read_only_stakeholder`) to their current canonical key at read-time.
* Is read-only from a consumer perspective — never written by anything other than the team-assignments routes.

## Runtime tests already passing

`tests/test_team_snapshot_embedding.py` (4 tests passing):

* `test_writer_incident_captures_snapshot` — verifies a write emits the snapshot on the parent document.
* `test_missing_project_number_is_safe` — defensive guard.
* `test_unknown_project_number_is_safe` — defensive guard.
* `test_snapshot_immutability_across_roster_mutation` — once an artefact (Incident, Daily Report) captures the snapshot, later roster changes do NOT mutate the historical artefact.

## Consumer surfaces

| Surface | Reads | Render |
|---|---|---|
| PM Project Health | `jobs.team_snapshot` | Roster card |
| PM Command Center (Team tab) | `project_team_assignments` live | Inline panel |
| Daily Report PDF | embedded `team_snapshot` from time of DR | Header |
| Ownership PDFs | embedded `team_snapshot` | Signatures |
| Incident records | embedded `team_snapshot` | Routing |
| Notifications | live route through `team_routing.recipients_for()` | n/a |

**What needs runtime cert**: end-to-end assignment → snapshot update → consumer render. The 4 existing pytest cases lock the contract; per-consumer visual cert is the missing piece.
