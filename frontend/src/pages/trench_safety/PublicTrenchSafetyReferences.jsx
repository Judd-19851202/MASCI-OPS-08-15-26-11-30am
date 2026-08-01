// Public Trench Safety · Safety References
//
// Sprint: Public Trench Safety UX Correction.
//
// Distinct from /trench-safety/tabulated-data. This surface holds
// OSHA / general trench safety guidance, competent-person reminders,
// unsafe-condition examples, missing-pins / missing-labels guidance,
// stop-work guidance, and safe-use reminders. Plain-English + Spanish.
//
// Route: /trench-safety/references  (public, no auth)
import React from "react";
import { Link } from "react-router-dom";
import {
  FileWarning, ShieldAlert, AlertTriangle, ScanLine, BookOpen,
  ArrowRight, OctagonAlert, HardHat, Eye, Wrench, ClipboardCheck,
  Tag, BookmarkCheck,
} from "lucide-react";
import { OperationalPageFrame } from "@/components/public/OperationalPageFrame";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import { useT } from "@/lib/i18n";

function RefCard({ icon: Icon, title, body, tone = "default", testId }) {
  const toneRing = {
    default: "border-slate-200 hover:border-cyan-600",
    danger:  "border-red-300 hover:border-red-500 bg-red-50/40",
    warn:    "border-amber-300 hover:border-amber-500 bg-amber-50/40",
  }[tone];
  const iconColor = {
    default: "text-cyan-700",
    danger: "text-red-700",
    warn:  "text-amber-700",
  }[tone];
  return (
    <div className={`bg-white border rounded-md p-4 transition ${toneRing}`} data-testid={testId}>
      <div className="flex items-start gap-2.5">
        <Icon className={`w-5 h-5 ${iconColor} mt-0.5 shrink-0`} />
        <div>
          <div className="font-display text-base font-black text-slate-900 leading-tight">{title}</div>
          <div className="text-sm text-slate-700 mt-1.5 leading-relaxed">{body}</div>
        </div>
      </div>
    </div>
  );
}

