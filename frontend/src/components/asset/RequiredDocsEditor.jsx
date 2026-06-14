// Track 13.31B-D7 · Required Documents editor.
// Asset Admin can adjust the expected documents per Asset Type.
// Backed by /api/asset-spine/dashboard/required-documents-config-effective
// (read) + PUT/DELETE /required-documents-config/{asset_type} (write).
// Operator-friendly language · photos never required by default.

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Search, RotateCcw, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

const LEVELS = [
  {
    value: "required",
    label: "Required",
    color: "bg-red-100 text-red-900 border-red-300",
    help: "Must be on file. Asset will show Not Ready until uploaded.",
  },
  {
    value: "recommended",
    label: "Recommended",
    color: "bg-amber-100 text-amber-900 border-amber-300",
    help: "Should be on file. Will appear as a soft warning until uploaded.",
  },
  {
    value: "optional",
    label: "Optional",
    color: "bg-sky-100 text-sky-900 border-sky-300",
    help: "Nice to have. Never blocks readiness.",
  },
  {
    value: "not_applicable",
    label: "Not Applicable",
    color: "bg-slate-100 text-slate-700 border-slate-300",
    help: "Does not apply to this asset type. Hidden from missing-document lists.",
  },
];

const DOC_TYPES = [
  { v: "registration", l: "Registration", help: "DMV / state registration document. Renewal-tracked." },
  { v: "insurance_card", l: "Insurance Card", help: "Wallet-size proof of insurance carried in the vehicle." },
  { v: "insurance_policy", l: "Insurance Policy", help: "Full policy document. Restricted — admin only." },
  { v: "title", l: "Title", help: "Vehicle title / ownership document. Restricted — admin only." },
  { v: "purchase_document", l: "Purchase Document", help: "Bill of sale / purchase order. Restricted — admin only." },
  { v: "warranty", l: "Warranty", help: "Manufacturer or extended warranty paperwork." },
  { v: "dot_document", l: "DOT Document", help: "DOT inspection / authority paperwork. Annual renewal." },
  { v: "inspection_certificate", l: "Inspection Certificate", help: "Annual or jurisdictional inspection certificate." },
  { v: "calibration_certificate", l: "Calibration Certificate", help: "Calibration record for survey / measurement equipment." },
  { v: "asset_photo", l: "Asset Photo", help: "Identification photos (primary, VIN plate, etc.). Always optional." },
  { v: "operator_manual", l: "Operator Manual", help: "Manufacturer operator / service manual." },
  { v: "safety_documentation", l: "Safety Documentation", help: "Hazard sheets, SDS, lock-out tag-out procedures." },
  { v: "other_supporting_document", l: "Other Supporting Document", help: "Anything else worth keeping with the asset record." },
];

