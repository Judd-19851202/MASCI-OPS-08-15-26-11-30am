# TRACK 20.1 · Data Ownership Matrix

Every employee-related field belongs to exactly one owner.

| Field / capability                     | Owner portal        | Endpoint (canonical)                                                | Consumed by                                        |
|----------------------------------------|---------------------|---------------------------------------------------------------------|----------------------------------------------------|
| Employee CRUD (name / email / role)    | Admin / HR          | `GET /employees`, `POST/PUT/DELETE /admin/employees/{id}`           | Every portal via `EmployeeCombo`                    |
| Employment lifecycle (hire / term)     | HR                  | Employee record fields + timeline category `HR Lifecycle`           | Accountability timeline · HR Hub · OI              |
| Roster                                 | HR                  | `GET /hr/employee-roster`                                            | Every portal that picks an employee                |
| Training completion                    | HR                  | `GET /training/videos` + acknowledgements                            | Timeline `Training` category · HR Hub · Cockpit    |
| CDL / DOT medical                      | Transportation      | Timeline `Driver Qualification` payload                              | Accountability timeline · Dispatch · Cockpit        |
| Driver-qualification holds             | Transportation      | Same as above                                                        | Accountability timeline · Dispatch                  |
| Safety incidents                       | Safety              | Incident engine (Track 12.x)                                         | Timeline `Incidents` category · Safety Hub · OI    |
| PPE & equipment assignments            | Shop / Fleet        | Fleet assignment tables                                              | Timeline `PPE & Equipment` category                |
| Current project assignment             | PM                  | Daily reports + project assignments                                  | Timeline `Field Leadership` category · PM CC        |
| Field-leadership notes / recognition   | Ops / PM            | Field-leadership record store                                        | Timeline `Field Leadership` category                |
| Documents / historical records         | HR / Admin          | `GET /employee-records/records/{rid}/file`                           | Employee Profile · Historical Records queue         |
| Photos                                 | Field / Safety      | Photo storage (already existing)                                    | Employee Profile · Safety records                   |
| Audit                                  | Admin               | `GET /operational-intelligence/audit`                                | Cockpit                                             |
| Operational Intelligence score / trend | OI engine           | `GET /operational-intelligence/summary`                              | Attention Strips · Guidance Card · Cockpit         |

## Duplicate-ownership scan
None. Every field has exactly one authoritative owner. The Accountability
timeline is a **view**, not a copy — it queries owner endpoints server-side
and returns a merged event list. No duplicate storage.

## Zero-drift statement
- No employee field is stored in two collections.
- No employee field is served by two APIs of record.
- No portal reimplements roster / lifecycle / training / driver-qualification / incident storage.
- OI engine remains the sole score/attention/trend producer.
- Operational Thread is a pure presentation layer over these owners.
