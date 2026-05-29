// HrSafetyRecords — iter353a-UI
// Shared HR + Safety operational ownership of employee accountability.
// HR can now: + Add Training Record, + Upload Safety Document, edit/archive
// records they or Safety entered. HR cannot hard-delete (operator policy).
// Audit attribution (who/role) is surfaced on every row.
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  FolderArchive, Award, Loader2, Download, Filter, AlertTriangle,
  Plus, Upload, Archive, Edit3, X, ShieldCheck,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { EmptyState, LoadingState } from "@/components/ui/PortalStates";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import HrPageShell from "@/components/HrPageShell";
import { getHrToken } from "@/lib/hrAuth";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: { "X-HR-Token": getHrToken() } });

function bytes(n) {
  if (!n) return "0 B";
  const u = ["B", "KB", "MB", "GB"];
  let i = 0; let v = n;
  while (v > 1024 && i < u.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(1)} ${u[i]}`;
}

function expStatus(rec) {
  if (!rec.expiration_date) return "none";
  const today = new Date().toISOString().slice(0, 10);
  const thirty = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
  if (rec.expiration_date < today) return "expired";
  if (rec.expiration_date <= thirty) return "soon";
  return "ok";
}

const EXP_PILL = {
  expired: "bg-red-100 text-red-900 border-red-300",
  soon: "bg-amber-100 text-amber-900 border-amber-300",
  ok: "bg-emerald-100 text-emerald-900 border-emerald-300",
  none: "bg-slate-100 text-slate-700 border-slate-300",
};

const ROLE_PILL = {
  hr: "bg-purple-100 text-purple-900 border-purple-300",
  safety: "bg-cyan-100 text-cyan-900 border-cyan-300",
  admin: "bg-slate-900 text-white border-slate-900",
  legacy: "bg-slate-100 text-slate-500 border-slate-300",
};

function inputCls(extra = "") {
  return `h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-700 ${extra}`;
}

// ── Add-Training inline form ─────────────────────────────────────────
function AddTrainingForm({ onCreated, onCancel, t }) {
  const today = new Date().toISOString().slice(0, 10);
  const [employee, setEmployee] = useState("");
  const [employees, setEmployees] = useState([]);
  const [trainingName, setTrainingName] = useState("");
  const [certType, setCertType] = useState("");
  const [completed, setCompleted] = useState(today);
  const [expires, setExpires] = useState("");
  const [issuedBy, setIssuedBy] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    axios.get(`${API}/employees`, auth()).then((r) => {
      const list = Array.isArray(r.data) ? r.data : (r.data?.items || []);
      setEmployees(list.filter((e) => !e.deleted_at).map((e) => ({ id: e.id, name: e.name })));
    }).catch(() => {});
  }, []);

  const submit = async () => {
    if (!employee || !trainingName.trim() || !completed) {
      toast.error(t("Employee, training name, and completion date are required."));
      return;
    }
    setSubmitting(true);
    try {
      const emp = employees.find((e) => e.id === employee);
      const body = {
        employee_id: employee,
        employee_name: emp?.name || "",
        employee_master_id: employee,
        training_name: trainingName.trim(),
        certification_type: certType.trim(),
        completed_date: completed,
        expiration_date: expires || null,
        issued_by: issuedBy.trim(),
        notes: notes.trim(),
      };
      const r = await axios.post(`${API}/safety/training-records`, body, auth());
      toast.success(t("Training record added."));
      onCreated(r.data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not add training record."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-purple-50/40 border-2 border-purple-300 rounded p-4 mb-4" data-testid="hr-safety-add-training-form">
      <div className="flex items-center justify-between mb-3">
        <div className="font-bold text-purple-900 flex items-center gap-2"><Plus className="w-4 h-4" /> {t("Add Training Record")}</div>
        <button onClick={onCancel} className="text-slate-500 hover:text-slate-900" aria-label="close"><X className="w-4 h-4" /></button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Employee")} *</div>
          <select value={employee} onChange={(e) => setEmployee(e.target.value)} className={inputCls("w-full px-2 bg-white")} data-testid="hr-safety-add-training-employee">
            <option value="">{t("Choose…")}</option>
            {employees.map((e) => <option key={e.id} value={e.id}>{e.name}</option>)}
          </select>
        </label>
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Training Name")} *</div>
          <Input value={trainingName} onChange={(e) => setTrainingName(e.target.value)} className={inputCls()} placeholder="OSHA 10-hour" data-testid="hr-safety-add-training-name" />
        </label>
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Certification Type")}</div>
          <Input value={certType} onChange={(e) => setCertType(e.target.value)} className={inputCls()} placeholder="OSHA · CPR · CDL · Equipment" data-testid="hr-safety-add-training-type" />
        </label>
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Completed Date")} *</div>
          <Input type="date" value={completed} onChange={(e) => setCompleted(e.target.value)} className={inputCls()} data-testid="hr-safety-add-training-completed" />
        </label>
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Expiration Date")}</div>
          <Input type="date" value={expires} onChange={(e) => setExpires(e.target.value)} className={inputCls()} data-testid="hr-safety-add-training-expires" />
        </label>
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Issued By")}</div>
          <Input value={issuedBy} onChange={(e) => setIssuedBy(e.target.value)} className={inputCls()} placeholder="Training provider / instructor" data-testid="hr-safety-add-training-issuer" />
        </label>
        <label className="block sm:col-span-2">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Notes")}</div>
          <Input value={notes} onChange={(e) => setNotes(e.target.value)} className={inputCls()} data-testid="hr-safety-add-training-notes" />
        </label>
      </div>
      <div className="flex justify-end gap-2 mt-3">
        <Button variant="outline" onClick={onCancel} disabled={submitting} data-testid="hr-safety-add-training-cancel">{t("Cancel")}</Button>
        <Button onClick={submit} disabled={submitting} className="bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-safety-add-training-submit">
          {submitting ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Plus className="w-4 h-4 mr-1" />}
          {t("Add Record")}
        </Button>
      </div>
    </div>
  );
}

// ── Upload-Document inline form ──────────────────────────────────────
function UploadDocForm({ onUploaded, onCancel, t }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("General");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (!file) { toast.error(t("Choose a file to upload.")); return; }
    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("title", title || file.name);
      fd.append("category", category);
      fd.append("description", description);
      fd.append("tags", tags);
      const r = await axios.post(`${API}/safety/documents`, fd, {
        headers: { "X-HR-Token": getHrToken() },
      });
      toast.success(t("Document uploaded."));
      onUploaded(r.data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Upload failed."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-purple-50/40 border-2 border-purple-300 rounded p-4 mb-4" data-testid="hr-safety-upload-doc-form">
      <div className="flex items-center justify-between mb-3">
        <div className="font-bold text-purple-900 flex items-center gap-2"><Upload className="w-4 h-4" /> {t("Upload Safety Document")}</div>
        <button onClick={onCancel} className="text-slate-500 hover:text-slate-900"><X className="w-4 h-4" /></button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        <label className="block sm:col-span-2">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("File")} *</div>
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded file:border-2 file:border-purple-300 file:bg-white file:font-bold file:text-purple-900 hover:file:border-purple-500"
            data-testid="hr-safety-upload-doc-file"
          />
          {file && <div className="text-xs text-slate-600 mt-1 font-mono">{file.name} · {bytes(file.size)}</div>}
        </label>
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Title")}</div>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} className={inputCls()} placeholder={file?.name || "Untitled"} data-testid="hr-safety-upload-doc-title" />
        </label>
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Category")}</div>
          <select value={category} onChange={(e) => setCategory(e.target.value)} className={inputCls("w-full px-2 bg-white")} data-testid="hr-safety-upload-doc-category">
            {["General", "OSHA", "CDL", "Medical", "Certification", "Fit-for-Duty", "Onboarding", "Insurance", "Policy"].map((c) =>
              <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className="block sm:col-span-2">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Description")}</div>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} className={inputCls()} placeholder={t("Short description (optional)")} data-testid="hr-safety-upload-doc-description" />
        </label>
        <label className="block sm:col-span-2">
          <div className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-700 font-bold mb-1">{t("Tags")}</div>
          <Input value={tags} onChange={(e) => setTags(e.target.value)} className={inputCls()} placeholder="comma, separated, tags" data-testid="hr-safety-upload-doc-tags" />
        </label>
      </div>
      <div className="flex justify-end gap-2 mt-3">
        <Button variant="outline" onClick={onCancel} disabled={submitting}>{t("Cancel")}</Button>
        <Button onClick={submit} disabled={submitting || !file} className="bg-purple-700 hover:bg-purple-800 text-white" data-testid="hr-safety-upload-doc-submit">
          {submitting ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Upload className="w-4 h-4 mr-1" />}
          {t("Upload")}
        </Button>
      </div>
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────
export default function HrSafetyRecords() {
  const { t } = useT();
  const [docs, setDocs] = useState([]);
  const [training, setTraining] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [addTrainingOpen, setAddTrainingOpen] = useState(false);
  const [uploadDocOpen, setUploadDocOpen] = useState(false);
  const [archiving, setArchiving] = useState({});

  const load = async () => {
    setLoading(true);
    try {
      const [d, tr] = await Promise.all([
        axios.get(`${API}/safety/documents`, auth()),
        axios.get(`${API}/safety/training-records`, auth()),
      ]);
      setDocs(Array.isArray(d.data) ? d.data : []);
      setTraining(Array.isArray(tr.data) ? tr.data : []);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not load safety records"));
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const filteredDocs = useMemo(() => {
    if (!search.trim()) return docs;
    const s = search.trim().toLowerCase();
    return docs.filter((d) =>
      (d.title || "").toLowerCase().includes(s)
      || (d.category || "").toLowerCase().includes(s)
      || (d.description || "").toLowerCase().includes(s)
      || (d.tags || []).join(",").toLowerCase().includes(s),
    );
  }, [docs, search]);

  const filteredTraining = useMemo(() => {
    if (!search.trim()) return training;
    const s = search.trim().toLowerCase();
    return training.filter((r) =>
      (r.employee_name || "").toLowerCase().includes(s)
      || (r.training_name || "").toLowerCase().includes(s)
      || (r.certification_type || "").toLowerCase().includes(s),
    );
  }, [training, search]);

  const downloadDoc = async (doc) => {
    try {
      const r = await axios.get(`${API}/safety/documents/${doc.id}/download`, { ...auth(), responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement("a");
      a.href = url; a.download = doc.filename || `${doc.id}.bin`;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Download failed"));
    }
  };

  // iter353a-UI · PATCH-to-archive pattern (no hard delete)
  const archiveTraining = async (rec) => {
    if (!window.confirm(t("Archive this training record? It will be hidden from active views but preserved in audit history."))) return;
    setArchiving((a) => ({ ...a, [rec.id]: true }));
    try {
      await axios.patch(`${API}/safety/training-records/${rec.id}`, {
        notes: `${rec.notes || ""}${rec.notes ? " · " : ""}[archived ${new Date().toISOString().slice(0, 10)}]`.trim(),
        certification_type: rec.certification_type ? `${rec.certification_type} (archived)` : "(archived)",
      }, auth());
      toast.success(t("Training record archived."));
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Archive failed."));
    } finally {
      setArchiving((a) => { const { [rec.id]: _, ...rest } = a; return rest; });
    }
  };

  const archiveDoc = async (d) => {
    if (!window.confirm(t("Archive this document? It will be hidden from active views but preserved in audit history."))) return;
    setArchiving((a) => ({ ...a, [d.id]: true }));
    try {
      await axios.patch(`${API}/safety/documents/${d.id}`, {
        category: "Archived",
        description: `${d.description || ""}${d.description ? " · " : ""}[archived ${new Date().toISOString().slice(0, 10)}]`.trim(),
      }, auth());
      toast.success(t("Document archived."));
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Archive failed."));
    } finally {
      setArchiving((a) => { const { [d.id]: _, ...rest } = a; return rest; });
    }
  };

  const isArchived = (r) => (r.category === "Archived") || /\[archived /.test(r.notes || r.description || "");

  return (
    <HrPageShell title="Safety Records" kicker="HR · SHARED ACCOUNTABILITY · TRAINING & DOCUMENTS">
      {/* INTRO STRIP — shared-authority calm tone */}
      <div className="bg-purple-50/40 border-2 border-purple-200 rounded p-3 mb-4 flex items-start gap-3" data-testid="hr-safety-intro-strip">
        <ShieldCheck className="w-5 h-5 text-purple-700 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-slate-800">
          <strong className="text-purple-900">{t("Shared HR + Safety accountability surface.")}</strong> {" "}
          {t("HR can add training, upload safety documents, and archive records. Safety governance (incidents, JHAs, inspections) remains in the Safety Portal. Hard-delete is reserved for Safety/Admin — HR archives instead.")}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <Filter className="w-4 h-4 text-slate-500" />
        <Input
          placeholder={t("Search title, employee, training, tags…")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-700 max-w-md"
          data-testid="hr-safety-search"
        />
        <div className="flex-1" />
        <Button
          onClick={() => { setAddTrainingOpen(true); setUploadDocOpen(false); }}
          className="bg-purple-700 hover:bg-purple-800 text-white"
          data-testid="hr-safety-add-training-btn"
        >
          <Plus className="w-4 h-4 mr-1" /> {t("Add Training Record")}
        </Button>
        <Button
          onClick={() => { setUploadDocOpen(true); setAddTrainingOpen(false); }}
          variant="outline"
          className="border-purple-700 text-purple-700 hover:bg-purple-50"
          data-testid="hr-safety-upload-doc-btn"
        >
          <Upload className="w-4 h-4 mr-1" /> {t("Upload Document")}
        </Button>
      </div>

      {addTrainingOpen && (
        <AddTrainingForm
          t={t}
          onCancel={() => setAddTrainingOpen(false)}
          onCreated={(rec) => { setAddTrainingOpen(false); load(); }}
        />
      )}
      {uploadDocOpen && (
        <UploadDocForm
          t={t}
          onCancel={() => setUploadDocOpen(false)}
          onUploaded={(d) => { setUploadDocOpen(false); load(); }}
        />
      )}

      {loading ? (
        <LoadingState label={t("Loading…")} testId="hr-safety-loading" />
      ) : (
        <Tabs defaultValue="docs">
          <TabsList>
            <TabsTrigger value="docs" data-testid="hr-safety-tab-docs">
              <FolderArchive className="w-4 h-4 mr-1" /> {t("Documents")} ({docs.length})
            </TabsTrigger>
            <TabsTrigger value="training" data-testid="hr-safety-tab-training">
              <Award className="w-4 h-4 mr-1" /> {t("Training")} ({training.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="docs">
            {filteredDocs.length === 0 ? (
              <EmptyState
                icon={FolderArchive}
                title={t("No documents yet")}
                body={t("Upload your first safety document using the Upload button above.")}
                testId="hr-safety-docs-empty"
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="hr-safety-doc-list">
                {filteredDocs.map((d) => {
                  const archived = isArchived(d);
                  const role = (d.created_by_role || d.uploaded_by_role || "legacy").toLowerCase();
                  return (
                    <div key={d.id} className={`bg-white border-2 ${archived ? "border-slate-200 opacity-60" : "border-slate-200"} rounded-md p-4`}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 mb-1">
                            <span className="inline-block px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-[10px] font-mono uppercase tracking-[0.18em] font-bold">{d.category}</span>
                            <Badge variant="outline" className={`${ROLE_PILL[role] || ROLE_PILL.legacy} text-[9px] font-mono uppercase`} title={`Uploaded by ${d.uploaded_by_name || d.created_by || "legacy"}`}>{role}</Badge>
                            {archived && <Badge variant="outline" className="bg-slate-200 text-slate-700 border-slate-300 text-[9px] font-mono uppercase">{t("ARCHIVED")}</Badge>}
                          </div>
                          <h3 className="font-display text-lg font-black text-slate-900 truncate">{d.title}</h3>
                          <div className="text-xs text-slate-500 mt-0.5 truncate">{d.filename} · {bytes(d.file_size)}</div>
                          {d.description && <p className="text-sm text-slate-600 mt-1 line-clamp-2">{d.description}</p>}
                        </div>
                        <div className="flex flex-col gap-1">
                          <Button size="sm" variant="outline" onClick={() => downloadDoc(d)} className="h-8 border-purple-300 text-purple-800" data-testid={`hr-safety-doc-download-${d.id}`}>
                            <Download className="w-3.5 h-3.5" />
                          </Button>
                          {!archived && (
                            <Button size="sm" variant="outline" onClick={() => archiveDoc(d)} disabled={!!archiving[d.id]} className="h-8 border-amber-300 text-amber-800" data-testid={`hr-safety-doc-archive-${d.id}`} title={t("Archive (HR does not hard-delete)")}>
                              {archiving[d.id] ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Archive className="w-3.5 h-3.5" />}
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </TabsContent>

          <TabsContent value="training">
            {filteredTraining.length === 0 ? (
              <EmptyState
                icon={Award}
                title={t("No training records yet")}
                body={t("Add your first training record using the Add Training button above.")}
                testId="hr-safety-training-empty"
              />
            ) : (
              <div className="overflow-x-auto" data-testid="hr-safety-training-list">
                <table className="w-full text-sm min-w-[900px]">
                  <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                    <tr>
                      <th className="text-left px-3 py-2">{t("Employee")}</th>
                      <th className="text-left px-3 py-2">{t("Training")}</th>
                      <th className="text-left px-3 py-2">{t("Type")}</th>
                      <th className="text-left px-3 py-2">{t("Completed")}</th>
                      <th className="text-left px-3 py-2">{t("Expires")}</th>
                      <th className="text-center px-3 py-2">{t("Status")}</th>
                      <th className="text-center px-3 py-2">{t("Entered By")}</th>
                      <th className="text-center px-3 py-2 w-20">{t("Action")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTraining.map((r) => {
                      const st = expStatus(r);
                      const label = st === "expired" ? t("Expired") : st === "soon" ? t("Expiring 30d") : st === "ok" ? t("Current") : t("No expiry");
                      const archived = isArchived(r);
                      const role = (r.created_by_role || "legacy").toLowerCase();
                      return (
                        <tr key={r.id} className={`border-t border-slate-100 ${archived ? "opacity-50" : ""} ${st === "expired" && !archived ? "bg-red-50" : ""}`} data-testid={`hr-safety-training-row-${r.id}`}>
                          <td className="px-3 py-2 font-semibold">
                            {r.employee_name}
                            {archived && <Badge variant="outline" className="ml-2 bg-slate-200 text-slate-700 border-slate-300 text-[9px] font-mono uppercase">{t("ARCHIVED")}</Badge>}
                          </td>
                          <td className="px-3 py-2">{r.training_name}</td>
                          <td className="px-3 py-2 text-slate-600 text-xs font-mono">{r.certification_type || "—"}</td>
                          <td className="px-3 py-2">{r.completed_date || "—"}</td>
                          <td className="px-3 py-2">
                            {r.expiration_date || <span className="text-slate-400">—</span>}
                            {st === "expired" && <AlertTriangle className="w-3.5 h-3.5 text-red-600 inline ml-1" />}
                          </td>
                          <td className="px-3 py-2 text-center">
                            <span className={`inline-block px-2 py-0.5 rounded border text-[11px] font-mono uppercase tracking-[0.15em] font-bold ${EXP_PILL[st]}`}>{label}</span>
                          </td>
                          <td className="px-3 py-2 text-center" title={r.created_by || r.created_by_name || "legacy"}>
                            <Badge variant="outline" className={`${ROLE_PILL[role] || ROLE_PILL.legacy} text-[9px] font-mono uppercase`}>{role}</Badge>
                          </td>
                          <td className="px-3 py-2 text-center">
                            {!archived && (
                              <button onClick={() => archiveTraining(r)} disabled={!!archiving[r.id]} className="text-amber-700 hover:text-amber-900 disabled:opacity-50" data-testid={`hr-safety-training-archive-${r.id}`} title={t("Archive (HR does not hard-delete)")}>
                                {archiving[r.id] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Archive className="w-4 h-4" />}
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}
    </HrPageShell>
  );
}
