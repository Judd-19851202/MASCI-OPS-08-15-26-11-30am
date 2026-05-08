import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  Download,
  Mail,
  Loader2,
  X,
  ChevronDown,
  ChevronRight,
  CheckSquare,
  Square,
  RefreshCw,
  Camera,
  ImageIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { toast } from "sonner";

/**
 * <JobPhotosLibrary>
 *
 * Phase 1 of the Job Photos feature — a read-only aggregator that surfaces
 * every photo crews have already submitted on Daily Reports, Site
 * Inspections, and QA/QC inspections, organized into a Job → Week
 * accordion. Multi-select + download ZIP + email a packet.
 *
 * Photos are NOT duplicated — the backend stores only metadata in
 * `job_photos`, and on render we lazy-fetch each photo's data URL via
 * GET /api/job-photos/{id}/raw. Caches in component state so a thumbnail
 * is only fetched once.
 *
 * Used by both /admin/photos (admin sees all jobs) and /pm/photos (PM
 * sees only assigned jobs — backend handles scoping).
 */

const SOURCE_LABELS = {
  daily_report: "Daily Report",
  inspection: "Site Inspection",
  qaqc: "QA/QC",
};
const SOURCE_COLORS = {
  daily_report: "bg-red-700",
  inspection: "bg-amber-600",
  qaqc: "bg-emerald-700",
};

