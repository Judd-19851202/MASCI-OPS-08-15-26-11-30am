import React, { useEffect, useState } from "react";
import AdminShell from "@/components/AdminShell";
import { api } from "@/lib/api";
import { toast } from "sonner";

const EMPTY = {
  code: "",
  item_name: "",
  unit_of_measure: "LF",
  bid_unit_price: "",
  target_man_hours: "",
};

export default function AdminCostRegistry() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const { data } = await api.get("/cost-codes/registry");
      setItems(Array.isArray(data?.items) ? data.items : []);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to load cost registry");
    }
  };

  useEffect(() => { load(); }, []);

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/cost-codes/registry", {
        ...form,
        bid_unit_price: Number(form.bid_unit_price || 0),
        target_man_hours: Number(form.target_man_hours || 0),
      });
      toast.success("Cost code saved");
      setForm(EMPTY);
      await load();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AdminShell title="Universal Cost Registry" section="jobs">
      <div className="mx-auto max-w-6xl space-y-8" data-testid="admin-cost-registry-page">
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-red-700">Enterprise Spine</p>
          <h1 className="mt-2 text-4xl font-black text-slate-900">Universal Cost Registry</h1>
          <p className="mt-3 max-w-3xl text-sm text-slate-600">
            Maintain the master cost-code library used by PM job setup, field quantity entry, and progress rollups.
          </p>
        </div>

        <form onSubmit={save} className="grid gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:grid-cols-5" data-testid="admin-cost-registry-form">
          <input className="rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="536 - D-Curb" value={form.code} onChange={(e) => setForm((p) => ({ ...p, code: e.target.value }))} data-testid="admin-cost-registry-code" />
          <input className="rounded-xl border border-slate-300 px-3 py-2 text-sm" placeholder="Item name" value={form.item_name} onChange={(e) => setForm((p) => ({ ...p, item_name: e.target.value }))} data-testid="admin-cost-registry-item-name" />
          <select className="rounded-xl border border-slate-300 px-3 py-2 text-sm" value={form.unit_of_measure} onChange={(e) => setForm((p) => ({ ...p, unit_of_measure: e.target.value }))} data-testid="admin-cost-registry-unit">
            {['LF', 'CY', 'TONS', 'LS'].map((unit) => <option key={unit} value={unit}>{unit}</option>)}
          </select>
          <input className="rounded-xl border border-slate-300 px-3 py-2 text-sm" type="number" step="0.01" placeholder="Bid unit price" value={form.bid_unit_price} onChange={(e) => setForm((p) => ({ ...p, bid_unit_price: e.target.value }))} data-testid="admin-cost-registry-bid-unit-price" />
          <input className="rounded-xl border border-slate-300 px-3 py-2 text-sm" type="number" step="0.01" placeholder="Target man-hours" value={form.target_man_hours} onChange={(e) => setForm((p) => ({ ...p, target_man_hours: e.target.value }))} data-testid="admin-cost-registry-target-man-hours" />
          <div className="md:col-span-5 flex justify-end">
            <button type="submit" disabled={saving} className="rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white" data-testid="admin-cost-registry-save-button">
              {saving ? 'Saving…' : 'Save cost code'}
            </button>
          </div>
        </form>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" data-testid="admin-cost-registry-table">
          <div className="grid grid-cols-[1.2fr_2fr_0.7fr_0.8fr_0.8fr] gap-3 border-b border-slate-200 pb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            <div>Code</div><div>Item</div><div>Unit</div><div>Bid $</div><div>MH</div>
          </div>
          <div className="mt-3 space-y-2">
            {items.map((item, index) => (
              <button key={item.id || item.code || index} type="button" onClick={() => setForm({
                code: item.code || "",
                item_name: item.item_name || "",
                unit_of_measure: item.unit_of_measure || "LF",
                bid_unit_price: item.bid_unit_price ?? "",
                target_man_hours: item.target_man_hours ?? "",
              })} className="grid w-full grid-cols-[1.2fr_2fr_0.7fr_0.8fr_0.8fr] gap-3 rounded-2xl border border-slate-100 px-3 py-3 text-left text-sm text-slate-700 hover:border-slate-300" data-testid={`admin-cost-registry-row-${index}`}>
                <div className="font-semibold text-slate-900">{item.code}</div>
                <div>{item.item_name}</div>
                <div>{item.unit_of_measure}</div>
                <div>{item.bid_unit_price}</div>
                <div>{item.target_man_hours}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </AdminShell>
  );
}
