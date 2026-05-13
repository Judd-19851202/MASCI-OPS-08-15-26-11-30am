import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, Printer, ClipboardCheck, Users, AlertOctagon, ClipboardList,
  Wrench, Mail, ShieldCheck, HardDrive, QrCode, HelpCircle, Truck,
  TrendingUp, Building2, ListChecks, KeyRound, Cloud, LayoutDashboard,
  GraduationCap, Rocket,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { Button } from "@/components/ui/button";

/**
 * AdminGuide — plain-English, print-friendly owner's manual for the MASCI
 * Operations Platform. Accessible at /admin/guide. Crews never see this page.
 *
 * Last rebuilt 2026-05-13 (iter85) to reflect:
 *   - Multi-portal sign-in (/sign-in + per-portal /admin/login, /pm/login, ...)
 *   - Email + password auth (no shared single-password admin gate in UI)
 *   - Admin Console sub-routes (/admin/people, /admin/jobs, /admin/system, ...)
 *   - Pre-Deploy Snapshot panel + hourly R2 auto-snapshots
 *   - 5-portal Hub (Field/Safety/PM/Shop/HR + Leadership)
 */
export default function AdminGuide() {
  return (
    <div className="min-h-screen bg-white" data-testid="admin-guide-page">
      {/* Screen-only header (hidden in print) */}
      <header className="bg-slate-900 text-white border-b-4 border-red-700 print:hidden">
        <div className="max-w-4xl mx-auto px-5 py-3 flex items-center justify-between gap-3">
          <Link
            to="/admin"
            className="inline-flex items-center gap-1 text-xs font-bold uppercase tracking-wide hover:text-red-300"
            data-testid="guide-back-link"
          >
            <ArrowLeft className="w-4 h-4" /> Admin Console
          </Link>
          <MasciLogo variant="lockup" size="md" className="hidden sm:block" homeLink="/admin" />
          <Button
            onClick={() => window.print()}
            className="h-9 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs"
            data-testid="guide-print-btn"
          >
            <Printer className="w-4 h-4 mr-1" /> Print
          </Button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 sm:px-8 py-8 sm:py-12 print:py-4 print:px-0">
        {/* Print header */}
        <div className="hidden print:block mb-6 pb-3 border-b-2 border-black">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-black text-lg">MASCI Operations Platform</div>
              <div className="text-xs uppercase tracking-[0.2em]">Owner's Manual · Print / Tape to wall</div>
            </div>
            <div className="text-xs">mascidocs.com</div>
          </div>
        </div>

        {/* Screen hero */}
        <div className="mb-10 print:hidden">
          <div className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold">
            MASCI Admin · Owner's Manual
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-2">
            How to run this thing.
          </h1>
          <p className="text-slate-600 mt-3 max-w-2xl text-base">
            One page, plain English. Print it, tape it to the wall, hand it to whoever covers the office
            when you're out. You do not need to understand any code to run the MASCI Operations Platform.
          </p>
        </div>

        {/* THE PLATFORM AT A GLANCE */}
        <Section icon={ShieldCheck} title="The Hub at a glance" color="slate">
          <p>Open <code>mascidocs.com</code> and you'll see the main tiles. Five portals plus public submission entry points:</p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li>🦺 <strong>Safety</strong> — Public submission. Inspections · Meetings · Incidents · JHP Plans · Trench Box Data.</li>
            <li>👷 <strong>Field</strong> — Public submission. Daily Reports · Equipment Pre-Op · Calculators.</li>
            <li>🧑‍💼 <strong>PM</strong> — Login required (per-PM email + password). Scoped dashboards for assigned jobs.</li>
            <li>🔧 <strong>Shop</strong> — Login required (per-mechanic email + password). Pre-Op trends, sign-off.</li>
            <li>👥 <strong>HR</strong> — Login required (per-HR-user email + password). Time verification, accountability, training records.</li>
            <li>🛡️ <strong>Field Leadership</strong> — Shared password gate. Write-ups, coaching, crew evaluations.</li>
            <li>🗄️ <strong>Admin</strong> — Office console. Everything in this manual below.</li>
            <li>🏗️ <strong>Basecamp</strong> + 📍 <strong>OnStation</strong> — External tabs for project comms + field staking.</li>
          </ul>
          <p className="mt-3 text-xs text-slate-500"><em>The in-app Crew Hub project workspace was retired on 2026-04-28 — we now use Basecamp for project comms and OnStation for field staking. Both open in a new tab from the Hub home.</em></p>
        </Section>

        {/* SIGN-IN OPTIONS */}
        <Section icon={KeyRound} title="How to sign in (3 ways)" color="red">
          <p>Every office user signs in with their <strong>work email + personal password</strong>. The legacy "single shared admin password" is gone from the human-facing UI (kept only as an API break-glass for IT).</p>
          <div className="grid sm:grid-cols-3 gap-3 mt-4">
            <div className="border-2 border-red-700 bg-red-50 rounded-md p-3">
              <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-red-700 font-bold mb-1">
                One portal only
              </div>
              <p className="text-sm m-0">
                Go to <code>/admin/login</code> (or <code>/pm/login</code>, <code>/shop/login</code>, <code>/hr/login</code>). Email + password. Drops you straight into that portal.
              </p>
            </div>
            <div className="border-2 border-slate-800 bg-slate-50 rounded-md p-3">
              <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-700 font-bold mb-1">
                Multiple portals
              </div>
              <p className="text-sm m-0">
                Go to <code>/sign-in</code>. Same email + password works as the "master sign-in" — backend issues tokens for every portal you're assigned to in one shot. Switch between them via the <strong>SWITCH PORTAL</strong> dropdown in the header.
              </p>
            </div>
            <div className="border-2 border-amber-600 bg-amber-50 rounded-md p-3">
              <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber-700 font-bold mb-1">
                Field crew
              </div>
              <p className="text-sm m-0">
                <strong>No login.</strong> Field workers open <code>mascidocs.com</code> on their phone and tap a Safety or Field submission tile directly — no password needed for public submissions.
              </p>
            </div>
          </div>
          <p className="mt-3">
            <strong>Forgot password?</strong> Each portal's login page has a "Forgot password?" link that emails a 30-minute reset link. Admin can also re-issue any user's temp password from the Access Control panel in under 30 seconds.
          </p>
        </Section>

        {/* ADMIN CONSOLE LAYOUT */}
        <Section icon={LayoutDashboard} title="Admin Console layout (what each section does)" color="slate">
          <p>The Admin Console at <code>/admin</code> is now organized into <strong>7 sections plus an Overview dashboard</strong>. Sidebar nav on the left (or hamburger on mobile). Every section has a "← Back to Admin Overview" button at the top.</p>
          <table className="w-full border-collapse text-sm mt-3">
            <thead>
              <tr className="bg-slate-100">
                <th className="text-left p-2 border border-slate-300">Section</th>
                <th className="text-left p-2 border border-slate-300">Path</th>
                <th className="text-left p-2 border border-slate-300">What lives there</th>
              </tr>
            </thead>
            <tbody>
              <tr><td className="p-2 border border-slate-300 font-bold">Overview</td><td className="p-2 border border-slate-300 font-mono text-xs">/admin</td><td className="p-2 border border-slate-300 text-xs">Welcome + Doc-ID record search + section tiles.</td></tr>
              <tr><td className="p-2 border border-slate-300 font-bold">People &amp; Access</td><td className="p-2 border border-slate-300 font-mono text-xs">/admin/people</td><td className="p-2 border border-slate-300 text-xs">PM accounts · Shop users · HR users · Multi-portal directory · Employee master roster.</td></tr>
              <tr><td className="p-2 border border-slate-300 font-bold">Jobs &amp; Field</td><td className="p-2 border border-slate-300 font-mono text-xs">/admin/jobs</td><td className="p-2 border border-slate-300 text-xs">Job master · Site posters · Active banners.</td></tr>
              <tr><td className="p-2 border border-slate-300 font-bold">Equipment &amp; Suppliers</td><td className="p-2 border border-slate-300 font-mono text-xs">/admin/equipment</td><td className="p-2 border border-slate-300 text-xs">Pre-Op status board · Equipment master · Parts catalog · Supplier list.</td></tr>
              <tr><td className="p-2 border border-slate-300 font-bold">Email &amp; Routing</td><td className="p-2 border border-slate-300 font-mono text-xs">/admin/email</td><td className="p-2 border border-slate-300 text-xs">Auto-routing rules · Distribution lists.</td></tr>
              <tr><td className="p-2 border border-slate-300 font-bold">Training &amp; Forms</td><td className="p-2 border border-slate-300 font-mono text-xs">/admin/training</td><td className="p-2 border border-slate-300 text-xs">Field adoption analytics (scans, bilingual, calculator usage) · Training resources · Safety-forms library.</td></tr>
              <tr><td className="p-2 border border-slate-300 font-bold">Compliance &amp; Audits</td><td className="p-2 border border-slate-300 font-mono text-xs">/admin/compliance</td><td className="p-2 border border-slate-300 text-xs">Date-range CSV exports · Document audit.</td></tr>
              <tr><td className="p-2 border border-slate-300 font-bold">System &amp; Backups</td><td className="p-2 border border-slate-300 font-mono text-xs">/admin/system</td><td className="p-2 border border-slate-300 text-xs">Pre-Deploy snapshot panel · Hero backup buttons · Cloud (R2) archives · Verification cron · Restore · Crew recovery.</td></tr>
            </tbody>
          </table>
        </Section>

        {/* PRE-DEPLOY SNAPSHOT */}
        <Section icon={Rocket} title="⚠ Before any redeploy — the Pre-Deploy Snapshot panel" color="red">
          <p>Open <code>/admin/system</code>. The very top of that page shows a giant traffic-light panel:</p>
          <div className="grid sm:grid-cols-3 gap-3 mt-3">
            <div className="border-2 border-emerald-500 bg-emerald-50 rounded-md p-3">
              <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-emerald-700 font-bold mb-1">🟢 GREEN · &lt; 1 hour old</div>
              <p className="text-sm m-0">SAFE TO REDEPLOY. The hourly auto-snapshot has you covered.</p>
            </div>
            <div className="border-2 border-amber-500 bg-amber-50 rounded-md p-3">
              <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber-700 font-bold mb-1">🟡 YELLOW · 1–12 hours</div>
              <p className="text-sm m-0">Click "Snapshot Now" before redeploying.</p>
            </div>
            <div className="border-2 border-red-700 bg-red-50 rounded-md p-3">
              <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-red-700 font-bold mb-1">🔴 RED · &gt; 12 hours</div>
              <p className="text-sm m-0">Run a snapshot NOW. Wait for it to complete before any redeploy.</p>
            </div>
          </div>
          <p className="mt-3">
            <strong>Hourly auto-snapshots</strong> run in the background every UTC hour to a Cloudflare R2 archive. <strong>The "Snapshot Now" button</strong> on the panel forces a fresh archive build (30–60 seconds) if you need a closer recovery point. <strong>Nightly verification email</strong> at 14:00 UTC Mondays confirms the archive system is healthy.
          </p>
        </Section>

        {/* EVERY DAY */}
        <Section
          icon={ClipboardCheck}
          title="Every day — crews in the field"
          color="red"
        >
          <p className="mb-2">Crews do <strong>nothing different</strong> than before. They just open <code>mascidocs.com</code> on their phone or tablet and tap the section tile for what they need:</p>
          <ul className="ml-5 list-disc space-y-1">
            <li>👷 Field → <strong>Daily Reports</strong> — end of every shift, per job</li>
            <li>👷 Field → <strong>Equipment Pre-Op</strong> — before starting any piece of equipment</li>
            <li>🦺 Safety → <strong>Site Inspections</strong> — weekly or as needed (passcode <code>1982</code>)</li>
            <li>🦺 Safety → <strong>Safety Meetings</strong> — toolbox talks with crew signatures</li>
            <li>🦺 Safety → <strong>Incident Reports</strong> — any near-miss, injury, or property damage</li>
          </ul>
          <p className="mt-3">
            PDFs <strong>auto-email</strong> to the assigned PM + safety@mascigc.com as soon as the form is submitted.
            You don't push a button. It just happens.
          </p>
        </Section>

        {/* EVERY WEEK */}
        <Section icon={Users} title="Every week — you, in the office" color="amber">
          <p>Sign in at <code>mascidocs.com/admin/login</code> with your work email + password. Land on the Admin Overview. Most weekly tasks:</p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li>Use the <strong>Doc-ID search</strong> at top of Overview to jump to any specific record (e.g., <code>DR-2026-00007</code>).</li>
            <li>Visit <strong>Training &amp; Forms</strong> to see how many scans/calculations your crews logged this week (bilingual breakdown included).</li>
            <li>Visit <strong>Email &amp; Routing</strong> to confirm which PM gets which job's reports.</li>
            <li>Visit <strong>Equipment &amp; Suppliers</strong> to see the Pre-Op status board — every piece with pass/fail history.</li>
            <li>Visit <strong>Compliance &amp; Audits</strong> to pull date-range CSVs for OSHA / DOT.</li>
            <li>Visit <strong>System &amp; Backups</strong> to glance at the snapshot freshness panel (should always be green).</li>
          </ul>
        </Section>

        {/* PROJECT P&L */}
        <Section icon={TrendingUp} title="Project P&L Snapshot — live job-cost dashboard" color="amber">
          <p>
            From the Admin Overview, click <strong>Jobs &amp; Field</strong> → look for <strong>Project P&amp;L Snapshot</strong> —
            or go straight to <code>/admin/pnl</code>. Pick a project, optional date range, your
            labor rate ($/hr), and you get a live snapshot pulled straight from submitted Daily Reports.
          </p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li><strong>Crew hrs by employee</strong> — each MASCI worker, days on site, hours, cost @ rate.</li>
            <li><strong>Subs hrs by company</strong> — every sub, average headcount, total man-hours.</li>
            <li><strong>Materials</strong> — one row per delivery ticket (date, qty, unit, supplier, ticket #, photo count).</li>
            <li><strong>4 KPI tiles</strong> at the top: # of reports, MASCI crew hrs, Sub man-hrs, total Labor cost.</li>
          </ul>
          <p className="mt-3">
            Numbers update the second a foreman submits a Daily Report — no manual rollup. Use this to
            spot overruns mid-job, prep claim packets, or run a Friday cost meeting.
          </p>
        </Section>

        {/* MASTER LISTS */}
        <Section icon={ListChecks} title="Master lists — keeping the dropdowns current" color="slate">
          <p>
            Three uploadable lists feed every dropdown across the platform. Find them under{" "}
            <strong>Equipment &amp; Suppliers</strong> (<code>/admin/equipment</code>) and{" "}
            <strong>People &amp; Access</strong> (<code>/admin/people</code>):
          </p>
          <ul className="ml-5 list-disc space-y-2 mt-2">
            <li>
              <strong className="flex items-center gap-1.5"><Truck className="w-4 h-4" /> Equipment Master Fleet</strong>
              <br />Upload your master <code>Equipment List.xlsx</code> (Louis sheet). Auto-categorizes by
              prefix (DPT-, EXC-, LDR-, etc.). Feeds Equipment Pre-Op + Daily Report Equipment Log.
            </li>
            <li>
              <strong className="flex items-center gap-1.5"><Users className="w-4 h-4" /> Employee Roster</strong>
              <br />Upload .xlsx or .csv with at least a <code>Name</code> column (extra columns
              like Trade, Crew, Email all welcome but optional). Feeds the searchable employee picker
              in Daily Report Section 04 (Crew on Site), Site Inspection (operator), Incident
              (witnesses, supervisor), Equipment Pre-Op (operator).
            </li>
            <li>
              <strong className="flex items-center gap-1.5"><Building2 className="w-4 h-4" /> Supplier &amp; Subcontractor List</strong>
              <br />Upload .xlsx or .csv with company names in the first column. Feeds the searchable
              supplier picker in Daily Report Section 05 (Subcontractors) + Section 08 (Material
              Deliveries).
            </li>
          </ul>
          <p className="mt-3">
            <strong>Operators can always type free-text</strong> if a name/equipment/supplier isn't
            in the list yet — nothing blocks them in the field. Then you re-upload the master file
            when convenient.
          </p>
        </Section>

        {/* PRE-OP OOS WORKFLOW */}
        <Section icon={AlertOctagon} title="Equipment Pre-Op — Out of Service vs Needs Attention" color="red">
          <p>
            When an operator marks any item <strong>FAIL</strong>, the system splits the response in two:
          </p>
          <div className="grid sm:grid-cols-2 gap-3 mt-3">
            <div className="border-2 border-red-700 bg-red-50 rounded-md p-3">
              <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-red-700 font-bold mb-1">
                Red — OUT OF SERVICE
              </div>
              <p className="text-sm m-0">
                Critical fluids (oil, coolant, hydraulic, transmission, gearbox), brakes, steering, kill
                switch, ROPS/FOPS, seat belt, horn, backup alarm, tires/tracks, fire extinguisher,
                strobe/beacon, hydraulic hoses, boom/arm pins, outriggers, visible leaks. <strong>Operator
                gets a stop-work modal:</strong> "Get with your supervisor — this unit is unsafe. Notify
                shop. Tag-out the machine."
              </p>
            </div>
            <div className="border-2 border-amber-500 bg-amber-50 rounded-md p-3">
              <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber-700 font-bold mb-1">
                Yellow — NEEDS ATTENTION
              </div>
              <p className="text-sm m-0">
                Everything else (mirrors, lights/electrical, paint/decals, etc.). Logged + photographed
                so the shop has a record, but the unit can stay in service until reviewed.
              </p>
            </div>
          </div>
          <p className="mt-3">
            Both severities require a <strong>10-character description</strong> and at least one photo
            from the operator before the inspection can be submitted.
          </p>
        </Section>

        {/* PRE-OP TRENDS + SIGNOFF */}
        <Section icon={Wrench} title="Pre-Op trends + shop sign-off" color="slate">
          <p>
            On <code>/admin/equipment</code> the dashboard shows three leaderboards (last 90 days):
          </p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li><strong>Most-problematic equipment</strong> — units ranked by OOS fails ➔ Needs Attention fails ➔ inspection count.</li>
            <li><strong>Operators with most failed inspections</strong> — surfaces training opportunities or repeat trouble.</li>
            <li><strong>Jobsites trending bad</strong> — same ranking, by project number.</li>
          </ul>
          <p className="mt-3">
            On any inspection detail page, the <strong>Shop Sign-Off</strong> panel lists every FAIL
            line. The shop person types their name, action taken (Repaired / Tagged out / Parts ordered /
            No action needed), optional notes, and signs off. The original FAIL stays in the historical record;
            the sign-off is logged with timestamp + name. The <strong>Open Shop Items</strong> panel
            on <code>/admin/equipment</code> shows everything still pending across the whole fleet.
          </p>
          <div className="mt-4 bg-amber-50 border-l-4 border-amber-500 p-3 rounded-r">
            <div className="font-bold text-amber-900 uppercase text-sm tracking-wide">Shop Console (per-user login)</div>
            <p className="text-amber-900 text-sm mt-1">
              Mechanics get their own focused console at <code>/shop</code> — Pre-Op trends, open
              items, recent inspections, and the full equipment list. Each mechanic has their own
              email + password (admin issues a temp pw from <code>/admin/people</code>). Admins
              automatically have shop access through their admin token.
            </p>
          </div>
        </Section>

        {/* BACKUP */}
        <Section icon={HardDrive} title="Backups — how to never lose data" color="slate">
          <p className="font-bold text-slate-900 mb-2">Three layers of protection, in order of freshness:</p>
          <ul className="ml-5 list-disc space-y-1.5 mt-2">
            <li><strong>Hourly R2 cloud archives</strong> — every UTC hour the system writes a complete archive (DB + every photo inlined) to Cloudflare R2. Maximum data-loss window: ~1 hour. <em>Set</em> <code>BACKUP_R2_HOURLY=true</code> <em>in production env.</em></li>
            <li><strong>Nightly email backup</strong> — every night at 2 AM UTC a complete <code>.zip</code> emails to <strong>jaymn.judd@mascigc.com</strong>. Keep those emails as a separate off-site copy.</li>
            <li><strong>Weekly verification email</strong> — every Monday at 14:00 UTC the system emails a health report confirming R2 archives are recent and well-sized. Catches the "backend thinks it backed up but R2 silently rejected" scenario.</li>
          </ul>

          <div className="mt-4 bg-red-50 border-l-4 border-red-700 p-3 rounded-r">
            <div className="font-bold text-red-900 uppercase text-sm tracking-wide">⚠ Before any production redeploy</div>
            <p className="text-red-900 text-sm mt-1">
              Open <code>/admin/system</code>. Check the <strong>Pre-Deploy Snapshot</strong> panel at the top.
              If green, redeploy is safe. If yellow or red, click <strong>SNAPSHOT NOW</strong> and wait
              for the build to complete before deploying. Alternatively use the <strong>BACKUP EVERYTHING</strong>
              button (downloads + emails + writes to local disk) for a triple-redundancy moment.
            </p>
          </div>

          <div className="mt-4 bg-emerald-50 border-l-4 border-emerald-700 p-3 rounded-r">
            <div className="font-bold text-emerald-900 uppercase text-sm tracking-wide">If data is missing after a deploy</div>
            <ol className="text-emerald-900 text-sm mt-1 ml-5 list-decimal space-y-1">
              <li>Open <code>/admin/system</code> → <strong>Restore from Backup</strong> panel.</li>
              <li>Pick a source: <strong>"From R2 archive"</strong> (dropdown of recent cloud archives) <strong>or</strong> <strong>"Upload .zip"</strong> (your nightly email backup).</li>
              <li>Pick Merge (safe, default) or Replace (wipes collections first — destructive, requires password re-entry).</li>
              <li>Confirm. Wait 30–60 seconds. Done.</li>
            </ol>
          </div>
        </Section>

        {/* BACKUP FILE */}
        <Section icon={HelpCircle} title="What's actually in the backup .zip?" color="slate">
          <p>Any zip tool (Windows Explorer, Mac Finder, 7-Zip) opens it. Inside:</p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li><code>CSV/</code> — one spreadsheet per module (open in Excel)</li>
            <li><code>inspections/pdf/</code>, <code>meetings/pdf/</code>, <code>incidents/pdf/</code>, etc. — every record as a printable PDF</li>
            <li><code>inspections/json/</code>, etc. — every record as a structured data file (includes photos + signatures)</li>
            <li><code>safety_aux/</code> — equipment registry, JHP plans, trench-box data</li>
            <li><code>backup_log.txt</code> — human-readable manifest of how many of each thing was saved</li>
            <li><code>backup_manifest.json</code> — machine-readable version used by Restore</li>
          </ul>
          <p className="mt-3 font-semibold">
            The .zip is <strong>not encrypted</strong> — anyone with the file can read it. Treat it like a payroll binder:
            keep it somewhere only authorized office staff can access. Cloudflare R2 presigned URLs are valid 7 days each —
            safe to forward to IT for off-site copies.
          </p>
        </Section>

        {/* PASSWORDS */}
        <Section icon={ShieldCheck} title="Passwords &amp; Access Control" color="slate">
          <p className="mb-3">Every office user has their own email + password. The legacy single-password admin gate is gone from the UI. Admin manages all accounts from <code>/admin/people</code>.</p>
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="bg-slate-100">
                <th className="text-left p-2 border border-slate-300">Portal</th>
                <th className="text-left p-2 border border-slate-300">How users sign in</th>
                <th className="text-left p-2 border border-slate-300">How admin manages it</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-2 border border-slate-300 font-bold">Admin <code>/admin/login</code></td>
                <td className="p-2 border border-slate-300 text-xs">Work email + password (stored in <code>user_directory</code> as bcrypt)</td>
                <td className="p-2 border border-slate-300 text-xs"><code>/admin/people</code> → Multi-Portal Directory. Add/remove admins, reset passwords, audit log.</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300 font-bold">PM <code>/pm/login</code></td>
                <td className="p-2 border border-slate-300 text-xs">Work email + password. Forgot? In-page reset link.</td>
                <td className="p-2 border border-slate-300 text-xs"><code>/admin/people</code> → PM Accounts. Issue temp pw → email welcome PDF.</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300 font-bold">Shop <code>/shop/login</code></td>
                <td className="p-2 border border-slate-300 text-xs">Work email + password. Forgot? In-page reset link.</td>
                <td className="p-2 border border-slate-300 text-xs"><code>/admin/people</code> → Shop Users. Same flow as PM.</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300 font-bold">HR <code>/hr/login</code></td>
                <td className="p-2 border border-slate-300 text-xs">Work email + password. Forgot? In-page reset link.</td>
                <td className="p-2 border border-slate-300 text-xs"><code>/admin/people</code> → HR Users. Same flow as PM.</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300 font-bold">Multi-portal <code>/sign-in</code></td>
                <td className="p-2 border border-slate-300 text-xs">Same work email + password — backend issues every portal token in one shot.</td>
                <td className="p-2 border border-slate-300 text-xs"><code>/admin/people</code> → Multi-Portal Directory. Per-user <code>portals: [admin, pm, hr, ...]</code> array.</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300 font-bold">Field Leadership <code>/leadership</code></td>
                <td className="p-2 border border-slate-300 text-xs">Shared password gate (legacy). Admin + PM tokens also work.</td>
                <td className="p-2 border border-slate-300 text-xs">Rotated via <code>LEADERSHIP_PASSWORD</code> env var.</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300 font-bold">Site Inspection (field)</td>
                <td className="p-2 border border-slate-300 font-mono text-xs">1982 (gate code)</td>
                <td className="p-2 border border-slate-300 text-xs">Hardcoded gate — prevents randos submitting. On the field reference card.</td>
              </tr>
            </tbody>
          </table>
        </Section>

        {/* WHO GETS WHAT */}
        <Section icon={Mail} title="Auto-email routing" color="amber">
          <p>When a crew submits a form, the PDF auto-emails to:</p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li><strong>Assigned PM</strong> (based on project number — David, Chris, Ramon, or Jaymn)</li>
            <li><strong>jaymn.judd@mascigc.com</strong> (always)</li>
            <li><strong>safety@mascigc.com</strong> (always)</li>
            <li>For <strong>severe incidents</strong> (medical, lost-time, OSHA-recordable): also blasts the <code>SEVERE_INCIDENT_CC</code> list</li>
            <li>For <strong>failed Pre-Op</strong> (OOS or Needs Attention): fan-out to every active <code>shop_users</code> account.</li>
          </ul>
          <p className="mt-3">See the <em>Auto-Email Routing</em> panel on <code>/admin/email</code> for the full job-to-PM table.</p>
        </Section>

        {/* TRAINING */}
        <Section icon={GraduationCap} title="Training Hub &amp; QR posters" color="amber">
          <p>The <strong>Training Hub</strong> at <code>/training</code> serves four audience tracks: Field (public, no login), Shop, PM, Admin. Each track has bilingual EN/ES lessons + a printable PDF packet.</p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li><strong>Trailer QR posters</strong> — tape one in every trailer. Scanning opens the right Field training page in EN or ES, no login. Print all 3 from <code>/admin/jobs</code> → Site Posters.</li>
            <li><strong>Scan analytics</strong> — <code>/admin/training</code> shows last 7 days scans by track + by language + 14-day trend.</li>
            <li><strong>Bilingual adoption</strong> — same page shows what % of all field submissions were filed in Spanish (auto-translated to English on the record itself).</li>
            <li><strong>Calculator usage</strong> — material calculator runs (aggregate, asphalt, concrete, etc.) per EN/ES.</li>
          </ul>
        </Section>

        {/* SHARE FORMS */}
        <Section icon={QrCode} title="Sharing forms with the field" color="red">
          <p>Every form has a public submit URL + QR code. From each module dashboard (<code>/admin/inspections</code>, etc.) click the <strong>Share</strong> button to see the QR code.</p>
          <p className="mt-2">There are also <strong>printable wall posters</strong>:</p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li>Field Card (Cheat Sheet) — tape in every trailer · prints from <code>/cheatsheet</code></li>
            <li>Job Hazard Plans QR — tape next to the plans binder</li>
            <li>Trench Box QR — tape on the trench box</li>
            <li>Training Trailer Posters — one per training track, bilingual</li>
          </ul>
          <p className="mt-2">
            Print all posters from <code>/admin/jobs</code> → <strong>Site Posters</strong> panel → <strong>Print All Posters</strong>.
          </p>
        </Section>

        {/* WHEN THINGS BREAK */}
        <Section icon={AlertOctagon} title="When something breaks" color="red">
          <ol className="ml-5 list-decimal space-y-2">
            <li>
              <strong>Don't panic.</strong> The system has hourly cloud archives, nightly email backups, and a weekly health-check email.
            </li>
            <li>
              Screenshot the error. Note what you were doing when it happened.
            </li>
            <li>
              Reach out to <strong>ForgedOps</strong>. Share the screenshot + steps.
              Most bugs are fixed in under an hour.
            </li>
            <li>
              If you lost data after a redeploy, go to <code>/admin/system</code> → <strong>Restore from Backup</strong>.
              Pick "From R2 archive" and select the most recent hourly snapshot — fastest recovery path.
            </li>
          </ol>
        </Section>

        <div className="mt-10 pt-6 border-t-2 border-slate-200 text-center text-xs font-mono uppercase tracking-[0.2em] text-slate-500">
          MASCI Operations Platform · Admin Console · Powered by ForgedOps™
        </div>
      </main>

      <style>{`
        @media print {
          code { font-size: 0.85em; }
          table { font-size: 0.9em; }
          .print\\:hidden { display: none !important; }
          .print\\:block { display: block !important; }
          .print\\:py-4 { padding-top: 1rem !important; padding-bottom: 1rem !important; }
          .print\\:px-0 { padding-left: 0 !important; padding-right: 0 !important; }
        }
      `}</style>
    </div>
  );
}

function Section({ icon: Icon, title, color, children }) {
  const colors = {
    red: { border: "border-red-700", bg: "bg-red-700", text: "text-red-900" },
    amber: { border: "border-amber-600", bg: "bg-amber-600", text: "text-amber-900" },
    slate: { border: "border-slate-800", bg: "bg-slate-800", text: "text-slate-900" },
  };
  const c = colors[color] || colors.slate;
  return (
    <section className={`mb-6 pb-5 border-l-4 ${c.border} pl-4 sm:pl-5 break-inside-avoid`}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-8 h-8 rounded ${c.bg} text-white flex items-center justify-center shrink-0`}>
          <Icon className="w-4 h-4" />
        </div>
        <h2 className={`font-display font-black text-lg sm:text-xl ${c.text}`}>{title}</h2>
      </div>
      <div className="text-slate-800 text-sm sm:text-base leading-relaxed">{children}</div>
    </section>
  );
}
