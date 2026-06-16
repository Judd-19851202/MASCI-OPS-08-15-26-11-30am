# TRACK 15.0 · ROLE DAILY REALITY MAP

**Phase 1 deliverable. What every MASCI role actually does on a normal working day, and where the platform supports (or fails) that work.**

This is a working map — used to drive Phases 2-12 reality certification. Each section lists the daily cadence + the platform surfaces that MUST work for the role to do their job through MASCI instead of around it.

---

## 1. Superintendent

**Morning (5:30-7:00 AM)**
- Open MASCI on iPad in the truck.
- Check yesterday's daily reports for their job.
- Open project team to confirm crew assignments.
- Review overnight notifications / incidents on their projects.

**During the day**
- Review safety meetings logged that morning.
- Open trench safety / excavation records if their job has digs.
- Submit Operational Daily Record (ODR) entries.
- Photograph progress, push photos to job library.
- Submit incident / near-miss if needed.

**Submits**: ODR, photos, incident reports.
**Reviews**: daily reports, safety meetings, JHAs, trench assets, notifications.
**Approves**: nothing directly — sup is read/submit, not approval.
**Searches for**: project number · employee name · equipment number.
**Needs alerts for**: open holds on their projects · safety incidents on their projects · overdue corrective actions.
**Needs PDFs for**: daily report (when leadership/insurance asks), incident report.
**Currently might do outside platform**: progress photos via text message, written notes for own records.

**Platform surfaces required**: PM portal / FL portal (depending on identity) · ODR Center · Trench Safety hub · Job photos · Notifications · Global search.

---

## 2. Foreman

**Morning (5:30-6:30 AM)**
- Sign in (or open public field flow).
- Pre-shift meeting → submit safety meeting form (English or Spanish input).
- Confirm crew is on the right project.
- Submit Pre-Op / DVIR on equipment.

**During the day**
- Submit JHA if task changes.
- Document trench/excavation if any.
- Upload progress photos.
- Submit incident/near-miss if anything happens.

**Submits**: safety meeting · daily report · JHA · pre-op · trench daily · incident · photos.
**Reviews**: own previous submissions; current project assignment.
**Searches for**: project number · own employee record.
**Needs alerts for**: assignment changes · safety holds.
**Needs PDFs for**: copy of submitted safety meeting / JHA for binder.
**Currently might do outside platform**: paper safety meeting forms; Spanish-only crews use paper because digital flow is English-only.

**Platform surfaces required**: FL Portal Dashboard · public submit flows · Spanish input recognition · bilingual operational record output.

---

## 3. PM (Project Manager / Co-PM)

**Morning (6:30-8:00 AM)**
- Open PM portal · review overnight notifications.
- Open Command Center → today's risk picture across all assigned projects.
- Scan Overloaded Crew tile (new) for staffing risk.

**During the day**
- Open individual projects to review daily reports, photos, incidents.
- Approve / route PO requests.
- Open safety meetings + JHAs to confirm compliance.
- Adjust project team (limited: cannot reassign PM/Co-PM).
- Open ODRs for cross-project view.

**Submits**: rarely — PMs read/approve, not submit.
**Reviews**: daily reports · incidents · meetings · JHAs · trench · photos · staffing.
**Approves**: PO requests · operational actions on their projects.
**Searches for**: project number · employee · equipment · supplier.
**Needs alerts for**: incidents · overdue tasks · staffing changes · PO approvals.
**Needs PDFs for**: weekly project recap; insurance/owner-rep export.
**Currently might do outside platform**: spreadsheet of crew counts; manual reminder list of pending POs.

**Platform surfaces required**: PM portal (Hub V2 + sidebar) · Command Center · Project Staffing (with Overloaded Crew) · ODR · Operations Actions · Notifications · Search.

---

## 4. Project Engineer / Project Assistant / Project Coordinator

**Morning**
- Open PM portal · review assigned projects (read-only view of PM scope).
- Check pending submittals or RFI tracking outside MASCI (these are not yet in-platform).

**During the day**
- Pull daily reports for billing/owner reports.
- Pull photos for owner update.
- Update project people roster if permitted.
- Export reports if applicable.

**Submits**: rarely.
**Reviews**: daily reports · photos · meetings · staffing.
**Searches for**: project · employee · supplier.
**Needs alerts for**: same as PM, scoped to assigned projects.
**Needs PDFs for**: client recap.
**Currently does outside platform**: RFIs, submittals, owner letters.

**Platform surfaces required**: PM portal sub-views · search · staffing readonly · PDFs.

---

## 5. Safety Manager / Safety Officer

**Morning (6:30-8:00 AM)**
- Open Safety portal · review incidents overnight.
- Open corrective actions queue.
- Review trench safety boxes / excavations.

**During the day**
- Investigate / close incidents.
- Review safety meetings · JHAs.
- Cross-reference field leadership records (write-ups linked to safety).
- Run document expirations for OSHA cards / training.

**Submits**: incident investigation notes · corrective actions.
**Reviews**: incidents · near misses · meetings · JHAs · trench · photos · expirations.
**Approves**: incident closure.
**Searches for**: incident · employee · project.
**Needs alerts for**: new incident · corrective action overdue · upcoming expirations.
**Needs PDFs for**: incident binder · OSHA log · trench inspection.
**Currently does outside platform**: nothing critical — Safety is the most platform-native role.

**Platform surfaces required**: Safety Hub V2 (now with Field Records & Plans tiles) · Safety SideNav V2 · `/safety-portal/*` deep routes.

