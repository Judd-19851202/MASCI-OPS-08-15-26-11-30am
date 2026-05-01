import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Truck,
  Plus,
  Trash2,
  Pencil,
  Loader2,
  UploadCloud,
  RefreshCw,
  Search,
  CheckCircle2,
  X,
  Archive,
  RotateCcw,
  Download,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import { toast } from "sonner";

/**
 * EquipmentMasterPanel — manage the MASCI equipment fleet.
 *
 *  Header bar  : Refresh · Bulk Replace XLSX
 *  Stats line  : count + last upload + category chips
 *  + Add Unit  : opens a modal (~9 fields; too many for an inline row)
 *  Search/Cat  : filter the table
 *  Table       : Unit # · Year · Make · Model · Category · Type · Edit · Delete
 *
 *  Backend (require_shop_or_admin — admin / PM / shop can all edit):
 *    GET    /equipment-master                       (public list)
 *    GET    /admin/equipment-master/status          (count + categories)
 *    POST   /admin/equipment-master                 (single add)
 *    PUT    /admin/equipment-master/{id_or_unit}    (single edit)
 *    DELETE /admin/equipment-master/{id_or_unit}    (single delete)
 *    POST   /admin/equipment-master/upload          (bulk replace XLSX)
 */
const PREOP_TYPES = [
  "Excavator",
  "Loader",
  "Dozer",
  "Skid Steer",
  "Roller / Compactor",
  "Paver",
  "Milling Machine",
  "Dump Truck",
  "Pickup / Service Truck",
  "Trailer",
  "Generator / Compressor",
  "Light Plant",
  "Crane",
  "Forklift / Telehandler",
  "Other",
];

const blankUnit = {
  unit_number: "",
  year: "",
  make: "",
  model: "",
  vin_serial_number: "",
  category: "",
  preop_equipment_type: "Other",
  company: "MASCI",
  comments: "",
};

