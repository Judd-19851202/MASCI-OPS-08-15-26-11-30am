import React, { useEffect, useState } from "react";
import { Save, Video, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PortalShell } from "@/design-system";
import AdminSideNavV2 from "@/components/admin/sidebar/SideNavV2";
import { api } from "@/lib/api";
import { LESSONS, TRACKS } from "@/data/training";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";

/**
 * AdminTrainingVideos — paste YouTube / Loom / Vimeo / Wistia URLs per
 * lesson slug. Saves to the backend `training_videos` collection. Requires
 * admin-strict token (PM tokens are rejected by the backend).
 */
export default function AdminTrainingVideos() {
  const [videos, setVideos] = useState({});
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await api.get("/training/videos");
        if (mounted) setVideos(res?.data?.videos || {});
      } catch {
        toast.error("Could not load training videos");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const onSave = async () => {
    setSaving(true);
    try {
      const res = await api.put("/admin/training/videos", { videos });
      setVideos(res?.data?.videos || {});
      toast.success("Training videos saved");
    } catch (e) {
      toast.error(operationalError(e, "Could not save videos"));
    } finally {
      setSaving(false);
    }
  };

  const tracks = Object.values(TRACKS);
  // Normalize legacy single-string entries to {en, es} shape for the UI
  const norm = (v) => {
    if (!v) return { en: "", es: "" };
    if (typeof v === "string") return { en: v, es: "" };
    return { en: v.en || "", es: v.es || "" };
  };
  const filledEn = Object.values(videos).filter((v) => norm(v).en).length;
  const filledEs = Object.values(videos).filter((v) => norm(v).es).length;

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Admin · Training Videos"
      pageTitle="Paste a video URL per lesson"
      subtitle="Supports YouTube · Loom · Vimeo · Wistia"
      sideNav={<AdminSideNavV2 />}
      primaryActions={
        <Button onClick={onSave} disabled={saving} className="h-9 bg-red-700 hover:bg-red-800 text-white text-xs font-bold" data-testid="training-videos-save">
          <Save className="w-3.5 h-3.5 mr-1" /> {saving ? "Saving…" : "Save"}
        </Button>
      }
    >
      <div className="max-w-5xl mx-auto px-5 sm:px-6 py-6 sm:py-8" data-testid="admin-training-videos-page">
        <div className="mb-8 flex items-start justify-between gap-4 flex-wrap">
          <div>
            <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700 font-bold flex items-center gap-2">
              <Video className="w-4 h-4" /> Training Videos
            </span>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-2">
              Paste a video URL per lesson
            </h1>
            <p className="text-slate-600 text-sm mt-2 max-w-2xl leading-relaxed">
              Supports YouTube (watch / youtu.be / embed), Loom (share URL),
              Vimeo, Wistia. Leave a slug blank to hide the embed on that
              lesson. Changes are live the moment you click Save — no deploy
              needed.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
              EN {filledEn}/{LESSONS.length} · ES {filledEs}/{LESSONS.length}
            </span>
            <Button
              onClick={onSave}
              disabled={saving || loading}
              className="h-11 px-5 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide border-b-2 border-red-900"
              data-testid="training-videos-save"
            >
              <Save className="w-4 h-4 mr-1.5" />
              {saving ? "Saving…" : "Save All"}
            </Button>
          </div>
        </div>

        {tracks.map((track) => {
          const trackLessons = LESSONS.filter((l) => l.track === track.slug);
          return (
            <section key={track.slug} className="mb-10" data-testid={`track-${track.slug}-section`}>
              <h2 className="font-display text-xl font-black text-slate-900 mb-3">
                {track.title}
                <span className="ml-2 text-xs font-mono uppercase tracking-[0.2em] text-slate-500 font-normal">
                  {trackLessons.length} lessons
                </span>
              </h2>
              <div className="space-y-3">
                {trackLessons.map((l) => {
                  const cur = norm(videos[l.slug]);
                  return (
                    <div
                      key={l.slug}
                      className="bg-white border border-slate-200 rounded-md p-4"
                    >
                      <div className="flex items-baseline justify-between gap-3 mb-2 flex-wrap">
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-bold text-slate-900 truncate">
                            {l.title}
                          </div>
                          <div className="text-[11px] text-slate-500 font-mono uppercase tracking-[0.15em] mt-0.5 truncate">
                            {l.slug}
                          </div>
                        </div>
                      </div>
                      <div className="grid sm:grid-cols-2 gap-2.5">
                        {[
                          { code: "en", label: "English", color: "border-slate-300 focus-visible:ring-red-700" },
                          { code: "es", label: "Español", color: "border-amber-300 focus-visible:ring-amber-600" },
                        ].map(({ code, label, color }) => {
                          const url = cur[code];
                          return (
                            <div key={code} className="flex items-center gap-2 min-w-0">
                              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 shrink-0 w-12">
                                {label}
                              </span>
                              <Input
                                value={url}
                                onChange={(e) =>
                                  setVideos((prev) => ({
                                    ...prev,
                                    [l.slug]: { ...norm(prev[l.slug]), [code]: e.target.value },
                                  }))
                                }
                                placeholder={code === "en" ? "https://… (English MP4 / YouTube / Loom)" : "https://… (Spanish MP4 — optional)"}
                                className={`flex-1 min-w-0 h-10 text-sm border-2 ${color}`}
                                data-testid={`video-url-${l.slug}-${code}`}
                              />
                              {url && (
                                <a
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="shrink-0 inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700 hover:text-red-700"
                                >
                                  <ExternalLink className="w-3.5 h-3.5" />
                                </a>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>
    </PortalShell>
  );
}
