import React, { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  FileText,
  Search,
  Download,
  Lock,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { HelpTipBlock } from "@/components/HelpTip";
import { JhaAcknowledgeButton } from "@/components/JhaAcknowledgeButton";
import { useT } from "@/lib/i18n";
import { JOB_LIBRARY as JOBS } from "@/lib/jobLibrary";
import { api } from "@/lib/api";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

// JhaPlansHub now reads from the NEW multi-file collection
// (/api/job-hazard-files, backed by `job_hazard_files`) so the public
// /jha page surfaces every file an admin uploaded for a job — not just
// the single-file legacy `job_hazard_plans` doc. Each row expands to
// list every file; users tap any file to download it.
const REACT_APP_BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function JhaPlansHub() {
  const { t } = useT();
  // groups: [{ project_number, files: [{id, filename, uploaded_at, size_bytes, notes, uploaded_by}] }]
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [expanded, setExpanded] = useState(() => new Set());

  // FOCP Release 2 · TR-0001 — employee acknowledgement state.
  // Remembered email (localStorage) lets the page surface a per-file
  // ✓ "Acknowledged" pill for files this employee has already signed,
  // and pre-fills the ack modal.
  const [ackEmail, setAckEmail] = useState(() => {
    try {
      return window.localStorage.getItem("masci.jha.email") || "";
    } catch {
      return "";
    }
  });
  const [ackedFileIds, setAckedFileIds] = useState(() => new Set());

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/job-hazard-files/public/grouped");
        if (alive) setGroups(Array.isArray(r.data) ? r.data : []);
      } catch {
        if (alive) setGroups([]);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  // Refresh acked-files set whenever the remembered email changes.
  useEffect(() => {
    let alive = true;
    const e = (ackEmail || "").trim().toLowerCase();
    if (!e) {
      setAckedFileIds(new Set());
      return () => {
        alive = false;
      };
    }
    (async () => {
      try {
        const r = await api.get("/jha-acknowledgements/me", {
          params: { employee_email: e },
        });
        if (!alive) return;
        const ids = new Set();
        for (const row of r.data?.items || []) {
          if (row?.jha_file_id) ids.add(row.jha_file_id);
        }
        setAckedFileIds(ids);
      } catch {
        if (alive) setAckedFileIds(new Set());
      }
    })();
    return () => {
      alive = false;
    };
  }, [ackEmail]);

  const filesByProject = useMemo(() => {
    const m = {};
    for (const g of groups) {
      if (g && g.project_number) m[g.project_number] = g.files || [];
    }
    return m;
  }, [groups]);

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

  const uploadedCount = groups.filter((g) => (g.files || []).length > 0).length;

  const toggleExpand = (pn) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(pn)) next.delete(pn);
      else next.add(pn);
      return next;
    });
  };

  const fileHref = (fileId) =>
    `${REACT_APP_BACKEND_URL}/api/job-hazard-files/${fileId}/download`;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <Link
            to="/"
            className="inline-flex items-center min-h-[44px] -ml-2 px-2 text-white hover:text-red-300 text-sm font-bold uppercase tracking-wide"
            data-testid="back-link"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> {t("Home")}
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

        {/* iter275 · page-root coaching · canonical 4 kinds */}
        <HelpTipBlock formKey="jha" className="mb-4" showCounter />
        {/* iter275 · poster coaching · how the JHA reaches the crew */}
        <HelpTipBlock formKey="jha.poster" className="mb-4" />

        {/* FOCP Release 2 · TR-0001 — identity strip for acknowledgement.
            Shows the remembered email so the employee knows which
            identity is being used to mark plans as acknowledged. */}
        <div
          className="mb-5 rounded-md border-2 border-slate-200 bg-white px-3 py-2 flex flex-wrap items-center gap-2 text-xs"
          data-testid="jha-ack-identity-strip"
        >
          <span className="font-mono uppercase tracking-[0.18em] text-slate-500">
            {t("Signing as")}:
          </span>
          {ackEmail ? (
            <>
              <b className="text-slate-900">{ackEmail}</b>
              <span className="text-slate-400">·</span>
              <span className="text-slate-600">
                {ackedFileIds.size} {t("plans acknowledged")}
              </span>
              <button
                type="button"
                onClick={() => {
                  try {
                    window.localStorage.removeItem("masci.jha.email");
                  } catch {
                    /* noop */
                  }
                  setAckEmail("");
                }}
                className="ml-auto text-amber-700 hover:text-amber-900 underline font-bold uppercase tracking-wide text-[10px]"
                data-testid="jha-ack-identity-clear"
              >
                {t("Not me — clear")}
              </button>
            </>
          ) : (
            <span className="text-slate-600 italic">
              {t("Acknowledge any plan below to begin — your work email is your signature key.")}
            </span>
          )}
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
            {uploadedCount} {t("of")} {JOBS.length} {t("jobs have plans uploaded")}
          </p>
        )}

        <ul className="bg-white border border-slate-200 rounded-md divide-y-2 divide-slate-100 overflow-hidden">
          {filteredJobs.map((job) => {
            const files = filesByProject[job.project_number] || [];
            const hasFiles = files.length > 0;
            const isOpen = expanded.has(job.project_number);
            return (
              <li
                key={job.project_number}
                className={hasFiles ? "" : "bg-slate-50"}
                data-testid={`jha-row-${job.project_number}`}
              >
                <button
                  type="button"
                  onClick={() => hasFiles && toggleExpand(job.project_number)}
                  className="w-full p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-3 text-left"
                  disabled={!hasFiles}
                >
                  <div className="flex-1 min-w-0">
                    <div className="font-display font-bold text-slate-900 truncate">
                      {job.project_number} · {job.project_name}
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5 truncate">
                      {job.location}
                    </div>
                    {hasFiles && (
                      <div className="text-xs text-slate-500 mt-1 italic">
                        {files.length}{" "}
                        {files.length === 1
                          ? t("file uploaded")
                          : t("files uploaded")}
                      </div>
                    )}
                  </div>
                  {hasFiles ? (
                    <span className="inline-flex items-center gap-2 h-10 px-4 rounded-md bg-red-700 text-white font-bold text-sm uppercase tracking-wide">
                      <FileText className="w-4 h-4" />
                      {t("View Plans")}
                      {isOpen ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-[10px] uppercase tracking-[0.15em] font-bold bg-amber-50 text-amber-800 border border-amber-300">
                      <Lock className="w-3 h-3" /> {t("Not uploaded yet")}
                    </span>
                  )}
                </button>
                {hasFiles && isOpen && (
                  <ul className="bg-slate-50 border-t-2 border-slate-100 divide-y divide-slate-200">
                    {files.map((f) => (
                      <li
                        key={f.id}
                        className="px-5 py-3 flex flex-col sm:flex-row sm:items-center gap-3"
                        data-testid={`jha-file-${f.id}`}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="font-mono text-sm text-slate-900 truncate">
                            {f.filename}
                          </div>
                          <div className="text-[11px] text-slate-500 mt-0.5">
                            {f.uploaded_at
                              ? formatPlatformDate(f.uploaded_at)
                              : ""}
                            {f.uploaded_by ? ` · ${f.uploaded_by}` : ""}
                            {f.notes ? ` · ${f.notes}` : ""}
                          </div>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <a
                            href={fileHref(f.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center justify-center h-10 px-4 rounded-md bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm uppercase tracking-wide"
                            data-testid={`download-${f.id}`}
                          >
                            <Download className="w-4 h-4 mr-1" />{" "}
                            {t("Download")}
                          </a>
                          <JhaAcknowledgeButton
                            projectNumber={job.project_number}
                            fileId={f.id}
                            filename={f.filename}
                            acked={ackedFileIds.has(f.id)}
                            defaultEmail={ackEmail}
                            onAcknowledged={(_ack, email) => {
                              setAckEmail(email);
                              setAckedFileIds((prev) => {
                                const n = new Set(prev);
                                n.add(f.id);
                                return n;
                              });
                            }}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
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
            <b>{t("Download for offline use")}.</b>{" "}
            {t("On your phone, hold")} <b>{t("Download")}</b> &gt;{" "}
            <b>{t("Save to Files / Downloads")}</b>{" "}
            {t("to read it where there's no service.")}
          </div>
        </div>
      </main>
    </div>
  );
}
