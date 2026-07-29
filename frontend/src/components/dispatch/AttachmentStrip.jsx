/**
 * AttachmentStrip.jsx · iter417 · Phase 20.0 · Operational Attachments Foundation.
 *
 * Calm, camera-first attachment surface that mounts inline on the
 * dispatch AssignmentDrawer. Walking-skeleton scope:
 *
 *   - 12 canonical attachment types (asphalt_ticket · scale_ticket ·
 *     tanker_BOL · fuel_receipt · delivery_receipt · load_photo ·
 *     damage_photo · breakdown_photo · inspection_photo ·
 *     transfer_document · dump_receipt · operational_note_photo)
 *   - One file pick · one type pick · optional one-line note · submit
 *   - Thumbnails list (latest below latest above)
 *   - 5 MB cap (validated client-side + server-side)
 *   - In-flow HelpLink → dls-attachments-load-proof
 *
 * Doctrine: this is NOT a "Documents" section, NOT a file explorer,
 * NOT an album. It's operational proof glued to one assignment.
 *
 * Restraint: single component · NO modal · NO drag-and-drop UI fluff ·
 * NO album view · NO bulk operations. Mount inline only.
 */
import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Camera, FileImage, Upload, Trash2, ArrowRight, ImageOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { stagePhoto, flushStaged, StagedPhotoBadge } from "@/lib/resiliency";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const API = process.env.REACT_APP_BACKEND_URL;
const MAX_BYTES = 5 * 1024 * 1024;

// 12 canonical types · mirrors backend ATTACHMENT_TYPES set.
// Order is operationally relevant (most-common first).
const TYPE_LABELS = {
  asphalt_ticket: "Asphalt ticket",
  scale_ticket: "Scale ticket",
  tanker_BOL: "Tanker BOL",
  fuel_receipt: "Fuel receipt",
  delivery_receipt: "Delivery receipt",
  load_photo: "Load photo",
  damage_photo: "Damage photo",
  breakdown_photo: "Breakdown photo",
  inspection_photo: "Inspection photo",
  transfer_document: "Transfer document",
  dump_receipt: "Dump receipt",
  operational_note_photo: "Other photo",
};
const TYPE_ORDER = Object.keys(TYPE_LABELS);

function _authHeaders() {
  return buildScopedPortalAuthHeaders(["admin", "dispatch"]);
}

function _fmt(iso) {
  if (!iso) return "—";
  try { return formatPlatformTime(iso); } catch { return iso; }
}

