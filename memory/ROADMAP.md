# MasciDocs HUB — Future Features Roadmap

This file tracks **parked features** the user wants to revisit later. Surface these proactively when starting a new session or when the user asks "what's next?"

---

## 🅿️ PARKED — Awaiting User Green Light

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
