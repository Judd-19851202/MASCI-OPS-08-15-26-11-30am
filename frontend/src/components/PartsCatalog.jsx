import React, { useEffect, useMemo, useState } from "react";
import { Wrench, Plus, Trash2, Loader2, Save, ShoppingCart, Mail, Search, Truck, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useT, getLang } from "@/lib/i18n";
import { translateUserInput } from "@/lib/translateOnSubmit";

/**
 * Per-unit parts catalog. Mechanics:
 *   1. Search a unit from the 589-unit fleet
 *   2. View/edit its 5 wear-item categories (filters / cutting edges /
 *      wiper blades / tires / other wear items)
 *   3. Tick the parts they need into an Order Cart
 *   4. One-click email the order to the parts office (Resend)
 *
 * Editing is gated to shop OR admin (handled server-side).
 * Backed by GET/PUT /api/equipment-parts/{unit} + POST /api/equipment-parts/order
 */

const CATEGORY_DEFS = [
  { key: "filters",          label: "Filters",          extras: [] },
  { key: "cutting_edges",    label: "Cutting Edges",    extras: [] },
  { key: "wiper_blades",     label: "Wiper Blades",     extras: ["size"] },
  { key: "tires",            label: "Tires",            extras: ["position", "size", "ply", "brand"] },
  { key: "other_wear_items", label: "Other Wear Items", extras: [] },
];

const emptyDoc = (unit_number) => ({
  unit_number,
  filters: [],
  cutting_edges: [],
  wiper_blades: [],
  tires: [],
  other_wear_items: [],
  updated_at: "",
  updated_by: "",
});

