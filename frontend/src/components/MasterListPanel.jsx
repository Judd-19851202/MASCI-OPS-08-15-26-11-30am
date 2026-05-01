import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Loader2,
  Plus,
  Trash2,
  Pencil,
  Save,
  X,
  Search,
  UploadCloud,
  Download,
  RefreshCw,
  CheckCircle2,
  Archive,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { toast } from "sonner";

/**
 * MasterListPanel — generic single-add + table + edit + delete + bulk-replace
 * panel. Mirrors the AdminJobMasterPanel UX. Plug it in with a small config:
 *
 *   <MasterListPanel
 *     title="MASCI Employee Roster"
 *     icon={Users}
 *     accent="amber"
 *     listEndpoint="/employees"          // GET → {items: [...], count}
 *     statusEndpoint="/admin/employees/status"
 *     createEndpoint="/admin/employees"  // POST single
 *     updateEndpoint="/admin/employees/{id}"  // PUT single (use {id})
 *     deleteEndpoint="/admin/employees/{id}"
 *     uploadEndpoint="/admin/employees/upload"
 *     uploadAccept=".xlsx,.csv"
 *     fields={[{key: 'name', label: 'Name', required: true}, ...]}
 *     itemKey="id"
 *     itemLabel={(r) => r.name}
 *     emptyState="No employees yet — add one or upload an .xlsx."
 *     entitySingular="employee"
 *     onChange={() => clearEmployeeCache()}  // optional
 *   />
 */
