// AssetDocumentsTab — Track 13.31B-D3+D4 · Asset Profile · Documents tab.
//
// Operator-facing surface — no engineering language.
// Lists existing documents, allows upload, view, download, expiration
// edits, and surfaces missing/required documents with a single click.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Upload, FileText, Image as ImageIcon, Download, Trash2,
  Calendar, Loader2, RefreshCcw,
  ShieldAlert, Camera, FileImage, CheckCircle2, Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ModalFooter } from "@/components/ModalFooter";
import { api } from "@/lib/api";
import { toast } from "sonner";

const DOC_TYPES = [
  { value: "registration", label: "Registration", help: "State / DMV registration document." },
  { value: "insurance_card", label: "Insurance Card", help: "Wallet-size proof of insurance kept in the vehicle." },
  { value: "insurance_policy", label: "Insurance Policy (Restricted)", help: "Full insurance policy. Restricted — admin only." },
  { value: "title", label: "Title (Restricted)", help: "Vehicle title / ownership document. Restricted — admin only." },
  { value: "purchase_document", label: "Purchase Document (Restricted)", help: "Bill of sale or purchase order. Restricted — admin only." },
  { value: "warranty", label: "Warranty", help: "Manufacturer or extended warranty paperwork." },
  { value: "dot_document", label: "DOT Document", help: "DOT inspection or authority paperwork. Annual renewal." },
  { value: "inspection_certificate", label: "Inspection Certificate", help: "Annual or jurisdictional inspection certificate." },
  { value: "calibration_certificate", label: "Calibration Certificate", help: "Most recent calibration record for survey / measurement equipment." },
  { value: "asset_photo", label: "Asset Photo", help: "Identification photo. Choose a Photo Type below." },
  { value: "operator_manual", label: "Operator Manual", help: "Manufacturer operator or service manual." },
  { value: "safety_documentation", label: "Safety Documentation", help: "Hazard sheets, SDS, lock-out tag-out, safety procedures." },
  { value: "other_supporting_document", label: "Other Supporting Document", help: "Anything else worth keeping with this asset record." },
];

const PHOTO_KINDS = [
  "primary", "gallery", "serial_plate", "vin_plate", "dot_plate",
  "registration_card", "insurance_card", "calibration_sticker", "damage",
];

function daysFromIso(iso) {
  if (!iso) return null;
  const d = new Date(iso + "T00:00:00Z");
  if (Number.isNaN(d.getTime())) return null;
  return Math.floor((d - new Date()) / 86400000);
}

function VerificationChip({ status, testid }) {
  if (status === "verified") {
    return (
      <span
        className="px-1.5 py-0.5 rounded border bg-emerald-100 text-emerald-900 border-emerald-300 font-mono text-[10px] uppercase tracking-[0.14em] font-bold inline-flex items-center gap-1"
        title="Verified — Asset Admin reviewed and confirmed this document."
        data-testid={testid}
      >
        <CheckCircle2 className="w-3 h-3" /> Verified
      </span>
    );
  }
  if (status === "pending") {
    return (
      <span
        className="px-1.5 py-0.5 rounded border bg-amber-100 text-amber-900 border-amber-300 font-mono text-[10px] uppercase tracking-[0.14em] font-bold"
        title="Pending Verification — uploaded but not yet reviewed by Asset Admin."
        data-testid={testid}
      >
        Pending Verification
      </span>
    );
  }
  return null;
}

