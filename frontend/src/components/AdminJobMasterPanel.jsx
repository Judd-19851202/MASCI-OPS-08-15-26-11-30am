import React, { useEffect, useState } from "react";
import {
  Briefcase,
  Loader2,
  Plus,
  Trash2,
  Upload,
  Download,
  RefreshCcw,
  CheckCircle2,
  XCircle,
  Users,
  X as XIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { toast } from "sonner";

/**
 * AdminJobMasterPanel — manage MASCI active jobs.
 *
 * Mirrors EquipmentMasterPanel's UX:
 *   • Inline "Add Job" form (single)
 *   • Table of all jobs with edit/delete/toggle-active + PM dropdown
 *   • "Replace from JSON" bulk uploader (drag a .json file with the array)
 *
 * Backend:
 *   GET    /api/admin/jobs
 *   POST   /api/admin/jobs                  (upsert by project_number)
 *   PATCH  /api/admin/jobs/{id}/active
 *   DELETE /api/admin/jobs/{id}
 *   POST   /api/admin/jobs/bulk-replace     ({rows: [...]})
 *
 *   GET    /api/project-managers            (active list, for the PM dropdown)
 */
export default function AdminJobMasterPanel() {
  const [jobs, setJobs] = useState([]);
  const [archive, setArchive] = useState([]);
  const [retainDays, setRetainDays] = useState(14);
  const [showArchive, setShowArchive] = useState(false);
  const [restoringId, setRestoringId] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [pms, setPms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulkText, setBulkText] = useState("");
  const [bulkRunning, setBulkRunning] = useState(false);
  const [savingRow, setSavingRow] = useState(null);
  const [coPmJob, setCoPmJob] = useState(null);   // job whose co-PMs are being edited
  const [coPmDraft, setCoPmDraft] = useState([]); // emails currently selected
  const [savingCoPms, setSavingCoPms] = useState(false);
  const [form, setForm] = useState({
    project_number: "",
    project_name: "",
    location: "",
    client: "",
    pm_email: "",
  });

  const refresh = async () => {
    setLoading(true);
    try {
      const [jr, pr, ar] = await Promise.all([
        api.get("/admin/jobs"),
        api.get("/project-managers"),
        api.get("/admin/jobs/archive").catch(() => ({ data: { items: [], retain_days: 14 } })),
      ]);
      setJobs(jr.data?.items || []);
      setPms(pr.data?.items || []);
      setArchive(ar.data?.items || []);
      setRetainDays(ar.data?.retain_days || 14);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to load jobs / PMs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const pmNameByEmail = (email) => {
    const p = pms.find(
      (x) => (x.email || "").toLowerCase() === (email || "").toLowerCase()
    );
    return p ? p.name : "";
  };

  const addJob = async (e) => {
    e?.preventDefault?.();
    if (!form.project_number.trim() || !form.project_name.trim()) {
      toast.error("Project number + name are required");
      return;
    }
    setAdding(true);
    try {
      await api.post("/admin/jobs", {
        ...form,
        project_manager: pmNameByEmail(form.pm_email),
        active: true,
      });
      toast.success(`Saved job ${form.project_number}`);
      setForm({
        project_number: "",
        project_name: "",
        location: "",
        client: "",
        pm_email: "",
      });
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed");
    } finally {
      setAdding(false);
    }
  };

  const reassignPm = async (job, newPmEmail) => {
    setSavingRow(job.id);
    try {
      await api.post("/admin/jobs", {
        project_number: job.project_number,
        project_name: job.project_name,
        location: job.location || "",
        client: job.client || "",
        project_manager: pmNameByEmail(newPmEmail) || "",
        pm_email: newPmEmail || "",
        active: !!job.active,
      });
      toast.success(
        `${job.project_number} → ${pmNameByEmail(newPmEmail) || "Unassigned"}`
      );
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Reassign failed");
    } finally {
      setSavingRow(null);
    }
  };

  // ---------- Co-PMs ----------
  const openCoPm = (job) => {
    setCoPmJob(job);
    setCoPmDraft(Array.isArray(job.co_pm_emails) ? [...job.co_pm_emails] : []);
  };

  const toggleCoPm = (email) => {
    const e = (email || "").toLowerCase();
    setCoPmDraft((prev) =>
      prev.includes(e) ? prev.filter((x) => x !== e) : (prev.length >= 4 ? prev : [...prev, e])
    );
  };

  const saveCoPms = async () => {
    if (!coPmJob) return;
    setSavingCoPms(true);
    try {
      await api.patch(`/admin/jobs/${coPmJob.id}/co-pms`, {
        co_pm_emails: coPmDraft,
      });
      toast.success(`Co-PMs updated for ${coPmJob.project_number}`);
      setCoPmJob(null);
      setCoPmDraft([]);
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Co-PM save failed");
    } finally {
      setSavingCoPms(false);
    }
  };

  const pmNameByEmailLower = (email) => {
    const e = (email || "").toLowerCase();
    const p = pms.find((x) => (x.email || "").toLowerCase() === e);
    return p ? p.name : email;
  };

  const toggleActive = async (job) => {
    try {
      await api.patch(`/admin/jobs/${job.id}/active`, { active: !job.active });
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Toggle failed");
    }
  };

  const removeJob = async (job) => {
    if (
      !window.confirm(
        `Move job #${job.project_number} — ${job.project_name} to the archive?\n\nYou'll have ${retainDays} days to restore it from the Archive tab before it's purged.`
      )
    )
      return;
    try {
      await api.delete(`/admin/jobs/${job.id}`);
      toast.success(`${job.project_number} moved to archive`);
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    }
  };

  const restoreJob = async (job) => {
    setRestoringId(job.id);
    try {
      await api.post(`/admin/jobs/${job.id}/restore`);
      toast.success(`Restored ${job.project_number}`);
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
      const r = await api.get("/admin/jobs/export", { responseType: "blob" });
      const cd = r.headers["content-disposition"] || r.headers["Content-Disposition"] || "";
      const m = /filename="?([^";]+)"?/i.exec(cd);
      const fname = m ? m[1] : "MASCI_jobs.xlsx";
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

  const runBulk = async () => {
    let rows;
    try {
      rows = JSON.parse(bulkText);
    } catch (e) {
      toast.error("That's not valid JSON");
      return;
    }
    if (!Array.isArray(rows)) {
      toast.error("JSON must be a top-level ARRAY of jobs");
      return;
    }
    setBulkRunning(true);
    try {
      const r = await api.post("/admin/jobs/bulk-replace", { rows });
      toast.success(`Replaced jobs list — ${r.data?.replaced ?? 0} jobs`);
      setBulkOpen(false);
      setBulkText("");
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Bulk replace failed");
    } finally {
      setBulkRunning(false);
    }
  };

  const total = jobs.length;
  const activeCount = jobs.filter((j) => j.active).length;

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-5 sm:p-7 mb-8 shadow-sm"
      data-testid="admin-job-master-panel"
    >
      <div className="flex items-start gap-3 mb-4">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-red-700 text-white shrink-0">
          <Briefcase className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
            MASCI Current Jobs
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            Active Jobs Master
          </h2>
          <p className="text-sm text-slate-600 mt-2">
            Add, edit, deactivate, or bulk-replace the MASCI job list. Active jobs
            show up in the JobPicker on every form. Inactive jobs are hidden from
            the field but kept on file. Total: <strong>{total}</strong> ({activeCount}{" "}
            active).
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="outline"
            onClick={refresh}
            disabled={loading}
            className="h-9 text-xs font-mono uppercase tracking-wide"
            data-testid="job-master-refresh"
          >
            {loading ? (
              <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
            ) : (
              <RefreshCcw className="w-3.5 h-3.5 mr-1" />
            )}
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={onExport}
            disabled={exporting || loading}
            className="h-9 text-xs font-mono uppercase tracking-wide border-2 border-emerald-400 bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
            data-testid="job-master-export-btn"
            title="Download the active jobs list as XLSX"
          >
            {exporting ? (
              <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5 mr-1" />
            )}
            Export
          </Button>
          <Button
            variant="outline"
            onClick={() => setBulkOpen(true)}
            className="h-9 text-xs font-mono uppercase tracking-wide"
            data-testid="job-master-bulk"
          >
            <Upload className="w-3.5 h-3.5 mr-1" /> Bulk Replace
          </Button>
        </div>
      </div>

      {/* Add new job form */}
      <form
        onSubmit={addJob}
        className="grid sm:grid-cols-[1fr_2fr_1fr_1fr_1fr_auto] gap-2 mb-4 p-3 border-2 border-slate-200 rounded bg-slate-50"
      >
        <div>
          <Label className="font-mono text-[9px] uppercase tracking-wide text-slate-700">
            Project #
          </Label>
          <Input
            value={form.project_number}
            onChange={(e) => setForm({ ...form, project_number: e.target.value })}
            placeholder="25-21"
            className="h-9 text-sm mt-1"
            data-testid="job-master-input-project-number"
          />
        </div>
        <div>
          <Label className="font-mono text-[9px] uppercase tracking-wide text-slate-700">
            Project Name
          </Label>
          <Input
            value={form.project_name}
            onChange={(e) => setForm({ ...form, project_name: e.target.value })}
            placeholder="SJR2C - Loop Trail - Spruce Creek"
            className="h-9 text-sm mt-1"
            data-testid="job-master-input-project-name"
          />
        </div>
        <div>
          <Label className="font-mono text-[9px] uppercase tracking-wide text-slate-700">
            Location
          </Label>
          <Input
            value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
            placeholder="Spruce Creek"
            className="h-9 text-sm mt-1"
            data-testid="job-master-input-location"
          />
        </div>
        <div>
          <Label className="font-mono text-[9px] uppercase tracking-wide text-slate-700">
            Client
          </Label>
          <Input
            value={form.client}
            onChange={(e) => setForm({ ...form, client: e.target.value })}
            placeholder="FDOT"
            className="h-9 text-sm mt-1"
            data-testid="job-master-input-client"
          />
        </div>
        <div>
          <Label className="font-mono text-[9px] uppercase tracking-wide text-slate-700">
            PM
          </Label>
          <select
            value={form.pm_email}
            onChange={(e) => setForm({ ...form, pm_email: e.target.value })}
            className="h-9 text-sm mt-1 w-full border border-slate-300 rounded px-2 bg-white"
            data-testid="job-master-input-pm"
          >
            <option value="">— Unassigned —</option>
            {pms.map((p) => (
              <option key={p.id} value={p.email}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-end">
          <Button
            type="submit"
            disabled={adding}
            className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs h-9 px-3 border-b-2 border-red-900"
            data-testid="job-master-add-btn"
          >
            {adding ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <>
                <Plus className="w-3.5 h-3.5 mr-1" /> Add / Update
              </>
            )}
          </Button>
        </div>
      </form>

      {/* Active / Archive tabs */}
      <div className="px-1 mb-3 flex items-center gap-2 flex-wrap" data-testid="job-master-tabs">
        <Button
          type="button"
          size="sm"
          onClick={() => setShowArchive(false)}
          className={`h-8 px-3 text-[11px] font-mono uppercase tracking-wide font-bold ${
            !showArchive
              ? "bg-slate-900 text-white"
              : "bg-white border-2 border-slate-300 text-slate-700 hover:border-amber-600"
          }`}
          data-testid="job-master-tab-active"
        >
          Active ({jobs.length})
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
          data-testid="job-master-tab-archive"
        >
          Archive ({archive.length})
        </Button>
        {showArchive && (
          <span className="text-xs text-slate-500 ml-2">
            Soft-deleted jobs · auto-purged after {retainDays} days. Click ⟲ to restore.
          </span>
        )}
      </div>

      {/* Jobs table */}
      {showArchive ? (
        <div className="overflow-x-auto rounded border border-slate-200">
          {archive.length === 0 ? (
            <p className="text-sm text-slate-500 py-8 text-center italic">
              Archive is empty — nothing to restore.
            </p>
          ) : (
            <table className="w-full text-sm" data-testid="job-master-archive-table">
              <thead className="bg-slate-100">
                <tr className="text-left font-mono text-[10px] uppercase tracking-wide text-slate-700">
                  <th className="px-3 py-2">#</th>
                  <th className="px-3 py-2">Project Name</th>
                  <th className="px-3 py-2">Location</th>
                  <th className="px-3 py-2">Client</th>
                  <th className="px-3 py-2">Deleted</th>
                  <th className="px-3 py-2 w-12"></th>
                </tr>
              </thead>
              <tbody>
                {archive.map((j) => (
                  <tr
                    key={j.id}
                    className="border-t border-slate-100 bg-slate-50/40"
                    data-testid={`job-archive-row-${j.id}`}
                  >
                    <td className="px-3 py-2 font-mono text-xs font-bold text-slate-900">
                      {j.project_number}
                    </td>
                    <td className="px-3 py-2 text-slate-800">{j.project_name}</td>
                    <td className="px-3 py-2 text-slate-600">{j.location || "—"}</td>
                    <td className="px-3 py-2 text-slate-600">{j.client || "—"}</td>
                    <td className="px-3 py-2 text-xs text-slate-500 whitespace-nowrap">
                      {j.deleted_at ? new Date(j.deleted_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        size="icon"
                        variant="outline"
                        onClick={() => restoreJob(j)}
                        disabled={restoringId === j.id}
                        className="h-8 w-8 border-2 border-emerald-400 text-emerald-700 hover:bg-emerald-50"
                        data-testid={`job-restore-${j.id}`}
                        title="Restore to active list"
                      >
                        {restoringId === j.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          "⟲"
                        )}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ) : (
      <div className="overflow-x-auto rounded border border-slate-200">
        <table className="w-full text-sm" data-testid="job-master-table">
          <thead className="bg-slate-100">
            <tr className="text-left font-mono text-[10px] uppercase tracking-wide text-slate-700">
              <th className="px-3 py-2">#</th>
              <th className="px-3 py-2">Project Name</th>
              <th className="px-3 py-2">Location</th>
              <th className="px-3 py-2">Client</th>
              <th className="px-3 py-2">PM</th>
              <th className="px-3 py-2">Co-PMs</th>
              <th className="px-3 py-2 text-center">Active</th>
              <th className="px-3 py-2 w-12"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} className="px-3 py-6 text-center text-slate-500">
                  <Loader2 className="w-5 h-5 animate-spin inline-block" /> Loading…
                </td>
              </tr>
            ) : jobs.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-3 py-6 text-center text-slate-500">
                  No jobs yet. Add one above or bulk-replace from JSON.
                </td>
              </tr>
            ) : (
              jobs.map((j) => (
                <tr
                  key={j.id}
                  className={`border-t border-slate-100 ${j.active ? "" : "bg-slate-50 text-slate-500"}`}
                  data-testid={`job-row-${j.project_number}`}
                >
                  <td className="px-3 py-2 font-mono text-xs whitespace-nowrap">
                    <span className="inline-block px-1.5 py-0.5 bg-red-700 text-white rounded font-bold">
                      {j.project_number}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-medium">{j.project_name}</td>
                  <td className="px-3 py-2 text-xs text-slate-600">{j.location || "—"}</td>
                  <td className="px-3 py-2 text-xs text-slate-600">{j.client || "—"}</td>
                  <td className="px-3 py-2 text-xs">
                    <div className="flex items-center gap-1.5">
                      <select
                        value={j.pm_email || ""}
                        onChange={(e) => reassignPm(j, e.target.value)}
                        disabled={savingRow === j.id}
                        className={`h-7 text-xs border border-slate-300 rounded px-1.5 max-w-[150px] ${
                          j.pm_email ? "bg-white text-slate-800" : "bg-amber-50 text-amber-700 border-amber-300"
                        }`}
                        data-testid={`job-pm-select-${j.project_number}`}
                        title="Reassign PM"
                      >
                        <option value="">— Unassigned —</option>
                        {pms.map((p) => (
                          <option key={p.id} value={p.email}>
                            {p.name}
                          </option>
                        ))}
                      </select>
                      {savingRow === j.id && (
                        <Loader2 className="w-3 h-3 animate-spin text-slate-400" />
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-2 text-xs">
                    <div className="flex items-center gap-1 flex-wrap max-w-[260px]">
                      {(j.co_pm_emails || []).slice(0, 4).map((e) => (
                        <span
                          key={e}
                          className="inline-flex items-center px-1.5 py-0.5 rounded bg-slate-200 text-slate-800 font-mono text-[10px]"
                          title={e}
                        >
                          {pmNameByEmailLower(e)}
                        </span>
                      ))}
                      <button
                        type="button"
                        onClick={() => openCoPm(j)}
                        className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded border border-dashed border-slate-300 text-slate-500 hover:border-amber-500 hover:text-amber-700 font-mono text-[10px] uppercase tracking-wide"
                        data-testid={`job-copm-add-${j.project_number}`}
                        title="Add or remove co-PMs"
                      >
                        <Plus className="w-2.5 h-2.5" />
                        {(j.co_pm_emails || []).length === 0 ? "Add" : "Edit"}
                      </button>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-center">
                    <button
                      type="button"
                      onClick={() => toggleActive(j)}
                      className={`inline-flex items-center justify-center w-7 h-7 rounded ${j.active ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200" : "bg-slate-200 text-slate-500 hover:bg-slate-300"}`}
                      title={j.active ? "Click to deactivate" : "Click to activate"}
                      data-testid={`job-toggle-${j.project_number}`}
                    >
                      {j.active ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                    </button>
                  </td>
                  <td className="px-3 py-2">
                    <button
                      type="button"
                      onClick={() => removeJob(j)}
                      className="inline-flex items-center justify-center w-7 h-7 rounded text-slate-400 hover:text-red-600 hover:bg-red-50"
                      title="Delete"
                      data-testid={`job-delete-${j.project_number}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      )}

      {/* Bulk replace dialog */}
      <Dialog open={bulkOpen} onOpenChange={setBulkOpen}>
        <DialogContent className="max-w-2xl" data-testid="job-master-bulk-dialog">
          <DialogHeader>
            <DialogTitle className="font-display font-black">
              Bulk replace MASCI jobs
            </DialogTitle>
            <DialogDescription>
              Paste a JSON <strong>array</strong> of jobs. Every existing job is
              wiped and replaced. Each item needs at minimum{" "}
              <code>project_number</code> and <code>project_name</code>; optional{" "}
              <code>location</code>, <code>client</code>,{" "}
              <code>project_manager</code>, <code>active</code>.
            </DialogDescription>
          </DialogHeader>
          <textarea
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
            rows={14}
            className="w-full font-mono text-xs border-2 border-slate-300 rounded p-2"
            placeholder={`[
  {"project_number": "25-21", "project_name": "SJR2C - Loop Trail - Spruce Creek", "client": "City of Port Orange", "project_manager": "Ramon Rodriguez", "active": true}
]`}
            data-testid="job-master-bulk-textarea"
          />
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setBulkOpen(false)}
              disabled={bulkRunning}
            >
              Cancel
            </Button>
            <Button
              onClick={runBulk}
              disabled={bulkRunning || !bulkText.trim()}
              className="bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide"
              data-testid="job-master-bulk-confirm"
            >
              {bulkRunning ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Replacing…
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" /> Replace all jobs
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Co-PMs editor — assign up to 4 additional PMs per job */}
      <Dialog open={!!coPmJob} onOpenChange={(o) => !o && setCoPmJob(null)}>
        <DialogContent data-testid="co-pm-dialog">
          <DialogHeader>
            <DialogTitle className="font-display font-black flex items-center gap-2 text-amber-700">
              <Users className="w-5 h-5" />
              Co-PMs for {coPmJob?.project_number}
            </DialogTitle>
            <DialogDescription className="leading-relaxed">
              Pick up to <strong>4 additional PMs</strong> who should also
              receive every Daily Report, Incident, Inspection, Meeting,
              and Pre-Op email filed against this job. The primary PM
              ({pmNameByEmail(coPmJob?.pm_email) || "Unassigned"}) stays
              unchanged — co-PMs are CC'd on top.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-1.5 max-h-[50vh] overflow-y-auto pr-1">
            {pms
              .filter((p) => (p.email || "").toLowerCase() !== (coPmJob?.pm_email || "").toLowerCase())
              .map((p) => {
                const e = (p.email || "").toLowerCase();
                const checked = coPmDraft.includes(e);
                const disabled = !checked && coPmDraft.length >= 4;
                return (
                  <label
                    key={p.id}
                    className={`flex items-center gap-2 p-2 rounded border ${
                      checked
                        ? "bg-amber-50 border-amber-400"
                        : disabled
                        ? "bg-slate-50 border-slate-200 opacity-50 cursor-not-allowed"
                        : "bg-white border-slate-200 hover:bg-slate-50 cursor-pointer"
                    }`}
                    data-testid={`co-pm-option-${p.id}`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={disabled}
                      onChange={() => toggleCoPm(p.email)}
                      className="w-4 h-4"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-bold text-slate-900 truncate">{p.name}</div>
                      <div className="text-[11px] font-mono text-slate-500 truncate">{p.email}</div>
                    </div>
                    {p.is_active === false && (
                      <span className="text-[10px] font-mono uppercase tracking-wide text-slate-400">Inactive</span>
                    )}
                  </label>
                );
              })}
            {pms.filter((p) => (p.email || "").toLowerCase() !== (coPmJob?.pm_email || "").toLowerCase()).length === 0 && (
              <div className="text-sm text-slate-500 text-center py-4">
                No other PMs available — add them in the Project Managers panel first.
              </div>
            )}
          </div>

          <div className="text-[11px] font-mono uppercase tracking-wide text-slate-600 pt-1">
            {coPmDraft.length} / 4 selected
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setCoPmJob(null)}
              disabled={savingCoPms}
              data-testid="co-pm-cancel"
            >
              <XIcon className="w-4 h-4 mr-1" /> Cancel
            </Button>
            <Button
              onClick={saveCoPms}
              disabled={savingCoPms}
              className="bg-amber-600 hover:bg-amber-700 text-white font-bold uppercase tracking-wide"
              data-testid="co-pm-save"
            >
              {savingCoPms ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Saving…
                </>
              ) : (
                <>Save co-PMs</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
