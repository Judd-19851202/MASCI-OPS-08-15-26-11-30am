/**
 * OA-1 · PhotoUploader.jsx
 * Reuses backend R2 upload pattern. Magic-byte check is on the server;
 * client only enforces MIME + size to fail fast on mobile.
 */
import React, { useRef, useState } from "react";
import { Camera, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { oaApi } from "@/lib/oa";

const ACCEPT = "image/jpeg,image/png,image/webp,image/heic,image/heif";
const MAX_BYTES = 15 * 1024 * 1024;

function PhotoTile({ oaId, photo, onDelete }) {
  const [url, setUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const open = async () => {
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
      return;
    }
    setLoading(true);
    try {
      const r = await oaApi.photoUrl(oaId, photo.id);
      setUrl(r.data.url);
      window.open(r.data.url, "_blank", "noopener,noreferrer");
    } finally {
      setLoading(false);
    }
  };

  const del = async (e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this photo?")) return;
    setDeleting(true);
    try {
      await oaApi.deletePhoto(oaId, photo.id);
      onDelete?.(photo.id);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div
      data-testid={`oa-photo-tile-${photo.id}`}
      onClick={open}
      className="relative aspect-square bg-slate-100 border border-slate-200 rounded cursor-pointer flex items-center justify-center hover:bg-slate-200 group"
    >
      {loading ? <Loader2 className="w-5 h-5 text-slate-500 animate-spin" /> : <Camera className="w-6 h-6 text-slate-500" />}
      <div className="absolute bottom-1 left-1 right-1 text-[9px] font-mono uppercase tracking-wider text-slate-500 truncate">
        {Math.round((photo.size || 0) / 1024)} KB
      </div>
      <button
        type="button"
        onClick={del}
        disabled={deleting}
        data-testid={`oa-photo-delete-${photo.id}`}
        className="absolute top-1 right-1 p-1 rounded bg-white/90 text-rose-700 opacity-0 group-hover:opacity-100 transition"
        aria-label="Delete photo"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

export default function PhotoUploader({ oaId, photos, onChange }) {
  const { t } = useT();
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);

  const onPick = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";  // allow re-picking same file
    if (!file) return;
    if (file.size > MAX_BYTES) {
      toast.error(t("Photo exceeds size limit."));
      return;
    }
    if (!ACCEPT.split(",").includes(file.type)) {
      toast.error(t("Photo must be JPEG, PNG, WebP, or HEIC."));
      return;
    }
    setUploading(true);
    try {
      const r = await oaApi.uploadPhoto(oaId, file);
      onChange?.([...(photos || []), r.data]);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not save. Please try again."));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-2" data-testid="oa-photo-uploader">
      <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2">
        {(photos || []).map((p) => (
          <PhotoTile
            key={p.id}
            oaId={oaId}
            photo={p}
            onDelete={(pid) => onChange?.((photos || []).filter((x) => x.id !== pid))}
          />
        ))}
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          data-testid="oa-photo-upload-btn"
          className="aspect-square border-2 border-dashed border-slate-300 rounded flex flex-col items-center justify-center gap-1 hover:border-indigo-400 hover:bg-indigo-50/40 text-slate-600 text-xs disabled:opacity-50"
        >
          {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Camera className="w-5 h-5" />}
          <span className="font-mono uppercase tracking-wider text-[10px]">{t("Add Photo")}</span>
        </button>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        capture="environment"
        className="hidden"
        onChange={onPick}
        data-testid="oa-photo-input"
      />
    </div>
  );
}