function ExpirationBadge({ iso }) {
  if (!iso) return null;
  const d = daysFromIso(iso);
  if (d === null) return null;
  if (d < 0) {
    return (
      <span className="px-1.5 py-0.5 rounded border bg-red-100 text-red-900 border-red-300 font-mono text-[10px] uppercase tracking-[0.14em] font-bold">
        Expired
      </span>
    );
  }
  if (d <= 30) {
    return (
      <span className="px-1.5 py-0.5 rounded border bg-amber-100 text-amber-900 border-amber-300 font-mono text-[10px] uppercase tracking-[0.14em] font-bold">
        Expiring Soon · {d}d
      </span>
    );
  }
  if (d <= 90) {
    return (
      <span className="px-1.5 py-0.5 rounded border bg-sky-100 text-sky-900 border-sky-300 font-mono text-[10px] uppercase tracking-[0.14em] font-bold">
        {d}d remaining
      </span>
    );
  }
  return (
    <span className="px-1.5 py-0.5 rounded border bg-emerald-100 text-emerald-900 border-emerald-300 font-mono text-[10px] uppercase tracking-[0.14em] font-bold">
      Current · {d}d
    </span>
  );
}

function MissingItem({ label, present, testid }) {
  return (
    <div
      data-testid={testid}
      className={`flex items-center justify-between gap-2 px-2.5 py-1.5 rounded border text-xs ${
        present
          ? "bg-emerald-50 border-emerald-200 text-emerald-900"
          : "bg-amber-50 border-amber-200 text-amber-900"
      }`}
    >
      <span>{label}</span>
      {present ? (
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
      ) : (
        <span className="font-mono text-[10px] uppercase tracking-[0.16em] font-bold">
          Pending Upload
        </span>
      )}
    </div>
  );
}

