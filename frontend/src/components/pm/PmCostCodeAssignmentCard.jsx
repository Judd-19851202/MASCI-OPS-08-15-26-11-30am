import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";

export default function PmCostCodeAssignmentCard({ projectNumber }) {
  const [registry, setRegistry] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [progress, setProgress] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!projectNumber) return;
    let alive = true;
    (async () => {
      try {
        const [{ data: registryRes }, { data: assignmentRes }] = await Promise.all([
          api.get("/cost-codes/registry"),
          api.get(`/cost-codes/projects/${encodeURIComponent(projectNumber)}/assignments`),
        ]);
        if (!alive) return;
        setRegistry(Array.isArray(registryRes?.items) ? registryRes.items : []);
        setAssignments(Array.isArray(assignmentRes?.assignments) ? assignmentRes.assignments : []);
        setProgress(assignmentRes?.progress || null);
      } catch (error) {
        if (!alive) return;
        const detail = error?.response?.data?.detail;
        const msg = typeof detail === "string" ? detail : (detail?.reason || detail?.explanation || "Failed to load project cost-code setup");
        toast.error(msg);
      }
    })();
    return () => { alive = false; };
  }, [projectNumber]);

  const addCode = (code) => {
    const source = registry.find((item) => item.code === code);
    if (!source) return;
    if (assignments.some((item) => item.code === code)) return;
    setAssignments((prev) => ([...prev, {
      code: source.code,
      item_name: source.item_name,
      unit_of_measure: source.unit_of_measure,
      bid_unit_price: source.bid_unit_price,
      target_man_hours: source.target_man_hours,
      bid_quantity: 0,
      original_quantity: 0,
      authorized_quantity: 0,
      forecast_quantity: 0,
      cpm_activity_id: "",
      cpm_activity_name: "",
      schedule_phase: "",
      planned_performer: "",
      notes: "",
    }]));
  };

  const update = (index, delta) => {
    setAssignments((prev) => prev.map((row, i) => (i === index ? { ...row, ...delta } : row)));
  };

  const remove = (index) => {
    setAssignments((prev) => prev.filter((_, i) => i !== index));
  };

  const save = async () => {
    setSaving(true);
    try {
      const { data } = await api.put(`/cost-codes/projects/${encodeURIComponent(projectNumber)}/assignments`, {
        assignments: assignments.map((row) => ({
          ...row,
          bid_quantity: Number(row.authorized_quantity ?? row.bid_quantity ?? 0),
          original_quantity: Number(row.original_quantity || row.authorized_quantity || row.bid_quantity || 0),
          authorized_quantity: Number(row.authorized_quantity ?? row.bid_quantity ?? 0),
          forecast_quantity: Number(row.forecast_quantity || row.authorized_quantity || row.bid_quantity || 0),
          bid_unit_price: Number(row.bid_unit_price || 0),
          target_man_hours: Number(row.target_man_hours || 0),
        })),
      });
      setAssignments(Array.isArray(data?.assignments) ? data.assignments : []);
      setProgress(data?.progress || null);
      toast.success("Project cost codes updated");
    } catch (error) {
      const detail = error?.response?.data?.detail;
      const msg = typeof detail === "string" ? detail : (detail?.reason || detail?.explanation || "Save failed");
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" data-testid="pm-cost-code-assignment-card">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-700">Job setup</p>
          <h2 className="mt-1 text-xl font-bold text-slate-900">Assigned cost codes</h2>
          <p className="mt-1 text-sm text-slate-600">Attach bid quantities now so the field can report installed quantities and job progress can roll forward.</p>
        </div>
        <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700" data-testid="pm-cost-code-progress-pill">
          Progress {Number(progress?.overall_percent_complete || 0).toFixed(2)}%
        </div>
      </div>

      <div className="mt-4 flex max-h-36 flex-wrap gap-2 overflow-y-auto" data-testid="pm-cost-code-registry-pills">
        {registry.map((item) => (
          <button key={item.code} type="button" onClick={() => addCode(item.code)} className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:border-slate-300" data-testid={`pm-cost-code-add-${item.code.replace(/[^a-zA-Z0-9]+/g, '-').toLowerCase()}`}>
            {item.code}
          </button>
        ))}
      </div>

      <div className="mt-5 space-y-3">
        {assignments.map((row, index) => (
          <div key={`${row.code}-${index}`} className="grid gap-3 rounded-2xl border border-slate-100 p-4 lg:grid-cols-[1.1fr_0.7fr_0.7fr_0.7fr_0.8fr_0.9fr_0.9fr_auto]" data-testid={`pm-cost-code-assignment-row-${index}`}>
            <div>
              <div className="text-sm font-semibold text-slate-900">{row.code}</div>
              <div className="text-xs text-slate-500">{row.item_name}</div>
            </div>
            <input type="number" step="0.01" value={row.original_quantity ?? row.bid_quantity ?? ""} onChange={(e) => update(index, { original_quantity: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="Original qty" data-testid={`pm-cost-code-original-qty-${index}`} />
            <input type="number" step="0.01" value={row.authorized_quantity ?? row.bid_quantity ?? ""} onChange={(e) => update(index, { authorized_quantity: e.target.value, bid_quantity: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="Authorized qty" data-testid={`pm-cost-code-authorized-qty-${index}`} />
            <input type="number" step="0.01" value={row.forecast_quantity ?? row.authorized_quantity ?? row.bid_quantity ?? ""} onChange={(e) => update(index, { forecast_quantity: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="Forecast qty" data-testid={`pm-cost-code-forecast-qty-${index}`} />
            <input type="text" value={row.cpm_activity_id || ""} onChange={(e) => update(index, { cpm_activity_id: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="CPM ID" data-testid={`pm-cost-code-cpm-id-${index}`} />
            <input type="text" value={row.schedule_phase || ""} onChange={(e) => update(index, { schedule_phase: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="Phase" data-testid={`pm-cost-code-phase-${index}`} />
            <input type="text" value={row.planned_performer || ""} onChange={(e) => update(index, { planned_performer: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="Planned performer" data-testid={`pm-cost-code-planned-performer-${index}`} />
            <input type="text" value={row.cpm_activity_name || ""} onChange={(e) => update(index, { cpm_activity_name: e.target.value })} className="rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="CPM activity name" data-testid={`pm-cost-code-cpm-name-${index}`} />
            <button type="button" onClick={() => remove(index)} className="rounded-full border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700" data-testid={`pm-cost-code-remove-${index}`}>Remove</button>
          </div>
        ))}
      </div>

      <div className="mt-5 flex justify-end">
        <button type="button" onClick={save} disabled={saving} className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white" data-testid="pm-cost-code-save-button">
          {saving ? "Saving…" : "Save assignments"}
        </button>
      </div>
    </div>
  );
}