export default function MasterListPanel({
  title,
  icon: Icon,
  accent = "amber", // "amber" | "red" | "slate"
  testIdPrefix,
  listEndpoint,
  statusEndpoint,
  createEndpoint,
  updateEndpoint,
  deleteEndpoint,
  uploadEndpoint,
  exportEndpoint,         // optional GET — XLSX download
  archiveEndpoint,        // optional GET — soft-deleted rows
  restoreEndpoint,        // optional POST — restore (uses {id} placeholder)
  uploadAccept = ".xlsx,.csv",
  uploadHint = "XLSX or CSV · max 25 MB",
  fields,
  itemKey = "id",
  itemLabel = (r) => r.name,
  emptyState = "No entries yet.",
  entitySingular = "entry",
  onChange,
  search = true,
}) {
  const [items, setItems] = useState([]);
  const [archive, setArchive] = useState([]);
  const [retainDays, setRetainDays] = useState(14);
  const [showArchive, setShowArchive] = useState(false);
  const [restoringId, setRestoringId] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [savingRow, setSavingRow] = useState(null);
  const [filter, setFilter] = useState("");
  const blank = useMemo(
    () => Object.fromEntries(fields.map((f) => [f.key, ""])),
    [fields]
  );
  const [form, setForm] = useState(blank);
  const fileRef = useRef(null);

  const accentBg = accent === "red" ? "bg-red-700 hover:bg-red-800"
                 : accent === "slate" ? "bg-slate-900 hover:bg-slate-800"
                 : "bg-amber-600 hover:bg-amber-700";
  const accentTitleBar = "bg-slate-900";
  const accentChip = accent === "red" ? "text-red-300"
                   : accent === "slate" ? "text-amber-300"
                   : "text-amber-300";

  const refresh = async () => {
    setLoading(true);
    try {
      const [listR, statusR, archiveR] = await Promise.all([
        api.get(listEndpoint),
        statusEndpoint ? api.get(statusEndpoint) : Promise.resolve({ data: null }),
        archiveEndpoint ? api.get(archiveEndpoint) : Promise.resolve({ data: { items: [], retain_days: 14 } }),
      ]);
      const arr = listR.data?.items || listR.data || [];
      setItems(Array.isArray(arr) ? arr : []);
      setStatus(statusR.data);
      setArchive(archiveR.data?.items || []);
      setRetainDays(archiveR.data?.retain_days || 14);
    } catch (e) {
      toast.error(e?.response?.data?.detail || `Failed to load ${entitySingular} list`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listEndpoint]);

  const requiredOk = (obj) =>
    fields.filter((f) => f.required).every((f) => (obj[f.key] || "").trim());

  const addOne = async (e) => {
    e?.preventDefault?.();
    if (!requiredOk(form)) {
      toast.error(
        `Required: ${fields.filter((f) => f.required).map((f) => f.label).join(", ")}`
      );
      return;
    }
    setAdding(true);
    try {
      await api.post(createEndpoint, form);
      toast.success(`Added ${form[fields[0].key] || entitySingular}`);
      setForm(blank);
      onChange?.();
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed");
    } finally {
      setAdding(false);
    }
  };

  const startEdit = (row) => {
    setEditingId(row[itemKey]);
    setEditForm(
      Object.fromEntries(fields.map((f) => [f.key, row[f.key] ?? ""]))
    );
  };
  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };
  const saveEdit = async (row) => {
    if (!requiredOk(editForm)) {
      toast.error("Required field missing");
      return;
    }
    setSavingRow(row[itemKey]);
    try {
      const url = updateEndpoint.replace("{id}", row[itemKey]);
      await api.put(url, editForm);
      toast.success("Updated");
      setEditingId(null);
      onChange?.();
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Update failed");
    } finally {
      setSavingRow(null);
    }
  };

  const deleteRow = async (row) => {
    if (!window.confirm(`Delete ${itemLabel(row)}? This cannot be undone.`)) return;
    setSavingRow(row[itemKey]);
    try {
      const url = deleteEndpoint.replace("{id}", row[itemKey]);
      await api.delete(url);
      toast.success("Deleted");
      onChange?.();
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    } finally {
      setSavingRow(null);
    }
  };

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 25 * 1024 * 1024) {
      toast.error("File too big — max 25 MB");
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await api.post(uploadEndpoint, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success(`Bulk replace OK — ${r.data?.count ?? "?"} rows.`);
      onChange?.();
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const onExport = async () => {
    if (!exportEndpoint) return;
    setExporting(true);
    try {
      const r = await api.get(exportEndpoint, { responseType: "blob" });
      // Pull filename out of Content-Disposition
      const cd = r.headers["content-disposition"] || r.headers["Content-Disposition"] || "";
      const m = /filename="?([^";]+)"?/i.exec(cd);
      const fname = m ? m[1] : `MASCI_${entitySingular}s.xlsx`;
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

  const filtered = useMemo(() => {
    if (!filter.trim()) return items;
    const q = filter.toLowerCase();
    return items.filter((r) =>
      fields.some((f) => String(r[f.key] || "").toLowerCase().includes(q))
    );
  }, [items, filter, fields]);

  const total = status?.count ?? items.length;
  const lastUpdated = status?.last_updated
    ? new Date(status.last_updated)
    : null;

  return (
    <div
      className="mb-8 bg-white border-2 border-slate-200 rounded-md overflow-hidden shadow-sm"
      data-testid={`${testIdPrefix}-panel`}
    >
      {/* Header bar */}
      <div className={`${accentTitleBar} text-white px-5 py-3 flex items-center gap-3 flex-wrap`}>
        {Icon && <Icon className={`w-5 h-5 ${accentChip}`} />}
        <span className={`font-mono text-xs uppercase tracking-[0.2em] ${accentChip} font-bold flex-1`}>
          {title}
        </span>
        <Button
          type="button"
          variant="outline"
          onClick={refresh}
          disabled={loading || adding || uploading || exporting}
          className="h-8 px-3 border-2 border-slate-600 bg-slate-800 text-white hover:bg-slate-700 font-mono uppercase tracking-wide text-[11px]"
          data-testid={`${testIdPrefix}-refresh`}
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
        </Button>
        {exportEndpoint && (
          <Button
            type="button"
            variant="outline"
            onClick={onExport}
            disabled={exporting || loading}
            className="h-8 px-3 border-2 border-emerald-400 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 font-mono uppercase tracking-wide text-[11px]"
            data-testid={`${testIdPrefix}-export-btn`}
            title="Download the current active list as XLSX"
          >
            {exporting ? (
              <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5 mr-1" />
            )}
            Export
          </Button>
        )}
        <input
          ref={fileRef}
          type="file"
          accept={uploadAccept}
          onChange={onFile}
          className="hidden"
          data-testid={`${testIdPrefix}-bulk-input`}
        />
        <Button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className={`h-8 px-3 ${accentBg} text-white font-mono uppercase tracking-wide text-[11px]`}
          data-testid={`${testIdPrefix}-bulk-btn`}
          title={uploadHint}
        >
          {uploading ? (
            <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
          ) : (
            <UploadCloud className="w-3.5 h-3.5 mr-1" />
          )}
          Bulk Replace
        </Button>
      </div>

      {/* Stats + add-one form */}
      <div className="p-5 border-b-2 border-slate-100">
        <div className="flex items-baseline gap-3 flex-wrap">
          <span
            className="font-display text-4xl font-black text-slate-900"
            data-testid={`${testIdPrefix}-total`}
          >
            {total}
          </span>
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
            {entitySingular}{total === 1 ? "" : "s"} on file
          </span>
          {lastUpdated && (
            <span className="text-xs text-slate-500 flex items-center gap-1.5 ml-auto">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              Last bulk update {lastUpdated.toLocaleString()}
            </span>
          )}
        </div>

        <form onSubmit={addOne} className="mt-4">
          <div
            className="grid gap-3"
            style={{
              gridTemplateColumns: `repeat(${Math.min(fields.length + 1, 5)}, minmax(0,1fr))`,
            }}
          >
            {fields.map((f) => (
              <div key={f.key} className={f.span ? `col-span-${f.span}` : ""}>
                <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                  {f.label}
                  {f.required ? " *" : ""}
                </label>
                <Input
                  value={form[f.key] || ""}
                  onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                  placeholder={f.placeholder || ""}
                  className="h-9 mt-1 border-2 text-sm"
                  data-testid={`${testIdPrefix}-add-${f.key}`}
                />
              </div>
            ))}
            <div className="flex items-end">
              <Button
                type="submit"
                disabled={adding}
                className={`w-full h-9 ${accentBg} text-white font-bold uppercase tracking-wide text-xs`}
                data-testid={`${testIdPrefix}-add-btn`}
              >
                {adding ? (
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4 mr-1" />
                )}
                Add
              </Button>
            </div>
          </div>
        </form>
      </div>

      {/* Search + table */}
      <div className="p-5">
        {/* Active / Archive toggle */}
        {archiveEndpoint && (
          <div className="mb-3 flex items-center gap-2 flex-wrap" data-testid={`${testIdPrefix}-tabs`}>
            <Button
              type="button"
              size="sm"
              onClick={() => setShowArchive(false)}
              className={`h-8 px-3 text-[11px] font-mono uppercase tracking-wide font-bold ${
                !showArchive
                  ? "bg-slate-900 text-white"
                  : "bg-white border-2 border-slate-300 text-slate-700 hover:border-amber-600"
              }`}
              data-testid={`${testIdPrefix}-tab-active`}
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
              data-testid={`${testIdPrefix}-tab-archive`}
            >
              <Archive className="w-3.5 h-3.5 mr-1" /> Archive ({archive.length})
            </Button>
            {showArchive && (
              <span className="text-xs text-slate-500 ml-2">
                Soft-deleted rows · auto-purged after {retainDays} days. Click <RotateCcw className="w-3 h-3 inline" /> to restore.
              </span>
            )}
          </div>
        )}

        {!showArchive && search && (
          <div className="flex items-center gap-2 mb-3">
            <Search className="w-4 h-4 text-slate-400" />
            <Input
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Search…"
              className="h-9 border-2 max-w-md"
              data-testid={`${testIdPrefix}-search`}
            />
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
            <div className="overflow-x-auto border-2 border-slate-200 rounded max-h-[460px]">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-50 z-[1]">
                  <tr>
                    {fields.map((f) => (
                      <th
                        key={f.key}
                        className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold whitespace-nowrap"
                      >
                        {f.label}
                      </th>
                    ))}
                    <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold whitespace-nowrap">
                      Deleted
                    </th>
                    <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold w-24">
                      Restore
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {archive.map((row) => (
                    <tr key={row[itemKey]} className="border-t border-slate-100 bg-slate-50/40" data-testid={`${testIdPrefix}-archive-row-${row[itemKey]}`}>
                      {fields.map((f) => (
                        <td key={f.key} className="px-3 py-2 align-top text-slate-700">
                          {row[f.key] || <span className="text-slate-400">—</span>}
                        </td>
                      ))}
                      <td className="px-3 py-2 text-xs text-slate-500 whitespace-nowrap">
                        {row.deleted_at ? new Date(row.deleted_at).toLocaleString() : "—"}
                      </td>
                      <td className="px-3 py-2 text-right whitespace-nowrap">
                        <Button
                          size="icon"
                          variant="outline"
                          onClick={() => restoreRow(row)}
                          disabled={restoringId === row[itemKey]}
                          className="h-8 w-8 border-2 border-emerald-400 text-emerald-700 hover:bg-emerald-50"
                          data-testid={`${testIdPrefix}-restore-${row[itemKey]}`}
                          title="Restore to active list"
                        >
                          {restoringId === row[itemKey] ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <RotateCcw className="w-3.5 h-3.5" />
                          )}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500 py-8 text-center italic">
            {emptyState}
          </p>
        ) : (
          <div className="overflow-x-auto border-2 border-slate-200 rounded max-h-[460px]">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-slate-50 z-[1]">
                <tr>
                  {fields.map((f) => (
                    <th
                      key={f.key}
                      className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold whitespace-nowrap"
                    >
                      {f.label}
                    </th>
                  ))}
                  <th className="text-right px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold w-32">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => {
                  const isEditing = editingId === row[itemKey];
                  const busy = savingRow === row[itemKey];
                  return (
                    <tr
                      key={row[itemKey]}
                      className="border-t border-slate-100 hover:bg-slate-50"
                      data-testid={`${testIdPrefix}-row-${row[itemKey]}`}
                    >
                      {fields.map((f) => (
                        <td key={f.key} className="px-3 py-2 align-top">
                          {isEditing ? (
                            <Input
                              value={editForm[f.key] || ""}
                              onChange={(e) =>
                                setEditForm({ ...editForm, [f.key]: e.target.value })
                              }
                              className="h-8 border-2 text-sm"
                              data-testid={`${testIdPrefix}-edit-${f.key}-${row[itemKey]}`}
                            />
                          ) : (
                            <span className="text-slate-800">
                              {row[f.key] || <span className="text-slate-400">—</span>}
                            </span>
                          )}
                        </td>
                      ))}
                      <td className="px-3 py-2 text-right whitespace-nowrap">
                        {isEditing ? (
                          <>
                            <Button
                              size="icon"
                              variant="outline"
                              onClick={() => saveEdit(row)}
                              disabled={busy}
                              className="h-8 w-8 mr-1 border-2 border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                              data-testid={`${testIdPrefix}-save-${row[itemKey]}`}
                            >
                              {busy ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <Save className="w-3.5 h-3.5" />
                              )}
                            </Button>
                            <Button
                              size="icon"
                              variant="outline"
                              onClick={cancelEdit}
                              className="h-8 w-8 border-2 border-slate-300"
                              data-testid={`${testIdPrefix}-cancel-${row[itemKey]}`}
                            >
                              <X className="w-3.5 h-3.5" />
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button
                              size="icon"
                              variant="outline"
                              onClick={() => startEdit(row)}
                              className="h-8 w-8 mr-1 border-2 border-slate-300 hover:border-amber-600 hover:text-amber-700"
                              data-testid={`${testIdPrefix}-edit-${row[itemKey]}`}
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              size="icon"
                              variant="outline"
                              onClick={() => deleteRow(row)}
                              disabled={busy}
                              className="h-8 w-8 border-2 border-slate-300 hover:border-red-500 hover:text-red-600"
                              data-testid={`${testIdPrefix}-delete-${row[itemKey]}`}
                            >
                              {busy ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <Trash2 className="w-3.5 h-3.5" />
                              )}
                            </Button>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
