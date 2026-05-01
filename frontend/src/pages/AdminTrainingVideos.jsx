import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Save, Video, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MasciLogo } from "@/components/MasciLogo";
import { api } from "@/lib/api";
import { LESSONS, TRACKS } from "@/data/training";
import { toast } from "sonner";

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
      toast.error(e?.response?.data?.detail || "Could not save videos");
    } finally {
      setSaving(false);
    }
  };

  const tracks = Object.values(TRACKS);
  const filledCount = Object.values(videos).filter((v) => v && v.trim()).length;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-5xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link
            to="/admin"
            className="inline-flex items-center text-white hover:text-red-400 text-sm font-bold uppercase tracking-wide"
            data-testid="training-videos-back"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Admin
          </Link>
          <MasciLogo variant="lockup" size="lg" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
          <span className="w-20" />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
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
              {filledCount} / {LESSONS.length} filled
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
                  const url = videos[l.slug] || "";
                  return (
                    <div
                      key={l.slug}
                      className="bg-white border-2 border-slate-200 rounded-md p-4 flex items-center gap-3 flex-wrap sm:flex-nowrap"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-bold text-slate-900 truncate">
                          {l.title}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono uppercase tracking-[0.15em] mt-0.5 truncate">
                          {l.slug}
                        </div>
                      </div>
                      <Input
                        value={url}
                        onChange={(e) =>
                          setVideos((prev) => ({ ...prev, [l.slug]: e.target.value }))
                        }
                        placeholder="https://www.youtube.com/watch?v=…  or  https://loom.com/share/…"
                        className="flex-1 min-w-[260px] h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-red-700"
                        data-testid={`video-url-${l.slug}`}
                      />
                      {url && (
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="shrink-0 inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700 hover:text-red-700"
                        >
                          <ExternalLink className="w-3.5 h-3.5" /> open
                        </a>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>
          );
        })}
      </main>
    </div>
  );
}
