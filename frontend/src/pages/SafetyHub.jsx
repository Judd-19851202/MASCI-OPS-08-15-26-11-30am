// Safety Portal Hub — landing dashboard after sign-in.
//
// iter318 · Safety Hub Calm Pass (Platform UX Governance Phase A · iter318)
// Applies the iter317-C HR pattern: calm tile chrome (left-edge stripe,
// white background, lg headings), grouped operational sections, neutral
// KPI strip, integration cards demoted to the bottom Guidance & Systems
// section. NO sidebar · NO IA redesign · NO route changes · NO permission
// changes · NO new features. All 15 tile testids + SafetyShell chrome
// preserved.
//
// Tile groupings (operator-approved · UX_REFINEMENT_ROADMAP iter318):
//   01 · Primary Safety Operations
//   02 · Compliance & Records
//   03 · Operational Output
//   04 · Guidance & Systems  (visually demoted · top-border separator)

import React, { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import axios from "axios";
import {
  ShieldAlert, AlertOctagon, ClipboardCheck, Users, FileText,
  Award, Flame, FolderArchive, BarChart3, Loader2, Mail, GraduationCap, Truck, BookOpen, Package,
} from "lucide-react";
import SafetyShell from "@/components/SafetyShell";
import IntegrationHealthCard from "@/components/IntegrationHealthCard";
import IntegrationEventsCard from "@/components/IntegrationEventsCard";
import { useT } from "@/lib/i18n";
import { isSafety, getSafetyToken } from "@/lib/safetyAuth";
import { usePageTitle } from "@/lib/usePageTitle";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// ─── Calm KPI (UX_GOVERNANCE_RULES Rule 5) ───────────────────────────────
//
// Neutral chrome. Optional colored value text for emphasis. No
// `border-2`, no colored backgrounds. KPIs inform — they do not dominate.
function KPI({ label, value, sub, valueClass = "text-slate-900" }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
        {label}
      </div>
      <div className={`font-display text-3xl sm:text-4xl font-black mt-1 leading-none ${valueClass}`}>
        {value}
      </div>
      {sub ? <div className="text-xs text-slate-500 mt-1">{sub}</div> : null}
    </div>
  );
}

// ─── Calm Tile (UX_GOVERNANCE_RULES Rule 1) ──────────────────────────────
//
// Left-edge accent stripe + soft slate border + white background. The
// accent identifies the tile's semantic role without competing with the
// operational content.
const STRIPE = {
  red:     "border-l-red-600",
  redDeep: "border-l-red-900",
  amber:   "border-l-amber-500",
  emerald: "border-l-emerald-600",
  cyan:    "border-l-cyan-600",
  indigo:  "border-l-indigo-600",
  slate:   "border-l-slate-500",
  purple:  "border-l-purple-600",
};
const BTN = {
  red:     "bg-red-700 hover:bg-red-800",
  redDeep: "bg-red-900 hover:bg-red-950",
  amber:   "bg-amber-700 hover:bg-amber-800",
  emerald: "bg-emerald-700 hover:bg-emerald-800",
  cyan:    "bg-cyan-700 hover:bg-cyan-800",
  indigo:  "bg-indigo-700 hover:bg-indigo-800",
  slate:   "bg-slate-700 hover:bg-slate-800",
  purple:  "bg-purple-700 hover:bg-purple-800",
};

function SafetyTile({ to, icon: Icon, title, desc, accent = "cyan", ctaLabel = "OPEN", testId }) {
  const stripe = STRIPE[accent] || STRIPE.cyan;
  const btn = BTN[accent] || BTN.cyan;
  return (
    <Link
      to={to}
      className={`block rounded-lg border border-slate-200 border-l-4 ${stripe} bg-white p-5 hover:shadow-md hover:-translate-y-0.5 hover:border-slate-300 transition-all duration-150 relative`}
      data-testid={testId}
    >
      <div className="flex items-start gap-3">
        <Icon className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
        <div className="flex-1 min-w-0">
          <h3 className="font-display text-lg font-black">{title}</h3>
          <p className="text-sm text-slate-600 mt-1">{desc}</p>
          <span className={`mt-3 inline-flex items-center h-9 px-3 rounded-md ${btn} text-white font-bold uppercase tracking-wide text-xs`}>
            {ctaLabel} →
          </span>
        </div>
      </div>
    </Link>
  );
}

