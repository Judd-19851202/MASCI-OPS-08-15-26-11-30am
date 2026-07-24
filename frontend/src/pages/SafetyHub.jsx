// Safety Portal Hub — landing dashboard after sign-in.
//
// iter437 · Phase IV-BETA.5A · Safety Hub V2 calmness tuning.
//
// Reduces the 9-hue Hub palette to a 4-domain doctrine palette
// (red · cyan · violet · slate) per SAFETY_INFORMATION_PRIORITY_MAP.json.
// Single neutral slate-800 CTA across every tile (HR P1B trim pattern).
// Coaching sublines trimmed to ≤14 words. True urgency stays
// unmistakable — red is RESERVED for the Incidents & Escalation domain
// + severity pills + severe-tier banners (see SAFETY_ESCALATION_HIERARCHY
// _MAP.md §III + §VI).
//
// Doctrine preserved: Sidebar V2 is now the DEFAULT layout (iter437
// IV-BETA.5A-P6) with `?safetySidebarV2=0`, localStorage, and env
// escape hatches preserved. NO IA changes · NO route changes · NO
// permission changes · NO new features. All 15 tile testids and
// SafetyShell chrome preserved.
//
// Tile groupings (4-domain priority map · iter437 IV-BETA.5A):
//   01 · Incidents & Escalation  (red)
//   02 · Documents & Training    (cyan)
//   03 · Compliance & Records    (violet)
//   04 · Audits & Guidance       (slate · demoted)

