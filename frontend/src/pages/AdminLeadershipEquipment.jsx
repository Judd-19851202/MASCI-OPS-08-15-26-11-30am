// Admin — Field Leadership Equipment Catalog management.
// Two side-by-side panels: Equipment Catalog (with replacement value
// editing, disable/enable, search) and Manufacturers (add/disable). Plus
// an Export button for the cumulative equipment-checkout CSV.

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, Plus, Pencil, Search, Save, Power, X, Download, RefreshCw,
} from "lucide-react";
import { api, API } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";

const inputCls =
  "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-blue-600";

const fmtMoney = (n) =>
  `$${(Number(n) || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function AdminLeadershipEquipment() {
  const { t } = useT();
  const [catalog, setCatalog] = useState([]);
  const [makes, setMakes] = useState([]);
  const [search, setSearch] = useState("");
  const [showCatalogDialog, setShowCatalogDialog] = useState(false);
  const [editing, setEditing] = useState(null);
  const [showMakeDialog, setShowMakeDialog] = useState(false);
  const [editingMake, setEditingMake] = useState(null);

  const refresh = async () => {
    try {
      const [c, m] = await Promise.all([
        api.get("/field-leadership/admin/equipment-catalog"),
        api.get("/field-leadership/admin/equipment-makes"),
      ]);
      setCatalog(c.data?.items || []);
      setMakes(m.data?.items || []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not load equipment catalog"));
    }
  };

  useEffect(() => { refresh(); /* eslint-disable-next-line */ }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return catalog;
    return catalog.filter(
      (c) =>
        (c.name || "").toLowerCase().includes(q) ||
        (c.default_make || "").toLowerCase().includes(q) ||
        (c.category || "").toLowerCase().includes(q)
    );
  }, [catalog, search]);

  const openNew = () => {
    setEditing({ name: "", replacement_value: 0, default_make: "", category: "", active: true });
    setShowCatalogDialog(true);
  };
  const openEdit = (item) => {
    setEditing({ ...item });
    setShowCatalogDialog(true);
  };

  const saveItem = async () => {
    if (!editing.name?.trim()) {
      toast.error(t("Name required"));
      return;
    }
    try {
      if (editing.id) {
        await api.patch(`/field-leadership/admin/equipment-catalog/${editing.id}`, {
          name: editing.name,
          replacement_value: editing.replacement_value,
          default_make: editing.default_make,
          category: editing.category,
          active: editing.active,
        });
      } else {
        await api.post("/field-leadership/admin/equipment-catalog", editing);
      }
      toast.success(t("Saved"));
      setShowCatalogDialog(false);
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Save failed"));
    }
  };

  const toggleActive = async (item) => {
    try {
      await api.patch(`/field-leadership/admin/equipment-catalog/${item.id}`, {
        active: !item.active,
      });
      refresh();
    } catch {
      toast.error(t("Could not update"));
    }
  };

  const saveMake = async () => {
    if (!editingMake.name?.trim()) {
      toast.error(t("Name required"));
      return;
    }
    try {
      if (editingMake.id) {
        await api.patch(`/field-leadership/admin/equipment-makes/${editingMake.id}`, {
          name: editingMake.name, active: editingMake.active,
        });
      } else {
        await api.post("/field-leadership/admin/equipment-makes", editingMake);
      }
      toast.success(t("Saved"));
      setShowMakeDialog(false);
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Save failed"));
    }
  };

  const toggleMakeActive = async (m) => {
    try {
      await api.patch(`/field-leadership/admin/equipment-makes/${m.id}`, { active: !m.active });
      refresh();
    } catch {
      toast.error(t("Could not update"));
    }
  };

  const exportCsv = () => {
    const url = `${API}/field-leadership/admin/equipment-checkout-export.csv`;
    api.get(url.replace(API, ""), { responseType: "blob" })
      .then((r) => {
        const blobUrl = URL.createObjectURL(new Blob([r.data], { type: "text/csv" }));
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = "equipment_checkout_export.csv";
        a.click();
        setTimeout(() => URL.revokeObjectURL(blobUrl), 30000);
      })
      .catch(() => toast.error(t("Could not export CSV")));
  };

  return (
    <main className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
          </div>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-5 sm:px-8 pt-6">
        <div className="mb-6">
          <Link
            to="/admin"
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-red-700 font-bold"
            data-testid="admin-equip-back"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {t("Admin")}
          </Link>
        </div>

        <div className="font-mono text-xs uppercase tracking-[0.2em] text-red-700">
          {t("Field Leadership · Admin")}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-black mt-1">{t("Equipment Catalog & Manufacturers")}</h1>
        <p className="text-slate-600 mt-1 text-sm max-w-2xl">
          {t("Manage the searchable equipment list and manufacturer dropdown used by the Equipment Checkout & Accountability form. Disable old items instead of deleting to preserve historical record references.")}
        </p>

        {/* Catalog */}
        <Card className="mt-6 p-4">
          <div className="flex items-center justify-between gap-3 mb-3">
            <h2 className="font-display text-xl font-black flex items-center gap-2">
              {t("Equipment Catalog")}
              <span className="font-mono text-xs text-slate-500 font-normal">{catalog.length}</span>
            </h2>
            <div className="flex gap-2">
              <Button variant="outline" onClick={refresh} className="h-9" data-testid="admin-equip-refresh">
                <RefreshCw className="w-3.5 h-3.5 mr-1" />{t("Refresh")}
              </Button>
              <Button variant="outline" onClick={exportCsv} className="h-9" data-testid="admin-equip-export">
                <Download className="w-3.5 h-3.5 mr-1" />{t("Export Checkout CSV")}
              </Button>
              <Button onClick={openNew} className="bg-blue-700 hover:bg-blue-800 text-white h-9" data-testid="admin-equip-add">
                <Plus className="w-3.5 h-3.5 mr-1" />{t("Add Item")}
              </Button>
            </div>
          </div>

          <div className="relative mb-3">
            <Search className="absolute left-2 top-2.5 w-4 h-4 text-slate-400" />
            <Input
              placeholder={t("Search by name, make, or category…")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={`${inputCls} pl-8`}
              data-testid="admin-equip-search"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                <tr>
                  <th className="text-left px-3 py-2">{t("Name")}</th>
                  <th className="text-left px-3 py-2">{t("Default Make")}</th>
                  <th className="text-left px-3 py-2">{t("Category")}</th>
                  <th className="text-right px-3 py-2">{t("Replacement $")}</th>
                  <th className="text-center px-3 py-2">{t("Active")}</th>
                  <th className="text-right px-3 py-2">{t("Actions")}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr><td colSpan={6} className="px-3 py-6 text-center text-slate-500">{t("No items.")}</td></tr>
                ) : filtered.map((c) => (
                  <tr key={c.id} className="border-t border-slate-100" data-testid={`admin-equip-row-${c.id}`}>
                    <td className={`px-3 py-2 font-semibold ${c.active ? "text-slate-900" : "text-slate-400 line-through"}`}>{c.name}</td>
                    <td className="px-3 py-2 text-slate-700">{c.default_make || "—"}</td>
                    <td className="px-3 py-2 text-slate-700">{c.category || "—"}</td>
                    <td className="px-3 py-2 text-right font-mono tabular-nums">{fmtMoney(c.replacement_value)}</td>
                    <td className="px-3 py-2 text-center">
                      <button
                        onClick={() => toggleActive(c)}
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-bold uppercase ${c.active ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-500"}`}
                        data-testid={`admin-equip-toggle-${c.id}`}
                      >
                        <Power className="w-3 h-3" />{c.active ? t("Active") : t("Disabled")}
                      </button>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Button variant="outline" size="sm" onClick={() => openEdit(c)} className="h-8" data-testid={`admin-equip-edit-${c.id}`}>
                        <Pencil className="w-3.5 h-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Makes */}
        <Card className="mt-4 p-4">
          <div className="flex items-center justify-between gap-3 mb-3">
            <h2 className="font-display text-xl font-black flex items-center gap-2">
              {t("Manufacturers")}
              <span className="font-mono text-xs text-slate-500 font-normal">{makes.length}</span>
            </h2>
            <Button onClick={() => { setEditingMake({ name: "", active: true }); setShowMakeDialog(true); }} className="bg-blue-700 hover:bg-blue-800 text-white h-9" data-testid="admin-make-add">
              <Plus className="w-3.5 h-3.5 mr-1" />{t("Add Make")}
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {makes.map((m) => (
              <div key={m.id} className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md border-2 text-sm ${m.active ? "border-slate-300 bg-white" : "border-slate-200 bg-slate-50 text-slate-400"}`} data-testid={`admin-make-chip-${m.id}`}>
                <span className={m.active ? "" : "line-through"}>{m.name}</span>
                <button onClick={() => toggleMakeActive(m)} title={m.active ? t("Disable") : t("Enable")} data-testid={`admin-make-toggle-${m.id}`}>
                  <Power className={`w-3.5 h-3.5 ${m.active ? "text-emerald-700" : "text-slate-400"}`} />
                </button>
                <button onClick={() => { setEditingMake({ ...m }); setShowMakeDialog(true); }} title={t("Edit")} data-testid={`admin-make-edit-${m.id}`}>
                  <Pencil className="w-3.5 h-3.5 text-slate-500" />
                </button>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {/* Catalog edit dialog */}
      <Dialog open={showCatalogDialog} onOpenChange={setShowCatalogDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{editing?.id ? t("Edit Equipment") : t("Add Equipment")}</DialogTitle>
          </DialogHeader>
          {editing && (
            <div className="space-y-3">
              <div>
                <Label>{t("Name")}</Label>
                <Input value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} className={inputCls} data-testid="admin-equip-dlg-name" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>{t("Replacement $")}</Label>
                  <Input type="number" min="0" step="0.01" value={editing.replacement_value} onChange={(e) => setEditing({ ...editing, replacement_value: Number(e.target.value) || 0 })} className={inputCls} data-testid="admin-equip-dlg-rv" />
                </div>
                <div>
                  <Label>{t("Default Make")}</Label>
                  <Input value={editing.default_make || ""} onChange={(e) => setEditing({ ...editing, default_make: e.target.value })} className={inputCls} data-testid="admin-equip-dlg-make" />
                </div>
              </div>
              <div>
                <Label>{t("Category (optional)")}</Label>
                <Input value={editing.category || ""} onChange={(e) => setEditing({ ...editing, category: e.target.value })} className={inputCls} data-testid="admin-equip-dlg-cat" />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={!!editing.active} onChange={(e) => setEditing({ ...editing, active: e.target.checked })} data-testid="admin-equip-dlg-active" />
                {t("Active (visible in dropdown)")}
              </label>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCatalogDialog(false)}><X className="w-4 h-4 mr-1" />{t("Cancel")}</Button>
            <Button onClick={saveItem} className="bg-blue-700 hover:bg-blue-800 text-white" data-testid="admin-equip-dlg-save">
              <Save className="w-4 h-4 mr-1" />{t("Save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Make edit dialog */}
      <Dialog open={showMakeDialog} onOpenChange={setShowMakeDialog}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>{editingMake?.id ? t("Edit Manufacturer") : t("Add Manufacturer")}</DialogTitle>
          </DialogHeader>
          {editingMake && (
            <div className="space-y-3">
              <div>
                <Label>{t("Name")}</Label>
                <Input value={editingMake.name} onChange={(e) => setEditingMake({ ...editingMake, name: e.target.value })} className={inputCls} data-testid="admin-make-dlg-name" />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={!!editingMake.active} onChange={(e) => setEditingMake({ ...editingMake, active: e.target.checked })} data-testid="admin-make-dlg-active" />
                {t("Active")}
              </label>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMakeDialog(false)}>{t("Cancel")}</Button>
            <Button onClick={saveMake} className="bg-blue-700 hover:bg-blue-800 text-white" data-testid="admin-make-dlg-save">
              <Save className="w-4 h-4 mr-1" />{t("Save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main>
  );
}
