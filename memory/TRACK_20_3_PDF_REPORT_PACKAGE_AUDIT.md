# TRACK 20.3 · PDF · Report Package Audit

| Package                       | Endpoint                                                            | Audience                              | Legal marking             | Photos? | Evidence? | CAPA? | Medical?  | Link · embed · reference |
|-------------------------------|---------------------------------------------------------------------|---------------------------------------|---------------------------|:-------:|:---------:|:-----:|:---------:|--------------------------|
| Executive Case Report         | `GET /incident-cases/{id}/executive-report.pdf`                     | Executive · Board · Owner              | "Executive summary" footer| Redacted| Summary   | Yes   | ❌         | **Link** (Documents section) |
| Weekly Digest                 | `GET /incident-intelligence/digest/weekly.pdf`                      | Safety leadership                     | Internal use only         | ❌      | ❌        | Summary | ❌       | **Reference** (from OI cockpit) |
| Per-type Report Package       | `GET /incident-cases/{id}/reports/{report_type}.pdf`                | Depends on report_type (OSHA, insurance, etc.) | Marked per report_type    | Depends | Depends   | Depends | Depends  | **Link** (Documents section, Safety+Admin only) |
| Report Package (JSON)         | `GET /incident-cases/{id}/reports/{report_type}` (non-PDF)          | Same as above                         | Marked per report_type    | Depends | Depends   | Depends | Depends  | **Reference** (metadata only) |
| Report Types Catalog          | `GET /incident-reports/types`                                       | Safety                                | —                         | —       | —         | —     | —         | Reference (dropdown source) |

## Distribution paths
- Executive Report is deep-linked from Safety Case Workspace (L452-458) and from Executive Case Report page.
- Weekly Digest is emailed via the certified morning-digest recipient list (`/api/incident-intelligence/morning-digest/recipients`).
- Per-type packages are served on-demand — no automated distribution.

## Rules for Track 19.58 (proposed)
1. **Link, do not embed.** The Incident Thread renders a "Documents" section with deep-link buttons; PDFs are never inlined.
2. **Never generate new PDFs.** The thread consumes existing PDF endpoints as opaque downloads.
3. **Respect the report_type gate.** OSHA / insurance / attorney packages appear only when the viewer has Safety + Admin permission.
4. **No new PDF renderer.** Zero new backend rendering code.
5. **Executive Case Report deep-link is preserved** — it remains reachable from both Safety Case Workspace and the promoted thread.

## Certification
Every PDF endpoint listed above already exists and is already permissioned. The proposed Incident Thread consumes them as links only. **No new PDF is generated. No new report package is registered. No distribution path is added.**
