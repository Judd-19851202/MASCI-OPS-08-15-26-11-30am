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
- **Collections:** `inspections`, `meetings`, `jhas` (legacy — no UI), `job_hazard_plans` (PDF blobs), `trench_boxes`, `incidents`, `daily_reports`, `equipment_units`, `equipment_inspections`. Photos + signatures stored as base64 data URLs inline.
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

## What's Implemented (2026-04-27 · Phase 4 Crew Hub + P1 safety backlog)
- **Backend Phase 4 router live:** `/api/projects/{id}/activity`, `/api/me/activity`, `/api/me/notifications`, `/api/me/notifications/mark-all-read`, `/api/me/notifications/{id}/read`, `/api/projects/{id}/search`, `/api/users/directory`. Every Phase 2/3 write in `tools.py` now calls `log_activity()` + `process_mentions()` so the activity feed + @-mention notifications + Resend email fan-out all populate automatically.
- **6 Phase 4 frontend pieces shipped:**
  1. **`/app/me` My Stuff page** — "Hey!" inbox, 3 tabs (Mentions, My to-dos, Activity feed), mark-all-read, inline mark-one-read.
  2. **Activity feed on ProjectHome** — scrollable last-15 activity card below the scorecard.
  3. **@-mention autocomplete** (`MentionTextarea`) in MessageBoard composers (both new post + comments). Fetches `/api/users/directory` once, type `@` → dropdown of up to 6 matches, Enter/Tab to insert `@email@mascigc.com `.
  4. **Per-project search** (`ProjectSearch`) in ProjectHome header — instant results across messages, to-dos, docs, events (250 ms debounce).
  5. **NotificationBell in sidebar footer** — unread badge (9+ cap), 60s polling, dropdown with mark-one or mark-all-read, deep-link to My Stuff.
  6. **Distribution List widget** (`DistributionList`) on `/incidents/new` (section 07 Notifications) and `/daily/new` (section 11 Sign-Off). Chip input, email validation, backspace-to-pop. Stored on `incident.distribution_list` / `daily_report.distribution_list` (backend models accept list of strings, max 20). Included in the PDF footer and routable to auto-email.
- **Full Backup ZIP now archives the Crew Hub too.** `/api/exports/full-backup` appends 12 `crew_hub/*.json` files: `projects`, `users` (password_hash **redacted**), `project_members`, `messages`, `message_comments`, `todo_lists`, `todos`, `events`, `docs` (includes base64 file blobs), `hill_scopes`, `activity_log`, `notifications`. `backup_log.txt` shows a per-collection count + Crew Hub subtotal.
- **Verified end-to-end** via iteration 16 test report: 13/13 backend Pytest + 9/9 Playwright UI tests passing. Cross-user @mention delivery (safety@ posts mention → david@ sees notification) confirmed.

## What's Implemented (2026-04-27 · Phase 3.5 Scorecard Layout)
- **ProjectHome scorecard (2026-04-27):** Rebuilt `/app/projects/:id` as a Basecamp-style "everything at a glance" scorecard. One `GET /api/projects/{id}/scorecard` aggregate endpoint returns latest 3 messages, next 2 events, todo counts, 2 latest docs, top 3 hill scopes — one round trip instead of five.
  - **Hill Chart snapshot** at the top with inline mini-SVG + colored-dot legend (matches Basecamp IMG_4413 hero area).
  - **4-card grid** below: Message Board (red accent), To-dos (amber + progress bar), Schedule (emerald + day badges), Docs (blue + uploader info).
  - **Colored accent bars** per card; empty-state fallbacks on every card.
  - **Member avatar stack** in the project header (+N badge when >5 members).
  - **Secondary tiles row**: Hill Charts + Members with live counts.
- Verified end-to-end with seed data: 2 messages + 2 events + 3/5 todos + 1 doc + 3 hill scopes all render correctly in a 1600×1200 viewport.

## What's Implemented (2026-04-27 · Phase 2 + Phase 3 Crew Hub tools)
- **Message Board** (`/app/projects/:id/messages`) — post, list, view, threaded comments, delete. Author avatars + relative timestamps everywhere.
- **To-dos** (`/app/projects/:id/todos`) — multiple lists per project, inline add with assignee picker + due date, check-off with strikethrough + emerald badge, done items collapsed. `GET /api/me/todos` returns every open todo assigned to the current user across all projects.
- **Schedule** (`/app/projects/:id/schedule`) — day-grouped event list with start/end times, location, description. All-day toggle.
- **Docs & Files** (`/app/projects/:id/docs`) — 7 MASCI-specific categories (`Submittals`, `Plans & Specs`, `Safety`, `Daily Logs`, `Pictures & Drone`, `Locate Tickets`, `General`). Per-category filter tabs. 30 MB max per file. PDFs open inline, other types force download. `X-Content-Type-Options: nosniff` on every download.
- **Hill Charts** (`/app/projects/:id/hills`) — SVG hill with draggable dots (pointer + touch). Position 0–50 "figuring it out" / 50–100 "making it happen". Click a dot → edit dialog with slider + update note. Each scope gets a stable color.
- **7 new MongoDB collections** (`messages`, `message_comments`, `todo_lists`, `todos`, `events`, `docs`, `hill_scopes`) with proper indexes created on startup.
- **Authorization**: every tool endpoint requires project membership; destructive ops (edit/delete) additionally require author OR owner/admin role.
- **Verified end-to-end** with a 10-step curl chain (login → create → update → delete for all 5 tools) and a frontend smoke screenshot.

