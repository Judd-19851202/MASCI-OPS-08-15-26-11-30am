import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { MasciLogo } from "@/components/MasciLogo";
import HubBackLink from "@/components/HubBackLink";
import { api } from "@/lib/api";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";

const REACT_APP_BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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
  const fileInputs = useRef({});

  const refresh = async () => {
    setLoading(true);
    try {
      const [r, j] = await Promise.all([
        api.get("/job-hazard-files"),
        api.get("/jobs"),
      ]);
      setGroups(r.data?.projects || []);
      setJobs(j.data?.items || []);
    } catch (e) {
      toast.error(operationalError(e,
        "JHP library temporarily unavailable. Try again in a moment.",
        "Your admin session expired. Please sign in again."));
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    refresh();
  }, []);

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

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b-2 border-slate-200 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3">
          <HubBackLink
            className="text-slate-600 hover:text-slate-900"
            testId="jha-back-link"
          />
          <MasciLogo className="h-6 w-auto" />
          <div className="flex-1">
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
              Job Hazard Library
            </div>
            <h1 className="font-display text-lg sm:text-xl font-black text-slate-900">
              JHP Plans &amp; Files
            </h1>
          </div>
        </div>
      </header>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-xl">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Filter by project #, name, location, or filename…"
              className="pl-9 h-10"
              data-testid="jha-filter"
            />
          </div>
          <Button
            variant="outline"
            onClick={refresh}
            disabled={loading}
            className="h-10"
            data-testid="jha-refresh"
          >
            {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            Refresh
          </Button>
        </div>

        {/* New project (orphan upload) */}
        <details className="border-2 border-slate-200 rounded p-4 bg-white">
          <summary className="font-mono text-[11px] uppercase tracking-wide text-slate-700 cursor-pointer">
            + Upload to a NEW / unlisted project number
          </summary>
          <div className="mt-3 grid sm:grid-cols-[1fr_auto] gap-2 items-end">
            <div>
              <Label className="font-mono text-[9px] uppercase tracking-wide text-slate-700">
                Project #
              </Label>
              <Input
                value={newProject}
                onChange={(e) => setNewProject(e.target.value)}
                placeholder="26-99 or any custom number"
                className="h-9 mt-1"
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
              className="h-9 text-xs font-mono uppercase"
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
            />
          </div>
        </details>

        {/* Per-project rows */}
        {loading ? (
          <div className="text-center py-12 text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin inline-block mr-2" />
            Loading library…
          </div>
        ) : rows.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            No matching jobs. Adjust your filter.
          </div>
        ) : (
          <div className="space-y-2">
            {rows.map((row) => {
              const isOpen = !!openMap[row.project_number];
              const isBusy = busyJob === row.project_number;
              return (
                <div
                  key={row.project_number}
                  className="border-2 border-slate-200 rounded bg-white"
                  data-testid={`jha-job-${row.project_number}`}
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                  }}
                  onDrop={(e) => onDrop(row.project_number, e)}
                >
                  {/* Header row */}
                  <button
                    type="button"
                    onClick={() => toggleOpen(row.project_number)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-slate-50"
                    data-testid={`jha-toggle-${row.project_number}`}
                  >
                    {isOpen ? (
                      <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-slate-500 shrink-0" />
                    )}
                    <span className="inline-block px-1.5 py-0.5 bg-red-700 text-white text-xs font-bold font-mono rounded shrink-0">
                      {row.project_number}
                    </span>
                    <Briefcase className="w-4 h-4 text-slate-400 shrink-0" />
                    <span className="font-medium text-sm text-slate-900 truncate">
                      {row.project_name}
                    </span>
                    <span className="text-xs text-slate-500 truncate hidden sm:inline">
                      · {row.location || "—"} · {row.client || "—"}
                    </span>
                    <span className="ml-auto inline-flex items-center gap-1.5 text-xs text-slate-500 shrink-0">
                      <Folder className="w-3.5 h-3.5" />
                      {row.files.length}
                    </span>
                  </button>

                  {/* Files list (expanded) */}
                  {isOpen && (
                    <div className="border-t border-slate-200 px-3 py-2 bg-slate-50">
                      {row.files.length === 0 && (
                        <p className="text-xs text-slate-500 py-1.5">
                          No files yet — drop one here or click <strong>+ Add file</strong>.
                        </p>
                      )}
                      <ul className="space-y-1.5">
                        {row.files.map((f) => (
                          <li
                            key={f.id}
                            className="flex items-center gap-2 px-2 py-1.5 bg-white rounded border border-slate-200"
                            data-testid={`jha-file-${f.id}`}
                          >
                            {fileIconFor(f.filename, f.content_type)}
                            <a
                              href={downloadHref(f.id)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex-1 truncate text-xs text-slate-800 hover:text-red-700 hover:underline font-medium"
                              data-testid={`jha-file-link-${f.id}`}
                            >
                              {f.filename}
                            </a>
                            <span className="text-[10px] font-mono text-slate-400 shrink-0">
                              {bytesPretty(f.file_size)}
                              {f.storage === "disk" ? " · disk" : ""}
                            </span>
                            <span className="text-[10px] text-slate-400 shrink-0 hidden sm:inline">
                              {f.uploaded_at
                                ? new Date(f.uploaded_at).toLocaleDateString()
                                : ""}
                            </span>
                            <button
                              type="button"
                              onClick={() =>
                                removeFile({ ...f, project_number: row.project_number })
                              }
                              className="inline-flex items-center justify-center w-6 h-6 rounded text-slate-400 hover:text-red-600 hover:bg-red-50"
                              title="Delete"
                              data-testid={`jha-file-delete-${f.id}`}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </li>
                        ))}
                      </ul>

                      {/* Add-file row */}
                      <div className="mt-2 flex items-center gap-2">
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
                          onClick={() =>
                            fileInputs.current[row.project_number]?.click()
                          }
                          className="h-8 text-xs font-mono uppercase tracking-wide"
                          data-testid={`jha-add-${row.project_number}`}
                        >
                          {isBusy ? (
                            <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                          ) : (
                            <Upload className="w-3.5 h-3.5 mr-1" />
                          )}
                          + Add file
                        </Button>
                        <span className="text-[10px] text-slate-400">
                          PDF, Word, Excel, ZIP, images, CAD, video — up to 250 MB
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
