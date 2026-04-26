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

## What's Implemented (2026-04-26)
- **Field-crew Hub at `/`** — 5 module tiles (Daily Reports, Site Inspections, Safety Meetings, JHA, Incident Reports) each leading to `/<module>/new`. Crews see NO counts, NO record lists, NO delete affordance. Tiny "Admin" link in the footer.
- **Admin wall at `/admin/*`** — shared-password gate. Login at `/admin/login` (default password `masci-admin-2026`, set in `backend/.env` → `ADMIN_PASSWORD`). After sign-in, the office gets:
  - `/admin` — landing with all 5 module counts + sign out.
  - `/admin/inspections`, `/admin/meetings`, `/admin/jha`, `/admin/incidents`, `/admin/daily` — full dashboards with view / print / delete.
  - `/admin/<module>/<id>` — individual record view with print + map thumbnail.
- All previous top-level URLs (`/inspections`, `/meetings`, etc.) redirect to their `/admin/*` equivalents and bounce to `/admin/login` if no token.
- All 5 modules: list dashboard, new form, view/print, public submit, share-form QR dialog.
- 81-topic library on Safety Meetings with searchable picker.
- Incident severity tiers, root-cause checklist, witnesses, OSHA-recordable + work-stopped flags.
- **Daily Job Reports** — crews/subs/visitors/equipment/materials/activities with Open-Meteo weather, GPS, 6-photo minimum, prepared-by + superintendent signatures, full bilingual UI, and a **stop-the-line Safety Escalation gate** that triggers when the report flags an accident or injury (must notify Safety with name + time, then confirm an Accident/Incident Report has been filed with its own filing time, before the Daily Report can be submitted).
- **MASCI Current Jobs picker on every form** (31 active jobs + Custom).
- **Bilingual UI (English / Spanish)** — language toggle in every form header. Choice persists per device.
- **Bilingual topic library** — all 81 toolbox-talk topics in construction-trade Spanish.
- **Spanish → English auto-translate at submit** — every freeform Spanish-typed field is sent to `/api/translate` (Claude Haiku 4.5 via Emergent universal LLM key) before POST. Skips photos / signatures / dates / numbers / yes-no / GPS coords. Stored DB record + printed PDF stay 100% English. Graceful fallback on LLM failure — submit is never blocked.
- **Map preview thumbnail on PDF** — every View page renders an `<MapThumbnail>` keyless 3×2 OpenStreetMap tile grid with a MASCI-red marker. Hidden on screen, visible in print preview / PDF only.
- **Native browser spell check** — `setLang()` syncs `document.documentElement.lang`. Browsers automatically swap to the Spanish dictionary when in ES mode.
- **MASCI lockup logo** — sized by WIDTH (not height) so the M emblem + MASCI + SAFETY + tagline stays legible at every breakpoint and on the printed PDF.
- Backend: CRUD on `/api/inspections`, `/api/meetings`, `/api/jhas`, `/api/incidents`, `/api/daily-reports` + `/api/translate` + `/api/admin/{login,check}`. POST + translate are public; GET list / GET single / DELETE are admin-only.
- 81/81 pytest backend (22 new admin-gate tests, 5 translate, 15 daily-report, 39 carry-over modules), full frontend e2e covering field-crew Hub, admin login, RequireAdmin redirect on 7 gated paths, lockup width audit, lang toggle, map thumbnail, translate round-trip.
- All interactive elements have kebab-case `data-testid`.

## Backlog

**P0**
- _none active — Hub, 5 modules, auto-translate, map thumbnail, spell check, admin wall, logo fix all complete and tested_

**P1**
- **Equipment Inspection forms** (daily pre-op for trucks/excavators/rollers/loaders/skid-steers + custom)
- **Distribution List** field on PDF footer (PM/GC/DOT recipients, who got a copy)
- **Email/SMS notification** on incident submit (Resend or SendGrid) — auto-route by severity tier to `jaymn.judd@mascigc.com`
- Multi-user admin (per-account login, audit trail of who viewed/deleted)
- Server-rendered PDF (weasyprint/ReportLab) for browser-independent output
- CSV / multi-report export for monthly compliance reports

**P2**
- Object storage (S3-compatible) for photos once typical record exceeds ~5 MB
- Aggregation `$size` on photos in list endpoints to skip pulling base64 bytes
- Trend dashboard: hazards-by-section, top recurring findings, near-miss → injury conversion
- Refactor: split `server.py` (~750+ lines) into `routes/{admin,inspections,meetings,jhas,incidents,daily_reports,translate}.py` with shared models module

## Next Action Items
1. Hand a foreman the public Hub URL — verify the 5-tile flow on phone end-to-end.
2. Wire **email auto-notify** to safety manager on POST `/api/incidents` (Resend recommended) — playbook fetched, never implemented.
3. Decide if next module is **Equipment Pre-Op** or **DOT Vehicle Daily**.
4. Consider multi-user admin (with audit trail) once 2+ office staff need access.
