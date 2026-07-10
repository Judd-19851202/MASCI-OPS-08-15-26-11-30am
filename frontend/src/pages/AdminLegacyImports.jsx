// AdminLegacyImports.jsx — Phase A · Foundation reconciliation queue.
// Phase A · Admin scope. HR/Safety can use the same backend endpoints when
// operator activates per-portal reconciliation UI in Phase B+.
//
// Operational philosophy: side-by-side scan + extracted fields always
// visible; reviewer must literally see the original before approving.
import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Upload, FileText, CheckCircle2, XCircle, Eye, Clock, AlertTriangle, ShieldAlert, Users, Wrench, Briefcase, Copy, ExternalLink, RotateCw } from "lucide-react";
import { api } from "@/lib/api";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";

const DOCUMENT_TYPES = [
  "equipment_checkout", "training_record", "osha_card", "toolbox_talk",
  "fit_test", "medical_card", "cdl_license", "certification",
  "safety_orientation", "signed_acknowledgement", "write_up",
  "onboarding_packet", "hr_record", "qualification_record", "unknown",
];

const STATUS_PILL = {
  uploaded: { color: "bg-slate-200 text-slate-700", icon: Clock, label: "Uploaded" },
  ocr_in_progress: { color: "bg-amber-100 text-amber-800", icon: Clock, label: "OCR Running" },
  ocr_failed: { color: "bg-red-100 text-red-800", icon: AlertTriangle, label: "OCR Failed" },
  needs_review: { color: "bg-indigo-100 text-indigo-800", icon: Eye, label: "Needs Review" },
  approved: { color: "bg-emerald-100 text-emerald-800", icon: CheckCircle2, label: "Approved" },
  promoted: { color: "bg-emerald-200 text-emerald-900", icon: CheckCircle2, label: "Promoted" },
  rejected: { color: "bg-slate-300 text-slate-700", icon: XCircle, label: "Rejected" },
};

const friendlyError = (e, fallback) =>
  e?.response?.data?.detail || e?.message || fallback || "Something went wrong";

