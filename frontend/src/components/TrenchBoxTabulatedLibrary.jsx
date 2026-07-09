import React, { useEffect, useMemo, useRef, useState } from "react";
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
  Folder,
  Library,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const REACT_APP_BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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

/**
 * TrenchBoxTabulatedLibrary — multi-file library for trench-box
 * tabulated data. Each trench box in /trench-boxes gets a folder.
 * A "General / Educational" folder holds shared documents (like the
 * United Rentals explainer PDF).
 *
 * adminMode=true shows upload + delete controls. Crew-facing view
 * (adminMode=false) only allows browsing + downloading.
 */
export default function TrenchBoxTabulatedLibrary({ adminMode = false }) {
  const { t, lang } = useT();
  const [groups, setGroups] = useState([]);       // [{project_number, files:[]}]
  const [boxes, setBoxes] = useState([]);         // trench-box master list
  const [loading, setLoading] = useState(true);
  const [busyBox, setBusyBox] = useState(null);
  const [openMap, setOpenMap] = useState({ general: true });
  const fileInputs = useRef({});

  const refresh = async () => {
    setLoading(true);
    try {
      const [r, b] = await Promise.all([
        api.get("/trench-box-files"),
        api.get("/trench-boxes"),
      ]);
      setGroups(r.data?.projects || []);
      setBoxes(b.data || []);
    } catch (e) {
      toast.error(
        e?.response?.data?.detail || "Failed to load tabulated-data library"
      );
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    refresh();
  }, []);

  /** Build the combined row list: "general" first, then every trench box. */
  const rows = useMemo(() => {
    const filesByKey = {};
    for (const g of groups) filesByKey[g.project_number] = g.files;

    const out = [];
    out.push({
      key: "general",
      label: t(
        "General / Educational — United Rentals explainers, OSHA references"
      ),
      files: filesByKey.general || [],
      isGeneral: true,
    });
    for (const b of boxes) {
      out.push({
        key: b.id,
        label: `${b.manufacturer ? b.manufacturer + " · " : ""}${b.model_number || "(unnamed)"}${b.inside_width_in && b.inside_length_in ? ` · ${b.inside_length_in}×${b.inside_height_in}×${b.inside_width_in}` : ""}`,
        files: filesByKey[b.id] || [],
        isGeneral: false,
      });
    }
    // Orphan groups (files for a box that no longer exists)
    const knownKeys = new Set(out.map((r) => r.key));
    for (const g of groups) {
      if (!knownKeys.has(g.project_number)) {
        out.push({
          key: g.project_number,
          label: "(orphan — box no longer in master list)",
          files: g.files,
          isGeneral: false,
        });
      }
    }
    return out;
  }, [groups, boxes, t, lang]);

  const toggleOpen = (k) =>
    setOpenMap((m) => ({ ...m, [k]: !m[k] }));

  const onPickFile = (key, e) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(key, file);
    if (fileInputs.current[key]) fileInputs.current[key].value = "";
  };

  const onDrop = (key, e) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer?.files?.[0];
    if (file) uploadFile(key, file);
  };

  const uploadFile = async (box_id, file) => {
    setBusyBox(box_id);
    try {
      const fd = new FormData();
      fd.append("box_id", box_id);
      fd.append("file", file, file.name);
      await api.post("/trench-box-files", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 5 * 60 * 1000,
      });
      toast.success(`Uploaded ${file.name}`);
      await refresh();
      setOpenMap((m) => ({ ...m, [box_id]: true }));
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setBusyBox(null);
    }
  };

  const removeFile = async (file, box_id) => {
    if (!window.confirm(`Delete ${file.filename}?\n\nThis cannot be undone.`))
      return;
    setBusyBox(box_id);
    try {
      await api.delete(`/trench-box-files/${file.id}`);
      toast.success(`Deleted ${file.filename}`);
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Delete failed");
    } finally {
      setBusyBox(null);
    }
  };

  const downloadHref = (id) =>
    `${REACT_APP_BACKEND_URL}/api/job-hazard-files/${id}/download`;

  const totalFiles = rows.reduce((n, r) => n + r.files.length, 0);

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-5 sm:p-7 mb-6"
      data-testid="trench-tabulated-library"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-red-700 text-white shrink-0">
          <Library className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-800 font-bold">
            {adminMode ? "Admin — upload · delete · browse" : t("Field Reference")}
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            {t("Tabulated Data Library")}
          </h2>
          <p className="text-sm text-slate-600 mt-1.5">
            {t("Manufacturer tabulated-data PDFs, technical data sheets, and educational resources — one folder per trench box plus a shared")}
            <strong> {t("General / Educational")} </strong>
            {t("folder. Total:")}{" "}
            <strong>{totalFiles}</strong> {t("files across")}{" "}
            <strong>{rows.length}</strong> {t("folders.")}
          </p>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-10 text-slate-500">
          <Loader2 className="w-6 h-6 animate-spin inline-block mr-2" />
          {t("Loading…")}
        </div>
      ) : (
        <div className="space-y-2">
          {rows.map((row) => {
            const isOpen = !!openMap[row.key];
            const isBusy = busyBox === row.key;
            return (
              <div
                key={row.key}
                className={`border-2 ${row.isGeneral ? "border-amber-400 bg-amber-50" : "border-slate-200 bg-white"} rounded`}
                data-testid={`tab-box-${row.key}`}
                onDragOver={(e) => {
                  if (!adminMode) return;
                  e.preventDefault();
                  e.stopPropagation();
                }}
                onDrop={(e) => adminMode && onDrop(row.key, e)}
              >
                <button
                  type="button"
                  onClick={() => toggleOpen(row.key)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-slate-50"
                  data-testid={`tab-toggle-${row.key}`}
                >
                  {isOpen ? (
                    <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-500 shrink-0" />
                  )}
                  {row.isGeneral ? (
                    <span className="inline-block px-1.5 py-0.5 bg-amber-500 text-white text-[10px] font-bold font-mono rounded uppercase tracking-wide shrink-0">
                      {t("Start Here")}
                    </span>
                  ) : (
                    <span className="inline-block px-1.5 py-0.5 bg-red-700 text-white text-[10px] font-bold font-mono rounded uppercase tracking-wide shrink-0">
                      {t("Box")}
                    </span>
                  )}
                  <span className="font-medium text-sm text-slate-900 truncate">
                    {row.label}
                  </span>
                  <span className="ml-auto inline-flex items-center gap-1.5 text-xs text-slate-500 shrink-0">
                    <Folder className="w-3.5 h-3.5" />
                    {row.files.length}
                  </span>
                </button>

                {isOpen && (
                  <div className="border-t border-slate-200 px-3 py-2">
                    {row.files.length === 0 && (
                      <p className="text-xs text-slate-500 py-1.5">
                        {adminMode
                          ? "No files yet — drop one here or click + Add file."
                          : t("No files for this box yet. Ask the office to upload the manufacturer data sheet.")}
                      </p>
                    )}
                    <ul className="space-y-1.5">
                      {row.files.map((f) => (
                        <li
                          key={f.id}
                          className="flex items-center gap-2 px-2 py-1.5 bg-white rounded border border-slate-200"
                          data-testid={`tab-file-${f.id}`}
                        >
                          {fileIconFor(f.filename, f.content_type)}
                          <a
                            href={downloadHref(f.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 truncate text-xs text-slate-800 hover:text-red-700 hover:underline font-medium"
                            data-testid={`tab-file-link-${f.id}`}
                          >
                            {f.filename}
                          </a>
                          <span className="text-[10px] font-mono text-slate-400 shrink-0">
                            {bytesPretty(f.file_size)}
                          </span>
                          <span className="text-[10px] text-slate-400 shrink-0 hidden sm:inline">
                            {f.uploaded_at
                              ? formatPlatformDate(f.uploaded_at)
                              : ""}
                          </span>
                          {adminMode && (
                            <button
                              type="button"
                              onClick={() => removeFile(f, row.key)}
                              className="inline-flex items-center justify-center w-6 h-6 rounded text-slate-400 hover:text-red-600 hover:bg-red-50"
                              title="Delete"
                              data-testid={`tab-file-delete-${f.id}`}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </li>
                      ))}
                    </ul>

                    {adminMode && (
                      <div className="mt-2 flex items-center gap-2">
                        <input
                          type="file"
                          ref={(el) => (fileInputs.current[row.key] = el)}
                          className="hidden"
                          onChange={(e) => onPickFile(row.key, e)}
                          data-testid={`tab-file-input-${row.key}`}
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={isBusy}
                          onClick={() => fileInputs.current[row.key]?.click()}
                          className="h-8 text-xs font-mono uppercase tracking-wide"
                          data-testid={`tab-add-${row.key}`}
                        >
                          {isBusy ? (
                            <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                          ) : (
                            <Upload className="w-3.5 h-3.5 mr-1" />
                          )}
                          + Add file
                        </Button>
                        <span className="text-[10px] text-slate-400">
                          PDF, Word, Excel, ZIP, images — up to 250 MB
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