## What's Implemented (2026-04-27 · Phase 1 Crew Hub)
- **Per-user JWT auth (2026-04-27):** New `/app/*` section kicks off the Basecamp-style Crew Hub. Login at `/app/login` with email+password → httpOnly access_token (60 min) + refresh_token (7 days) cookies. `/app/change-password` enforced on first login. `/api/auth/me`, `/api/auth/logout`, `/api/auth/refresh` round out the flow. bcrypt password hashing, PyJWT HS256 tokens.
- **Seeded 5 initial users** (David Jewett, Chris Wright, Ramon Rodriguez, Jaymn Judd as `owner`; safety@mascigc.com as `admin`). Default temp password `Welcome2MASCI!` — all forced to change on first login.
- **Admin Users panel** at `/app/users` (owner/admin role-gated): invite new users with temp password, edit role (owner/admin/member), toggle active, reset password. Own-account disable is blocked.
- **31 MASCI jobs + HQ seeded as projects** on first boot. HQ auto-includes every active user. Regular projects have explicit membership managed at `/app/projects/:id/members`.
- **Sidebar layout** with pinned HQ + scrollable project list + Admin section + user footer (avatar + logout). Main content scrolls independently.
- **5 tool tiles per project** (Message Board, To-dos, Schedule, Docs & Files, Hill Charts) wired to placeholder routes — Phase 2 ships Message Board + To-dos first.
- **Coexistence with legacy admin:** the existing `X-Admin-Token` / `Happy123!` password flow continues to work for all `/admin/*` safety dashboards. New JWT users will replace it in Phase 4 after 30-day migration.
- **Backend lint + frontend lint clean, 160/160 existing backend tests still pass.**

## What's Implemented (2026-04-27 · Security Hardening)
  - **Rate limiting** on every public POST endpoint (`/inspections`, `/meetings`, `/jhas`, `/incidents`, `/daily-reports`, `/equipment-units`, `/equipment-inspections`, `/translate`) — per-IP, per-endpoint, default 30/hour, returns 429 on excess. In-memory bucket (single-instance backend, no Redis).
  - **Login throttle** on `/api/admin/login` — 10 failed attempts per IP per 15-minute window → 429 lockout. Successful login resets the counter for that IP.
  - **Admin HMAC secret moved to its own `ADMIN_HMAC_SECRET` env var** (was previously derived from `MONGO_URL` — fragile if Mongo URI ever leaked). Backend warns + auto-generates a per-process secret if the env var is unset.
  - **CORS locked down** — `allow_origins` reads from `CORS_ORIGINS` (now `https://mascidocs.com,https://www.mascidocs.com`) plus `CORS_ORIGIN_REGEX` for the Emergent preview wildcard. Falls back to permissive `*` only when env is unset, in which case `allow_credentials` is automatically dropped to remain CORS-spec compliant.
  - **PDF magic-byte validation** on every JHA Plan + trench-box tabulated-data upload. Files not starting with `%PDF-` are rejected at upload with HTTP 400. Downloads now force `Content-Type: application/pdf` + `X-Content-Type-Options: nosniff` regardless of stored MIME — even a maliciously-stored file cannot render as HTML/JS in the browser.
  - All 160 backend tests still pass after the lockdown. End-to-end verified: 11th login attempt → 429, 31st translate POST → 429, malformed PDF upload → 400 with magic-byte mismatch.
- **Site Posters hub on AdminHub (2026-04-27):** New `SitePostersPanel` lists every printable handout in one place — Crew Cheat Sheet, Trench Box QR, Job Hazard Plans QR. Each row has Preview + Print (`?autoprint=1` triggers the OS print dialog). A "Print All Posters" CTA opens `/admin/posters/print-all?autoprint=1` which stacks the 3 cards with `page-break-after: always` so a single Cmd+P → 3 letter-size sheets.
- **Job Hazard Plans QR Poster (2026-04-27):** Printable poster at `/admin/jha-plans/poster` — amber-themed, QR → `https://mascidocs.com/jha`, "What's in a Hazard Plan" cheat card, live job list. Goes inside every job trailer.
- **Refactored printable cards (2026-04-27):** `CheatSheetCard`, `TrenchBoxPosterCard`, `JhaPlansPosterCard` extracted to `/components/`. Standalone routes wrap them with toolbars; `AllPostersPrint` mounts all 3 with print page-break separators.
- **Trench Box QR Poster (2026-04-27):** Printable poster at `/admin/trench-boxes/poster`. QR → `https://mascidocs.com/trench-boxes`, soil-type quick reference, fleet snapshot.
- **JHA → Job Hazard Plans pivot (2026-04-27):** Old fillable JHA form removed (`NewJha.jsx`, `ViewJha.jsx`, `JhaDashboard.jsx` deleted). Replaced with read-only file-sharing hub at `/jha` and admin upload manager at `/admin/jha-plans`. Legacy URLs redirect cleanly.
- **Trench Box Tabulated Data (2026-04-27):** New OSHA reference at `/trench-boxes` with admin CRUD at `/admin/trench-boxes`.
- **Bilingual coverage extended:** Spanish dictionary expanded for `JhaPlansHub`, `TrenchBoxes`, new Hub tiles, `TrenchBoxPoster`, `JhaPlansPoster`, `AllPostersPrint`, and `SitePostersPanel`. Verified end-to-end via screenshots.
- **160/160 backend pytest passing**.

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
- ✅ **Distribution List** field on PDF footer — shipped 2026-04-27. Chip-input on Incident + Daily Report forms, list flows through to PDF + auto-email.
- ✅ **Severity-tier ops/GC fan-out** — `SEVERE_INCIDENT_CC` env var wired into `pm_routing.py`; production just needs the addresses set.
- Multi-user admin (per-account login, audit trail of who viewed/deleted) — legacy Safety Admin only. The Crew Hub side already has per-user JWT + roles.
- Resend Pro upgrade ($20/mo, 50,000 emails/month) when foreman volume exceeds free tier 100/day quota.

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
