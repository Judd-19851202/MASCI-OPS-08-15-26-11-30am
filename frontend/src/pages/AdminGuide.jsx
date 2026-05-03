import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, Printer, ClipboardCheck, Users, AlertOctagon, ClipboardList,
  Wrench, Mail, ShieldCheck, HardDrive, QrCode, HelpCircle, Truck,
  TrendingUp, Building2, ListChecks,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { Button } from "@/components/ui/button";

/**
 * AdminGuide — plain-English, print-friendly owner's manual for the MASCI
 * Safety Hub. Accessible at /admin/guide. Crews never see this page.
 *
 * After the MASCI Hub rebrand the structure is now:
 *   🦺 Safety   — inspections, meetings, incidents, JHP, trench box
 *   👷 Field    — daily reports, equipment pre-op
 *   🏗️ Basecamp  — external link to live MASCI Basecamp (project comms)
 *   📍 OnStation — external link to OnStation (field staking)
 *   🗄️ Admin    — this console
 *   🔧 Shop     — mechanic console
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
            <ArrowLeft className="w-4 h-4" /> Admin Hub
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
              <div className="font-black text-lg">MASCI Hub</div>
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
            when you're out. You do not need to understand any code to run MASCI Hub.
          </p>
        </div>

        {/* STRUCTURE */}
        <Section icon={ShieldCheck} title="The MASCI Hub at a glance" color="slate">
          <p>Open <code>mascidocs.com</code> and you'll see the main tiles. Here's who uses which:</p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li>🦺 <strong>Safety</strong> — Compliance forms. Inspections · Meetings · Incidents · JHP Plans · Trench Box Data.</li>
            <li>👷 <strong>Field</strong> — Daily operational logs. Daily Reports · Equipment Pre-Op.</li>
            <li>🏗️ <strong>Basecamp</strong> — Opens our live Basecamp account in a new tab. Project messages, to-dos, schedules, docs, and hill charts all live in Basecamp now.</li>
            <li>📍 <strong>OnStation</strong> — Opens OnStation in a new tab for field staking, station mapping, and GPS coordination.</li>
            <li>🗄️ <strong>Admin</strong> — Office console. Everything in this manual below.</li>
            <li>🔧 <strong>Shop</strong> — Mechanic console. Equipment list, Pre-Op trends, Sign-off.</li>
          </ul>
          <p className="mt-3 text-xs text-slate-500"><em>The in-app Crew Hub project workspace was retired on 2026-04-28 — we now use Basecamp for project comms and OnStation for field staking. Both open in a new tab from the Hub home.</em></p>
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
          <p>Sign in at <code>mascidocs.com/admin</code> with password <code className="font-bold">Happy123!</code>. You'll see:</p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li><strong>6 module tiles</strong> showing how many records are on file. Click any tile to view / print / delete.</li>
            <li><strong>Auto-Email Routing panel</strong> — confirms which PM gets which job's reports.</li>
            <li><strong>Equipment Status Board</strong> — every piece of equipment with pass/fail history.</li>
            <li><strong>Compliance Export</strong> — date-range CSVs per module for OSHA / DOT audits.</li>
          </ul>
        </Section>

        {/* PROJECT P&L */}
        <Section icon={TrendingUp} title="Project P&L Snapshot — live job-cost dashboard" color="amber">
          <p>
            On <code>/admin</code> click the <strong>Project P&amp;L Snapshot</strong> tile (top-left) —
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
            Three uploadable lists feed every dropdown across the platform. All three live on{" "}
            <code>/admin</code> right under the Backup panel:
          </p>
          <ul className="ml-5 list-disc space-y-2 mt-2">
            <li>
              <strong className="flex items-center gap-1.5"><Truck className="w-4 h-4" /> Equipment Master Fleet</strong>
              <br />Upload your master <code>Equipment List.xlsx</code> (Louis sheet). Auto-categorizes by
              prefix (DPT-, EXC-, LDR-, etc.). Feeds Equipment Pre-Op + Daily Report Equipment Log.
              Today: <strong>589 units</strong>.
            </li>
            <li>
              <strong className="flex items-center gap-1.5"><Users className="w-4 h-4" /> Employee Roster</strong>
              <br />Upload .xlsx or .csv with at least a <code>Name</code> column (extra columns
              like Trade, Crew, Email all welcome but optional). Feeds the searchable employee picker
              in Daily Report Section 04 (Crew on Site), Site Inspection (operator), Incident
              (witnesses, supervisor), Equipment Pre-Op (operator). Today: <strong>234 names</strong>.
            </li>
            <li>
              <strong className="flex items-center gap-1.5"><Building2 className="w-4 h-4" /> Supplier &amp; Subcontractor List</strong>
              <br />Upload .xlsx or .csv with company names in the first column. Feeds the searchable
              supplier picker in Daily Report Section 05 (Subcontractors) + Section 08 (Material
              Deliveries). Today: <strong>145 entries</strong>.
            </li>
          </ul>
          <p className="mt-3">
            <strong>Operators can always type free-text</strong> if a name/equipment/supplier isn't
            in the list yet — nothing blocks them in the field. Then you re-upload the master file
            when convenient.
          </p>
        </Section>

        {/* EQUIPMENT FLEET (legacy section — keep for clarity) */}
        <Section icon={Truck} title="Updating the equipment fleet" color="amber">
          <p>Every equipment dropdown in the Hub (Pre-Op, Daily Reports, etc.)
            is fed by a single master list parsed from your <code>Equipment List.xlsx</code>.</p>
          <ol className="ml-5 list-decimal space-y-1 mt-2">
            <li>Open <code>/admin</code> and find the <strong>MASCI Equipment Master Fleet</strong> panel near the top.</li>
            <li>Click <strong>PICK .XLSX</strong> and choose your latest copy.</li>
            <li>Done — the count + last-updated stamp refresh on screen, and every form picks up the new units instantly.</li>
          </ol>
          <p className="mt-3 text-sm">
            By default the parser reads the <strong>Louis</strong> sheet (the master list).
            Operators can still type custom equipment that isn't in the file as a fallback.
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
            <div className="font-bold text-amber-900 uppercase text-sm tracking-wide">Shop Console (separate login)</div>
            <p className="text-amber-900 text-sm mt-1">
              Mechanics get their own focused console at <code>/shop</code> — Pre-Op trends, open
              items, recent inspections, and the full equipment list. Same sign-off endpoint;
              they don't see incidents / dailies / meetings / inspections / settings.
              Default password: <strong>Nothappy123!</strong> (changeable via <code>SHOP_PASSWORD</code>
              env var). Admins automatically have shop access through their admin token.
            </p>
          </div>
        </Section>

        {/* BACKUP */}
        <Section icon={HardDrive} title="Backups — how to never lose data" color="slate">
          <p className="font-bold text-slate-900 mb-2">Good news: a full backup lands in your inbox every night.</p>
          <p>Each night at 2 AM UTC (10 PM ET), the system builds a complete <code>.zip</code> of everything and emails it to <strong>jaymn.judd@mascigc.com</strong>. Keep those emails. That's your off-site archive.</p>

          <div className="mt-4 bg-red-50 border-l-4 border-red-700 p-3 rounded-r">
            <div className="font-bold text-red-900 uppercase text-sm tracking-wide">⚠ Before any production redeploy</div>
            <p className="text-red-900 text-sm mt-1">
              Open <code>/admin</code>, scroll to the <strong>Backup &amp; Restore</strong> box at the top,
              click the big <strong>BACKUP EVERYTHING</strong> button. Wait 30 seconds. The .zip will email you AND
              download to your computer simultaneously. Then redeploy.
            </p>
          </div>

          <div className="mt-4 bg-emerald-50 border-l-4 border-emerald-700 p-3 rounded-r">
            <div className="font-bold text-emerald-900 uppercase text-sm tracking-wide">If data is missing after a deploy</div>
            <ol className="text-emerald-900 text-sm mt-1 ml-5 list-decimal space-y-1">
              <li>Open your inbox → search <em>"MASCI Nightly Backup"</em> → download the most recent .zip.</li>
              <li>Go to <code>/admin</code> → find the <strong>BACKUP &amp; RESTORE</strong> box → click <strong>RESTORE FROM FILE</strong>.</li>
              <li>Pick the .zip, confirm. Wait 30 seconds. Done.</li>
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
          <p className="mt-3 text-xs text-slate-500"><em>Older backups (pre-2026-04-28) also contain a <code>crew_hub/</code> folder with the in-app Crew Hub messages, to-dos, schedule, docs, and hill charts. New backups skip that folder since the Crew Hub was retired in favor of Basecamp.</em></p>
          <p className="mt-3 font-semibold">
            The .zip is <strong>not encrypted</strong> — anyone with the file can read it. Treat it like a payroll binder:
            keep it somewhere only authorized office staff can access.
          </p>
        </Section>

        {/* PASSWORDS */}
        <Section icon={ShieldCheck} title="Passwords" color="slate">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="bg-slate-100">
                <th className="text-left p-2 border border-slate-300">What</th>
                <th className="text-left p-2 border border-slate-300">Password</th>
                <th className="text-left p-2 border border-slate-300">Where to change</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="p-2 border border-slate-300">Admin console <code>/admin</code></td>
                <td className="p-2 border border-slate-300 font-mono">Happy123!</td>
                <td className="p-2 border border-slate-300 text-xs">Your developer updates <code>ADMIN_PASSWORD</code> in the production deploy env vars</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300">Site Inspection form</td>
                <td className="p-2 border border-slate-300 font-mono">1982</td>
                <td className="p-2 border border-slate-300 text-xs">Hardcoded gate — prevents randos submitting</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300">Shop console <code>/shop</code></td>
                <td className="p-2 border border-slate-300 font-mono">Nothappy123!</td>
                <td className="p-2 border border-slate-300 text-xs">Developer updates <code>SHOP_PASSWORD</code> in the production deploy env vars</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300">Basecamp / OnStation</td>
                <td className="p-2 border border-slate-300 font-mono text-xs">— external —</td>
                <td className="p-2 border border-slate-300 text-xs">Sign in on the vendor site (basecamp.com / onstation.us). Not managed here.</td>
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
          </ul>
          <p className="mt-3">See the <em>Auto-Email Routing</em> panel on <code>/admin</code> for the full job-to-PM table.</p>
        </Section>

        {/* SHARE FORMS */}
        <Section icon={QrCode} title="Sharing forms with the field" color="red">
          <p>Every form has a public submit URL + QR code. From each module dashboard (<code>/admin/inspections</code>, etc.) click the <strong>Share</strong> button to see the QR code.</p>
          <p className="mt-2">There are also <strong>printable wall posters</strong>:</p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li>Crew Cheat Sheet — tape in every trailer</li>
            <li>Job Hazard Plans QR — tape next to the plans binder</li>
            <li>Trench Box QR — tape on the trench box</li>
          </ul>
          <p className="mt-2">
            Print all 3 at once from <code>/admin</code> → <strong>Site Posters</strong> panel → <strong>Print All Posters</strong>.
          </p>
        </Section>

        {/* WHEN THINGS BREAK */}
        <Section icon={AlertOctagon} title="When something breaks" color="red">
          <ol className="ml-5 list-decimal space-y-2">
            <li>
              <strong>Don't panic.</strong> Every bit of data is backed up every night.
            </li>
            <li>
              Screenshot the error. Note what you were doing when it happened.
            </li>
            <li>
              Reach out to <strong>The Judd Group</strong>. Share the screenshot + steps.
              Most bugs are fixed in under an hour.
            </li>
            <li>
              If you lost data after a redeploy, use the <strong>Restore From File</strong> button
              with the most recent nightly backup email.
            </li>
          </ol>
        </Section>

        <div className="mt-10 pt-6 border-t-2 border-slate-200 text-center text-xs font-mono uppercase tracking-[0.2em] text-slate-500">
          MASCI · Admin Console
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
