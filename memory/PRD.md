# MASCI Safety Hub — PRD

## 2026-04-28 — Bilingual sweep + Performance + Cleared-to-Operate (iter24, ALL GREEN)
- **ES→EN auto-translate wired into the 3 new shop modules**: `ShopSignoffCard.jsx` (sign-off notes), `PartsCatalog.jsx` save (PUT — part name + notes), and `PartsCatalog.jsx` parts-order email (additional_notes + item.name + item.notes). Mechanic types Spanish, DB + outgoing email both end up in English. Pattern matches the iter15-16 wire-up of the original 5 forms (Inspection, Meeting, Incident, Daily, Equipment Pre-Op) — confirmed end-to-end via iter24 pytest.
- **Spell-check verified**: `i18n.js._syncHtmlLang()` mirrors `lang=es|en` onto `<html lang>` on every toggle + persists via localStorage. Zero inputs override the html-level attribute, so browsers swap dictionaries automatically. Verified via Playwright (en → click ES → es → reload → still es → EN → en).
- **Photo-stripped list endpoints**: `GET /api/inspections`, `/api/incidents`, `/api/daily-reports`, `/api/equipment-inspections` migrated from cursor.find with photos:1 projection to MongoDB aggregation with `$size`. Photo bytes no longer travel for dashboard listings — 10-100x faster on records with multiple photos.
- **MongoDB indexes** ensured on every startup (idempotent `_create_safety_indexes()`): `equipment_inspections.created_at/inspection_date/equipment_unit/project_number/fail_count`, `inspections.created_at/inspection_date/project_number`, `daily_reports.created_at/report_date/project_number`, `incidents.created_at/incident_date/severity`, `meetings.created_at/meeting_date`, `equipment_parts.unit_number` (unique), `equipment_master.unit_number/category`. Log line: `[safety-indexes] ensured`.
- **"✓ CLEARED TO OPERATE" badge** on `/admin/equipment` + `/shop` Recent Inspections tab when `fail_count > 0 AND signoff_count >= fail_count`. Replaces the red FAIL badge once every flagged item is signed off — closes the visual loop. New `EquipmentInspectionSummary.signoff_count + cleared` fields computed server-side via aggregation. Bilingual: `LIBERADO PARA OPERAR`.
- **Validated by testing agent (iter24)**: 10/10 backend pytest (`test_iter24_bilingual_perf.py`) + Playwright bilingual sweep + cleared-badge UI verification + perf < 2.5s on all four list endpoints. Iter22 (15) + iter23 (19) regression suites still green = 44 backend tests total covering the iter22-24 work.

## 2026-04-28 — Shop Activity Feed + Equipment Parts Catalog (P0 complete)
- **Shop Activity Feed** — new `GET /api/shop/activity?limit=20` flattens `equipment_inspections.shop_signoffs[]` across the fleet, newest first. Mounted as a new tab on `/shop` (data-testid=shop-tab-activity → shop-activity-panel) and as a permanent panel on `/admin/equipment` (admin-activity-panel). Each row: mechanic name, action chip (Repaired / Tagged out / Parts ordered / No action), unit, item, optional notes, timestamp, deep-link into the inspection. Doubles as a credibility log for owners + insurance auditors.
- **Equipment Parts Catalog** — per-unit wearable parts so field mechanics can pull up a unit and order parts on the way to the PM service.
  - New `equipment_parts` MongoDB collection. Schema: `{unit_number (PK), filters[], cutting_edges[], wiper_blades[], tires[], other_wear_items[], updated_at, updated_by}`. Each row has `name, part_number, qty, notes` (+ `size` on wipers, `position/size/ply/brand` on tires).
  - **Endpoints** (require_shop_or_admin): `GET /api/equipment-parts` (list), `GET /api/equipment-parts/{unit}` (returns empty doc shape if not found), `PUT /api/equipment-parts/{unit}` (upsert), `POST /api/equipment-parts/order` (Resend email to parts office). Admin-only: `DELETE /api/equipment-parts/{unit}`, `GET /api/admin/equipment-parts/status`, `POST /api/admin/equipment-parts/upload` (.xlsx/.csv bulk upload). Defense-in-depth 400 on empty unit_number.
  - **`/shop` Parts Catalog tab**: searchable 589-unit fleet picker → 5-category editor (filters / cutting edges / wiper blades / tires / other) → "🛒 Add to Order List" → email order to parts office in one click. Mechanics + admins both edit (server-gated). Empty `unit_number` rows are filtered client-side to avoid trailing-slash 307→http Mixed-Content blocks.
  - **`/admin` EquipmentPartsPanel**: bulk upload `.xlsx/.csv` with columns `Unit Number | Category | Name | Part Number | Qty | Size | Position | Ply | Brand | Notes`. Aliases accepted (`filter` → `filters`, `wipers` → `wiper_blades`, etc.). Replaces ALL category lists for affected units (idempotent re-upload).
