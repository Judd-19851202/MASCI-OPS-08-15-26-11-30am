import React from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, Printer, ClipboardCheck, Users, AlertOctagon, ClipboardList,
  Wrench, Mail, ShieldCheck, HardDrive, QrCode, HelpCircle,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { Button } from "@/components/ui/button";

/**
 * AdminGuide — plain-English, print-friendly owner's manual for the MASCI
 * Safety Hub. Accessible at /admin/guide. Crews never see this page.
 *
 * After the MASCI Hub rebrand the structure is now:
 *   🦺 Safety  — inspections, meetings, incidents, JHA, trench box
 *   👷 Field   — daily reports, equipment pre-op
 *   🏗️ Projects — Crew Hub (sign-in required)
 *   🗄️ Admin   — this console
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
        <Section icon={ShieldCheck} title="The 4 sections of MASCI Hub" color="slate">
          <p>Open <code>mascidocs.com</code> and you'll see 4 big tiles. Here's who uses which:</p>
          <ul className="ml-5 list-disc space-y-1 mt-2">
            <li>🦺 <strong>Safety</strong> — Compliance forms. Inspections · Meetings · Incidents · JHA Plans · Trench Box Data.</li>
            <li>👷 <strong>Field</strong> — Daily operational logs. Daily Reports · Equipment Pre-Op.</li>
            <li>🏗️ <strong>Projects</strong> — Crew Hub. Per-job messages, to-dos, schedule, docs, hill charts. Sign-in required.</li>
            <li>🗄️ <strong>Admin</strong> — Office console. Everything in this manual below.</li>
          </ul>
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

        {/* BACKUP */}
        <Section icon={HardDrive} title="Backups — how to never lose data" color="slate">
          <p className="font-bold text-slate-900 mb-2">Good news: a full backup lands in your inbox every night.</p>
          <p>Each night at 2 AM UTC (10 PM ET), the system builds a complete <code>.zip</code> of everything and emails it to <strong>jaymn.judd@mascigc.com</strong>. Keep those emails. That's your off-site archive.</p>

          <div className="mt-4 bg-red-50 border-l-4 border-red-700 p-3 rounded-r">
            <div className="font-bold text-red-900 uppercase text-sm tracking-wide">⚠ Before any Emergent redeploy</div>
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
            <li><code>crew_hub/</code> — all messages, to-dos, schedule, docs, hill charts</li>
            <li><code>safety_aux/</code> — equipment registry, JHA plans, trench-box data</li>
            <li><code>backup_log.txt</code> — human-readable manifest of how many of each thing was saved</li>
            <li><code>backup_manifest.json</code> — machine-readable version used by Restore</li>
          </ul>
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
                <td className="p-2 border border-slate-300 text-xs">Your developer updates <code>ADMIN_PASSWORD</code> in Emergent env vars</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300">Site Inspection form</td>
                <td className="p-2 border border-slate-300 font-mono">1982</td>
                <td className="p-2 border border-slate-300 text-xs">Hardcoded gate — prevents randos submitting</td>
              </tr>
              <tr>
                <td className="p-2 border border-slate-300">Crew Hub <code>/app</code></td>
                <td className="p-2 border border-slate-300 font-mono">Welcome2MASCI!</td>
                <td className="p-2 border border-slate-300 text-xs">Each user changes on first login</td>
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
              Reach out to your developer (Emergent chat). Share the screenshot + steps.
              Most bugs are fixed in under an hour.
            </li>
            <li>
              If you lost data after a redeploy, use the <strong>Restore From File</strong> button
              with the most recent nightly backup email.
            </li>
          </ol>
        </Section>

        <div className="mt-10 pt-6 border-t-2 border-slate-200 text-center text-xs font-mono uppercase tracking-[0.2em] text-slate-500">
          MASCI · Accountability · Adapt · Overcome
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