export default function JobPhotosLibrary({ portalKey = "admin" }) {
  const { t } = useT();
  const [items, setItems] = useState(null); // null = loading
  const [openMap, setOpenMap] = useState({}); // { "<jobKey>": true, "<jobKey>::<week>": true }
  const [selected, setSelected] = useState(new Set()); // photo ids
  const [filter, setFilter] = useState({ source: "", search: "" });
  const [thumbCache, setThumbCache] = useState({}); // id -> data_url
  const [lightboxId, setLightboxId] = useState(null);
  const [busy, setBusy] = useState(false);

  // Load metadata
  useEffect(() => {
    api.get("/job-photos").then(
      (res) => setItems(res.data.items || []),
      () => {
        toast.error(t("Failed to load photos"));
        setItems([]);
      }
    );
  }, [t]);

  // Group: jobKey -> { number, name, weeks: { weekTag -> [items] } }
  const folders = useMemo(() => {
    const map = new Map();
    const q = filter.search.trim().toLowerCase();
    for (const it of items || []) {
      if (filter.source && it.source !== filter.source) continue;
      if (
        q &&
        !(
          (it.project_name || "").toLowerCase().includes(q) ||
          (it.project_number || "").toLowerCase().includes(q) ||
          (it.submitter || "").toLowerCase().includes(q)
        )
      )
        continue;
      const number = (it.project_number || "—").trim();
      const name = (it.project_name || t("(No Job)")).trim();
      const key = `${number}::${name}`;
      if (!map.has(key))
        map.set(key, { key, number, name, weeks: new Map(), latest: null });
      const folder = map.get(key);
      const week = it.week_of || "unknown-week";
      if (!folder.weeks.has(week)) folder.weeks.set(week, []);
      folder.weeks.get(week).push(it);
      if (!folder.latest || it.record_date > folder.latest)
        folder.latest = it.record_date;
    }
    const arr = Array.from(map.values()).map((f) => ({
      ...f,
      weeks: Array.from(f.weeks.entries())
        .sort((a, b) => (a[0] < b[0] ? 1 : -1))
        .map(([week, photos]) => ({
          week,
          photos: photos.sort((a, b) =>
            a.record_date < b.record_date ? 1 : -1
          ),
        })),
    }));
    arr.sort((a, b) =>
      a.latest && b.latest ? (a.latest < b.latest ? 1 : -1) : 0
    );
    return arr;
  }, [items, filter, t]);

  const total = items?.length || 0;

  // ── Thumbnail loader (now signed-URL, no axios round-trip) ────────────
  // Each photo metadata row from /api/job-photos carries a 1h HMAC-signed
  // ``thumb_token`` we can plug straight into <img src=...?t=...>. That:
  //   • Lets the browser cache + service worker actually do their job
  //     (axios+blob+objectURL bypassed both → ~1s/photo on a warm reload).
  //   • Drops 60 axios requests + 60 token-validation passes per gallery
  //     view → backend worker stays free for /api/health, killing the
  //     phantom "server down" red banner reports.
  //   • Lazy-decoded by the <img> tag itself (loading="lazy") so the
  //     browser only fetches what scrolls into view.
  // We still keep the OBSERVER below for visibility tracking (used to
  // gate the lightbox preloader), but no per-thumb fetch is needed.
  const THUMB_BASE = `${process.env.REACT_APP_BACKEND_URL}/api/job-photos`;
  const thumbSrc = (it) =>
    it?.thumb_token
      ? `${THUMB_BASE}/${encodeURIComponent(it.id)}/thumb-signed?t=${encodeURIComponent(it.thumb_token)}`
      : null;

  // Full-resolution loader for the lightbox only.
  const ensureFullSrc = async (id) => {
    const key = `full:${id}`;
    if (thumbCache[key]) return;
    try {
      const res = await api.get(`/job-photos/${id}/raw`);
      setThumbCache((p) => ({ ...p, [key]: res.data.data_url }));
    } catch {
      setThumbCache((p) => ({ ...p, [key]: "error" }));
    }
  };

  // ── Selection helpers ────────────────────────────────────────────────
  const toggle = (id) =>
    setSelected((p) => {
      const next = new Set(p);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  const selectMany = (ids) =>
    setSelected((p) => {
      const next = new Set(p);
      const allIn = ids.every((i) => p.has(i));
      ids.forEach((i) => (allIn ? next.delete(i) : next.add(i)));
      return next;
    });
  const clearSelection = () => setSelected(new Set());

  // ── Bulk actions ─────────────────────────────────────────────────────
  const downloadZip = async () => {
    if (selected.size === 0) return;
    setBusy(true);
    try {
      const res = await api.post(
        "/job-photos/zip",
        { photo_ids: Array.from(selected) },
        { responseType: "blob" }
      );
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `masci-photos-${new Date()
        .toISOString()
        .slice(0, 10)}.zip`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(t("Downloaded {n} photos.").replace("{n}", selected.size));
    } catch {
      toast.error(t("Download failed"));
    } finally {
      setBusy(false);
    }
  };

  const [emailDialog, setEmailDialog] = useState(false);
  const [emailForm, setEmailForm] = useState({ to: "", subject: "", note: "" });

  const sendEmail = async () => {
    if (!emailForm.to.includes("@")) {
      toast.error(t("Enter a valid email"));
      return;
    }
    setBusy(true);
    try {
      const res = await api.post("/job-photos/email", {
        photo_ids: Array.from(selected),
        ...emailForm,
      });
      toast.success(
        t("Emailed {n} photos.").replace("{n}", res.data.included || 0)
      );
      setEmailDialog(false);
      setEmailForm({ to: "", subject: "", note: "" });
      clearSelection();
    } catch {
      toast.error(t("Email failed"));
    } finally {
      setBusy(false);
    }
  };

  const reindex = async () => {
    setBusy(true);
    try {
      const res = await api.post("/job-photos/admin/reindex");
      toast.success(
        t("Re-indexed {n} photos.").replace("{n}", res.data.total || 0)
      );
      const r2 = await api.get("/job-photos");
      setItems(r2.data.items || []);
    } catch {
      toast.error(t("Re-index failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b-4 border-red-700 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <Link
              to={portalKey === "pm" ? "/pm" : "/admin"}
              className="p-2 -ml-2 text-slate-700 hover:text-red-700"
              data-testid="photos-back"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <MasciLogo size="sm" />
            <div className="min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                {portalKey === "pm" ? t("PM Portal") : t("Admin")}
              </div>
              <h1 className="font-display text-lg sm:text-xl font-bold text-slate-900 truncate">
                {t("Job Photos")}
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <LangToggle />
            {portalKey === "admin" && (
              <Button
                variant="outline"
                size="sm"
                onClick={reindex}
                disabled={busy}
                className="border-2"
                data-testid="photos-reindex"
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${busy ? "animate-spin" : ""}`} />
                {t("Re-index")}
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Filter bar */}
        <div
          className="bg-white border-2 border-slate-200 rounded-md p-3 mb-4 flex flex-wrap gap-2 items-center"
          data-testid="photos-filter-bar"
        >
          <Input
            value={filter.search}
            onChange={(e) =>
              setFilter((p) => ({ ...p, search: e.target.value }))
            }
            placeholder={t("Search jobs / submitter…")}
            className="flex-1 min-w-[200px] h-10 border-2"
            data-testid="photos-search"
          />
          <select
            value={filter.source}
            onChange={(e) =>
              setFilter((p) => ({ ...p, source: e.target.value }))
            }
            className="h-10 px-3 border-2 border-slate-300 rounded-md font-mono text-sm bg-white"
            data-testid="photos-source-filter"
          >
            <option value="">{t("All sources")}</option>
            <option value="daily_report">{t("Daily Reports")}</option>
            <option value="inspection">{t("Site Inspections")}</option>
            <option value="qaqc">{t("QA/QC")}</option>
          </select>
          <span className="font-mono text-xs uppercase tracking-wider text-slate-500 ml-auto">
            {t("Total")}: {total}
          </span>
        </div>

        {/* Folders */}
        {items === null ? (
          <div className="p-16 text-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mx-auto" />
          </div>
        ) : folders.length === 0 ? (
          <div className="p-16 text-center text-slate-500" data-testid="photos-empty">
            <ImageIcon className="w-12 h-12 mx-auto mb-3 text-slate-300" />
            {total === 0
              ? t("No photos yet — submit a Daily Report, Site Inspection, or QA/QC to populate.")
              : t("No photos match your filter.")}
          </div>
        ) : (
          <ul className="space-y-3" data-testid="photos-folders">
            {folders.map((folder) => {
              const open = !!openMap[folder.key];
              const folderTotal = folder.weeks.reduce(
                (n, w) => n + w.photos.length,
                0
              );
              return (
                <li
                  key={folder.key}
                  className="bg-white border-2 border-slate-200 rounded-md overflow-hidden"
                >
                  <button
                    type="button"
                    onClick={() =>
                      setOpenMap((p) => ({ ...p, [folder.key]: !open }))
                    }
                    className="w-full px-4 py-3 flex items-center gap-3 hover:bg-red-50 transition-colors"
                    data-testid={`photos-folder-${folder.number}`}
                  >
                    {open ? (
                      <ChevronDown className="w-5 h-5 text-red-700" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-slate-500" />
                    )}
                    {folder.number !== "—" && (
                      <span className="inline-flex items-center px-2 py-0.5 bg-slate-800 text-white text-[10px] font-mono uppercase tracking-wider rounded font-bold">
                        #{folder.number}
                      </span>
                    )}
                    <span className="font-display text-base sm:text-lg font-bold text-slate-900 flex-1 text-left truncate">
                      {folder.name}
                    </span>
                    <span className="inline-flex items-center justify-center min-w-[2.5rem] h-7 px-2 rounded bg-red-700 text-white text-xs font-mono font-bold">
                      {folderTotal}
                    </span>
                  </button>
                  {open && (
                    <div className="border-t border-slate-100 bg-slate-50/40">
                      {folder.weeks.map((wk) => {
                        const wkKey = `${folder.key}::${wk.week}`;
                        const wkOpen = openMap[wkKey] !== false; // weeks default open
                        const wkIds = wk.photos.map((p) => p.id);
                        const allSel = wkIds.every((id) => selected.has(id));
                        return (
                          <div
                            key={wkKey}
                            className="border-b border-slate-100 last:border-b-0"
                          >
                            <div className="px-4 py-2 flex items-center gap-2 bg-white">
                              <button
                                type="button"
                                onClick={() =>
                                  setOpenMap((p) => ({ ...p, [wkKey]: !wkOpen }))
                                }
                                className="text-slate-600 hover:text-slate-900"
                                data-testid={`photos-week-${wk.week}`}
                              >
                                {wkOpen ? (
                                  <ChevronDown className="w-4 h-4" />
                                ) : (
                                  <ChevronRight className="w-4 h-4" />
                                )}
                              </button>
                              <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-slate-700">
                                {t("Week of")} {wk.week}
                              </span>
                              <span className="text-xs text-slate-500">
                                · {wk.photos.length} {t("photos")}
                              </span>
                              <button
                                type="button"
                                onClick={() => selectMany(wkIds)}
                                className="ml-auto text-xs font-mono uppercase tracking-wider text-red-700 hover:text-red-900"
                                data-testid={`photos-select-week-${wk.week}`}
                              >
                                {allSel ? t("Deselect week") : t("Select all week")}
                              </button>
                            </div>
                            {wkOpen && (
                              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2 p-3">
                                {wk.photos.map((p) => (
                                  <PhotoTile
                                    key={p.id}
                                    photo={p}
                                    src={thumbSrc(p)}
                                    selected={selected.has(p.id)}
                                    onToggle={() => toggle(p.id)}
                                    onZoom={() => setLightboxId(p.id)}
                                  />
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </main>

      {/* Floating action bar — only when something is selected */}
      {selected.size > 0 && (
        <div
          className="fixed bottom-0 inset-x-0 bg-white border-t-4 border-red-700 shadow-xl z-40"
          data-testid="photos-actionbar"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3 flex-wrap">
            <div className="font-mono text-sm font-bold text-slate-900">
              {t("Selected")}: <span className="text-red-700">{selected.size}</span>
            </div>
            <div className="flex items-center gap-2 ml-auto">
              <Button
                variant="ghost"
                size="sm"
                onClick={clearSelection}
                data-testid="photos-clear"
              >
                <X className="w-4 h-4 mr-1" /> {t("Clear")}
              </Button>
              <Button
                onClick={() => setEmailDialog(true)}
                disabled={busy}
                className="bg-slate-900 hover:bg-slate-800 text-white"
                data-testid="photos-email-btn"
              >
                <Mail className="w-4 h-4 mr-1" /> {t("Email")}
              </Button>
              <Button
                onClick={downloadZip}
                disabled={busy}
                className="bg-red-700 hover:bg-red-800 text-white"
                data-testid="photos-download-btn"
              >
                {busy ? (
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                ) : (
                  <Download className="w-4 h-4 mr-1" />
                )}
                {t("Download ZIP")}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Lightbox — uses full-resolution /raw, not the small /thumb */}
      {lightboxId && (
        <Lightbox
          id={lightboxId}
          src={thumbCache[`full:${lightboxId}`]}
          meta={(items || []).find((i) => i.id === lightboxId)}
          onClose={() => setLightboxId(null)}
          onLoad={() => ensureFullSrc(lightboxId)}
        />
      )}

      {/* Email dialog */}
      {emailDialog && (
        <EmailDialog
          form={emailForm}
          setForm={setEmailForm}
          count={selected.size}
          onCancel={() => setEmailDialog(false)}
          onSend={sendEmail}
          busy={busy}
        />
      )}
    </div>
  );
}

function PhotoTile({ photo, src, selected, onToggle, onZoom }) {
  const [broken, setBroken] = useState(false);

  // Plain <img src=signed-url loading="lazy"> — the browser handles
  // visibility tracking + native lazy-loading. The previous
  // IntersectionObserver was needed because we were axios-fetching
  // each thumb and converting to an object URL; now that the URL is
  // browser-cacheable directly, the OS-level lazy loader is the right
  // tool for the job. ~10× less JS work per gallery scroll.
  const renderable = typeof src === "string" && src.length > 10 && !broken;
  return (
    <div
      className={`relative group rounded overflow-hidden border-2 ${
        selected ? "border-red-700 ring-2 ring-red-300" : "border-slate-200"
      } cursor-pointer aspect-square bg-slate-100`}
      data-testid={`photo-tile-${photo.id}`}
    >
      {renderable ? (
        <img
          src={src}
          alt=""
          loading="lazy"
          decoding="async"
          fetchPriority="low"
          className="w-full h-full object-cover"
          onClick={onZoom}
          onError={() => setBroken(true)}
        />
      ) : (
        <div
          className="w-full h-full flex items-center justify-center text-slate-300"
          onClick={onZoom}
        >
          {broken || !src ? (
            <ImageIcon className="w-6 h-6 text-slate-400" title="Photo unavailable" />
          ) : (
            <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
          )}
        </div>
      )}
      {/* Source badge */}
      <span
        className={`absolute top-1 left-1 px-1.5 py-0.5 ${
          SOURCE_COLORS[photo.source] || "bg-slate-700"
        } text-white text-[9px] font-mono uppercase rounded`}
      >
        {SOURCE_LABELS[photo.source] || photo.source}
      </span>
      {/* Select toggle */}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onToggle();
        }}
        className="absolute top-1 right-1 p-1 bg-white/95 rounded shadow-sm hover:bg-white"
        data-testid={`photo-select-${photo.id}`}
      >
        {selected ? (
          <CheckSquare className="w-4 h-4 text-red-700" />
        ) : (
          <Square className="w-4 h-4 text-slate-400" />
        )}
      </button>
      {/* Date footer */}
      <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent text-white text-[10px] font-mono px-1.5 py-1 truncate pointer-events-none">
        {photo.record_date}
      </div>
    </div>
  );
}

function Lightbox({ src, meta, onClose, onLoad }) {
  useEffect(() => {
    onLoad();
    const onEsc = (e) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const renderable =
    typeof src === "string" &&
    src !== "loading" &&
    src !== "error" &&
    (src.startsWith("data:image/") || src.startsWith("blob:") || src.startsWith("http")) &&
    src.length > 30;
  return (
    <div
      className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
      onClick={onClose}
      data-testid="photos-lightbox"
      role="dialog"
      aria-modal="true"
      aria-label="Photo preview"
    >
      <button
        type="button"
        onClick={onClose}
        className="absolute top-4 right-4 p-2 bg-white/10 hover:bg-white/20 text-white rounded-full"
        aria-label="Close"
        data-testid="photos-lightbox-close"
      >
        <X className="w-6 h-6" />
      </button>
      <div
        className="max-w-5xl max-h-full flex flex-col items-center"
        onClick={(e) => e.stopPropagation()}
      >
        {renderable ? (
          <img
            src={src}
            alt=""
            className="max-w-full max-h-[85vh] object-contain rounded"
          />
        ) : src ? (
          <div className="px-8 py-12 bg-white/5 rounded text-white/70 text-sm font-mono text-center">
            <Camera className="w-12 h-12 mx-auto mb-3 text-white/40" />
            Photo data unavailable or corrupt.
          </div>
        ) : (
          <Loader2 className="w-8 h-8 animate-spin text-white" />
        )}
        {meta && (
          <div className="mt-3 text-white/90 text-sm font-mono text-center">
            <div className="font-bold">
              #{meta.project_number} · {meta.project_name}
            </div>
            <div className="text-white/60 text-xs mt-1">
              {SOURCE_LABELS[meta.source] || meta.source} · {meta.record_date} ·{" "}
              {meta.submitter}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function EmailDialog({ form, setForm, count, onCancel, onSend, busy }) {
  const { t } = useT();
  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
      data-testid="photos-email-dialog"
    >
      <div className="bg-white rounded-md max-w-md w-full p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Mail className="w-5 h-5 text-red-700" />
          <h2 className="font-display text-lg font-bold">
            {t("Email")} {count} {t("photos")}
          </h2>
        </div>
        <Input
          value={form.to}
          onChange={(e) => setForm({ ...form, to: e.target.value })}
          placeholder={t("Recipient email")}
          className="h-10 border-2"
          data-testid="photos-email-to"
        />
        <Input
          value={form.subject}
          onChange={(e) => setForm({ ...form, subject: e.target.value })}
          placeholder={t("Subject (optional)")}
          className="h-10 border-2"
          data-testid="photos-email-subject"
        />
        <textarea
          value={form.note}
          onChange={(e) => setForm({ ...form, note: e.target.value })}
          placeholder={t("Note (optional)")}
          className="w-full min-h-[80px] p-2 border-2 border-slate-300 rounded-md text-sm"
          data-testid="photos-email-note"
        />
        <p className="text-[11px] text-slate-500 font-mono">
          {t("Note: emails capped at 25MB. For larger packets use Download ZIP.")}
        </p>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onCancel} disabled={busy}>
            {t("Cancel")}
          </Button>
          <Button
            onClick={onSend}
            disabled={busy}
            className="bg-red-700 hover:bg-red-800 text-white"
            data-testid="photos-email-send"
          >
            {busy ? (
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <Mail className="w-4 h-4 mr-1" />
            )}
            {t("Send")}
          </Button>
        </div>
      </div>
    </div>
  );
}