export default function PartsCatalog() {
  const { t } = useT();
  const [fleet, setFleet] = useState([]);
  const [search, setSearch] = useState("");
  const [unit, setUnit] = useState(null); // selected fleet entry
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [updatedBy, setUpdatedBy] = useState("");
  const [cart, setCart] = useState([]); // [{key, name, part_number, qty, category, notes}]
  const [orderOpen, setOrderOpen] = useState(false);
  const [exporting, setExporting] = useState(false);

  const onExport = async () => {
    setExporting(true);
    try {
      const r = await api.get("/admin/equipment-parts/export", { responseType: "blob" });
      const cd = r.headers["content-disposition"] || r.headers["Content-Disposition"] || "";
      const m = /filename="?([^";]+)"?/i.exec(cd);
      const fname = m ? m[1] : "MASCI_parts.xlsx";
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = fname;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`Downloaded ${fname}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Export failed");
    } finally {
      setExporting(false);
    }
  };

  // Load 589-unit fleet for the picker
  useEffect(() => {
    (async () => {
      try {
        const r = await api.get("/equipment-master");
        // Drop entries with no unit_number — they'd resolve to /equipment-parts/
        // (trailing slash) which the K8s ingress 307s to plain http and the
        // browser blocks as Mixed Content.
        const items = (r.data?.items || []).filter((u) => (u.unit_number || "").trim());
        setFleet(items);
      } catch {
        toast.error(t("Could not load fleet list"));
      }
    })();
  }, []); // eslint-disable-line

  const filteredFleet = useMemo(() => {
    const s = search.trim().toLowerCase();
    if (!s) return fleet.slice(0, 100);
    return fleet
      .filter(
        (u) =>
          (u.unit_number || "").toLowerCase().includes(s) ||
          (u.make || "").toLowerCase().includes(s) ||
          (u.model || "").toLowerCase().includes(s) ||
          (u.category || "").toLowerCase().includes(s)
      )
      .slice(0, 100);
  }, [fleet, search]);

  const pickUnit = async (u) => {
    setUnit(u);
    setLoading(true);
    try {
      const r = await api.get(`/equipment-parts/${encodeURIComponent(u.unit_number)}`);
      setDoc(r.data || emptyDoc(u.unit_number));
    } catch {
      setDoc(emptyDoc(u.unit_number));
    } finally {
      setLoading(false);
    }
  };

  const updateRow = (catKey, idx, patch) => {
    setDoc((p) => {
      const copy = { ...p, [catKey]: [...(p?.[catKey] || [])] };
      copy[catKey][idx] = { ...copy[catKey][idx], ...patch };
      return copy;
    });
  };
  const addRow = (catKey) => {
    setDoc((p) => ({
      ...p,
      [catKey]: [...(p?.[catKey] || []), { name: "", part_number: "", qty: "1", notes: "" }],
    }));
  };
  const deleteRow = (catKey, idx) => {
    setDoc((p) => ({
      ...p,
      [catKey]: (p?.[catKey] || []).filter((_, i) => i !== idx),
    }));
  };

  const save = async () => {
    if (!doc || !unit) return;
    if (!updatedBy.trim()) {
      toast.error(t("Enter your name before saving."));
      return;
    }
    setSaving(true);
    try {
      let payload = {
        filters: doc.filters || [],
        cutting_edges: doc.cutting_edges || [],
        wiper_blades: doc.wiper_blades || [],
        tires: doc.tires || [],
        other_wear_items: doc.other_wear_items || [],
        updated_by: updatedBy.trim(),
      };
      // ES → EN: translate part names + notes before persisting.
      // Part numbers, sizes, ply, brand are passed through unchanged
      // (proper nouns / SKUs / numerics — the translateOnSubmit walker
      // already skips data: URLs, dates, numbers, and the `*_number` key
      // pattern matches "part_number".)
      payload = await translateUserInput(payload, getLang());
      const r = await api.put(`/equipment-parts/${encodeURIComponent(unit.unit_number)}`, payload);
      setDoc(r.data);
      toast.success(t("Catalog saved."));
    } catch {
      toast.error(t("Could not save catalog."));
    } finally {
      setSaving(false);
    }
  };

  const addToCart = (catKey, row) => {
    const k = `${unit.unit_number}|${catKey}|${row.part_number}|${row.name}`;
    setCart((p) => {
      if (p.find((x) => x.key === k)) {
        toast.message(t("Already in order list"));
        return p;
      }
      return [
        ...p,
        {
          key: k,
          category: catKey,
          name: row.name,
          part_number: row.part_number,
          qty: row.qty || "1",
          notes: row.notes || "",
        },
      ];
    });
    toast.success(t("Added to order list"));
  };
  const removeFromCart = (k) => setCart((p) => p.filter((x) => x.key !== k));
  const updateCartQty = (k, qty) =>
    setCart((p) => p.map((x) => (x.key === k ? { ...x, qty } : x)));

  return (
    <div className="space-y-4" data-testid="parts-catalog">
      <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <div className="bg-slate-900 text-white px-4 py-3 flex items-center gap-3 flex-wrap">
          <Truck className="w-5 h-5 text-amber-400" />
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-400 font-bold flex-1">
            {t("Pick a Unit")}
          </span>
          <div className="flex items-center gap-1 bg-slate-800 border border-slate-700 rounded px-2">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t("Search unit, make, model, category…")}
              className="bg-transparent text-white placeholder:text-slate-500 px-2 py-1 text-xs focus:outline-none w-72"
              data-testid="parts-fleet-search"
            />
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={onExport}
            disabled={exporting}
            className="h-8 px-3 border-2 border-emerald-400 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 font-mono uppercase tracking-wide text-[11px]"
            data-testid="parts-export-btn"
            title="Download every parts entry across the fleet as XLSX"
          >
            {exporting ? (
              <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5 mr-1" />
            )}
            Export
          </Button>
        </div>
        <div className="max-h-56 overflow-y-auto" data-testid="parts-fleet-list">
          {filteredFleet.map((u, i) => (
            <button
              key={`${u.unit_number}-${i}`}
              type="button"
              onClick={() => pickUnit(u)}
              className={`w-full text-left px-4 py-2 text-sm border-b border-slate-100 hover:bg-amber-50 ${
                unit?.unit_number === u.unit_number ? "bg-amber-100 font-bold" : ""
              }`}
              data-testid={`parts-fleet-pick-${u.unit_number}`}
            >
              <span className="font-mono font-bold">{u.unit_number}</span>
              <span className="text-slate-700 ml-2">{u.make} {u.model}</span>
              <span className="text-slate-400 text-xs ml-2">· {u.category}</span>
            </button>
          ))}
          {filteredFleet.length === 0 && (
            <div className="p-6 text-center text-slate-500 text-sm">{t("No matching units.")}</div>
          )}
        </div>
      </div>

      {!unit && (
        <div className="text-center text-slate-500 py-12 bg-white border-2 border-dashed border-slate-300 rounded-md" data-testid="parts-empty-state">
          <Wrench className="w-10 h-10 mx-auto text-slate-400 mb-2" />
          <p className="font-display text-xl font-bold text-slate-700">{t("Pick a unit to view its parts catalog")}</p>
          <p className="text-sm mt-1">{t("Search the 589-unit fleet above. Each unit has filters, cutting edges, wiper blades, tires, and other wear items.")}</p>
        </div>
      )}

      {unit && doc && (
        <>
          <div className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid="parts-editor">
            <div className="bg-amber-50 border-b-2 border-amber-200 px-4 py-3 flex items-center justify-between gap-3 flex-wrap">
              <div>
                <div className="font-display text-xl font-black text-slate-900">
                  {unit.unit_number} · {unit.make} {unit.model}
                </div>
                <div className="text-xs font-mono uppercase tracking-wider text-slate-600 mt-0.5">
                  {unit.category || "—"}
                  {doc.updated_at && (
                    <> · {t("Last updated")}: {new Date(doc.updated_at).toLocaleString()} {t("by")} {doc.updated_by || "—"}</>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  value={updatedBy}
                  onChange={(e) => setUpdatedBy(e.target.value)}
                  placeholder={t("Your name")}
                  className="h-9 w-44 text-sm border-amber-300"
                  data-testid="parts-updated-by"
                />
                <Button
                  onClick={save}
                  disabled={saving}
                  className="h-9 px-3 bg-emerald-700 hover:bg-emerald-800 text-white font-bold uppercase text-xs"
                  data-testid="parts-save-btn"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Save className="w-4 h-4 mr-1" />}
                  {t("Save Catalog")}
                </Button>
              </div>
            </div>

            {loading ? (
              <div className="p-12 flex items-center justify-center text-slate-500">
                <Loader2 className="w-5 h-5 animate-spin mr-2" /> {t("Loading…")}
              </div>
            ) : (
              <div className="divide-y-2 divide-slate-100">
                {CATEGORY_DEFS.map((c) => (
                  <CategoryEditor
                    key={c.key}
                    catKey={c.key}
                    label={t(c.label)}
                    extras={c.extras}
                    rows={doc[c.key] || []}
                    onAdd={() => addRow(c.key)}
                    onChange={(idx, patch) => updateRow(c.key, idx, patch)}
                    onDelete={(idx) => deleteRow(c.key, idx)}
                    onAddToCart={(row) => addToCart(c.key, row)}
                  />
                ))}
              </div>
            )}
          </div>

          <OrderCart
            cart={cart}
            unit={unit}
            removeFromCart={removeFromCart}
            updateCartQty={updateCartQty}
            open={orderOpen}
            setOpen={setOrderOpen}
            requestedByDefault={updatedBy}
            clear={() => setCart([])}
          />
        </>
      )}
    </div>
  );
}

const CategoryEditor = ({ catKey, label, extras, rows, onAdd, onChange, onDelete, onAddToCart }) => {
  const { t } = useT();
  return (
    <div className="p-4 sm:p-5" data-testid={`parts-cat-${catKey}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base font-black text-slate-900 uppercase tracking-wide">
          {label}
          <span className="ml-2 text-xs font-mono text-slate-500">({rows.length})</span>
        </h3>
        <Button
          onClick={onAdd}
          variant="outline"
          size="sm"
          className="h-8 px-2 border-amber-400 text-amber-800 hover:bg-amber-50"
          data-testid={`parts-cat-${catKey}-add`}
        >
          <Plus className="w-3.5 h-3.5 mr-1" /> {t("Add Part")}
        </Button>
      </div>
      {rows.length === 0 ? (
        <div className="text-xs text-slate-400 italic">{t("No parts on file. Click Add Part.")}</div>
      ) : (
        <div className="space-y-2">
          {rows.map((row, idx) => (
            <div
              key={`${catKey}-${idx}`}
              className="grid grid-cols-12 gap-2 items-start bg-slate-50 border border-slate-200 rounded p-2"
              data-testid={`parts-row-${catKey}-${idx}`}
            >
              <Input
                value={row.name || ""}
                onChange={(e) => onChange(idx, { name: e.target.value })}
                placeholder={t("Part name")}
                className="col-span-3 h-9 text-xs"
                data-testid={`parts-row-${catKey}-${idx}-name`}
              />
              <Input
                value={row.part_number || ""}
                onChange={(e) => onChange(idx, { part_number: e.target.value })}
                placeholder={t("Part #")}
                className="col-span-2 h-9 text-xs font-mono"
                data-testid={`parts-row-${catKey}-${idx}-pn`}
              />
              <Input
                value={row.qty || ""}
                onChange={(e) => onChange(idx, { qty: e.target.value })}
                placeholder={t("Qty")}
                className="col-span-1 h-9 text-xs"
                data-testid={`parts-row-${catKey}-${idx}-qty`}
              />
              {extras.map((ex) => (
                <Input
                  key={ex}
                  value={row[ex] || ""}
                  onChange={(e) => onChange(idx, { [ex]: e.target.value })}
                  placeholder={t(ex.charAt(0).toUpperCase() + ex.slice(1))}
                  className={`col-span-${Math.max(1, Math.floor(8 / extras.length))} h-9 text-xs`}
                  data-testid={`parts-row-${catKey}-${idx}-${ex}`}
                />
              ))}
              <Input
                value={row.notes || ""}
                onChange={(e) => onChange(idx, { notes: e.target.value })}
                placeholder={t("Notes")}
                className={`col-span-${Math.max(1, 6 - extras.length)} h-9 text-xs`}
                data-testid={`parts-row-${catKey}-${idx}-notes`}
              />
              <div className="col-span-1 flex gap-1 justify-end">
                <Button
                  type="button"
                  onClick={() => onAddToCart(row)}
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9 text-emerald-700 hover:bg-emerald-50"
                  title={t("Add to order list")}
                  data-testid={`parts-row-${catKey}-${idx}-cart`}
                >
                  <ShoppingCart className="w-4 h-4" />
                </Button>
                <Button
                  type="button"
                  onClick={() => onDelete(idx)}
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9 text-red-600 hover:bg-red-50"
                  title={t("Remove part")}
                  data-testid={`parts-row-${catKey}-${idx}-del`}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const OrderCart = ({ cart, unit, removeFromCart, updateCartQty, requestedByDefault, clear }) => {
  const { t } = useT();
  const [requestedBy, setRequestedBy] = useState("");
  const [sendTo, setSendTo] = useState("");
  const [cc, setCc] = useState("");
  const [notes, setNotes] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (requestedByDefault && !requestedBy) setRequestedBy(requestedByDefault);
  }, [requestedByDefault]); // eslint-disable-line

  const sendOrder = async () => {
    if (cart.length === 0) {
      toast.error(t("Order list is empty."));
      return;
    }
    if (!requestedBy.trim()) {
      toast.error(t("Enter your name."));
      return;
    }
    const toList = sendTo.split(/[,;\s]+/).map((s) => s.trim()).filter(Boolean);
    if (toList.length === 0) {
      toast.error(t("Enter at least one email address to send to."));
      return;
    }
    const ccList = cc.split(/[,;\s]+/).map((s) => s.trim()).filter(Boolean);
    setSending(true);
    try {
      let orderPayload = {
        unit_number: unit.unit_number,
        equipment_label: `${unit.make || ""} ${unit.model || ""}`.trim(),
        requested_by: requestedBy.trim(),
        send_to: toList,
        cc: ccList,
        additional_notes: notes.trim(),
        items: cart.map((it) => ({
          name: it.name || "",
          part_number: it.part_number || "",
          qty: it.qty || "1",
          category: it.category || "",
          notes: it.notes || "",
        })),
      };
      // ES → EN: translate freeform fields (additional_notes, item.name,
      // item.notes). part_number is a SKU and stays as-is via the walker.
      orderPayload = await translateUserInput(orderPayload, getLang());
      await api.post("/equipment-parts/order", orderPayload);
      toast.success(t("Parts order emailed."));
      clear();
      setNotes("");
    } catch (err) {
      const msg = err?.response?.data?.detail || t("Could not send order email.");
      toast.error(typeof msg === "string" ? msg : t("Could not send order email."));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-white border-2 border-emerald-300 rounded-md overflow-hidden" data-testid="parts-order-cart">
      <div className="bg-emerald-700 text-white px-4 py-3 flex items-center gap-3 flex-wrap">
        <ShoppingCart className="w-5 h-5" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] font-bold flex-1">
          {t("Order List")} ({cart.length})
        </span>
      </div>
      {cart.length === 0 ? (
        <div className="p-6 text-center text-slate-500 text-sm" data-testid="parts-order-empty">
          {t("Tap the cart icon next to a part to add it. Then send the list to the parts office.")}
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="parts-order-table">
              <thead className="bg-slate-50">
                <tr className="border-b-2 border-slate-200">
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Part #")}</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Name")}</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Qty")}</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Category")}</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {cart.map((it) => (
                  <tr key={it.key} className="border-b border-slate-100">
                    <td className="px-3 py-2 font-mono text-slate-900">{it.part_number || "—"}</td>
                    <td className="px-3 py-2 text-slate-800">{it.name}</td>
                    <td className="px-3 py-2">
                      <Input
                        value={it.qty}
                        onChange={(e) => updateCartQty(it.key, e.target.value)}
                        className="h-8 w-16 text-sm"
                        data-testid={`parts-order-qty-${it.key}`}
                      />
                    </td>
                    <td className="px-3 py-2 text-slate-500 text-xs">{it.category}</td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        type="button"
                        onClick={() => removeFromCart(it.key)}
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-red-600 hover:bg-red-50"
                        data-testid={`parts-order-remove-${it.key}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4 border-t-2 border-slate-100">
            <Input
              value={requestedBy}
              onChange={(e) => setRequestedBy(e.target.value)}
              placeholder={t("Your name (mechanic)")}
              data-testid="parts-order-requested-by"
            />
            <Input
              value={sendTo}
              onChange={(e) => setSendTo(e.target.value)}
              placeholder={t("Send to email(s) — comma-separated")}
              data-testid="parts-order-to"
            />
            <Input
              value={cc}
              onChange={(e) => setCc(e.target.value)}
              placeholder={t("CC (optional)")}
              data-testid="parts-order-cc"
            />
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder={t("Additional notes (e.g. needed by Friday for PM service)")}
              rows={2}
              className="lg:col-span-2"
              data-testid="parts-order-notes"
            />
            <div className="lg:col-span-2 flex justify-end">
              <Button
                onClick={sendOrder}
                disabled={sending}
                className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold uppercase tracking-wide h-10 px-5"
                data-testid="parts-order-send"
              >
                {sending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Mail className="w-4 h-4 mr-2" />}
                {t("Email Order to Parts Office")}
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
