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
import { getAdminToken } from "@/lib/adminAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";

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
  const headers = {};
  const admin = getAdminToken();
  const disp = getDispatchToken();
  if (admin) headers["X-Admin-Token"] = admin;
  if (disp) headers["X-Dispatch-Token"] = disp;
  return headers;
}

function _fmt(iso) {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

export default function AttachmentStrip({ assignmentId, canWrite = true }) {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadingType, setUploadingType] = useState("load_photo");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

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
      form.append("file", file);
      const r = await fetch(`${API}/api/operational-attachments/upload`, {
        method: "POST",
        headers: _authHeaders(),
        body: form,
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        toast.error(data?.detail || t("Upload failed."));
      } else {
        toast.success(t("Attached."));
        setNote("");
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
        <Link
          to="/guidance/dls-attachments-load-proof"
          data-testid="attachment-strip-help"
          className="text-xs text-slate-500 hover:text-slate-800 underline decoration-slate-300 underline-offset-2 inline-flex items-center"
        >
          {t("How load proof works")}
          <ArrowRight className="w-3 h-3 ml-1 opacity-70" />
        </Link>
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
