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

### 04. Accident / Incident Reports (`/incidents`)
- 6 severity tiers: Near Miss → First Aid → Medical → Restricted Duty → Lost Time (DART) → Fatality/Catastrophic
- 9 incident types (Injury, Near Miss, Property Damage, Vehicle, Environmental, Utility Strike, Public/3rd-Party, Security, Other)
- Conditional Person-Involved section (body part, injury nature, treatment, medical facility)
- Root-cause categories (PPE/Training/Procedure/Supervision/Equipment/Design/Communication/Fatigue/Housekeeping/Weather)
- Multiple witness statements
- Notification log (Safety Mgr / PM / GC / Owner / OSHA / Other)
- Reporter + Supervisor signatures, photo evidence with watermark, printable PDF, public submit link via QR

### 05. Equipment Pre-Op Inspections (`/equipment`) — **NEW (2026-02-26)**
- 23 equipment types covering every heavy-civil machine: Dozer, Excavator, Loader, Motor Grader, Skid Steer, Paver, Backhoe, Tractor, Telehandler/Forklift, Haul Truck, Water Truck, Shuttle Buggy/Transfer Machine, Steel Drum & Rubber Tire Asphalt Rollers, Asphalt Milling Machine, Dirt Roller, Dirt Mixer, Road Widener, Broom, Curb Machine, Plate Compactor, Walk Behind Saw, Other.
- OSHA 1926-aligned checklists per type (Fluids & Leaks · Walk-Around · Operator Station · Lights & Electrical · Controls & Brakes · Safety Equipment), each with equipment-specific items (e.g. screed plates for pavers, restraint bar for skid steers, body prop for haul trucks).
- PASS / FAIL / N/A buttons with required note on FAIL.
- Optional **hour meter** AND/OR **odometer** (some equipment has only one).
- Saved equipment units (auto-remembers every unit submitted, picker shows them next time per type).
- Live tally bar + "FAIL — DO NOT OPERATE" banner the moment any item fails.
- Operator certification statement + signature; stop-the-line if no items rated.
- WeasyPrint PDF includes a red "OUT OF SERVICE" banner header on FAILs.
- **Auto-email subject is automatically prefixed `EQUIPMENT FAIL · `** so PMs see it instantly. Sent to assigned PM + always-CC pipeline (David / Chris / Ramon / Jaymn / safety@).

## What's Implemented (2026-04-26)
- **Field-crew Hub at `/`** — 5 module tiles (Daily Reports, Site Inspections, Safety Meetings, JHA, Incident Reports) each leading to `/<module>/new`. Crews see NO counts, NO record lists, NO delete affordance. Tiny "Admin" link in the footer.
- **Admin wall at `/admin/*`** — shared-password gate. Login at `/admin/login` (default password `masci-admin-2026`, set in `backend/.env` → `ADMIN_PASSWORD`). After sign-in, the office gets:
  - `/admin` — landing with all 5 module counts + sign out + **Auto-Email Routing panel** (PM table + always-CC + live status badge).
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
- **Server-rendered PDFs (WeasyPrint)** + manual `/api/email-report` (Resend) for one-off office sends.
- **Auto-Email PM Routing (2026-02-26)** — every successful POST to `/api/{inspections|meetings|jhas|incidents|daily-reports}` schedules a fire-and-forget background task that:
  1. Resolves the assigned PM by `project_number` (exact → CP-prefix → fuzzy job-name).
  2. Renders the PDF server-side via WeasyPrint.
  3. Emails it via Resend to PM + always-CC (`jaymn.judd@mascigc.com`, `safety@mascigc.com`).
  4. For severe incidents (Medical / Restricted / Lost Time / Fatality / OSHA-recordable / work-stopped) it also CC's whatever is in `SEVERE_INCIDENT_CC` env.
  5. Skips silently with a log line if `RESEND_API_KEY` is missing — submit never crashes.
  - Routing source of truth: `/app/backend/pm_routing.py` (David Jewett: 15 jobs, Chris Wright: 8, Ramon Rodriguez: 4, Jaymn Judd: 1).
  - Admin endpoints: `GET /api/auto-email/routing-table` and `GET /api/auto-email/preview?project_number=…` for verification.
  - Admin Hub now shows a live "Auto-Email Routing" panel summarizing the table + Resend status badge.
- Backend: CRUD on `/api/inspections`, `/api/meetings`, `/api/jhas`, `/api/incidents`, `/api/daily-reports` + `/api/translate` + `/api/admin/{login,check}` + `/api/email-report` + `/api/auto-email/{preview,routing-table}`. POST + translate are public; GET list / GET single / DELETE / auto-email helpers are admin-only.
- 102/102 pytest backend (19 new auto-email-routing tests).
- All interactive elements have kebab-case `data-testid`.

## Backlog

**P0**
- _none active — Hub, 5 modules, auto-translate, map thumbnail, spell check, admin wall, logo fix all complete and tested_

**P1**
- **Distribution List** field on PDF footer (PM/GC/DOT recipients, who got a copy)
- **Severity-tier ops/GC fan-out** — populate `SEVERE_INCIDENT_CC` env with the addresses MASCI wants blasted on Medical+/OSHA-recordable incidents.
- Multi-user admin (per-account login, audit trail of who viewed/deleted)
- CSV / multi-report export for monthly compliance reports

**P2**
- Object storage (S3-compatible) for photos once typical record exceeds ~5 MB
- Aggregation `$size` on photos in list endpoints to skip pulling base64 bytes
- Trend dashboard: hazards-by-section, top recurring findings, near-miss → injury conversion
- Refactor: split `server.py` (~950+ lines) into `routes/{admin,inspections,meetings,jhas,incidents,daily_reports,translate,email}.py` with shared models module

## Next Action Items
1. **Get the Resend API key from MASCI ops** + verify the sender domain (e.g. `safety@mascigc.com`) at https://resend.com → Domains. Drop the key into `/app/backend/.env` → `RESEND_API_KEY=…`, optionally set `SENDER_EMAIL=safety@mascigc.com`, then `sudo supervisorctl restart backend`.
2. Test the live pipeline: submit one Site Inspection from `/inspect/new` with `project_number=24-06` and confirm David Jewett + Jaymn + safety@ all receive the PDF.
3. Decide if next module is **Equipment Pre-Op** or **DOT Vehicle Daily**.
4. Consider multi-user admin (with audit trail) once 2+ office staff need access.