export default function AdminLegacyImports() {
  const [meta, setMeta] = useState(null);
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("needs_review");
  const [loading, setLoading] = useState(false);
  const [openId, setOpenId] = useState(null);

  const loadMeta = async () => {
    try {
      const { data } = await api.get("/legacy-imports/_meta");
      setMeta(data);
    } catch (e) {
      toast.error(friendlyError(e, "Could not load meta"));
    }
  };

  const loadList = useCallback(async () => {
    setLoading(true);
    try {
      const q = filter === "all" ? "" : `?status=${filter}`;
      const { data } = await api.get(`/legacy-imports${q}`);
      setItems(data.items || []);
    } catch (e) {
      toast.error(friendlyError(e, "Could not load imports"));
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { loadMeta(); }, []);
  useEffect(() => { loadList(); }, [loadList]);

  const counts = items.reduce((acc, x) => {
    acc[x.status] = (acc[x.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <LegacyAdminModernShell
      title="Historical Records"
      subtitle="OCR/AI-assisted reconciliation queue · humans approve every promotion."
      breadcrumb={[
        { label: "Maintenance", to: "/admin/maintenance" },
        { label: "Historical Records" },
      ]}
      testidPrefix="legacy-imports"
    >
      <div className="max-w-6xl mx-auto" data-testid="legacy-imports-page">
        <div className="flex items-start justify-between flex-wrap gap-3 mb-1">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-indigo-700 font-black">
              {meta?.phase === "B" ? "Equipment Checkout Pilot" : "Reconciliation Queue"}
            </div>
            <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              Historical Records · Reconciliation Queue
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              OCR/AI assists — humans approve. Imported records become live
              operational records only after human review. Equipment Checkout
              is the first activated document type; other types remain
              staging-only until operator activation.
            </p>
          </div>
          {meta && (
            <div className="text-xs font-mono text-slate-500 bg-white border border-slate-200 rounded-md px-3 py-2 min-w-[200px]">
              <div>portal: <strong className="text-slate-900">{meta.upload_portal}</strong></div>
              <div>role: <strong className="text-slate-900">{meta.actor_role}</strong></div>
              <div>phase: <strong className="text-slate-900">{meta.phase}</strong></div>
              <div>active promoters: <strong className="text-slate-900">{meta.active_promoters?.join(", ") || "none yet"}</strong></div>
              {meta.equipment_checkout_pilot_cap != null && (
                <div className="mt-1 pt-1 border-t border-slate-100" data-testid="legacy-imports-pilot-cap">
                  pilot cap (equipment_checkout):{" "}
                  <strong className="text-slate-900">
                    {meta.equipment_checkout_pilot_remaining} / {meta.equipment_checkout_pilot_cap} remaining
                  </strong>
                </div>
              )}
            </div>
          )}
        </div>

        <UploadCard meta={meta} onUploaded={loadList} />

        {/* Queue filters */}
        <div className="mt-6 flex items-center gap-2 flex-wrap" data-testid="legacy-imports-filters">
          {["needs_review", "uploaded", "ocr_in_progress", "ocr_failed", "approved", "promoted", "rejected", "all"].map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => setFilter(k)}
              className={`text-xs font-mono uppercase tracking-wide px-3 py-1.5 rounded-md border-2 transition-colors ${
                filter === k
                  ? "border-indigo-700 bg-indigo-700 text-white"
                  : "border-slate-200 bg-white text-slate-700 hover:border-slate-400"
              }`}
              data-testid={`legacy-imports-filter-${k}`}
            >
              {k.replace(/_/g, " ")}
              {counts[k] != null && filter === "all" ? ` · ${counts[k]}` : ""}
            </button>
          ))}
        </div>

        {/* List */}
        <div className="mt-4 bg-white border border-slate-200 rounded-md overflow-hidden">
          {loading && (
            <div className="px-4 py-8 text-center text-sm text-slate-500">Loading…</div>
          )}
          {!loading && items.length === 0 && (
            <div className="px-4 py-12 text-center" data-testid="legacy-imports-empty">
              <FileText className="w-8 h-8 mx-auto text-slate-300 mb-2" />
              <div className="text-sm text-slate-500">
                Nothing in the <strong>{filter.replace(/_/g, " ")}</strong> queue.
              </div>
            </div>
          )}
          {!loading && items.length > 0 && (
            <div className="divide-y divide-slate-100">
              {items.map((row) => (
                <RowCard
                  key={row.id}
                  row={row}
                  onOpen={() => setOpenId(row.id)}
                />
              ))}
            </div>
          )}
        </div>

        {openId && (
          <ReviewModal
            importId={openId}
            onClose={() => setOpenId(null)}
            onChange={loadList}
            meta={meta}
          />
        )}
      </div>
    </LegacyAdminModernShell>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────
function UploadCard({ meta, onUploaded }) {
  const [docType, setDocType] = useState("unknown");
  const [batchId, setBatchId] = useState("");
  const [busy, setBusy] = useState(false);

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("document_type", docType);
      if (batchId.trim()) fd.append("batch_id", batchId.trim());
      const { data } = await api.post("/legacy-imports/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      if (data.duplicate_of) {
        toast.warning(`Already uploaded · returning existing row ${data.duplicate_of.slice(0, 8)}`);
      } else {
        toast.success(`Uploaded · ${data.row.id.slice(0, 8)}`);
      }
      onUploaded();
    } catch (err) {
      toast.error(friendlyError(err, "Upload failed"));
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  };

  return (
    <div className="mt-5 bg-white border border-slate-200 rounded-md p-4 sm:p-5">
      <div className="flex items-start gap-3">
        <Upload className="w-5 h-5 text-indigo-700 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-bold text-sm text-slate-900">Upload a paper record</div>
          <div className="text-xs text-slate-500 mt-0.5">
            PDF · JPG · PNG · phone photos OK. Max 25 MB. Source file is permanently retained.
          </div>
          <div className="mt-3 grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4.5">
            <div className="sm:col-span-1">
              <Label className="text-[10px] font-mono uppercase tracking-wide text-slate-600">Document type</Label>
              <Select value={docType} onValueChange={setDocType}>
                <SelectTrigger className="mt-1" data-testid="legacy-imports-doc-type"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(meta?.allowed_document_types || DOCUMENT_TYPES).map((d) => (
                    <SelectItem key={d} value={d}>{d.replace(/_/g, " ")}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="sm:col-span-1">
              <Label className="text-[10px] font-mono uppercase tracking-wide text-slate-600">Batch label (optional)</Label>
              <Input
                value={batchId}
                onChange={(e) => setBatchId(e.target.value)}
                placeholder="e.g. jakes-onboarding-2019"
                className="mt-1"
                data-testid="legacy-imports-batch"
              />
            </div>
            <div className="sm:col-span-1 flex items-end">
              <label className="w-full">
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.webp,.heic"
                  onChange={onFile}
                  disabled={busy}
                  className="hidden"
                  data-testid="legacy-imports-file"
                />
                <span className="inline-flex items-center justify-center w-full h-10 px-4 rounded-md bg-indigo-700 hover:bg-indigo-800 text-white text-xs font-bold uppercase tracking-wide cursor-pointer">
                  {busy ? "Uploading…" : "Choose file"}
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function RowCard({ row, onOpen }) {
  const pill = STATUS_PILL[row.status] || STATUS_PILL.uploaded;
  const Icon = pill.icon;
  const firstFile = row.source_files?.[0];
  return (
    <button
      type="button"
      onClick={onOpen}
      className="w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors flex items-center gap-3"
      data-testid={`legacy-imports-row-${row.id}`}
    >
      <FileText className="w-5 h-5 text-slate-400 shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-bold text-sm text-slate-900 truncate">
            {firstFile?.original_name || row.id.slice(0, 8)}
          </span>
          <Badge className={`text-[10px] font-mono uppercase ${pill.color}`}>
            <Icon className="w-3 h-3 mr-1" />
            {pill.label}
          </Badge>
          <Badge className="bg-slate-100 text-slate-700 text-[10px] font-mono uppercase">
            {row.document_type.replace(/_/g, " ")}
          </Badge>
          <Badge className="bg-slate-100 text-slate-700 text-[10px] font-mono uppercase">
            {row.upload_portal}
          </Badge>
        </div>
        <div className="text-xs text-slate-500 mt-0.5 truncate">
          {firstFile?.uploaded_by_name || "—"} · {(row.created_at || "").slice(0, 16).replace("T", " ")}
          {row.batch_id ? ` · batch=${row.batch_id}` : ""}
          {row.ocr?.confidence ? ` · OCR ${(row.ocr.confidence * 100).toFixed(0)}%` : ""}
        </div>
      </div>
      <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wide">open →</span>
    </button>
  );
}

function ReviewModal({ importId, onClose, onChange, meta }) {
  const [doc, setDoc] = useState(null);
  const [signedUrl, setSignedUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [adminOverride, setAdminOverride] = useState(false);
  const [rejectReason, setRejectReason] = useState("illegible");
  const [notes, setNotes] = useState("");
  const [corrections, setCorrections] = useState({});

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get(`/legacy-imports/${importId}`);
      setDoc(data);
      setCorrections(data.ocr?.extracted_fields || {});
      setNotes(data.review?.notes || "");
    } catch (e) {
      toast.error(friendlyError(e, "Could not load import"));
      onClose();
    }
  }, [importId, onClose]);

  useEffect(() => { refresh(); }, [refresh]);

  const openOriginal = async () => {
    try {
      const { data } = await api.get(`/legacy-imports/${importId}/file`);
      setSignedUrl(data.url);
      window.open(data.url, "_blank", "noopener,noreferrer");
    } catch (e) {
      toast.error(friendlyError(e, "Could not generate signed URL"));
    }
  };

  const approve = async () => {
    setBusy(true);
    try {
      const { data } = await api.post(`/legacy-imports/${importId}/approve`, {
        corrections, notes,
        admin_override_self_approval: adminOverride,
      });
      const row = data?.row;
      if (row?.promotion?.promoted) {
        toast.success(
          `Approved & promoted · live record ${row.promotion.promoted_record_id?.slice(0, 8) || "?"}`
        );
      } else {
        toast.success("Approved");
      }
      onChange();
      onClose();
    } catch (e) {
      toast.error(friendlyError(e, "Approve failed"));
    } finally {
      setBusy(false);
    }
  };

  const reject = async () => {
    setBusy(true);
    try {
      await api.post(`/legacy-imports/${importId}/reject`, {
        reason: rejectReason, notes,
      });
      toast.success("Rejected");
      onChange();
      onClose();
    } catch (e) {
      toast.error(friendlyError(e, "Reject failed"));
    } finally {
      setBusy(false);
    }
  };

  const retryOcr = async () => {
    setBusy(true);
    try {
      await api.post(`/legacy-imports/${importId}/retry-ocr`);
      toast.success("OCR re-queued");
      await refresh();
      onChange();
    } catch (e) {
      toast.error(friendlyError(e, "Retry failed"));
    } finally {
      setBusy(false);
    }
  };

  if (!doc) return null;
  const firstFile = doc.source_files?.[0];
  const pill = STATUS_PILL[doc.status] || STATUS_PILL.uploaded;
  const uploaderIsMe = (firstFile?.uploaded_by_id === meta?.actor_id);

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent
        className="sm:max-w-3xl max-h-[92vh] overflow-y-auto"
        data-testid="legacy-imports-review-modal"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>Review · {firstFile?.original_name || importId.slice(0, 8)}</span>
            <Badge className={`text-[10px] font-mono uppercase ${pill.color}`}>{pill.label}</Badge>
          </DialogTitle>
        </DialogHeader>

        {/* Side-by-side · scan + fields */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
          {/* LEFT · scan */}
          <div>
            <div className="text-[10px] font-mono uppercase tracking-wide text-slate-500 font-bold mb-1.5">
              Original document
            </div>
            <div className="bg-slate-100 border border-slate-200 rounded-md p-4 min-h-[200px] flex flex-col items-center justify-center gap-2 text-center">
              <FileText className="w-10 h-10 text-slate-400" />
              <div className="text-xs font-mono text-slate-600 break-all">
                {firstFile?.original_name}
              </div>
              <div className="text-[10px] text-slate-400">
                {(firstFile?.size_bytes / 1024).toFixed(1)} KB · {firstFile?.mime}
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={openOriginal}
                className="mt-2"
                data-testid="legacy-imports-view-evidence"
              >
                <Eye className="w-4 h-4 mr-1.5" /> View original scan
              </Button>
              <div className="text-[10px] text-slate-400 mt-1">
                Opens via 5-min signed URL · access is audited
              </div>
            </div>

            {/* Provenance */}
            <div className="mt-3 text-[11px] space-y-1 font-mono text-slate-500">
              <div>uploaded by: <strong className="text-slate-800">{firstFile?.uploaded_by_name}</strong></div>
              <div>uploaded at: {(firstFile?.uploaded_at || "").replace("T", " ").slice(0, 19)}</div>
              <div>portal: <strong className="text-slate-800">{doc.upload_portal}</strong></div>
              <div>doc type: <strong className="text-slate-800">{doc.document_type.replace(/_/g, " ")}</strong></div>
              {doc.batch_id && <div>batch: <strong className="text-slate-800">{doc.batch_id}</strong></div>}
              <div>OCR provider: {doc.ocr?.provider}</div>
              <div>OCR confidence: {doc.ocr?.confidence != null ? (doc.ocr.confidence * 100).toFixed(0) + "%" : "—"}</div>
              {doc.promotion?.promoted && (
                <div className="mt-2 pt-2 border-t border-emerald-200 bg-emerald-50 -mx-1 px-1.5 py-1.5 rounded text-emerald-900" data-testid="legacy-imports-promoted-info">
                  <div className="font-bold">PROMOTED to live record</div>
                  <div>collection: <strong>{doc.promotion.promoted_to_collection}</strong></div>
                  <div>record id: <strong className="break-all">{doc.promotion.promoted_record_id}</strong></div>
                  <div>at: {(doc.promotion.promoted_at || "").replace("T", " ").slice(0, 19)}</div>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT · extracted fields */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <div className="text-[10px] font-mono uppercase tracking-wide text-slate-500 font-bold">
                Extracted fields (editable)
              </div>
              {doc.ocr?.confidence != null && (
                <ConfidencePill value={doc.ocr.confidence} data-testid="legacy-imports-overall-confidence" />
              )}
            </div>
            {doc.ocr?.provider === "stub" && Object.keys(corrections).length === 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-md p-3 text-xs text-amber-900 mb-2 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  No fields extracted yet (stub OCR for this document type).
                  Reviewer fills fields manually below. Activation of the AI
                  extractor for this document type is operator-gated.
                </div>
              </div>
            )}
            {doc.ocr?.error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3 text-xs text-red-900 mb-2 flex items-start gap-2" data-testid="legacy-imports-ocr-error">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-bold">OCR failed</div>
                  <div className="font-mono text-[10px] mt-1">{doc.ocr.error}</div>
                </div>
                {doc.status === "ocr_failed" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={retryOcr}
                    className="text-[10px] h-7"
                    data-testid="legacy-imports-retry-ocr"
                  >
                    <RotateCw className="w-3 h-3 mr-1" />
                    Retry
                  </Button>
                )}
              </div>
            )}
            <FieldEditor
              value={corrections}
              onChange={setCorrections}
              fieldConfidences={doc.ocr?.field_confidences || {}}
            />

            {/* Matches panel — Phase B + */}
            {doc.matches && (doc.matches.employee?.suggested_id ||
                             doc.matches.equipment?.suggested_id ||
                             doc.matches.project?.suggested_id ||
                             doc.matches.duplicate_of) && (
              <MatchesPanel matches={doc.matches} />
            )}

            {/* Notes */}
            <Label className="text-[10px] font-mono uppercase tracking-wide text-slate-600 mt-3 block">
              Reviewer notes (optional)
            </Label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="mt-1"
              data-testid="legacy-imports-notes"
            />

            {/* Anti-self-approval warning */}
            {uploaderIsMe && (
              <div className="mt-3 bg-red-50 border border-red-200 rounded-md p-3 text-xs">
                <div className="flex items-start gap-2 text-red-900">
                  <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    <strong>You uploaded this record.</strong> Per separation-of-duties policy, the same person cannot upload and approve.
                    {meta?.actor_role === "admin" && (
                      <>
                        {" "}As Admin you can override — this will be recorded in the audit log.
                        <label className="flex items-center gap-2 mt-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={adminOverride}
                            onChange={(e) => setAdminOverride(e.target.checked)}
                            className="w-3.5 h-3.5 accent-red-700"
                            data-testid="legacy-imports-admin-override"
                          />
                          <span className="font-mono text-[11px] uppercase tracking-wide">I confirm Admin override</span>
                        </label>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Reject reason (only when modal in needs_review state) */}
            {doc.status === "needs_review" && (
              <div className="mt-3">
                <Label className="text-[10px] font-mono uppercase tracking-wide text-slate-600">
                  Reject reason (if rejecting)
                </Label>
                <Select value={rejectReason} onValueChange={setRejectReason}>
                  <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {["illegible", "wrong_employee", "duplicate", "out_of_scope", "wrong_document_type", "other"].map((r) => (
                      <SelectItem key={r} value={r}>{r.replace(/_/g, " ")}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        </div>

        <DialogFooter className="flex-row justify-between sm:justify-between gap-2 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={reject}
            disabled={busy || doc.status !== "needs_review"}
            data-testid="legacy-imports-reject"
          >
            <XCircle className="w-4 h-4 mr-1.5" />
            Reject
          </Button>
          <Button
            type="button"
            onClick={approve}
            disabled={busy || doc.status !== "needs_review" || (uploaderIsMe && !adminOverride)}
            className="bg-emerald-700 hover:bg-emerald-800"
            data-testid="legacy-imports-approve"
          >
            <CheckCircle2 className="w-4 h-4 mr-1.5" />
            Approve
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Tiny dynamic key/value editor for the extracted fields.
function FieldEditor({ value, onChange, fieldConfidences = {} }) {
  const [newKey, setNewKey] = useState("");
  const entries = Object.entries(value || {});
  return (
    <div className="space-y-2" data-testid="legacy-imports-field-editor">
      {entries.map(([k, v]) => {
        const conf = fieldConfidences?.[k];
        return (
          <div key={k} className="flex items-start gap-2">
            <div className="w-32 shrink-0 font-mono text-[10px] uppercase tracking-wide text-slate-600 pt-2 truncate">
              <div className="truncate">{k}</div>
              {typeof conf === "number" && (
                <ConfidencePill value={conf} compact />
              )}
            </div>
            <FieldValueInput
              fieldKey={k}
              value={v}
              onChange={(nv) => onChange({ ...value, [k]: nv })}
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                const next = { ...value };
                delete next[k];
                onChange(next);
              }}
              className="text-xs"
            >
              ×
            </Button>
          </div>
        );
      })}
      <div className="flex items-center gap-2 pt-1">
        <Input
          value={newKey}
          onChange={(e) => setNewKey(e.target.value)}
          placeholder="add field (e.g. employee_name)"
          className="flex-1 text-xs"
          data-testid="legacy-imports-new-field-key"
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            if (!newKey.trim()) return;
            onChange({ ...value, [newKey.trim()]: "" });
            setNewKey("");
          }}
        >
          + Add field
        </Button>
      </div>
    </div>
  );
}

// Render either a simple text input, or for `equipment_lines` show a
// readable summary so the reviewer can see the list at a glance
// (full per-line editing happens via the side-panel for Phase B+).
function FieldValueInput({ fieldKey, value, onChange }) {
  if (fieldKey === "equipment_lines" && Array.isArray(value)) {
    return (
      <div className="flex-1 border border-slate-200 rounded-md p-2 bg-slate-50" data-testid="legacy-imports-equipment-lines">
        {value.length === 0 && (
          <div className="text-[11px] text-slate-500 font-mono italic">No equipment lines extracted — add manually if needed.</div>
        )}
        <div className="space-y-1">
          {value.map((line, idx) => (
            <div key={idx} className="text-[11px] font-mono text-slate-700 flex items-start gap-2">
              <span className="text-slate-400">{idx + 1}.</span>
              <span className="font-bold">{line?.name || "—"}</span>
              {line?.serial && <span className="text-slate-500">· s/n {line.serial}</span>}
              {line?.qty && line.qty !== 1 && <span className="text-slate-500">· qty {line.qty}</span>}
              {line?.returned && <span className="text-emerald-700">· returned</span>}
            </div>
          ))}
        </div>
      </div>
    );
  }
  return (
    <Input
      value={String(value ?? "")}
      onChange={(e) => onChange(e.target.value)}
      className="flex-1"
      data-testid={`legacy-imports-field-${fieldKey}`}
    />
  );
}

// Small colored confidence pill — green ≥0.7, amber 0.4-0.7, red <0.4.
function ConfidencePill({ value, compact = false }) {
  const pct = Math.round((Number(value) || 0) * 100);
  const cls = value >= 0.7 ? "bg-emerald-100 text-emerald-800"
            : value >= 0.4 ? "bg-amber-100 text-amber-800"
            :                "bg-red-100 text-red-800";
  return (
    <span
      className={`inline-block ${compact ? "text-[9px] px-1.5 py-0 mt-0.5" : "text-[10px] px-2 py-0.5"} font-mono font-bold uppercase rounded ${cls}`}
      data-testid="legacy-imports-confidence-pill"
    >
      {pct}%
    </span>
  );
}

// Phase B Matches panel — employee/equipment/project suggestions + dup banner.
function MatchesPanel({ matches }) {
  const sections = [
    { key: "employee", label: "Employee", icon: Users },
    { key: "equipment", label: "Equipment", icon: Wrench },
    { key: "project", label: "Project", icon: Briefcase },
  ];
  return (
    <div className="mt-3 bg-indigo-50 border border-indigo-200 rounded-md p-3" data-testid="legacy-imports-matches-panel">
      <div className="text-[10px] font-mono uppercase tracking-wide text-indigo-700 font-bold mb-2">
        Suggested matches
      </div>
      <div className="space-y-2">
        {sections.map(({ key, label, icon: Icon }) => {
          const m = matches?.[key];
          if (!m?.suggested_id && !m?.suggested_name) return null;
          return (
            <div key={key} className="flex items-start gap-2 text-xs" data-testid={`legacy-imports-match-${key}`}>
              <Icon className="w-3.5 h-3.5 text-indigo-700 mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="font-mono text-[10px] uppercase tracking-wide text-indigo-700 font-bold">{label}</span>
                  <ConfidencePill value={m.confidence} />
                </div>
                <div className="font-bold text-slate-900 truncate">{m.suggested_name || m.suggested_id}</div>
                {m.alternatives?.length > 0 && (
                  <div className="text-[10px] font-mono text-slate-500 mt-0.5 truncate">
                    alt: {m.alternatives.slice(0, 3).map(a => a.name || a.id).join(" · ")}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {matches?.duplicate_of && (
          <div className="mt-2 bg-red-50 border border-red-200 rounded-md p-2.5 text-[11px] text-red-900 flex items-start gap-2" data-testid="legacy-imports-duplicate-banner">
            <Copy className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <div>
              <div className="font-bold">Possible duplicate</div>
              <div className="font-mono text-[10px] mt-0.5">{matches.duplicate_of.note}</div>
              <div className="font-mono text-[10px] mt-0.5">
                {matches.duplicate_of.match_count} matching native record(s) found.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