export default function PublicTrenchSafetyReferences() {
  const { t } = useT();
  return (
    <OperationalPageFrame
      testId="public-refs-page"
      backTo="/trench-safety"
      backLabel={t("Back to Trench Safety")}
      accent="amber"
      familyLabel={t("MASCI Trench Safety")}
      familyMeta={t("Public trench workflow")}
      mainWidthClass="max-w-5xl"
      heroIcon={FileWarning}
      kicker={t("MASCI Trench Safety · Field References")}
      title={t("Safety References")}
      description={t("Open the OSHA-aligned reminders crews need when conditions change: competent-person rules, unsafe-condition examples, missing-pin guidance, and stop-work standards.")}
      heroMeta={(
        <>
          <OperationalStatusBadge tone="amber" testId="public-refs-meta-stop">{t("Stop-work guidance")}</OperationalStatusBadge>
          <OperationalStatusBadge tone="cyan" testId="public-refs-meta-field">{t("Crew-safe language")}</OperationalStatusBadge>
        </>
      )}
      heroAside={(
        <div className="wp17-panel p-4" data-testid="public-refs-hero-aside">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-700 font-bold mb-2">{t("Need the engineered sheets?")}</div>
          <p className="text-sm text-slate-600 mb-3">
            {t("Use references for field judgment and tabulated data for the exact shield or panel configuration before entry.")}
          </p>
          <Link to="/trench-safety/tabulated-data" className="inline-flex items-center gap-1.5 rounded-full border border-cyan-200 bg-cyan-50 px-4 py-2 text-[11px] font-mono font-bold uppercase tracking-[0.18em] text-cyan-800" data-testid="public-refs-hero-tabdata">
            {t("Open Tabulated Data")} <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}
      footerText={t("MASCI Operations Platform · Trench reference workflow")}
    >
      <div className="space-y-5">

        <div className="rounded-[1.5rem] border-2 border-red-300 bg-red-50 p-4 flex items-start gap-3 shadow-[0_18px_40px_rgba(15,23,42,0.06)]" data-testid="public-refs-stopwork">
          <OctagonAlert className="w-5 h-5 text-red-700 mt-0.5 shrink-0" />
          <div className="text-sm text-red-900">
            <strong className="uppercase tracking-[0.1em]">{t("Stop-Work Authority.")}</strong>{" "}
            {t("Every MASCI crew member has the right and the duty to stop work for unsafe conditions. You will never be punished for stopping a job to keep someone alive. Stop. Step back. Call Safety.")}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" data-testid="public-refs-grid">
          <RefCard
            icon={HardHat}
            title={t("Competent Person Required")}
            tone="default"
            testId="public-refs-competent"
            body={t("Every trench 5 ft or deeper requires a designated competent person on-site — trained to identify hazards, authorized to correct them, and present before crews enter. No competent person, no entry.")}
          />
          <RefCard
            icon={Eye}
            title={t("Inspect Daily — and After Every Change")}
            tone="default"
            testId="public-refs-inspect"
            body={t("Inspect the trench, the box, and the surrounding area at the start of every shift, after every rain event, and after any condition that could change soil stability. Document it.")}
          />
          <RefCard
            icon={AlertTriangle}
            title={t("Unsafe Condition Examples")}
            tone="warn"
            testId="public-refs-unsafe"
            body={t("Cracks in shield panels · spreaders bent or non-original · standing water around the trench · spoil pile within 2 ft of the edge · cracks/fissures in the trench wall · undermined utilities · improper sloping or benching.")}
          />
          <RefCard
            icon={Wrench}
            title={t("Missing Pins")}
            tone="danger"
            testId="public-refs-missing-pins"
            body={t("Do not use a box with missing connector pins. Pins are engineered to the box — substitutes are not allowed. Tag the box, report the missing pin, and stage another box.")}
          />
          <RefCard
            icon={Tag}
            title={t("Missing or Illegible Labels")}
            tone="danger"
            testId="public-refs-missing-labels"
            body={t("If the manufacturer label, serial plate, or depth rating is missing or illegible, the box cannot be matched to its tabulated data. Stop. Report it. Without tabulated data the box is not OSHA-compliant for use.")}
          />
          <RefCard
            icon={ClipboardCheck}
            title={t("Safe Use Reminders")}
            tone="default"
            testId="public-refs-safe-use"
            body={t("Enter and exit through a ladder or ramp every 25 ft of trench. Keep workers out of the swing radius of the excavator. Never lift the box with workers inside. Verify spreaders before stacking.")}
          />
          <RefCard
            icon={BookmarkCheck}
            title={t("Tabulated Data Match")}
            tone="default"
            testId="public-refs-tabdata-match"
            body={
              <>
                {t("Tabulated data is specific to manufacturer, model, soil type, and spreader configuration. Confirm the sheet matches the box before use.")}{" "}
                <Link to="/trench-safety/tabulated-data" className="text-cyan-800 underline font-bold inline-flex items-center gap-0.5" data-testid="public-refs-to-tabdata">
                  {t("Open Tabulated Data")} <ArrowRight className="w-3 h-3" />
                </Link>
              </>
            }
          />
          <RefCard
            icon={ShieldAlert}
            title={t("When in Doubt — Don't")}
            tone="warn"
            testId="public-refs-doubt"
            body={t("A trench that looks 'mostly okay' has killed people. Anything that feels off — soil, water, the box, the spoil pile, the spotter — is a reason to stop. Safety beats schedule. Every time.")}
          />
        </div>

        <section className="wp17-panel p-4 text-xs text-slate-600" data-testid="public-refs-qr-help">
          <ScanLine className="w-3.5 h-3.5 inline mr-1 -mt-0.5 text-cyan-700" />
          <strong className="text-slate-700">{t("Found something wrong?")}</strong>{" "}
          <Link to="/trench-safety/report" className="text-cyan-800 underline font-bold inline-flex items-center gap-0.5 ml-1" data-testid="public-refs-to-report">
            {t("Report a Problem")} <ArrowRight className="w-3 h-3" />
          </Link>
          <span className="ml-1">{t("— it goes straight to Safety. You can also scan the box's QR code to report on the exact asset.")}</span>
        </section>

      </div>
    </OperationalPageFrame>
  );
}
