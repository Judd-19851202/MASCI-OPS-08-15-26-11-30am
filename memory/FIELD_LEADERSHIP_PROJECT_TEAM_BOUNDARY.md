# FIELD LEADERSHIP ↔ PROJECT TEAM BOUNDARY (TRACK 15.10)

## TL;DR
- **Field Leadership** owns *documentation*: coaching notes, recognition records, safety training history, accountability ledger, equipment issuance trail.
- **Project Team Management** owns *assignment*: who is on which project in which operational role.
- They share *people* (`user_directory`). They do **not** share assignment authority.

## What this means in practice

| Concern | Field Leadership | Project Team Management |
|---|---|---|
| People records | reads `user_directory` + `employees` | reads `user_directory` + `employees` |
| Per-project assignment | does NOT write | writes `project_team_assignments` |
| Coaching / accountability log | writes `field_leadership_records` | does NOT read or write |
| Safety training records | writes `safety_training_records` | reads them only for the workforce-intel summary |
| Recognition | writes `field_leadership_recognition` | does NOT read or write |
| Equipment issuance | writes `equipment_outstanding` | does NOT read or write |

## Why this matters operationally
- A field-leadership coaching note about Alice is **separate** from her assignment to Project 26-07 as Superintendent. Removing her from the project (Project Team Management surface) does **not** delete coaching history (Field Leadership surface).
- HR's read-only Daily Reports view (Track 15.9 / 15.9A) reads from `daily_reports`, not from Field Leadership.
- PM cannot trigger field-leadership writes from the Project Team page. The Track 15.10 Add Member modal calls only `/api/pm/job/{n}/team` (assignment) and `/api/pm/directory/users` (read-only picker).

## Enforcement
- **No new collection** introduced in Track 15.10 — asserted by `test_no_new_collections_introduced` in `test_track_15_10_project_team_recovery.py`.
- **No silent login creation** from Project Team Add Member — asserted by `test_no_silent_account_creation_in_panel`.
- **No FL writes** from Project Team — Add Member only POSTs to `/api/pm/job/{n}/team`, no `field_leadership_*` endpoints invoked from the panel.

## Future enhancements (separate tracks, NOT blockers)
- A `view this person's coaching history` deep-link from the Project Team row into the Field Leadership Records page would be a nice next step, but it must remain a *navigation* affordance, not a data merge.
