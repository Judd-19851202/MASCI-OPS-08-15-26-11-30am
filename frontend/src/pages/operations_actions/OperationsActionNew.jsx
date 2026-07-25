/**
 * OA-1 · OperationsActionNew.jsx
 * 30-second creation form. Mobile-first.
 */
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Home, Loader2, Save } from "lucide-react";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { usePageTitle } from "@/lib/usePageTitle";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import CoachingPanel from "@/components/oa/CoachingPanel";
import OwnerPicker from "@/components/oa/OwnerPicker";
import {
  inferOperationsActionsPortalFromPath,
  oaApi, setOperationsActionsPortalScope, CATEGORIES, CATEGORY_LABEL, PRIORITIES, PRIORITY_LABEL,
} from "@/lib/oa";

export default function OperationsActionNew() {
  usePageTitle("New Operations Action · MASCI");
  const { t } = useT();
  const nav = useNavigate();
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("truck_down");
  const [priority, setPriority] = useState("normal");
  const [jobNumber, setJobNumber] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [owner, setOwner] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  React.useEffect(() => {
    setOperationsActionsPortalScope(inferOperationsActionsPortalFromPath(document.referrer || window.location.pathname));
  }, []);

  const submit = async (e) => {
    e?.preventDefault?.();
    if (!title.trim()) {
      toast.error(t("Title is required."));
      return;
    }
    setSubmitting(true);
    try {
      const r = await oaApi.create({
        title: title.trim(),
        category, priority,
        job_number: jobNumber.trim() || null,
        location: location.trim() || null,
        description: description.trim(),
        due_date: dueDate || null,
        owner: owner ? { directory: owner.directory, id: owner.id, name: owner.name, email: owner.email } : null,
      });
      toast.success(`${r.data.oa_number} ${t("created.")}`);
      nav(`/operations-actions/${r.data.id}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not save. Try again."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen blueprint-bg pb-12" data-testid="oa-new-root">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-indigo-500">
        <div className="max-w-3xl mx-auto px-4 sm:px-8 py-3 flex items-center gap-3">
          <Link to="/" className="text-white hover:text-indigo-200 text-xs sm:text-sm font-bold" data-testid="oa-new-nav-home"><Home className="w-4 h-4 sm:mr-1 inline" /><span className="hidden sm:inline">Home</span></Link>
          <button onClick={() => nav(-1)} className="text-white hover:text-indigo-200 text-xs sm:text-sm font-bold" data-testid="oa-new-nav-back"><ArrowLeft className="w-4 h-4 sm:mr-1 inline" /><span className="hidden sm:inline">Back</span></button>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <div className="flex-1" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-8 py-6">
        <div className="font-mono text-xs uppercase tracking-[0.22em] text-indigo-700 font-bold">OA-1 · NEW</div>
        <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight mt-1 mb-3">{t("Create Action")}</h1>

        {/* Mandatory coaching */}
        <CoachingPanel compact className="mb-5" />

        <form onSubmit={submit} className="bg-white border border-slate-200 rounded-md p-4 space-y-4" data-testid="oa-new-form">
          <Field label={t("Title")} required testid="oa-field-title">
            <input
              type="text" value={title} onChange={(e) => setTitle(e.target.value)}
              required maxLength={120}
              placeholder="Truck 142 down at JOB-2024-188"
              className="w-full px-3 py-2 border border-slate-300 rounded text-base"
              data-testid="oa-input-title"
              autoFocus
            />
          </Field>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label={t("Category")} required testid="oa-field-category">
              <select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded text-base" data-testid="oa-input-category">
                {CATEGORIES.map((c) => (<option key={c} value={c}>{t(CATEGORY_LABEL[c])}</option>))}
              </select>
            </Field>
            <Field label={t("Priority")} required testid="oa-field-priority">
              <select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded text-base" data-testid="oa-input-priority">
                {PRIORITIES.map((p) => (<option key={p} value={p}>{t(PRIORITY_LABEL[p])}</option>))}
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label={t("Job Number")} testid="oa-field-job">
              <input type="text" value={jobNumber} onChange={(e) => setJobNumber(e.target.value)} placeholder="JOB-2024-188" className="w-full px-3 py-2 border border-slate-300 rounded text-base font-mono" data-testid="oa-input-job" />
            </Field>
            <Field label={t("Location")} testid="oa-field-location">
              <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Site / yard / plant" className="w-full px-3 py-2 border border-slate-300 rounded text-base" data-testid="oa-input-location" />
            </Field>
          </div>

          <Field label={t("Description")} testid="oa-field-description">
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} maxLength={4000} className="w-full px-3 py-2 border border-slate-300 rounded text-base" data-testid="oa-input-description" />
          </Field>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label={t("Due Date")} testid="oa-field-due">
              <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded text-base" data-testid="oa-input-due" />
            </Field>
            <Field label={t("Owner")} testid="oa-field-owner">
              <OwnerPicker value={owner} onChange={setOwner} />
            </Field>
          </div>

          <div className="flex items-center justify-between gap-3 pt-2 border-t border-slate-100">
            <button type="button" onClick={() => nav(-1)} className="px-3 py-2 text-sm font-bold uppercase tracking-wide text-slate-600 hover:text-slate-900" data-testid="oa-new-cancel">
              {t("Cancel")}
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold uppercase tracking-wide disabled:opacity-50"
              data-testid="oa-new-submit"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {t("Save")}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

function Field({ label, required, children, testid }) {
  return (
    <label className="block" data-testid={testid}>
      <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-600 font-bold">
        {label} {required ? <span className="text-rose-600">*</span> : null}
      </span>
      <div className="mt-1">{children}</div>
    </label>
  );
}
