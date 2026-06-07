// Phase 10D · Linked Excavation Compliance Summary.
// Pulls a linked excavation record by ID (public auth-less GET only works
// for Safety/Admin; for foreman view, we use the same data already on
// the daily report and run the Phase 10C engine against it).
import React, { useEffect, useState } from "react";
import { ShieldCheck, OctagonAlert, AlertTriangle, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { computeExcavationCompliance } from "@/lib/excavationCompliance";

const STATUS_PALETTE = {
  "Ready":           { bg: "bg-emerald-50 border-emerald-400 text-emerald-900", icon: ShieldCheck,    chip: "bg-emerald-700" },
  "Submitted":       { bg: "bg-emerald-50 border-emerald-400 text-emerald-900", icon: ShieldCheck,    chip: "bg-emerald-700" },
  "Needs Review":    { bg: "bg-amber-50 border-amber-400 text-amber-900",       icon: AlertTriangle,  chip: "bg-amber-700" },
  "Action Required": { bg: "bg-red-50 border-red-400 text-red-900",             icon: OctagonAlert,   chip: "bg-red-700" },
};

async function _loadExcavation(excId) {
  try {
    const r = await api.get(`/trench-safety/excavations/${excId}`);
    return r.data || null;
  } catch { return null; }
}

export default function LinkedExcavationCompliance({ excavationId, testId }) {
  const { t } = useT();
  const [state, setState] = useState({ doc: null, loading: true });
  const { doc, loading } = state;

  useEffect(() => {
    if (!excavationId) return undefined;
    let alive = true;
    _loadExcavation(excavationId).then((d) => { if (alive) setState({ doc: d, loading: false }); });
    return () => { alive = false; };
  }, [excavationId]);

  if (!excavationId) return null;
  const tid = testId || `linked-exc-${excavationId}`;
  if (loading) return <div className="bg-slate-100 border border-slate-200 rounded p-2 text-xs text-slate-500" data-testid={tid}>{t("Loading")} {excavationId}…</div>;
  if (!doc) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded p-2 text-xs text-slate-700" data-testid={tid}>
        <span className="font-mono font-bold">{excavationId}</span>
        <span className="ml-2 text-slate-500">{t("Compliance view requires Safety/Admin sign-in.")}</span>
      </div>
    );
  }

  // Re-run the same Phase 10C engine against the stored record so the
  // status the foreman sees here matches the status the excavation form
  // shows. The doc's persisted `status` is used as a fallback for the
  // banner color when the engine reports Ready but the persisted status
  // is more severe (e.g. Action Required from prior flags).
  const live = computeExcavationCompliance(doc);
  const palette = STATUS_PALETTE[doc.status] || STATUS_PALETTE[live.status] || STATUS_PALETTE["Needs Review"];
  const Icon = palette.icon;

  return (
    <div className={`border rounded p-2 text-xs ${palette.bg}`} data-testid={tid}>
      <div className="flex items-start gap-2">
        <Icon className="w-4 h-4 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono font-black text-base">{doc.id}</span>
            <span className={`text-[10px] font-bold uppercase tracking-[0.12em] text-white px-1.5 py-0.5 rounded ${palette.chip}`}>{t(doc.status)}</span>
            <span className="text-[10px] opacity-80">{doc.date_of_work}</span>
          </div>
          <div className="text-[11px] mt-0.5">
            {[doc.project_name, doc.depth_ft && `${doc.depth_ft} ft`, doc.soil_classification, doc.protective_system]
              .filter(Boolean).join(" · ")}
          </div>
          {doc.competent_person_name && (
            <div className="text-[11px] mt-0.5">{t("CP:")} <b>{doc.competent_person_name}</b></div>
          )}
          {(doc.assigned_asset_ids?.length || doc.road_plate_ids?.length) > 0 && (
            <div className="text-[11px] mt-0.5 inline-flex flex-wrap gap-1">
              {(doc.assigned_asset_ids || []).map((a) => <span key={a} className="bg-white border border-slate-300 px-1 py-0.5 rounded font-mono">{a}</span>)}
              {(doc.road_plate_ids || []).map((a) => <span key={a} className="bg-white border border-amber-300 px-1 py-0.5 rounded font-mono">{a}</span>)}
            </div>
          )}
          {/* Live engine output (top 2) */}
          {live.requirements.length > 0 && (
            <ul className="mt-1.5 space-y-0.5">
              {live.requirements.slice(0, 2).map((r) => (
                <li key={r.id} className="text-[11px] flex items-start gap-1" data-testid={`${tid}-req-${r.id}`}>
                  <ChevronRight className="w-3 h-3 mt-0.5 shrink-0" />
                  <span><b>{t(r.title)}</b> — {t(r.action || r.why)}</span>
                </li>
              ))}
              {live.requirements.length > 2 && (
                <li className="text-[11px] opacity-70">+{live.requirements.length - 2} {t("more in the excavation record")}</li>
              )}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
