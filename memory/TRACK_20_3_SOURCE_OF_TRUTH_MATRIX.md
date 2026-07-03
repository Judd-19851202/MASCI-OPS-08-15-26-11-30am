# TRACK 20.3 · Source-of-Truth Matrix

Exactly one owner per category. If two owners exist → architectural defect.

| Category                    | Authoritative collection / endpoint                                               | Owner portal   | Permission gate                                     | Duplicate? |
|-----------------------------|-----------------------------------------------------------------------------------|----------------|-----------------------------------------------------|:----------:|
| Original field report       | `incidents` (legacy) → `/api/incidents/{id}`                                      | Safety · Admin | `require_admin` (mutations) · public POST (rate-lt) | ❌         |
| Incident type / severity    | `incident_cases.type` · `.severity`                                               | Safety         | Admin / Safety                                       | ❌         |
| Project / job number        | `incident_cases.project_number`                                                   | Safety         | Admin / Safety / PM                                  | ❌         |
| Reporter                    | `incidents.reporter` (field) · `incident_cases.reporter_ref`                       | Safety         | Admin / Safety                                       | ❌         |
| Involved employees          | `incident_cases.involved_employees[]`                                             | Safety · HR    | Admin / Safety / HR                                 | ❌         |
| Witnesses                   | `incident_witnesses` → `/incident-cases/{id}/witnesses`                            | Safety         | Safety · Admin                                       | ❌         |
| Personnel present           | `incident_cases.personnel_present[]`                                              | Safety         | Safety · Admin                                       | ❌         |
| Equipment / fleet units     | `incident_cases.equipment_units[]` · `cross_links` (equipment)                     | Fleet · Safety | Safety · Admin · Fleet                              | ❌         |
| Photos                      | `incident_evidence` (image kind)                                                  | Safety         | Safety · Admin                                       | ❌         |
| Attachments (non-photo)     | `incident_evidence` (file kind)                                                   | Safety         | Safety · Admin                                       | ❌         |
| GPS / location              | `incident_cases.gps` · `.location`                                                | Safety         | Safety · Admin                                       | ❌         |
| Weather                     | `incident_cases.weather_snapshot`                                                 | Safety         | Safety · Admin                                       | ❌         |
| Narrative                   | `incident_cases.narrative`                                                        | Safety         | Safety · Admin                                       | ❌         |
| Immediate actions           | `incident_cases.immediate_actions`                                                | Safety         | Safety · Admin                                       | ❌         |
| Medical                     | `incident_medical` → `/incident-cases/{id}/medical`                                | Safety         | **Safety + Admin only · never PM/exec/HR by default** | ❌       |
| Agency (police/fire/utility)| `incident_agency_contacts` → `/incident-cases/{id}/agency-contacts`                | Safety         | Safety · Admin                                       | ❌         |
| Evidence                    | `incident_evidence` → `/incident-cases/{id}/evidence`                              | Safety         | Safety · Admin                                       | ❌         |
| Root cause                  | `incident_cases.root_cause` · `incident_intelligence/root-causes` (portfolio view) | Safety         | Safety · Admin · Executive                          | ❌         |
| Contributing factors        | `incident_cases.contributing_factors[]`                                            | Safety         | Safety · Admin                                       | ❌         |
| CAPA                        | `corrective_actions` → `/corrective-actions`                                       | Safety         | Safety · Admin · PM (read)                          | ❌         |
| Safety Tasks (case-scoped)  | `incident_tasks` → `/incident-cases/{id}/tasks`                                    | Safety         | Safety · Admin                                       | ❌         |
| Communications              | `incident_communications` → `/incident-cases/{id}/communications`                  | Safety         | Safety · Admin                                       | ❌         |
| Timeline                    | Composite view over case events + child collections → `/incident-cases/{id}/timeline` | Safety      | Safety · Admin · PM (redacted)                      | ❌         |
| Status / readiness          | `incident_cases.status` · `.field_block` · `.safety_block` · presence-score        | Safety         | Safety · Admin                                       | ❌         |
| Reports / PDFs              | `/incident-cases/{id}/reports/{type}{,.pdf}` · `/executive-report.pdf`              | Safety · Exec  | Safety · Admin · Executive                          | ❌         |
| Email routing               | `oi_recipients` + `morning_digest_recipients`                                     | Admin          | Admin only                                           | ❌         |
| Audit log                   | `incident_case_audit` + `incident_case_events` → `/incident-cases/{id}/audit`      | Safety · Admin | Safety · Admin                                       | ❌         |
| Employee linkage            | `cross_links` where target_kind=employee                                          | Safety         | Safety · HR (redacted for others)                   | ❌         |
| Project linkage             | `incident_cases.project_number` + `cross_links` where target_kind=project         | Safety · PM    | Safety · PM · Admin                                  | ❌         |
| Equipment linkage           | `cross_links` where target_kind=equipment                                         | Safety · Fleet | Safety · Fleet · Admin                              | ❌         |

## Duplicate-storage certificate
**No duplicate storage detected.** Every category resolves to exactly one authoritative collection and one authoritative endpoint. The legacy `incidents` collection is the only cross-cutting concern; it is bridged to `incident_cases` via `/api/incident-cases/legacy/{incident_id}`.

## Downstream consumers (read-only)
- Executive Intelligence Center reads `/incident-intelligence/portfolio-attention` + `/safety-priority`.
- OI cockpit reads incident signals via `safety_morning_digest`, `executive_operations_brief`, and `corporate_intelligence` products.
- Employee Thread reads `incident_cases` (redacted list) via the accountability timeline.
- Project Thread reads `project_intelligence` OI product (which internally aggregates incident signals).
- Fleet Unit Thread reads `assets/{n}/timeline` which includes incident cross-links.