export default function AssetDocumentsTab({ assetId, unitNumber }) {
  const [docs, setDocs] = useState([]);
  const [required, setRequired] = useState(null);
  const [photos, setPhotos] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showUpload, setShowUpload] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [d, r, p] = await Promise.all([
        api.get(`/asset-spine/assets/${assetId}/documents`),
        api.get(`/asset-spine/assets/${assetId}/required-documents`),
        api.get(`/asset-spine/assets/${assetId}/missing-photos`),
      ]);
      setDocs(d.data.items || []);
      setRequired(r.data);
      setPhotos(p.data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Could not load asset documents. Try again.");
    } finally {
      setLoading(false);
    }
  }, [assetId]);

  useEffect(() => {
    reload();
  }, [reload]);

  const downloadPDF = useCallback(async () => {
    try {
      const r = await api.get(`/asset-spine/assets/${assetId}/profile.pdf`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `MASCI_Asset_Profile_${(unitNumber || assetId).replace(/[^\w-]/g, "_")}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("PDF generation failed. Try again.");
    }
  }, [assetId, unitNumber]);

  if (loading) {
    return (
      <div className="py-12 text-center text-slate-500" data-testid="ap-docs-loading">
        <Loader2 className="w-5 h-5 animate-spin mx-auto" />
        <div className="mt-2 font-mono text-xs uppercase tracking-[0.16em]">Loading documents…</div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="bg-red-50 border-2 border-red-200 rounded p-4 text-red-900" data-testid="ap-docs-error">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="asset-documents-tab">
      <div className="flex items-center justify-between gap-2">
        <div className="text-xs font-mono uppercase tracking-[0.18em] text-slate-600 font-bold">
          {docs.length} document{docs.length === 1 ? "" : "s"} on file
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline" size="sm" onClick={reload}
            data-testid="ap-docs-refresh"
          >
            <RefreshCcw className="w-3.5 h-3.5 mr-1" /> Refresh
          </Button>
          <Button
            variant="outline" size="sm" onClick={downloadPDF}
            data-testid="ap-docs-download-pdf"
          >
            <FileText className="w-3.5 h-3.5 mr-1" /> Generate Profile PDF
          </Button>
          <Button
            size="sm" onClick={() => setShowUpload(true)}
            className="bg-red-700 hover:bg-red-800 text-white"
            data-testid="ap-docs-upload-open"
          >
            <Upload className="w-3.5 h-3.5 mr-1" /> Upload Document
          </Button>
        </div>
      </div>

      {/* Required documents */}
      {required && required.required_documents.length > 0 && (
        <section className="bg-white rounded border border-slate-200 p-4" data-testid="ap-docs-required">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">
            Documentation Required for {required.asset_type}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {required.required_documents.map((r) => (
              <MissingItem
                key={r.document_type}
                label={r.label}
                present={r.uploaded}
                testid={`ap-docs-req-${r.document_type}`}
              />
            ))}
          </div>
        </section>
      )}

      {/* Photo coverage */}
      {photos && (
        <section className="bg-white rounded border border-slate-200 p-4" data-testid="ap-docs-photos">
          <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">
            <Camera className="w-3.5 h-3.5" /> Photo Coverage
            <span className="text-slate-400 normal-case font-sans text-xs">— suggested, never required</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
            {photos.photo_kinds.map((p) => (
              <MissingItem
                key={p.photo_kind}
                label={p.label}
                present={p.uploaded}
                testid={`ap-docs-photo-${p.photo_kind}`}
              />
            ))}
          </div>
        </section>
      )}

      {/* Document list */}
      <section className="bg-white rounded border border-slate-200" data-testid="ap-docs-list">
        {docs.length === 0 ? (
          <div className="p-8 text-center text-slate-500" data-testid="ap-docs-empty">
            <FileText className="w-8 h-8 mx-auto mb-2 text-slate-400" />
            <div className="font-mono text-xs uppercase tracking-[0.16em]">No documents uploaded yet</div>
            <Button
              size="sm" variant="outline" className="mt-3"
              onClick={() => setShowUpload(true)}
            >
              <Upload className="w-3.5 h-3.5 mr-1" /> Upload the first document
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {docs.map((d) => (
              <DocRow
                key={d.id}
                assetId={assetId}
                doc={d}
                onChange={reload}
              />
            ))}
          </div>
        )}
      </section>

      {showUpload && (
        <UploadDialog
          assetId={assetId}
          onClose={() => setShowUpload(false)}
          onUploaded={() => { setShowUpload(false); reload(); }}
        />
      )}
    </div>
  );
}

function DocRow({ assetId, doc, onChange }) {
  const [editing, setEditing] = useState(false);
  const [exp, setExp] = useState(doc.expiration_date || "");
  const [eff, setEff] = useState(doc.effective_date || "");
  const [busy, setBusy] = useState(false);

  const fileUrl = useMemo(() => {
    return `${api.defaults.baseURL}/asset-spine/assets/${assetId}/documents/${doc.id}/file`;
  }, [assetId, doc.id]);

  const view = useCallback(async () => {
    try {
      const r = await api.get(`/asset-spine/assets/${assetId}/documents/${doc.id}/file`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(r.data);
      window.open(url, "_blank");
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch {
      toast.error("Could not open the document. Try again.");
    }
  }, [assetId, doc.id]);

  const download = useCallback(async () => {
    try {
      const r = await api.get(`/asset-spine/assets/${assetId}/documents/${doc.id}/file`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.filename || "document";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Download failed. Try again.");
    }
  }, [assetId, doc.id, doc.filename]);

  const save = useCallback(async () => {
    setBusy(true);
    try {
      await api.patch(`/asset-spine/assets/${assetId}/documents/${doc.id}`, {
        effective_date: eff || "",
        expiration_date: exp || "",
      });
      toast.success("Changes saved.");
      setEditing(false);
      onChange();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not save. Try again.");
    } finally {
      setBusy(false);
    }
  }, [assetId, doc.id, eff, exp, onChange]);

  const remove = useCallback(async () => {
    if (!window.confirm(`Remove "${doc.document_label}" from this asset record?`)) return;
    setBusy(true);
    try {
      await api.delete(`/asset-spine/assets/${assetId}/documents/${doc.id}`);
      toast.success("Removed.");
      onChange();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not delete. Try again, or contact your administrator if it keeps failing.");
    } finally {
      setBusy(false);
    }
  }, [assetId, doc.id, doc.document_label, onChange]);

  const isImage = (doc.content_type || "").startsWith("image/");
  const isPDF = doc.content_type === "application/pdf";

  return (
    <div className="p-3 flex items-center gap-3" data-testid={`ap-doc-row-${doc.id}`}>
      <div className="w-9 h-9 rounded bg-slate-100 flex items-center justify-center shrink-0">
        {isImage ? (
          <ImageIcon className="w-4 h-4 text-slate-500" />
        ) : isPDF ? (
          <FileText className="w-4 h-4 text-red-700" />
        ) : (
          <FileImage className="w-4 h-4 text-slate-500" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-bold text-sm text-slate-900">{doc.document_label}</span>
          {doc.is_sensitive && (
            <span className="px-1.5 py-0.5 rounded border bg-purple-100 text-purple-900 border-purple-300 font-mono text-[10px] uppercase tracking-[0.14em] font-bold inline-flex items-center gap-1">
              <ShieldAlert className="w-3 h-3" /> Restricted
            </span>
          )}
          <VerificationChip
            status={doc.verified_at || doc.is_verified ? "verified" : (doc.verification_status === "pending" ? "pending" : null)}
            testid={`ap-doc-verify-${doc.id}`}
          />
          <ExpirationBadge iso={doc.expiration_date} />
        </div>
        <div className="text-xs text-slate-500 mt-0.5 truncate">
          {doc.filename || "—"} · uploaded {doc.uploaded_at?.slice(0, 10)}
        </div>
        {editing ? (
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            <label className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">Effective</label>
            <input
              type="date" value={eff} onChange={(e) => setEff(e.target.value)}
              className="border-2 border-slate-300 rounded px-2 py-1 text-xs"
              data-testid={`ap-doc-eff-${doc.id}`}
            />
            <label className="text-[10px] font-mono uppercase tracking-[0.14em] text-slate-500">Expires</label>
            <input
              type="date" value={exp} onChange={(e) => setExp(e.target.value)}
              className="border-2 border-slate-300 rounded px-2 py-1 text-xs"
              data-testid={`ap-doc-exp-${doc.id}`}
            />
            <Button size="sm" onClick={save} disabled={busy} data-testid={`ap-doc-save-${doc.id}`}>
              Save
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>
          </div>
        ) : null}
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <Button size="sm" variant="ghost" onClick={view} data-testid={`ap-doc-view-${doc.id}`}>View</Button>
        <Button size="sm" variant="ghost" onClick={download} title="Download" aria-label="Download document" data-testid={`ap-doc-dl-${doc.id}`}>
          <Download className="w-3.5 h-3.5" />
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setEditing((v) => !v)} title="Edit dates" aria-label="Edit document dates" data-testid={`ap-doc-edit-${doc.id}`}>
          <Calendar className="w-3.5 h-3.5" />
        </Button>
        <Button size="sm" variant="ghost" onClick={remove} disabled={busy} title="Remove" aria-label="Remove document" data-testid={`ap-doc-del-${doc.id}`}>
          <Trash2 className="w-3.5 h-3.5 text-red-700" />
        </Button>
      </div>
    </div>
  );
}

function UploadDialog({ assetId, onClose, onUploaded }) {
  const fileRef = useRef(null);
  const [documentType, setDocumentType] = useState("registration");
  const [photoKind, setPhotoKind] = useState("");
  const [effective, setEffective] = useState("");
  const [expiration, setExpiration] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  const docMeta = useMemo(
    () => DOC_TYPES.find((t) => t.value === documentType) || DOC_TYPES[0],
    [documentType],
  );

  const submit = async (e) => {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) {
      toast.error("Choose a file first.");
      return;
    }
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("document_type", documentType);
      if (documentType === "asset_photo" && photoKind) fd.append("photo_kind", photoKind);
      if (effective) fd.append("effective_date", effective);
      if (expiration) fd.append("expiration_date", expiration);
      if (note) fd.append("operational_note", note);
      fd.append("file", file);
      await api.post(`/asset-spine/assets/${assetId}/documents/upload`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Document uploaded.");
      onUploaded();
    } catch (e2) {
      toast.error(e2?.response?.data?.detail || "Upload failed. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
      data-testid="ap-doc-upload-dialog"
    >
      <form
        onSubmit={submit}
        className="bg-white rounded-lg shadow-xl p-5 max-w-md w-full space-y-3"
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">
              Asset Document Vault
            </div>
            <div className="font-bold text-lg">Upload Document</div>
          </div>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={onClose}
            aria-label="Close"
            title="Close"
            data-testid="ap-doc-upload-close"
          >
            Close
          </Button>
        </div>
        <div
          className="rounded border border-sky-200 bg-sky-50/70 px-3 py-2 text-[12px] text-sky-900 flex items-start gap-2"
          data-testid="ap-doc-upload-coaching"
        >
          <Info className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            Documents are attached to this asset and tracked for renewal.
            Uploads land as <span className="font-bold">Pending Verification</span> until
            Asset Admin reviews them.
          </div>
        </div>
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-600 font-bold mb-1">
            Document Type
          </div>
          <select
            className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
            value={documentType} onChange={(e) => setDocumentType(e.target.value)}
            data-testid="ap-doc-upload-type"
          >
            {DOC_TYPES.map((t) => (
              <option key={t.value} value={t.value} title={t.help}>{t.label}</option>
            ))}
          </select>
          <div
            className="text-[11px] text-slate-600 mt-1 leading-snug"
            data-testid="ap-doc-upload-type-help"
          >
            {docMeta.help}
          </div>
        </label>
        {documentType === "asset_photo" && (
          <label className="block">
            <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-600 font-bold mb-1">
              Photo Type
            </div>
            <select
              className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
              value={photoKind} onChange={(e) => setPhotoKind(e.target.value)}
              data-testid="ap-doc-upload-photokind"
            >
              <option value="">— Select a photo type —</option>
              {PHOTO_KINDS.map((p) => (
                <option key={p} value={p}>{p.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</option>
              ))}
            </select>
          </label>
        )}
        <div className="grid grid-cols-2 gap-2">
          <label>
            <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-600 font-bold mb-1">
              Effective Date
            </div>
            <input
              type="date" value={effective} onChange={(e) => setEffective(e.target.value)}
              className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
              data-testid="ap-doc-upload-eff"
            />
            <div className="text-[10.5px] text-slate-500 mt-1">When the document took effect.</div>
          </label>
          <label>
            <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-600 font-bold mb-1">
              Expires
            </div>
            <input
              type="date" value={expiration} onChange={(e) => setExpiration(e.target.value)}
              className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
              data-testid="ap-doc-upload-exp"
            />
            <div className="text-[10.5px] text-slate-500 mt-1">Drives renewal alerts. Leave blank if not applicable.</div>
          </label>
        </div>
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-600 font-bold mb-1">
            Note <span className="text-slate-400 font-sans normal-case">(optional)</span>
          </div>
          <input
            type="text" value={note} onChange={(e) => setNote(e.target.value)}
            placeholder="e.g. Annual renewal"
            className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
            data-testid="ap-doc-upload-note"
          />
        </label>
        <label className="block">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-600 font-bold mb-1">
            File
          </div>
          <input
            type="file" ref={fileRef}
            accept="image/*,application/pdf"
            className="w-full border-2 border-dashed border-slate-300 rounded px-2 py-2 text-sm"
            data-testid="ap-doc-upload-file"
          />
          <div className="text-[10px] text-slate-500 mt-1">
            Images up to 10&nbsp;MB · PDFs up to 25&nbsp;MB.
          </div>
        </label>
        <ModalFooter testid="ap-doc-upload-footer">
          <ModalFooter.Cancel onClick={onClose} disabled={busy} testid="ap-doc-upload-cancel">
            Cancel
          </ModalFooter.Cancel>
          <ModalFooter.Primary disabled={busy} testid="ap-doc-upload-submit">
            {busy ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
            ) : (
              <Upload className="w-3.5 h-3.5 mr-1" />
            )}
            Upload Document
          </ModalFooter.Primary>
        </ModalFooter>
      </form>
    </div>
  );
}