export default function AttachmentStrip({ assignmentId, canWrite = true }) {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadingType, setUploadingType] = useState("load_photo");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  // Track 13.14 · scale-ticket structured fields. Kept local; all optional.
  const [scaleFields, setScaleFields] = useState({
    weight_gross_lbs: "",
    weight_tare_lbs:  "",
    weight_net_lbs:   "",
    material_code:    "",
  });
  const resetScaleFields = () => setScaleFields({
    weight_gross_lbs: "", weight_tare_lbs: "", weight_net_lbs: "", material_code: "",
  });

  const refresh = useCallback(async () => {
    if (!assignmentId) return;
    setLoading(true);
    try {
      const r = await fetch(
        `${API}/api/operational-attachments/list?host_kind=assignment&host_id=${encodeURIComponent(assignmentId)}`,
        { headers: _authHeaders() },
      );
      const data = await r.json().catch(() => ({}));
      if (r.ok && Array.isArray(data.attachments)) {
        setItems(data.attachments);
      }
    } catch {
      /* silent */
    } finally {
      setLoading(false);
    }
  }, [assignmentId]);

  useEffect(() => { refresh(); }, [refresh]);

  const onPick = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-picking same file
    if (!file) return;
    if (file.size > MAX_BYTES) {
      toast.error(t("File too large (5 MB max)."));
      return;
    }
    if (!String(file.type || "").startsWith("image/")) {
      toast.error(t("Only image files are supported."));
      return;
    }
    setBusy(true);
    try {
      const form = new FormData();
      form.append("host_kind", "assignment");
      form.append("host_id", assignmentId);
      form.append("attachment_type", uploadingType);
      form.append("operational_note", note.slice(0, 500));
      // Track 13.14 · scale-ticket structured fields. Only sent when the
      // selected attachment type is scale_ticket AND the value is non-empty.
      // Backend treats all four as optional and never fabricates zero.
      if (uploadingType === "scale_ticket") {
        const sf = scaleFields;
        if (sf.weight_gross_lbs.trim()) form.append("weight_gross_lbs", sf.weight_gross_lbs.trim());
        if (sf.weight_tare_lbs.trim())  form.append("weight_tare_lbs",  sf.weight_tare_lbs.trim());
        if (sf.weight_net_lbs.trim())   form.append("weight_net_lbs",   sf.weight_net_lbs.trim());
        if (sf.material_code.trim())    form.append("material_code",    sf.material_code.trim().slice(0, 64));
      }
      form.append("file", file);
      let r;
      try {
        r = await fetch(`${API}/api/operational-attachments/upload`, {
          method: "POST",
          headers: _authHeaders(),
          body: form,
        });
      } catch (netErr) {
        // iter435 · Phase 31 · network failure → stage locally · calm.
        try {
          await stagePhoto({
            file,
            hostKind: "assignment",
            hostId: assignmentId,
            attachmentType: uploadingType,
            note: note.slice(0, 500),
          });
          toast.message(t("Photo saved on this device · will send when online."));
          setNote("");
        } catch (stageErr) {
          toast.error(String(stageErr?.message || stageErr));
        }
        return;
      }
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        if (r.status >= 500) {
          // Server hiccup → stage for later retry.
          try {
            await stagePhoto({
              file,
              hostKind: "assignment",
              hostId: assignmentId,
              attachmentType: uploadingType,
              note: note.slice(0, 500),
            });
            toast.message(t("Photo saved on this device · will send when online."));
            setNote("");
          } catch {
            toast.error(data?.detail || t("Upload failed."));
          }
        } else {
          toast.error(data?.detail || t("Upload failed."));
        }
      } else {
        toast.success(t("Attached."));
        setNote("");
        // Track 13.14 · clear scale-ticket fields after a successful upload
        // so a subsequent scale ticket starts from a clean slate.
        if (uploadingType === "scale_ticket") resetScaleFields();
        // Opportunistic flush in case any earlier upload was staged.
        flushStaged().catch(() => { /* silent */ });
        refresh();
      }
    } catch (err) {
      toast.error(String(err?.message || err));
    } finally {
      setBusy(false);
    }
  };

  const onDelete = async (id) => {
    if (!window.confirm(t("Delete this attachment? (5 minutes after upload only)"))) return;
    try {
      const r = await fetch(`${API}/api/operational-attachments/${id}`, {
        method: "DELETE",
        headers: _authHeaders(),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        toast.error(data?.detail || t("Delete failed."));
      } else {
        toast.success(t("Removed."));
        refresh();
      }
    } catch (err) {
      toast.error(String(err?.message || err));
    }
  };

  return (
    <div data-testid="attachment-strip" className="mt-4">
      {/* Section header · calm operational chrome */}
      <div className="flex items-baseline justify-between mb-2">
        <div>
          <div className="text-[11px] uppercase tracking-wide text-slate-500 font-bold">
            {t("Operational proof")}
          </div>
          <h3 className="text-sm font-bold text-slate-900">
            {t("Tickets · photos · receipts")}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {/* iter435 · Phase 31 · calm "N waiting to send" pill */}
          <StagedPhotoBadge
            hostKind="assignment"
            hostId={assignmentId}
            testId="attachment-staged-badge"
          />
          <Link
            to="/guidance/dls-attachments-load-proof"
            data-testid="attachment-strip-help"
            className="text-xs text-slate-500 hover:text-slate-800 underline decoration-slate-300 underline-offset-2 inline-flex items-center"
          >
            {t("How load proof works")}
            <ArrowRight className="w-3 h-3 ml-1 opacity-70" />
          </Link>
        </div>
      </div>

      {/* Upload row · camera-first */}
      {canWrite && (
        <div
          data-testid="attachment-upload-row"
          className="bg-slate-50 border border-slate-200 rounded-xl p-3 mb-3"
        >
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-2">
            <div className="sm:col-span-5">
              <Label className="block text-xs text-slate-600 mb-1">
                {t("Attachment type")}
              </Label>
              <select
                data-testid="attachment-type-select"
                value={uploadingType}
                onChange={(e) => setUploadingType(e.target.value)}
                className="w-full h-10 rounded-md border border-slate-300 bg-white px-2 text-sm"
              >
                {TYPE_ORDER.map((k) => (
                  <option key={k} value={k}>{t(TYPE_LABELS[k])}</option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-7">
              <Label className="block text-xs text-slate-600 mb-1">
                {t("Note (optional)")}
              </Label>
              <Input
                data-testid="attachment-note-input"
                value={note}
                maxLength={500}
                onChange={(e) => setNote(e.target.value)}
                placeholder={t("Plant A scale · ticket #1421")}
                className="h-10 text-sm"
              />
            </div>
          </div>
          {/* Track 13.14 · Scale-ticket structured fields. Rendered ONLY
              when the operator selects scale_ticket. All four fields are
              optional · glove-friendly numeric inputs · never block photo
              upload. Net is auto-computed server-side when gross + tare
              are present and net is empty. */}
          {uploadingType === "scale_ticket" && (
            <div
              data-testid="scale-ticket-fields"
              className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 border-t border-slate-200 pt-3"
            >
              <div>
                <Label className="block text-[10px] uppercase tracking-wide text-slate-500 mb-1">
                  {t("Gross (lbs)")}
                </Label>
                <Input
                  data-testid="scale-ticket-gross"
                  inputMode="decimal"
                  value={scaleFields.weight_gross_lbs}
                  onChange={(e) => setScaleFields((s) => ({ ...s, weight_gross_lbs: e.target.value }))}
                  placeholder="—"
                  className="h-10 text-sm font-mono"
                />
              </div>
              <div>
                <Label className="block text-[10px] uppercase tracking-wide text-slate-500 mb-1">
                  {t("Tare (lbs)")}
                </Label>
                <Input
                  data-testid="scale-ticket-tare"
                  inputMode="decimal"
                  value={scaleFields.weight_tare_lbs}
                  onChange={(e) => setScaleFields((s) => ({ ...s, weight_tare_lbs: e.target.value }))}
                  placeholder="—"
                  className="h-10 text-sm font-mono"
                />
              </div>
              <div>
                <Label className="block text-[10px] uppercase tracking-wide text-slate-500 mb-1">
                  {t("Net (lbs)")}
                </Label>
                <Input
                  data-testid="scale-ticket-net"
                  inputMode="decimal"
                  value={scaleFields.weight_net_lbs}
                  onChange={(e) => setScaleFields((s) => ({ ...s, weight_net_lbs: e.target.value }))}
                  placeholder={t("auto if gross + tare")}
                  className="h-10 text-sm font-mono"
                />
              </div>
              <div>
                <Label className="block text-[10px] uppercase tracking-wide text-slate-500 mb-1">
                  {t("Material")}
                </Label>
                <Input
                  data-testid="scale-ticket-material"
                  value={scaleFields.material_code}
                  maxLength={64}
                  onChange={(e) => setScaleFields((s) => ({ ...s, material_code: e.target.value }))}
                  placeholder={t("e.g. SP-12.5")}
                  className="h-10 text-sm"
                />
              </div>
            </div>
          )}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <label className="inline-flex">
              <input
                data-testid="attachment-file-input"
                type="file"
                accept="image/*"
                capture="environment"
                onChange={onPick}
                disabled={busy}
                className="hidden"
              />
              <span
                className={`inline-flex items-center gap-2 px-3 h-10 rounded-md text-sm font-bold cursor-pointer
                  ${busy ? "bg-slate-300 text-slate-500" : "bg-slate-900 text-white hover:bg-slate-800"}`}
              >
                <Camera className="w-4 h-4" />
                {busy ? t("Uploading…") : t("Capture / Upload")}
              </span>
            </label>
            <span className="text-xs text-slate-500">
              {t("Images up to 5 MB · camera-first on phones.")}
            </span>
          </div>
        </div>
      )}

      {/* List · latest above */}
      {loading ? (
        <div data-testid="attachment-loading" className="text-xs text-slate-500">{t("Loading attachments…")}</div>
      ) : items.length === 0 ? (
        <div
          data-testid="attachment-empty"
          className="text-xs text-slate-500 flex items-center gap-2 px-1"
        >
          <ImageOff className="w-3.5 h-3.5" />
          {t("No operational proof attached yet.")}
        </div>
      ) : (
        <ul data-testid="attachment-list" className="space-y-2">
          {items
            .slice()
            .sort((a, b) => String(b.uploaded_at).localeCompare(String(a.uploaded_at)))
            .map((a) => (
              <li
                key={a.id}
                data-testid={`attachment-item-${a.id}`}
                className="flex items-start gap-3 bg-white rounded-md border border-slate-200 p-2"
              >
                <a
                  href={`${API}/api/operational-attachments/${a.id}/file`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-14 h-14 shrink-0 rounded-md bg-slate-100 flex items-center justify-center overflow-hidden border border-slate-200"
                  title={t("Open original")}
                >
                  <img
                    src={`${API}/api/operational-attachments/${a.id}/file`}
                    alt={a.filename || "attachment"}
                    className="w-full h-full object-cover"
                    onError={(e) => { e.currentTarget.style.display = "none"; }}
                  />
                  <FileImage className="w-5 h-5 text-slate-500" />
                </a>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-900">
                    {t(TYPE_LABELS[a.type] || a.type)}
                  </div>
                  {a.operational_note && (
                    <div className="text-xs text-slate-700 mt-0.5 truncate">
                      {a.operational_note}
                    </div>
                  )}
                  {/* Track 13.14 · Scale-ticket structured fields render.
                      Only shown when present on the attachment. No fake
                      zeros · no fabricated material code. */}
                  {a.type === "scale_ticket" && (
                    a.weight_gross_lbs != null
                    || a.weight_tare_lbs != null
                    || a.weight_net_lbs != null
                    || a.material_code
                  ) && (
                    <div
                      data-testid={`scale-ticket-meta-${a.id}`}
                      className="mt-1 flex flex-wrap gap-1.5 text-[10px]"
                    >
                      {a.weight_gross_lbs != null && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-mono">
                          <span className="uppercase tracking-wide text-slate-500">Gross</span>
                          {a.weight_gross_lbs.toLocaleString()} lb
                        </span>
                      )}
                      {a.weight_tare_lbs != null && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-mono">
                          <span className="uppercase tracking-wide text-slate-500">Tare</span>
                          {a.weight_tare_lbs.toLocaleString()} lb
                        </span>
                      )}
                      {a.weight_net_lbs != null && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 font-mono">
                          <span className="uppercase tracking-wide text-emerald-600">Net</span>
                          {a.weight_net_lbs.toLocaleString()} lb
                        </span>
                      )}
                      {a.material_code && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-800">
                          <span className="uppercase tracking-wide text-amber-600">Material</span>
                          <span className="font-mono">{a.material_code}</span>
                        </span>
                      )}
                    </div>
                  )}
                  <div className="text-[11px] text-slate-500 mt-1">
                    {a.uploaded_by || "—"} · {_fmt(a.uploaded_at)}
                  </div>
                </div>
                {canWrite && (
                  <button
                    onClick={() => onDelete(a.id)}
                    data-testid={`attachment-delete-${a.id}`}
                    className="text-slate-400 hover:text-rose-700 p-1"
                    title={t("Delete (5 min mistake-recovery window)")}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </li>
            ))}
        </ul>
      )}
    </div>
  );
}
