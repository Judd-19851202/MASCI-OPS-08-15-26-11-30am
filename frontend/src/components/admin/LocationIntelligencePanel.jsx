// M-3 · M3-5 · Location Intelligence panel for the Admin Jobs page.
// VISIBILITY ONLY — no operational workflow changes, no editing of jobs,
// no Motive writes. Pulls /api/admin/locations/by-project to overlay
// geocode + linked-geofence info onto the existing job master list.
import React, { useEffect, useState, useMemo, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { MapPin, AlertCircle, CheckCircle2, ChevronRight, Loader2 } from "lucide-react";

export default function LocationIntelligencePanel() {
  const [verified, setVerified] = useState({});
  const [proposed, setProposed] = useState({});
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const [locRes, jobRes] = await Promise.all([
          api.get("/admin/locations/by-project"),
          api.get("/admin/jobs?include_archived=false"),
        ]);
        if (cancelled) return;
        setVerified(locRes.data.verified || {});
        setProposed(locRes.data.proposed || {});
        const list = jobRes.data?.jobs || jobRes.data?.records || jobRes.data || [];
        setJobs((Array.isArray(list) ? list : []).filter((j) => j.active !== false));
      } catch {
        if (!cancelled) { setVerified({}); setProposed({}); setJobs([]); }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const stats = useMemo(() => {
    const total = jobs.length;
    const linked = jobs.filter((j) => !!verified[j.project_number]).length;
    const pending = jobs.filter(
      (j) => !verified[j.project_number] && (proposed[j.project_number] || []).length > 0
    ).length;
    const orphan = total - linked - pending;
    return { total, linked, pending, orphan, pct: total > 0 ? Math.round((linked / total) * 100) : 0 };
  }, [jobs, verified, proposed]);

  return (
    <div
      className="rounded border-2 border-slate-300 bg-white p-4 space-y-3"
      data-testid="location-intel-panel"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
            M-3 · Location Intelligence
          </div>
          <div className="text-base font-black text-slate-900 mt-0.5">
            Project ↔ Motive geofence coverage
          </div>
          <p className="text-xs text-slate-600 mt-1 max-w-xl">
            Read-only overlay. Approve / reject linkages from the
            Reconciliation screen.
          </p>
        </div>
        <Link to="/admin/geofence-reconciliation">
          <Button
            variant="outline"
            className="border-2 border-slate-900 text-slate-900 hover:bg-slate-50"
            data-testid="location-intel-open-recon"
          >
            Open Reconciliation
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="location-intel-stats">
        <Stat label="Active jobs"           value={stats.total}                           tone="slate" />
        <Stat label="Verified geofence"     value={stats.linked}    sub={`${stats.pct}%`} tone="emerald" />
        <Stat label="Pending review"        value={stats.pending}                         tone="amber" />
        <Stat label="No proposal"           value={stats.orphan}                          tone="red" />
      </div>

      <div className="rounded border border-slate-200 overflow-x-auto">
        {loading ? (
          <div className="p-6 text-center text-slate-500 text-sm">
            <Loader2 className="w-4 h-4 animate-spin inline mr-2" />Loading…
          </div>
        ) : jobs.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-sm">No active jobs.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left font-mono text-[10px] uppercase tracking-wide text-slate-700">
              <tr>
                <th className="px-3 py-2">Project #</th>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Linked Geofence</th>
                <th className="px-3 py-2">Geocode Status</th>
                <th className="px-3 py-2">Lat / Lng</th>
                <th className="px-3 py-2">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => {
                const v = verified[j.project_number];
                const p = (proposed[j.project_number] || [])[0];
                const row = v || p;
                const tone = v
                  ? { dot: "bg-emerald-500", label: "Verified" }
                  : p
                    ? { dot: "bg-amber-500", label: "Pending review" }
                    : { dot: "bg-red-400", label: "Not geocoded" };
                return (
                  <tr
                    key={j.project_number}
                    className="border-t border-slate-100"
                    data-testid={`location-intel-row-${j.project_number}`}
                  >
                    <td className="px-3 py-2 font-mono font-bold text-slate-900">{j.project_number}</td>
                    <td className="px-3 py-2 text-slate-700">{j.project_name}</td>
                    <td className="px-3 py-2">
                      {row ? (
                        <span className="flex items-center gap-1 text-slate-800">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          {row.name}
                        </span>
                      ) : (
                        <span className="text-slate-400 italic flex items-center gap-1">
                          <AlertCircle className="w-3.5 h-3.5" />
                          none
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-mono text-[10px] uppercase tracking-wider font-bold bg-slate-100 text-slate-700">
                        <span className={`w-1.5 h-1.5 rounded-full ${tone.dot}`} />
                        {tone.label}
                      </span>
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-slate-600">
                      {row?.latitude != null && row?.longitude != null
                        ? `${row.latitude.toFixed(4)}, ${row.longitude.toFixed(4)}`
                        : "—"}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {row?.confidence_score != null
                        ? `${(row.confidence_score * 100).toFixed(0)}%`
                        : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, sub, tone }) {
  const tones = {
    slate:   "bg-slate-100 text-slate-900",
    emerald: "bg-emerald-50 text-emerald-900 border border-emerald-300",
    amber:   "bg-amber-50 text-amber-900 border border-amber-300",
    red:     "bg-red-50 text-red-800 border border-red-300",
  };
  return (
    <div className={`px-3 py-2 rounded ${tones[tone] || tones.slate}`}>
      <div className="font-mono text-[10px] uppercase tracking-wider opacity-80">{label}</div>
      <div className="text-2xl font-black flex items-baseline gap-2">
        {value} {sub && <span className="text-xs opacity-70">{sub}</span>}
      </div>
    </div>
  );
}
