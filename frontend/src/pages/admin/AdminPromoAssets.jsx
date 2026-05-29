// AdminPromoAssets.jsx — iter347 (Promo Asset Library)
//
// Admin-only media-asset library for organizing/downloading the cinematic
// platform clips that feed the long-form MASCI promo film + homepage
// hero loop.
//
// Capabilities:
//   • Upload (multipart) → R2 via the existing client
//   • Preview (in-page <video> via 7-day presigned URL)
//   • Download / copy-link / copy-manifest
//   • Filter by category, visibility, tag, search
//   • Delete (best-effort R2 cleanup + mongo row)
//   • Edit metadata
//
// All routes are /api/admin/promo-assets/* (admin-strict). The component
// matches the calm platform-family chrome — slate-700 stripes, mono
// kickers, card grid. Bilingual labels via useT().
import React, { useEffect, useMemo, useState, useCallback } from "react";
import {
  Film,
  Upload,
  Trash2,
  Download,
  Link as LinkIcon,
  Loader2,
  Search,
  RefreshCw,
  FileDown,
  Play,
  X,
  Pencil,
  ImageIcon,
} from "lucide-react";
import { toast } from "sonner";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { operationalError } from "@/lib/errors";

const VISIBILITIES = ["internal", "public"];

function StatPill({ value, label, testid }) {
  return (
    <div className="flex flex-col" data-testid={testid}>
      <div className="font-mono text-2xl font-black text-slate-900 leading-none">
        {value}
      </div>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mt-1.5">
        {label}
      </div>
    </div>
  );
}

function copyToClipboard(text) {
  if (!text) return Promise.reject(new Error("empty"));
  if (navigator?.clipboard?.writeText) {
    return navigator.clipboard.writeText(text);
  }
  return new Promise((resolve, reject) => {
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      resolve();
    } catch (e) {
      reject(e);
    }
  });
}

function formatSeconds(s) {
  if (!s && s !== 0) return "—";
  const n = Math.round(s);
  const m = Math.floor(n / 60);
  const r = n % 60;
  return m > 0 ? `${m}:${String(r).padStart(2, "0")}` : `${n}s`;
}

