// Track 19.21b · Historical Records Intake page
// -----------------------------------------------------------------
// Manual, HR-gated intake for legacy paper/digital employee records.
//
// Rules (per problem statement):
//   * HR uploads to any lane. Safety → Safety lane. Asset Admin → Asset lane.
//   * Original file preserved (SHA-256 hash stored).
//   * Manual employee link required before approval.
//   * NO OCR / NO AI classification / NO fuzzy matching.
//   * Every upload writes an audit trail row on submit.
//
// Route: /hr/historical-records/intake
// Query params: ?employee_id=<id>  → seeds the employee field.
//
// Zero drift: additive. Reuses `EmployeeCombo` for employee picking.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import {
  ArrowLeft, CheckCircle2, FileText, Inbox, ShieldCheck,
  Upload, UserCheck,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import {
  createRecord, fetchVocabulary, uploadOriginalFile,
} from "@/lib/employeeRecordsApi";
import { EmployeeCombo } from "@/components/EmployeeCombo";

const LANE_LABEL = {
  hr: "HR",
  safety: "Safety",
  asset: "Asset Administration",
  corporate_import: "Corporate Import",
};

const LANE_STYLE = {
  hr:               "border-purple-300 bg-purple-50 text-purple-900",
  safety:           "border-cyan-300 bg-cyan-50 text-cyan-900",
  asset:            "border-orange-300 bg-orange-50 text-orange-900",
  corporate_import: "border-slate-300 bg-slate-50 text-slate-900",
};

