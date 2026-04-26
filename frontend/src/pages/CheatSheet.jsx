import React from "react";
import { Link } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import { Printer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";

/**
 * Crew Cheat Sheet — printable 1-page handout for foremen.
 *
 * Visit /cheatsheet, hit Print, get a single sheet that explains how to use
 * the Hub in 4 steps with a big QR code that drops them straight onto the
 * public Hub from any phone camera.
 */

export default function CheatSheet() {
  // QR points at whatever this build is currently served from — so once the
  // app is deployed at safety.mascigc.com, the QR auto-resolves there.
  const hubUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/`
      : "https://safety.mascigc.com/";

  return (
    <div className="min-h-screen blueprint-bg print:bg-white">
      <div className="caution-stripe no-print" />

      {/* On-screen toolbar */}
      <header className="bg-slate-900 border-b-4 border-red-700 no-print">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="cheatsheet-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Hub
          </Link>
          <div className="font-mono text-xs uppercase tracking-[0.25em] text-red-400">
            Crew Cheat Sheet
          </div>
          <Button
            onClick={() => window.print()}
            className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
            data-testid="cheatsheet-print-btn"
          >
            <Printer className="w-4 h-4 mr-2" /> Print
          </Button>
        </div>
      </header>

      {/* The actual printable page */}
      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 print:p-0">
        <div className="bg-white border-2 border-slate-300 print:border-0 rounded-md p-8 sm:p-12 print:p-8 shadow-xl print:shadow-none">
          {/* Top banner: logo + tagline */}
          <div className="flex items-start justify-between gap-6 pb-6 border-b-4 border-red-700">
            <div className="flex-1">
              <MasciLogo variant="lockup" size="2xl" />
              <div className="mt-3 font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-bold">
                Crew Cheat Sheet · Field Safety Reporting Portal
              </div>
            </div>
            <div className="text-right">
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
                Office
              </div>
              <div className="font-display font-black text-slate-900 text-xl leading-none mt-1">
                386-322-4500
              </div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">
                safety@mascigc.com
              </div>
            </div>
          </div>

          {/* Hero: scan-to-start */}
          <div className="grid grid-cols-1 sm:grid-cols-[auto,1fr] gap-6 mt-8 items-center">
            <div className="bg-slate-900 p-4 rounded-md inline-flex items-center justify-center">
              <QRCodeSVG
                value={hubUrl}
                size={180}
                bgColor="#0F172A"
                fgColor="#FFFFFF"
                level="M"
                marginSize={1}
                data-testid="cheatsheet-qr"
              />
            </div>
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-bold">
                Scan to start
              </div>
              <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 leading-[0.95] mt-2">
                One front door for every safety form.
              </h1>
              <p className="text-slate-700 text-base mt-3 leading-relaxed">
                Open your camera, point it at the QR code, and tap the link.
                The MASCI Safety Hub opens in your browser. No login. No app
                to install. Add it to your home screen and you're set.
              </p>
              <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-slate-500 mt-3 break-all">
                {hubUrl.replace(/^https?:\/\//, "")}
              </div>
            </div>
          </div>

          {/* Four steps */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mt-10">
            {[
              {
                n: "01",
                title: "Pick the form",
                body: "Daily Report, Site Inspection, Safety Meeting, JHA, or Incident — tap the tile.",
              },
              {
                n: "02",
                title: "Fill it on site",
                body: "GPS auto-fills location, weather auto-loads, your job is in the picker. Tap to add photos.",
              },
              {
                n: "03",
                title: "Sign + Submit",
                body: "Sign with your finger. Hit Submit. Translates Spanish to English automatically before saving.",
              },
              {
                n: "04",
                title: "Done",
                body: "Office gets the report instantly. You'll see a Thank You screen with the option to file another.",
              },
            ].map((s) => (
              <div
                key={s.n}
                className="bg-slate-50 print:bg-white border-2 border-slate-200 rounded-md p-4"
              >
                <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-red-700 font-black">
                  Step {s.n}
                </div>
                <div className="font-display text-lg font-black text-slate-900 leading-tight mt-2">
                  {s.title}
                </div>
                <div className="text-slate-700 text-sm mt-2 leading-relaxed">
                  {s.body}
                </div>
              </div>
            ))}
          </div>

          {/* Two-column rules + safety stop */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-10">
            <div className="bg-slate-50 print:bg-white border-2 border-slate-300 rounded-md p-5">
              <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-slate-700 font-black">
                Tips for Foremen
              </div>
              <ul className="mt-3 space-y-2 text-slate-800 text-sm leading-relaxed">
                <li>
                  <span className="font-black text-red-700">·</span> Use the
                  ES button to switch the form to Spanish — it submits in
                  English automatically.
                </li>
                <li>
                  <span className="font-black text-red-700">·</span> Daily
                  Reports require <strong>at least 6 photos</strong>. Take
                  them as you walk the site.
                </li>
                <li>
                  <span className="font-black text-red-700">·</span> Add the
                  Hub to your home screen so it opens with one tap.
                </li>
                <li>
                  <span className="font-black text-red-700">·</span> If GPS
                  doesn't grab, type the address in the Location field — same
                  result.
                </li>
              </ul>
            </div>

            <div className="bg-red-50 border-2 border-red-700 rounded-md p-5">
              <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-red-700 font-black">
                Stop-the-line · Accidents & Injuries
              </div>
              <ol className="mt-3 space-y-2 text-slate-900 text-sm leading-relaxed list-decimal list-inside">
                <li>
                  <strong>Make the scene safe</strong> and get any injured
                  worker medical attention.
                </li>
                <li>
                  <strong>Call Safety immediately</strong> at{" "}
                  <span className="font-mono font-black">386-322-4500</span>.
                </li>
                <li>
                  Open the <strong>Incident Report</strong> form on the Hub
                  and fill it out as soon as the scene is stable.
                </li>
                <li>
                  Then complete your <strong>Daily Report</strong> — it will
                  prompt you to confirm Safety was notified and the Incident
                  Report was filed before you can submit.
                </li>
              </ol>
            </div>
          </div>

          {/* Footer with motto */}
          <div className="mt-8 pt-5 border-t-2 border-black flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-700">
              MASCI · Field Safety Reporting Portal
            </div>
            <div className="font-display font-black text-red-700 tracking-tight text-sm">
              No Shortcuts · No Exceptions
            </div>
          </div>
        </div>
      </main>

      {/* Print-only sizing rules */}
      <style>{`
        @media print {
          @page { size: letter; margin: 0.4in; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .no-print { display: none !important; }
        }
      `}</style>
    </div>
  );
}
