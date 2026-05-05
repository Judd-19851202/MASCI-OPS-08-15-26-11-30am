# MasciDocs HUB — Future Features Roadmap

This file tracks **parked features** the user wants to revisit later. Surface these proactively when starting a new session or when the user asks "what's next?"

---

## 🅿️ PARKED — Awaiting User Green Light

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