// ─── Section heading (UX_GOVERNANCE_RULES Rule 3) ────────────────────────
//
// Mono kicker · thin divider · italic muted subtitle. Demoted sections
// (e.g. Guidance & Systems) get slate-500 + a top-border separator above.
function SectionHeading({ title, sub, muted = false, testId }) {
  return (
    <div className="mb-4 flex items-baseline gap-3 flex-wrap">
      <h2
        className={`font-mono text-xs uppercase tracking-[0.22em] ${muted ? "text-slate-500" : "text-slate-700"}`}
        data-testid={testId}
      >
        {title}
      </h2>
      <span className="hidden sm:inline-block h-px flex-1 bg-slate-200" aria-hidden="true" />
      <span className="text-xs text-slate-500 italic">{sub}</span>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────

export default function SafetyHub() {
  usePageTitle("Safety · MASCI");
  const { t } = useT();
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isSafety()) return;
    let alive = true;
    (async () => {
      try {
        const r = await axios.get(`${API}/safety/overview`, {
          headers: { "X-Safety-Token": getSafetyToken() },
        });
        if (alive) setKpis(r.data);
      } catch (e) {
        if (alive) setKpis({ error: true });
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (!isSafety()) {
    return <Navigate to="/safety-portal/login" replace />;
  }

  return (
    <SafetyShell title="Safety Operations Dashboard" kicker="SAFETY PORTAL">
      {/* KPI strip — neutral chrome per Rule 5. Colored value text for
          incident/CA emphasis; everything else stays calm. */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-10" data-testid="safety-kpi-strip">
        {loading ? (
          <div className="col-span-full text-center py-8 text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" /> {t("Loading metrics…")}
          </div>
        ) : kpis?.error ? (
          <div className="col-span-full text-center py-8 text-red-700">
            {t("Could not load metrics. Sign out and back in.")}
          </div>
        ) : (
          <>
            <KPI label={t("Incidents (Total)")} value={kpis.incidents_total ?? 0} sub={t("All time")} />
            <KPI label={t("Incidents · 7d")} value={kpis.incidents_last_7d ?? 0} sub={t("Last 7 days")} valueClass="text-red-700" />
            <KPI label={t("Meetings · 7d")} value={kpis.meetings_last_7d ?? 0} sub={t("Toolbox + huddles")} valueClass="text-emerald-700" />
            <KPI label={t("Inspections · 30d")} value={kpis.inspections_last_30d ?? 0} sub={t("Last 30 days")} />
            <KPI label={t("CA · Open")} value={kpis.corrective_actions_open ?? 0} sub={t("Awaiting close-out")} valueClass="text-amber-700" />
            <KPI label={t("CA · Overdue")} value={kpis.corrective_actions_overdue ?? 0} sub={t("Past due date")} valueClass="text-red-700" />
            <KPI label={t("Training Deficiencies")} value={kpis.training_deficiencies_total ?? 0} sub={t("Field Leadership records")} />
            <KPI label={t("PPE Issuances")} value={kpis.safety_equipment_issuances_total ?? 0} sub={t("Equipment Accountability")} />
          </>
        )}
      </div>

      {/* ─── Group 01 · Primary Safety Operations ─────────────────────── */}
      <section data-testid="safety-group-primary" className="mb-10">
        <SectionHeading
          title={t("Primary Safety Operations")}
          sub={t("Day-to-day safety workflows")}
          testId="safety-group-heading-primary"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <SafetyTile
            to="/tasks"
            icon={ClipboardCheck}
            title={t("Tasks & Actions")}
            desc={t("Cross-portal accountability engine. Track corrective actions, follow-ups, deficiencies, and approvals to closure.")}
            accent="amber"
            ctaLabel={t("OPEN")}
            testId="safety-tile-tasks"
          />
          <SafetyTile
            to="/safety-portal/corrective-actions"
            icon={AlertOctagon}
            title={t("Corrective Actions")}
            desc={t("Open → In Progress → Pending Review → Closed. Track every safety deficiency to resolution. Auto-link to incidents, audits, inspections, and training records.")}
            accent="red"
            ctaLabel={t("OPEN")}
            testId="safety-tile-ca"
          />
          <SafetyTile
            to="/safety-portal/incidents"
            icon={ClipboardCheck}
            title={t("Incidents & Near Misses")}
            desc={t("Read-only roll-up of every incident report filed from the field. Filter by severity, project, employee, and date.")}
            accent="red"
            ctaLabel={t("OPEN")}
            testId="safety-tile-incidents"
          />
          <SafetyTile
            to="/safety-portal/audits"
            icon={ShieldAlert}
            title={t("Audits & Inspections")}
            desc={t("Review every Job Site Safety Inspection submitted from the field · filter, search, drill in · start a new inspection from the same page.")}
            accent="emerald"
            ctaLabel={t("OPEN")}
            testId="safety-tile-audits"
          />
        </div>
      </section>

      {/* ─── Group 02 · Compliance & Records ──────────────────────────── */}
      <section data-testid="safety-group-compliance" className="mb-10">
        <SectionHeading
          title={t("Compliance & Records")}
          sub={t("Training, certifications, documents, expirations")}
          testId="safety-group-heading-compliance"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <SafetyTile
            to="/document-expirations"
            icon={ClipboardCheck}
            title={t("Document Expirations")}
            desc={t("Training certifications, competent-person docs, fall protection, CPR/First Aid — visibility before they lapse.")}
            accent="amber"
            ctaLabel={t("OPEN")}
            testId="safety-tile-expirations"
          />
          <SafetyTile
            to="/safety-portal/training"
            icon={Award}
            title={t("Training & Certifications")}
            desc={t("Employee certifications, training records, expiration tracking, sign-in sheets, and renewal alerts.")}
            accent="cyan"
            ctaLabel={t("OPEN")}
            testId="safety-tile-training"
          />
          <SafetyTile
            to="/safety-portal/employees"
            icon={Users}
            title={t("Employee Safety Profiles")}
            desc={t("Per-employee roll-up: trainings, certs, meeting attendance, incident involvement, retraining, and PPE issuance.")}
            accent="slate"
            ctaLabel={t("OPEN")}
            testId="safety-tile-employees"
          />
          <SafetyTile
            to="/safety-portal/fire-extinguishers"
            icon={Flame}
            title={t("Fire Extinguishers")}
            desc={t("Monthly inspections, due-date tracking, pass/fail records, and unit-level history per truck / job / facility.")}
            accent="redDeep"
            ctaLabel={t("OPEN")}
            testId="safety-tile-extinguishers"
          />
          {/* iter323 · Safety Forms ownership closure — review surface
              for Equipment Issuance + Use & Care Training records. Lets
              Safety see every form submission tied to an employee, with
              filters by employee/project/date and drill-in to detail. */}
          <SafetyTile
            to="/safety-portal/forms-records"
            icon={Package}
            title={t("Equipment & PPE Accountability")}
            desc={t("Review every Equipment Issuance and Use & Care Training submission — per-employee chain of custody, returns, damages, and chargebacks.")}
            accent="cyan"
            ctaLabel={t("OPEN")}
            testId="safety-tile-forms-records"
          />
          <SafetyTile
            to="/safety-portal/documents"
            icon={FolderArchive}
            title={t("Safety Document Library")}
            desc={t("OSHA records, SDS, emergency action plans, competent-person docs, fall-protection training, sign-in sheets, and more.")}
            accent="cyan"
            ctaLabel={t("OPEN")}
            testId="safety-tile-docs"
          />
        </div>
      </section>

      {/* ─── Group 03 · Operational Output ────────────────────────────── */}
      <section data-testid="safety-group-output" className="mb-10">
        <SectionHeading
          title={t("Operational Output")}
          sub={t("Digests, reports, topic prep, fleet visibility")}
          testId="safety-group-heading-output"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <SafetyTile
            to="/safety-portal/digest"
            icon={Mail}
            title={t("Weekly Digest")}
            desc={t("Monday-morning email digest of open CAs, overdue items, 7-day incidents, and 30-day training expirations. Preview anytime or send on demand.")}
            accent="emerald"
            ctaLabel={t("OPEN")}
            testId="safety-tile-digest"
          />
          <SafetyTile
            to="/safety-portal/reports"
            icon={BarChart3}
            title={t("Reports & Exports")}
            desc={t("OSHA 300, insurance summaries, trend reports, executive roll-ups, and project safety flags.")}
            accent="slate"
            ctaLabel={t("OPEN")}
            testId="safety-tile-reports"
          />
          <SafetyTile
            to="/safety-portal/library"
            icon={BookOpen}
            title={t("Topic Library · Operational Prep")}
            desc={t("Filter the 136-topic safety library by severity and domain · build a multi-topic PDF pack for kickoffs, mobilizations, and high-risk job prep. Internal use only.")}
            accent="amber"
            ctaLabel={t("OPEN LIBRARY")}
            testId="safety-tile-topic-library"
          />
          <SafetyTile
            to="/safety-portal/fleet"
            icon={Truck}
            title={t("Trucking · Fleet")}
            desc={t("See defects grouped by truck · driver notes · current status · severity context. Mobile-friendly · operational clarity only.")}
            accent="amber"
            ctaLabel={t("OPEN FLEET VIEW")}
            testId="safety-tile-fleet"
          />
        </div>
      </section>

      {/* ─── Group 04 · Guidance & Systems (DEMOTED) ──────────────────── */}
      {/*
         Per UX_GOVERNANCE_RULES Rule 6: integrations + guidance must
         support the hub, not compete with operational workflows. Rendered
         with a top-border separator and muted slate-500 heading.
      */}
      <section
        data-testid="safety-group-systems"
        className="pt-6 border-t border-slate-200"
      >
        <SectionHeading
          title={t("Guidance & Systems")}
          sub={t("Supporting tools · operator guides · cross-portal integration visibility")}
          muted
          testId="safety-group-heading-systems"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <SafetyTile
            to="/guidance?from=safety"
            icon={GraduationCap}
            title={t("Training Center & Guides")}
            desc={t("Step-by-step operator guides for Safety Portal workflows — Corrective Actions, Incidents, Fire Extinguisher Bulk Import, Weekly Digest. Download any guide as PDF.")}
            accent="slate"
            ctaLabel={t("OPEN")}
            testId="safety-tile-training-center"
          />
          <SafetyTile
            to="/safety-portal/change-password"
            icon={FileText}
            title={t("Change Password")}
            desc={t("Update your Safety Portal password. Required for first login after Admin issues a temp password.")}
            accent="slate"
            ctaLabel={t("OPEN")}
            testId="safety-tile-changepw"
          />
        </div>

        {/* Integration health + Motive events — neutral chrome, lives
            inside the demoted Systems group so it never competes with
            the operational sections above. */}
        <div
          className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6"
          data-testid="safety-integrations-strip"
        >
          <IntegrationHealthCard
            tokenHeader={{ "X-Safety-Token": getSafetyToken() }}
            accent="cyan"
            showAdminLink={false}
          />
          <IntegrationEventsCard
            provider="motive"
            tokenHeader={{ "X-Safety-Token": getSafetyToken() }}
            accent="cyan"
          />
        </div>
      </section>
    </SafetyShell>
  );
}
