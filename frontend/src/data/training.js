// MASCI Training Hub — lesson library.
//
// Every lesson is a self-contained record. The Training Hub pages render
// them as stacked cards with an optional video embed above each one. Video
// URLs are stored per-slug in the `training_videos` collection on the
// backend and pulled on page load; lessons with no video saved just show
// the written walk-through.
//
// To add a lesson: append a new object to the track array below with a
// unique `slug`, pick icons from lucide-react, and keep the tone plain
// and direct — these are construction crews reading on a phone, not
// software engineers reading a doc.
//
// Spanish translations for every lesson body live in training_es.js and are
// merged at the bottom of this module via mergeTranslations(). Lessons
// expose `title_es`, `why_es`, `steps_es`, `tips_es`, `cheatSheet_es` fields
// which TrainingTrack.jsx picks up automatically when the ES toggle is on.

import { LESSON_TRANSLATIONS_ES } from "./training_es";

export const TRACKS = {
  field: {
    slug: "field",
    title: "Field Crew Training",
    title_es: "Capacitación de Cuadrilla de Campo",
    blurb: "Everything the crew on the ground needs — from scanning the QR at the trailer to submitting a Daily Report after the shift.",
    blurb_es: "Todo lo que la cuadrilla en campo necesita — desde escanear el QR en el tráiler hasta enviar el Reporte Diario después del turno.",
    accent: "amber",
    audience: "public",
    icon: "HardHat",
  },
  shop: {
    slug: "shop",
    title: "Shop / Mechanic Training",
    title_es: "Capacitación del Taller / Mecánico",
    blurb: "How the shop clears failed Pre-Ops, tracks parts, and keeps the fleet running.",
    blurb_es: "Cómo el taller libera Pre-Ops fallados, rastrea partes y mantiene la flota funcionando.",
    accent: "slate",
    audience: "shop",
    icon: "Wrench",
  },
  pm: {
    slug: "pm",
    title: "PM / Project Management Training",
    title_es: "Capacitación del Gerente de Proyectos",
    blurb: "Day-to-day management: master lists, email routing, import/export, archive recovery — everything a PM touches without stepping on the Admin's backup controls.",
    blurb_es: "Gestión diaria: listas maestras, ruteo de correos, importar/exportar, archivo — todo lo que toca un Gerente sin tocar los controles de respaldo del Admin.",
    accent: "amber",
    audience: "pm",
    icon: "Briefcase",
  },
  admin: {
    slug: "admin",
    title: "Admin / Owner Training",
    title_es: "Capacitación del Administrador / Dueño",
    blurb: "The full platform overview, system-recovery tools, and the exact backup workflow that protects every record. For owners and the person who holds the admin password.",
    blurb_es: "Panorama completo de la plataforma, herramientas de recuperación y el flujo exacto de respaldo. Para dueños y quien tenga la contraseña de admin.",
    accent: "red",
    audience: "admin",
    icon: "ShieldCheck",
  },
};

