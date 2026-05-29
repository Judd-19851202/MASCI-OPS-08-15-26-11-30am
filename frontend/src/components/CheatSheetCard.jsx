import React from "react";
import { QRCodeSVG } from "qrcode.react";
import {
  HardHat, ClipboardCheck, Shield, ClipboardList, Wrench, Users,
  UserCheck, Building2,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { useT } from "@/lib/i18n";

/**
 * Crew Field Card — printable single-page poster for every job trailer.
 *
 * Iter77 rebuild:
 *  - Re-titled "MASCI Operations Platform · Field Card" (was the
 *    safety-only "Crew Cheat Sheet · Field Safety Reporting Portal").
 *  - Removed safety@mascigc.com per owner request. Office phone only.
 *  - Surface the FULL platform — 3 submission tiles (Field / QA-QC /
 *    Safety) + 4 office-portal pills (PM / Shop / HR / Field Leadership).
 *  - Keep Stop-the-Line emergency steps and "Tips for Everyone".
 *  - Footer matches the iter74/76 brand standard:
 *    "MASCI Operations Platform · Powered by ForgedOps™".
 */

export default function CheatSheetCard() {
  const { t } = useT();
  const hubUrl = "https://mascidocs.com/";

  const submissionTiles = [
    {
      icon: HardHat,
      eyebrow: t("Step into the Hub"),
      title: t("Field"),
      body: t(
        "Daily Reports · Equipment Pre-Op walk-arounds. GPS auto-fills location, weather auto-loads, photos in two taps.",
      ),
      accent: "amber",
    },
    {
      icon: ClipboardCheck,
      eyebrow: t("Quality & Compliance"),
      title: t("QA / QC"),
      body: t(
        "Concrete · Rebar · Subcontractor Inspections. Sign on screen, submit, instant PDF + record.",
      ),
      accent: "emerald",
    },
    {
      icon: Shield,
      eyebrow: t("Safety & Stop-the-Line"),
      title: t("Safety"),
      body: t(
        "Inspections · Toolbox Talks · Incidents · JHPs · Trench Box reference. Routed to the office in 60 seconds.",
      ),
      accent: "red",
    },
  ];

  const officePortals = [
    {
      icon: ClipboardList,
      title: t("PM Portal"),
      body: t("Project managers · active jobs · routing · fleet · staff."),
      accent: "indigo",
    },
    {
      icon: Wrench,
      title: t("Shop"),
      body: t("Mechanics · out-of-service queue · Pre-Op FAILs · sign-offs."),
      accent: "orange",
    },
    {
      icon: Users,
      title: t("HR Portal"),
      body: t("Employee accountability · time verification · payroll cross-check."),
      accent: "purple",
    },
    {
      icon: UserCheck,
      title: t("Field Leadership"),
      body: t("Supervisor forms · crew accountability · equipment checkout."),
      accent: "slate",
    },
  ];

  return (
    <div className="bg-white border-2 border-slate-300 print:border-0 rounded-md p-8 sm:p-10 print:p-8 shadow-xl print:shadow-none">
      {/* Top banner */}
      <div className="flex items-start justify-between gap-6 pb-6 border-b-4 border-red-700">
        <div className="flex-1">
          <MasciLogo variant="mark" size="2xl" onLight homeLink="/" />
          <div className="mt-3 font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-bold">
            {t("MASCI Operations Platform · Field Card")}
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
            {t("Office")}
          </div>
          <div className="font-display font-black text-slate-900 text-xl leading-none mt-1">
            386-322-4500
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">
            mascidocs.com
          </div>
        </div>
      </div>

      {/* Hero */}
      <div className="grid grid-cols-1 sm:grid-cols-[auto,1fr] gap-6 mt-7 items-center">
        <div className="bg-slate-900 p-4 rounded-md inline-flex items-center justify-center">
          <QRCodeSVG
            value={hubUrl}
            size={170}
            bgColor="#0F172A"
            fgColor="#FFFFFF"
            level="M"
            marginSize={1}
            data-testid="cheatsheet-qr"
          />
        </div>
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-bold">
            {t("Scan to start")}
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 leading-[0.95] mt-2">
            {t("Run every job. Control every detail.")}
          </h1>
          <p className="text-slate-700 text-base mt-3 leading-relaxed">
            {t(
              "Open your camera, point it at the QR code, tap the link. MASCI Operations Platform opens in your browser. No login for field forms. No app to install. Add it to your home screen and you're set.",
            )}
          </p>
        </div>
      </div>

      {/* Submit on Site — 3 tiles */}
      <SectionHeader kicker="01" title={t("Submit on Site")} subtitle={t("Public · no sign-in required.")} />
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-7">
        {submissionTiles.map((tile) => (
          <TileCard key={tile.title} {...tile} />
        ))}
      </div>

      {/* Office Portals — 4 pills */}
      <SectionHeader kicker="02" title={t("Office Portals")} subtitle={t("Sign-in required. Office staff, mechanics, HR.")} />
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-7">
        {officePortals.map((p) => (
          <PortalPillPrint key={p.title} {...p} />
        ))}
      </div>

      {/* Tips + Stop-the-Line */}
      <SectionHeader kicker="03" title={t("Field Tips & Emergency Steps")} subtitle={t("Memorize these.")} />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div className="bg-slate-50 print:bg-white border border-slate-200 rounded-md p-5">
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-slate-700 font-black">
            {t("Tips for Everyone")}
          </div>
          <ul className="mt-3 space-y-2 text-slate-800 text-[13px] leading-relaxed">
            <li>
              <span className="font-black text-red-700">·</span>{" "}
              {t(
                "Use the ES button to switch any form to Spanish — it submits in English automatically.",
              )}
            </li>
            <li>
              <span className="font-black text-red-700">·</span>{" "}
              {t("Daily Reports require")} <strong>{t("at least 6 photos")}</strong>
              {t(". Take them as you walk the site.")}
            </li>
            <li>
              <span className="font-black text-red-700">·</span>{" "}
              {t("Add the Hub to your home screen so it opens with one tap.")}
            </li>
            <li>
              <span className="font-black text-red-700">·</span>{" "}
              {t("If GPS doesn't grab, type the address in the Location field — same result.")}
            </li>
            <li>
              <span className="font-black text-red-700">·</span>{" "}
              <strong>{t("Doc ID:")}</strong>{" "}
              {t(
                "Every submission gets a unique tracking number printed on the PDF (e.g. DR-2026-00042). Read it back when the office calls — they find it instantly.",
              )}
            </li>
            <li>
              <span className="font-black text-red-700">·</span>{" "}
              <strong>{t("Pre-Op FAILs")}</strong>{" "}
              {t(
                "auto-email every active mechanic and the parts office in 60 seconds. No need to call separately.",
              )}
            </li>
          </ul>
        </div>

        <div className="bg-red-50 border-2 border-red-700 rounded-md p-5">
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-red-700 font-black">
            {t("Stop-the-line · Accidents & Injuries")}
          </div>
          <ol className="mt-3 space-y-2 text-slate-900 text-[13px] leading-relaxed list-decimal list-inside">
            <li>
              <strong>{t("Make the scene safe")}</strong>{" "}
              {t("and get any injured worker medical attention.")}
            </li>
            <li>
              <strong>{t("Call the office immediately")}</strong>{" "}
              <span className="font-mono font-black">386-322-4500</span>.
            </li>
            <li>
              {t("Open the")} <strong>{t("Incident Report")}</strong>{" "}
              {t("form on the Hub and fill it out as soon as the scene is stable.")}
            </li>
            <li>
              {t("Then complete your")} <strong>{t("Daily Report")}</strong>{" "}
              {t(
                "— it will prompt you to confirm the office was notified and the Incident Report was filed before you can submit.",
              )}
            </li>
          </ol>
        </div>
      </div>

      {/* Training & Help mini-strip */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        <div className="border border-slate-200 rounded-md p-3 flex items-center gap-3 bg-slate-50 print:bg-white">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white shrink-0">
            <Building2 className="w-5 h-5" />
          </div>
          <div className="text-[13px] text-slate-800 leading-snug">
            <div className="font-bold">{t("Training Hub")}</div>
            {t("Short bilingual lessons for every role — open mascidocs.com/training.")}
          </div>
        </div>
        <div className="border border-slate-200 rounded-md p-3 flex items-center gap-3 bg-slate-50 print:bg-white">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-200 text-slate-900 shrink-0">
            <span className="font-display font-black text-base">?</span>
          </div>
          <div className="text-[13px] text-slate-800 leading-snug">
            <div className="font-bold">{t("Need Help?")}</div>
            {t("Tap the Need Help tile on the Hub — office phone, address, and after-hours contact.")}
          </div>
        </div>
      </div>

      {/* Footer — matches global brand standard */}
      <div className="mt-7 pt-4 border-t-2 border-black flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="text-center sm:text-left">
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-slate-900 font-bold">
            {t("MASCI Operations Platform")}
          </div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
            {t("Powered by ForgedOps™")}
          </div>
        </div>
        <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-slate-500">
          {t("Print and post inside every site trailer.")}
        </div>
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────

function SectionHeader({ kicker, title, subtitle }) {
  return (
    <div className="flex items-baseline gap-3 mt-7 mb-3">
      <span className="font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-black">{kicker}</span>
      <span className="h-px flex-1 bg-slate-300 max-w-6" />
      <div className="flex-1 min-w-0">
        <h2 className="font-display text-lg sm:text-xl font-black tracking-tight text-slate-900">{title}</h2>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

function TileCard({ icon: Icon, eyebrow, title, body, accent }) {
  const palette = {
    amber:   { bar: "bg-amber-600",   bg: "bg-amber-600",   pill: "text-amber-800 bg-amber-100" },
    emerald: { bar: "bg-emerald-700", bg: "bg-emerald-700", pill: "text-emerald-800 bg-emerald-100" },
    red:     { bar: "bg-red-700",     bg: "bg-red-700",     pill: "text-red-800 bg-red-100" },
  }[accent] || { bar: "bg-slate-900", bg: "bg-slate-900", pill: "text-slate-700 bg-slate-100" };
  return (
    <div className="relative bg-white print:bg-white border border-slate-200 rounded-md p-4">
      <div className={`absolute top-0 left-0 right-0 h-1.5 rounded-t ${palette.bar}`} />
      <div className="flex items-start gap-3 mt-1">
        <div className={`inline-flex items-center justify-center w-10 h-10 rounded-md ${palette.bg} text-white shrink-0`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <span className={`inline-block px-2 py-0.5 rounded ${palette.pill} font-mono text-[9px] uppercase tracking-[0.2em] font-bold`}>
            {eyebrow}
          </span>
          <h3 className="font-display text-lg font-black text-slate-900 mt-1 leading-tight">{title}</h3>
          <p className="text-slate-700 text-[12px] mt-1 leading-relaxed">{body}</p>
        </div>
      </div>
    </div>
  );
}

function PortalPillPrint({ icon: Icon, title, body, accent }) {
  const palette = {
    indigo: { bg: "bg-indigo-700" },
    orange: { bg: "bg-orange-600" },
    purple: { bg: "bg-purple-700" },
    slate:  { bg: "bg-slate-900" },
  }[accent] || { bg: "bg-slate-900" };
  return (
    <div className="bg-white print:bg-white border border-slate-200 rounded-md p-3">
      <div className="flex items-start gap-2.5">
        <div className={`inline-flex items-center justify-center w-9 h-9 rounded-md ${palette.bg} text-white shrink-0`}>
          <Icon className="w-4.5 h-4.5" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-display text-sm font-black text-slate-900 leading-tight">{title}</h3>
          <p className="text-slate-700 text-[11px] mt-0.5 leading-snug">{body}</p>
        </div>
      </div>
    </div>
  );
}
