import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import {
  CheckCircle2, FileText, Inbox, ShieldCheck, Upload, UserCheck, ArrowLeft,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import {
  createRecord, fetchVocabulary, uploadOriginalFile,
} from "@/lib/employeeRecordsApi";
import { EmployeeCombo } from "@/components/EmployeeCombo";
import HrPageShell from "@/components/HrPageShell";
import { WorkflowCoachingDisclosure } from "@/components/WorkflowCoachingDisclosure";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const LANE_LABEL = {
  hr: "HR",
  safety: "Safety",
  asset: "Asset Administration",
  corporate_import: "Corporate Import",
  vendor: "Vendor (HR/Admin)",
};

const LANE_STYLE = {
  hr: "border-purple-300 bg-purple-50 text-purple-900",
  safety: "border-cyan-300 bg-cyan-50 text-cyan-900",
  asset: "border-orange-300 bg-orange-50 text-orange-900",
  corporate_import: "border-slate-300 bg-slate-50 text-slate-900",
  vendor: "border-emerald-300 bg-emerald-50 text-emerald-900",
};

const CONTROL_CLASS = "wp17-focus-ring mt-2 flex h-[3rem] w-full rounded-[1rem] border border-[color:var(--border-bold)] bg-white px-3.5 text-sm text-[color:var(--ink-strong)] disabled:opacity-50";
const TEXTAREA_CLASS = "wp17-focus-ring mt-2 w-full rounded-[1rem] border border-[color:var(--border-bold)] bg-white px-3.5 py-2.5 text-sm text-[color:var(--ink-strong)]";

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function HistoricalRecordsIntake() {
  const navigate = useNavigate();
  const { t } = useT();
  const [params] = useSearchParams();
  const preEmployeeId = params.get("employee_id") || "";

  const [vocab, setVocab] = useState(null);
  const [vocabErr, setVocabErr] = useState(null);
  const [lane, setLane] = useState("");
  const [recordType, setRecordType] = useState("");
  const [employeeId, setEmployeeId] = useState(preEmployeeId);
  const [employeeName, setEmployeeName] = useState("");
  const [vendorName, setVendorName] = useState("");
  const [vendorId, setVendorId] = useState("");
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
      .then((payload) => {
        setVocab(payload);
        if (payload?.allowed_lanes_for_actor?.length) {
          setLane((prev) => prev || payload.allowed_lanes_for_actor[0]);
        }
      })
      .catch((e) => setVocabErr(String(e.message || e)));
  }, []);

  const recordTypeOptions = useMemo(() => {
    if (!lane || !vocab) return [];
    return vocab.record_types_by_lane?.[lane] || [];
  }, [lane, vocab]);

  const canSubmit = Boolean(lane && recordType && file && !busy);

  const onFilePick = useCallback((e) => {
    const picked = e.target.files?.[0] || null;
    setFile(picked || null);
  }, []);

  const onSubmit = useCallback(async () => {
    if (!file) {
      toast.error(t("Attach a file first."));
      return;
    }
    if (!lane) {
      toast.error(t("Choose an ownership lane."));
      return;
    }
    if (!recordType) {
      toast.error(t("Choose a record type."));
      return;
    }

    setBusy(true);
    try {
      const upload = await uploadOriginalFile({ lane, file });
      const tags = tagsRaw.split(",").map((value) => value.trim()).filter(Boolean);
      const result = await createRecord({
        ownership_lane: lane,
        record_type: recordType,
        entity_kind: lane === "vendor" ? "vendor" : "employee",
        employee_id: lane === "vendor" ? null : (employeeId || null),
        employee_name_snapshot: lane === "vendor" ? null : (employeeName || null),
        vendor_id: lane === "vendor" ? (vendorId || null) : null,
        vendor_name: lane === "vendor" ? (vendorName || null) : null,
        effective_date: effectiveDate || null,
        notes,
        tags,
        related_incident_case_id: relatedIncidentCaseId || null,
        related_asset_id: relatedAssetId || null,
        source_file_ref: upload.source_file_ref,
        source_file_name: upload.source_file_name,
        source_file_hash: upload.source_file_hash,
      });
      toast.success(t("Record staged for approval."));
      setLastCreated(result.record);
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
  }, [employeeId, employeeName, effectiveDate, file, lane, notes, recordType, relatedAssetId, relatedIncidentCaseId, t, tagsRaw, vendorId, vendorName]);

  if (vocabErr) {
    return (
      <HrPageShell title="Add people record" kicker="HR · Historical record intake">
        <Card className="mx-auto max-w-xl border-red-200" data-testid="historical-records-intake">
          <CardHeader>
            <CardTitle className="text-red-900">{t("Could not load record options")}</CardTitle>
            <CardDescription>{vocabErr}</CardDescription>
          </CardHeader>
        </Card>
      </HrPageShell>
    );
  }

  return (
    <HrPageShell title="Add people record" kicker="HR · Historical record intake">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6" data-testid="historical-records-intake">
        <Card data-testid="intake-header">
          <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-2">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Historical records")} · {t("Single record intake")}
              </div>
              <CardTitle>{t("Bring one older people record into the review flow")}</CardTitle>
              <CardDescription className="max-w-3xl">
                {t("Attach the original file, link it to the right person or company record, and send it to the review queue before it becomes part of the permanent record.")}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={() => navigate(-1)} data-testid="intake-back">
                <ArrowLeft className="h-4 w-4" /> {t("Back")}
              </Button>
              <Button type="button" variant="secondary" onClick={() => navigate("/hr/historical-records/queue")} data-testid="intake-open-queue">
                <Inbox className="h-4 w-4" /> {t("Open review queue")}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1 rounded-full border border-emerald-300 bg-emerald-100 px-3 py-1 font-semibold text-emerald-900">
                <ShieldCheck className="h-3 w-3" /> {t("Reviewed by a person before approval")}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full border border-slate-300 bg-slate-100 px-3 py-1 font-semibold text-slate-800">
                {t("No automatic scanning")} · {t("No automatic sorting")} · {t("No guesswork")}
              </span>
            </div>
          </CardContent>
        </Card>

        <section className="grid gap-6 lg:grid-cols-2" data-testid="intake-guidance">
          <Card data-testid="intake-what-you-can-upload">
            <CardHeader>
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Accepted records")}</div>
              <CardTitle>{t("What can you bring in here?")}</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="flex flex-wrap gap-1.5">
                {[
                  "Employee Write-Up", "Training Certificate", "Incident Report",
                  "Safety Document", "PPE Issue Record", "Tool Issue Record",
                  "Phone / Tablet / iPad", "Survey Equipment",
                  "Driver Qualification", "Policy Acknowledgement",
                  "Evaluation", "Recognition", "Termination", "Other",
                ].map((label) => (
                  <span key={label} className="inline-flex items-center rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-700">
                    {t(label)}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>

          <WorkflowCoachingDisclosure
            eyebrow={t("How this works")}
            title={t("Three steps to a clean record")}
            testIdPrefix="intake-how-it-works"
            blocks={[
              {
                tone: "slate",
                label: t("Attach the file"),
                body: t("Bring in the original record exactly as it was saved or scanned."),
                testId: "intake-how-it-works-step-1",
              },
              {
                tone: "sky",
                label: t("Link the right person"),
                body: t("Choose the employee, company, or related job detail before approval."),
                testId: "intake-how-it-works-step-2",
              },
              {
                tone: "emerald",
                label: t("Send it for review"),
                body: t("The review queue is the final stop before it becomes part of the permanent record."),
                testId: "intake-how-it-works-step-3",
              },
            ]}
            defaultOpen={false}
          />
        </section>

        <Card data-testid="intake-form">
          <CardHeader>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Record details")}</div>
            <CardTitle>{t("Set the record up for clean approval")}</CardTitle>
            <CardDescription>{t("Choose the right lane, record type, and person link before you send the file to review.")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-0">
            <div>
              <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Ownership lane")} <span className="text-red-600">*</span>
              </label>
              <div className="mt-2 flex flex-wrap gap-2" data-testid="intake-lane-picker">
                {(vocab?.allowed_lanes_for_actor || []).map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => { setLane(value); setRecordType(""); }}
                    className={`wp17-focus-ring rounded-full border px-3 py-1.5 text-sm font-semibold transition-colors ${lane === value ? LANE_STYLE[value] : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}
                    data-testid={`intake-lane-${value}`}
                  >
                    {t(LANE_LABEL[value] || value)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label htmlFor="intake-record-type" className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Record type")} <span className="text-red-600">*</span>
              </label>
              <select
                id="intake-record-type"
                value={recordType}
                onChange={(e) => setRecordType(e.target.value)}
                disabled={!lane}
                className={CONTROL_CLASS}
                data-testid="intake-record-type"
              >
                <option value="">{lane ? t("Select a type…") : t("Pick a lane first")}</option>
                {recordTypeOptions.map((rt) => (
                  <option key={rt} value={rt}>{rt.replace(/_/g, " ")}</option>
                ))}
              </select>
            </div>

            {lane !== "vendor" ? (
              <div>
                <label className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                  {t("Employee link")} <span className="text-slate-500">({t("required before approval")})</span>
                </label>
                <div className="mt-2" data-testid="intake-employee-combo">
                  <EmployeeCombo
                    value={employeeName}
                    onChange={(value) => setEmployeeName(value)}
                    onPick={(emp) => {
                      setEmployeeId(emp?.id || "");
                      setEmployeeName(emp?.name || "");
                    }}
                    placeholder={t("Type or pick an employee…")}
                    testId="intake-employee-picker"
                  />
                </div>
                {employeeId ? (
                  <div className="mt-1 inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-800">
                    <UserCheck className="h-3 w-3" /> {t("Linked")}: {employeeName}
                  </div>
                ) : null}
              </div>
            ) : (
              <div data-testid="intake-vendor-block">
                <label htmlFor="intake-vendor-name" className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                  {t("Company name")} <span className="text-slate-500">({t("required before approval")})</span>
                </label>
                <Input
                  id="intake-vendor-name"
                  type="text"
                  value={vendorName}
                  onChange={(e) => setVendorName(e.target.value)}
                  placeholder={t("Type the company or supplier name…")}
                  data-testid="intake-vendor-name-input"
                  className="mt-2"
                />
                <label htmlFor="intake-vendor-id" className="mt-3 block font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                  {t("Company ID")} <span className="text-slate-500">({t("optional — from supplier records")})</span>
                </label>
                <Input
                  id="intake-vendor-id"
                  type="text"
                  value={vendorId}
                  onChange={(e) => setVendorId(e.target.value)}
                  placeholder={t("Company ID from supplier records (optional)")}
                  data-testid="intake-vendor-id-input"
                  className="mt-2"
                />
                <p className="mt-2 text-xs text-emerald-900" data-testid="intake-vendor-owner-note">
                  {t("Company documents stay with HR and administration for future review threads.")}
                </p>
              </div>
            )}

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label htmlFor="intake-effective-date" className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Effective date")}</label>
                <Input
                  id="intake-effective-date"
                  type="date"
                  value={effectiveDate}
                  onChange={(e) => setEffectiveDate(e.target.value)}
                  className="mt-2"
                  data-testid="intake-effective-date"
                />
              </div>
              {lane === "safety" ? (
                <div>
                  <label htmlFor="intake-related-incident" className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Incident case number")}</label>
                  <Input
                    id="intake-related-incident"
                    type="text"
                    placeholder="e.g. 2026-00003"
                    value={relatedIncidentCaseId}
                    onChange={(e) => setRelatedIncidentCaseId(e.target.value)}
                    className="mt-2 font-mono"
                    data-testid="intake-related-incident"
                  />
                </div>
              ) : null}
              {lane === "asset" ? (
                <div>
                  <label htmlFor="intake-related-asset" className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Asset or unit number")}</label>
                  <Input
                    id="intake-related-asset"
                    type="text"
                    placeholder="e.g. TRK-142"
                    value={relatedAssetId}
                    onChange={(e) => setRelatedAssetId(e.target.value)}
                    className="mt-2 font-mono"
                    data-testid="intake-related-asset"
                  />
                </div>
              ) : null}
            </div>

            <div>
              <label htmlFor="intake-tags" className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
                {t("Tags")} <span className="text-slate-500">({t("comma-separated")})</span>
              </label>
              <Input
                id="intake-tags"
                type="text"
                placeholder="acknowledged, 2023, cdl"
                value={tagsRaw}
                onChange={(e) => setTagsRaw(e.target.value)}
                className="mt-2"
                data-testid="intake-tags"
              />
            </div>

            <div>
              <label htmlFor="intake-notes" className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">{t("Notes")}</label>
              <textarea
                id="intake-notes"
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className={TEXTAREA_CLASS}
                data-testid="intake-notes"
                placeholder={t("Optional context for the reviewer.")}
              />
            </div>

            <div className="rounded-[1.5rem] border border-dashed border-[color:var(--border-hairline)] bg-[color:var(--surface-muted)] p-4" data-testid="intake-file-drop">
              <Button type="button" asChild data-testid="intake-file-attach-button">
                <label htmlFor="intake-file-input" className="cursor-pointer">
                  <Upload className="h-4 w-4" /> {t("Attach original file")}
                </label>
              </Button>
              <input
                id="intake-file-input"
                type="file"
                className="hidden"
                onChange={onFilePick}
                accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.heic,.heif,.doc,.docx,.xls,.xlsx,.xlsm,.csv,.txt,.rtf"
                data-testid="intake-file-input"
              />
              {file ? (
                <div className="mt-3 inline-flex items-center gap-2 rounded-[1rem] border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800" data-testid="intake-file-selected">
                  <FileText className="h-3.5 w-3.5" />
                  <span className="font-mono">{file.name}</span>
                  <span className="text-xs text-slate-500">· {formatBytes(file.size)}</span>
                </div>
              ) : (
                <p className="mt-2 text-xs text-slate-500">
                  {t("Supported: PDF, image files, Word files, spreadsheet files, CSV, TXT, and RTF. Max 25 MB.")}
                </p>
              )}
            </div>

            <div className="pt-2">
              <Button type="button" onClick={onSubmit} disabled={!canSubmit} data-testid="intake-submit">
                <Upload className="h-4 w-4" /> {busy ? t("Uploading…") : t("Send to review")}
              </Button>
            </div>
          </CardContent>
        </Card>

        {lastCreated ? (
          <Card className="border-emerald-300 bg-emerald-50" data-testid="intake-last-created">
            <CardContent className="pt-5">
              <div className="inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-800">
                <CheckCircle2 className="h-3.5 w-3.5" /> {t("Ready for review")}
              </div>
              <div className="mt-1 text-sm text-emerald-900">
                {t("Record")} <span className="font-mono">{lastCreated.id.slice(0, 8)}</span>
                {" · "}{lastCreated.record_type.replace(/_/g, " ")}
                {" · "}{t("status")}: <span className="font-mono">{lastCreated.approval_status.replace(/_/g, " ")}</span>
              </div>
              <Button type="button" variant="ghost" onClick={() => navigate("/hr/historical-records/queue")} className="mt-3" data-testid="intake-goto-queue">
                <Inbox className="h-4 w-4" /> {t("Open review queue")}
              </Button>
            </CardContent>
          </Card>
        ) : null}
      </div>
    </HrPageShell>
  );
}