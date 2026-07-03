# EXECUTIVE DEMO CHECKLIST

**Doctrine:** Every executive audience deserves a 15-minute walkthrough that showcases MASCI / ForgedOps at its best.
**Established:** Track 19.30 · 2026-07-03
**Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

---

## Target audiences

- MASCI leadership (Ownership · Operations · Safety · HR)
- Safety leadership (internal + external OSHA / regulatory)
- Operations leadership (VP Operations · Ops Managers)
- HR leadership (VP HR · HR Business Partners)
- PM leadership (VP Project Management · Senior PMs)
- Shop / Fleet leadership (VP Equipment · Fleet Manager · Shop Manager)
- Potential external customers (other heavy-civil contractors)
- Industry comparison audience (analysts benchmarking against HCSS · Procore · Raken · SafetyCulture · Samsara)

---

## Pre-demo checklist

- [ ] Preview environment reachable (`REACT_APP_BACKEND_URL` from `/app/frontend/.env`).
- [ ] Demo credentials ready and rotated (see `/app/memory/test_credentials.md`).
- [ ] Seed data reflects a realistic active project · active crews · recent incidents (not empty · not visibly demo-y).
- [ ] Preview banner acknowledged ("PREVIEW ENVIRONMENT · DB: MASCI_SAFETY_PREVIEW · DO NOT ENTER REAL OPERATIONAL DATA").
- [ ] Both English and Spanish tabs tested for the demo path.
- [ ] Mobile mirror (iPhone/iPad) available for field-first showcase.
- [ ] Notes on rollback available if executive asks "what if this breaks?"

---

## 15-minute demo sequence

### 1 · Login / Landing (60 seconds)
- Open `/` in a fresh incognito window.
- **Say:** "This is the public front door. Every crew member has this URL on a QR code and a bookmark. Field crew comes in through here; office roles sign in."
- Show: hero "One System. Every Crew. Every Job." · portal tiles · language toggle · Cheat Sheet.

### 2 · Field Daily Report (90 seconds)
- Navigate to `/daily/submit` on a mobile viewport.
- **Say:** "Foreman files a Daily Report at end of day, on his phone, one-handed, in bad light, sometimes in Spanish."
- Show: mobile-first form · photo attachment · autosave · Spanish toggle · submit → `/thank-you`.

### 3 · Equipment Pre-Op (60 seconds)
- Show a scan of a QR sticker on a piece of equipment leading to a pre-op.
- **Say:** "Operator scans the machine, walks it, marks defects. Defects cascade to Shop instantly."
- Show: defect capture · Shop `/shop/equipment` shows the OOS unit.

### 4 · DVIR (45 seconds)
- Show `/fleet/dvir/submit` from a driver's phone.
- **Say:** "Same primitive for drivers. DVIR feeds Fleet + Dispatch + Shop."
- Show: OOS on a unit propagates through the platform.

### 5 · Safety Meeting / Toolbox Talk (60 seconds)
- Log in as foreman and open `/meetings/new`.
- **Say:** "Every Toolbox Talk becomes a permanent training record with attendance signatures."
- Show: topic auto-load · attendance capture · PDF preview.

### 6 · Incident / Safety Case Workspace (2 minutes) — the "wow" moment
- Log in as Safety and open a real Case Workspace via `/safety/cases/:caseId`.
- **Say:** "This is the Incident Intelligence Engine. Every incident opens a full investigation workspace — evidence, findings, CAPAs, executive PDF, closeout — all in one command center."
- Show: 7-tab workspace · evidence preservation · Executive PDF export · timeline linkage to Employee 360.

### 7 · HR Employee Record — Employee 360° (2 minutes) — the second "wow"
- Log in as HR and open `/hr/employees/<empId>/profile`.
- **Say:** "One page. Every record for one employee. HR, Safety, Asset, and Corporate lanes. Auto-composed Employee Story. Compliance Brief PDF one click away."
- Show: 7-tab visual timeline · Employee Story · Next-Action chip · Compliance Brief PDF export.

### 8 · Bulk Historical Intake (60 seconds)
- Show `/hr/historical-records/batches` with an active Intake Session.
- **Say:** "Legacy paper files, digitized in batches. One session, one lane, one classify pass."
- Show: session provenance · queue routing · Employee 360 reflection.

### 9 · PM Portal (60 seconds)
- Log in as PM and show `PmHubV2`.
- **Say:** "PMs get every daily report, safety event, and asset movement on their projects."
- Show: sidebar V2 · project health · daily report roll-up.

### 10 · Safety Portal (45 seconds)
- Log in as Safety and show `SafetyHubV2`.
- **Say:** "Safety runs the platform from here. Cases · Meetings · Inspections · Executive Intelligence."
- Show: sidebar V2 · executive intelligence center.

### 11 · Shop / Fleet (45 seconds)
- Log in as Shop and show `ShopHubV2`.
- **Say:** "Shop sees Pre-Op failures, DVIR defects, and the recovery map. Repair complete ≠ safe to use — Dispatch verifies RTS."
- Show: Recovery Map · defect queue · Fuel/Lube · Asset Care.

### 12 · Executive Dashboard / Analytics (60 seconds)
- Log in as Admin and open `/admin` (Operations Control Center).
- **Say:** "This answers the one question executives ask: what requires attention right now?"
- Show: Sidebar V2 (6 domains) · Command Center · Governance Health · Executive Overview.

### 13 · PDFs / Emails / Audit Logs (30 seconds)
- Open `/admin/audit-log`.
- **Say:** "Every action is captured. Every email is routed through a single provider with a full audit ledger. Zero-drift by design."
- Show: unified merged timeline · `email_routing_audit_v2` entries.

### 14 · Bilingual Mode (30 seconds)
- Toggle to Spanish on any active surface.
- **Say:** "Full EN + ES coverage on every field-facing surface. Translation-on-submit doctrine keeps records auditable in canonical English."

### 15 · Mobile / iPad view (30 seconds)
- Resize the browser to iPhone width or open in an actual iPad.
- **Say:** "Field-first. Everything works on a phone in the truck, on an iPad on the jobsite, and on a desktop in the office."

---

## Q & A prep

- **"What does this cost to run?"** → Cloud MongoDB · single-node Kubernetes preview · Resend email · R2 storage · costs pilot-affordable.
- **"How do you compare to Procore/HCSS/Raken?"** → Reference `TRACK_19_27_INDUSTRY_COMPARISON.md`. MASCI wins on field-first, bilingual completeness, operational intelligence, and audit trail depth. Roadmapped: mobile-native shell, OSHA 300 auto-fill, wider integrations catalog.
- **"How do you protect against data loss?"** → Autosave · draft restore · SessionStatusOverlay · SHA-256 original preservation · R2 + base64 fallback.
- **"What if you need to roll back?"** → Every V2 canonical surface has a `_legacy` or `hub_v1` alias. Every migration has a documented reverse.
- **"How do you audit who did what?"** → Append-only audit ledgers on every mutation. `/admin/audit-log` for unified timeline.
- **"Is this OSHA-compliant?"** → Records support OSHA compliance workflows today (incident reports · training records · JHA · Site Inspections). Pre-canned OSHA 300 auto-fill is roadmapped.

## Post-demo actions

- Log the demo audience and questions asked in `/app/memory/EXECUTIVE_DEMO_LOG.md` (append-only monthly file).
- Route any product-shaping questions into the P2/P3 backlog per `PILOT_OBSERVATION_PLAYBOOK.md`.
- Update this checklist if any part of the demo felt weak.

## Owner

Executive demo readiness is owned by the main platform agent and the MASCI leadership sponsor.
