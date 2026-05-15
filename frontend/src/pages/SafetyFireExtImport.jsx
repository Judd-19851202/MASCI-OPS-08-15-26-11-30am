// SafetyFireExtImport — Iter134. Bulk-import fire extinguisher inventory.
// Two-step flow mirrors the backend: upload -> /preview returns a plan,
// then user confirms -> /commit applies it. Nothing writes without the
// explicit "Apply" click.
import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  Upload, Download, FileSpreadsheet, Loader2, CheckCircle2,
  AlertTriangle, ArrowRight, X, Plus, RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import SafetyShell from "@/components/SafetyShell";
import { getSafetyToken } from "@/lib/safetyAuth";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const tokenHeader = () => ({ "X-Safety-Token": getSafetyToken() });

const ACTION_STYLE = {
  create: "bg-emerald-100 text-emerald-900 border-emerald-300",
  update: "bg-sky-100 text-sky-900 border-sky-300",
  skip:   "bg-amber-100 text-amber-900 border-amber-300",
};

const ACTION_ICON = {
  create: Plus,
  update: RefreshCw,
  skip:   AlertTriangle,
};

function Stat({ label, value, accent = "slate" }) {
  const colors = {
    slate:   "border-slate-300 text-slate-900",
    emerald: "border-emerald-500 text-emerald-900",
    sky:     "border-sky-500 text-sky-900",
    amber:   "border-amber-500 text-amber-900",
    red:     "border-red-500 text-red-900",
  };
  return (
    <div className={`bg-white border-2 ${colors[accent]} rounded-md p-3 sm:p-4`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
        {label}
      </div>
      <div className="font-display text-2xl sm:text-3xl font-black leading-none mt-1">
        {value}
      </div>
    </div>
  );
}

export default function SafetyFireExtImport() {
  const nav = useNavigate();
  const fileRef = useRef(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [preview, setPreview] = useState(null);
  const [committed, setCommitted] = useState(null);
  const [errorFilter, setErrorFilter] = useState(false);

  const downloadTemplate = () => {
    // Template route is public — no auth header required, but we send the
    // token anyway via axios for symmetry. Use anchor href for browser save.
    window.open(`${API}/safety/fire-extinguishers/import/template`, "_blank");
  };

  const onPick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const name = f.name.toLowerCase();
    if (!name.endsWith(".csv") && !name.endsWith(".xlsx") && !name.endsWith(".xlsm")) {
      toast.error("Use a .csv or .xlsx file");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      toast.error("File too large — 10 MB limit");
      return;
    }
    setFile(f);
    setPreview(null);
    setCommitted(null);
  };

  const doPreview = async () => {
    if (!file) { toast.error("Choose a file first"); return; }
    setUploading(true);
    setCommitted(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const r = await axios.post(
        `${API}/safety/fire-extinguishers/import/preview`,
        form,
        { headers: { ...tokenHeader(), "Content-Type": "multipart/form-data" } },
      );
      setPreview(r.data);
      toast.success(
        `Parsed ${r.data.total_rows} rows — ${r.data.to_create} new, ${r.data.to_update} updates, ${r.data.to_skip} skip`,
      );
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Preview failed");
    } finally {
      setUploading(false);
    }
  };

  const doCommit = async () => {
    if (!preview?.preview_id) return;
    if (!window.confirm(
      `Apply ${preview.to_create} new + ${preview.to_update} updates to the register?\n\n` +
      `${preview.to_skip} row(s) with errors will be skipped.\n\nThis cannot be undone.`,
    )) return;
    setCommitting(true);
    try {
      const r = await axios.post(
        `${API}/safety/fire-extinguishers/import/commit`,
        { preview_id: preview.preview_id },
        { headers: tokenHeader() },
      );
      setCommitted(r.data);
      toast.success(`Imported — ${r.data.created} created, ${r.data.updated} updated`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Commit failed");
    } finally {
      setCommitting(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setCommitted(null);
    setErrorFilter(false);
    if (fileRef.current) fileRef.current.value = "";
  };

  const rows = preview?.rows || [];
  const visibleRows = errorFilter ? rows.filter((r) => (r.errors || []).length > 0) : rows;
  const errorCount = rows.filter((r) => (r.errors || []).length > 0).length;

  return (
    <SafetyShell title="Bulk Import — Fire Extinguishers" kicker="SAFETY · IMPORT WIZARD">
      {/* Intro + template download */}
      <div className="bg-white border-2 border-slate-300 rounded-md p-4 sm:p-5 mb-5">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
          <div className="max-w-2xl">
            <h2 className="font-display text-lg font-black text-slate-900 mb-1">
              Upload legacy extinguisher inventory
            </h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              Accepts .csv or .xlsx. Each row becomes one extinguisher record.
              Rows matched on <strong>Extinguisher ID</strong>, <strong>Serial Number</strong>,
              or <strong>Truck + Location</strong> update the existing unit; unmatched rows create new.
              Nothing is written until you review and click <strong>Apply</strong>.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={downloadTemplate}
            className="h-10 border-2 border-slate-300 font-bold uppercase tracking-wide shrink-0"
            data-testid="safety-fe-import-template"
          >
            <Download className="w-4 h-4 mr-2" /> Download Template
          </Button>
        </div>
      </div>

      {/* Step 1 — file picker */}
      <div className="bg-white border-2 border-slate-300 rounded-md p-4 sm:p-5 mb-5">
        <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-600 mb-3">
          Step 1 · Choose File
        </div>
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.xlsx,.xlsm,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={onPick}
            className="block text-sm flex-1 file:mr-3 file:py-2 file:px-4 file:rounded file:border-2 file:border-slate-300 file:bg-slate-50 file:text-slate-800 file:font-bold file:uppercase file:text-xs hover:file:bg-slate-100"
            data-testid="safety-fe-import-file"
          />
          <Button
            onClick={doPreview}
            disabled={!file || uploading}
            className="bg-cyan-700 hover:bg-cyan-800 text-white border-b-2 border-cyan-900 font-bold uppercase tracking-wide h-10 shrink-0"
            data-testid="safety-fe-import-preview"
          >
            {uploading
              ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Parsing…</>
              : <><Upload className="w-4 h-4 mr-2" /> Parse &amp; Preview</>}
          </Button>
          {(file || preview) && (
            <Button
              variant="outline"
              onClick={reset}
              className="h-10 border-2 border-slate-300 font-bold uppercase tracking-wide shrink-0"
              data-testid="safety-fe-import-reset"
            >
              <X className="w-4 h-4 mr-2" /> Reset
            </Button>
          )}
        </div>
        {file && !preview && (
          <div className="mt-3 text-xs text-slate-600 flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-slate-500" />
            <span className="font-mono">{file.name}</span>
            <span className="text-slate-400">({(file.size / 1024).toFixed(1)} KB)</span>
          </div>
        )}
      </div>

      {/* Step 2 — preview summary */}
      {preview && !committed && (
        <div className="bg-white border-2 border-slate-300 rounded-md p-4 sm:p-5 mb-5" data-testid="safety-fe-import-preview-card">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-600">
              Step 2 · Review Preview <span className="text-slate-400">({preview.file_name})</span>
            </div>
            <Button
              onClick={doCommit}
              disabled={committing || (preview.to_create + preview.to_update === 0)}
              className="bg-emerald-700 hover:bg-emerald-800 text-white border-b-2 border-emerald-900 font-bold uppercase tracking-wide h-10"
              data-testid="safety-fe-import-commit"
            >
              {committing
                ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Applying…</>
                : <>Apply {preview.to_create + preview.to_update} Changes <ArrowRight className="w-4 h-4 ml-2" /></>}
            </Button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <Stat label="Total Rows" value={preview.total_rows} accent="slate" />
            <Stat label="Will Create" value={preview.to_create} accent="emerald" />
            <Stat label="Will Update" value={preview.to_update} accent="sky" />
            <Stat label="Will Skip" value={preview.to_skip} accent={preview.to_skip > 0 ? "amber" : "slate"} />
          </div>

          {errorCount > 0 && (
            <div className="flex items-center justify-between bg-amber-50 border-2 border-amber-300 rounded p-3 mb-3">
              <div className="flex items-center gap-2 text-sm text-amber-900">
                <AlertTriangle className="w-4 h-4" />
                <strong>{errorCount}</strong> row(s) have validation issues and will be skipped.
              </div>
              <button
                onClick={() => setErrorFilter((v) => !v)}
                className="text-xs font-bold uppercase tracking-wide text-amber-800 hover:underline"
                data-testid="safety-fe-import-error-filter"
              >
                {errorFilter ? "Show All Rows" : "Show Errors Only"}
              </button>
            </div>
          )}

          {/* Row table */}
          <div className="overflow-x-auto border-2 border-slate-200 rounded">
            <table className="w-full text-sm" data-testid="safety-fe-import-preview-table">
              <thead className="bg-slate-50 border-b-2 border-slate-200">
                <tr>
                  <th className="px-2 py-2 text-left font-mono text-[10px] uppercase tracking-wider text-slate-600 w-10">#</th>
                  <th className="px-2 py-2 text-left font-mono text-[10px] uppercase tracking-wider text-slate-600 w-24">Action</th>
                  <th className="px-2 py-2 text-left font-mono text-[10px] uppercase tracking-wider text-slate-600">Unit ID</th>
                  <th className="px-2 py-2 text-left font-mono text-[10px] uppercase tracking-wider text-slate-600">Serial</th>
                  <th className="px-2 py-2 text-left font-mono text-[10px] uppercase tracking-wider text-slate-600">Location / Truck</th>
                  <th className="px-2 py-2 text-left font-mono text-[10px] uppercase tracking-wider text-slate-600">Status / Next Due</th>
                  <th className="px-2 py-2 text-left font-mono text-[10px] uppercase tracking-wider text-slate-600">Notes</th>
                </tr>
              </thead>
              <tbody>
                {visibleRows.slice(0, 500).map((r) => {
                  const Icon = ACTION_ICON[r.action] || AlertTriangle;
                  const hasErr = (r.errors || []).length > 0;
                  return (
                    <tr key={r.row_number} className={`border-b border-slate-100 ${hasErr ? "bg-red-50/40" : ""}`}>
                      <td className="px-2 py-2 font-mono text-xs text-slate-500">{r.row_number}</td>
                      <td className="px-2 py-2">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] uppercase tracking-wide font-bold ${ACTION_STYLE[r.action]}`}>
                          <Icon className="w-3 h-3" /> {r.action}
                        </span>
                        {r.match_reason && (
                          <div className="text-[10px] text-slate-500 mt-0.5 italic">{r.match_reason}</div>
                        )}
                      </td>
                      <td className="px-2 py-2 font-mono text-xs">{r.data?.unit_id || <span className="text-slate-300">—</span>}</td>
                      <td className="px-2 py-2 font-mono text-xs">{r.data?.serial_number || <span className="text-slate-300">—</span>}</td>
                      <td className="px-2 py-2 text-xs">
                        <div>{r.data?.location_value || <span className="text-slate-300">—</span>}</div>
                        {r.data?.truck && <div className="text-[10px] text-slate-500">Truck: {r.data.truck}</div>}
                      </td>
                      <td className="px-2 py-2 text-xs">
                        <div>{r.data?.last_status || <span className="text-slate-300">—</span>}</div>
                        {r.data?.next_due_date && <div className="text-[10px] text-slate-500">Due: {r.data.next_due_date}</div>}
                      </td>
                      <td className="px-2 py-2 text-xs text-slate-600">
                        {hasErr ? (
                          <ul className="list-disc pl-4 text-red-700">
                            {r.errors.map((e, i) => <li key={i}>{e}</li>)}
                          </ul>
                        ) : (
                          r.data?.notes || <span className="text-slate-300">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {visibleRows.length === 0 && (
                  <tr><td colSpan={7} className="px-3 py-6 text-center text-slate-500 text-sm">No rows to display.</td></tr>
                )}
              </tbody>
            </table>
            {visibleRows.length > 500 && (
              <div className="px-3 py-2 text-xs text-slate-500 bg-slate-50 border-t border-slate-200">
                Showing first 500 of {visibleRows.length}. Apply will process all rows.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 3 — result */}
      {committed && (
        <div className="bg-emerald-50 border-2 border-emerald-400 rounded-md p-4 sm:p-5 mb-5" data-testid="safety-fe-import-result">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-700 mt-1 shrink-0" />
            <div className="flex-1">
              <div className="font-display text-lg font-black text-emerald-900">
                Import Complete
              </div>
              <p className="text-sm text-emerald-900 mt-1">
                <strong>{committed.created}</strong> new extinguishers added, <strong>{committed.updated}</strong> updated,{" "}
                <strong>{committed.skipped}</strong> skipped.
              </p>
              {(committed.errors || []).length > 0 && (
                <div className="mt-2 text-xs text-amber-800 bg-amber-50 border border-amber-300 rounded p-2">
                  <strong>Note:</strong> {committed.errors.length} row(s) errored on apply:
                  <ul className="list-disc pl-4 mt-1">
                    {committed.errors.slice(0, 10).map((e, i) => <li key={i}>{e}</li>)}
                  </ul>
                </div>
              )}
              <div className="mt-3 flex gap-2">
                <Button
                  onClick={() => nav("/safety-portal/fire-extinguishers")}
                  className="bg-cyan-700 hover:bg-cyan-800 text-white border-b-2 border-cyan-900 font-bold uppercase tracking-wide h-9"
                  data-testid="safety-fe-import-view-register"
                >
                  View Register <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
                <Button
                  variant="outline"
                  onClick={reset}
                  className="h-9 border-2 border-slate-300 font-bold uppercase tracking-wide"
                  data-testid="safety-fe-import-another"
                >
                  Import Another File
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </SafetyShell>
  );
}
