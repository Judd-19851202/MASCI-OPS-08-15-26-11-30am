// Trench Equipment list — filterable roster of every MASCI trench
// safety asset. Reads live from /api/trench-safety/assets (Phase 2).
//
// Phase 3 · MASCI Trench Safety Operations System.
import React, { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Loader2, Search, AlertTriangle, FileWarning, Plus, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import TrenchSafetyShell from "@/pages/trench_safety/TrenchSafetyShell";
import { CreateAssetDialog } from "@/pages/trench_safety/TrenchSafetyActions";
import {
  QuickAddAssetDialog,
  CSVImportDialog,
  TrenchAssetFilterChips,
} from "@/pages/trench_safety/TrenchSafetyPolish";

const TYPES = [
  "Trench Box", "End Panel", "Spreader Bar", "Hydraulic Shore",
  "Slide Rail System", "Trench Jack", "Ladder", "Accessory",
  // Phase 8A — Road Plate
  "Road Plate",
];
const STATUSES = [
  "Available", "Assigned", "In Transport", "Inspection Hold", "Repair", "Retired",
];
const CONDITIONS = ["Excellent", "Good", "Fair", "Poor", "Out Of Service"];

const STATUS_COLOR = {
  "Available":          "bg-emerald-50 text-emerald-900 border-emerald-300",
  "Assigned":           "bg-blue-50 text-blue-900 border-blue-300",
  "In Transport":       "bg-cyan-50 text-cyan-900 border-cyan-300",
  "Inspection Hold":    "bg-amber-50 text-amber-900 border-amber-400",
  "Maintenance Hold":   "bg-orange-50 text-orange-900 border-orange-400",
  "Certification Hold": "bg-purple-50 text-purple-900 border-purple-400",
  "Safety Hold":        "bg-red-50 text-red-900 border-red-500",
  "Retired":            "bg-slate-100 text-slate-600 border-slate-300",
};

const CONDITION_COLOR = {
  "Excellent":      "text-emerald-700",
  "Good":           "text-emerald-700",
  "Fair":           "text-amber-700",
  "Poor":           "text-red-700",
  "Out Of Service": "text-red-800 font-black",
};

export default function TrenchSafetyAssetsList() {
  const { t } = useT();
  const location = useLocation();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  // Filters
  const [q, setQ] = useState("");
  const [fType, setFType] = useState("__all");
  const [fStatus, setFStatus] = useState("__all");
  const [fCondition, setFCondition] = useState("__all");
  const [fNeeds, setFNeeds] = useState("__all");
  const [createOpen, setCreateOpen] = useState(false);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [csvOpen, setCsvOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const params = {};
        if (q) params.q = q;
        if (fType !== "__all") params.asset_type = fType;
        if (fStatus !== "__all") params.operational_status = fStatus;
        if (fCondition !== "__all") params.condition = fCondition;
        if (fNeeds === "yes") params.needs_review = true;
        if (fNeeds === "no") params.needs_review = false;
        const r = await api.get("/trench-safety/assets", { params });
        if (!cancelled) setItems(r.data?.items || []);
      } catch (e) {
        if (!cancelled) setErr(e?.response?.data?.detail || e?.message || "Failed to load assets");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [q, fType, fStatus, fCondition, fNeeds, reloadKey]);

  const count = items.length;
  const portalBase = location.pathname.startsWith("/admin/trench-safety")
    ? "/admin/trench-safety"
    : location.pathname.startsWith("/pm/trench-safety")
      ? "/pm/trench-safety"
      : "/safety/trench-safety";

  return (
    <TrenchSafetyShell active="assets">
      <div className="flex items-end justify-between flex-wrap gap-3 mb-2">
        <div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900" data-testid="trench-list-title">
            {t("Trench Equipment")}
          </h1>
          <p className="text-slate-600 text-sm mt-1">
            {t("Live roster of every MASCI trench safety asset. Tap an asset to see its full record.")}
          </p>
        </div>
        <div className="font-mono text-xs text-slate-500" data-testid="trench-list-count">
          {count} {t("asset(s)")}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 mt-2" data-testid="trench-list-actions">
        <Button onClick={() => setQuickAddOpen(true)} className="bg-cyan-700 hover:bg-cyan-800" data-testid="trench-list-quick-add-btn">
          <Plus className="w-4 h-4 mr-1" /> {t("Quick Add")}
        </Button>
        <Button onClick={() => setCreateOpen(true)} variant="outline" data-testid="trench-list-create-btn">
          <Plus className="w-4 h-4 mr-1" /> {t("New Asset (Full)")}
        </Button>
        <Button onClick={() => setCsvOpen(true)} variant="outline" data-testid="trench-list-csv-btn">
          <Upload className="w-4 h-4 mr-1" /> {t("Import CSV")}
        </Button>
        <p className="text-xs text-slate-500">
          {t("Asset IDs are permanent once created. Safety and Admin can both create, edit, and retire.")}
        </p>
      </div>

      <CreateAssetDialog open={createOpen} onOpenChange={setCreateOpen} onCreated={() => setReloadKey((k) => k + 1)} />
      <QuickAddAssetDialog open={quickAddOpen} onOpenChange={setQuickAddOpen} onCreated={() => setReloadKey((k) => k + 1)} />
      <CSVImportDialog open={csvOpen} onOpenChange={setCsvOpen} onImported={() => setReloadKey((k) => k + 1)} />

      {/* Phase 8B — One-tap filter chips (mobile-safe, no horizontal scroll) */}
      <div className="mt-4" data-testid="trench-list-chips-wrap">
        <TrenchAssetFilterChips
          value={{ status: fStatus, type: fType }}
          onChange={(v) => { setFStatus(v.status); setFType(v.type); }}
        />
      </div>

      {/* Filters strip */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-2 mt-4" data-testid="trench-list-filters">
        <div className="md:col-span-2 relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("Search by ID, serial, size, location…")}
            className="pl-8 h-10 border-2"
            data-testid="trench-list-search"
          />
        </div>
        <Select value={fType} onValueChange={setFType}>
          <SelectTrigger className="h-10 border-2" data-testid="trench-list-filter-type"><SelectValue placeholder={t("Asset Type")} /></SelectTrigger>
          <SelectContent>
            <SelectItem value="__all">{t("All Types")}</SelectItem>
            {TYPES.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={fStatus} onValueChange={setFStatus}>
          <SelectTrigger className="h-10 border-2" data-testid="trench-list-filter-status"><SelectValue placeholder={t("Status")} /></SelectTrigger>
          <SelectContent>
            <SelectItem value="__all">{t("All Statuses")}</SelectItem>
            {STATUSES.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={fCondition} onValueChange={setFCondition}>
          <SelectTrigger className="h-10 border-2" data-testid="trench-list-filter-condition"><SelectValue placeholder={t("Condition")} /></SelectTrigger>
          <SelectContent>
            <SelectItem value="__all">{t("All Conditions")}</SelectItem>
            {CONDITIONS.map((x) => <SelectItem key={x} value={x}>{t(x)}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="mt-2 flex flex-wrap gap-2 items-center">
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
          {t("Needs Review")}:
        </span>
        {[
          { key: "__all", label: t("All") },
          { key: "yes",   label: t("Yes") },
          { key: "no",    label: t("No") },
        ].map((opt) => (
          <button
            key={opt.key}
            data-testid={`trench-list-needs-${opt.key}`}
            onClick={() => setFNeeds(opt.key)}
            className={
              "px-3 h-8 rounded border text-xs font-bold uppercase tracking-[0.12em] " +
              (fNeeds === opt.key
                ? "border-cyan-700 bg-cyan-50 text-cyan-900"
                : "border-slate-300 bg-white text-slate-600 hover:border-cyan-400")
            }
          >
            {opt.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center gap-2 mt-8 text-slate-500" data-testid="trench-list-loading">
          <Loader2 className="w-5 h-5 animate-spin" />
          {t("Loading assets…")}
        </div>
      ) : err ? (
        <div className="mt-8 p-4 border border-red-300 bg-red-50 rounded text-red-900 text-sm" data-testid="trench-list-error">
          {err}
        </div>
      ) : count === 0 ? (
        <div className="mt-10 p-8 bg-white border border-slate-200 rounded text-center text-slate-500" data-testid="trench-list-empty">
          {t("No trench safety assets match the current filters.")}
        </div>
      ) : (
        <div className="mt-4 overflow-x-auto" data-testid="trench-list-table-wrap">
          <table className="w-full bg-white border border-slate-200 rounded text-sm">
            <thead className="bg-slate-50 border-b-2 border-slate-200">
              <tr className="text-left font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
                <th className="px-3 py-2">{t("Asset ID")}</th>
                <th className="px-3 py-2 hidden sm:table-cell">{t("Type")}</th>
                <th className="px-3 py-2">{t("Size")}</th>
                <th className="px-3 py-2 hidden md:table-cell">{t("Serial #")}</th>
                <th className="px-3 py-2 hidden lg:table-cell">{t("Color")}</th>
                <th className="px-3 py-2">{t("Condition")}</th>
                <th className="px-3 py-2">{t("Status")}</th>
                <th className="px-3 py-2 hidden md:table-cell">{t("Location")}</th>
                <th className="px-3 py-2 hidden lg:table-cell">{t("Current Project")}</th>
                <th className="px-3 py-2 hidden lg:table-cell">{t("Last Inspection")}</th>
                <th className="px-3 py-2 hidden 2xl:table-cell">{t("Alerts")}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.id || a.asset_id} className="border-b border-slate-100 hover:bg-cyan-50/40">
                  <td className="px-3 py-2 font-mono font-bold text-slate-900">
                    <Link to={`${portalBase}/assets/${a.asset_id}`} className="hover:text-cyan-800 underline-offset-2 hover:underline" data-testid={`trench-row-${a.asset_id}`}>
                      {a.asset_id}
                    </Link>
                  </td>
                  <td className="px-3 py-2 hidden sm:table-cell">{t(a.asset_type || "Trench Box")}</td>
                  <td className="px-3 py-2">{a.size || "—"}</td>
                  <td className="px-3 py-2 hidden md:table-cell font-mono text-xs">
                    {a.serial_number || <span className="text-amber-700 inline-flex items-center gap-1"><FileWarning className="w-3 h-3" />{t("missing")}</span>}
                  </td>
                  <td className="px-3 py-2 hidden lg:table-cell">{a.color || "—"}</td>
                  <td className={`px-3 py-2 font-bold ${CONDITION_COLOR[a.condition] || "text-slate-700"}`}>{t(a.condition || "Good")}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-block px-2 py-0.5 rounded border text-[11px] font-bold uppercase tracking-[0.08em] ${STATUS_COLOR[a.operational_status] || "bg-slate-50 text-slate-700 border-slate-300"}`}>
                      {t(a.operational_status || "Available")}
                    </span>
                  </td>
                  <td className="px-3 py-2 hidden md:table-cell">{a.current_location || "—"}</td>
                  <td className="px-3 py-2 hidden lg:table-cell text-xs">
                    {a.current_project_name ? (
                      <div>
                        <div className="font-medium text-slate-900">{a.current_project_name}</div>
                        {a.current_project_number ? <div className="font-mono text-[10px] text-slate-500">#{a.current_project_number}</div> : null}
                      </div>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-3 py-2 hidden lg:table-cell font-mono text-xs">
                    {a.last_inspection_at ? a.last_inspection_at.slice(0, 10) : <span className="text-amber-700">{t("never")}</span>}
                  </td>
                  <td className="px-3 py-2 hidden 2xl:table-cell">
                    <div className="flex gap-1">
                      {a.missing_serial_number && <span title={t("Missing Serial Number")} className="inline-flex items-center gap-1 text-amber-700 text-xs"><FileWarning className="w-3 h-3" />SN</span>}
                      {a.needs_review && <span title={t("Needs Review")} className="inline-flex items-center gap-1 text-amber-700 text-xs"><AlertTriangle className="w-3 h-3" />RV</span>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </TrenchSafetyShell>
  );
}