function AssetCard({ asset, onPreview, onEdit, onDelete, onCopyLink, t }) {
  const isVideo = (asset.content_type || "").startsWith("video/");
  const isImage = (asset.content_type || "").startsWith("image/");
  return (
    <div
      className="bg-white border border-slate-200 rounded-md overflow-hidden flex flex-col"
      data-testid={`promo-asset-card-${asset.id}`}
    >
      <div className="aspect-video bg-slate-900 relative flex items-center justify-center">
        {isVideo ? (
          <Film className="w-10 h-10 text-slate-500" />
        ) : isImage ? (
          <ImageIcon className="w-10 h-10 text-slate-500" />
        ) : (
          <FileDown className="w-10 h-10 text-slate-500" />
        )}
        {asset.visibility === "public" && (
          <div className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-emerald-600 text-white font-mono text-[9px] uppercase tracking-wider">
            {t("PUBLIC")}
          </div>
        )}
        <button
          type="button"
          onClick={() => onPreview(asset)}
          className="absolute inset-0 bg-black/0 hover:bg-black/30 transition-colors flex items-center justify-center group"
          data-testid={`promo-asset-preview-${asset.id}`}
          aria-label={t("Preview")}
        >
          <Play className="w-12 h-12 text-white opacity-0 group-hover:opacity-90 transition-opacity" />
        </button>
      </div>
      <div className="p-4 flex flex-col gap-2 flex-1">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-display text-sm font-black text-slate-900 leading-tight">
            {asset.name}
          </h3>
        </div>
        <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500">
          {asset.category}
        </div>
        {asset.description && (
          <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
            {asset.description}
          </p>
        )}
        <div className="grid grid-cols-3 gap-2 text-[10px] font-mono text-slate-600 pt-1 border-t border-slate-100">
          <div>
            <div className="uppercase tracking-wider text-slate-400">{t("Size")}</div>
            <div className="font-bold text-slate-700">
              {asset.file_size_mb} MB
            </div>
          </div>
          <div>
            <div className="uppercase tracking-wider text-slate-400">{t("Length")}</div>
            <div className="font-bold text-slate-700">
              {formatSeconds(asset.duration_seconds)}
            </div>
          </div>
          <div>
            <div className="uppercase tracking-wider text-slate-400">{t("Type")}</div>
            <div className="font-bold text-slate-700 uppercase">
              {asset.file_type || "—"}
            </div>
          </div>
        </div>
        {asset.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {asset.tags.slice(0, 4).map((tg) => (
              <span
                key={tg}
                className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[9px] uppercase tracking-wider"
              >
                {tg}
              </span>
            ))}
          </div>
        )}
        <div className="flex gap-1.5 mt-auto pt-2 border-t border-slate-100">
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => onCopyLink(asset)}
            className="flex-1 h-8 text-[10px] font-mono uppercase tracking-wider"
            data-testid={`promo-asset-copy-link-${asset.id}`}
          >
            <LinkIcon className="w-3 h-3 mr-1" /> {t("Copy Link")}
          </Button>
          <a
            href={`${process.env.REACT_APP_BACKEND_URL}/api/admin/promo-assets/${asset.id}/download`}
            target="_blank"
            rel="noopener noreferrer"
            data-testid={`promo-asset-download-${asset.id}`}
            className="flex-1"
          >
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="w-full h-8 text-[10px] font-mono uppercase tracking-wider"
            >
              <Download className="w-3 h-3 mr-1" /> {t("Download")}
            </Button>
          </a>
        </div>
        <div className="flex gap-1.5">
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => onEdit(asset)}
            className="flex-1 h-7 text-[9px] font-mono uppercase tracking-wider text-slate-600 hover:text-slate-900"
            data-testid={`promo-asset-edit-${asset.id}`}
          >
            <Pencil className="w-3 h-3 mr-1" /> {t("Edit")}
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => onDelete(asset)}
            className="flex-1 h-7 text-[9px] font-mono uppercase tracking-wider text-red-700 hover:text-red-900 hover:bg-red-50"
            data-testid={`promo-asset-delete-${asset.id}`}
          >
            <Trash2 className="w-3 h-3 mr-1" /> {t("Delete")}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function AdminPromoAssets() {
  const { t } = useT();
  const [assets, setAssets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState("__all__");
  const [filterVisibility, setFilterVisibility] = useState("__all__");
  const [search, setSearch] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [previewAsset, setPreviewAsset] = useState(null);
  const [editAsset, setEditAsset] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterCategory !== "__all__") params.category = filterCategory;
      if (filterVisibility !== "__all__") params.visibility = filterVisibility;
      if (search.trim()) params.q = search.trim();
      const r = await api.get("/admin/promo-assets", { params });
      setAssets(r.data?.items || []);
      setCategories(r.data?.categories || []);
    } catch (e) {
      toast.error(operationalError(e, t("Could not load promo assets")));
    } finally {
      setLoading(false);
    }
  }, [filterCategory, filterVisibility, search, t]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // ── upload handler ────────────────────────────────────────────────
  const handleUpload = async (formData) => {
    try {
      await api.post("/admin/promo-assets", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 600_000, // 10 min for large videos
      });
      toast.success(t("Asset uploaded"));
      setUploadOpen(false);
      refresh();
    } catch (e) {
      toast.error(operationalError(e, t("Upload failed")));
    }
  };

  const handleDelete = async (asset) => {
    if (!window.confirm(t("Delete this asset? This cannot be undone."))) return;
    try {
      await api.delete(`/admin/promo-assets/${asset.id}`);
      toast.success(t("Asset deleted"));
      refresh();
    } catch (e) {
      toast.error(operationalError(e, t("Delete failed")));
    }
  };

  const handleCopyLink = async (asset) => {
    try {
      const r = await api.get(`/admin/promo-assets/${asset.id}`);
      const url = r.data?.asset?.playback_url;
      if (!url) {
        toast.error(t("No playback URL available"));
        return;
      }
      await copyToClipboard(url);
      toast.success(t("Link copied — valid for 7 days"));
    } catch (e) {
      toast.error(operationalError(e, t("Could not copy link")));
    }
  };

  const stats = useMemo(() => {
    const byCat = {};
    let publicCount = 0;
    let totalMb = 0;
    for (const a of assets) {
      byCat[a.category] = (byCat[a.category] || 0) + 1;
      if (a.visibility === "public") publicCount += 1;
      totalMb += a.file_size_mb || 0;
    }
    return {
      total: assets.length,
      categories: Object.keys(byCat).length,
      public: publicCount,
      sizeMb: Math.round(totalMb),
    };
  }, [assets]);

  return (
    <AdminShell>
      <div className="space-y-5" data-testid="admin-promo-assets-page">
        {/* ── header ─── */}
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-1">
            {t("Promo & Brand")}
          </div>
          <h1 className="font-display text-3xl font-black text-slate-900 leading-none">
            {t("Promo Asset Library")}
          </h1>
          <p className="text-sm text-slate-600 mt-2 max-w-3xl leading-relaxed">
            {t(
              "Cinematic platform clips, hero loops, and screen captures for the long-form MASCI promo film. Organized, downloadable, hand-off ready for any video editor."
            )}
          </p>
        </div>

        {/* ── stats stripe ─── */}
        <div className="bg-white border border-slate-200 rounded-md border-l-4 border-l-slate-700 p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold">
              {t("Library At A Glance")}
            </div>
            <div className="flex gap-2">
              <a
                href={`${process.env.REACT_APP_BACKEND_URL}/api/admin/promo-assets/manifest.json`}
                target="_blank"
                rel="noopener noreferrer"
                data-testid="promo-manifest-export"
              >
                <Button size="sm" variant="outline" className="h-8 text-[10px] font-mono uppercase tracking-wider">
                  <FileDown className="w-3 h-3 mr-1" /> {t("Manifest JSON")}
                </Button>
              </a>
              <Button
                size="sm"
                variant="outline"
                onClick={refresh}
                className="h-8 text-[10px] font-mono uppercase tracking-wider"
                data-testid="promo-refresh"
              >
                <RefreshCw className={`w-3 h-3 mr-1 ${loading ? "animate-spin" : ""}`} /> {t("Refresh")}
              </Button>
              <Button
                size="sm"
                onClick={() => setUploadOpen(true)}
                className="h-8 text-[10px] font-mono uppercase tracking-wider bg-slate-900 hover:bg-slate-800 text-white"
                data-testid="promo-upload-btn"
              >
                <Upload className="w-3 h-3 mr-1" /> {t("Upload Asset")}
              </Button>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3">
            <StatPill value={stats.total} label={t("Total Assets")} testid="promo-stat-total" />
            <StatPill value={stats.categories} label={t("Categories Used")} testid="promo-stat-categories" />
            <StatPill value={stats.public} label={t("Public")} testid="promo-stat-public" />
            <StatPill value={`${stats.sizeMb} MB`} label={t("Storage")} testid="promo-stat-size" />
          </div>
        </div>

        {/* ── filters ─── */}
        <div className="bg-white border border-slate-200 rounded-md p-4 grid grid-cols-1 md:grid-cols-4 gap-x-4 gap-y-3">
          <div>
            <Label className="font-mono text-[9px] uppercase tracking-wider text-slate-500">
              {t("Search")}
            </Label>
            <div className="relative mt-1">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t("name, description, tag…")}
                className="h-9 pl-8 text-sm"
                data-testid="promo-search-input"
              />
            </div>
          </div>
          <div>
            <Label className="font-mono text-[9px] uppercase tracking-wider text-slate-500">
              {t("Category")}
            </Label>
            <Select value={filterCategory} onValueChange={setFilterCategory}>
              <SelectTrigger className="h-9 mt-1 text-sm" data-testid="promo-filter-category">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">{t("All categories")}</SelectItem>
                {categories.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="font-mono text-[9px] uppercase tracking-wider text-slate-500">
              {t("Visibility")}
            </Label>
            <Select value={filterVisibility} onValueChange={setFilterVisibility}>
              <SelectTrigger className="h-9 mt-1 text-sm" data-testid="promo-filter-visibility">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">{t("All visibilities")}</SelectItem>
                {VISIBILITIES.map((v) => (
                  <SelectItem key={v} value={v}>
                    {v}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-end">
            <Button
              variant="ghost"
              onClick={() => {
                setSearch("");
                setFilterCategory("__all__");
                setFilterVisibility("__all__");
              }}
              className="h-9 text-xs font-mono uppercase tracking-wider w-full"
              data-testid="promo-clear-filters"
            >
              <X className="w-3 h-3 mr-1" /> {t("Clear filters")}
            </Button>
          </div>
        </div>

        {/* ── grid ─── */}
        {loading ? (
          <div className="bg-white border border-slate-200 rounded-md p-12 flex flex-col items-center gap-2">
            <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
            <div className="font-mono text-xs uppercase tracking-wider text-slate-500">
              {t("Loading library…")}
            </div>
          </div>
        ) : assets.length === 0 ? (
          <div
            className="bg-white border-2 border-dashed border-slate-200 rounded-md p-12 flex flex-col items-center gap-3 text-center"
            data-testid="promo-empty-state"
          >
            <Film className="w-10 h-10 text-slate-400" />
            <div className="font-display text-lg font-black text-slate-700">
              {t("No assets yet")}
            </div>
            <p className="text-sm text-slate-500 max-w-md leading-relaxed">
              {t(
                "Upload your first cinematic platform clip to start building the MASCI media library. Recommended naming: WorkflowName_DeviceType_Aspect_Resolution.mp4"
              )}
            </p>
            <Button
              size="sm"
              onClick={() => setUploadOpen(true)}
              className="mt-2 bg-slate-900 hover:bg-slate-800 text-white"
              data-testid="promo-empty-upload-btn"
            >
              <Upload className="w-4 h-4 mr-1" /> {t("Upload first asset")}
            </Button>
          </div>
        ) : (
          <div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
            data-testid="promo-assets-grid"
          >
            {assets.map((a) => (
              <AssetCard
                key={a.id}
                asset={a}
                onPreview={setPreviewAsset}
                onEdit={setEditAsset}
                onDelete={handleDelete}
                onCopyLink={handleCopyLink}
                t={t}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── upload dialog ─── */}
      <UploadDialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        categories={categories}
        onSubmit={handleUpload}
        t={t}
      />

      {/* ── preview dialog ─── */}
      <PreviewDialog
        asset={previewAsset}
        onClose={() => setPreviewAsset(null)}
        t={t}
      />

      {/* ── edit dialog ─── */}
      <EditDialog
        asset={editAsset}
        onClose={() => setEditAsset(null)}
        categories={categories}
        onSaved={() => {
          setEditAsset(null);
          refresh();
        }}
        t={t}
      />
    </AdminShell>
  );
}

// ─── Upload Dialog ──────────────────────────────────────────────────
function UploadDialog({ open, onClose, categories, onSubmit, t }) {
  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [visibility, setVisibility] = useState("internal");
  const [duration, setDuration] = useState("");
  const [resolution, setResolution] = useState("");
  const [aspect, setAspect] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) {
      setFile(null);
      setName("");
      setCategory("");
      setDescription("");
      setTags("");
      setVisibility("internal");
      setDuration("");
      setResolution("");
      setAspect("");
      setBusy(false);
    }
  }, [open]);

  const submit = async (e) => {
    e.preventDefault();
    if (!file || !name.trim() || !category) {
      toast.error(t("File, name, and category are required"));
      return;
    }
    setBusy(true);
    const fd = new FormData();
    fd.append("file", file);
    fd.append("name", name);
    fd.append("category", category);
    fd.append("description", description);
    fd.append("tags", tags);
    fd.append("visibility", visibility);
    if (duration) fd.append("duration_seconds", duration);
    if (resolution) fd.append("resolution", resolution);
    if (aspect) fd.append("aspect_ratio", aspect);
    await onSubmit(fd);
    setBusy(false);
  };

  return (
    <Dialog open={open} onOpenChange={(o) => (!o ? onClose() : null)}>
      <DialogContent className="max-w-2xl" data-testid="promo-upload-dialog">
        <DialogHeader>
          <DialogTitle className="font-display font-black uppercase tracking-tight">
            {t("Upload Promo Asset")}
          </DialogTitle>
          <DialogDescription className="leading-relaxed">
            {t("Streaming straight to Cloudflare R2. 500 MB cap per asset.")}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-3 py-2">
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
              {t("File")} *
            </Label>
            <Input
              type="file"
              accept="video/*,image/*"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="mt-1 cursor-pointer"
              data-testid="promo-upload-file"
              required
            />
            {file && (
              <div className="font-mono text-[10px] text-slate-500 mt-1">
                {(file.size / 1024 / 1024).toFixed(1)} MB · {file.type || "—"}
              </div>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                {t("Name")} *
              </Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Daily Report Workflow · Desktop"
                className="mt-1"
                data-testid="promo-upload-name"
                required
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                {t("Category")} *
              </Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="mt-1" data-testid="promo-upload-category">
                  <SelectValue placeholder={t("Pick one")} />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
              {t("Description")}
            </Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t("What does this clip show? What workflow / screens / mood?")}
              className="mt-1"
              rows={3}
              data-testid="promo-upload-description"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                {t("Tags (comma separated)")}
              </Label>
              <Input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="daily-report, field, desktop, workflow"
                className="mt-1"
                data-testid="promo-upload-tags"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                {t("Visibility")}
              </Label>
              <Select value={visibility} onValueChange={setVisibility}>
                <SelectTrigger className="mt-1" data-testid="promo-upload-visibility">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VISIBILITIES.map((v) => (
                    <SelectItem key={v} value={v}>
                      {v}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                {t("Duration (s)")}
              </Label>
              <Input
                type="number"
                step="0.1"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                placeholder="12"
                className="mt-1"
                data-testid="promo-upload-duration"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                {t("Resolution")}
              </Label>
              <Input
                value={resolution}
                onChange={(e) => setResolution(e.target.value)}
                placeholder="1920x1080"
                className="mt-1"
                data-testid="promo-upload-resolution"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                {t("Aspect ratio")}
              </Label>
              <Input
                value={aspect}
                onChange={(e) => setAspect(e.target.value)}
                placeholder="16:9"
                className="mt-1"
                data-testid="promo-upload-aspect"
              />
            </div>
          </div>
          <DialogFooter className="gap-2 pt-3">
            <Button type="button" variant="outline" onClick={onClose} disabled={busy}>
              {t("Cancel")}
            </Button>
            <Button
              type="submit"
              disabled={busy || !file || !name.trim() || !category}
              className="bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide"
              data-testid="promo-upload-submit"
            >
              {busy ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Uploading…")}
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-1" /> {t("Upload Asset")}
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─── Preview Dialog ─────────────────────────────────────────────────
function PreviewDialog({ asset, onClose, t }) {
  const [playbackUrl, setPlaybackUrl] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!asset) {
      setPlaybackUrl(null);
      return;
    }
    setLoading(true);
    api
      .get(`/admin/promo-assets/${asset.id}`)
      .then((r) => setPlaybackUrl(r.data?.asset?.playback_url || null))
      .catch((e) =>
        toast.error(operationalError(e, t("Could not load preview")))
      )
      .finally(() => setLoading(false));
  }, [asset, t]);

  const isVideo = (asset?.content_type || "").startsWith("video/");
  const isImage = (asset?.content_type || "").startsWith("image/");

  return (
    <Dialog open={!!asset} onOpenChange={(o) => (!o ? onClose() : null)}>
      <DialogContent className="max-w-4xl" data-testid="promo-preview-dialog">
        <DialogHeader>
          <DialogTitle className="font-display font-black uppercase tracking-tight">
            {asset?.name}
          </DialogTitle>
          <DialogDescription className="font-mono text-[10px] uppercase tracking-wider">
            {asset?.category}
          </DialogDescription>
        </DialogHeader>
        <div className="bg-slate-900 rounded-md aspect-video flex items-center justify-center overflow-hidden">
          {loading ? (
            <Loader2 className="w-8 h-8 text-slate-400 animate-spin" />
          ) : !playbackUrl ? (
            <div className="text-slate-500 font-mono text-xs">
              {t("Preview unavailable")}
            </div>
          ) : isVideo ? (
            <video
              src={playbackUrl}
              controls
              autoPlay
              muted
              className="w-full h-full"
              data-testid="promo-preview-video"
            />
          ) : isImage ? (
            <img src={playbackUrl} alt={asset?.name || ""} className="w-full h-full object-contain" />
          ) : (
            <a
              href={playbackUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-200 underline"
            >
              {t("Open file")}
            </a>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Edit Dialog ────────────────────────────────────────────────────
function EditDialog({ asset, onClose, categories, onSaved, t }) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [visibility, setVisibility] = useState("internal");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (asset) {
      setName(asset.name || "");
      setCategory(asset.category || "");
      setDescription(asset.description || "");
      setTags((asset.tags || []).join(", "));
      setVisibility(asset.visibility || "internal");
    }
  }, [asset]);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.patch(`/admin/promo-assets/${asset.id}`, {
        name: name.trim(),
        category,
        description: description.trim(),
        tags: tags.split(",").map((s) => s.trim()).filter(Boolean),
        visibility,
      });
      toast.success(t("Asset updated"));
      onSaved();
    } catch (e2) {
      toast.error(operationalError(e2, t("Update failed")));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={!!asset} onOpenChange={(o) => (!o ? onClose() : null)}>
      <DialogContent className="max-w-xl" data-testid="promo-edit-dialog">
        <DialogHeader>
          <DialogTitle className="font-display font-black uppercase tracking-tight">
            {t("Edit Asset")}
          </DialogTitle>
        </DialogHeader>
        {asset && (
          <form onSubmit={submit} className="space-y-3 py-2">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                {t("Name")}
              </Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} className="mt-1" data-testid="promo-edit-name" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                  {t("Category")}
                </Label>
                <Select value={category} onValueChange={setCategory}>
                  <SelectTrigger className="mt-1" data-testid="promo-edit-category">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                  {t("Visibility")}
                </Label>
                <Select value={visibility} onValueChange={setVisibility}>
                  <SelectTrigger className="mt-1" data-testid="promo-edit-visibility">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {VISIBILITIES.map((v) => (
                      <SelectItem key={v} value={v}>
                        {v}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                {t("Description")}
              </Label>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="mt-1"
                data-testid="promo-edit-description"
              />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-wider text-slate-700 font-bold">
                {t("Tags (comma separated)")}
              </Label>
              <Input value={tags} onChange={(e) => setTags(e.target.value)} className="mt-1" data-testid="promo-edit-tags" />
            </div>
            <DialogFooter className="gap-2 pt-3">
              <Button type="button" variant="outline" onClick={onClose} disabled={busy}>
                {t("Cancel")}
              </Button>
              <Button
                type="submit"
                disabled={busy}
                className="bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide"
                data-testid="promo-edit-submit"
              >
                {busy ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Saving…")}
                  </>
                ) : (
                  <>{t("Save Changes")}</>
                )}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
