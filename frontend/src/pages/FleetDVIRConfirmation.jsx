// FleetDVIRConfirmation.jsx — iter251 Phase 2 · Calm submission outcome page.
//
// Operator philosophy: NO "FAILED · NONCOMPLIANT" tone. Three outcomes:
//   🟢 Available — All clear · ready to roll
//   🟡 Defect(s) Logged — Shop has been notified · truck still available
//   🔴 Out of Service — Repair required before return to service
//
// Reads from React Router navigation state (set by submit handler) so we
// stay on a purely public surface · no admin/dispatch token required.

import React from "react";
import { useLocation, useNavigate, useParams, Link } from "react-router-dom";
import {
  CheckCircle2, AlertOctagon, Wrench, ArrowLeft, Home, RefreshCw, Truck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { HelpTip } from "@/components/HelpTip";
import { useT } from "@/lib/i18n";

export default function FleetDVIRConfirmation() {
  const { id } = useParams();
  const loc = useLocation();
  const nav = useNavigate();
  const { t } = useT();
  const s = loc.state || {};

  // If a driver lands here directly (e.g. clicks a stale link) we fall
  // back to a calm "thanks · come back via /field" surface.
  const orphan = !s.result;

  const outcome = (() => {
    if (orphan) return null;
    if (s.outOfService) {
      return {
        tone: "oos",
        icon: AlertOctagon,
        bg: "bg-red-700",
        bgSoft: "bg-red-50",
        border: "border-red-300",
        iconColor: "text-white",
        title: t("Out of Service"),
        sub: t("Repair required before return to service."),
        explainer: t("Shop has been notified automatically. Dispatch will reassign as needed. Thank you for catching this before rolling."),
      };
    }
    if ((s.defectCount || 0) > 0) {
      return {
        tone: "monitor",
        icon: Wrench,
        bg: "bg-amber-600",
        bgSoft: "bg-amber-50",
        border: "border-amber-300",
        iconColor: "text-white",
        title: t("Defect Logged · Truck Still Available"),
        sub: t("Shop has been notified · they'll schedule a repair window."),
        explainer: t("This truck stays available for your shift. Keep an eye on the item you flagged · if anything changes, log another DVIR."),
      };
    }
    return {
      tone: "clear",
      icon: CheckCircle2,
      bg: "bg-emerald-600",
      bgSoft: "bg-emerald-50",
      border: "border-emerald-300",
      iconColor: "text-white",
      title: t("All Clear · Ready to Roll"),
      sub: t("Thanks for the walk-around. Drive safe."),
      explainer: t("Nothing flagged. Truck status is Available. Have a good shift."),
    };
  })();

  const refNum = id ? id.slice(0, 8).toUpperCase() : "";

  return (
    <div className="min-h-screen blueprint-bg" data-testid="fleet-dvir-confirmation">
      <div className="caution-stripe" />

      <header className="bg-slate-900 border-b-4 border-amber-600">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-8 py-6 sm:py-10">
        <div className="mb-4">
          <Link
            to="/field"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-amber-600 font-bold"
            data-testid="dvir-confirm-back"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Field")}
          </Link>
        </div>

        {orphan ? (
          <div className="rounded-md bg-white border-2 border-slate-300 p-6 sm:p-8 text-center">
            <Truck className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <h1 className="font-display text-2xl font-bold text-slate-900 mb-2">
              {t("DVIR submitted")}
            </h1>
            <p className="text-slate-600 text-sm mb-5">
              {t("Your inspection was received. This confirmation page only shows details right after submission · please start a fresh DVIR if you need to log another.")}
            </p>
            <Button asChild className="bg-amber-600 hover:bg-amber-700 text-white h-12">
              <Link to="/field">{t("Back to Field")}</Link>
            </Button>
          </div>
        ) : (
          <>
            {/* Outcome hero */}
            <div
              className={`rounded-lg overflow-hidden border-2 ${outcome.border}`}
              data-testid={`dvir-outcome-${outcome.tone}`}
            >
              <div className={`${outcome.bg} text-white px-5 sm:px-8 py-6 sm:py-8 flex items-start gap-4`}>
                <outcome.icon className={`w-9 h-9 sm:w-12 sm:h-12 shrink-0 ${outcome.iconColor}`} />
                <div className="min-w-0">
                  <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-white/80 font-bold">
                    {t("Submitted")} · #{refNum}
                  </div>
                  <h1 className="font-display text-2xl sm:text-3xl font-black leading-tight mt-1">
                    {outcome.title}
                  </h1>
                  <p className="text-white/90 text-sm sm:text-base mt-1.5">{outcome.sub}</p>
                </div>
              </div>
              <div className={`${outcome.bgSoft} px-5 sm:px-8 py-4 sm:py-5 text-slate-800 text-sm sm:text-[15px] leading-relaxed`}>
                {outcome.explainer}
              </div>
            </div>

            {/* Summary chip strip */}
            <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Chip label={t("Truck")} value={s.truckUnit || "—"} testId="dvir-summary-truck" />
              <Chip label={t("Defects")} value={String(s.defectCount || 0)} testId="dvir-summary-defects" />
              <Chip label={t("Status")} value={chipStatus(s.truckStatusAfter, t)} testId="dvir-summary-status" />
              <Chip label={t("Driver")} value={s.driverName || "—"} testId="dvir-summary-driver" />
            </div>

            {/* Logged defects · calm itemized list */}
            {Array.isArray(s.failedItems) && s.failedItems.length > 0 && (
              <div className="mt-6 rounded-md border border-slate-200 bg-white" data-testid="dvir-logged-defects">
                <div className="px-4 py-3 border-b border-slate-200 font-mono text-[11px] uppercase tracking-widest text-slate-600 font-bold">
                  {t("Logged for Shop")}
                </div>
                <ul className="divide-y divide-slate-100">
                  {s.failedItems.map((item, i) => {
                    const detail = s.defectDetails?.[item];
                    return (
                      <li
                        key={`${item}-${i}`}
                        className="px-4 py-3 text-sm text-slate-800"
                        data-testid={`dvir-logged-defect-${i}`}
                      >
                        <div className="font-semibold leading-snug">{item}</div>
                        {detail?.note && (
                          <div className="text-slate-600 text-[13px] mt-0.5 italic">
                            "{detail.note}"
                          </div>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Coaching · what happens next */}
            <div className="mt-6">
              <HelpTip
                kind="next"
                title={t("What happens next")}
                body={
                  outcome.tone === "oos"
                    ? t("Shop sees this truck in their queue right now. Once they repair and sign off, Dispatch re-clears the unit for service. You'll see status update on the next DVIR.")
                    : outcome.tone === "monitor"
                    ? t("Shop sees the defect on their queue. Repair gets scheduled within the operational window for the item. Drive normally until then.")
                    : t("You're good to go. Submit another DVIR at the start of your next shift.")
                }
                defaultOpen={true}
                testId="dvir-next-tip"
              />
            </div>

            {/* CTAs */}
            <div className="mt-6 flex flex-wrap gap-3" data-testid="dvir-confirm-ctas">
              <Button
                asChild
                className="h-12 px-5 bg-amber-600 hover:bg-amber-700 text-white"
              >
                <Link to="/fleet/dvir/new" data-testid="dvir-confirm-new">
                  <RefreshCw className="w-4 h-4 mr-1.5" />
                  {t("Start another DVIR")}
                </Link>
              </Button>
              <Button asChild variant="outline" className="h-12 px-5 border-2">
                <Link to="/field" data-testid="dvir-confirm-field">
                  <ArrowLeft className="w-4 h-4 mr-1.5" />
                  {t("Back to Field")}
                </Link>
              </Button>
              <Button asChild variant="ghost" className="h-12 px-3 text-slate-600">
                <Link to="/" data-testid="dvir-confirm-home">
                  <Home className="w-4 h-4 mr-1.5" />
                  {t("Home")}
                </Link>
              </Button>
            </div>
          </>
        )}
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500 border-t-2 border-slate-200">
        {t("MASCI · Trucking · DVIR")}
      </footer>
    </div>
  );
}

function Chip({ label, value, testId }) {
  return (
    <div
      className="bg-white border border-slate-200 rounded-md px-3 py-2.5"
      data-testid={testId}
    >
      <div className="font-mono text-[10px] uppercase tracking-widest text-slate-500 font-bold">
        {label}
      </div>
      <div className="font-display text-base sm:text-lg font-bold text-slate-900 mt-0.5 truncate">
        {value}
      </div>
    </div>
  );
}

function chipStatus(status, t) {
  if (!status) return "—";
  const map = {
    available: t("Available"),
    defect_open: t("Defect Logged"),
    oos: t("Out of Service"),
    unknown: t("Unknown"),
  };
  return map[status] || status;
}
