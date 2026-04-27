import React, { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, FileText, Search, Download, Lock } from "lucide-react";
import { Input } from "@/components/ui/input";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { JOBS } from "@/lib/jobLibrary";
import { api } from "@/lib/api";

const REACT_APP_BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function JhaPlansHub() {
  const { t } = useT();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/job-hazard-plans");
        if (alive) setPlans(r.data || []);
      } catch {
        if (alive) setPlans([]);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const planByNumber = useMemo(() => {
    const m = {};
    for (const p of plans) m[p.project_number] = p;
    return m;
  }, [plans]);

  const filteredJobs = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return JOBS;
    return JOBS.filter(
      (j) =>
        j.project_number.toLowerCase().includes(term) ||
        j.project_name.toLowerCase().includes(term) ||
        (j.location || "").toLowerCase().includes(term)
    );
  }, [q]);

  const uploadedCount = plans.length;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link
            to="/"
            className="inline-flex items-center text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="back-link"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Hub
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
        <div className="mb-6">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
            {t("Job Hazard Plans")}
          </span>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
            {t("Pick your job to view its Hazard Plan")}
          </h1>
          <p className="text-slate-600 text-sm mt-2">
            {t(
              "Each MASCI job has its own Job Hazard Plan PDF. Open your job and read it before crew breaks ground. If your job has no plan yet, get with your PM."
            )}
          </p>
        </div>

        <div className="relative mb-5">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("Search by job number, name, or location…")}
            className="h-12 pl-9 border-2 border-slate-300"
            data-testid="jha-search"
          />
        </div>

        {!loading && (
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-3">
            {uploadedCount} of {JOBS.length} jobs have plans uploaded
          </p>
        )}

        <ul className="bg-white border-2 border-slate-300 rounded-md divide-y-2 divide-slate-100 overflow-hidden">
          {filteredJobs.map((job) => {
            const plan = planByNumber[job.project_number];
            const fileUrl = plan
              ? `${REACT_APP_BACKEND_URL}/api/job-hazard-plans/${encodeURIComponent(job.project_number)}/file`
              : null;
            return (
              <li
                key={job.project_number}
                className={`p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-3 ${
                  plan ? "" : "bg-slate-50"
                }`}
                data-testid={`jha-row-${job.project_number}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="font-display font-bold text-slate-900 truncate">
                    {job.project_number} · {job.project_name}
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5 truncate">
                    {job.location}
                  </div>
                  {plan && (
                    <div className="text-xs text-slate-500 mt-1 italic">
                      {t("Uploaded")} {new Date(plan.uploaded_at).toLocaleDateString()} · {plan.filename}
                    </div>
                  )}
                </div>
                {plan ? (
                  <a
                    href={fileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center h-10 px-4 rounded-md bg-red-700 hover:bg-red-800 text-white font-bold text-sm uppercase tracking-wide"
                    data-testid={`view-plan-${job.project_number}`}
                  >
                    <FileText className="w-4 h-4 mr-1" /> {t("View Plan")}
                  </a>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-[10px] uppercase tracking-[0.15em] font-bold bg-amber-50 text-amber-800 border border-amber-300">
                    <Lock className="w-3 h-3" /> {t("Not uploaded yet")}
                  </span>
                )}
              </li>
            );
          })}
          {filteredJobs.length === 0 && (
            <li className="p-8 text-center text-slate-500 italic">
              {t("No job matches your search.")}
            </li>
          )}
        </ul>

        <div className="mt-8 bg-amber-50 border-2 border-amber-300 rounded-md p-4 text-sm text-amber-900 flex items-start gap-3">
          <Download className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <b>{t("Download for offline use")}.</b> {t("On your phone, hold")} <b>{t("View Plan")}</b> &gt; <b>{t("Save to Files / Downloads")}</b> {t("to read it where there's no service.")}
          </div>
        </div>
      </main>
    </div>
  );
}