import React, { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import axios from "axios";
import {
  ShieldAlert, AlertOctagon, ClipboardCheck, Users, FileText,
  Award, Flame, FolderArchive, BarChart3, Loader2, Mail, GraduationCap, Truck, BookOpen, Package, Boxes,
} from "lucide-react";
import SafetyShell from "@/components/SafetyShell";
import IntegrationHealthCard from "@/components/IntegrationHealthCard";
import IntegrationEventsCard from "@/components/IntegrationEventsCard";
import { useT } from "@/lib/i18n";
import { isSafety, getSafetyToken } from "@/lib/safetyAuth";
import { usePageTitle } from "@/lib/usePageTitle";
import { PasskeyEnrollPrompt } from "@/components/auth/PasskeyEnrollPrompt";
import { FieldMemoryGlance } from "@/components/field_memory/FieldMemoryGlance";
import LastActivityLine from "@/components/admin/LastActivityLine";
import GovernanceHealthChip from "@/components/GovernanceHealthChip";
import ExpirationsSummary from "@/components/ExpirationsSummary";
import OperationsActionsTile from "@/components/oa/OperationsActionsTile";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

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
// iter437 IV-BETA.5A · 4-domain doctrine palette per
// SAFETY_INFORMATION_PRIORITY_MAP.json. Legacy accent keys (red/redDeep
// /amber/emerald/cyan/indigo/slate/purple) remap onto the 4-domain
// stripes so existing tile call-sites stay working while the visual
// surface collapses to red · cyan · violet · slate.
//
// All Hub CTA buttons share the single neutral slate-800 colour
// (HR P1B trim pattern). Red is RESERVED for severity pills + severe-
// tier banners — never decorative.
const STRIPE = {
  // 4-domain doctrine palette
  incidents:  "border-l-red-700",   // the ONE red domain
  documents:  "border-l-cyan-700",  // Safety brand chrome
  compliance: "border-l-violet-600",
  audits:     "border-l-slate-500",
  // ── legacy aliases (back-compat for existing accent= values) ──────
  red:     "border-l-red-700",
  redDeep: "border-l-red-700",
  amber:   "border-l-violet-600",   // demoted: amber → compliance domain
  emerald: "border-l-slate-500",    // demoted: emerald → guidance/audits
  cyan:    "border-l-cyan-700",
  indigo:  "border-l-violet-600",
  slate:   "border-l-slate-500",
  purple:  "border-l-violet-600",
};

// Single neutral CTA across all Hub tiles. Reserves true colour for
// severity pills and severe-tier banners — see SAFETY_ESCALATION_
// HIERARCHY_MAP.md §IV. The accent prop is intentionally unused for
// CTA colour now — the stripe carries the domain identity.
const CTA_NEUTRAL = "bg-slate-800 hover:bg-slate-900";

function SafetyTile({ to, icon: Icon, title, desc, accent = "cyan", ctaLabel = "OPEN", testId, badge }) {
  const stripe = STRIPE[accent] || STRIPE.documents;
  return (
    <Link
      to={to}
      className={`block rounded-lg border border-slate-200 border-l-4 ${stripe} bg-white p-5 hover:shadow-md hover:-translate-y-0.5 hover:border-slate-300 transition-all duration-150 relative`}
      data-testid={testId}
    >
      <div className="flex items-start gap-3">
        <Icon className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-display text-lg font-black">{title}</h3>
            {/* iter324 · Optional passive accountability badge.
                Subtle amber count + label. Quiet by design — must
                NEVER become a warning beacon or pulse animation. */}
            {badge && badge.count > 0 && (
              <span
                className="inline-flex items-center gap-1 px-2 h-5 rounded-full border border-yellow-400 bg-yellow-50 text-yellow-900 font-mono text-[10px] tracking-wide uppercase shrink-0"
                title={badge.tooltip || ""}
                data-testid={`${testId}-aging-badge`}
              >
                <span className="font-bold tabular-nums">{badge.count}</span>
                <span className="font-semibold">{badge.label}</span>
              </span>
            )}
          </div>
          <p className="text-sm text-slate-600 mt-1">{desc}</p>
          <span className={`mt-3 inline-flex items-center h-9 px-3 rounded-md ${CTA_NEUTRAL} text-white font-bold uppercase tracking-wide text-xs`}>
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
  // iter324 · accountability aging signal — count of issuances that are
  // (a) still out, (b) > 90 days old, and (c) include at least one
  // serialized/recoverable PPE class. Consumable PPE never raises.
  const [agingCount, setAgingCount] = useState(0);

  useEffect(() => {
    if (!isSafety()) return;
    let alive = true;
    (async () => {
      try {
        const r = await axios.get(`${API}/safety/overview`, {
          headers: buildScopedPortalAuthHeaders(["safety"]),
        });
        if (alive) setKpis(r.data);
      } catch (e) {
        if (alive) setKpis({ error: true });
      } finally {
        if (alive) setLoading(false);
      }
    })();
    // Parallel · accountability aging fetch. Independent of overview;
    // failure is silent (badge simply stays at 0).
    (async () => {
      try {
        const { isAgingAccountability } = await import("@/lib/safetyAccountabilityClass");
        const resp = await axios.get(`${API}/safety-forms/equipment-issuances`, {
          headers: buildScopedPortalAuthHeaders(["safety"]),
        });
        const list = Array.isArray(resp.data?.items) ? resp.data.items : [];
        const count = list.filter((rec) => isAgingAccountability(rec, 90)).length;
        if (alive) setAgingCount(count);
      } catch (e) {
        if (alive) setAgingCount(0);
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
      <div className="-mt-4 mb-6">
        <GovernanceHealthChip portal="safety" />
      </div>
      {/* iter429 · Phase 28 · Optional device sign-in enrollment ·
          self-gated · dismissible · single-card · NEVER nags */}
      <div className="mb-6">
        <PasskeyEnrollPrompt />
      </div>

      {/* iter432 · Phase 30 · Part 6 · Option iii · ONE calm additive
          operational-attention surface — read-only Field Memory glance. */}
      <div className="mb-6">
        <FieldMemoryGlance />
      </div>

      {/* iter440 · calm "Last activity" trace. */}
      <div className="mb-6">
        <LastActivityLine portal="safety" />
      </div>

      {/* Sprint A · DocExp-60/90 · Safety-scoped certification expirations */}
      <div className="mb-6" data-testid="safety-expirations-section">
        <ExpirationsSummary title="Training & Certification Expirations" />
      </div>

      {/* OA-1 · Operations Actions cross-portal tile */}
      <div className="mb-6" data-testid="safety-oa-tile">
        <OperationsActionsTile />
      </div>

      {/* KPI strip — neutral chrome per Rule 5. Colored value text for
          incident/CA emphasis; everything else stays calm. */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 sm:gap-4 mb-10" data-testid="safety-kpi-strip">
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
            desc={t("Cross-portal accountability. Track corrective actions, follow-ups, deficiencies, approvals.")}
            accent="incidents"
            ctaLabel={t("OPEN")}
            testId="safety-tile-tasks"
          />
          <SafetyTile
            to="/safety-portal/corrective-actions"
            icon={AlertOctagon}
            title={t("Corrective Actions")}
            desc={t("Open, investigate, verify, close. Linked to incidents, audits, training.")}
            accent="incidents"
            ctaLabel={t("OPEN")}
            testId="safety-tile-ca"
          />
          <SafetyTile
            to="/safety-portal/incidents"
            icon={ClipboardCheck}
            title={t("Incidents & Near Misses")}
            desc={t("Severity-tagged review of every field report. Filter by project, employee, date.")}
            accent="incidents"
            ctaLabel={t("OPEN")}
            testId="safety-tile-incidents"
          />
          <SafetyTile
            to="/safety-portal/audits"
            icon={ShieldAlert}
            title={t("Audits & Inspections")}
            desc={t("Review every job-site inspection. Filter, search, drill in, or start new.")}
            accent="audits"
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
            desc={t("Training certifications, competent-person docs, fall protection, CPR/First Aid windows.")}
            accent="compliance"
            ctaLabel={t("OPEN")}
            testId="safety-tile-expirations"
          />
          <SafetyTile
            to="/safety-portal/training"
            icon={Award}
            title={t("Training & Certifications")}
            desc={t("Certifications, training records, expirations, sign-in sheets, renewal reminders.")}
            accent="documents"
            ctaLabel={t("OPEN")}
            testId="safety-tile-training"
          />
          <SafetyTile
            to="/safety-portal/employees"
            icon={Users}
            title={t("Employee Safety Profiles")}
            desc={t("Per-employee training, certs, meetings, incidents, retraining, PPE issuance.")}
            accent="documents"
            ctaLabel={t("OPEN")}
            testId="safety-tile-employees"
          />
          <SafetyTile
            to="/safety-portal/fire-extinguishers"
            icon={Flame}
            title={t("Fire Extinguishers")}
            desc={t("Monthly inspections, due-date tracking, pass/fail records, per-unit history.")}
            accent="compliance"
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
            desc={t("Issuance, returns, damages, chargebacks. Per-employee chain of custody review.")}
            accent="documents"
            ctaLabel={t("OPEN")}
            testId="safety-tile-forms-records"
            badge={
              agingCount > 0
                ? {
                    count: agingCount,
                    label: t("aging"),
                    tooltip: t(
                      "Serialized / recoverable PPE issued more than 90 days ago without a return logged. Consumable PPE excluded."
                    ),
                  }
                : null
            }
          />
          <SafetyTile
            to="/safety-portal/documents"
            icon={FolderArchive}
            title={t("Safety Document Library")}
            desc={t("OSHA, SDS, emergency action plans, competent-person docs, fall-protection records.")}
            accent="documents"
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
            desc={t("Monday email summarising open CAs, overdue items, recent incidents, expirations.")}
            accent="compliance"
            ctaLabel={t("OPEN")}
            testId="safety-tile-digest"
          />
          <SafetyTile
            to="/safety-portal/reports"
            icon={BarChart3}
            title={t("Reports & Exports")}
            desc={t("OSHA 300, insurance summaries, trend reports, executive roll-ups, project flags.")}
            accent="compliance"
            ctaLabel={t("OPEN")}
            testId="safety-tile-reports"
          />
          <SafetyTile
            to="/safety-portal/library"
            icon={BookOpen}
            title={t("Topic Library · Operational Prep")}
            desc={t("Filter the 136-topic library, build a PDF pack for kickoffs and prep.")}
            accent="audits"
            ctaLabel={t("OPEN LIBRARY")}
            testId="safety-tile-topic-library"
          />
          <SafetyTile
            to="/safety-portal/fleet"
            icon={Truck}
            title={t("Trucking · Fleet")}
            desc={t("Defects grouped by truck, driver notes, current status, severity context.")}
            accent="audits"
            ctaLabel={t("OPEN FLEET VIEW")}
            testId="safety-tile-fleet"
          />
          {/* Phase 3 · Trench Safety Operations System */}
          <SafetyTile
            to="/safety/trench-safety"
            icon={Boxes}
            title={t("Trench Safety")}
            desc={t("Trench boxes, end panels, spreaders, hydraulic shores · tabulated data, inspections, holds, repairs, QR field view.")}
            accent="audits"
            ctaLabel={t("OPEN")}
            testId="safety-tile-trench-safety"
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
            desc={t("Step-by-step Safety operator guides. Download any guide as a PDF.")}
            accent="audits"
            ctaLabel={t("OPEN")}
            testId="safety-tile-training-center"
          />
          <SafetyTile
            to="/safety-portal/change-password"
            icon={FileText}
            title={t("Change Password")}
            desc={t("Update your Safety Portal password. Required after a temp-password issue.")}
            accent="audits"
            ctaLabel={t("OPEN")}
            testId="safety-tile-changepw"
          />
        </div>

        {/* Integration health + Motive events — neutral chrome, lives
            inside the demoted Systems group so it never competes with
            the operational sections above. */}
        <div
          className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4 mt-6"
          data-testid="safety-integrations-strip"
        >
          <IntegrationHealthCard
            tokenHeader={buildScopedPortalAuthHeaders(["safety"])}
            accent="cyan"
            showAdminLink={false}
          />
          <IntegrationEventsCard
            provider="motive"
            tokenHeader={buildScopedPortalAuthHeaders(["safety"])}
            accent="cyan"
          />
        </div>
      </section>
    </SafetyShell>
  );
}