// ============================================================
// FIELD CREW LESSONS (7)
// ============================================================
const FIELD_LESSONS = [
  {
    slug: "field-01-hub-navigation",
    track: "field",
    order: 1,
    title: "Lesson 1 — Navigating the MASCI Hub",
    why: "Everything starts here. If you can find the Hub on your phone, you can file any form the company needs in under 2 minutes.",
    duration: "~4 min",
    steps: [
      "Point your phone camera at the QR code posted inside the site trailer — the MASCI Hub opens in your browser automatically. No app to install, no login for Field forms.",
      "On the Hub home page you'll see 7 tiles: Field, Safety, Projects, QA/QC (coming soon), PM Portal, Shop, and Admin. Field and Safety are the two you'll use every day.",
      "Tap the language toggle in the top-right to switch between EN and ES — your choice is remembered on this phone.",
      "Tap 'Company Info' in the top-right to see MASCI's office address and phone numbers if you need to call HQ from the field.",
      "Tap 'Add to Home Screen' in your browser menu once — after that the Hub opens like a real app with one tap.",
    ],
    tips: [
      "If GPS doesn't grab on the first try, type the address in the Location field instead — same result.",
      "The Hub works offline for reading, but submitting a form needs a signal — save and retry when you get bars.",
    ],
    cheatSheet: [
      "Scan the QR → Hub opens → Pick Field or Safety → Fill → Sign → Submit.",
      "Language toggle is top-right. Company Info is next to it.",
    ],
  },
  {
    slug: "field-02-daily-report",
    track: "field",
    order: 2,
    title: "Lesson 2 — Daily Reports",
    why: "The Daily Report is the company's memory for what happened today. No Daily Report = no proof of crew time, material deliveries, subs on site, equipment used, or progress made. It protects you and it protects the company in a dispute.",
    duration: "~8 min",
    steps: [
      "From the Hub, tap Field → Daily Reports → 'File First Report' (or 'New Report').",
      "Pick your MASCI Job from the picker at the top — project number, name, location, and client all auto-fill. Pick 'Custom Job' only if your job isn't in the list yet (rare).",
      "Tap 'Use GPS' to auto-fill Location. The weather auto-loads from today's forecast for that lat/long. If GPS fails, type the address.",
      "General Information: answer Yes/No on Schedule Delays, Weather Impact, Accidents, Injuries. If ANY answer is Yes, a red Safety Escalation box appears — fill that out completely or you can't submit.",
      "MASCI Crews on Site: tap 'Add Crew Member'. The roster dropdown is pre-loaded — type a name and pick. Enter Start / Stop times. Lunch auto-deducts 30 min. Hours auto-calculate.",
      "Subcontractors on Site: same pattern — who, how many workers, how many hours, what they did.",
      "Site Visitors, Equipment Log, Material Deliveries, Activity / Production Log: fill whatever applies today. Skip sections that don't apply.",
      "Photos: minimum 6 required. Take them as you walk the site — start, progress, any issues, end.",
      "Prepared By + Superintendent sign at the bottom. Tap 'Submit Daily Report'. You'll see the Thank-You screen.",
    ],
    tips: [
      "If an accident or injury was reported, the app BLOCKS submission until (1) Safety was notified AND (2) an Incident Report was filed. Don't try to shortcut this — fill the Incident Report first, then come back.",
      "Hit 'Save Draft' at any point if a crew meeting interrupts you — your progress persists on this phone.",
      "Spanish-speaking crews: set the language to ES, fill in Spanish. The app auto-translates to English before saving to the office.",
    ],
    cheatSheet: [
      "6 photos minimum. GPS + weather are automatic.",
      "If Yes on Accident/Injury → Incident Report FIRST, then Daily Report.",
      "Prepared By + Superintendent both sign.",
    ],
  },
  {
    slug: "field-03-equipment-preop",
    track: "field",
    order: 3,
    title: "Lesson 3 — Equipment Pre-Op Inspection",
    why: "OSHA 1926 requires a daily walk-around before you operate heavy equipment. The Pre-Op protects you from getting hurt by a known bad machine and protects the company from running a unit into the ground. A FAIL here tags the unit OUT OF SERVICE until the shop clears it.",
    duration: "~6 min",
    steps: [
      "Hub → Field → Equipment Pre-Op.",
      "Pick your Job and Equipment Type. Search the 'Saved units' list for the unit you're operating — makes, models, and serials auto-fill.",
      "Enter Hour Meter OR Odometer (one required). Enter your full name.",
      "Walk the unit. For every checklist item, tap Pass, Fail, or N/A. A FAIL requires a description (min 10 characters) AND a photo of the defect.",
      "Major-safety failures (brakes, steering, seat belt, ROPS, horn) trigger the red 'STOP — Major Safety Failure' modal. The unit is marked OUT OF SERVICE — do NOT operate. Tell your supervisor, notify the shop, tag the machine out.",
      "Critical-fluid failures (no oil, no coolant, leaking hydraulic fluid) block the submission until the fluid is refilled and the item flipped from Fail to Pass.",
      "Add deficiency notes, corrective actions, and equipment photos at the bottom.",
      "Operator Sign-Off: read the certification, sign, tap 'Submit Inspection'.",
    ],
    tips: [
      "Do the Pre-Op with the engine off first (visual walk-around), then start it and check gauges, brakes, and hydraulics.",
      "If you skip an item as N/A, the app accepts it — don't lie on a Pass. The shop reviews every FAIL and will see a pattern.",
      "Once the shop signs off a FAIL, the unit is CLEARED TO OPERATE and you'll see it on the equipment dashboard.",
    ],
    cheatSheet: [
      "Engine off → walk around → engine on → check fluids & gauges.",
      "FAIL = unit out of service + photo required.",
      "Major safety items = STOP, do not operate.",
    ],
  },
  {
    slug: "field-04-site-inspection",
    track: "field",
    order: 4,
    title: "Lesson 4 — Site Safety Inspection",
    why: "Daily and weekly walk-throughs to catch hazards before they hurt someone. Graded automatically so you can see at a glance if your site is passing OSHA.",
    duration: "~5 min",
    steps: [
      "Hub → Safety → Site Inspections → New Inspection.",
      "Fill project info, pick Day or Night operation, enter Inspector + Foreman names.",
      "List the crew and any subs onsite. Note weather and what the crew is working on today.",
      "Walk the site. Grade PPE Compliance, Site Hazards, MOT, Fall Protection, Electrical, Housekeeping, Fire, Heat/Cold Stress as Pass / Fail / N/A. Live Grade % updates as you go.",
      "Photo any Fail. Note Stop Work issued, Corrected On Site, Responsible Party.",
      "Inspector + Foreman sign. Submit.",
    ],
    tips: [
      "Weekly inspections are more thorough than daily. Use the same form — just mark more items.",
      "A Live Grade below 80% should trigger a stand-down with the crew.",
    ],
    cheatSheet: [
      "Pass/Fail each category. Photo every Fail.",
      "Live Grade shows where you stand. <80% = stand-down.",
    ],
  },
  {
    slug: "field-05-safety-meeting",
    track: "field",
    order: 5,
    title: "Lesson 5 — Safety Meetings (Toolbox Talks)",
    why: "Required daily huddle before work starts. Documents that the crew was briefed on today's hazards — critical if OSHA shows up or an incident happens later.",
    duration: "~4 min",
    steps: [
      "Hub → Safety → Safety Meetings → New Meeting.",
      "Fill project, date/time, Conducted By, Topic Category.",
      "Tap 'Topic Library — Pick a topic to prefill' and search (e.g. 'trench', 'silica', 'heat'). 80+ topics come pre-filled with hazards, key points, references, and action items. Or tap 'Custom Topic' to write your own.",
      "Review / edit the Hazards, Discussion Notes, References, and Action Items.",
      "Add every attendee — each one signs to confirm they were there.",
      "Conductor signs at the bottom. Submit.",
    ],
    tips: [
      "Do this before the crew picks up a shovel — not after. Documentation trumps memory.",
      "Rotate who conducts the meeting each week — builds crew ownership.",
    ],
    cheatSheet: [
      "80+ prefilled topics. Pick one, edit, get signatures.",
      "Every attendee signs. Conductor signs. Submit.",
    ],
  },
  {
    slug: "field-06-jha",
    track: "field",
    order: 6,
    title: "Lesson 6 — Job Hazard Analysis (JHA / JSA)",
    why: "Done BEFORE a specific task starts, not at the start of the day. Walks every step, lists every hazard, documents every control. Best defense against 'we didn't know' after an incident.",
    duration: "~6 min",
    steps: [
      "Hub → Safety → Job Hazard Analysis → New JHA.",
      "Fill project, crew lead, task title, description, and crew members performing the task.",
      "Check every Required PPE item and every Required Permit (confined space, hot work, excavation, etc.).",
      "List the Tools & Equipment needed.",
      "For each Step of the task: describe what the crew is doing → list Potential Hazards → list Controls / Safe Practices. Add as many steps as needed.",
      "Emergency info: Stop Work Authority Acknowledged, Nearest Hospital/ER, Emergency Contact #.",
      "Every crew member signs to confirm understanding. Foreman approves. Submit.",
    ],
    tips: [
      "This is NOT a checklist you fill out at your desk. Walk the task physically before you write it.",
      "Stop Work Authority: every crew member has it. No questions, no discipline — if it doesn't feel right, stop.",
    ],
    cheatSheet: [
      "Task-specific, done before the work starts.",
      "Step → Hazards → Controls for every step.",
      "Every crew member signs. Foreman approves.",
    ],
  },
  {
    slug: "field-07-incident",
    track: "field",
    order: 7,
    title: "Lesson 7 — Accident / Incident Reports",
    why: "The moment something goes wrong, this is the form. Near miss, first aid, medical, DART, fatality — every level gets documented. Root cause, witnesses, corrective actions — all in one record.",
    duration: "~7 min",
    steps: [
      "SECURE THE SCENE FIRST. Get injured workers medical attention. Call 911 if serious. THEN open the app.",
      "Hub → Safety → Incident Reports → New Report.",
      "Fill date, time, location, Reported By, Supervisor.",
      "Pick Incident Type (Injury, Property Damage, Vehicle, Utility Strike, Environmental, Public, Other) and Severity Tier (Near Miss → Fatality). The tier drives OSHA reporting.",
      "Person Involved section: name, role, employer, years experience, body part affected, nature of injury, treatment provided, medical facility, whether sent home.",
      "Description: sequence of events, what changed, what happened. Be factual, be specific.",
      "Root Cause Analysis: check every contributing category (PPE, training, procedure, supervision, equipment, communication, fatigue, housekeeping, weather).",
      "Add every witness with a short statement while it's fresh.",
      "Immediate Actions Taken + Long-Term Corrective Actions. Who owns the follow-up, by when.",
      "Notifications Made: Safety Manager, PM, GC, Owner, OSHA if catastrophic.",
      "Add photos of the scene, equipment, environment.",
      "Reporter + Supervisor sign. Submit.",
    ],
    tips: [
      "A 'Near Miss' with severe potential gets tier 'Near Miss' + describe the potential in the description. Don't upgrade it.",
      "Once you submit, the Safety Manager is emailed automatically within seconds.",
    ],
    cheatSheet: [
      "Scene safe → medical first → app second.",
      "Type + Severity → Person → Story → Root Cause → Witnesses → Fixes → Notifications → Photos.",
      "Reporter + Supervisor sign. Safety is emailed automatically.",
    ],
  },
];

