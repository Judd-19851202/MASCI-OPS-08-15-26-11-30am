import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  FileText,
  FileSpreadsheet,
  FileType,
  FileArchive,
  FileImage,
  File as FileIcon,
  Upload,
  Trash2,
  Loader2,
  ChevronDown,
  ChevronRight,
  Briefcase,
  Folder,
  Search,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PortalShell } from "@/design-system";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import SafetySideNavV2 from "@/components/safety/sidebar/SafetySideNavV2";
import EmptyState from "@/components/EmptyState";
import { api } from "@/lib/api";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";
import { buildWave3AdminHeaders } from "@/lib/wave3AdminHeaders";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const REACT_APP_BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function SurfaceSection({ eyebrow, title, description, actions = null, children, testId }) {
  return (
    <section className="wp17-panel p-5 sm:p-6" data-testid={testId}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          {eyebrow ? <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">{eyebrow}</div> : null}
          <h2 className="mt-2 font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">{title}</h2>
          {description ? <p className="mt-2 max-w-3xl text-sm sm:text-base leading-6 text-slate-600">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2 lg:justify-end">{actions}</div> : null}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function MetricChip({ label, value, tone = "slate", testId }) {
  const toneClass = {
    red: "border-red-200 bg-red-50 text-red-900",
    emerald: "border-emerald-200 bg-emerald-50 text-emerald-900",
    slate: "border-slate-200 bg-white text-slate-800",
  }[tone];

  return (
    <div className={`rounded-full border px-3 py-1.5 ${toneClass}`} data-testid={testId}>
      <div className="font-mono text-[9px] uppercase tracking-[0.22em] font-bold opacity-70">{label}</div>
      <div className="mt-0.5 text-sm font-semibold">{value}</div>
    </div>
  );
}

/**
 * JhaPlansAdmin — multi-file Job Hazard library per project.
 *
 *   • Accepts PDF / Word / Excel / ZIP / images / CAD / video.
 *   • Per-job folder view with collapsible groups.
 *   • Drag-drop OR click "+ Add file" inside any project's row.
 *   • Files >8 MB stream straight to disk on the backend; smaller ones
 *     stay inline in Mongo for instant download.
 *
 * Backend:
 *   GET    /api/job-hazard-files                            (admin — grouped)
 *   POST   /api/job-hazard-files                            (multipart)
 *   GET    /api/job-hazard-files/{file_id}/download         (stream)
 *   DELETE /api/job-hazard-files/{file_id}                  (admin)
 */
function fileIconFor(filename, contentType) {
  const ext = (filename || "").split(".").pop()?.toLowerCase() || "";
  if (ext === "pdf" || contentType === "application/pdf")
    return <FileText className="w-4 h-4 text-red-600" />;
  if (["xlsx", "xls", "csv"].includes(ext))
    return <FileSpreadsheet className="w-4 h-4 text-emerald-700" />;
  if (["docx", "doc", "rtf", "odt", "txt", "md"].includes(ext))
    return <FileType className="w-4 h-4 text-blue-700" />;
  if (["zip", "7z", "tar", "gz"].includes(ext))
    return <FileArchive className="w-4 h-4 text-amber-700" />;
  if (
    ["png", "jpg", "jpeg", "heic", "heif", "webp", "gif"].includes(ext) ||
    (contentType || "").startsWith("image/")
  )
    return <FileImage className="w-4 h-4 text-purple-700" />;
  return <FileIcon className="w-4 h-4 text-slate-500" />;
}

function bytesPretty(n) {
  if (!n && n !== 0) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export default function JhaPlansAdmin() {
  const [groups, setGroups] = useState([]);   // [{project_number, files:[]}]
  const [jobs, setJobs] = useState([]);       // jobs_master for project picker
  const [loading, setLoading] = useState(true);
  const [busyJob, setBusyJob] = useState(null);
  const [openMap, setOpenMap] = useState({});
  const [filter, setFilter] = useState("");
  const [newProject, setNewProject] = useState("");
  const [error, setError] = useState("");
  const fileInputs = useRef({});
  // TRACK 14.0-DISCOVERABILITY · Wave B — when this page is mounted in
  // the Safety portal shell (/safety-portal/jha-plans), the safety
  // token cannot satisfy /api/job-hazard-files (admin-gated). Fall
  // back to the public-grouped endpoint, which is read-only and
  // already permission-safe (returns no file_data). Admin / PM keep
  // the authenticated endpoint with full upload capability.
  const isSafetyContext = typeof window !== "undefined"
    && window.location.pathname.startsWith("/safety-portal/");
  const adminRoute = typeof window !== "undefined"
    && window.location.pathname.startsWith("/admin/");
  const adminAuth = useMemo(
    () => (adminRoute ? { headers: buildWave3AdminHeaders() } : undefined),
    [adminRoute]
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [r, j] = await Promise.all([
        isSafetyContext
          ? api.get("/job-hazard-files/public/grouped").then((res) => ({ data: { projects: res.data } }))
          : api.get("/job-hazard-files", adminAuth),
        api.get("/jobs", adminAuth).catch(() => ({ data: { items: [] } })),
      ]);
      setGroups(r.data?.projects || []);
      setJobs(j.data?.items || []);
    } catch (e) {
      const message = operationalError(e,
        "JHP library temporarily unavailable. Try again in a moment.",
        "Your admin session expired. Please sign in again.");
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [adminAuth, isSafetyContext]);
  useEffect(() => {
    refresh();
  }, [refresh]);

  /** Map project_number → {project_name, location, client} from jobs_master. */
  const jobByNumber = useMemo(() => {
    const m = {};
    for (const j of jobs) {
      if (j.project_number) m[j.project_number] = j;
    }
    return m;
  }, [jobs]);

  /** Combined view: every job + any files attached. Even jobs with 0 files
   * appear so the admin sees them and can attach. */
  const rows = useMemo(() => {
    const filesByPn = {};
    for (const g of groups) filesByPn[g.project_number] = g.files;
    const all = jobs.map((j) => ({
      project_number: j.project_number,
      project_name: j.project_name,
      location: j.location || "",
      client: j.client || "",
      project_manager: j.project_manager || "",
      files: filesByPn[j.project_number] || [],
    }));
    // Append any orphan project_numbers (files exist but job is gone)
    for (const g of groups) {
      if (!jobByNumber[g.project_number]) {
        all.push({
          project_number: g.project_number,
          project_name: "(orphan — job not in master list)",
          location: "",
          client: "",
          project_manager: "",
          files: g.files,
        });
      }
    }
    // Filter
    const f = filter.trim().toLowerCase();
    if (!f) return all;
    return all.filter(
      (r) =>
        r.project_number.toLowerCase().includes(f) ||
        (r.project_name || "").toLowerCase().includes(f) ||
        (r.location || "").toLowerCase().includes(f) ||
        (r.client || "").toLowerCase().includes(f) ||
        r.files.some((x) => (x.filename || "").toLowerCase().includes(f))
    );
  }, [groups, jobs, jobByNumber, filter]);

  const totalFiles = useMemo(
    () => rows.reduce((sum, row) => sum + row.files.length, 0),
    [rows]
  );

  const toggleOpen = (pn) =>
    setOpenMap((m) => ({ ...m, [pn]: !m[pn] }));

  const onPickFile = (pn, e) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(pn, file);
    if (fileInputs.current[pn]) fileInputs.current[pn].value = "";
  };

  const onDrop = (pn, e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer?.files?.[0];
    if (file) uploadFile(pn, file);
  };

  const uploadFile = async (project_number, file) => {
    setBusyJob(project_number);
    try {
      const fd = new FormData();
      fd.append("project_number", project_number);
      fd.append("file", file, file.name);
      await api.post("/job-hazard-files", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        // Big files take time — give it 5 min just in case (250 MB cap).
        timeout: 5 * 60 * 1000,
      });
      toast.success(`Uploaded ${file.name}`);
      await refresh();
      setOpenMap((m) => ({ ...m, [project_number]: true }));
    } catch (err) {
      toast.error(operationalError(err,
        "Upload temporarily unavailable. Try again in a moment.",
        "Your admin session expired. Please sign in again."));
    } finally {
      setBusyJob(null);
    }
  };

  const removeFile = async (file) => {
    if (
      !window.confirm(
        `Delete ${file.filename}?\n\nThis cannot be undone.`
      )
    )
      return;
    setBusyJob(file.project_number);
    try {
      await api.delete(`/job-hazard-files/${file.id}`);
      toast.success(`Deleted ${file.filename}`);
      await refresh();
    } catch (err) {
      toast.error(operationalError(err,
        "Delete temporarily unavailable. Try again in a moment.",
        "Your admin session expired. Please sign in again."));
    } finally {
      setBusyJob(null);
    }
  };

  const downloadHref = (id) =>
    `${REACT_APP_BACKEND_URL}/api/job-hazard-files/${id}/download`;

  const content = (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe print:hidden" />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6" data-testid="jha-admin-page">
        <section className="wp17-public-hero" data-testid="jha-admin-hero">
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr),19rem] xl:items-start">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">Safety compliance · document control</div>
              <h1 className="mt-3 font-display text-4xl sm:text-5xl font-black tracking-tight text-slate-900">JHP Plans &amp; Files</h1>
              <p className="mt-3 max-w-3xl text-sm sm:text-base leading-6 text-slate-600">
                Upload, organize, and retrieve hazard-plan files by project without leaving the MASCI project workspace.
                Every attachment stays in a managed project folder for field, admin, and review follow-through.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <MetricChip label="Visible projects" value={rows.length} tone="red" testId="jha-visible-projects-chip" />
                <MetricChip label="Visible files" value={totalFiles} tone="emerald" testId="jha-visible-files-chip" />
                <MetricChip label="Master jobs" value={jobs.length} testId="jha-master-jobs-chip" />
              </div>
            </div>
            <div className="wp17-panel p-4" data-testid="jha-admin-attention-panel">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-red-700 font-bold mb-2">Operator standard</div>
              <div className="space-y-3 text-sm text-slate-700 leading-6">
                <div className="flex gap-2">
                  <ShieldCheck className="w-4 h-4 mt-0.5 shrink-0 text-emerald-700" />
                  <span>Attach the project-specific JHP before field execution or external review handoff.</span>
                </div>
                <div className="flex gap-2">
                  <Folder className="w-4 h-4 mt-0.5 shrink-0 text-slate-600" />
                  <span>Use unlisted project upload only when the job has not yet reached the master register.</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {error ? (
          <section className="wp17-panel border border-amber-200 bg-amber-50 p-4 sm:p-5" data-testid="jha-admin-error-state">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-start gap-3 text-amber-900">
                <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0" />
                <div>
                  <div className="font-display text-lg font-black">Library temporarily unavailable</div>
                  <p className="mt-1 text-sm leading-6">{error}</p>
                </div>
              </div>
              <Button
                type="button"
                variant="outline"
                onClick={refresh}
                className="h-11 border-amber-300 bg-white text-amber-900 hover:bg-amber-100"
                data-testid="jha-admin-error-retry"
              >
                Retry
              </Button>
            </div>
          </section>
        ) : null}

        <SurfaceSection
          eyebrow="Find the right folder fast"
          title="Project library filters"
          description="Search by project number, name, location, client, or filename before opening a folder or uploading a replacement file."
          actions={(
            <Button
              variant="outline"
              onClick={refresh}
              disabled={loading}
              className="h-11 border-slate-300 bg-white text-slate-900 hover:border-red-500 hover:text-red-700"
              data-testid="jha-refresh"
            >
              {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
              Refresh
            </Button>
          )}
          testId="jha-filter-section"
        >
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr),20rem] xl:items-start">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <Input
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Filter by project #, name, location, or filename…"
                className="h-11 pl-10 border-slate-300 bg-white"
                data-testid="jha-filter"
              />
            </div>

            <details className="rounded-[1.25rem] border border-slate-200 bg-slate-50/90 p-4" data-testid="jha-new-project-panel">
              <summary className="cursor-pointer font-mono text-[11px] uppercase tracking-[0.22em] text-slate-700">
                Upload to a new or unlisted project
              </summary>
              <div className="mt-4 grid gap-3 sm:grid-cols-[minmax(0,1fr),auto] sm:items-end">
                <div>
                  <Label className="font-mono text-[9px] uppercase tracking-[0.22em] text-slate-600">
                    Project #
                  </Label>
                  <Input
                    value={newProject}
                    onChange={(e) => setNewProject(e.target.value)}
                    placeholder="26-99 or any custom number"
                    className="mt-2 h-10 border-slate-300 bg-white"
                    data-testid="jha-new-project-input"
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={() => {
                    if (!newProject.trim()) {
                      toast.error("Enter a project number first");
                      return;
                    }
                    fileInputs.current[`__new__${newProject.trim()}`]?.click();
                  }}
                  className="h-10 text-xs font-mono uppercase tracking-[0.18em]"
                  data-testid="jha-new-project-pick-file"
                >
                  Pick file
                </Button>
                <input
                  type="file"
                  ref={(el) => {
                    if (newProject.trim()) {
                      fileInputs.current[`__new__${newProject.trim()}`] = el;
                    }
                  }}
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (!file || !newProject.trim()) return;
                    uploadFile(newProject.trim(), file);
                    setNewProject("");
                    e.target.value = "";
                  }}
                  data-testid="jha-new-project-hidden-input"
                />
              </div>
            </details>
          </div>
        </SurfaceSection>

        <SurfaceSection
          eyebrow="Browse · upload · replace · delete"
          title="Project folders"
          description="Open a folder to review attached files, add a new revision, or delete obsolete material. Drag-and-drop is enabled on every project row."
          testId="jha-project-folders-section"
        >
          {loading ? (
            <div className="flex min-h-[14rem] items-center justify-center text-slate-500" data-testid="jha-loading-state">
              <Loader2 className="mr-2 h-6 w-6 animate-spin" /> Loading library…
            </div>
          ) : rows.length === 0 ? (
            <EmptyState
              title="No matching jobs"
              message="Adjust your filter or upload to a new project number to seed the first folder."
              icon={Folder}
              data-testid="jha-empty-state"
            />
          ) : (
            <div className="space-y-3">
              {rows.map((row) => {
                const isOpen = !!openMap[row.project_number];
                const isBusy = busyJob === row.project_number;
                return (
                  <div
                    key={row.project_number}
                    className="overflow-hidden rounded-[1.35rem] border border-slate-200 bg-white shadow-[0_10px_24px_rgba(15,23,42,0.05)]"
                    data-testid={`jha-job-${row.project_number}`}
                    onDragOver={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                    }}
                    onDrop={(e) => onDrop(row.project_number, e)}
                  >
                    <button
                      type="button"
                      onClick={() => toggleOpen(row.project_number)}
                      className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50"
                      data-testid={`jha-toggle-${row.project_number}`}
                    >
                      {isOpen ? (
                        <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-500 shrink-0" />
                      )}
                      <span className="inline-flex min-w-[4.25rem] justify-center rounded-full bg-red-700 px-2.5 py-1 text-[11px] font-bold font-mono text-white shrink-0">
                        {row.project_number}
                      </span>
                      <Briefcase className="w-4 h-4 text-slate-400 shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-semibold text-slate-900">{row.project_name}</div>
                        <div className="mt-0.5 truncate text-xs text-slate-500">
                          {[row.location, row.client, row.project_manager].filter(Boolean).join(" · ") || "Metadata pending"}
                        </div>
                      </div>
                      <span className="ml-auto inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600 shrink-0">
                        <Folder className="w-3.5 h-3.5" />
                        {row.files.length}
                      </span>
                    </button>

                    {isOpen ? (
                      <div className="border-t border-slate-200 bg-slate-50/80 px-4 py-4" data-testid={`jha-open-panel-${row.project_number}`}>
                        {row.files.length === 0 ? (
                          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-4 text-sm text-slate-500" data-testid={`jha-empty-folder-${row.project_number}`}>
                            No files yet — drop one here or click <strong>+ Add file</strong> to create the first project record.
                          </div>
                        ) : null}

                        <ul className="space-y-2">
                          {row.files.map((f) => (
                            <li
                              key={f.id}
                              className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2.5"
                              data-testid={`jha-file-${f.id}`}
                            >
                              {fileIconFor(f.filename, f.content_type)}
                              <a
                                href={downloadHref(f.id)}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="min-w-0 flex-1 truncate text-sm font-medium text-slate-800 hover:text-red-700 hover:underline"
                                data-testid={`jha-file-link-${f.id}`}
                              >
                                {f.filename}
                              </a>
                              <span className="text-[10px] font-mono text-slate-500 shrink-0">
                                {bytesPretty(f.file_size)}
                                {f.storage === "disk" ? " · disk" : ""}
                              </span>
                              <span className="text-[10px] text-slate-400 shrink-0 hidden sm:inline">
                                {f.uploaded_at ? formatPlatformDate(f.uploaded_at) : ""}
                              </span>
                              <button
                                type="button"
                                onClick={() => removeFile({ ...f, project_number: row.project_number })}
                                className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-transparent text-slate-400 transition-colors hover:border-red-100 hover:bg-red-50 hover:text-red-600"
                                title="Delete"
                                data-testid={`jha-file-delete-${f.id}`}
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </li>
                          ))}
                        </ul>

                        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                          <div className="flex flex-wrap items-center gap-2">
                            <input
                              type="file"
                              ref={(el) => (fileInputs.current[row.project_number] = el)}
                              className="hidden"
                              onChange={(e) => onPickFile(row.project_number, e)}
                              data-testid={`jha-file-input-${row.project_number}`}
                            />
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={isBusy}
                              onClick={() => fileInputs.current[row.project_number]?.click()}
                              className="h-9 text-xs font-mono uppercase tracking-[0.18em]"
                              data-testid={`jha-add-${row.project_number}`}
                            >
                              {isBusy ? (
                                <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                              ) : (
                                <Upload className="w-3.5 h-3.5 mr-1" />
                              )}
                              Add file
                            </Button>
                          </div>
                          <span className="text-[10px] text-slate-500">
                            PDF, Word, Excel, ZIP, images, CAD, video — up to 250 MB
                          </span>
                        </div>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}
        </SurfaceSection>
      </main>
    </div>
  );

  if (adminRoute) {
    return (
      <AdminRouteShell
        pageTitle="JHP Plans & Files"
        subtitle="Project hazard plans · attached files"
        portalRole="Admin · JHP Files"
        crumbs={[
          { label: "Admin OS" },
          { label: "Safety & Compliance" },
          { label: "JHA / JHP Plans" },
        ]}
        showShellHeader={false}
        showBreadcrumbs={false}
        contentClassName="px-0 py-0"
        testId="admin-jha-plans-shell"
      >
        {content}
      </AdminRouteShell>
    );
  }

  return (
    <PortalShell
      portalName="MASCI" portalRole="Safety Portal · Job Hazard Library"
      pageTitle="JHP Plans & Files"
      subtitle="Project hazard plans · attached files"
      sideNav={<SafetySideNavV2 />}
      showPageHeader={false}
    >
      {content}
    </PortalShell>
  );
}
