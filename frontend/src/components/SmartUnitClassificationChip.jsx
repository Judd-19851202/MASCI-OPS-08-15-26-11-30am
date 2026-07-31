// Track 13.31B-D5.1 BUILD · Smart Pre-Op / DVIR auto-detect chip.
//
// When the operator selects a unit, this component asks the asset spine
// for the canonical classification and shows one operator-safe line:
//
//   • Asset type · auto-detected · {Excavator} · verified
//   • Asset type · auto-detected · {Motor Grader} · mapped from existing record
//   • Asset type · review needed · you can continue — Asset Admin will review
//   • Unit not found · enter manually · Asset Admin will review later
//
// It is a pure read; never blocks submission. Honest "needs review" state
// is the same chip vocabulary the Asset Admin queue uses.

import { useEffect, useState } from "react";
import { ShieldCheck, AlertTriangle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

export default function SmartUnitClassificationChip({ unitNumber, testidPrefix = "smart-class" }) {
  const [state, setState] = useState({ loading: false, found: null, source: null, asset_class: null, asset_type: null, verified: false });

  useEffect(() => {
    const u = (unitNumber || "").trim();
    if (!u) { setState({ loading: false, found: null }); return; }
    let cancelled = false;
    setState((s) => ({ ...s, loading: true }));
    api
      .get(`/asset-spine/taxonomy/by-unit/${encodeURIComponent(u)}`, { skipSessionStatus: true })
      .then((r) => {
        if (cancelled) return;
        const d = r.data || {};
        setState({
          loading: false,
          found: !!d.found,
          source: d.classification_source || null,
          asset_class: d.asset_class || null,
          asset_type: d.asset_type || null,
          verified: !!d.classification_verified,
        });
      })
      .catch((e) => {
        if (cancelled) return;
        // Public submissions may not have a portal token; silently hide
        // the chip rather than show an auth error to a driver.
        const status = e?.response?.status;
        if (status === 401 || status === 403) {
          setState({ loading: false, found: null });
        } else {
          setState({ loading: false, found: false });
        }
      });
    return () => { cancelled = true; };
  }, [unitNumber]);

  if (!unitNumber) return null;
  // Silent: auth-failed (public submission) → hide entirely.
  if (state.found === null && !state.loading) return null;

  if (state.loading) {
    return (
      <div data-testid={`${testidPrefix}-loading`}
           className="mt-2 text-xs font-mono uppercase tracking-[0.16em] text-slate-500 inline-flex items-center gap-1.5">
        <Loader2 className="w-3 h-3 animate-spin" /> Checking asset record…
      </div>
    );
  }

  // Unit not in equipment_master.
  // Track 15.72C · trust fix · suppress this chip when the unit isn't
  // found — the calmer "Unit not cataloged yet" banner rendered by
  // <CanonicalInspectionSections> handles this state with the operator's
  // approved copy. Showing both produced duplicate/contradictory warnings.
  if (state.found === false) {
    return null;
  }

  // Verified canonical
  if (state.verified && state.asset_type) {
    return (
      <div data-testid={`${testidPrefix}-verified`}
           className="mt-2 inline-flex items-center gap-2 px-2.5 py-1 rounded border border-emerald-300 bg-emerald-50 text-emerald-900 text-xs font-mono uppercase tracking-[0.14em] font-bold">
        <ShieldCheck className="w-3.5 h-3.5" />
        Asset type · {state.asset_type} · verified
      </div>
    );
  }

  // Legacy-mapped (asset record exists, classification mapped from legacy fields)
  if (state.source === "legacy_mapped" && state.asset_type) {
    return (
      <div data-testid={`${testidPrefix}-mapped`}
           className="mt-2 inline-flex items-center gap-2 px-2.5 py-1 rounded border border-sky-300 bg-sky-50 text-sky-900 text-xs font-mono uppercase tracking-[0.14em] font-bold">
        <ShieldCheck className="w-3.5 h-3.5" />
        Asset type · {state.asset_type} · mapped from existing record
      </div>
    );
  }

  // Needs review
  return (
    <div data-testid={`${testidPrefix}-needs-review`}
         className="mt-2 inline-flex items-center gap-2 px-2.5 py-1 rounded border border-amber-300 bg-amber-50 text-amber-900 text-xs font-mono uppercase tracking-[0.14em] font-bold">
      <AlertTriangle className="w-3.5 h-3.5" />
      {state.asset_type
        ? `Asset type · ${state.asset_type} · review needed`
        : "Classification review needed"}
      {" · you can continue — Asset Admin will review"}
    </div>
  );
}