// ============================================================
// SHOP LESSONS (3)
// ============================================================
const SHOP_LESSONS = [
  {
    slug: "shop-01-portal-intro",
    track: "shop",
    order: 1,
    title: "Lesson 1 — Shop Portal Overview",
    why: "The shop console is where mechanics see every Pre-Op submitted by the field, what units are flagged, and what needs attention. One place to keep the fleet running.",
    duration: "~4 min",
    steps: [
      "Go to /shop/login → enter the shop password → you land on the Shop Console.",
      "Top bar shows 4 stats: Inspections on file, Units flagged FAIL, Shop sign-offs, Equipment in fleet.",
      "Left panel: Open Items queue (every FAIL that hasn't been signed off). Right panel: Trends (pass rate by unit/category).",
      "Scroll down: Recent Pre-Op Inspections (full list), Equipment List (searchable fleet), Parts Catalog.",
      "Sign out in the top-right when you're done on a shared computer.",
    ],
    tips: [
      "Admin can also see everything the shop sees. PMs see the trends but cannot sign off items.",
      "The 'All clear.' banner on Open Items is the goal — zero unsigned failures.",
    ],
    cheatSheet: [
      "4 stats at the top. Open Items queue is the priority.",
      "Every FAIL must be signed off or the unit stays OOS.",
    ],
  },
  {
    slug: "shop-02-signing-off",
    track: "shop",
    order: 2,
    title: "Lesson 2 — Signing Off a Failed Pre-Op",
    why: "A FAIL keeps the unit OUT OF SERVICE until the shop clears it. Your sign-off is the audit trail — who fixed it, what parts went in, whether follow-up is needed.",
    duration: "~5 min",
    steps: [
      "Open Items panel → pick a severity filter (All / Out of Service only / Needs Attention only) → tap 'Sign Off' on the row you're working.",
      "The Shop Sign-Off card opens. Enter your name. Write optional notes (parts replaced, follow-up needed, etc.).",
      "Pick an outcome: Repaired, Tagged out of service, Parts ordered, No action needed.",
      "Tap 'Sign Off'. The unit is CLEARED TO OPERATE (or stays OOS if you tagged it that way).",
      "To undo: tap 'Reopen' on any signed-off item. The stamp is removed and the item goes back in the queue.",
    ],
    tips: [
      "If you ordered parts and the unit's still waiting, choose 'Parts ordered' — the unit stays OOS but the queue shows you're on it.",
      "'Repaired' is the only outcome that puts the unit back in service.",
    ],
    cheatSheet: [
      "Name → notes → outcome → Sign Off.",
      "Repaired = cleared. Parts ordered = still OOS but tracked.",
      "Reopen if you signed off too early.",
    ],
  },
  {
    slug: "shop-03-parts-catalog",
    track: "shop",
    order: 3,
    title: "Lesson 3 — Parts Catalog + Order List",
    why: "Every unit has its own parts list — filters, cutting edges, wiper blades, tires, other wear items. Build the order list in one tap per part, email it to the parts office in one tap at the end.",
    duration: "~5 min",
    steps: [
      "Shop Console → Parts Catalog → Pick a Unit from the searchable fleet.",
      "The unit's catalog opens with 5 categories (Filters, Cutting Edges, Wiper Blades, Tires, Other Wear Items). Each category has rows for every part.",
      "Tap 'Add Part' in a category → enter name, part #, qty, notes / size / position / ply / brand as applicable.",
      "Tap 'Save Catalog' when you've added or edited parts — tracked with your name + timestamp.",
      "To order: tap the cart icon next to any part. It's added to the Order List panel below.",
      "In the Order List: enter your name, email(s) of the parts office (comma-separated), optional CC, optional notes.",
      "Tap 'Email Order to Parts Office'. Done — the office gets a formatted list they can act on.",
    ],
    tips: [
      "The catalog persists — once you build a unit's list, every mechanic benefits from it.",
      "If the same part appears on multiple units (e.g., a common filter), add it once per unit so quantities stack correctly in orders.",
    ],
    cheatSheet: [
      "Pick unit → Add Part in the right category → Save.",
      "Cart icon adds to order list. Email at the end.",
    ],
  },
];

