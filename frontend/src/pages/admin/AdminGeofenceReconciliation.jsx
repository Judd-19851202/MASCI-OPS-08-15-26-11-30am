// M-3 · Geocode Foundation · Admin Reconciliation Screen.
//
// Lets the operator review proposed Motive geofence ↔ MASCI project
// matches, approve / reject / reassign / bulk-approve.
//
// Constitutional rules (UI-enforced):
//   • Bulk-approve only enabled when ALL selected rows are HIGH band.
//   • Reassign requires a real project_number (typed in).
//   • Verified / Rejected rows are read-only.
//   • No write actions touch Motive directly.
import React, { useEffect, useState, useMemo, useCallback } from "react";
import { Link } from "react-router-dom";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  Loader2, CheckCircle2, XCircle, RefreshCw, MapPin,
  ChevronRight, Shuffle, ArrowDownToLine,
} from "lucide-react";

const BAND_STYLES = {
  high:   { bg: "bg-emerald-50",  border: "border-emerald-400", text: "text-emerald-800", label: "HIGH" },
  medium: { bg: "bg-amber-50",    border: "border-amber-400",   text: "text-amber-900",   label: "MEDIUM" },
  low:    { bg: "bg-red-50",      border: "border-red-300",     text: "text-red-800",     label: "LOW" },
};

const STATUS_STYLES = {
  "Verified":     { bg: "bg-emerald-100", text: "text-emerald-900" },
  "Matched":      { bg: "bg-amber-100",   text: "text-amber-900" },
  "Imported":     { bg: "bg-slate-100",   text: "text-slate-700" },
  "Rejected":     { bg: "bg-red-100",     text: "text-red-900" },
  "Not Geocoded": { bg: "bg-slate-100",   text: "text-slate-700" },
};

