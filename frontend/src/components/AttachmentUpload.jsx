// AttachmentUpload.jsx — Track 19.04 · Unified Daily Report attachments.
//
// One picker, one metadata model, one submit path — for PDFs, Excel
// (.xlsx / .xls) and CSV files. Photos continue to use PhotoUpload:
// this component is intentionally scoped to "documents" so the
// existing photo compression + PDF-embed pipeline is not disturbed.
//
// Doctrine (operator directive 2026-06-29):
//   * Do NOT build a second storage architecture. The upload endpoint
//     `POST /api/daily-reports/attachments/upload` reuses the SAME R2
//     bucket, client, and signed-URL helpers that back photos. The
//     server returns an already-uploaded metadata blob; this
//     component holds only the metadata (not the base64 bytes) in
//     form state so a 25 MB PDF never bloats the Daily Report autosave.
//   * Filename is sanitised server-side, so the client can pass the
//     raw picker filename without risk.
//   * Grouping: Photos / PDFs / Spreadsheets — driven off the
//     server-supplied `category`, not client-side heuristics.

import React, { useRef, useState } from "react";
import { FileText, FileSpreadsheet, X, Loader2, Upload } from "lucide-react";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";

const ALLOWED_MIME = new Set([
  "application/pdf",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  // TRACK 19.19 · Macro-enabled Excel workbook (.xlsm) support.
  // Passive attachment only — browser never opens the file for
  // execution; server never parses macros. Some browsers report .xlsm
  // under the plain application/vnd.ms-excel MIME (already allow-listed
  // above) — the server-side filename fallback disambiguates.
  "application/vnd.ms-excel.sheet.macroenabled.12",
  "application/vnd.ms-excel.sheet.macroenabled",
  "text/csv",
  "application/csv",
  // TRACK 24.11B · Word + plain text (universal field-doc types).
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
]);
const MAX_BYTES = 25 * 1024 * 1024; // matches server _MAX_DOC_BYTES

// TRACK 19.19 · Filename-extension fallback lets .xlsm through even
// when the browser reports application/octet-stream (rare, but seen on
// some Windows installs after a Reset File Associations).
// TRACK 24.11B · Extended for Word + text.
const ALLOWED_EXT_FALLBACK = new Set([
  "pdf", "xls", "xlsx", "xlsm", "csv", "doc", "docx", "txt",
]);

function _fileExt(name) {
  const m = /\.([a-z0-9]{1,8})$/i.exec(name || "");
  return m ? m[1].toLowerCase() : "";
}

function _fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("read-failed"));
    reader.readAsDataURL(file);
  });
}

function _iconFor(category) {
  if (category === "Spreadsheet") return <FileSpreadsheet className="w-5 h-5 text-emerald-600" />;
  if (category === "PDF") return <FileText className="w-5 h-5 text-rose-600" />;
  return <FileText className="w-5 h-5 text-slate-600" />;
}

