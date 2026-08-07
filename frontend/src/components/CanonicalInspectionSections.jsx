// Track 13.31B-D5.4 · CanonicalInspectionSections — interactive structured
// capture for canonical Pre-Op + DVIR templates.
//
// Behavior (D5.4):
//   • Fetches /api/asset-spine/inspection-templates/by-asset-type/{type}
//   • Renders each section's items with PASS / FAIL / N/A controls.
//   • FAIL surfaces an optional short note field.
//   • Tallies pass / fail / na live and emits a structured payload to
//     the parent via `onChange` so it can be persisted alongside the
//     existing legacy `checklist`. The legacy form path is NOT replaced —
//     this is an additive, canonical-authority capture layer.
//   • Silent when no unit; honest empty state when the template is missing.
//
// Emitted payload (via onChange):
//   {
//     unit_number, asset_type, template_key, template_label, applies_to,
//     template_status: "available" | "missing_template",
//     sections: [{label, items: [{name, status, note}]}],
//     pass_count, fail_count, na_count, total_count,
//   }
//
// data-testids preserved from D5.3 + new interactive ones added.

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, AlertTriangle, Loader2, Wrench } from "lucide-react";
import { api } from "@/lib/api";
import { hasAnyPortalAuthToken } from "@/lib/authHeaders";

const STATUSES = ["pass", "fail", "na"];

const safeSeg = (s) =>
  String(s || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60);

function CapButton({ active, color, label, onClick, testId }) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testId}
      className={`flex-1 min-w-0 h-9 rounded font-mono text-[10px] font-black uppercase tracking-tight border-2 transition-colors truncate px-1 ${
        active
          ? `${color} text-white border-transparent`
          : "bg-white text-slate-500 border-slate-300 hover:border-slate-500"
      }`}
    >
      {label}
    </button>
  );
}

