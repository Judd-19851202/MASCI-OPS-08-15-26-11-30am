/**
 * pm/command/PmSafetyImpactBoard.jsx — Section 5.
 * Open incidents + CAPAs scoped to this PM.
 */
import React, { useCallback, useEffect, useState } from "react";
import PmBoardShell, { TrustChip } from "./PmBoardShell";
import { pmCommandApi } from "./pmCommandApi";

export default function PmSafetyImpactBoard({ projectNumber }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    setRefreshing(true);
    try {
      const d = await pmCommandApi.safetyImpact(projectNumber);
      setData(d);
    } catch (e) { setError(e?.message || String(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, [projectNumber]);
  useEffect(() => { load(); }, [load]);

  const incidents = data?.incidents || [];
  const capas = data?.capas || [];
  const counts = data?.counts || {};

  const totalRows = incidents.length + capas.length;

  return (
    <PmBoardShell
      title="Safety Impact"
      subtitle={`${counts.incidents || 0} open incidents · ${counts.capas || 0} open capas`}
      count={totalRows}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={!loading && totalRows === 0}
      emptyText="No open safety items for this PM scope."
      testId="pm-cc-safety"
    >
      {incidents.length > 0 ? (
        <div className="space-y-1.5">
          <h3 className="text-[10px] uppercase tracking-widest font-bold text-slate-500">Incidents</h3>
          <div className="overflow-x-auto -mx-3 sm:mx-0">
            <table className="w-full min-w-[700px] text-xs sm:text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-200">
                  <th className="py-2 pl-3 pr-2">Summary</th>
                  <th className="py-2 px-2">Severity</th>
                  <th className="py-2 px-2">Project</th>
                  <th className="py-2 px-2">Occurred</th>
                  <th className="py-2 pr-3 pl-2">Status</th>
                </tr>
              </thead>
              <tbody data-testid="pm-cc-safety-incident-rows">
                {incidents.map((r, i) => (
                  <tr
                    key={`inc-${r.incident_id || i}`}
                    data-testid={`pm-cc-safety-incident-row-${i}`}
                    className="border-b border-slate-100 hover:bg-slate-50"
                  >
                    <td className="py-2 pl-3 pr-2 text-slate-700 max-w-md truncate" title={r.summary}>{r.summary || "—"}</td>
                    <td className="py-2 px-2">
                      <TrustChip state="incident_open">{r.severity || "—"}</TrustChip>
                    </td>
                    <td className="py-2 px-2 font-mono text-slate-700">{r.project_number || "—"}</td>
                    <td className="py-2 px-2 font-mono text-[11px] text-slate-600">
                      {String(r.occurred_at || "—").slice(0, 16).replace("T", " ")}
                    </td>
                    <td className="py-2 pr-3 pl-2 text-slate-700">{r.resolution_status || r.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {capas.length > 0 ? (
        <div className="space-y-1.5 mt-4">
          <h3 className="text-[10px] uppercase tracking-widest font-bold text-slate-500">Corrective Actions (CAPAs)</h3>
          <div className="overflow-x-auto -mx-3 sm:mx-0">
            <table className="w-full min-w-[700px] text-xs sm:text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-200">
                  <th className="py-2 pl-3 pr-2">Summary</th>
                  <th className="py-2 px-2">Project</th>
                  <th className="py-2 px-2">Due</th>
                  <th className="py-2 pr-3 pl-2">Status</th>
                </tr>
              </thead>
              <tbody data-testid="pm-cc-safety-capa-rows">
                {capas.map((r, i) => (
                  <tr
                    key={`capa-${r.capa_id || i}`}
                    data-testid={`pm-cc-safety-capa-row-${i}`}
                    className="border-b border-slate-100 hover:bg-slate-50"
                  >
                    <td className="py-2 pl-3 pr-2 text-slate-700 max-w-md truncate" title={r.summary}>{r.summary || "—"}</td>
                    <td className="py-2 px-2 font-mono text-slate-700">{r.project_number || "—"}</td>
                    <td className="py-2 px-2 font-mono text-[11px] text-slate-600">
                      {String(r.due_at || "—").slice(0, 16).replace("T", " ")}
                    </td>
                    <td className="py-2 pr-3 pl-2">
                      <TrustChip state="capa_open">{r.status}</TrustChip>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </PmBoardShell>
  );
}
