// Trench Safety Hub (dashboard landing). Live counts from the
// /api/trench-safety/dashboard endpoint (Phase 2 backend).
//
// Phase 3 · MASCI Trench Safety Operations System.
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ShieldAlert, Wrench, Boxes, FileWarning, ScanLine, AlertTriangle, Loader2,
  Plus, Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import TrenchSafetyShell from "@/pages/trench_safety/TrenchSafetyShell";
import { DailyPosturePanel } from "@/pages/trench_safety/TrenchSafetyOpsCenter";
import {
  QuickAddAssetDialog,
  OperationalSummaryPanel,
  CSVImportDialog,
} from "@/pages/trench_safety/TrenchSafetyPolish";
import { TrenchSafetyPulseCard } from "@/pages/trench_safety/TrenchSafetyPulse";

function KPI({ label, value, sub, valueClass = "text-slate-900", testId }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-4" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className={`font-display text-3xl sm:text-4xl font-black mt-1 leading-none ${valueClass}`}>
        {value}
      </div>
      {sub ? <div className="text-xs text-slate-500 mt-1">{sub}</div> : null}
    </div>
  );
}

function AlertRow({ icon: Icon, color, label, count, testId }) {
  const dim = count === 0;
  return (
    <div
      data-testid={testId}
      className={
        "flex items-center justify-between gap-3 px-3 py-2 rounded border " +
        (dim ? "bg-slate-50 border-slate-200" : `bg-${color}-50 border-${color}-300`)
      }
    >
      <span className="inline-flex items-center gap-2">
        <Icon className={`w-4 h-4 ${dim ? "text-slate-400" : `text-${color}-700`}`} />
        <span className={`text-sm font-bold ${dim ? "text-slate-500" : `text-${color}-900`}`}>{label}</span>
      </span>
      <span className={`font-mono text-sm font-black ${dim ? "text-slate-400" : `text-${color}-900`}`}>
        {count}
      </span>
    </div>
  );
}

