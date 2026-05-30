// iter352 · HR · Driver Qualification — Roster Importer
// Self-service replacement for the iter351 one-off loader. HR + Admin
// can upload XLSX/CSV → preview → confirm → apply, with full audit
// trail. All operations route through /api/hr/driver-qualification/
// import/* and are gated by require_hr_or_admin on the backend.
//
// UX intent: feel like an HR operational compliance tool, not a
// developer utility. Calm tone, clear states, safe defaults.
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Loader2, Upload, FileSpreadsheet, CheckCircle2, AlertTriangle,
  ShieldAlert, ArrowRight, ClipboardList, Download, History,
} from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import HrPageShell from "@/components/HrPageShell";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { operationalError } from "@/lib/errors";

const CONFIDENCE_PILL = {
  high:   "bg-emerald-100 text-emerald-900 border-emerald-300",
  medium: "bg-amber-100   text-amber-900   border-amber-300",
  low:    "bg-orange-100  text-orange-900  border-orange-300",
  none:   "bg-red-100     text-red-900     border-red-300",
};

function fmtVal(v) {
  if (v === null || v === undefined || v === "") return "—";
  if (Array.isArray(v)) return v.length ? v.join(", ") : "—";
  if (v === true) return "Yes";
  if (v === false) return "No";
  return String(v);
}

