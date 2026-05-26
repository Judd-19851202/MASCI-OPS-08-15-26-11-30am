# MasciDocs HUB — Future Features Roadmap

This file tracks **parked features** the user wants to revisit later. Surface these proactively when starting a new session or when the user asks "what's next?"

---

## ✅ RESOLVED — Atlas Tier Capacity (iter437 · 2026-05-26)

**Outcome:** Cluster upgraded M0 → M10. Restore drill completed end-to-end. Currently at **7.6% utilization** (782 MB / 10 240 MB). Operational runway ≈ 12 months at observed +25 MB/day growth.

**What's in place:**
- ✅ Cluster-capacity probe (`/api/cluster/capacity`) + frontend banner (`<ClusterCapacityBanner />`)
- ✅ Atlas alerts runbook ready for operator configuration: `/app/memory/ATLAS_ALERTS_RUNBOOK.md`
- ✅ Restore-drill script idempotent and proven: `/app/backend/tools/restore_drill.py`
- ✅ Full certification at `/app/memory/PHASE_RESTORE_DRILL_ATLAS_BLOCKER.md` (CERTIFIED PASS)

**Open items for operator (low priority, documented):**
- 🟡 Configure Atlas alerts (75% / 90% storage, CPU, connection spikes) per `ATLAS_ALERTS_RUNBOOK.md`
- 🟡 Review `idempotency_keys` (3.3 MB/doc — abnormally large; likely storing request bodies)
- 🟡 Decide on lifecycle policies (TTL indexes for `usage_events`, `health_monitor_runs`, photo migration) — list in certification report § 12

---

## 🅿️ PARKED — Awaiting User Green Light

### 🔐 Site-Wide Employee Login Gate
- **Status**: PARKED by user on 2026-05-07 — *"we will do this soon just not today"*
- **Priority when unparked**: P1 (security + audit trail + usage analytics)
- **Why parked**: Other priorities first. User wants this in the very near future.
- **Reminder trigger**: Surface during any conversation about user audit trail, security hardening, employee accountability, or "what should we tackle next?"

**Spec Summary (already mapped out in detail — ready to execute on user's go):**

The gate: every visitor to mascidocs.com hits a login screen first. Only after entering their employee credentials do they see any HUB content. PM/Shop/Admin/Safety-Forms portals stay as their own gates inside.

**Eight components to build (~14 hours / 1.5–2 days total):**
1. Bulk employee import from spreadsheet (name, email/ID, password, active flag) — ~1 hr
2. Site-wide login gate component wrapping the whole app — ~3 hr
3. `/api/field/login` endpoint (issues 30-day signed cookie token) — ~1 hr
4. Usage tracking: every page view + form submission stamps who/when/what — ~3 hr
5. Termination toggle: admin button → revokes all tokens instantly + blocks future logins — ~1 hr
6. Self-service password reset via Resend — ~2 hr
7. (Optional) First-time forced password change — ~1 hr
8. Per-employee record stamping: every form auto-tags `submitted_by_employee_id` — ~2 hr

**Smart additions I'd build alongside (free since we're in there):**
- Multi-device tracking (flag password sharing — same login from 3+ IPs in a week)
- "Stay logged in 30 days" on mobile (so crews don't type passwords at 6am)
- Biometric unlock prompt on iOS (Face ID via passkeys)
- Admin "Recent Activity" live stream
- Per-employee productivity stats (reports filed per month)
- Auto-flag accounts inactive for 90+ days

**Recommended phased rollout:**
- 🥇 Phase 1 (Day 1): Hard gate + employee import + admin termination toggle — ~6–10 hrs
- 🥈 Phase 2: Usage tracking + per-record stamping + admin activity dashboard — ~½ day
- 🥉 Phase 3: Self-service password reset + 30-day mobile sessions — ~½ day
- 🎖️ Phase 4: Productivity dashboard + multi-device alerts — ~½ day, optional

**Open decisions when unparked:**
- a) Identifier: email / employee ID / **either (recommended)**
- b) Force password change on first MASCI HUB login: yes / no / optional
- c) Pages staying public (no login): `/legal/terms`, `/legal/privacy`, `/company-info`?
- d) Subcontractor share-links: keep one-time signed URLs or also gate behind login?
- e) Phase 1 scope: just gate / gate + record stamping / full Phase 1+2
- f) Build a hardcoded "super-owner" backdoor login (strongly recommend yes — prevents lockout if deploy goes sideways)

