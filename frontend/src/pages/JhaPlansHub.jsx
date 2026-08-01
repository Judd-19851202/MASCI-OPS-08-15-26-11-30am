import React, { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  Search,
  Download,
  Lock,
  ChevronDown,
  ChevronRight,
  ShieldAlert,
  CheckCircle2,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { JhaAcknowledgeButton } from "@/components/JhaAcknowledgeButton";
import { OperationalStatusBadge } from "@/components/public/OperationalStatusBadge";
import { useT } from "@/lib/i18n";
import { JOB_LIBRARY as JOBS } from "@/lib/jobLibrary";
import { api } from "@/lib/api";
import { PortalShell } from "@/design-system/PortalShell";
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
    <PortalShell
      portalName="MASCI"
      portalRole="Field Safety"
      pageTitle={t("Job Hazard Plans")}
      subtitle={t("Search by job and open the latest hazard-plan files before work starts.")}
      homeHref="/"
      backHref="/"
      showBack={false}
      showSearch={false}
      showNotifications={false}
      showPortalSwitcher={false}
      showSignOut={false}
      showPageHeader={false}
    >
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10 overflow-x-hidden">
        <div className="wp17-public-hero mb-6 overflow-hidden max-w-full" data-testid="jha-summary">
          <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr),19rem] lg:items-start">
            <div className="min-w-0 max-w-full">
              <span className="wp17-kicker text-red-700">{t("Field Safety · Pre-task access")}</span>
              <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900 mt-2 break-words max-w-[12ch] sm:max-w-none">
                {t("Open the latest hazard plan before work starts.")}
              </h1>
              <p className="text-slate-600 text-sm sm:text-base mt-3 max-w-3xl break-words">
                {t("Search by project number, project name, or location. Open the current plan, download it for offline use, and acknowledge the file you actually reviewed.")}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <OperationalStatusBadge tone="red" testId="jha-badge-live-files">{t("Live file library")}</OperationalStatusBadge>
                <OperationalStatusBadge tone="amber" testId="jha-badge-crew-read">{t("Crew read-before-work")}</OperationalStatusBadge>
                <OperationalStatusBadge tone="cyan" testId="jha-badge-ack">{t("Acknowledgement tracked")}</OperationalStatusBadge>
              </div>
            </div>
            <div className="wp17-panel p-4 min-w-0 max-w-full" data-testid="jha-attention-panel">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-red-700 font-bold mb-2">{t("What needs attention now")}</div>
              <div className="text-sm text-slate-700 leading-6">
                {t("If your job has no uploaded plan, stop and get with your PM before the crew breaks ground. If it has changed, download the newest file and acknowledge that exact revision.")}
              </div>
            </div>
          </div>
        </div>

        <div
          className="mb-5 rounded-[1.25rem] border border-slate-200 bg-white px-4 py-3 flex flex-wrap items-center gap-2 text-xs shadow-[0_12px_28px_rgba(15,23,42,0.04)] max-w-full overflow-hidden"
          data-testid="jha-ack-identity-strip"
        >
          <span className="font-mono uppercase tracking-[0.18em] text-slate-500">
            {t("Signing as")}:
          </span>
          {ackEmail ? (
            <>
              <b className="text-slate-900 break-all">{ackEmail}</b>
              <OperationalStatusBadge tone="emerald" testId="jha-ack-count">
                {ackedFileIds.size} {t("plans acknowledged")}
              </OperationalStatusBadge>
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
            <span className="text-slate-600">{t("Your work email becomes the acknowledgement signature when you confirm a plan below.")}</span>
          )}
        </div>

        <div className="wp17-panel p-3 mb-5 relative max-w-full overflow-hidden">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("Search by job number, name, or location…")}
            className="h-12 pl-9 border-slate-300 w-full max-w-full"
            data-testid="jha-search"
          />
        </div>

        {!loading && (
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-3">
            {uploadedCount} {t("of")} {JOBS.length} {t("jobs have plans uploaded")}
          </p>
        )}

        <ul className="bg-white border border-slate-200 rounded-[1.5rem] divide-y divide-slate-100 overflow-hidden shadow-[0_16px_40px_rgba(15,23,42,0.05)]">
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
                    <div className="font-display font-bold text-slate-900 break-words pr-2">
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
                    <span className="inline-flex items-center gap-2 h-10 px-4 rounded-full bg-red-700 text-white font-bold text-sm uppercase tracking-wide">
                      <FileText className="w-4 h-4" />
                      {t("View Plans")}
                      {isOpen ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-mono text-[10px] uppercase tracking-[0.15em] font-bold bg-amber-50 text-amber-800 border border-amber-300">
                      <Lock className="w-3 h-3" /> {t("Not uploaded yet")}
                    </span>
                  )}
                </button>
                {hasFiles && isOpen && (
                  <ul className="bg-slate-50 border-t border-slate-100 divide-y divide-slate-200">
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
                            className="inline-flex items-center justify-center h-10 px-4 rounded-full bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm uppercase tracking-wide"
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
            <li className="p-8 text-center text-slate-500" data-testid="jha-empty-state">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 text-slate-500 mb-3">
                <Search className="w-5 h-5" />
              </div>
              <div className="font-display font-bold text-slate-900">{t("No job matches your search.")}</div>
              <div className="text-sm text-slate-500 mt-1">{t("Try the project number, a shorter job name, or the city/location label.")}</div>
            </li>
          )}
        </ul>

        <div className="mt-8 rounded-[1.25rem] bg-amber-50 border border-amber-300 p-4 text-sm text-amber-900 flex items-start gap-3" data-testid="jha-offline-tip">
          <ShieldAlert className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <b>{t("Download before you lose signal")}.</b>{" "}
            {t("Save the file to your device before the crew moves into low-service areas so the current plan is still readable at the point of work.")}
          </div>
        </div>
      </div>
    </PortalShell>
  );
}
