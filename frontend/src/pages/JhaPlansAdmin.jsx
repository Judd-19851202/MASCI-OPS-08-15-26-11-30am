import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, FileText, Upload, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { MasciLogo } from "@/components/MasciLogo";
import { JobPicker } from "@/components/JobPicker";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { JOB_LIBRARY as JOBS } from "@/lib/jobLibrary";

const REACT_APP_BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => resolve(reader.result);
    reader.readAsDataURL(file);
  });
}

export default function JhaPlansAdmin() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    project_number: "",
    project_name: "",
    location: "",
    file: null,
    uploaded_by: "",
    notes: "",
  });

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/job-hazard-plans");
      setPlans(r.data || []);
    } catch {
      setPlans([]);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { refresh(); }, []);

  const onJob = (j) => {
    setForm((p) => ({
      ...p,
      project_number: j ? j.project_number : "",
      project_name: j ? j.project_name : "",
      location: p.location || (j && j.location) || "",
    }));
  };

  const onSubmit = async () => {
    if (!form.project_number || !form.file) {
      return toast.error("Pick a job and a PDF file");
    }
    setSaving(true);
    try {
      const dataUrl = await readFileAsDataUrl(form.file);
      await api.post("/job-hazard-plans", {
        project_number: form.project_number,
        project_name: form.project_name,
        location: form.location,
        filename: form.file.name,
        file_data: dataUrl,
        uploaded_by: form.uploaded_by,
        notes: form.notes,
      });
      toast.success("Plan uploaded");
      setOpen(false);
      setForm({ project_number: "", project_name: "", location: "", file: null, uploaded_by: "", notes: "" });
      refresh();
    } catch (e) {
      console.error(e);
      toast.error(e?.response?.data?.detail || "Upload failed");
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (project_number) => {
    if (!window.confirm(`Delete the Job Hazard Plan for ${project_number}? This cannot be undone.`)) return;
    try {
      await api.delete(`/job-hazard-plans/${encodeURIComponent(project_number)}`);
      toast.success("Plan deleted");
      refresh();
    } catch {
      toast.error("Delete failed");
    }
  };

  const planByNumber = Object.fromEntries(plans.map((p) => [p.project_number, p]));

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link to="/admin" className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide" data-testid="back-link">
            <ArrowLeft className="w-4 h-4 mr-1" /> Admin
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/admin" />
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button className="h-10 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-xs" data-testid="upload-btn">
                <Upload className="w-4 h-4 mr-1" /> Upload Plan
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle className="font-display font-black">Upload Job Hazard Plan</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">MASCI Job</Label>
                  <div className="mt-1">
                    <JobPicker projectName={form.project_name} projectNumber={form.project_number} onSelect={onJob} />
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Project #</Label>
                    <Input value={form.project_number} onChange={(e) => setForm((p) => ({ ...p, project_number: e.target.value }))} className="h-10 mt-1 border-2" />
                  </div>
                  <div>
                    <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Location</Label>
                    <Input value={form.location} onChange={(e) => setForm((p) => ({ ...p, location: e.target.value }))} className="h-10 mt-1 border-2" />
                  </div>
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">PDF File</Label>
                  <Input type="file" accept="application/pdf,.pdf" onChange={(e) => setForm((p) => ({ ...p, file: e.target.files?.[0] || null }))} className="h-10 mt-1 border-2 file:mr-2 file:py-2 file:px-3 file:rounded file:border-0 file:bg-slate-900 file:text-white file:font-bold" data-testid="upload-file-input" />
                  {form.file && (
                    <p className="text-xs text-slate-500 mt-1">{form.file.name} · {(form.file.size / 1024).toFixed(1)} KB</p>
                  )}
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Uploaded By</Label>
                  <Input value={form.uploaded_by} onChange={(e) => setForm((p) => ({ ...p, uploaded_by: e.target.value }))} className="h-10 mt-1 border-2" placeholder="Your name" />
                </div>
                <div>
                  <Label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Notes</Label>
                  <Textarea value={form.notes} onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))} className="mt-1 border-2" placeholder="Revision date, changes, etc." />
                </div>
                <Button onClick={onSubmit} disabled={saving} className="w-full h-12 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide" data-testid="confirm-upload-btn">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Upload className="w-4 h-4 mr-1" />}
                  {saving ? "Uploading…" : "Upload"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
        <div className="mb-6">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">Job Hazard Plans</span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
            File Repository — one PDF per job
          </h1>
          <p className="text-slate-600 text-sm mt-2">
            Upload one Job Hazard Plan PDF per active MASCI job. Foremen browse the same list at <span className="font-mono text-red-700">/jha</span> on their phones to view it before crew breaks ground.
          </p>
        </div>

        {loading ? (
          <div className="p-12 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
          </div>
        ) : (
          <ul className="bg-white border-2 border-slate-300 rounded-md divide-y-2 divide-slate-100">
            {JOBS.map((job) => {
              const plan = planByNumber[job.project_number];
              return (
                <li key={job.project_number} className={`p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-3 ${plan ? "" : "bg-slate-50"}`} data-testid={`admin-jha-row-${job.project_number}`}>
                  <div className="flex-1 min-w-0">
                    <div className="font-display font-bold text-slate-900 truncate">
                      {job.project_number} · {job.project_name}
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5 truncate">{job.location}</div>
                    {plan && (
                      <div className="text-xs text-slate-500 mt-1 italic">
                        {plan.filename} · {(plan.file_size / 1024).toFixed(0)} KB · uploaded {new Date(plan.uploaded_at).toLocaleDateString()}{plan.uploaded_by ? ` by ${plan.uploaded_by}` : ""}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {plan ? (
                      <>
                        <a href={`${REACT_APP_BACKEND_URL}/api/job-hazard-plans/${encodeURIComponent(job.project_number)}/file`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center justify-center h-10 px-3 rounded-md bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs uppercase tracking-wide" data-testid={`admin-view-${job.project_number}`}>
                          <FileText className="w-4 h-4 mr-1" /> View
                        </a>
                        <Button variant="outline" size="icon" className="h-10 w-10 border-2 border-slate-300 hover:border-red-500 hover:text-red-600" onClick={() => onDelete(job.project_number)} data-testid={`admin-delete-${job.project_number}`}>
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-[10px] uppercase tracking-[0.15em] font-bold bg-amber-50 text-amber-800 border border-amber-300">
                        Not Uploaded
                      </span>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </main>
    </div>
  );
}