// ============================================================
// PM LESSONS (6)
// ============================================================
const PM_LESSONS = [
  {
    slug: "pm-01-portal-intro",
    track: "pm",
    order: 1,
    title: "Lesson 1 — PM Portal Overview",
    why: "Same surface as the Admin console for day-to-day work. Backup / restore / force-reseed are hidden from PMs on purpose — that's the Admin's job. Everything else is identical.",
    duration: "~5 min",
    steps: [
      "Go to /pm/login → enter the PM password (Happy123!). You land on Records & Forms.",
      "Dashboard tiles: Project P&L Snapshot, Daily Reports, Site Inspections, Safety Meetings, Job Hazard Plans, Trench Box Data, Incident Reports, Equipment Pre-Op.",
      "Scroll down to the master lists: Jobs, Employees, Suppliers, Equipment, Parts. Each has inline edit, bulk import, XLSX export, and Archive tab.",
      "Top bar: ALL OK badge (system health), PM Portal button, Guide link, Company Info, Sign Out.",
      "Backup / restore / force-reseed / recovery controls DO NOT APPEAR in the PM Portal. If you need one, ask the Admin.",
    ],
    tips: [
      "Your PM token lasts until you sign out or clear browser storage.",
      "Admin can see everything you see (and more). PMs cannot see what Admin sees (and shouldn't need to).",
    ],
    cheatSheet: [
      "Records & Forms on top → master lists below.",
      "No backup/restore in PM. That's Admin only.",
    ],
  },
  {
    slug: "pm-02-master-lists",
    track: "pm",
    order: 2,
    title: "Lesson 2 — Master Lists (Jobs / Employees / Suppliers / Equipment / Parts)",
    why: "These 5 lists power every drop-down in the field app. If a job isn't here, it isn't in the Job picker. If an employee isn't here, the crew can't tag them on a Daily Report. Keeping these clean = the whole app stays clean.",
    duration: "~7 min",
    steps: [
      "Pick a list (e.g., Jobs). Click 'Add New' to type a row inline. Click any cell to edit. Changes save on blur.",
      "Bulk Replace: the quickest way to seed a list. Click 'Bulk Replace' → paste a spreadsheet → the whole list is wiped and rebuilt from your paste. The existing data is soft-deleted (14-day undo).",
      "Single delete: click the red 🗑️ on any row → confirmation → row moves to the Archive tab (NOT permanently deleted).",
      "Archive tab (top of each panel): see every deleted row with its 'deleted 3 days ago' timestamp. Click 'Restore' to pull it back. After 14 days, rows are permanently purged.",
      "Export button (green): downloads the current list as an XLSX workbook. Round-trips cleanly into Bulk Replace.",
    ],
    tips: [
      "The 14-day soft-delete is your safety net for typos — delete freely, restore from Archive if you regret it.",
      "If you bulk-replace by mistake, every old row is in the Archive tab. Restore individually or just paste the OLD data back in another Bulk Replace.",
    ],
    cheatSheet: [
      "Add New → inline type. Click cell → inline edit.",
      "🗑️ = soft delete. Archive tab = 14-day undo.",
      "Bulk Replace = wipe + seed. Export = XLSX.",
    ],
  },
  {
    slug: "pm-03-import-export",
    track: "pm",
    order: 3,
    title: "Lesson 3 — Import / Export Round-Trips",
    why: "Your master lists may become the cleanest copy of this data the company has. Export regularly so finance, insurance, and auditors can pull fresh data anytime.",
    duration: "~4 min",
    steps: [
      "On any master list, click 'Export' (green button). A timestamped XLSX (e.g., MASCI_employees_2026-05-01.xlsx) downloads.",
      "Open it in Excel/Google Sheets. Every column matches what Bulk Replace expects on the way back in.",
      "Make edits offline (bulk updates, bulk adds). Save the workbook.",
      "Back in the portal, click 'Bulk Replace' → drop the workbook. The list is rebuilt.",
      "To check: after a bulk replace, pull the Export again and diff it against the file you imported. Should match byte-for-byte (aside from timestamps).",
    ],
    tips: [
      "Stage big imports by working on a clone of the export first. Test the file against one list (e.g., 5 rows) before replacing all 137 employees.",
      "After a bulk replace, glance at the Archive tab — every replaced row is there for 14 days if you need to compare.",
    ],
    cheatSheet: [
      "Export → edit offline → Bulk Replace back in.",
      "Round-trip matches byte-for-byte.",
    ],
  },
  {
    slug: "pm-04-archive",
    track: "pm",
    order: 4,
    title: "Lesson 4 — Archive & 14-Day Undo",
    why: "Every delete across the 5 master lists is a soft-delete. Rows aren't gone — they sit in the Archive tab for 14 days, then get purged. This is the safety net that saves you from a bad Friday-afternoon click.",
    duration: "~3 min",
    steps: [
      "On any master list panel (Jobs, Employees, Suppliers, Equipment, Parts), click the 'Archive' tab at the top.",
      "You'll see every deleted row with: what it was, who deleted it (if tracked), when it was deleted, and how many days until purge.",
      "Click 'Restore' to pull it back into the live list instantly.",
      "Rows older than 14 days are auto-purged by a background job. Once purged, only a full-backup restore can recover them.",
      "Admin only: a 'Purge Now' button exists for compliance sweeps — it nukes the entire Archive tab. PMs don't see this button.",
    ],
    tips: [
      "If you see a row you don't recognize in the Archive, don't restore it — check with Admin first. It may have been deliberately archived.",
      "The 14-day window is a HARD cap. Set a calendar reminder if you need something longer.",
    ],
    cheatSheet: [
      "Archive tab = soft-deleted rows.",
      "Restore → back in live list.",
      "Purged after 14 days. Then only a backup can save it.",
    ],
  },
  {
    slug: "pm-05-email-routing",
    track: "pm",
    order: 5,
    title: "Lesson 5 — Email Routing (PM & Safety)",
    why: "Every form submitted from the field is auto-emailed to the relevant PM (based on the job picked) and always CC'd to the Safety Manager. If the PM on a job changes, updating the routing table updates every future email — no manual config per form.",
    duration: "~4 min",
    steps: [
      "PM Portal → Email Routing panel (in the Project Manager roster / Job master).",
      "Each PM row: name, email, phone, active toggle.",
      "Open the Jobs master → each job has a 'Project Manager' field and a 'PM Email' field. When a Daily Report is submitted for that job, the app looks up the PM Email and CC's them automatically.",
      "To change who's on a job: edit the job row → pick a new PM from the dropdown → email field updates automatically → save.",
      "Test it: submit a test form from the field, check the PM's inbox within 60 seconds.",
    ],
    tips: [
      "AUTO_EMAIL_REPORTS is an env-level switch. Production has it ON. Preview is OFF so testing doesn't burn the daily send quota.",
      "If a PM isn't getting emails, check: (1) active toggle, (2) Job's PM assignment, (3) spam folder, (4) env var on the deployed server.",
    ],
    cheatSheet: [
      "Job → PM → PM Email → Daily Report auto-CC's the PM.",
      "Change PM on a job = all future emails re-route.",
    ],
  },
  {
    slug: "pm-06-posters-jha",
    track: "pm",
    order: 6,
    title: "Lesson 6 — Site Posters + JHA Plans",
    why: "Site Posters are the printable handouts you tape inside job trailers — QR-coded so crews can scan from any phone. JHA Plans are per-job PDFs the office uploads so foremen can read the Hazard Plan before breaking ground.",
    duration: "~5 min",
    steps: [
      "Site Posters panel (PM Portal → Site Posters). Three posters: Crew Cheat Sheet, Trench Box Poster, JHA Plans Poster.",
      "Preview any poster in a new tab. Print it. Tape it inside every active job trailer.",
      "JHA Plans Admin: upload a PDF per active job — drag/drop or click to pick. Max 10 MB per PDF.",
      "Field crews go to Safety → Job Hazard Plans → pick their job → read the PDF. No login needed.",
      "Download for offline use: crews tap the PDF on their phone → share menu → save to Files/Downloads. Works in dead zones.",
    ],
    tips: [
      "Reprint posters every quarterly safety refresh — QR codes don't change, but paper fades.",
      "If a job's JHA Plan isn't uploaded, foremen can't see it. Set a calendar reminder: upload before Day 1 of every new job.",
    ],
    cheatSheet: [
      "Posters → print → tape in trailer.",
      "JHA PDF → uploaded per job → readable offline on phones.",
    ],
  },
];