function _fmtBytes(n) {
  if (!n && n !== 0) return "";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export const AttachmentUpload = ({
  attachments = [],
  onChange,
  testIdBase = "dr-attachments",
}) => {
  const { t } = useT();
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(0);
  // TRACK 24.11B · Desktop drag/drop affordance for Toughbook /
  // Windows / Mac field users.
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;
    const list = Array.from(files);
    setBusy(list.length);
    const next = [...attachments];
    for (const file of list) {
      try {
        // Client-side type gate — server validates too, but bounce
        // the operator early on obvious misclicks (.exe, .zip).
        // TRACK 19.19 · Accept when EITHER the MIME is whitelisted OR
        // the filename extension is a known safe office/spreadsheet
        // extension. This lets .xlsm through on browsers that report
        // it under the ambiguous application/vnd.ms-excel MIME (already
        // allow-listed) or application/octet-stream.
        const mimeOk = file.type && ALLOWED_MIME.has(file.type.toLowerCase());
        const extOk = ALLOWED_EXT_FALLBACK.has(_fileExt(file.name));
        if (!mimeOk && !extOk) {
          toast.error(
            t("Unsupported file type: {t}").replace("{t}", file.type || "unknown")
          );
          continue;
        }
        if (file.size > MAX_BYTES) {
          toast.error(
            t("{n} is too large ({sz}) — 25 MB max")
              .replace("{n}", file.name || "file")
              .replace("{sz}", _fmtBytes(file.size))
          );
          continue;
        }
        const dataUrl = await _fileToDataUrl(file);
        const resp = await api.post(
          "/daily-reports/attachments/upload",
          { file_data: dataUrl, filename: file.name || "" },
          { timeout: 60000 },
        );
        if (resp?.data?.attachment_ref) {
          next.push(resp.data);
          onChange?.([...next]);
        } else {
          toast.error(t("Upload failed for {n}").replace("{n}", file.name || "file"));
        }
      } catch (e) {
        const detail =
          e?.response?.data?.detail || e?.message || t("Upload failed");
        toast.error(String(detail));
      } finally {
        setBusy((v) => Math.max(0, v - 1));
      }
    }
    setBusy(0);
    if (inputRef.current) inputRef.current.value = "";
  };

  const removeAt = (idx) => {
    const next = attachments.filter((_, i) => i !== idx);
    onChange?.(next);
  };

  // Group by category for the calm display grid.
  const grouped = attachments.reduce((acc, a) => {
    const k = a.category || "Other";
    (acc[k] = acc[k] || []).push(a);
    return acc;
  }, {});

  return (
    <div
      data-testid={testIdBase}
      className={
        "space-y-3 rounded-lg transition-colors " +
        (dragOver
          ? "border-2 border-dashed border-red-500 bg-red-50 p-3"
          : "border-2 border-transparent p-3")
      }
      onDragOver={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(false);
      }}
      onDrop={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(false);
        handleFiles(Array.from(e.dataTransfer?.files || []));
      }}
    >
      {dragOver && (
        <div
          className="text-center text-red-800 font-semibold text-sm py-2"
          data-testid={`${testIdBase}-drop-target`}
        >
          {t("Drop files here to upload")}
        </div>
      )}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <label
          className="inline-flex items-center gap-2 rounded-lg border-2 border-dashed border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer"
          data-testid={`${testIdBase}-picker-label`}
        >
          <Upload className="w-4 h-4" />
          {busy > 0 ? (
            <span className="inline-flex items-center gap-1">
              <Loader2 className="w-4 h-4 animate-spin" />
              {t("Uploading {n}…").replace("{n}", String(busy))}
            </span>
          ) : (
            t("Attach PDF, Excel, Word, or Text")
          )}
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.xls,.xlsx,.xlsm,.csv,.doc,.docx,.txt,application/pdf,application/vnd.ms-excel,application/vnd.ms-excel.sheet.macroEnabled.12,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
            multiple
            className="hidden"
            onChange={(e) => handleFiles(Array.from(e.target.files || []))}
            data-testid={`${testIdBase}-picker-input`}
          />
        </label>
        <p className="text-xs text-slate-500">
          {t("PDFs, Excel (.xlsx / .xls / .xlsm), CSV, Word (.doc / .docx), and text files up to 25 MB each.")}
        </p>
      </div>

      {Object.keys(grouped).length > 0 && (
        <div className="space-y-3">
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category} data-testid={`${testIdBase}-group-${category.toLowerCase()}`}>
              <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
                {category}
              </p>
              <ul className="space-y-1">
                {items.map((a) => {
                  const globalIdx = attachments.indexOf(a);
                  return (
                    <li
                      key={a.attachment_ref || globalIdx}
                      className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2"
                      data-testid={`${testIdBase}-item-${globalIdx}`}
                    >
                      {_iconFor(category)}
                      <div className="flex-1 min-w-0">
                        <p className="truncate text-sm font-medium text-slate-800">
                          {a.filename || t("Attachment")}
                        </p>
                        <p className="text-xs text-slate-500">
                          {(a.extension || "").toUpperCase()} · {_fmtBytes(a.file_size)}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeAt(globalIdx)}
                        className="text-slate-500 hover:text-red-600"
                        aria-label={t("Remove attachment")}
                        data-testid={`${testIdBase}-remove-${globalIdx}`}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AttachmentUpload;