- **Bilingual**: ~60 new ES strings (Catálogo de Partes, Filtros, Cuchillas, Plumas Limpiaparabrisas, Llantas, Otros Artículos de Desgaste, Lista de Pedido, Enviar Pedido a Oficina de Partes, etc.).
- **Validated by testing agent (iter23)**: 19/19 backend pytest in `test_shop_activity_parts_iter23.py`, frontend EN+ES end-to-end (login → activity tab → parts tab → save → cart → email order via Resend with real `resend_id` returned). Iter22 regression 15/15 still green. One UI bug found (empty fleet rows triggered Mixed Content) — fixed in same iteration.

## 2026-04-28 — Shop Console + Pre-Op Sign-Off (P0 complete)
- **New 5th Hub tile "Shop"** (amber Wrench, `data-testid="hub-section-shop"`) on `/`. Click → `/shop/login` with its own password gate (`SHOP_PASSWORD=Nothappy123!`, separate from admin's `Happy123!`).
- **New `/shop` console** (`ShopHub.jsx`) — focused subset of `/admin/equipment`: KPI strip (Inspections on file / Units flagged FAIL / Shop sign-offs / Equipment in fleet) + 6 tabs: **Open Items** (default), **Activity Feed**, **Trends**, **Recent Inspections**, **Equipment List**, **Parts Catalog**. No incidents / dailies / meetings / inspections / settings — shop only sees shop stuff.
- **New `ShopSignoffCard.jsx`** — renders per FAIL line on `/admin/equipment/:id` and `/shop/equipment/:id`. Inputs: signed_by (mechanic name), action_taken (Repaired / Tagged out of service / Parts ordered / No action needed), optional notes. After sign-off, shows green "Shop signed off" stamp with name + timestamp + Reopen button.
- **Severity coloring on FAIL lines** in the View page: OUT OF SERVICE items get a red border + red OOS pill; NEEDS ATTENTION items get amber border + amber ATTN pill.
- **Admin retains global view**: `/admin/equipment` now also mounts `<OpenItemsPanel/>` + `<ShopActivityFeed/>` directly under the Trends panel.
- **Backend auth**: `POST /api/shop/login` mirrors `/admin/login` (HMAC token via ADMIN_HMAC_SECRET, namespaced by `b"shop:" + password`). New dependency `require_shop_or_admin` accepts X-Shop-Token OR X-Admin-Token. DELETE inspection stays admin-only.


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

## What's Implemented (2026-04-28 · MASCI HUB Logo + Tagline Refresh)
User-driven brand refresh: new logo art using a user-supplied red M with white swoosh icon, new tagline, dark-header-friendly backplate.
- **New logo lockup** (`/app/frontend/public/masci-full-lockup.png`): regenerated 2x via Gemini Nano Banana — first pass produced silver gradient backplate that clashed with the navy header; second pass replaced the backplate with solid #0f172a (slate-900) so it sits flush in the dark header. Verified live with full-page screenshot.
- **3 lockup variants + 3 mark variants** all regenerated. Idempotent generator at `/app/backend/scripts/generate_hub_logos.py` (always edits from `/app/frontend/public/_old_safety_lockups/`). Background-fix script at `/app/backend/scripts/fix_lockup_background.py`.
- **Tagline change globally:** "No Shortcuts · No Exceptions" → "Accountability · Adapt · Overcome" — updated in `companyInfo.js`, Hub homepage, Section landings (Safety/Field), Dashboard, ThankYou, FormPasswordGate, ViewInspection, ViewMeeting, MasciLogo alt text, ShareFormDialog poster HTML, CheatSheetCard, JhaPlansPosterCard, TrenchBoxPosterCard, AdminGuide, PDF render footer (`pdf_render.py`), and i18n Spanish dictionary.
- Old "No Shortcuts · No Exceptions" Spanish keys retained in `i18n.js` for backwards-compat with older PDF records.

## What's Implemented (2026-04-27 · MASCI Hub Rebrand + New Logo)
App rebranded from "MASCI Safety Hub" to **"MASCI Hub"** — reflects that it's a full operations platform, not just safety. Logo art was also regenerated via Gemini Nano Banana (`gemini-3.1-flash-image-preview`) — 3 lockup variants (dark bg, onblack, onlight) all now say **"MASCI HUB"** instead of "MASCI SAFETY" while preserving the compass icon, red M with checkmark, tagline, core values subtext, and overall composition. Originals archived to `/app/frontend/public/_old_safety_lockups/`. One-off script at `/app/backend/scripts/generate_hub_logos.py` (idempotent — always edits from the archived originals). Verified via MD5 — file on disk and server-served bytes match.
- **New homepage `/`** (`Hub.jsx`): 4 big section cards instead of 7 mixed tiles:
  - 🦺 **Safety** (red) → `/safety` — Site Inspections, Safety Meetings, Incident Reports, JHA Plans, Trench Box Data
  - 👷 **Field** (amber) → `/field` — Daily Reports, Equipment Pre-Op
  - 🏗️ **Projects** (emerald) → `/app` — Crew Hub (Basecamp clone), sign-in required
  - 🗄️ **Admin** (slate) → `/admin/login` — Office console
- **New `SafetySection.jsx`** (`/safety`) — 5 compliance-form tiles with red accent + "← MASCI Hub" back link.
- **New `FieldSection.jsx`** (`/field`) — 2 daily-ops tiles with amber accent + "← MASCI Hub" back link.
- Taglines + footers updated ("MASCI · Operations Platform").
- **Copy updates across codebase:** Login page, backup panels, cheat sheet, share-form dialog, Owner's Manual, PDF headers, email subject lines, i18n Spanish translations, backend fallback titles. The product is now "MASCI Hub" everywhere.
- **Owner's Manual (`/admin/guide`) updated** with a new "The 4 sections of MASCI Hub" section explaining who uses Safety / Field / Projects / Admin.

## What's Implemented (2026-04-27 · Owner's Manual + One-Stop Backup Hero)

## What's Implemented (2026-04-27 · Owner's Manual + One-Stop Backup Hero)
- **New `/admin/guide` page** — plain-English, print-friendly Owner's Manual. Answers "how do I run this?", "what's in the backup .zip?", "what do I do if data is missing after a deploy?", "what are the passwords?". Linked from a "📖 Guide" button in the admin header. Crews never see it. Print button in the header → print-optimized layout.
- **New `BackupHeroPanel`** at the very top of the Admin Hub — 2 giant buttons:
  - 🟥 **BACKUP EVERYTHING** — one click fires `/admin/backups/run-now`, emails the .zip to `BACKUP_EMAIL_TO`, AND downloads it locally in a single flow.
  - 🟩 **RESTORE FROM FILE** — file picker + a single confirm dialog (always merge mode — safe). No mode toggles, no REPLACE typing, no jargon.
- Below the hero panel the existing detailed panels (Compliance Export, Full Off-Site Backup, Stored Backups, Restore from Backup with merge/replace modes) remain as "advanced" controls for power users.
- Goal: the customer never has to touch anything except the 2 hero buttons. Everything else is decoration.

## What's Implemented (2026-04-27 · Data-Loss Defense-in-Depth)
Customer reported data loss after Emergent redeploy — in-container MongoDB and `/app/backend/backups/` are BOTH ephemeral per the platform. Built multiple defenses on top of the nightly backup:
- **Auto-email nightly backup** via Resend — every scheduled backup also attaches the .zip to an email sent to `BACKUP_EMAIL_TO` (default `jaymn.judd@mascigc.com`). Gives the customer a durable off-site copy even without Atlas.
- **Persistence-health banner** (`PersistenceHealthBanner`) at the top of `/admin`. Reads `GET /api/admin/persistence-check` which inspects `MONGO_URL` — localhost/127.* → RED "⚠ Your data will be deleted on the next redeploy" banner with Atlas migration callout + "Backup + email + download NOW" button. Atlas/external hostname → GREEN "Persistent database connected" banner.
- **Pre-deploy emergency backup button** — one-click flow that calls `/admin/backups/run-now`, emails the .zip, AND downloads it to the user's browser simultaneously. Prevents deploys-without-backup.
- Guidance given to user: MongoDB Atlas free-tier migration (6-step instructions delivered via chat).

## What's Implemented (2026-04-27 · Nightly On-Server Backups)
- **Daily scheduled backup** — `_backup_scheduler_loop` runs as a FastAPI startup task, ticks every 5 min, and fires the backup once per day at `BACKUP_HOUR_UTC` (default 02:00 UTC).
- **Stored on disk** at `BACKUPS_DIR` (default `/app/backend/backups`). Each run writes `MASCI_full_backup_YYYY-MM-DD_HHMMSSZ.zip` atomically via a `.zip.tmp` rename so a crashed backup can't produce a corrupt file.
- **Retention** — `BACKUP_RETENTION_DAYS` (default 14). Older zips auto-pruned after each successful run.
- **New admin endpoints:**
  - `GET /api/admin/backups` — list every stored backup + schedule config.
  - `GET /api/admin/backups/{filename}` — download one (strict filename regex — no path traversal).
  - `DELETE /api/admin/backups/{filename}` — delete one.
  - `POST /api/admin/backups/run-now` — trigger an immediate backup (same path as nightly).
- **Admin UI** — new `StoredBackupsPanel` on the Admin Hub, between "Full Off-Site Backup" and "Restore from Backup". Shows the schedule strip (hour, retention, dir, enabled) + every stored file with size/date + Download/Delete buttons + a `Run backup now` CTA.
- **Env vars:** `BACKUPS_DIR`, `BACKUP_RETENTION_DAYS`, `BACKUP_HOUR_UTC`, `DISABLE_BACKUP_SCHEDULER` (set to `1` to turn off).
- **Verified end-to-end via curl + screenshot**: scheduler logged on boot, `run-now` produced a 2.4 MB zip with 80 records, list/download/delete all work, admin panel renders.

## What's Implemented (2026-04-27 · Whole-System Backup & Restore)
- **Full backup ZIP now covers EVERYTHING on the system** — all 21 MongoDB collections. Adds `safety_aux/equipment_units.json`, `safety_aux/job_hazard_plans.json`, `safety_aux/trench_boxes.json` on top of the 6 safety kinds + 12 Crew Hub collections already being exported. Includes a `backup_manifest.json` (version "2") listing every collection covered so future agents can validate authenticity. Password hashes stay redacted from `crew_hub/users.json`.
- **Restore from Backup** — new `POST /api/exports/restore` endpoint + Admin Hub panel. Upload any `.zip` produced by "Download Full Backup" and the entire system is rebuilt.
  - **Merge mode (default, emerald):** upsert by `id` — existing rows overwritten with the backup's copy, new rows added, anything not in the backup left untouched. Safe to run repeatedly.
  - **Replace mode (destructive, red):** wipes each collection found in the zip first, then reinserts. Guarded by a REPLACE-typed confirmation dialog. Anything added since the backup is permanently lost.
  - **User-hash safeguard:** since the backup redacts `password_hash`, restore preserves the DB's existing hash in merge mode, or stamps the seed password `Welcome2MASCI!` with `must_change_password=True` in replace mode. **No account can ever be locked out by a restore.**
  - 500 MB upload ceiling, manifest validation (`backup_manifest.json` must be present), bad-zip + empty-upload fail fast with clear messages.
- **Verified end-to-end** via curl: backup → change password → add data → merge restore keeps current password + new data · replace restore wipes post-backup data and resets to seed password.

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

## 2026-04-28 — Equipment Master Fleet (P0 complete)
- Parsed `Equipment List.xlsx` (Louis sheet — master) → 589 units across 27 categories.
- Seed file: `/app/backend/data/equipment_master.json` (committed; auto-syncs to DB on startup if file count differs from `equipment_master` collection count).
- New endpoint: `GET /api/equipment-master[?category=...]` → `{ categories[], items[], grouped{}, count }`.
- Pre-Op fan-out: seed also populates legacy `equipment_units` (mapped via `preop_equipment_type`) so existing Pre-Op dropdown auto-fills with master fleet.
- New shared component: `/app/frontend/src/components/EquipmentCombo.jsx` — searchable, category-grouped picker with always-on free-text fallback (operators can still type custom equipment).
- Wired into:
  - `NewEquipmentInspection.jsx` — Unit # / Label field (auto-fills make/serial on pick).
  - `NewDailyReport.jsx` — Equipment Log → "Unit / Equipment" field (replaces free-text "Description / ID").

## 2026-04-28 — Suppliers + Employees Live (P0 complete)
- **234 MASCI employees** seeded from `EmployeeList 4-28-26.xls` (.xls binary parsed with xlrd) — names only, no PII like hire dates. Stored in `employees` collection. Available at `GET /api/employees`. Searchable via the existing `<EmployeeCombo>`.
- **135 MASCI suppliers / subcontractors** seeded from `Supplier & Vendors.xlsx`. Stored in `suppliers`. Available at `GET /api/suppliers`. New `<SupplierCombo>` component (mirrors EquipmentCombo / EmployeeCombo) with searchable list + free-text fallback for one-off vendors.
- Wired into Daily Report:
  - **Section 05 Subcontractors on Site** — Company → SupplierCombo, Foreman → EmployeeCombo.
  - **Section 08 Material Deliveries** — Supplier → SupplierCombo (Ticket Photo uploader unchanged).
- Admin upload tooling on `/admin` (mirrors EquipmentMasterPanel / EmployeeMasterPanel):
  - **MASCI Supplier & Subcontractor List** panel — `.xlsx` or `.csv`, column 1 = company name. Auto-skips dividers ("MASCI", "D-MAC", "NOT LISTED ADD TO NOTES") and header rows.
- Idempotent startup seed for both employees + suppliers (only runs when collection is empty — won't overwrite admin uploads).
- ES translations added: "Type or pick a supplier…", "Browse supplier list", "Search by company name…", "Supplier list not uploaded yet — type freely.", "Tip: type freely for one-off vendors not in the list.". RepeatBlock + DR field configs cleaned of hardcoded English placeholder fallbacks so all combos use their `useT()` defaults in ES mode.
- Validation (testing agent iteration 21): 6/6 backend pytest, frontend EN+ES end-to-end ('Cemex' picker → fills company; 'Alec' → fills foreman; ES placeholders confirmed via attribute). Equipment-fleet 589 + Employees 234 regression intact.


### Daily Report
- **Auto-generated Report #** — `DR-YYYYMMDD-NNN`. Fetched on form mount via new endpoint `GET /api/daily-reports/next-number`. Editable by user if needed.
- **Section 04 "MASCI Crews on Site" rebuilt** — now a row-table per crew member with Name (EmployeeCombo) + Trade + Start Time + Lunch Minutes + Stop Time → auto-calculated `hours` field (handles overnight shifts) + a sticky "Total crew hours today" footer bar. PDF prints the same table with totals row.
- **Section 08 Material Deliveries** — added per-row `ticket_photos` uploader; PDF inlines the ticket photos under the materials table.
- **Photo upload (used everywhere)** — split into two buttons: "From Gallery" (no `capture` attr → iOS shows Library/Take Photo/Choose File sheet) and "Take Photo" (forces camera). Removed the camera-only behavior on iOS.
- **GPS reliability** — `getCurrentPosition` now retries with low-accuracy + cached fix on timeout; iOS PositionError codes are mapped to actionable user messages (e.g. "Location permission denied. Tap AA in Safari → Website Settings → Location → Allow").

### Cross-form upgrades
- **EmployeeCombo** (`/app/frontend/src/components/EmployeeCombo.jsx`) — searchable picker fed by `GET /api/employees`. Drop-in component: free-text fallback always works.
- Added EmployeeCombo to **Site Inspection** (operator), **Incident** (reported_by, supervisor_name, witness names), **Equipment Pre-Op** (operator), **Daily Report** (every crew name).

### Backend
- Added `GET /api/employees`, `GET /api/admin/employees/status`, `POST /api/admin/employees/upload` (.xlsx or .csv with column "Name" + optional Employee ID/Trade/Role/Crew/Email/Phone), `POST /api/admin/employees`, `DELETE /api/admin/employees/{id}`.
- Added `GET /api/daily-reports/next-number?date=` — registered BEFORE `/daily-reports/{report_id}` so FastAPI route ordering doesn't swallow it.
- `pdf_render._render_daily` field mapping fixed (was using stale `crews/materials.name/qty` keys); now matches actual schema and prints crew totals + ticket photos.

### Admin UI
- New `EmployeeMasterPanel` on `/admin` (mounted directly under `EquipmentMasterPanel`) — counter, last-updated timestamp, single "PICK FILE" button to upload roster.

## 2026-04-28 — Admin Upload Tool for Equipment Fleet
- New module `/app/backend/equipment_parser.py` — shared `parse_equipment_xlsx(bytes, sheet="Louis")` used by both startup seed and the admin upload endpoint (single source of truth for parsing rules).
- New endpoints (admin-only):
  - `GET /api/admin/equipment-master/status` → `{ count, categories{}, last_updated, seed_file }`.
  - `POST /api/admin/equipment-master/upload` → multipart file upload; rejects non-xlsx (400); backs up prior seed JSON to `equipment_master.<timestamp>.bak.json`; rewrites `data/equipment_master.json`; replaces both `equipment_master` and fans out into `equipment_units`.
- New frontend component: `/app/frontend/src/components/EquipmentMasterPanel.jsx` — mounted on `/admin` directly under the Backup hero. Shows total units, last-updated stamp, top-6 category chips, "Pick .xlsx" upload button + refresh button.
- AdminGuide (`/admin/guide`) gained a new "Updating the equipment fleet" section.
- Added `openpyxl==3.1.5` to `backend/requirements.txt`.
- Validated by testing agent: 9/9 backend pytest passes, 3/3 frontend smoke flows verified end-to-end (panel renders, Pre-Op combo filters + auto-fills make, Daily Report combo opens, upload replaces collection + JSON + creates backup, auth gates work).