// ============================================================
// ADMIN LESSONS (7)
// ============================================================
const ADMIN_LESSONS = [
  {
    slug: "admin-01-platform-overview",
    track: "admin",
    order: 1,
    title: "Lesson 1 — Platform Overview",
    why: "You hold the admin password. That means everything a PM can do, plus the controls that keep the platform itself safe — backups, restores, force-reseed, integrity audits. This lesson is a map of what's under the hood.",
    duration: "~8 min",
    steps: [
      "The platform is React (frontend) + FastAPI (backend) + MongoDB (database), deployed at mascidocs.com. Preview at safety-audit-mobile-1.preview.emergentagent.com.",
      "Three password levels: Admin (MASCI1982!) sees everything. PM (Happy123!) sees day-to-day but NOT backup/restore. Shop (Nothappy123!) sees only equipment + Pre-Op sign-offs.",
      "Admin Hub tile in the Hub bottom area. /admin/login with MASCI1982!. After login you land on Records & Forms (identical to PM view) + the System Recovery section at the bottom.",
      "Top-level panels under Admin: Dashboards (compliance), Master Lists (Jobs/Employees/Suppliers/Equipment/Parts), Forms (View & Email), Email Routing, Site Posters, JHA Admin, Trench Boxes Admin, Project Managers, System Recovery.",
      "System Recovery section (admin-strict, PMs cannot see it): Backup & Restore Everything, Integrity Check, On-Server Backups list, Crew Recovery, Force-Reseed.",
      "Scheduled backups run twice a day: 02:00 UTC and 18:00 UTC. 14-day retention. Pruned automatically. Admin has zero-touch.",
    ],
    tips: [
      "Never share the Admin password. If you suspect it's leaked, rotate it via ADMIN_PASSWORD in the production deploy env vars.",
      "Everything a PM can do is also in Admin — there's no reason to 'be a PM' as admin. Log in as admin and go.",
    ],
    cheatSheet: [
      "Admin = PM + System Recovery (backups, restore, force-reseed).",
      "3 password tiers: Admin > PM > Shop.",
      "Backups run 02:00 + 18:00 UTC. 14-day retention. Automatic.",
    ],
  },
  {
    slug: "admin-02-backups-how",
    track: "admin",
    order: 2,
    title: "Lesson 2 — How Backups Work (Automatic + Manual)",
    why: "If mongocidocs.com's database disappeared right now, backups are the only thing that would bring MASCI's records back. You need to know EXACTLY how they run, where they live, and how to get one out fast if the production app is on fire.",
    duration: "~10 min",
    steps: [
      "TWO scheduled windows daily: 02:00 UTC (~10pm Eastern, overnight) and 18:00 UTC (~2pm Eastern, mid-day). Set in the backend via BACKUP_HOURS_UTC env var. Default safe values.",
      "Backup content: ONE zip per run, named MASCI_full_backup_YYYY-MM-DD_HHMMSSZ.zip. Contains every MongoDB collection as raw JSON + an index manifest + all uploaded files (PDFs, signatures, photos).",
      "Storage location: /app/backend/backups/ on the server disk. Listed via the Admin → On-Server Backups panel.",
      "Retention: 14 days. Files older than 14 days are pruned automatically on every backup run (pre-flight).",
      "Manual backup: Admin → System Recovery → Backup Hero Panel → click 'Backup + email + download NOW'. Within ~30 seconds you get: (1) a .zip downloaded to your machine, (2) the same .zip emailed to BACKUP_EMAIL_TO via Resend.",
      "What's IN the .zip: it's a normal file. Unzip in Windows Explorer or Mac Finder. Each collection has a .json file. Each safety record has a printable .pdf. Photos/signatures are embedded as base64 inside the JSON. Nothing is encrypted — store it somewhere safe.",
      "Integrity Check: Admin → System Recovery → 'Integrity Check'. Compares live DB collections vs the most recent backup's manifest. If any live collection isn't in the backup, it flags it. Run after big changes or before a deploy.",
      "If the scheduled backup fails: check /app/backend logs (grep 'scheduled-backup'). Common cause is disk space — the pre-flight check aborts if disk is >95% full after pruning.",
    ],
    tips: [
      "Before any redeploy, run the manual backup. Takes 30 seconds. Saves you if the deploy flips a hidden env var.",
      "BACKUP_EMAIL_TO is set in the deploy env. If it's wrong, backups still save to disk — but you won't get a copy to your inbox.",
      "DON'T delete .zip files from the UI unless you have another copy. The app can't resurrect them.",
    ],
    cheatSheet: [
      "Auto: 02:00 + 18:00 UTC. 14-day retention.",
      "Manual: Admin → Backup + email + download NOW.",
      "Integrity Check before every deploy.",
      "BACKUP_EMAIL_TO must be set in prod env.",
    ],
  },
  {
    slug: "admin-03-restore",
    track: "admin",
    order: 3,
    title: "Lesson 3 — How to Restore from a Backup",
    why: "You have a .zip. Something went wrong. You need the data back. This is the exact flow.",
    duration: "~6 min",
    steps: [
      "Confirm what went wrong. If a single row was soft-deleted, use the Archive tab in the master list — faster and safer than a full restore.",
      "Grab a .zip. Either download the most recent one from Admin → On-Server Backups, or use the .zip from your email (BACKUP_EMAIL_TO sent it to your inbox).",
      "Admin → System Recovery → Backup Hero Panel → 'Restore From File' → pick the .zip from your computer. Max 500 MB.",
      "The restore MERGES records: existing rows matching a backup's row are overwritten with the backup copy. New rows in the backup are added. Rows in the live DB that AREN'T in the backup are LEFT ALONE (not deleted). Safe to run.",
      "Confirmation modal: 'Every record inside this .zip will be merged into the live system…'. Click 'Yes, restore it'.",
      "Watch the progress. At the end you'll see 'Restored X records across Y collections'.",
      "Open a couple of dashboards to sanity-check the restored data.",
    ],
    tips: [
      "Restores NEVER wipe. If you're trying to roll back a bad change, you need to ALSO delete the new bad rows after restoring — the old backup doesn't know about them.",
      "If the .zip is older than your current live data, you'll OVERWRITE live data with stale data. Think before you click Yes.",
      "Full system recovery (nuke everything, restore from backup): contact your developer / vendor support — not a UI button on purpose.",
    ],
    cheatSheet: [
      "Restore = merge. Never wipes. Old rows restored + new rows ADDED.",
      "If you want true rollback: restore + manually delete new bad rows.",
      "Soft-delete tab is faster for single-row mistakes.",
    ],
  },
  {
    slug: "admin-04-integrity-check",
    track: "admin",
    order: 4,
    title: "Lesson 4 — Integrity Check & Audit Trail",
    why: "Trust but verify. The Integrity Check proves that every collection currently in your live DB is captured in the most recent backup — catches new collections that a future feature adds without updating the backup routine.",
    duration: "~4 min",
    steps: [
      "Admin → System Recovery → Integrity Check (or /api/admin/backups/integrity-check directly).",
      "Output: last_backup_filename, last_backup_at, live_collections (every Mongo collection right now), captured_collections (what the last backup contained), missing_from_backup (⚠ any mismatches), ok (true/false).",
      "If ok === false: a collection exists live but wasn't backed up. Action: run a manual backup immediately, then check that next scheduled run catches it. If still missing, the backup code needs a patch.",
      "Run this check: (1) after any feature release that adds a collection, (2) before any prod deploy, (3) as a monthly sanity sweep.",
    ],
    tips: [
      "As of the last audit, all 23 collections are captured: activity_log, daily_reports, docs, employees, equipment_inspections, equipment_master, equipment_parts, equipment_units, events, hill_scopes, incidents, inspections, jhas, job_hazard_files, jobs_master, meetings, message_comments, messages, notifications, project_managers, project_members, projects, suppliers.",
      "The integrity check is cheap (<1 sec). No reason not to run it often.",
    ],
    cheatSheet: [
      "Integrity Check = do live collections match last backup's manifest?",
      "ok=true → all good. ok=false → run manual backup now.",
    ],
  },
  {
    slug: "admin-05-crew-recovery",
    track: "admin",
    order: 5,
    title: "Lesson 5 — Crew Recovery Tools (Force-Reseed, Password Reset)",
    why: "Rare-use tools for when the seed data (jobs, roster) drifts or the deployed app loses its seed on redeploy. Admin-only. NEVER used by PMs. Most admins never touch these — but when you need them, you really need them.",
    duration: "~5 min",
    steps: [
      "Crew Recovery Status: /api/admin/crew-recovery/status (or via the UI panel). Shows how many jobs, employees, suppliers are in the live DB vs what the seed would insert.",
      "Reset Password: /api/admin/crew-recovery/reset-password. Rarely needed. Use if a shop user forgot and you can't update them via the users panel.",
      "Force-Reseed: /api/admin/crew-recovery/force-reseed. WIPES AND REBUILDS the seeded collections (jobs_master, employees, suppliers) from the hard-coded JOB_LIBRARY. All hand-edits to those tables are LOST.",
      "Before force-reseed: run a manual backup. Confirm you want to lose every edit since the last seed. Then click.",
      "Scrap-Crew-Hub: /api/admin/crew-recovery/scrap-crew-hub. Nukes the old Basecamp-clone feature flag and associated collections. Already run historically. Do not re-run unless re-enabling Crew Hub.",
    ],
    tips: [
      "If a PM accidentally Bulk Replaced all 137 employees with 2 test rows, DON'T force-reseed — restore from Archive (14-day soft-delete) instead. Force-reseed is for deeper corruption.",
      "Every recovery route is require_admin_strict. PM tokens return 401. Shop tokens return 401.",
    ],
    cheatSheet: [
      "Force-reseed = wipe + seed from JOB_LIBRARY. Last resort.",
      "Always manual-backup FIRST.",
      "Prefer Archive restore for single-row mistakes.",
    ],
  },
  {
    slug: "admin-06-deploy-redeploy",
    track: "admin",
    order: 6,
    title: "Lesson 6 — Safe Deploy / Redeploy Workflow",
    why: "Every redeploy is a chance for something to break. The routine below has shipped 20+ deploys without data loss. Follow it.",
    duration: "~7 min",
    steps: [
      "Step 1 — BACKUP. Admin → System Recovery → 'Backup + email + download NOW'. Wait for the green check.",
      "Step 2 — Integrity Check. Admin → 'Integrity Check'. Confirm ok: true.",
      "Step 3 — Save-to-GitHub (in the deploy chat input). Captures the current frontend+backend as a commit — rollback checkpoint.",
      "Step 4 — Verify production deploy env vars: ADMIN_PASSWORD, PM_PASSWORD, SHOP_PASSWORD, ADMIN_HMAC_SECRET, CORS_ORIGINS, MONGO_URL, DB_NAME, BACKUP_EMAIL_TO, RESEND_API_KEY, AUTO_EMAIL_REPORTS=true, RATE_LIMITING=on.",
      "Step 5 — Click Deploy in the deployment dashboard. Wait for the build.",
      "Step 6 — Post-deploy smoke: curl /api/health → 200. Log in as Admin, PM, Shop. Spot-check a dashboard. Spot-check Backup panel loads.",
      "Step 7 — Run Integrity Check again on the live site. Confirm the post-deploy backup captures all collections.",
      "If anything looks wrong: use the Rollback option in the deployment dashboard to return to the pre-deploy checkpoint. If data changed between deploy and rollback, restore from the Step-1 backup.",
    ],
    tips: [
      "Rollback is free and fast. Don't hesitate if something looks off — rollback first, debug after.",
      "Always keep the pre-deploy backup for at least a week after the deploy — that's your insurance if a subtle bug only shows up on day 3.",
    ],
    cheatSheet: [
      "Backup → Integrity Check → GitHub → Deploy → Smoke → Integrity Check.",
      "Rollback if anything's off. Debug later.",
    ],
  },
  {
    slug: "admin-07-security-passwords",
    track: "admin",
    order: 7,
    title: "Lesson 7 — Passwords, Access, and Security",
    why: "The weakest link in any system is the password. Here's how MASCI's token model works and what to do when a password is leaked or a PM/Shop person leaves.",
    duration: "~5 min",
    steps: [
      "Passwords live in env vars: ADMIN_PASSWORD, PM_PASSWORD, SHOP_PASSWORD. All set in the production deploy env.",
      "Frontend flow: login POST /api/{admin|pm|shop}/login with the password → backend returns a 64-char HMAC token → frontend stores it in localStorage and sends it as an X-{Admin|PM|Shop}-Token header on every request.",
      "Token has no expiry — it's invalidated by rotating the password (all old tokens stop working immediately).",
      "Rotate Admin: set ADMIN_PASSWORD to a new value in the production deploy env → redeploy. Every admin session is kicked. Same for PM_PASSWORD / SHOP_PASSWORD.",
      "Rate limiting: LOGIN_MAX_FAILS=10 (default) and LOGIN_LOCKOUT_SECONDS=900 (15 min) — blocks password-spray attacks by IP.",
      "CORS: only mascidocs.com and its www origin can hit the prod API. Preview URLs are allowed via CORS_ORIGIN_REGEX.",
      "When a PM leaves: rotate PM_PASSWORD. Inform the remaining PMs of the new password out-of-band (Signal, phone, in person — NOT email).",
    ],
    tips: [
      "If an admin password LEAKS: rotate immediately. Audit the activity_log collection for anything weird in the last 72 hours.",
      "ADMIN_HMAC_SECRET is the HMAC key that signs tokens. If THAT leaks, rotate it too — which invalidates every admin session system-wide.",
    ],
    cheatSheet: [
      "Passwords = env vars. Rotate = redeploy = all old tokens invalidated.",
      "Rate limit: 10 fails → 15-min IP lockout.",
      "When someone leaves → rotate their tier's password.",
    ],
  },
];

export const LESSONS = [
  ...FIELD_LESSONS,
  ...SHOP_LESSONS,
  ...PM_LESSONS,
  ...ADMIN_LESSONS,
].map((l) => {
  const es = LESSON_TRANSLATIONS_ES[l.slug];
  return es ? { ...l, ...es } : l;
});

export const lessonsForTrack = (trackSlug) =>
  LESSONS.filter((l) => l.track === trackSlug).sort((a, b) => a.order - b.order);
