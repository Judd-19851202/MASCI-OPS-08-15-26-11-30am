import React from "react";

export function ResourceTable({ rows = [], kind = "resource", dataTestId = "resource-table" }) {
  if (!rows.length) {
    return (
      <div
        className="rounded-[1.5rem] border border-dashed border-slate-300 bg-white/80 p-6 text-sm text-slate-500"
        data-testid={`${dataTestId}-empty`}
      >
        No governed {kind} evidence is available yet.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-[1.5rem] border border-slate-200 bg-white/95 shadow-sm" data-testid={dataTestId}>
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-left text-[11px] uppercase tracking-[0.2em] text-slate-500">
          <tr>
            <th className="px-4 py-3">{kind}</th>
            <th className="px-4 py-3">Unit</th>
            <th className="px-4 py-3 text-right">Accepted</th>
            <th className="px-4 py-3 text-right">Hours / qty</th>
            <th className="px-4 py-3 text-right">Productivity</th>
            <th className="px-4 py-3 text-right">Utilization</th>
            <th className="px-4 py-3">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${kind}-${row.id}-${row.unit}`} className="border-t border-slate-100" data-testid={`${dataTestId}-row-${row.id}`}>
              <td className="px-4 py-3">
                <div className="font-semibold text-slate-900">{row.label || row.id}</div>
                <div className="text-xs text-slate-500">{(row.work_block_ids || []).slice(0, 3).join(", ") || "No Work Block lineage"}</div>
              </td>
              <td className="px-4 py-3 text-slate-600">{row.unit || "—"}</td>
              <td className="px-4 py-3 text-right font-semibold text-slate-900">{row.accepted_quantity ?? "—"}</td>
              <td className="px-4 py-3 text-right text-slate-600">{row.hours ?? row.material_quantity ?? "—"}</td>
              <td className="px-4 py-3 text-right text-slate-900">{row.productivity ?? "—"}</td>
              <td className="px-4 py-3 text-right text-slate-900">{row.utilization ?? "—"}</td>
              <td className="px-4 py-3">
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-700">{row.confidence || "—"}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}