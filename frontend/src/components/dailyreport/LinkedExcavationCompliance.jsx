// Phase 10D · Linked Excavation — Path A compact summary.
// One line per record. ID · status badge · depth · soil. No paragraphs.
import React, { useEffect, useState } from "react";
import { ShieldCheck, AlertTriangle, OctagonAlert } from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

const PALETTE = {
  "Submitted":       { bg: "bg-emerald-50 border-emerald-400 text-emerald-900", icon: ShieldCheck },
  "Reviewed":        { bg: "bg-emerald-50 border-emerald-400 text-emerald-900", icon: ShieldCheck },
  "Closed":          { bg: "bg-slate-50 border-slate-300 text-slate-800",       icon: ShieldCheck },
  "Needs Review":    { bg: "bg-amber-50 border-amber-400 text-amber-900",       icon: AlertTriangle },
  "Action Required": { bg: "bg-red-50 border-red-400 text-red-900",             icon: OctagonAlert },
  "Reopened":        { bg: "bg-red-50 border-red-400 text-red-900",             icon: OctagonAlert },
};

async function _loadExcavation(excId) {
  try {
    const r = await api.get(`/trench-safety/excavations/${excId}`);
    return r.data || null;
  } catch { return null; }
}

export default function LinkedExcavationCompliance({ excavationId }) {
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
  const tid = `linked-exc-${excavationId}`;
  if (loading) {
    return <div className="text-xs text-slate-500" data-testid={tid}>{excavationId}…</div>;
  }
  if (!doc) {
    return (
      <div className="text-xs text-slate-700 flex items-center gap-2" data-testid={tid}>
        <span className="font-mono font-bold">{excavationId}</span>
        <span className="opacity-60">·</span>
        <span className="opacity-60">{t("Safety/Admin view")}</span>
      </div>
    );
  }

  const p = PALETTE[doc.status] || PALETTE["Needs Review"];
  const Icon = p.icon;
  return (
    <div className={`border rounded px-2 py-1 text-xs flex items-center gap-2 flex-wrap ${p.bg}`} data-testid={tid}>
      <Icon className="w-3.5 h-3.5 shrink-0" />
      <span className="font-mono font-black">{doc.id}</span>
      <span className="font-bold uppercase tracking-[0.10em] text-[10px]">{t(doc.status)}</span>
      {doc.depth_ft && <span className="opacity-70">· {doc.depth_ft} ft</span>}
      {doc.soil_classification && <span className="opacity-70">· {doc.soil_classification}</span>}
      {(doc.flags || []).length > 0 && (
        <span className="opacity-70">· {doc.flags.length} {t("open")}</span>
      )}
    </div>
  );
}