export default function TrenchSafetyHub() {
  const { t } = useT();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [csvOpen, setCsvOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get("/trench-safety/dashboard");
        if (!cancelled) setData(r.data || null);
      } catch (e) {
        if (!cancelled) setErr(e?.response?.data?.detail || e?.message || "Unable to load dashboard");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [reloadKey]);

  const counts_status = data?.counts_by_status || {};
  const counts_type = data?.counts_by_type || {};
  const counts_cond = data?.counts_by_condition || {};
  const alerts = data?.alerts || {};

  return (
    <TrenchSafetyShell active="hub">
      <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mb-1" data-testid="trench-hub-title">
        {t("Trench Safety")}
      </h1>
      <p className="text-slate-600 text-sm max-w-3xl">
        {t("Operational hub for every MASCI trench safety asset — inspections, holds, repairs, tabulated data, and field QR access. Real counts from the platform — no static numbers.")}
      </p>

      <div className="bg-amber-50 border border-amber-300 rounded-md p-3 mt-5 flex items-start gap-2" data-testid="trench-hub-coaching">
        <ShieldAlert className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
        <p className="text-sm text-amber-900">
          <strong>{t("Coaching:")}</strong>{" "}
          {t("Match the box to the correct tabulated data before use. If the serial plate or tabulated data is missing, stop and contact Safety. A box on Inspection Hold is not available for use.")}
        </p>
      </div>

      {/* Phase 8B — Quick Add + CSV Import actions */}
      <div className="mt-4 flex flex-wrap gap-2" data-testid="trench-hub-actions">
        <Button onClick={() => setQuickAddOpen(true)} className="bg-cyan-700 hover:bg-cyan-800" data-testid="trench-hub-quick-add">
          <Plus className="w-4 h-4 mr-1" /> {t("Quick Add Asset")}
        </Button>
        <Button onClick={() => setCsvOpen(true)} variant="outline" data-testid="trench-hub-csv-import">
          <Upload className="w-4 h-4 mr-1" /> {t("Import CSV")}
        </Button>
      </div>
      <QuickAddAssetDialog open={quickAddOpen} onOpenChange={setQuickAddOpen} onCreated={() => setReloadKey((k) => k + 1)} />
      <CSVImportDialog open={csvOpen} onOpenChange={setCsvOpen} onImported={() => setReloadKey((k) => k + 1)} />

      {loading ? (
        <div className="flex items-center gap-2 mt-8 text-slate-500" data-testid="trench-hub-loading">
          <Loader2 className="w-5 h-5 animate-spin" />
          {t("Loading dashboard…")}
        </div>
      ) : err ? (
        <div className="mt-8 p-4 border border-red-300 bg-red-50 rounded text-red-900 text-sm" data-testid="trench-hub-error">
          {t("Unable to load dashboard.")} {err}
        </div>
      ) : (
        <>
          {/* Phase 7.5B — Daily Posture Dashboard (top of portal, no scrolling) */}
          <section className="mt-2" data-testid="trench-hub-posture">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
              {t("Daily Posture")}
            </div>
            <DailyPosturePanel />
          </section>

          {/* Phase 8C — Trench Safety Pulse (Operational Intelligence) */}
          <section className="mt-6" data-testid="trench-hub-pulse">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
              {t("Operational Intelligence")}
            </div>
            <TrenchSafetyPulseCard />
          </section>

          {/* Phase 8B — Executive Operational Summary */}
          <section className="mt-6" data-testid="trench-hub-ops-summary">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
              {t("Executive Summary")}
            </div>
            <OperationalSummaryPanel assetsBasePath="/safety/trench-safety/assets" />
          </section>

          {/* Headline KPIs */}
          <section className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="trench-hub-kpis">
            <KPI label={t("Active Assets")} value={data.total_active_assets ?? 0} testId="kpi-active" />
            <KPI label={t("Available")} value={counts_status["Available"] ?? 0} testId="kpi-available" />
            <KPI label={t("Inspection Hold")} value={counts_status["Inspection Hold"] ?? 0} valueClass={(counts_status["Inspection Hold"] ?? 0) > 0 ? "text-amber-700" : "text-slate-900"} testId="kpi-hold" />
            <KPI label={t("Open Repairs")} value={alerts.open_repairs ?? 0} valueClass={(alerts.open_repairs ?? 0) > 0 ? "text-red-700" : "text-slate-900"} testId="kpi-repairs" />
          </section>

          {/* Type / condition / status detail */}
          <section className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-4" data-testid="trench-hub-breakdowns">
            <div className="bg-white border border-slate-200 rounded-md p-4">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2">{t("By Type")}</div>
              <ul className="text-sm divide-y divide-slate-100">
                {Object.entries(counts_type).map(([k, v]) => (
                  <li key={k} className="flex justify-between py-1">
                    <span className={v === 0 ? "text-slate-400" : "text-slate-800"}>{t(k)}</span>
                    <span className={`font-mono ${v === 0 ? "text-slate-400" : "text-slate-900 font-bold"}`}>{v}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-white border border-slate-200 rounded-md p-4">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2">{t("By Status")}</div>
              <ul className="text-sm divide-y divide-slate-100">
                {Object.entries(counts_status).map(([k, v]) => (
                  <li key={k} className="flex justify-between py-1">
                    <span className={v === 0 ? "text-slate-400" : "text-slate-800"}>{t(k)}</span>
                    <span className={`font-mono ${v === 0 ? "text-slate-400" : "text-slate-900 font-bold"}`}>{v}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-white border border-slate-200 rounded-md p-4">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2">{t("By Condition")}</div>
              <ul className="text-sm divide-y divide-slate-100">
                {Object.entries(counts_cond).map(([k, v]) => (
                  <li key={k} className="flex justify-between py-1">
                    <span className={v === 0 ? "text-slate-400" : "text-slate-800"}>{t(k)}</span>
                    <span className={`font-mono ${v === 0 ? "text-slate-400" : "text-slate-900 font-bold"}`}>{v}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* Alerts strip */}
          <section className="mt-6" data-testid="trench-hub-alerts">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2">
              {t("Alerts")}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              <AlertRow icon={FileWarning}    color="amber"   label={t("Missing Serial Number")}  count={alerts.missing_serial_number ?? 0} testId="alert-missing-sn" />
              <AlertRow icon={FileWarning}    color="amber"   label={t("Missing Manufacturer")}   count={alerts.missing_manufacturer ?? 0} testId="alert-missing-mfr" />
              <AlertRow icon={AlertTriangle}  color="amber"   label={t("Needs Review")}            count={alerts.needs_review ?? 0}          testId="alert-needs-review" />
              <AlertRow icon={Wrench}         color="red"     label={t("Open Repairs")}           count={alerts.open_repairs ?? 0}          testId="alert-open-repairs" />
              <AlertRow icon={ShieldAlert}    color="amber"   label={t("Inspections Due")}        count={alerts.inspections_due ?? 0}       testId="alert-insp-due" />
              <AlertRow icon={Boxes}          color="amber"   label={t("Missing Tabulated Data")} count={alerts.missing_tabulated_data ?? 0} testId="alert-missing-tabdata" />
            </div>
          </section>

          {/* Quick links */}
          <section className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="trench-hub-quicklinks">
            <Link to="/safety/trench-safety/assets" className="bg-white border border-slate-200 rounded-md p-4 hover:border-cyan-600 hover:shadow transition" data-testid="ql-equipment">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold">{t("Open")}</div>
              <div className="font-display text-xl font-black text-slate-900 mt-1">{t("Trench Equipment")}</div>
              <div className="text-xs text-slate-600 mt-1">{t("Filterable list of every MASCI trench safety asset.")}</div>
            </Link>
            <Link to="/safety/trench-safety/tabulated-data" className="bg-white border border-slate-200 rounded-md p-4 hover:border-cyan-600 hover:shadow transition" data-testid="ql-tabdata">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold">{t("Open")}</div>
              <div className="font-display text-xl font-black text-slate-900 mt-1">{t("Tabulated Data")}</div>
              <div className="text-xs text-slate-600 mt-1">{t("OSHA tabulated data PDFs · per-box folders + general library.")}</div>
            </Link>
          </section>

          {/* In-progress strip */}
          <section className="mt-6 p-3 border border-slate-200 bg-slate-50 rounded text-xs text-slate-600" data-testid="trench-hub-roadmap">
            <strong className="text-slate-700">{t("Coming in later certified phases:")}</strong>{" "}
            {t("Inspections workflow · Repairs workflow · Certifications · Deployments history · Reports · QR PNG label generator · OCR for serial plates.")}
          </section>
        </>
      )}
    </TrenchSafetyShell>
  );
}
