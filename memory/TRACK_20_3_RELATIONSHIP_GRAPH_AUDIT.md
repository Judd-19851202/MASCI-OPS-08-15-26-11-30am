# TRACK 20.3 · Relationship Graph Audit

Every incident relationship is grounded in an existing collection or cross-link.

| Node              | Source of link                                                                       | Route?   | Clickable in future thread? | Permission gate            |
|-------------------|--------------------------------------------------------------------------------------|----------|:---------------------------:|----------------------------|
| Project           | `incident_cases.project_number` + `cross_links(target_kind="project")`               | ✅       | ✅ `/pm/project/{pn}/thread` | PM · Safety · Admin        |
| PM / Superintendent | Derived from `pm/jobs` + `jobs/{pn}/recent-context`                                | ✅       | ✅ (Employee Thread)         | HR · Safety · Admin        |
| Reporter          | `incident_cases.reporter_ref` (employee OR anonymous kiosk submission)               | Sometimes| ✅ if employee, else read-only | HR · Safety · Admin      |
| Involved Employees| `incident_cases.involved_employees[]`                                                | ✅       | ✅ Employee Thread           | HR · Safety · Admin        |
| Witnesses         | `incident_witnesses`                                                                 | ❌       | ❌ (name-only, no thread)    | Safety · Admin             |
| Equipment / Fleet | `incident_cases.equipment_units[]` + `cross_links(target_kind="equipment")`          | ✅       | ✅ Fleet Unit Thread         | Fleet · Safety · Admin     |
| Vehicles          | Same as Equipment                                                                    | ✅       | ✅                            | Fleet · Safety · Admin     |
| Photos            | `incident_evidence` (kind=image)                                                     | ✅       | ✅ inline preview             | Safety · Admin             |
| Documents         | `incident_evidence` (kind=file)                                                      | ✅       | ✅ deep-link download         | Safety · Admin             |
| CAPAs             | `corrective_actions.incident_case_id`                                                | ✅       | ✅ CAPA detail                | Safety · Admin · PM (read) |
| Safety Meetings   | `safety_meetings` linked via `project_number` (not case_id direct)                   | ✅       | ✅ meeting detail             | Safety · Admin             |
| Daily Reports     | Related by `project_number` + `date`                                                 | ✅       | ✅ DR detail                  | Safety · Admin · PM        |
| Employee Thread   | Cross-link fan-in                                                                    | ✅       | ✅ `/hr/employees/{id}/thread`| HR · Safety · Admin        |
| Project Thread    | Cross-link fan-in                                                                    | ✅       | ✅ `/pm/project/{pn}/thread`  | PM · Safety · Admin        |
| Fleet Unit Thread | Cross-link fan-in                                                                    | ✅       | ✅ `/fleet/unit/{n}/thread`   | Fleet · Safety · Admin     |
| Insurance / agency| `incident_agency_contacts`                                                           | Sometimes| Read-only display             | Safety · Admin             |
| OSHA package      | `/incident-cases/{id}/reports/osha.pdf` (if configured)                              | ✅       | Read-only download            | Safety · Admin             |

## Certification
- Every rendered relationship must resolve to an existing cross-link or an existing field on `incident_cases`.
- No inferred relationships — if the link is not explicitly stored, it is not drawn.
- No fake nodes — witnesses render as text pills (not clickable) because there is no Witness Thread.
- Cross-portal links respect the destination page's own permission gate; the Incident Thread never bypasses those gates.