function _fmtBytes(b) {
  if (!b && b !== 0) return "";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(2)} MB`;
}

export default function HistoricalRecordsIntake() {
  const navigate = useNavigate();
  const { t } = useT();
  const [params] = useSearchParams();
  const preEmployeeId = params.get("employee_id") || "";

  const [vocab, setVocab] = useState(null);
  const [vocabErr, setVocabErr] = useState(null);

  // Form state
  const [lane, setLane] = useState("");
  const [recordType, setRecordType] = useState("");
  const [employeeId, setEmployeeId] = useState(preEmployeeId);
  const [employeeName, setEmployeeName] = useState("");
  const [effectiveDate, setEffectiveDate] = useState("");
  const [notes, setNotes] = useState("");
  const [tagsRaw, setTagsRaw] = useState("");
  const [relatedIncidentCaseId, setRelatedIncidentCaseId] = useState("");
  const [relatedAssetId, setRelatedAssetId] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [lastCreated, setLastCreated] = useState(null);

  useEffect(() => {
    fetchVocabulary()
      .then((v) => {
        setVocab(v);
        // Default lane to first allowed for the actor.
        if (v?.allowed_lanes_for_actor?.length) {
          setLane((prev) => prev || v.allowed_lanes_for_actor[0]);
        }
      })
      .catch((e) => setVocabErr(String(e.message || e)));
  }, []);

  const recordTypeOptions = useMemo(() => {
    if (!lane || !vocab) return [];
    return vocab.record_types_by_lane?.[lane] || [];
  }, [lane, vocab]);

  const canSubmit = !!(lane && recordType && file && !busy);

  const onFilePick = useCallback((e) => {
    const f = e.target.files?.[0] || null;
    setFile(f || null);
  }, []);

  const onSubmit = useCallback(async () => {
    if (!file) { toast.error(t("Attach a file first.")); return; }
    if (!lane) { toast.error(t("Choose an ownership lane.")); return; }
    if (!recordType) { toast.error(t("Choose a record type.")); return; }
    setBusy(true);
    try {
      // 1. Upload original file (preserved with hash).
      const up = await uploadOriginalFile({ lane, file });
      // 2. Create staged record — never auto-approved.
      const tags = tagsRaw
        .split(",").map((s) => s.trim()).filter(Boolean);
      const rec = await createRecord({
        ownership_lane: lane,
        record_type: recordType,
        employee_id: employeeId || null,
        employee_name_snapshot: employeeName || null,
        effective_date: effectiveDate || null,
        notes,
        tags,
        related_incident_case_id: relatedIncidentCaseId || null,
        related_asset_id: relatedAssetId || null,
        source_file_ref: up.source_file_ref,
        source_file_name: up.source_file_name,
        source_file_hash: up.source_file_hash,
      });
      toast.success(t("Record staged for approval."));
      setLastCreated(rec.record);
      // Reset the file input, keep employee for batch uploads.
      setFile(null);
      const input = document.getElementById("intake-file-input");
      if (input) input.value = "";
      setEffectiveDate("");
      setNotes("");
      setTagsRaw("");
      setRelatedIncidentCaseId("");
      setRelatedAssetId("");
    } catch (e) {
      toast.error(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }, [file, lane, recordType, employeeId, employeeName, effectiveDate,
      notes, tagsRaw, relatedIncidentCaseId, relatedAssetId, t]);

  if (vocabErr) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="max-w-md p-6 rounded-xl border-2 border-red-300 bg-white">
          <div className="font-display text-lg font-black text-red-900"
               data-testid="intake-vocab-error">
            {t("Could not load intake vocabulary")}
          </div>
          <p className="mt-2 text-sm text-slate-600">{vocabErr}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="historical-records-intake">
      <div className="max-w-4xl mx-auto p-4 sm:p-6 space-y-4">
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
            data-testid="intake-back"
          >
            <ArrowLeft className="w-4 h-4" /> {t("Back")}
          </button>
          <button
            type="button"
            onClick={() => navigate("/hr/historical-records/queue")}
            className="inline-flex items-center gap-2 rounded-md border-2 border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-800 hover:bg-slate-100"
            data-testid="intake-open-queue"
          >
            <Inbox className="w-3.5 h-3.5" /> {t("Open Review Queue")}
          </button>
        </div>

        {/* Header */}
        <header className="rounded-xl border-2 border-slate-300 bg-white p-4 sm:p-5"
                data-testid="intake-header">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("Historical Records")} · {t("Manual Intake")}
          </div>
          <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
            {t("Add a Historical Record")}
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            {t("Upload a legacy paper/digital record and classify it manually. Nothing goes live on an employee's profile until HR (or the lane owner) approves it in the queue.")}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1 rounded-md bg-emerald-100 border border-emerald-300 px-2 py-1 text-emerald-900 font-semibold">
              <ShieldCheck className="w-3 h-3" /> {t("Manual classification only")}
            </span>
            <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 border border-slate-300 px-2 py-1 text-slate-800 font-semibold">
              {t("No OCR")} · {t("No AI")} · {t("No fuzzy matching")}
            </span>
          </div>
        </header>

        {/* Form */}
        <section className="rounded-xl border-2 border-slate-300 bg-white p-4 sm:p-5 space-y-4"
                 data-testid="intake-form">
          {/* Ownership lane */}
          <div>
            <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
              {t("Ownership lane")} <span className="text-red-600">*</span>
            </label>
            <div className="mt-2 flex flex-wrap gap-2" data-testid="intake-lane-picker">
              {(vocab?.allowed_lanes_for_actor || []).map((l) => (
                <button
                  key={l}
                  type="button"
                  onClick={() => { setLane(l); setRecordType(""); }}
                  className={`px-3 py-1.5 rounded-md text-sm font-semibold border-2 transition-colors ${
                    lane === l ? LANE_STYLE[l] : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                  }`}
                  data-testid={`intake-lane-${l}`}
                >
                  {t(LANE_LABEL[l] || l)}
                </button>
              ))}
            </div>
          </div>

          {/* Record type */}
          <div>
            <label htmlFor="intake-record-type"
                   className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
              {t("Record type")} <span className="text-red-600">*</span>
            </label>
            <select
              id="intake-record-type"
              value={recordType}
              onChange={(e) => setRecordType(e.target.value)}
              disabled={!lane}
              className="mt-2 w-full rounded-md border-2 border-slate-300 bg-white px-3 py-2 text-sm font-mono disabled:opacity-50"
              data-testid="intake-record-type"
            >
              <option value="">{lane ? t("Select a type…") : t("Pick a lane first")}</option>
              {recordTypeOptions.map((rt) => (
                <option key={rt} value={rt}>{rt.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>

          {/* Employee */}
          <div>
            <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
              {t("Employee link")} <span className="text-slate-500">({t("required before approval")})</span>
            </label>
            <div className="mt-2" data-testid="intake-employee-combo">
              <EmployeeCombo
                value={employeeName}
                onChange={(v) => setEmployeeName(v)}
                onPick={(emp) => {
                  setEmployeeId(emp?.id || "");
                  setEmployeeName(emp?.name || "");
                }}
                placeholder={t("Type or pick an employee…")}
                testId="intake-employee-picker"
              />
            </div>
            {employeeId && (
              <div className="mt-1 inline-flex items-center gap-1.5 text-xs text-emerald-800 font-semibold">
                <UserCheck className="w-3 h-3" /> {t("Linked")}: {employeeName}
              </div>
            )}
          </div>

          {/* Effective date + related IDs (lane-specific) */}
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor="intake-effective-date"
                     className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Effective date")}
              </label>
              <input
                id="intake-effective-date"
                type="date"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                className="mt-2 w-full rounded-md border-2 border-slate-300 bg-white px-3 py-2 text-sm"
                data-testid="intake-effective-date"
              />
            </div>
            {lane === "safety" && (
              <div>
                <label htmlFor="intake-incident-case"
                       className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                  {t("Link to Incident Case ID")}
                </label>
                <input
                  id="intake-incident-case"
                  type="text"
                  placeholder="e.g. 2026-00003"
                  value={relatedIncidentCaseId}
                  onChange={(e) => setRelatedIncidentCaseId(e.target.value)}
                  className="mt-2 w-full rounded-md border-2 border-slate-300 bg-white px-3 py-2 text-sm font-mono"
                  data-testid="intake-related-incident"
                />
              </div>
            )}
            {lane === "asset" && (
              <div>
                <label htmlFor="intake-asset-id"
                       className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                  {t("Link to Asset ID / Unit #")}
                </label>
                <input
                  id="intake-asset-id"
                  type="text"
                  placeholder="e.g. TRK-142 or asset UUID"
                  value={relatedAssetId}
                  onChange={(e) => setRelatedAssetId(e.target.value)}
                  className="mt-2 w-full rounded-md border-2 border-slate-300 bg-white px-3 py-2 text-sm font-mono"
                  data-testid="intake-related-asset"
                />
              </div>
            )}
          </div>

          {/* Tags + notes */}
          <div>
            <label htmlFor="intake-tags"
                   className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
              {t("Tags")} <span className="text-slate-500">(comma-separated)</span>
            </label>
            <input
              id="intake-tags"
              type="text"
              placeholder="acknowledged, 2023, cdl"
              value={tagsRaw}
              onChange={(e) => setTagsRaw(e.target.value)}
              className="mt-2 w-full rounded-md border-2 border-slate-300 bg-white px-3 py-2 text-sm"
              data-testid="intake-tags"
            />
          </div>
          <div>
            <label htmlFor="intake-notes"
                   className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
              {t("Notes")}
            </label>
            <textarea
              id="intake-notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-2 w-full rounded-md border-2 border-slate-300 bg-white px-3 py-2 text-sm"
              data-testid="intake-notes"
              placeholder={t("Optional context for the reviewer.")}
            />
          </div>

          {/* File */}
          <div className="rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-4"
               data-testid="intake-file-drop">
            <label htmlFor="intake-file-input"
                   className="inline-flex items-center gap-2 rounded-md bg-slate-900 text-white px-3 py-1.5 text-sm font-semibold cursor-pointer hover:bg-slate-800">
              <Upload className="w-3.5 h-3.5" /> {t("Attach original file")}
            </label>
            <input
              id="intake-file-input"
              type="file"
              className="hidden"
              onChange={onFilePick}
              accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.heic,.heif,.doc,.docx,.xls,.xlsx,.xlsm,.csv,.txt,.rtf"
              data-testid="intake-file-input"
            />
            {file ? (
              <div className="mt-3 inline-flex items-center gap-2 rounded-md bg-white border border-slate-300 px-3 py-1.5 text-sm text-slate-800"
                   data-testid="intake-file-selected">
                <FileText className="w-3.5 h-3.5" />
                <span className="font-mono">{file.name}</span>
                <span className="text-xs text-slate-500">· {_fmtBytes(file.size)}</span>
              </div>
            ) : (
              <p className="mt-2 text-xs text-slate-500">
                {t("Supported: PDF, images, DOC/DOCX, XLS/XLSX/XLSM, CSV, TXT, RTF. Max 25 MB.")}
              </p>
            )}
          </div>

          {/* Submit */}
          <div className="pt-2">
            <button
              type="button"
              onClick={onSubmit}
              disabled={!canSubmit}
              className="inline-flex items-center gap-2 rounded-md bg-purple-700 text-white px-4 py-2 text-sm font-semibold hover:bg-purple-800 disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="intake-submit"
            >
              <Upload className="w-3.5 h-3.5" /> {busy ? t("Uploading…") : t("Stage for Approval")}
            </button>
          </div>
        </section>

        {/* Last created flash */}
        {lastCreated && (
          <div className="rounded-xl border-2 border-emerald-300 bg-emerald-50 p-4"
               data-testid="intake-last-created">
            <div className="inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-800">
              <CheckCircle2 className="w-3.5 h-3.5" /> {t("Staged")}
            </div>
            <div className="mt-1 text-sm text-emerald-900">
              {t("Record")} <span className="font-mono">{lastCreated.id.slice(0, 8)}</span>{" "}
              · {lastCreated.record_type.replace(/_/g, " ")}{" "}
              · {t("state")}: <span className="font-mono">{lastCreated.approval_status}</span>
            </div>
            <button
              type="button"
              onClick={() => navigate("/hr/historical-records/queue")}
              className="mt-2 inline-flex items-center gap-1.5 text-emerald-800 font-semibold text-sm hover:underline"
              data-testid="intake-goto-queue"
            >
              <Inbox className="w-3.5 h-3.5" /> {t("Review in Queue")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
