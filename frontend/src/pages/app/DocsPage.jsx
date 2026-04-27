import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Plus, Loader2, Trash2, FileText, Download, Upload, Folder } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { UserAvatar, relativeTime, apiErr } from "@/lib/crewHubUi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function DocsPage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const [cats, setCats] = useState([]);
  const [docs, setDocs] = useState(null);
  const [active, setActive] = useState("All");
  const [open, setOpen] = useState(false);

  const load = async () => {
    try {
      const [c, d] = await Promise.all([
        api.get("/doc-categories"),
        api.get(`/projects/${projectId}/docs`),
      ]);
      setCats(c.data.categories);
      setDocs(d.data);
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Failed to load docs"));
    }
  };
  useEffect(() => { load(); }, [projectId]);

  const counts = {};
  cats.forEach((c) => { counts[c] = 0; });
  (docs || []).forEach((d) => { counts[d.category] = (counts[d.category] || 0) + 1; });

  const filtered = active === "All" ? docs : (docs || []).filter((d) => d.category === active);

  const onDelete = async (doc) => {
    if (!window.confirm(`Delete "${doc.filename}"?`)) return;
    try {
      await api.delete(`/docs/${doc.id}`);
      toast.success("Deleted"); load();
    } catch (e) {
      toast.error(apiErr(e?.response?.data?.detail, "Delete failed"));
    }
  };

  return (
    <div className="p-8 sm:p-10 max-w-5xl" data-testid="docs-page">
      <Link to={`/app/projects/${projectId}`} className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-500 hover:text-red-700 font-bold mb-6">
        <ArrowLeft className="w-3 h-3" /> Back to project
      </Link>

      <div className="flex items-start justify-between gap-4 flex-wrap mb-6">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-700 font-bold">Docs & Files</div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">Project documents</h1>
          <p className="text-slate-600 text-sm mt-1">Organized by MASCI categories. Max 30 MB per file.</p>
        </div>
        <Button onClick={() => setOpen(true)} className="h-10 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs" data-testid="new-doc-btn">
          <Upload className="w-4 h-4 mr-1" /> Upload file
        </Button>
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 flex-wrap mb-5" data-testid="category-tabs">
        {["All", ...cats].map((c) => (
          <button
            key={c}
            onClick={() => setActive(c)}
            className={`inline-flex items-center gap-1.5 px-3 h-9 rounded-md text-xs font-mono uppercase tracking-[0.15em] font-bold transition-colors ${
              active === c
                ? "bg-red-700 text-white border-2 border-red-900"
                : "bg-white text-slate-700 border-2 border-slate-200 hover:border-red-700"
            }`}
            data-testid={`category-tab-${c}`}
          >
            <Folder className="w-3 h-3" />
            {c}
            {c !== "All" && <span className="ml-0.5 opacity-75">· {counts[c] || 0}</span>}
          </button>
        ))}
      </div>

      {docs === null && <div className="flex justify-center py-10"><Loader2 className="w-5 h-5 animate-spin text-red-700" /></div>}
      {docs && filtered.length === 0 && (
        <div className="bg-white border-2 border-dashed border-slate-300 rounded-md p-10 text-center">
          <FileText className="w-8 h-8 mx-auto text-slate-400" />
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold mt-3">No files in {active}</div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered?.map((d) => {
          const canDelete = d.uploaded_by.user_id === user?.id || ["owner", "admin"].includes(user?.role);
          const dlUrl = `${BACKEND_URL}/api/docs/${d.id}/file`;
          return (
            <div key={d.id} className="bg-white border-2 border-slate-200 hover:border-red-700 rounded-md p-4 transition-colors" data-testid={`doc-card-${d.id}`}>
              <div className="flex items-start gap-2">
                <div className="w-10 h-10 rounded-md bg-blue-600 text-white flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-display font-bold text-slate-900 text-sm truncate" title={d.filename}>{d.filename}</div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.1em] text-slate-500 mt-0.5">
                    {d.category} · {Math.ceil(d.size_bytes / 1024)} KB
                  </div>
                </div>
              </div>
              {d.notes && <div className="text-xs text-slate-600 mt-2 line-clamp-2">{d.notes}</div>}
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
                <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-[0.1em] text-slate-500">
                  <UserAvatar name={d.uploaded_by.name} userId={d.uploaded_by.user_id} size="xs" />
                  {relativeTime(d.uploaded_at)}
                </div>
                <div className="flex items-center gap-1">
                  <a
                    href={dlUrl}
                    target="_blank" rel="noopener noreferrer"
                    className="p-1.5 text-slate-500 hover:text-red-700 rounded hover:bg-slate-100"
                    title="Open"
                    data-testid={`doc-download-${d.id}`}
                  >
                    <Download className="w-4 h-4" />
                  </a>
                  {canDelete && (
                    <button onClick={() => onDelete(d)} className="p-1.5 text-slate-300 hover:text-red-700 rounded hover:bg-slate-100" title="Delete">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <UploadDialog open={open} onOpenChange={setOpen} projectId={projectId} cats={cats} onCreated={load} initialCategory={active !== "All" ? active : null} />
    </div>
  );
}

function UploadDialog({ open, onOpenChange, projectId, cats, onCreated, initialCategory }) {
  const [file, setFile] = useState(null);
  const [category, setCategory] = useState(initialCategory || "General");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) { setFile(null); setNotes(""); }
    else setCategory(initialCategory || "General");
  }, [open, initialCategory]);

  const fileToDataURL = (f) => new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result);
    r.onerror = rej;
    r.readAsDataURL(f);
  });

  const onSave = async (e) => {
    e.preventDefault();
    if (!file) { toast.error("Choose a file"); return; }
    if (file.size > 30 * 1024 * 1024) { toast.error("Max 30 MB"); return; }
    setSaving(true);
    try {
      const file_data = await fileToDataURL(file);
      await api.post(`/projects/${projectId}/docs`, {
        category, filename: file.name, file_data, notes: notes || null,
      });
      toast.success("Uploaded");
      onCreated(); onOpenChange(false);
    } catch (err) {
      toast.error(apiErr(err?.response?.data?.detail, "Upload failed"));
    } finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="upload-dialog">
        <DialogHeader><DialogTitle>Upload file</DialogTitle></DialogHeader>
        <form onSubmit={onSave} className="space-y-4">
          <div>
            <Label>Category</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="mt-1.5" data-testid="upload-category"><SelectValue /></SelectTrigger>
              <SelectContent>
                {cats.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>File <span className="text-slate-400 font-normal">(max 30 MB)</span></Label>
            <Input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="mt-1.5" data-testid="upload-file" />
            {file && <div className="text-xs text-slate-600 mt-1">{file.name} · {Math.ceil(file.size / 1024)} KB</div>}
          </div>
          <div>
            <Label>Notes <span className="text-slate-400 font-normal">(optional)</span></Label>
            <Textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} className="mt-1.5" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={saving || !file} className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="upload-save">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Upload"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