export default function EquipmentMasterPanel() {
  const [items, setItems] = useState([]);
  const [archive, setArchive] = useState([]);
  const [retainDays, setRetainDays] = useState(14);
  const [showArchive, setShowArchive] = useState(false);
  const [restoringId, setRestoringId] = useState(null);
  const [grouped, setGrouped] = useState({});
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [filter, setFilter] = useState("");
  const [cat, setCat] = useState("all");

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null); // unit object or null for "new"
  const [form, setForm] = useState(blankUnit);
  const [saving, setSaving] = useState(false);
  const [busyRow, setBusyRow] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const fileRef = useRef(null);

  const refresh = async () => {
    setLoading(true);
    try {
      const [listR, statusR, archR] = await Promise.all([
        api.get("/equipment-master"),
        api.get("/admin/equipment-master/status").catch(() => ({ data: null })),
        api.get("/admin/equipment-master/archive").catch(() => ({ data: { items: [], retain_days: 14 } })),
      ]);
      setItems(listR.data?.items || []);
      setGrouped(listR.data?.grouped || {});
      setStatus(statusR.data);
      setArchive(archR.data?.items || []);
      setRetainDays(archR.data?.retain_days || 14);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to load fleet");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    refresh();
  }, []);

  const cats = useMemo(() => Object.keys(grouped).sort(), [grouped]);
  const filtered = useMemo(() => {
    return items.filter((u) => {
      if (cat !== "all" && u.category !== cat) return false;
      if (!filter.trim()) return true;
      const q = filter.toLowerCase();
      return (
        (u.unit_number || "").toLowerCase().includes(q) ||
        (u.make || "").toLowerCase().includes(q) ||
        (u.model || "").toLowerCase().includes(q) ||
        (u.make_model || "").toLowerCase().includes(q) ||
        (u.vin_serial_number || "").toLowerCase().includes(q) ||
        (u.category || "").toLowerCase().includes(q)
      );
    });
  }, [items, filter, cat]);

  const openNew = () => {
    setEditing(null);
    setForm(blankUnit);
    setOpen(true);
  };
  const openEdit = (u) => {
    setEditing(u);
    setForm({
      unit_number: u.unit_number || "",
      year: u.year || "",
      make: u.make || "",
      model: u.model || "",
      vin_serial_number: u.vin_serial_number || "",
      category: u.category || "",
      preop_equipment_type: u.preop_equipment_type || "Other",
      company: u.company || "MASCI",
      comments: u.comments || "",
    });
    setOpen(true);
  };

  const submit = async (e) => {
    e?.preventDefault?.();
    if (!form.unit_number.trim()) {
      toast.error("Unit number is required");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        make_model:
          [form.make, form.model].filter(Boolean).join(" ").trim() || form.unit_number,
        display_label:
          [form.year, form.make, form.model].filter(Boolean).join(" ").trim() ||
          form.unit_number,
      };
      if (editing) {
        await api.put(
          `/admin/equipment-master/${encodeURIComponent(editing.id || editing.unit_number)}`,
          payload
        );
        toast.success(`Updated ${form.unit_number}`);
      } else {
        await api.post("/admin/equipment-master", payload);
        toast.success(`Added ${form.unit_number}`);
      }
      setOpen(false);
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const deleteUnit = async (u) => {
    if (
      !window.confirm(
        `Move unit ${u.unit_number} to the archive? You'll have ${retainDays} days to restore from the Archive tab before it's purged.`
      )
    )
      return;
    setBusyRow(u.id || u.unit_number);
    try {
      await api.delete(`/admin/equipment-master/${encodeURIComponent(u.id || u.unit_number)}`);
      toast.success("Moved to archive — click Archive to restore.");
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    } finally {
      setBusyRow(null);
    }
  };

  const restoreUnit = async (u) => {
    setRestoringId(u.id || u.unit_number);
    try {
      await api.post(`/admin/equipment-master/${encodeURIComponent(u.id || u.unit_number)}/restore`);
      toast.success(`Restored ${u.unit_number}`);
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Restore failed");
    } finally {
      setRestoringId(null);
    }
  };

  const onExport = async () => {
    setExporting(true);
    try {
      const r = await api.get("/admin/equipment-master/export", { responseType: "blob" });
      const cd = r.headers["content-disposition"] || r.headers["Content-Disposition"] || "";
      const m = /filename="?([^";]+)"?/i.exec(cd);
      const fname = m ? m[1] : "MASCI_equipment.xlsx";
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


  const onFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!/\.xlsx?$/i.test(file.name)) {
      toast.error("Please pick a .xlsx file");
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      toast.error("File too big — max 25 MB");
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await api.post("/admin/equipment-master/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const cats = Object.keys(r.data?.category_counts || {}).length;
      toast.success(`Fleet replaced — ${r.data.count} units across ${cats} categories.`);
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const total = status?.count ?? items.length;
  const lastUpdated = status?.last_updated
    ? new Date(status.last_updated)
    : null;

  return (
    <div
      className="mb-8 bg-white border-2 border-slate-200 rounded-md overflow-hidden shadow-sm"
      data-testid="equipment-master-panel"
    >
      {/* Header */}
      <div className="bg-slate-900 text-white px-5 py-3 flex items-center gap-3 flex-wrap">
        <Truck className="w-5 h-5 text-amber-400" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-400 font-bold flex-1">
          MASCI Equipment Master Fleet
        </span>
        <Button
          type="button"
          variant="outline"
          onClick={refresh}
          disabled={loading || saving || uploading || exporting}
          className="h-8 px-3 border-2 border-slate-600 bg-slate-800 text-white hover:bg-slate-700 font-mono uppercase tracking-wide text-[11px]"
          data-testid="equipment-master-refresh"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={onExport}
          disabled={exporting || loading}
          className="h-8 px-3 border-2 border-emerald-400 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 font-mono uppercase tracking-wide text-[11px]"
          data-testid="equipment-master-export-btn"
          title="Download the current fleet as XLSX"
        >
          {exporting ? (
            <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
          ) : (
            <Download className="w-3.5 h-3.5 mr-1" />
          )}
          Export
        </Button>
        <input
          ref={fileRef}
          type="file"
          accept=".xlsx,.xlsm"
          onChange={onFile}
          className="hidden"
          data-testid="equipment-master-bulk-input"
        />
        <Button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className="h-8 px-3 bg-amber-600 hover:bg-amber-700 text-white font-mono uppercase tracking-wide text-[11px]"
          data-testid="equipment-master-bulk-btn"
          title="Reads the 'Louis' sheet by default · max 25 MB"
        >
          {uploading ? (
            <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
          ) : (
            <UploadCloud className="w-3.5 h-3.5 mr-1" />
          )}
          Bulk Replace
        </Button>
      </div>

      {/* Stats + Add */}
      <div className="p-5 border-b-2 border-slate-100 flex items-center gap-3 flex-wrap">
        <span
          className="font-display text-4xl font-black text-slate-900"
          data-testid="equipment-master-total"
        >
          {total}
        </span>
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
          units in fleet
        </span>
        {lastUpdated && (
          <span className="text-xs text-slate-500 flex items-center gap-1.5">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            {lastUpdated.toLocaleString()}
          </span>
        )}
        <Button
          onClick={openNew}
          className="h-9 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs ml-auto"
          data-testid="equipment-master-add-btn"
        >
          <Plus className="w-4 h-4 mr-1" /> Add Unit
        </Button>
      </div>

      {/* Search + filter */}
      <div className="p-5">
        {/* Active / Archive tabs */}
        <div className="mb-3 flex items-center gap-2 flex-wrap" data-testid="equipment-tabs">
          <Button
            type="button"
            size="sm"
            onClick={() => setShowArchive(false)}
            className={`h-8 px-3 text-[11px] font-mono uppercase tracking-wide font-bold ${
              !showArchive
                ? "bg-slate-900 text-white"
                : "bg-white border-2 border-slate-300 text-slate-700 hover:border-amber-600"
            }`}
            data-testid="equipment-tab-active"
          >
            Active ({items.length})
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={() => setShowArchive(true)}
            className={`h-8 px-3 text-[11px] font-mono uppercase tracking-wide font-bold ${
              showArchive
                ? "bg-slate-700 text-white"
                : "bg-white border-2 border-slate-300 text-slate-700 hover:border-amber-600"
            }`}
            data-testid="equipment-tab-archive"
          >
            <Archive className="w-3.5 h-3.5 mr-1" /> Archive ({archive.length})
          </Button>
          {showArchive && (
            <span className="text-xs text-slate-500 ml-2">
              Soft-deleted units · auto-purged after {retainDays} days. Click <RotateCcw className="w-3 h-3 inline" /> to restore.
            </span>
          )}
        </div>

        {!showArchive && (
          <div className="flex items-center gap-2 flex-wrap mb-3">
          <Search className="w-4 h-4 text-slate-400" />
          <Input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Search unit, make, model, VIN…"
            className="h-9 border-2 max-w-md"
            data-testid="equipment-master-search"
          />
          <Select value={cat} onValueChange={setCat}>
            <SelectTrigger className="w-56 h-9 border-2" data-testid="equipment-master-cat">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              {cats.map((c) => (
                <SelectItem key={c} value={c}>
                  {c} ({grouped[c]?.length || 0})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-xs text-slate-500 font-mono">
            {filtered.length} / {items.length}
          </span>
          </div>
        )}

        {loading ? (
          <div className="py-10 text-center text-slate-500">
            <Loader2 className="w-5 h-5 inline-block animate-spin mr-2" /> Loading…
          </div>
        ) : showArchive ? (
          archive.length === 0 ? (
            <p className="text-sm text-slate-500 py-8 text-center italic">
              Archive is empty — nothing to restore.
            </p>
          ) : (
            <div className="overflow-x-auto border-2 border-slate-200 rounded max-h-[480px]">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-50 z-[1]">
                  <tr>
                    <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Unit #</th>
                    <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Year</th>
                    <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Make / Model</th>
                    <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Category</th>
                    <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Deleted</th>
                    <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold w-24">Restore</th>
                  </tr>
                </thead>
                <tbody>
                  {archive.map((u) => {
                    const id = u.id || u.unit_number;
                    return (
                      <tr key={id} className="border-t border-slate-100 bg-slate-50/40" data-testid={`equipment-archive-row-${id}`}>
                        <td className="px-3 py-2 font-bold font-mono text-slate-900">{u.unit_number || "—"}</td>
                        <td className="px-3 py-2 text-slate-700">{u.year || "—"}</td>
                        <td className="px-3 py-2 text-slate-800">{[u.make, u.model].filter(Boolean).join(" ") || u.make_model || "—"}</td>
                        <td className="px-3 py-2 text-slate-500 text-xs">{u.category || "—"}</td>
                        <td className="px-3 py-2 text-xs text-slate-500 whitespace-nowrap">
                          {u.deleted_at ? new Date(u.deleted_at).toLocaleString() : "—"}
                        </td>
                        <td className="px-3 py-2 text-right whitespace-nowrap">
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => restoreUnit(u)}
                            disabled={restoringId === id}
                            className="h-8 w-8 border-2 border-emerald-400 text-emerald-700 hover:bg-emerald-50"
                            data-testid={`equipment-restore-${id}`}
                            title="Restore to active fleet"
                          >
                            {restoringId === id ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <RotateCcw className="w-3.5 h-3.5" />
                            )}
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500 py-8 text-center italic">
            Fleet is empty — click <strong>Add Unit</strong> or <strong>Bulk Replace</strong>.
          </p>
        ) : (
          <div className="overflow-x-auto border-2 border-slate-200 rounded max-h-[480px]">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-slate-50 z-[1]">
                <tr>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Unit #</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Year</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Make</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Model</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Category</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">Pre-Op Type</th>
                  <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold w-24">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u) => {
                  const id = u.id || u.unit_number;
                  return (
                    <tr key={id} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`equipment-row-${id}`}>
                      <td className="px-3 py-2 font-bold font-mono text-slate-900">{u.unit_number || "—"}</td>
                      <td className="px-3 py-2 text-slate-700">{u.year || "—"}</td>
                      <td className="px-3 py-2 text-slate-800">{u.make || "—"}</td>
                      <td className="px-3 py-2 text-slate-700">{u.model || "—"}</td>
                      <td className="px-3 py-2 text-slate-500 text-xs">{u.category || "—"}</td>
                      <td className="px-3 py-2 text-slate-500 text-xs">{u.preop_equipment_type || "—"}</td>
                      <td className="px-3 py-2 text-right whitespace-nowrap">
                        <Button
                          size="icon"
                          variant="outline"
                          onClick={() => openEdit(u)}
                          className="h-8 w-8 mr-1 border-2 border-slate-300 hover:border-amber-600 hover:text-amber-700"
                          data-testid={`equipment-edit-${id}`}
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          size="icon"
                          variant="outline"
                          onClick={() => deleteUnit(u)}
                          disabled={busyRow === id}
                          className="h-8 w-8 border-2 border-slate-300 hover:border-red-500 hover:text-red-600"
                          data-testid={`equipment-delete-${id}`}
                        >
                          {busyRow === id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="w-3.5 h-3.5" />
                          )}
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add / Edit modal */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="font-display font-black text-xl">
              {editing ? `Edit Unit · ${editing.unit_number}` : "Add a Unit to the Fleet"}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={submit} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em]">Unit Number *</Label>
              <Input
                value={form.unit_number}
                onChange={(e) => setForm({ ...form, unit_number: e.target.value })}
                className="h-10 mt-1 border-2"
                placeholder="EX-101"
                data-testid="eq-form-unit"
                required
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em]">Year</Label>
              <Input
                value={form.year}
                onChange={(e) => setForm({ ...form, year: e.target.value })}
                className="h-10 mt-1 border-2"
                placeholder="2022"
                data-testid="eq-form-year"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em]">Make</Label>
              <Input
                value={form.make}
                onChange={(e) => setForm({ ...form, make: e.target.value })}
                className="h-10 mt-1 border-2"
                placeholder="CAT"
                data-testid="eq-form-make"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em]">Model</Label>
              <Input
                value={form.model}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
                className="h-10 mt-1 border-2"
                placeholder="320GC"
                data-testid="eq-form-model"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em]">Category</Label>
              <Input
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                list="eq-cat-list"
                className="h-10 mt-1 border-2"
                placeholder="Excavators"
                data-testid="eq-form-cat"
              />
              <datalist id="eq-cat-list">
                {cats.map((c) => (
                  <option key={c} value={c} />
                ))}
              </datalist>
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em]">Pre-Op Type</Label>
              <Select
                value={form.preop_equipment_type}
                onValueChange={(v) => setForm({ ...form, preop_equipment_type: v })}
              >
                <SelectTrigger className="h-10 mt-1 border-2" data-testid="eq-form-preop">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PREOP_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em]">VIN / Serial #</Label>
              <Input
                value={form.vin_serial_number}
                onChange={(e) => setForm({ ...form, vin_serial_number: e.target.value })}
                className="h-10 mt-1 border-2"
                placeholder=""
                data-testid="eq-form-vin"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em]">Company</Label>
              <Input
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                className="h-10 mt-1 border-2"
                data-testid="eq-form-company"
              />
            </div>
            <div className="sm:col-span-2">
              <Label className="font-mono text-[10px] uppercase tracking-[0.2em]">Comments / Notes</Label>
              <Textarea
                value={form.comments}
                onChange={(e) => setForm({ ...form, comments: e.target.value })}
                className="mt-1 border-2"
                rows={2}
                data-testid="eq-form-comments"
              />
            </div>
            <DialogFooter className="sm:col-span-2 mt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                className="h-10 border-2"
              >
                <X className="w-4 h-4 mr-1" /> Cancel
              </Button>
              <Button
                type="submit"
                disabled={saving}
                className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs"
                data-testid="eq-form-save"
              >
                {saving ? (
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4 mr-1" />
                )}
                {editing ? "Save Changes" : "Add Unit"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
