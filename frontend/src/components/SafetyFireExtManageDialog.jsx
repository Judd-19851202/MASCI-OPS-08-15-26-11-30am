// SafetyFireExtManageDialog — Iter135. Per-unit "manage" dialog showing
// attachments + history-PDF download. Keeps SafetyFireExtinguishers.jsx
// focused on the list/CRUD while this owns the attachment workflow.
import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import {
  Paperclip, Upload, Trash2, Loader2, FileDown, Image as ImageIcon,
  FileText, Download, X,
} from "lucide-react";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { getSafetyToken } from "@/lib/safetyAuth";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: { "X-Safety-Token": getSafetyToken() } });

const KIND_OPTIONS = [
  { value: "paperwork", label: "Paperwork" },
  { value: "photo",     label: "Photo" },
  { value: "other",     label: "Other" },
];

function fmtBytes(n) {
  if (!n) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export default function SafetyFireExtManageDialog({ open, fe, onClose, onChanged }) {
  const fileRef = useRef(null);
  const [file, setFile] = useState(null);
  const [kind, setKind] = useState("paperwork");
  const [uploading, setUploading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [unit, setUnit] = useState(fe);

  useEffect(() => { setUnit(fe); }, [fe]);

  if (!unit) return null;

  const attachments = unit.attachments || [];

  const refresh = async () => {
    try {
      const r = await axios.get(`${API}/safety/fire-extinguishers`, auth());
      const updated = (r.data || []).find((x) => x.id === unit.id);
      if (updated) {
        setUnit(updated);
        onChanged && onChanged(updated);
      }
    } catch (e) { /* swallow */ }
  };

  const doUpload = async () => {
    if (!file) { toast.error("Choose a file first"); return; }
    if (file.size > 10 * 1024 * 1024) { toast.error("File too large — 10 MB cap"); return; }
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("kind", kind);
      await axios.post(
        `${API}/safety/fire-extinguishers/${unit.id}/attachments`,
        form,
        { headers: { ...auth().headers, "Content-Type": "multipart/form-data" } },
      );
      toast.success("Attachment uploaded");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const doDelete = async (attId) => {
    if (!window.confirm("Delete this attachment? Cannot be undone.")) return;
    try {
      await axios.delete(`${API}/safety/fire-extinguishers/${unit.id}/attachments/${attId}`, auth());
      toast.success("Deleted");
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    }
  };

  const doDownloadAtt = async (att) => {
    try {
      const r = await axios.get(
        `${API}/safety/fire-extinguishers/${unit.id}/attachments/${att.id}`,
        { ...auth(), responseType: "blob" },
      );
      const url = URL.createObjectURL(new Blob([r.data], { type: att.content_type || "application/octet-stream" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = att.filename || "attachment";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error("Download failed");
    }
  };

  const doHistoryPdf = async () => {
    setDownloading(true);
    try {
      const r = await axios.get(
        `${API}/safety/fire-extinguishers/${unit.id}/history.pdf`,
        { ...auth(), responseType: "blob" },
      );
      const url = URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      const safeId = (unit.unit_id || unit.id || "fe").replace(/[^a-z0-9]/gi, "_");
      a.download = `fe_${safeId}_history.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error("PDF download failed");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[92vh] overflow-y-auto" data-testid="safety-fe-manage-dialog">
        <DialogHeader>
          <DialogTitle>Manage · {unit.unit_id}</DialogTitle>
          <DialogDescription>
            Attach inspection paperwork, photos, and download the printable unit history.
          </DialogDescription>
        </DialogHeader>

        {/* History PDF */}
        <div className="bg-slate-50 border-2 border-slate-200 rounded-md p-3 sm:p-4 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              Printable Unit History
            </div>
            <div className="text-sm text-slate-700 mt-0.5">
              Register info + inspection log + attachment list as a single PDF.
            </div>
          </div>
          <Button
            onClick={doHistoryPdf}
            disabled={downloading}
            className="bg-slate-900 hover:bg-cyan-700 text-white border-b-2 border-black font-bold uppercase tracking-wide h-10 shrink-0"
            data-testid="safety-fe-history-pdf"
          >
            {downloading
              ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Building…</>
              : <><FileDown className="w-4 h-4 mr-2" /> Download PDF</>}
          </Button>
        </div>

        {/* Upload */}
        <div className="bg-white border-2 border-slate-300 rounded-md p-3 sm:p-4 mt-4">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 mb-2">
            Upload Attachment
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-2 sm:items-center">
            <input
              ref={fileRef}
              type="file"
              accept="image/*,.pdf,.heic,.heif"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block text-sm sm:col-span-6 file:mr-2 file:py-1.5 file:px-3 file:rounded file:border-2 file:border-slate-300 file:bg-slate-50 file:text-slate-800 file:font-bold file:uppercase file:text-xs hover:file:bg-slate-100"
              data-testid="safety-fe-att-file"
            />
            <div className="sm:col-span-3">
              <Select value={kind} onValueChange={setKind}>
                <SelectTrigger className="h-9 text-sm border-2 border-slate-300" data-testid="safety-fe-att-kind">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {KIND_OPTIONS.map((k) => (
                    <SelectItem key={k.value} value={k.value}>{k.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              onClick={doUpload}
              disabled={!file || uploading}
              className="sm:col-span-3 bg-cyan-700 hover:bg-cyan-800 text-white border-b-2 border-cyan-900 font-bold uppercase tracking-wide h-9"
              data-testid="safety-fe-att-upload"
            >
              {uploading
                ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Uploading…</>
                : <><Upload className="w-4 h-4 mr-2" /> Add</>}
            </Button>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Max 10 MB. Images + PDFs only. Stored to Cloudflare R2 when configured; falls back to inline storage if R2 is degraded.
          </p>
        </div>

        {/* Attachment list */}
        <div className="mt-4">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 mb-2 flex items-center gap-2">
            <Paperclip className="w-3.5 h-3.5" /> Attachments ({attachments.length})
          </div>
          {attachments.length === 0 ? (
            <div className="text-sm text-slate-500 italic border-2 border-dashed border-slate-200 rounded p-4 text-center">
              No attachments on file.
            </div>
          ) : (
            <ul className="border-2 border-slate-200 rounded divide-y divide-slate-100" data-testid="safety-fe-att-list">
              {attachments.map((a) => {
                const Icon = (a.content_type || "").startsWith("image/") ? ImageIcon : FileText;
                return (
                  <li key={a.id} className="p-2.5 flex items-center gap-3 hover:bg-slate-50">
                    <Icon className="w-5 h-5 text-slate-500 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-xs text-slate-900 truncate">{a.filename}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        <span className="inline-block px-1.5 py-0 rounded bg-slate-100 text-[9px] uppercase tracking-wider mr-1">{a.kind}</span>
                        {fmtBytes(a.file_size)} · {String(a.uploaded_at || "").slice(0, 10)}
                        {a.storage_backend === "inline" && (
                          <span className="ml-2 text-amber-700 font-bold">· inline (R2 unavailable at upload time)</span>
                        )}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => doDownloadAtt(a)}
                      className="h-8"
                      data-testid={`safety-fe-att-download-${a.id}`}
                      title="Download"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => doDelete(a.id)}
                      className="h-8 border-red-300 text-red-700"
                      data-testid={`safety-fe-att-delete-${a.id}`}
                      title="Delete"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <DialogFooter className="pt-4">
          <Button variant="outline" onClick={onClose} data-testid="safety-fe-manage-close">
            <X className="w-4 h-4 mr-1" /> Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