export default function CanonicalInspectionSections({
  unitNumber,
  appliesTo = "pre_op",
  onChange,
  testidPrefix = "canonical-sections",
}) {
  const [state, setState] = useState({
    loading: false,
    asset_type: null,
    template_key: null,
    template_label: null,
    applies_to: null,
    sections: [],
    status: null,
  });
  // results[sectionLabel][itemName] = { status: 'pass'|'fail'|'na'|'', note: '' }
  const [results, setResults] = useState({});

  useEffect(() => {
    const u = (unitNumber || "").trim();
    if (!u) {
      setState({ loading: false, asset_type: null, sections: [], status: null });
      setResults({});
      return undefined;
    }
    if (!hasAnyPortalAuthToken()) {
      setState({ loading: false, asset_type: null, sections: [], status: null });
      setResults({});
      return undefined;
    }
    let cancelled = false;
    setState((s) => ({ ...s, loading: true }));
    (async () => {
      try {
        const lookup = await api.get(`/asset-spine/taxonomy/by-unit/${encodeURIComponent(u)}`, {
          skipSessionStatus: true,
        });
        if (cancelled) return;
        const found = !!lookup.data?.found;
        const at = lookup.data?.asset_type;
        // Track 15.72C · trust fix · distinguish 3 honest states instead of
        // collapsing them all into "missing_template":
        //   1. unit_not_in_registry  — asset doesn't exist (template state unknown)
        //   2. missing_template      — asset exists, but no template for its type
        //   3. available              — asset exists AND template exists
        if (!found) {
          setState({ loading: false, asset_type: null, sections: [], status: "unit_not_in_registry" });
          setResults({});
          return;
        }
        if (!at) {
          // Found in registry but no asset_type resolved → still a catalog gap,
          // not a missing template per se.
          setState({ loading: false, asset_type: null, sections: [], status: "unit_not_in_registry" });
          setResults({});
          return;
        }
        const t = await api.get(`/asset-spine/inspection-templates/by-asset-type/${encodeURIComponent(at)}`, {
          skipSessionStatus: true,
        });
        if (cancelled) return;
        const sections = t.data?.sections || [];
        const tplStatus = t.data?.template_status || "missing_template";
        setState({
          loading: false,
          asset_type: at,
          template_key: t.data?.template_key || null,
          template_label: t.data?.template_label || `${at} Inspection`,
          applies_to: t.data?.applies_to || null,
          sections,
          status: tplStatus,
        });
        // Seed empty results map fresh on (unit/template) change.
        const seed = {};
        sections.forEach((sec) => {
          seed[sec.label] = {};
          (sec.items || []).forEach((it) => {
            seed[sec.label][it] = { status: "", note: "" };
          });
        });
        setResults(seed);
      } catch (e) {
        if (cancelled) return;
        if (e?.response?.status === 401 || e?.response?.status === 403) {
          setState({ loading: false, asset_type: null, sections: [], status: null });
        } else {
          // Track 15.72C · honest "temporarily unavailable" state instead of
          // claiming the template doesn't exist when we don't actually know.
          setState({ loading: false, asset_type: null, sections: [], status: "lookup_unavailable" });
        }
        setResults({});
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [unitNumber, appliesTo]);

  // Aggregate + emit on every results change.
  const aggregate = useMemo(() => {
    let pass = 0;
    let fail = 0;
    let na = 0;
    let total = 0;
    const sectionsOut = (state.sections || []).map((sec) => {
      const itemsOut = (sec.items || []).map((name) => {
        const r = results?.[sec.label]?.[name] || { status: "", note: "" };
        total += 1;
        if (r.status === "pass") pass += 1;
        else if (r.status === "fail") fail += 1;
        else if (r.status === "na") na += 1;
        return { name, status: r.status || "", note: (r.note || "").trim() };
      });
      return { label: sec.label, items: itemsOut };
    });
    return {
      unit_number: (unitNumber || "").trim(),
      asset_type: state.asset_type,
      template_key: state.template_key,
      template_label: state.template_label,
      applies_to: state.applies_to || appliesTo,
      template_status: state.status,
      sections: sectionsOut,
      pass_count: pass,
      fail_count: fail,
      na_count: na,
      total_count: total,
    };
  }, [results, state, unitNumber, appliesTo]);

  useEffect(() => {
    if (typeof onChange === "function") onChange(aggregate);
  }, [aggregate, onChange]);

  if (!unitNumber || state.status === null) return null;

  if (state.loading) {
    return (
      <div
        data-testid={`${testidPrefix}-loading`}
        className="mt-3 text-xs font-mono uppercase tracking-[0.16em] text-slate-500 inline-flex items-center gap-1.5"
      >
        <Loader2 className="w-3 h-3 animate-spin" /> Building inspection from saved asset record…
      </div>
    );
  }

  if (state.status === "unit_not_in_registry") {
    return (
      <div
        data-testid={`${testidPrefix}-unit-not-in-registry`}
        className="mt-3 px-3 py-2 rounded border border-amber-300 bg-amber-50 text-amber-900 text-xs font-mono"
      >
        <div className="inline-flex items-center gap-2 font-bold uppercase tracking-[0.14em]">
          <AlertTriangle className="w-3.5 h-3.5" /> Unit not cataloged yet
        </div>
        <div className="mt-1 normal-case font-sans text-amber-900">
          You can continue with a general inspection. Asset Admin will review this unit and connect it to the equipment registry.
        </div>
      </div>
    );
  }

  if (state.status === "lookup_unavailable") {
    return (
      <div
        data-testid={`${testidPrefix}-lookup-unavailable`}
        className="mt-3 px-3 py-2 rounded border border-amber-300 bg-amber-50 text-amber-900 text-xs font-mono"
      >
        <div className="inline-flex items-center gap-2 font-bold uppercase tracking-[0.14em]">
          <AlertTriangle className="w-3.5 h-3.5" /> Asset lookup temporarily unavailable
        </div>
        <div className="mt-1 normal-case font-sans text-amber-900">
          Continue with a general inspection. Asset Admin will review.
        </div>
      </div>
    );
  }

  if (state.status === "missing_template") {
    return (
      <div
        data-testid={`${testidPrefix}-missing`}
        className="mt-3 px-3 py-2 rounded border border-amber-300 bg-amber-50 text-amber-900 text-xs font-mono"
      >
        <div className="inline-flex items-center gap-2 font-bold uppercase tracking-[0.14em]">
          <AlertTriangle className="w-3.5 h-3.5" /> Template not available yet for {state.asset_type || "this asset type"}
        </div>
        <div className="mt-1 normal-case font-sans text-amber-900">
          Continue with a general inspection. Asset Admin can add a template.
        </div>
      </div>
    );
  }

  const setStatus = (sectionLabel, item, status) => {
    setResults((prev) => {
      const next = { ...prev, [sectionLabel]: { ...(prev[sectionLabel] || {}) } };
      const existing = next[sectionLabel][item] || { status: "", note: "" };
      next[sectionLabel][item] = {
        ...existing,
        status: existing.status === status ? "" : status,
      };
      // Auto-clear note when leaving fail
      if (next[sectionLabel][item].status !== "fail") {
        next[sectionLabel][item].note = "";
      }
      return next;
    });
  };

  const setNote = (sectionLabel, item, note) => {
    setResults((prev) => {
      const next = { ...prev, [sectionLabel]: { ...(prev[sectionLabel] || {}) } };
      next[sectionLabel][item] = {
        ...(next[sectionLabel][item] || { status: "", note: "" }),
        note,
      };
      return next;
    });
  };

  return (
    <div
      data-testid={testidPrefix}
      className="mt-4 rounded border border-emerald-200 bg-emerald-50/40 p-3"
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.16em] font-bold text-emerald-900">
            {state.template_label} · canonical inspection
          </span>
        </div>
        <div
          className="flex items-center gap-2 font-mono text-[10px] font-bold"
          data-testid={`${testidPrefix}-summary`}
        >
          <span className="text-emerald-700" data-testid={`${testidPrefix}-pass-count`}>
            {aggregate.pass_count} PASS
          </span>
          <span className="text-red-700" data-testid={`${testidPrefix}-fail-count`}>
            {aggregate.fail_count} FAIL
          </span>
          <span className="text-slate-600" data-testid={`${testidPrefix}-na-count`}>
            {aggregate.na_count} N/A
          </span>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {(state.sections || []).map((s, i) => {
          const secKey = safeSeg(s.label);
          return (
            <div
              key={`${s.label}-${i}`}
              data-testid={`${testidPrefix}-section-${i}`}
              className="rounded bg-white border border-slate-200 px-3 py-2"
            >
              <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-slate-700 font-bold mb-2">
                <Wrench className="w-3 h-3" />
                {s.label}
              </div>
              <ul className="space-y-2">
                {(s.items || []).map((it, j) => {
                  const r = results?.[s.label]?.[it] || { status: "", note: "" };
                  const itKey = safeSeg(it);
                  const idStem = `${testidPrefix}-${secKey}-${itKey}`;
                  return (
                    <li key={`${s.label}-${j}`} data-testid={idStem} className="text-sm">
                      <div className="text-slate-800">{it}</div>
                      <div className="flex gap-1.5 mt-1">
                        <CapButton
                          active={r.status === "pass"}
                          color="bg-emerald-600"
                          label="Pass"
                          onClick={() => setStatus(s.label, it, "pass")}
                          testId={`${idStem}-pass`}
                        />
                        <CapButton
                          active={r.status === "fail"}
                          color="bg-red-700"
                          label="Fail"
                          onClick={() => setStatus(s.label, it, "fail")}
                          testId={`${idStem}-fail`}
                        />
                        <CapButton
                          active={r.status === "na"}
                          color="bg-slate-600"
                          label="N/A"
                          onClick={() => setStatus(s.label, it, "na")}
                          testId={`${idStem}-na`}
                        />
                      </div>
                      {r.status === "fail" && (
                        <input
                          type="text"
                          value={r.note}
                          onChange={(e) => setNote(s.label, it, e.target.value)}
                          placeholder="Short note (what failed)"
                          data-testid={`${idStem}-note`}
                          className="mt-1.5 w-full text-xs border-2 border-red-300 rounded px-2 py-1 focus:outline-none focus:border-red-500"
                        />
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </div>
      <div className="mt-2 text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500">
        Sections auto-detected from {state.asset_type} record · pass/fail captured to the structured payload
      </div>
    </div>
  );
}
