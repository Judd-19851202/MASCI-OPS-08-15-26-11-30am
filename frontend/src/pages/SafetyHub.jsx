// Safety Portal Hub — the landing dashboard after sign-in. Uses the
// same `SectionTile` component as every other hub for visual parity.
// Phase 1 ships with the Overview KPIs + Corrective Actions tile;
// future phases add Training, Fire Extinguishers, Document Library.
import React, { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  ShieldAlert, AlertOctagon, ClipboardCheck, Users, FileText,
  Award, Flame, FolderArchive, BarChart3, Loader2,
} from "lucide-react";
import { SectionTile } from "@/components/SectionTile";
import SafetyShell from "@/components/SafetyShell";
import { useT } from "@/lib/i18n";
import { isSafety, getSafetyToken, getSafetyUser } from "@/lib/safetyAuth";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function KPI({ label, value, sub, accent = "cyan" }) {
  const colors = {
    cyan: "border-cyan-700 text-cyan-900",
    red: "border-red-700 text-red-900",
    amber: "border-amber-600 text-amber-900",
    emerald: "border-emerald-700 text-emerald-900",
  };
  return (
    <div className={`bg-white border-2 ${colors[accent]} rounded-md p-4 sm:p-5`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
        {label}
      </div>
      <div className="font-display text-3xl sm:text-4xl font-black mt-1 leading-none">
        {value}
      </div>
      {sub ? <div className="text-xs text-slate-500 mt-1">{sub}</div> : null}
    </div>
  );
}

export default function SafetyHub() {
  const { t } = useT();
  const nav = useNavigate();
  const user = getSafetyUser();
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
    <SafetyShell
      title="Safety Operations Dashboard"
      kicker={`SAFETY PORTAL · ${user?.role || "SAFETY"}`}
    >
      {/* KPI strip — reads existing collections, no duplicate forms */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 mb-8">
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
            <KPI label={t("Incidents · 7d")} value={kpis.incidents_last_7d ?? 0} accent="red" sub={t("Last 7 days")} />
            <KPI label={t("Meetings · 7d")} value={kpis.meetings_last_7d ?? 0} accent="emerald" sub={t("Toolbox + huddles")} />
            <KPI label={t("Inspections · 30d")} value={kpis.inspections_last_30d ?? 0} sub={t("Last 30 days")} />
            <KPI label={t("CA · Open")} value={kpis.corrective_actions_open ?? 0} accent="amber" sub={t("Awaiting close-out")} />
            <KPI label={t("CA · Overdue")} value={kpis.corrective_actions_overdue ?? 0} accent="red" sub={t("Past due date")} />
            <KPI label={t("Training Deficiencies")} value={kpis.training_deficiencies_total ?? 0} sub={t("Field Leadership records")} />
            <KPI label={t("PPE Issuances")} value={kpis.safety_equipment_issuances_total ?? 0} sub={t("Equipment Accountability")} />
          </>
        )}
      </div>

      {/* Module tiles — use the shared SectionTile component so this
          matches every other Hub in the system pixel-for-pixel. */}
      <h2 className="font-display text-xl sm:text-2xl font-black tracking-tight text-slate-900 mb-3">
        {t("Modules")}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        <SectionTile
          to="/safety-portal/corrective-actions"
          icon={AlertOctagon}
          title={t("Corrective Actions")}
          desc={t("Open → In Progress → Pending Review → Closed. Track every safety deficiency to resolution. Auto-link to incidents, audits, inspections, and training records.")}
          accent="red"
          ctaLabel={t("Open")}
          testId="safety-tile-ca"
        />
        <SectionTile
          to="/safety-portal/incidents"
          icon={ClipboardCheck}
          title={t("Incidents & Near Misses")}
          desc={t("Read-only roll-up of every incident report filed from the field. Filter by severity, project, employee, and date.")}
          accent="amber"
          ctaLabel={t("Coming soon")}
          disabled
          disabledLabel={t("Phase 2 visibility — coming next")}
          testId="safety-tile-incidents"
        />
        <SectionTile
          to="/safety-portal/audits"
          icon={ShieldAlert}
          title={t("Audits & Inspections")}
          desc={t("Site safety audits and jobsite inspections — same records the field submits, organized for Safety review and close-out.")}
          accent="emerald"
          ctaLabel={t("Coming soon")}
          disabled
          disabledLabel={t("Phase 2 visibility — coming next")}
          testId="safety-tile-audits"
        />
        <SectionTile
          to="/safety-portal/training"
          icon={Award}
          title={t("Training & Certifications")}
          desc={t("Employee certifications, training records, expiration tracking, sign-in sheets, and renewal alerts.")}
          accent="indigo"
          ctaLabel={t("Coming soon")}
          disabled
          disabledLabel={t("Phase 4 — coming after Fire Ext + Docs")}
          testId="safety-tile-training"
        />
        <SectionTile
          to="/safety-portal/employees"
          icon={Users}
          title={t("Employee Safety Profiles")}
          desc={t("Per-employee roll-up: trainings, certs, meeting attendance, incident involvement, retraining, and PPE issuance.")}
          accent="slate"
          ctaLabel={t("Coming soon")}
          disabled
          disabledLabel={t("Phase 4 — coming after Fire Ext + Docs")}
          testId="safety-tile-employees"
        />
        <SectionTile
          to="/safety-portal/fire-extinguishers"
          icon={Flame}
          title={t("Fire Extinguishers")}
          desc={t("Monthly inspections, due-date tracking, pass/fail records, and unit-level history per truck / job / facility.")}
          accent="redDeep"
          ctaLabel={t("Coming soon")}
          disabled
          disabledLabel={t("Phase 3 — coming after Corrective Actions")}
          testId="safety-tile-extinguishers"
        />
        <SectionTile
          to="/safety-portal/documents"
          icon={FolderArchive}
          title={t("Safety Document Library")}
          desc={t("OSHA records, SDS, emergency action plans, competent-person docs, fall-protection training, sign-in sheets, and more.")}
          accent="cyan"
          ctaLabel={t("Coming soon")}
          disabled
          disabledLabel={t("Phase 3 — coming after Corrective Actions")}
          testId="safety-tile-docs"
        />
        <SectionTile
          to="/safety-portal/reports"
          icon={BarChart3}
          title={t("Reports & Exports")}
          desc={t("OSHA 300, insurance summaries, trend reports, executive roll-ups, and project safety flags.")}
          accent="purple"
          ctaLabel={t("Coming soon")}
          disabled
          disabledLabel={t("Phase 5 — coming after Training rollup")}
          testId="safety-tile-reports"
        />
        <SectionTile
          to="/safety-portal/change-password"
          icon={FileText}
          title={t("Change Password")}
          desc={t("Update your Safety Portal password. Required for first login after Admin issues a temp password.")}
          accent="slate"
          ctaLabel={t("Open")}
          testId="safety-tile-changepw"
        />
      </div>
    </SafetyShell>
  );
}