---

## 6. HR Manager

**Morning**
- Open HR portal · review documents expiring.
- Review pending employee requests / time-off requests.

**During the day**
- Search employees for hire info, project history, training, certifications.
- Update employee record (legal name, preferred name, hire data).
- Generate compliance exports.

**Submits**: employee record updates.
**Reviews**: employee master · doc expirations · time-off requests · training.
**Approves**: time-off requests · employee record changes.
**Searches for**: employee · document · training · project.
**Needs alerts for**: expiring docs · pending time-off · expiring certs.
**Needs PDFs for**: I-9 binder · termination letter · certifications.
**Currently does outside platform**: confidential disciplinary letters; performance reviews; some payroll.

**Platform surfaces required**: HR Hub V2 · HR KPI strip · Document Expirations (now canonical `/document-expirations`) · search · Employee record.

---

## 7. Shop Manager

**Morning**
- Open Shop portal · review equipment status board.
- Review pending PM / service items.

**During the day**
- Open individual equipment profiles · service history · pre-ops · inspections.
- Reassign equipment between projects.
- Confirm trench box inspections.
- Run shop dispatch / utilization.

**Submits**: service records · status changes · transfers.
**Reviews**: equipment · pre-ops · transfers · service history · trench boxes.
**Approves**: equipment status changes · service completion.
**Searches for**: equipment number · part · supplier.
**Needs alerts for**: service due · failed pre-op · damaged equipment.
**Needs PDFs for**: service report · trench box certification.
**Currently does outside platform**: parts ordering · vendor calls.

**Platform surfaces required**: Shop portal · equipment master · pre-op center · trench safety · asset transfers · dispatch.

---

## 8. Dispatcher

**Morning**
- Open Dispatch portal · today's dispatch board.
- Check driver qualifications.
- Confirm fleet status.

**During the day**
- Move equipment between sites.
- Update driver / equipment assignments.
- Search for equipment to assign.
- Confirm DOT compliance.

**Submits**: dispatch assignments · transfers.
**Reviews**: dispatch board · fleet · driver qualifications · transfers.
**Approves**: dispatch assignments.
**Searches for**: equipment · driver · project.
**Needs alerts for**: failed pre-op · expired DOT · equipment unavailable.
**Needs PDFs for**: rarely — dispatch is real-time.
**Currently does outside platform**: phone calls to drivers; spreadsheet day-plan.

**Platform surfaces required**: Dispatch Hub V2 · Dispatch board · Fleet · Driver Qual · Command Map.

---

## 9. Admin / Super Admin

**Morning**
- Open Admin portal · review overnight system health.
- Review notifications · audit log.

**During the day**
- Manage users, permissions, project staffing.
- Review operational records · operations actions · safety records.
- Run global search across everything.
- Configure email routing · digest schedules.
- Monitor deploy / backup state.
- Review session forensics.

**Submits**: user changes · permission changes · system config.
**Reviews**: everything.
**Approves**: everything.
**Searches for**: anything.
**Needs alerts for**: system health · failed deploys · security events.
**Needs PDFs for**: compliance exports · audit log.
**Currently does outside platform**: rarely — admin is fully native.

**Platform surfaces required**: Admin V1 (now 32 sections including Operational Records + Operations Actions · D-A15 fix) · Admin V2 (audit-only · feature-flagged off) · Audit Log · System Health · Database · Sessions.

---

## 10. Field Leadership User

**Morning**
- Sign in to FL Portal.
- See assigned projects + Operations Actions tile.

**During the day**
- Submit daily report · safety meeting · JHA · pre-op · incident.
- Submit leadership records — recognition · write-up · verbal coaching · attendance · equipment checkout · evaluations · promotion · training deficiency (D-A16 fix added launcher card).
- View own submissions.

**Submits**: every operational + leadership form they touch.
**Reviews**: own past submissions; project context.
**Searches for**: project · employee.
**Needs alerts for**: assignment changes.
**Needs PDFs for**: occasional copy of own submission.
**Currently does outside platform**: text messages between supers about write-ups (this is the gap D-A16 closed).

**Platform surfaces required**: FL Portal Dashboard (now with Operational workflows + Leadership submissions cards) · public submit forms · operations actions tile.

---

## Cross-cutting requirements (every role)

- **Login parity**: Track 14 closed — bcrypt parity across portals, no in-memory secrets.
- **Notifications**: each role's notification bell surfaces work assigned to them.
- **Global search**: each role's search results respect scope (Wave B + Finalization shipped bilingual support).
- **Mobile / iPad**: every operational surface MUST work on iPad portrait + landscape; this is the field truth.
- **Spanish input**: foremen and field-leadership flows must accept Spanish free text; ES synonym search now covers 47 tokens.
- **Trust signals**: confirmation toasts, save indicators, error messages, audit footprints on every submit.

---

## What this map tells us about Track 15

- **Strong surfaces** (already proven this session): Admin V1 sidebar parity, PM Hub V2 + Project Staffing (incl. Overloaded Crew), Safety Hub V2 (Field Records & Plans), FL Portal Dashboard launchers, HR Hub no-shell-hop expirations.
- **Verification work for Track 15**: prove the chain — does a Foreman's daily report actually surface to the PM and Admin? Does an Incident go from Foreman → Safety → PM with notifications on each step? Does an HR doc expiration alert reach the HR manager? These are CROSS-ROLE chain certifications (Phase 12) — not new builds, just verifying that what we already have works under daily-operating pressure.