**Tech approach:**
- Reuses existing JWT/signed-token pattern from PM/Admin/Shop auth (no new dependencies)
- New collection: `field_user_sessions` for active tokens
- New collection: `audit_log` for per-employee activity (or extend existing `activity_log`)
- Uses existing Resend integration for password reset emails
- Uses existing brute-force protection / rate limiting (already in production)

**Key gotchas to flag at build time:**
- Bootstrap risk: very first deploy with login required → user could lock self out → MUST ship super-owner backdoor first
- Existing 8-char paystub passwords are weak → recommend forced upgrade to 10+ chars on first MASCI HUB login
- Password sharing is real in construction → audit trail matters more than prevention
- Foremen at 6am with cold hands: 30-day sessions + Face ID is non-negotiable for adoption

**Call `integration_playbook_expert_v2` BEFORE writing any auth code** (per system policy — auth is always an integration).

---

### 🚛 Motive Fleet Watcher Integration
- **Status**: PARKED by user on 2026-02 — *"keep it on the list of things to add in the future"*
- **Priority when unparked**: P1 (huge ROI — Motive already knows almost everything crews currently type by hand)
- **Why parked**: User wants other priorities first; Motive can wait.
- **Reminder trigger**: Surface during any conversation about reducing Pre-Op friction, fleet visibility, incident documentation, or "what should we add next?"