export default function HrDriverQualificationImport() {
  const { t } = useT();
  const [file, setFile] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [preview, setPreview] = useState(null);    // server response
  const [skipRows, setSkipRows] = useState(new Set());
  const [createUnmatched, setCreateUnmatched] = useState(false);
  const [result, setResult] = useState(null);      // post-apply summary
  const [auditList, setAuditList] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const inputRef = useRef(null);

  const loadAudit = useCallback(async () => {
    setAuditLoading(true);
    try {
      const r = await api.get("/hr/driver-qualification/import/audit", { params: { limit: 20 } });
      setAuditList(r.data?.items || []);
    } catch (err) {
      // calm — audit list is non-critical
      toast.error(operationalError(err, t("Audit history temporarily unavailable.")));
    } finally {
      setAuditLoading(false);
    }
  }, [t]);

  useEffect(() => { loadAudit(); }, [loadAudit]);

  const reset = () => {
    setFile(null);
    setPreview(null);
    setSkipRows(new Set());
    setCreateUnmatched(false);
    setResult(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handlePreview = async () => {
    if (!file) {
      toast.error(t("Choose an XLSX or CSV roster file first."));
      return;
    }
    setPreviewLoading(true);
    setPreview(null);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await api.post("/hr/driver-qualification/import/preview", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setPreview(r.data);
      // Pre-skip every unmatched row so the default apply is safe.
      const auto = new Set();
      (r.data.preview || []).forEach((row, i) => {
        if (!row.employee_id) auto.add(i);
      });
      setSkipRows(auto);
      toast.success(t("Preview ready. Review each row before applying."));
    } catch (err) {
      toast.error(operationalError(err, t("Could not read the roster file. Confirm it's a valid XLSX or CSV with a 'name' column.")));
    } finally {
      setPreviewLoading(false);
    }
  };

  const toggleSkip = (i) => {
    setSkipRows((prev) => {
      const n = new Set(prev);
      if (n.has(i)) n.delete(i); else n.add(i);
      return n;
    });
  };

  const handleApply = async () => {
    if (!preview?.preview_token) return;
    setApplyLoading(true);
    try {
      const r = await api.post("/hr/driver-qualification/import/apply", {
        preview_token: preview.preview_token,
        skip_rows: Array.from(skipRows),
        create_unmatched: createUnmatched,
      });
      setResult(r.data);
      toast.success(t("Driver updates applied successfully."));
      loadAudit();
    } catch (err) {
      toast.error(operationalError(err, t("Could not apply the import. Please retry.")));
    } finally {
      setApplyLoading(false);
    }
  };

  const summary = preview?.summary || {};
  const totalRows = preview?.row_count || 0;
  const willUpdate = preview ? preview.preview.filter((r, i) => !skipRows.has(i) && r.employee_id && Object.keys(r.fields_to_update || {}).length > 0).length : 0;
  const willCreate = preview && createUnmatched ? preview.preview.filter((r, i) => !skipRows.has(i) && !r.employee_id).length : 0;
  const willSkip = skipRows.size;

  return (
    <HrPageShell title="CDL Roster Importer" kicker="HR · DRIVER QUALIFICATION · IMPORT WORKFLOW">
      {/* INTRO STRIP */}
      <Card className="p-4 mb-5 border-2 border-purple-300 bg-purple-50/50">
        <div className="flex items-start gap-3">
          <ClipboardList className="w-5 h-5 text-purple-700 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-slate-800">
            <div className="font-bold text-purple-900 mb-1">{t("Operational compliance tool")}</div>
            <p>{t("Upload your insurance / DOT driver roster as XLSX or CSV. The importer will match each name against the employee directory, show you exactly what will change, and only write after you confirm. Both HR and Admin can run imports.")}</p>
            <p className="mt-2 text-xs text-slate-600 font-mono uppercase tracking-[0.15em]">
              {t("Required column")}: <strong>name</strong> · {t("Optional")}: approved_company_driver · cdl_holder · cdl_license_number · cdl_state · cdl_expiration_date · medical_card_expiration_date · endorsements · restrictions · driver_status
            </p>
          </div>
        </div>
      </Card>

      {/* STEP 1: UPLOAD */}
      {!preview && !result && (
        <Card className="p-6 mb-5" data-testid="dqi-upload-card">
          <div className="flex flex-col items-center text-center gap-4">
            <Upload className="w-12 h-12 text-purple-600" />
            <div>
              <div className="font-bold text-lg text-slate-900">{t("Choose a roster file")}</div>
              <div className="text-sm text-slate-600 mt-1">{t("XLSX or CSV, up to 5 MB. Header row must include a 'name' column.")}</div>
            </div>
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block text-sm file:mr-4 file:py-2 file:px-4 file:rounded file:border-2 file:border-purple-300 file:bg-white file:font-bold file:text-purple-900 hover:file:border-purple-500"
              data-testid="dqi-file-input"
            />
            {file && (
              <div className="text-xs font-mono text-slate-700 flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4" /> {file.name} · {(file.size / 1024).toFixed(1)} KB
              </div>
            )}
            <Button
              onClick={handlePreview}
              disabled={!file || previewLoading}
              className="bg-purple-700 hover:bg-purple-800 text-white px-6 h-10"
              data-testid="dqi-preview-btn"
            >
              {previewLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ArrowRight className="w-4 h-4 mr-2" />}
              {t("Preview Import")}
            </Button>
          </div>
        </Card>
      )}

      {/* STEP 2: PREVIEW */}
      {preview && !result && (
        <>
          <Card className="p-4 mb-4 border-2 border-purple-200">
            <div className="flex flex-wrap gap-2 items-center justify-between mb-3">
              <div className="font-bold text-slate-900">{t("Preview Summary")}</div>
              <Button variant="outline" onClick={reset} size="sm" data-testid="dqi-restart-btn">{t("Start Over")}</Button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-center" data-testid="dqi-summary-strip">
              {[
                ["Total Rows", totalRows, "bg-slate-100 text-slate-900 border-slate-300"],
                ["Matched", summary.matched || 0, "bg-emerald-100 text-emerald-900 border-emerald-300"],
                ["Unmatched", summary.unmatched || 0, "bg-red-100 text-red-900 border-red-300"],
                ["Ambiguous", summary.ambiguous || 0, "bg-amber-100 text-amber-900 border-amber-300"],
                ["No Change", summary.no_change || 0, "bg-cyan-100 text-cyan-900 border-cyan-300"],
              ].map(([label, n, cls]) => (
                <div key={label} className={`px-2 py-2 rounded border-2 ${cls}`}>
                  <div className="text-xl font-bold">{n}</div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.15em] mt-1">{t(label)}</div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="overflow-x-auto mb-4" data-testid="dqi-preview-table">
            <table className="w-full text-sm min-w-[1100px]">
              <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                <tr>
                  <th className="text-center px-2 py-2 w-10">{t("Apply")}</th>
                  <th className="text-left px-3 py-2">{t("Source Name")}</th>
                  <th className="text-left px-3 py-2">{t("Matched Employee")}</th>
                  <th className="text-left px-3 py-2">{t("Method")}</th>
                  <th className="text-center px-3 py-2">{t("Confidence")}</th>
                  <th className="text-left px-3 py-2">{t("Fields To Update")}</th>
                  <th className="text-left px-3 py-2">{t("Warnings")}</th>
                </tr>
              </thead>
              <tbody>
                {(preview.preview || []).map((row, i) => {
                  const skipped = skipRows.has(i);
                  const unmatched = !row.employee_id;
                  const nochange = row.employee_id && Object.keys(row.fields_to_update || {}).length === 0;
                  return (
                    <tr
                      key={i}
                      className={`border-t border-slate-100 ${skipped ? "opacity-50 bg-slate-50" : "hover:bg-slate-50"} ${unmatched ? "bg-red-50/40" : ""}`}
                      data-testid={`dqi-preview-row-${i}`}
                    >
                      <td className="text-center px-2 py-2">
                        <Checkbox
                          checked={!skipped}
                          onCheckedChange={() => toggleSkip(i)}
                          disabled={unmatched && !createUnmatched}
                          data-testid={`dqi-apply-checkbox-${i}`}
                        />
                      </td>
                      <td className="px-3 py-2 font-semibold">{row.source_name}</td>
                      <td className="px-3 py-2">
                        {row.employee_name || <span className="text-red-700 font-mono text-xs uppercase tracking-[0.12em]">{t("Needs Employee Record")}</span>}
                        {row.employee_trade && <div className="text-xs text-slate-500">{row.employee_trade}</div>}
                      </td>
                      <td className="px-3 py-2 text-xs font-mono text-slate-700">{row.match_method}</td>
                      <td className="px-3 py-2 text-center">
                        <Badge variant="outline" className={`${CONFIDENCE_PILL[row.match_confidence]} text-[10px] uppercase font-mono`}>
                          {t(row.match_confidence)}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-xs">
                        {Object.keys(row.fields_to_update || {}).length === 0 ? (
                          <span className="text-slate-400">—</span>
                        ) : (
                          <div className="space-y-0.5">
                            {Object.entries(row.diff || {}).map(([f, ch]) => (
                              <div key={f} className="font-mono">
                                <span className="text-slate-500">{f}:</span> <span className="text-slate-400 line-through">{fmtVal(ch.before)}</span> <ArrowRight className="inline w-3 h-3 text-purple-600" /> <span className="font-bold text-emerald-700">{fmtVal(ch.after)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-2 text-xs">
                        {(row.warnings || []).map((w, j) => (
                          <div key={j} className="text-amber-700 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" /> {t(w)}
                          </div>
                        ))}
                        {nochange && <div className="text-cyan-700 text-xs">{t("No change")}</div>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>

          {summary.unmatched > 0 && (
            <Card className="p-3 mb-4 border-2 border-amber-300 bg-amber-50/60">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <Checkbox
                  checked={createUnmatched}
                  onCheckedChange={(v) => setCreateUnmatched(!!v)}
                  data-testid="dqi-create-unmatched"
                />
                <ShieldAlert className="w-4 h-4 text-amber-700" />
                <span>
                  <strong>{t("Create minimal employee records for unmatched rows")}</strong>
                  <div className="text-xs text-slate-600 mt-0.5">
                    {t("Off by default. When ON, unmatched names are added to the directory with only their name + active status — driver fields applied per source row. No phone, email, or trade is invented.")}
                  </div>
                </span>
              </label>
            </Card>
          )}

          <div className="flex flex-wrap gap-3 items-center justify-end" data-testid="dqi-apply-strip">
            <div className="text-xs text-slate-700 font-mono uppercase tracking-[0.12em] flex-1">
              {willUpdate} {t("to update")} · {willCreate} {t("to create")} · {willSkip} {t("to skip")}
            </div>
            <Button variant="outline" onClick={reset} disabled={applyLoading}>{t("Cancel")}</Button>
            <Button
              onClick={handleApply}
              disabled={applyLoading || (willUpdate === 0 && willCreate === 0)}
              className="bg-emerald-700 hover:bg-emerald-800 text-white"
              data-testid="dqi-apply-btn"
            >
              {applyLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
              {t("Apply Driver Updates")}
            </Button>
          </div>
        </>
      )}

      {/* STEP 3: RESULT */}
      {result && (
        <Card className="p-6 mb-5 border-2 border-emerald-400 bg-emerald-50/40" data-testid="dqi-result-card">
          <div className="flex flex-col items-center text-center gap-3">
            <CheckCircle2 className="w-12 h-12 text-emerald-700" />
            <div className="font-bold text-xl text-emerald-900">{t("Driver updates applied")}</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mt-2 w-full max-w-3xl">
              {[
                ["Updated", result.summary?.updated || 0, "bg-emerald-100 border-emerald-300 text-emerald-900"],
                ["Created", result.summary?.created || 0, "bg-cyan-100 border-cyan-300 text-cyan-900"],
                ["Skipped", result.summary?.skipped || 0, "bg-slate-100 border-slate-300 text-slate-700"],
                ["No Change", result.summary?.no_change || 0, "bg-purple-100 border-purple-300 text-purple-900"],
                ["Errors", result.summary?.errors || 0, "bg-red-100 border-red-300 text-red-900"],
              ].map(([label, n, cls]) => (
                <div key={label} className={`px-2 py-2 rounded border-2 ${cls}`}>
                  <div className="text-xl font-bold">{n}</div>
                  <div className="text-[10px] font-mono uppercase tracking-[0.15em] mt-1">{t(label)}</div>
                </div>
              ))}
            </div>
            {(result.errors || []).length > 0 && (
              <div className="mt-3 text-left w-full max-w-3xl">
                <div className="text-xs uppercase font-mono tracking-[0.15em] text-red-700 mb-1">{t("Errors")}</div>
                <div className="bg-white border-2 border-red-200 rounded p-3 text-xs space-y-1 font-mono">
                  {result.errors.map((e, i) => (<div key={i}>{e.name || e.employee_id}: {e.error}</div>))}
                </div>
              </div>
            )}
            <div className="mt-2 flex gap-3">
              <Button variant="outline" onClick={reset} data-testid="dqi-another-btn">{t("Import Another File")}</Button>
              <Button
                onClick={() => window.location.assign("/hr/driver-qualification")}
                className="bg-purple-700 hover:bg-purple-800 text-white"
                data-testid="dqi-go-dashboard-btn"
              >
                {t("Go to Driver Qualification")}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* AUDIT HISTORY */}
      <Card className="p-4" data-testid="dqi-audit-card">
        <div className="flex items-center gap-2 mb-3">
          <History className="w-4 h-4 text-slate-700" />
          <div className="font-bold text-slate-900">{t("Import Audit History")}</div>
        </div>
        {auditLoading ? (
          <div className="text-center py-6"><Loader2 className="w-5 h-5 mx-auto animate-spin text-slate-400" /></div>
        ) : auditList.length === 0 ? (
          <div className="text-center py-6 text-sm text-slate-500" data-testid="dqi-audit-empty">{t("No imports yet. Your first import will appear here.")}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[900px]">
              <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                <tr>
                  <th className="text-left px-3 py-2">{t("When")}</th>
                  <th className="text-left px-3 py-2">{t("File")}</th>
                  <th className="text-left px-3 py-2">{t("By")}</th>
                  <th className="text-center px-3 py-2">{t("Role")}</th>
                  <th className="text-right px-3 py-2">{t("Rows")}</th>
                  <th className="text-right px-3 py-2">{t("Updated")}</th>
                  <th className="text-right px-3 py-2">{t("Created")}</th>
                  <th className="text-right px-3 py-2">{t("Skipped")}</th>
                  <th className="text-right px-3 py-2">{t("Errors")}</th>
                </tr>
              </thead>
              <tbody>
                {auditList.map((a) => (
                  <tr key={a.id} className="border-t border-slate-100" data-testid={`dqi-audit-row-${a.id}`}>
                    <td className="px-3 py-2 text-xs font-mono">{(a.ts || "").slice(0, 16).replace("T", " ")}</td>
                    <td className="px-3 py-2 font-semibold">{a.file_name}</td>
                    <td className="px-3 py-2 text-xs">{a.uploaded_by}</td>
                    <td className="px-3 py-2 text-center text-xs">
                      <Badge variant="outline" className="font-mono text-[10px] uppercase">{a.uploaded_by_role}</Badge>
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs">{a.row_count}</td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-emerald-700 font-bold">{a.updated_count}</td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-cyan-700">{a.created_count || 0}</td>
                    <td className="px-3 py-2 text-right font-mono text-xs text-slate-500">{a.skipped_count}</td>
                    <td className={`px-3 py-2 text-right font-mono text-xs ${(a.errors_count || 0) > 0 ? "text-red-700 font-bold" : "text-slate-400"}`}>{a.errors_count || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </HrPageShell>
  );
}
