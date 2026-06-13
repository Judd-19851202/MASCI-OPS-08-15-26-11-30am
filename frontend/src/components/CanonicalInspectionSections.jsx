// Track 13.31B-D5.3 · CanonicalInspectionSections — renders the
// registry-defined sections for a unit's canonical asset_type.
//
// Fetches /api/asset-spine/inspection-templates/by-asset-type/{type} once
// the unit is resolved and renders MASCI-native sections + item lists.
// Honest empty state when the template is missing; silent when no unit.

import { useEffect, useState } from "react";
import { CheckCircle2, AlertTriangle, Loader2, Wrench } from "lucide-react";
import { api } from "@/lib/api";

export default function CanonicalInspectionSections({ unitNumber, appliesTo = "pre_op" }) {
  const [state, setState] = useState({ loading: false, asset_type: null, sections: [], status: null });

  useEffect(() => {
    const u = (unitNumber || "").trim();
    if (!u) { setState({ loading: false, asset_type: null, sections: [], status: null }); return; }
    let cancelled = false;
    setState((s) => ({ ...s, loading: true }));
    (async () => {
      try {
        const lookup = await api.get(`/asset-spine/taxonomy/by-unit/${encodeURIComponent(u)}`);
        if (cancelled) return;
        const at = lookup.data?.asset_type;
        if (!at) {
          setState({ loading: false, asset_type: null, sections: [], status: "missing_template" });
          return;
        }
        const t = await api.get(`/asset-spine/inspection-templates/by-asset-type/${encodeURIComponent(at)}`);
        if (cancelled) return;
        setState({
          loading: false,
          asset_type: at,
          template_label: t.data?.template_label || `${at} Inspection`,
          sections: t.data?.sections || [],
          applies_to: t.data?.applies_to,
          status: t.data?.template_status || "missing_template",
        });
      } catch (e) {
        if (cancelled) return;
        if (e?.response?.status === 401 || e?.response?.status === 403) {
          setState({ loading: false, asset_type: null, sections: [], status: null });
        } else {
          setState({ loading: false, asset_type: null, sections: [], status: "missing_template" });
        }
      }
    })();
    return () => { cancelled = true; };
  }, [unitNumber, appliesTo]);

  if (!unitNumber || state.status === null) return null;

  if (state.loading) {
    return (
      <div data-testid="canonical-sections-loading" className="mt-3 text-xs font-mono uppercase tracking-[0.16em] text-slate-500 inline-flex items-center gap-1.5">
        <Loader2 className="w-3 h-3 animate-spin" /> Building inspection from canonical record…
      </div>
    );
  }

  if (state.status === "missing_template") {
    return (
      <div data-testid="canonical-sections-missing" className="mt-3 px-3 py-2 rounded border border-amber-300 bg-amber-50 text-amber-900 text-xs font-mono">
        <div className="inline-flex items-center gap-2 font-bold uppercase tracking-[0.14em]">
          <AlertTriangle className="w-3.5 h-3.5" /> Template not built yet for this asset type
        </div>
        <div className="mt-1 normal-case font-sans text-amber-900">
          Continue with the general inspection. Asset Admin can review the missing-template backlog.
        </div>
      </div>
    );
  }

  return (
    <div data-testid="canonical-sections" className="mt-4 rounded border border-emerald-200 bg-emerald-50/40 p-3">
      <div className="flex items-center gap-2 mb-2">
        <CheckCircle2 className="w-4 h-4 text-emerald-700" />
        <span className="font-mono text-[10px] uppercase tracking-[0.16em] font-bold text-emerald-900">
          {state.template_label} · canonical inspection
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {state.sections.map((s, i) => (
          <div key={`${s.label}-${i}`} data-testid={`canonical-section-${i}`} className="rounded bg-white border border-slate-200 px-3 py-2">
            <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-slate-700 font-bold mb-1">
              <Wrench className="w-3 h-3" />
              {s.label}
            </div>
            <ul className="text-sm text-slate-800 list-disc list-inside space-y-0.5">
              {(s.items || []).map((it, j) => (
                <li key={`${s.label}-${j}`}>{it}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="mt-2 text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500">
        Sections auto-detected from {state.asset_type} record · complete the checks above + submit your standard form
      </div>
    </div>
  );
}
