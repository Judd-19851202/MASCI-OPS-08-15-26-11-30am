// SafetyDocuments — Phase 3 safety document library.
// Upload via multipart form; list returns metadata only (no file_data);
// download streams the inline base64 back through /download. Categories
// are free-text tags (OSHA, SDS, EAP, training, sign-in sheets, etc.).
import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  FolderArchive, Upload, Loader2, Download, Trash2, X, Filter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import SafetyShell from "@/components/SafetyShell";
import { EmptyState, LoadingState } from "@/components/ui/PortalStates";
import { HelpTipBlock } from "@/components/HelpTip";
import { getSafetyToken } from "@/lib/safetyAuth";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: { "X-Safety-Token": getSafetyToken() } });

const CATEGORIES = [
  "OSHA 300", "SDS", "Emergency Action Plan", "Competent Person",
  "Fall Protection", "Training Certificate", "Sign-In Sheet",
  "Inspection Report", "Policy / Manual", "General",
];
const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700";

function bytes(n) {
  if (!n) return "0 B";
  const u = ["B", "KB", "MB", "GB"];
  let i = 0; let v = n;
  while (v > 1024 && i < u.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(1)} ${u[i]}`;
}

export default function SafetyDocuments() {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [uploadDlg, setUploadDlg] = useState(false);
  const [form, setForm] = useState({
    title: "", category: "General", description: "", tags: "", file: null,
  });
  const [uploading, setUploading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const params = category ? `?category=${encodeURIComponent(category)}` : "";
      const r = await axios.get(`${API}/safety/documents${params}`, auth());
      setItems(Array.isArray(r.data) ? r.data : []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load documents");
    } finally {
      setLoading(false);
    }
  }, [category]);
  useEffect(() => { refresh(); }, [refresh]);

  const filtered = useMemo(() => {
    if (!search.trim()) return items;
    const s = search.trim().toLowerCase();
    return items.filter((d) =>
      (d.title || "").toLowerCase().includes(s)
      || (d.filename || "").toLowerCase().includes(s)
      || (d.description || "").toLowerCase().includes(s)
      || (d.tags || []).join(",").toLowerCase().includes(s),
    );
  }, [items, search]);

  const upload = async () => {
    if (!form.file) { toast.error("Choose a file first"); return; }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", form.file);
      fd.append("title", form.title || form.file.name);
      fd.append("category", form.category);
      fd.append("description", form.description);
      fd.append("tags", form.tags);
      await axios.post(`${API}/safety/documents`, fd, {
        headers: { "X-Safety-Token": getSafetyToken(), "Content-Type": "multipart/form-data" },
      });
      toast.success("Document uploaded");
      setUploadDlg(false);
      setForm({ title: "", category: "General", description: "", tags: "", file: null });
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const downloadDoc = async (doc) => {
    try {
      const r = await axios.get(`${API}/safety/documents/${doc.id}/download`, {
        ...auth(),
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.filename || `${doc.id}.bin`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Download failed");
    }
  };

  const removeDoc = async (doc) => {
    if (!window.confirm(`Delete "${doc.title}"?`)) return;
    try {
      await axios.delete(`${API}/safety/documents/${doc.id}`, auth());
      toast.success("Deleted");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    }
  };

  return (
    <SafetyShell title="Safety Document Library" kicker="SAFETY · DOCUMENT LIBRARY">
      {/* iter290 · coaching family · top-of-page canonical 4 */}
      <HelpTipBlock formKey="safety-document" />
      {/* iter290 · classification sub-key — sits next to the category filter */}
      <HelpTipBlock formKey="safety-document.classification" />

      <div className="flex flex-col sm:flex-row gap-3 mb-5 items-start sm:items-center justify-between">
        <p className="text-slate-600 text-sm max-w-2xl leading-relaxed">
          {t("Centralized storage for OSHA records, SDS, emergency action plans, training certificates, sign-in sheets, and policies. Visible to Safety, HR, and Admin.")}
        </p>
        <Button onClick={() => setUploadDlg(true)} className="bg-cyan-700 hover:bg-cyan-800 text-white border-b-2 border-cyan-900 font-bold uppercase tracking-wide h-11 shrink-0" data-testid="safety-doc-upload-btn">
          <Upload className="w-4 h-4 mr-1" /> {t("Upload Document")}
        </Button>
      </div>

      <div className="flex flex-wrap gap-2 items-center mb-4">
        <Filter className="w-4 h-4 text-slate-500" />
        <Select value={category || "all"} onValueChange={(v) => setCategory(v === "all" ? "" : v)}>
          <SelectTrigger className={`${inputCls} max-w-xs`} data-testid="safety-doc-filter-cat"><SelectValue placeholder={t("All categories")} /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("All categories")}</SelectItem>
            {CATEGORIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
          </SelectContent>
        </Select>
        <Input placeholder={t("Search title, filename, tags…")} value={search} onChange={(e) => setSearch(e.target.value)} className={`${inputCls} max-w-md`} data-testid="safety-doc-search" />
      </div>

      {loading ? (
        <LoadingState label={t("Loading…")} testId="safety-doc-loading" />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={FolderArchive}
          title={t("No documents")}
          body={t("Upload one with the button above.")}
          testId="safety-doc-empty"
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4" data-testid="safety-doc-list">
          {filtered.map((doc) => (
            <div key={doc.id} className="bg-white border border-slate-200 rounded-md p-4" data-testid={`safety-doc-row-${doc.id}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <span className="inline-block px-2 py-0.5 rounded bg-cyan-100 text-cyan-800 text-[10px] font-mono uppercase tracking-[0.18em] font-bold mb-1">
                    {doc.category || "General"}
                  </span>
                  <h3 className="font-display text-lg font-black text-slate-900 truncate">{doc.title}</h3>
                  <div className="text-xs text-slate-500 mt-0.5 truncate">{doc.filename} · {bytes(doc.file_size)}</div>
                  {doc.description && <p className="text-sm text-slate-600 mt-1 line-clamp-2">{doc.description}</p>}
                  {doc.tags && doc.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {doc.tags.map((tg) => (
                        <span key={tg} className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-mono">{tg}</span>
                      ))}
                    </div>
                  )}
                  <div className="text-[11px] text-slate-400 mt-2 font-mono">
                    {doc.uploaded_at?.slice(0, 10)} · {doc.uploaded_by_name || "—"}
                  </div>
                </div>
                <div className="flex flex-col gap-1 shrink-0">
                  <Button size="sm" variant="outline" onClick={() => downloadDoc(doc)} className="h-9 border-cyan-300 text-cyan-800" data-testid={`safety-doc-download-${doc.id}`}>
                    <Download className="w-3.5 h-3.5" />
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => removeDoc(doc)} className="h-9 border-red-300 text-red-700" data-testid={`safety-doc-delete-${doc.id}`}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={uploadDlg} onOpenChange={(o) => !uploading && setUploadDlg(o)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("Upload safety document")}</DialogTitle>
            <DialogDescription>{t("Max 15 MB. Visible to Safety, HR, and Admin once uploaded.")}</DialogDescription>
          </DialogHeader>
          {/* iter290 · upload-discipline coaching inside the upload dialog */}
          <HelpTipBlock formKey="safety-document.upload" />
          <div className="space-y-3 pt-2">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("File")} *</Label>
              <Input type="file" onChange={(e) => setForm({ ...form, file: e.target.files?.[0] || null })} className={`${inputCls} mt-1`} data-testid="safety-doc-form-file" />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Title")}</Label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className={`${inputCls} mt-1`} placeholder={t("Defaults to filename")} data-testid="safety-doc-form-title" />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Category")}</Label>
              <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                <SelectTrigger className={`${inputCls} mt-1`} data-testid="safety-doc-form-cat"><SelectValue /></SelectTrigger>
                <SelectContent>{CATEGORIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Tags")}</Label>
              <Input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} className={`${inputCls} mt-1`} placeholder={t("Comma-separated — e.g. confined-space, 2026")} />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Description")}</Label>
              <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="text-sm border-2 border-slate-300 mt-1" />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setUploadDlg(false)} disabled={uploading}><X className="w-4 h-4 mr-1" /> {t("Cancel")}</Button>
            <Button onClick={upload} disabled={uploading || !form.file} className="bg-cyan-700 hover:bg-cyan-800 text-white" data-testid="safety-doc-form-save">
              {uploading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Upload className="w-4 h-4 mr-1" />} {t("Upload")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </SafetyShell>
  );
}
