# MASCI Safety Hub — PRD

## Original Problem Statement
> "I want/need a fillable form I can send out to inspectors to do site safety inspections, then print or save as PDF... Look at what I have see what we could add or take away to make it awesome & work flawlessly on computers or mobile devices."

Evolved into a multi-module **MASCI Safety Hub**: Site Inspections, Safety Meetings (toolbox talks), Job Hazard Analysis (JHA), and Accident/Incident Reports — one branded URL, no login, mobile-first, with print/PDF + QR-share for trailer postings.

## User Choices
- Single deployment, multi-module under one URL
- No login — public form links + QR codes for any device
- MASCI red/black branding throughout, "No Shortcuts • No Exceptions"
- Photos with MASCI watermarks, on-screen signatures, GPS auto-fill via OpenStreetMap

## Architecture
- **Backend:** FastAPI + Motor (MongoDB) at `/app/backend/server.py`. Routes prefixed `/api`.
- **Frontend:** React 19 + Tailwind + shadcn/ui + lucide-react + react-signature-canvas + qrcode.react + sonner. CRA dev server on port 3000.
- **Collections:** `inspections`, `meetings`, `jhas`, `incidents`. Photos + signatures stored as base64 data URLs inline.
- **Design:** Swiss/industrial high-contrast — Chivo display + IBM Plex Sans body. MASCI red `#C8102E` accent. Print-optimized stylesheet.

## Personas
- **Field Inspector / Foreman** — completes form in field on phone (signatures, photos)
- **Crew member** — signs attendance on Safety Meetings, sign-off on JHA
- **Safety Manager / Office** — reviews dashboards, prints PDFs, files incidents

## Modules

### 01. Site Inspections (`/inspections`)
- 13 sections matching MASCI source PDF, conditional sub-checklists, real-time PASS/FAIL grading, auto-fail logic, photo uploads with compositing watermark, GPS auto-fill, inspector + foreman signatures.

### 02. Safety Meetings (`/meetings`) — toolbox talks
- 81-topic searchable Topic Library (heavy-civil/highway/concrete/MOT/electrical/etc.) with prefilled hazards, discussion points, references, action items
- Custom Topic option, multi-attendee signatures, conductor signature, photos
- **Searchable Combobox topic picker** (`TopicPicker.jsx` — cmdk + Popover, grouped by category)

### 03. Job Hazard Analysis (`/jha`)
- Pre-task multi-step hazard/control grid, PPE & permit checklists, crew sign-off, foreman approval signature

### 04. Accident / Incident Reports (`/incidents`) — **NEW**
- 6 severity tiers: Near Miss → First Aid → Medical → Restricted Duty → Lost Time (DART) → Fatality/Catastrophic
- 9 incident types (Injury, Near Miss, Property Damage, Vehicle, Environmental, Utility Strike, Public/3rd-Party, Security, Other)
- Conditional Person-Involved section (body part, injury nature, treatment, medical facility)
- Root-cause categories (PPE/Training/Procedure/Supervision/Equipment/Design/Communication/Fatigue/Housekeeping/Weather)
- Multiple witness statements
- Notification log (Safety Mgr / PM / GC / Owner / OSHA / Other)
- Reporter + Supervisor signatures, photo evidence with watermark, printable PDF, public submit link via QR

## What's Implemented (2026-02-25)
- Hub `/` with 4 module tiles + Recent Activity feed (merged across all modules)
- All 4 modules: list dashboard, new form, view/print, public submit, share-form QR dialog
- 81-topic library on Safety Meetings with searchable picker (filter by title or category)
- Incident severity tiers, root-cause checklist, witnesses, OSHA-recordable + work-stopped flags
- **MASCI Current Jobs picker on every form** (Inspections / Meetings / JHA / Incidents) — searchable by job #, name, route, or city; auto-fills project name + project number (and location when blank); 31 active jobs from `MASCI Current Jobs.pdf`; "Custom Job" option for anything not in the list.
- Backend: CRUD on `/api/incidents` + regression-passed CRUD on inspections/meetings/jhas
- 39/39 pytest backend, full frontend e2e covering 4-tile hub, picker filter, severity selector, public-mode routing
- All interactive elements have kebab-case `data-testid`

## Backlog

**P0**
- _none active — MVP + 4 modules complete and tested_

**P1**
- **Equipment Inspection forms** (daily pre-op for trucks/excavators/rollers/loaders/skid-steers + custom)
- **Distribution List** field on PDF footer (PM/GC/DOT recipients, who got a copy)
- **Email/SMS notification** on incident submit (Resend or SendGrid) — auto-route by severity tier
- Server-rendered PDF (weasyprint/ReportLab) for consistent output independent of browser
- CSV / multi-report export for monthly compliance reports

**P2**
- Object storage (S3-compatible) for photos once typical record exceeds ~5 MB
- Aggregation `$size` on photos in list endpoints to skip pulling base64 bytes
- Trend dashboard: hazards-by-section, top recurring findings, near-miss → injury conversion
- Map preview thumbnail on printed PDF (using GPS lat/lng + tile snapshot)
- Optional inspector login + per-account dashboards
- Refactor: split server.py into `routes/{inspections,meetings,jhas,incidents}.py` once next module is added (file currently ~548 lines)

## Next Action Items
1. Hand a foreman the `/incidents/submit` URL and run a real near-miss through it on phone — gather feedback.
2. Decide whether to wire **email auto-notify** to safety manager on POST `/api/incidents` (Resend recommended).
3. Decide if the next module is **Equipment Pre-Op** or **DOT Vehicle Daily**.
4. Optional: refactor `server.py` into per-module routers once a 5th module is added.