**Spec Summary (already mapped out — ready to scope on user's go):**

Top 5 integrations ranked by MASCI impact:
1. 🥇 **Equipment Pre-Op auto-fill** — odometer, engine hours, last DVIR, fault codes (DTCs), last 24-hr driver auto-pulled from Motive when operator picks unit. Cuts Pre-Op time from ~8 min → ~3 min.
2. 🥈 **Equipment Master auto-sync** — nightly pull of Motive vehicle list into MASCI's `equipment_master`. New units appear in dropdowns automatically. Decommissioned units auto-flagged inactive. Ends manual roster maintenance forever.
3. 🥉 **GPS verification on Daily Reports + Site Inspections** — cross-reference MASCI form GPS with Motive trip log. Auto-fill arrival/departure/hours-on-site. Flag phantom reports where unit was in yard but report claims work was done. Audit gold.
4. 🏅 **Dashcam clips auto-attached to Incident Reports** — when an incident is filed for a unit, auto-pull the 60-sec dashcam clip from Motive bracketing the incident time. Embed in PDF. Insurance/legal killer feature.
5. 🎖️ **Live fleet map on Admin Dashboard** — every unit pinned with status (active/idle/off/OOS). Click pin → today's daily report status, open Pre-Op fails, current driver, today's job site.

Mid-tier opportunities:
- 6. Fault code → Shop ticket (webhook-driven check-engine alerts auto-create Needs-Attention queue items)
- 7. HOS clock on Pre-Op (CDL drivers see remaining drive time)
- 8. Trip log → Daily Report pre-fill (miles driven, hours run, idle time)
- 9. Geofence arrival → auto-Slack/email PM
- 10. Per-driver safety scoring (harsh braking, speeding events)
- 11. Monthly fuel/idle abuse reports

**Tech approach (already designed):**
- Base URL: `api.gomotive.com` (formerly KeepTruckin/api.keeptruckin.com)
- Auth: API key from Motive dashboard → Settings → Integrations → API → Generate Key (free with existing Motive subscription)
- Rate limit: 1000 req/min — plenty
- Webhooks supported (real-time safety events / DVIR submissions)
- New module: `/app/backend/integrations/motive.py`
- Mongo cache collections: `motive_vehicles`, `motive_drivers`, `motive_trips`, `motive_events`
- Single env var: `MOTIVE_API_KEY`
- Nightly background job + on-demand calls + webhook receiver

**Phase options when unparked:**
- 🐢 **Phase 1a (1 day)**: Equipment master sync only
- 🚙 **Phase 1b (2–3 days)**: Sync + Pre-Op auto-fill
- 🚀 **Phase 1c (~1 week)**: Sync + Pre-Op + GPS verification + live fleet map
- 🛡️ **Phase 2**: Dashcam clips on incidents (killer for insurance/legal)
- 🔔 **Phase 3**: Webhook-driven fault codes, geofence alerts, safety scoring

**Open questions when unparked:**
- Top 3 features to ship in Phase 1
- Approximate fleet size (informs polling vs webhook strategy)
- Phase 1 scope choice

---

### 📷 Photo-First Daily Report (Gallery Upload + AI Draft)
- **Status**: PARKED by user on 2026-02 — *"Keep this for later rollout after crews learn the system... Will wait, remind me later."*
- **Priority when unparked**: P1 (high ROI, ~2–3 hour build)
- **Why parked**: User wants crews to fully adopt current system before adding AI-driven workflows.
- **Reminder trigger**: Bring up after crews show solid adoption of Daily Reports / Safety Forms (~1–3 months post-deploy), or whenever user asks for new feature ideas.

**Spec Summary (already discussed and approved in concept):**
1. Super takes 8–15 photos throughout the day on phone camera (existing habit).
2. End-of-day, opens Daily Report → "📷 Upload Photos from Gallery" button.
3. Multi-select photos from camera roll.
4. AI (Gemini 3 Vision) analyzes ALL photos and generates:
   - **Top of report**: Synthesized narrative (work performed, crew, equipment, conditions).
   - **Bottom of report**: Per-photo captions as photo log appendix.
   - Photos embedded inline in the PDF.
5. Super edits, adds hours/quantities, signs, submits.

**Smart features approved in concept:**
- Auto-sort photos by EXIF timestamp (chronological narrative).
- GPS verification (flag photos taken outside project geo-fence).
- Date filter (default to "today's photos only" in picker).
- Photo dedup (AI mentions multi-angle shots once).
- Per-photo annotation field (super can tag a photo before AI runs).
- Bilingual draft (Spanish-first if super's UI language is ES, auto-translate to EN on submit using existing `translateUserInput` pipeline).
- Cost: ~$0.03 per report (~$45/mo at 50 reports/day).

**Open decisions when unparked:**
- Output style: per-photo / synthesized / both (recommended: both).
- Source: gallery only vs gallery + in-app camera (recommended: both).
- Required vs optional on daily reports.
- Where it lives: integrated into existing Daily Report form vs separate "📷 Photo Report" entry point.

---

## 🚀 OTHER BRAINSTORMED FEATURES (Feb 2026 ideation session)

Not parked, just queued for user prioritization later:

### Crew Quality-of-Life
- **QR Code Equipment Tagging** — Scan QR sticker to auto-fill Issuance/Return forms with item + serial #. (~1-day build, very high crew adoption)
- **Voice-to-Text on Notes Fields** — Mic button on every notes field; Spanish supported via existing translation pipe.

### Alerts / Compliance
- **PPE Expiration & Inspection Reminders** — Auto-pings 30 days before harness/extinguisher/fall-protection expirations. Prevents OSHA fines.
- **Training Renewal Auto-Reminders** — 30/60/90 day countdown; weekly Monday digest to Safety Officer.
- **Weather-Triggered Alerts** — NWS forecast by project GPS; heat index >95°F or lightning <10mi triggers stop-work alert to foreman.

### Admin / Office
- **Equipment Cost Dashboard** — "We charged back $X this quarter for lost gear, 60% hard hats."
- **PM Weekly Digest Email** *(P2 from PRD)* — Monday 7am rollup of QA/QC, Daily Reports, Equipment fails by PM.
- **Crew Roster Sync / Termination Auto-Charge** — Flag unreturned gear on termination, route to HR for final-paycheck deduction.

### Bigger Bets
- **Job Site Map View** — Map pins for all active projects → click for daily status snapshot.
- **Crew Self-Service Portal** — Phone-friendly login showing each employee's PPE, training, renewals, signed forms.
- **Subcontractor Compliance Vault** — Sub uploads COI/W-9/safety plan once; auto-blocks expired subs from new jobs.

---

## ✅ EXISTING ROADMAP (from PRD)

- **P1**: Auto-suggest parts on Pre-Op FAIL (blocked on parts upload spreadsheet)
- **P2**: New Hire Onboarding flow (currently "Coming Soon" on Training Hub)
- **P2**: S3 Object Storage Migration (move local disk files/videos to S3)
- **P2**: PM Weekly Digest Email
- **P3**: Admin Bulk PDF Export (zip download for monthly archiving)

---

*Last updated: Feb 2026*
