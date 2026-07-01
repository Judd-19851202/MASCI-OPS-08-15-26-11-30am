# Track 19.15 · 08 · Market / Industry Comparison

Extracted best practices — DO NOT COPY. This is a benchmark study.

## Procore Incident Reporting
- Incident-type branching UI with progressive disclosure per type
- Photo grid with EXIF timestamps + captions
- Case-lifecycle status ladder (Open / Under Investigation / Corrective Actions / Closed)
- Root-cause taxonomy separate from field-facing form
- OSHA 300 / 301 export path
- Source: procore.com/incident-reporting product page

## HCSS Safety / HeavyJob
- Utility-strike specific fields (locate ticket number, potholing, hand-dig)
- 811 workflow integration hooks
- Corrective-action tracking with owner + due date
- Source: hcss.com/safety product page

## Raken Safety / Daily Reporting
- Field-first minimal capture, safety handles the rest
- Photo-first mobile UX (camera opens by default)
- Witness workflow with contact-info retention
- Source: rakenapp.com

## SafetyCulture (iAuditor)
- Template-driven branching (each incident type = a template)
- Corrective-action workflow with SLA reminders
- Read-only report distribution per role
- Source: safetyculture.com

## EHS Insight
- Case management with investigation lead + team
- Regulatory tracking (OSHA / EPA / DOT) with agency contact log
- Preventability determination flag (Management-owned)
- Source: ehsinsight.com

## VelocityEHS
- Root-cause analysis workflow (5 Whys / Fishbone) as first-class UI
- Corrective + preventive action (CAPA) tracking
- Analytics dashboards for trends
- Source: ehs.com

## KPA
- Motive/Samsara integration for vehicle incidents
- Automatic OSHA recordability suggestion (Safety confirms)
- Source: kpa.io

## Intelex
- Multi-jurisdictional regulatory tracking
- Legal-hold flagging on evidence
- Source: intelex.com

## Fleetio / Samsara / Motive
- Automatic vehicle-incident linkage from telemetry
- Driver behavior context (harsh braking, speeding at time of incident)
- Dashcam evidence auto-attached
- Source: fleetio.com, samsara.com, gomotive.com

## Utility strike best practices (industry)
- Positive locate confirmation before excavation (811 / Sunshine 811 in FL)
- Ticket number capture at scene
- Potholing / vacuum excavation / hand-dig documentation
- Utility-owner damage notification within 24 hours
- Source: Common Ground Alliance (CGA) DIRT Report, Sunshine 811 Florida guidelines

## OSHA recordkeeping guidance
- 29 CFR 1904 recordability criteria
- Recordable ≠ reportable (fatality, hospitalization, amputation, eye loss must be reported within 8/24 hrs)
- OSHA 300, 300A, 301 forms
- Source: osha.gov/recordkeeping

## Applied to MASCI (best-practice synthesis)

1. **Incident-type branching UI** — take from Procore + SafetyCulture
2. **Utility-strike deep questions** — take from HCSS + CGA DIRT
3. **Field-first minimal capture** — take from Raken
4. **Case-lifecycle status ladder** — take from EHS Insight
5. **Root-cause taxonomy separated from field UI** — take from VelocityEHS
6. **OSHA determination = Safety-owned, not field-owned** — take from OSHA guidance + KPA
7. **Evidence classification with retention flags** — take from Intelex
8. **Vehicle-incident telemetry linkage** — future integration with existing Motive-Samsara pipeline

Nothing above requires copying UI or code. Every applied pattern maps to a Track 19.16–19.20 deliverable.
