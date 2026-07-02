# TRACK 19.25 · Employee 360° · Show Me Everything Report

## Coverage confirmation
The Employee 360° page renders **all defensibly-linked** records for the employee. Track 19.25 added session-provenance display; the coverage itself was established in Track 19.21 + 19.22.

## What surfaces per employee

| Category | Source collection | Timeline | Documents tab |
|---|---|---|---|
| HR Lifecycle (hire, promotion, term.) | `db.employees` state changes | ✅ | via lane=hr |
| Training / certificates | Track 19.21 timeline fan-in | ✅ | via lane=hr (training records) / lane=safety |
| PPE issued / returned | `db.employee_records` asset lane | ✅ | ✅ |
| Tools · phones · tablets · iPads · survey · laser | `db.employee_records` asset lane | ✅ | ✅ |
| Vehicle / equipment assignments | Track 19.21 timeline fan-in | ✅ | — |
| Write-ups · coaching · discipline · recognition | `db.employee_records` HR lane | ✅ | ✅ |
| Incidents · Safety Cases | `db.incident_cases` (defensible roles only) | ✅ | — |
| Corrective actions owned | Track 19.21 timeline · CAPA owner | ✅ | — |
| Driver Qualification | Track 19.21 timeline · CDL history | ✅ | via lane=hr |
| Historical imports | `db.employee_records` (any lane) | ✅ (Documents tab) | ✅ + session provenance |
| Documents (originals) | `db.employee_records.source_file_ref` | link | Open original |
| Audit events | `db.employee_record_audit` (append-only) | per-record detail | per-record detail |

## Defensible roles (unchanged from Track 19.21)
- Reporter
- Involved
- Witness
- CAPA owner

**No passive scoring · no incident-presence noise · no political associations.**

## New in Track 19.25 · session provenance on doc cards
Doc card on Documents tab now shows a subtle italic line:
```
Source: 2019 HR File Cabinet · cabinet · University High School · trailer
```
Only rendered when `intake_source_name` is populated (i.e. the record came from a batch upload with session metadata). Records staged via the single-file intake path show no source line — clean fallback.

**Verdict:** GO. Employee 360° remains the single, comprehensive lens.