export default function RequiredDocsEditor() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get("/asset-spine/dashboard/required-documents-config-effective");
      setItems(r.data.items || []);
    } catch {
      toast.error("Could not load Required Documents settings. Try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const filtered = useMemo(() => {
    if (!filter) return items;
    const f = filter.toLowerCase();
    return items.filter((i) => i.asset_type.toLowerCase().includes(f));
  }, [items, filter]);

  const setLevel = useCallback(async (assetType, docType, level) => {
    setBusy(true);
    try {
      await api.put(`/asset-spine/dashboard/required-documents-config/${encodeURIComponent(assetType)}`, {
        document_type: docType,
        requirement_level: level,
      });
      toast.success("Changes saved.");
      await reload();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not save. Try again.");
    } finally {
      setBusy(false);
    }
  }, [reload]);

  const clearOverride = useCallback(async (assetType, docType) => {
    setBusy(true);
    try {
      await api.delete(`/asset-spine/dashboard/required-documents-config/${encodeURIComponent(assetType)}/${encodeURIComponent(docType)}`);
      toast.success("Reset to default.");
      await reload();
    } catch {
      toast.error("Could not reset. Try again.");
    } finally {
      setBusy(false);
    }
  }, [reload]);

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500" data-testid="rde-loading">
        <Loader2 className="w-5 h-5 animate-spin mx-auto" />
      </div>
    );
  }

  return (
    <div className="space-y-3" data-testid="required-docs-editor">
      <div
        className="rounded border border-sky-200 bg-sky-50/70 px-3 py-2 text-[12px] text-sky-900 flex items-start gap-2"
        data-testid="rde-coaching"
      >
        <Info className="w-4 h-4 mt-0.5 shrink-0" />
        <div>
          <span className="font-bold">Set the expected documents for each Asset Type.</span>{" "}
          These rules drive the missing-document dashboard and the readiness engine.
          Photos and documents are never required to create an asset.
        </div>
      </div>
      <div
        className="rounded border border-slate-200 bg-white px-3 py-2"
        data-testid="rde-level-legend"
      >
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">
          Requirement levels
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {LEVELS.map((lv) => (
            <div
              key={lv.value}
              className="flex items-start gap-2 text-[11.5px] text-slate-700"
              data-testid={`rde-level-help-${lv.value}`}
            >
              <span
                className={`px-1.5 py-0.5 rounded border font-mono text-[10px] uppercase tracking-[0.14em] font-bold ${lv.color}`}
              >
                {lv.label}
              </span>
              <span className="leading-snug">{lv.help}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs font-mono uppercase tracking-[0.18em] text-slate-700 font-bold">
          {items.length} asset types · adjust expected documents per type
        </div>
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2 top-1/2 -translate-y-1/2" />
          <input
            type="text" value={filter} onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter asset type…"
            className="pl-7 pr-3 py-2 border-2 border-slate-300 rounded text-sm w-64"
            data-testid="rde-filter"
          />
        </div>
      </div>
      <div className="rounded border border-slate-200 bg-white overflow-hidden">
        {filtered.map((it) => (
          <AssetTypeRow
            key={it.asset_type}
            item={it}
            onSetLevel={setLevel}
            onClearOverride={clearOverride}
            busy={busy}
          />
        ))}
        {filtered.length === 0 && (
          <div className="p-6 text-center text-slate-500 text-sm" data-testid="rde-empty">
            No asset types match.
          </div>
        )}
      </div>
      <div className="text-[11px] text-slate-500">
        Photos and documents are never required for asset creation — these settings only drive
        the "Documents Required" surfaces and the missing-document dashboard.
      </div>
    </div>
  );
}

function AssetTypeRow({ item, onSetLevel, onClearOverride, busy }) {
  const [expanded, setExpanded] = useState(false);
  const summary = useMemo(() => {
    const r = item.required?.length || 0;
    const rec = item.recommended?.length || 0;
    const opt = item.optional?.length || 0;
    const na = item.not_applicable?.length || 0;
    return { r, rec, opt, na };
  }, [item]);
  const totalConfigured = summary.r + summary.rec + summary.opt + summary.na;

  // Build current level map for editor
  const currentLevels = useMemo(() => {
    const m = {};
    (item.required || []).forEach((d) => { m[d.document_type] = "required"; });
    (item.recommended || []).forEach((d) => { m[d.document_type] = "recommended"; });
    (item.optional || []).forEach((d) => { m[d.document_type] = "optional"; });
    (item.not_applicable || []).forEach((d) => { m[d.document_type] = "not_applicable"; });
    return m;
  }, [item]);

  return (
    <div className="border-b border-slate-100 last:border-b-0" data-testid={`rde-row-${item.asset_type}`}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full px-3 py-2 flex items-center gap-3 hover:bg-slate-50 text-left"
        data-testid={`rde-row-toggle-${item.asset_type}`}
      >
        <div className="flex-1 min-w-0">
          <div className="font-bold text-slate-900 text-sm">{item.asset_type}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            {totalConfigured === 0
              ? "No expected documents configured yet."
              : `${summary.r} required · ${summary.rec} recommended · ${summary.opt} optional · ${summary.na} not applicable`}
          </div>
        </div>
        <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500">
          {expanded ? "Hide" : "Edit"}
        </div>
      </button>
      {expanded && (
        <div className="px-3 pb-3 pt-1">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {DOC_TYPES.map((d) => {
              const current = currentLevels[d.v] || "optional";
              return (
                <div key={d.v} className="flex items-start gap-2 text-xs bg-slate-50 rounded p-1.5"
                  data-testid={`rde-doc-${item.asset_type}-${d.v}`}>
                  <div className="flex-1 min-w-0">
                    <div className="truncate font-semibold text-slate-800">{d.l}</div>
                    <div
                      className="text-[10.5px] text-slate-500 leading-snug"
                      data-testid={`rde-doc-help-${d.v}`}
                    >
                      {d.help}
                    </div>
                  </div>
                  <select
                    value={current}
                    disabled={busy}
                    onChange={(e) => onSetLevel(item.asset_type, d.v, e.target.value)}
                    className="border-2 border-slate-300 rounded px-1 py-0.5 text-xs"
                    title={LEVELS.find((l) => l.value === current)?.help || ""}
                    data-testid={`rde-select-${item.asset_type}-${d.v}`}
                  >
                    {LEVELS.map((l) => (
                      <option key={l.value} value={l.value} title={l.help}>{l.label}</option>
                    ))}
                  </select>
                  <Button size="sm" variant="ghost" disabled={busy}
                    onClick={() => onClearOverride(item.asset_type, d.v)}
                    title="Reset to default"
                    aria-label="Reset to default"
                    data-testid={`rde-reset-${item.asset_type}-${d.v}`}>
                    <RotateCcw className="w-3 h-3" />
                  </Button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