export default function AdminGeofenceReconciliation() {
  const [rows, setRows] = useState([]);
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [filter, setFilter] = useState("all"); // all|high|medium|low|verified|rejected
  const [selected, setSelected] = useState(new Set());
  const [reassignFor, setReassignFor] = useState(null);
  const [reassignPn, setReassignPn] = useState("");
  const [imports, setImports] = useState(false);
  const [reloadTick, setReloadTick] = useState(0);
  const triggerReload = useCallback(() => setReloadTick((t) => t + 1), []);

  const load = useCallback(() => triggerReload(), [triggerReload]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (["high", "medium", "low"].includes(filter)) params.set("band", filter);
        if (filter === "verified") params.set("status", "Verified");
        if (filter === "rejected") params.set("status", "Rejected");
        const r = await api.get(`/admin/locations/reconciliation-queue?${params}`);
        if (cancelled) return;
        setRows(r.data.rows || []);
        setCounts(r.data.counts || {});
      } catch (e) {
        if (!cancelled) toast.error(`Load failed: ${e?.response?.data?.detail || e.message}`);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [filter, reloadTick]);

  const runImport = async () => {
    setImports(true);
    try {
      const r = await api.post("/admin/locations/import-geofences");
      toast.success(`Imported ${r.data.imported} · updated ${r.data.updated} (${r.data.total_geofences_in_motive} geofences in Motive)`);
      await load();
    } catch (e) {
      toast.error(`Import failed: ${e?.response?.data?.detail || e.message}`);
    } finally { setImports(false); }
  };

  const runReconcile = async () => {
    setImports(true);
    try {
      const r = await api.post("/admin/locations/reconcile");
      const b = r.data.bands || {};
      toast.success(`Reconciled ${r.data.scored} · HIGH ${b.high||0} · MEDIUM ${b.medium||0} · LOW ${b.low||0}`);
      await load();
    } catch (e) {
      toast.error(`Reconcile failed: ${e?.response?.data?.detail || e.message}`);
    } finally { setImports(false); }
  };

  const approve = async (id) => {
    setBusyId(id);
    try {
      await api.post(`/api/admin/locations/${id}/approve`);
      toast.success("Approved");
      await load();
    } catch (e) {
      toast.error(`Approve failed: ${e?.response?.data?.detail || e.message}`);
    } finally { setBusyId(null); }
  };

  const reject = async (id) => {
    setBusyId(id);
    try {
      await api.post(`/admin/locations/${id}/reject`);
      toast.success("Rejected");
      await load();
    } catch (e) {
      toast.error(`Reject failed: ${e?.response?.data?.detail || e.message}`);
    } finally { setBusyId(null); }
  };

  const reassign = async () => {
    if (!reassignFor || !reassignPn.trim()) return;
    setBusyId(reassignFor);
    try {
      await api.post(`/admin/locations/${reassignFor}/reassign`, {
        project_number: reassignPn.trim(),
      });
      toast.success(`Reassigned to ${reassignPn.trim()}`);
      setReassignFor(null);
      setReassignPn("");
      await load();
    } catch (e) {
      toast.error(`Reassign failed: ${e?.response?.data?.detail || e.message}`);
    } finally { setBusyId(null); }
  };

  const allHighSelected = useMemo(() => {
    if (selected.size === 0) return false;
    for (const id of selected) {
      const row = rows.find((r) => r.id === id);
      if (!row) return false;
      if (row.confidence_band !== "high") return false;
      if (row.geocode_status === "Verified" || row.geocode_status === "Rejected") return false;
    }
    return true;
  }, [selected, rows]);

  const bulkApprove = async () => {
    if (!allHighSelected) {
      toast.error("Bulk approve is only allowed for HIGH-confidence rows.");
      return;
    }
    try {
      const r = await api.post("/admin/locations/bulk-approve", {
        ids: Array.from(selected),
      });
      toast.success(`Bulk approved ${r.data.approved_count} · skipped ${r.data.skipped_count}`);
      setSelected(new Set());
      await load();
    } catch (e) {
      toast.error(`Bulk approve failed: ${e?.response?.data?.detail || e.message}`);
    }
  };

  const toggleSelect = (id) => {
    const s = new Set(selected);
    if (s.has(id)) s.delete(id); else s.add(id);
    setSelected(s);
  };

  return (
    <AdminShell title="Motive Geofence Reconciliation" section="jobs">
      <div className="space-y-4" data-testid="geofence-recon-page">
        {/* Header / actions */}
        <div className="rounded border-2 border-slate-300 bg-white p-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
                M-3 · Geocode Foundation
              </div>
              <h2 className="text-xl font-black text-slate-900 mt-0.5">
                Reconcile Motive geofences with MASCI projects
              </h2>
              <p className="text-sm text-slate-600 max-w-2xl mt-1">
                Motive provides coordinates. MASCI provides identity. Approve a
                match only when the geofence truly belongs to the project. This
                screen never writes to Motive.
              </p>
            </div>
            <div className="flex gap-2 shrink-0">
              <Button
                onClick={runImport}
                disabled={imports}
                variant="outline"
                className="border-2"
                data-testid="recon-import-btn"
              >
                {imports ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <ArrowDownToLine className="w-4 h-4 mr-1" />}
                Import Geofences
              </Button>
              <Button
                onClick={runReconcile}
                disabled={imports}
                className="bg-slate-900 hover:bg-black text-white"
                data-testid="recon-run-btn"
              >
                <RefreshCw className="w-4 h-4 mr-1" />
                Run Reconciliation
              </Button>
            </div>
          </div>
        </div>

        {/* Counts strip */}
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2" data-testid="recon-counts">
          {[
            { key: "total",     label: "Total",     color: "bg-slate-100 text-slate-900" },
            { key: "high",      label: "High",      color: "bg-emerald-50 text-emerald-800 border-emerald-300" },
            { key: "medium",    label: "Medium",    color: "bg-amber-50 text-amber-900 border-amber-300" },
            { key: "low",       label: "Low",       color: "bg-red-50 text-red-800 border-red-300" },
            { key: "verified",  label: "Verified",  color: "bg-emerald-100 text-emerald-900 border-emerald-400" },
            { key: "rejected",  label: "Rejected",  color: "bg-slate-200 text-slate-700" },
          ].map((c) => (
            <div
              key={c.key}
              className={`px-3 py-2 rounded border ${c.color}`}
              data-testid={`recon-count-${c.key}`}
            >
              <div className="font-mono text-[10px] uppercase tracking-wider opacity-80">{c.label}</div>
              <div className="text-2xl font-black">{counts[c.key] ?? 0}</div>
            </div>
          ))}
        </div>

        {/* Filter + bulk-approve */}
        <div className="flex flex-wrap items-center gap-2 justify-between rounded border-2 border-slate-200 bg-white p-3">
          <div className="flex flex-wrap gap-1.5">
            {["all", "high", "medium", "low", "verified", "rejected"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={
                  "px-3 py-1.5 rounded text-xs font-mono font-bold uppercase tracking-wider border " +
                  (filter === f
                    ? "bg-slate-900 text-white border-slate-900"
                    : "bg-white text-slate-700 border-slate-300 hover:border-slate-500")
                }
                data-testid={`recon-filter-${f}`}
              >
                {f}
              </button>
            ))}
          </div>
          <Button
            onClick={bulkApprove}
            disabled={selected.size === 0 || !allHighSelected}
            className="bg-emerald-700 hover:bg-emerald-800 text-white"
            data-testid="recon-bulk-approve-btn"
            title={
              selected.size === 0
                ? "Select rows first"
                : !allHighSelected
                  ? "Bulk approve is restricted to HIGH band only"
                  : `Approve ${selected.size} HIGH rows`
            }
          >
            <CheckCircle2 className="w-4 h-4 mr-1" />
            Bulk Approve {selected.size > 0 ? `(${selected.size})` : ""}
          </Button>
        </div>

        {/* Table */}
        <div className="rounded border-2 border-slate-300 bg-white overflow-x-auto" data-testid="recon-table-wrap">
          {loading ? (
            <div className="p-8 text-center text-slate-500">
              <Loader2 className="w-5 h-5 animate-spin inline mr-2" />
              Loading…
            </div>
          ) : rows.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-sm">
              No rows for this filter. Try “Import Geofences” + “Run Reconciliation”.
            </div>
          ) : (
            <table className="w-full text-sm" data-testid="recon-table">
              <thead className="bg-slate-100 text-left font-mono text-[10px] uppercase tracking-wide text-slate-700">
                <tr>
                  <th className="px-2 py-2 w-8"></th>
                  <th className="px-3 py-2">Geofence</th>
                  <th className="px-3 py-2">→ Proposed Project</th>
                  <th className="px-3 py-2">Confidence</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2 w-72">Action</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => {
                  const band = BAND_STYLES[r.confidence_band] || BAND_STYLES.low;
                  const stat = STATUS_STYLES[r.geocode_status] || STATUS_STYLES["Imported"];
                  const terminal = r.geocode_status === "Verified" || r.geocode_status === "Rejected";
                  const isSel = selected.has(r.id);
                  return (
                    <tr
                      key={r.id}
                      className="border-t border-slate-100 hover:bg-slate-50/50"
                      data-testid={`recon-row-${r.id}`}
                    >
                      <td className="px-2 py-2">
                        <input
                          type="checkbox"
                          checked={isSel}
                          disabled={terminal || r.confidence_band !== "high"}
                          onChange={() => toggleSelect(r.id)}
                          className="w-4 h-4"
                          data-testid={`recon-row-select-${r.id}`}
                        />
                      </td>
                      <td className="px-3 py-2">
                        <div className="font-bold text-slate-900 flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          {r.name || "—"}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          {r.motive_category || "—"} · radius {r.geofence_radius || "—"} ft
                          {r.latitude && r.longitude && (
                            <> · {r.latitude.toFixed(4)}, {r.longitude.toFixed(4)}</>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-2">
                        <div className="font-mono font-bold text-slate-900">
                          {r.project_number || r.proposed_project_number || "—"}
                        </div>
                        <div className="text-[11px] text-slate-600">{r.proposed_project_name || ""}</div>
                      </td>
                      <td className="px-3 py-2">
                        <div className={`inline-flex items-center gap-2 px-2 py-1 rounded border font-mono text-xs font-bold ${band.bg} ${band.border} ${band.text}`}>
                          {band.label}
                          {r.confidence_score != null && (
                            <span className="opacity-70">{(r.confidence_score * 100).toFixed(0)}%</span>
                          )}
                        </div>
                        {r.match_signal && (
                          <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                            {r.match_signal.kind} · {r.match_signal.evidence}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <span className={`px-2 py-0.5 rounded font-mono text-[10px] uppercase tracking-wider font-bold ${stat.bg} ${stat.text}`}>
                          {r.geocode_status}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        {terminal ? (
                          <span className="text-slate-400 text-xs italic">—</span>
                        ) : reassignFor === r.id ? (
                          <div className="flex gap-1 items-center">
                            <input
                              type="text"
                              value={reassignPn}
                              onChange={(e) => setReassignPn(e.target.value)}
                              placeholder="Project #"
                              className="border-2 border-slate-300 rounded px-2 py-1 text-xs font-mono w-28"
                              data-testid={`recon-reassign-input-${r.id}`}
                            />
                            <Button
                              size="sm"
                              onClick={reassign}
                              disabled={busyId === r.id || !reassignPn.trim()}
                              className="h-7 bg-slate-900 hover:bg-black text-white text-xs"
                              data-testid={`recon-reassign-confirm-${r.id}`}
                            >Save</Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => { setReassignFor(null); setReassignPn(""); }}
                              className="h-7 border-2 text-xs"
                            >Cancel</Button>
                          </div>
                        ) : (
                          <div className="flex gap-1.5">
                            <Button
                              size="sm"
                              onClick={() => approve(r.id)}
                              disabled={busyId === r.id || !r.proposed_project_number}
                              className="h-7 bg-emerald-700 hover:bg-emerald-800 text-white text-xs"
                              data-testid={`recon-approve-${r.id}`}
                              title={r.proposed_project_number ? "Approve proposal" : "No proposal — use Reassign"}
                            >
                              <CheckCircle2 className="w-3.5 h-3.5 mr-0.5" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              onClick={() => reject(r.id)}
                              disabled={busyId === r.id}
                              variant="outline"
                              className="h-7 border-2 border-red-300 text-red-700 hover:bg-red-50 text-xs"
                              data-testid={`recon-reject-${r.id}`}
                            >
                              <XCircle className="w-3.5 h-3.5 mr-0.5" />
                              Reject
                            </Button>
                            <Button
                              size="sm"
                              onClick={() => { setReassignFor(r.id); setReassignPn(r.proposed_project_number || ""); }}
                              disabled={busyId === r.id}
                              variant="outline"
                              className="h-7 border-2 text-xs"
                              data-testid={`recon-reassign-${r.id}`}
                            >
                              <Shuffle className="w-3.5 h-3.5 mr-0.5" />
                              Reassign
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <div className="text-xs text-slate-500 font-mono">
          <Link to="/admin/jobs" className="hover:underline">
            ← Back to Jobs & Field <ChevronRight className="inline w-3 h-3 rotate-180" />
          </Link>
        </div>
      </div>
    </AdminShell>
  );
}
