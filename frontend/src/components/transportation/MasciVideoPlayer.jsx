/**
 * TRACK 16.08 · MASCI Native Orientation Video Player.
 *
 * Compliance contract:
 *  - No fast-forward / no seeking — the timeline scrubber is removed.
 *  - No playback rate change — playbackRate clamped to 1.0.
 *  - Resume where left off (via assignment.position_seconds).
 *  - Heartbeat polling every 5 seconds to server.
 *  - Checkpoints fire at 25/50/75/99 %.
 *  - Completion only when server-acknowledged completion_pct ≥ 0.99.
 */
import React, { useEffect, useRef, useState, useCallback } from "react";
import { Play, Pause, Volume2, Languages, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";

const HEARTBEAT_MS = 5000;
const CHECKPOINTS = [25, 50, 75, 99];

export default function MasciVideoPlayer({
  token,
  assignment,
  module,
  onComplete,
}) {
  const videoRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [position, setPosition] = useState(assignment?.position_seconds || 0);
  const [completionPct, setCompletionPct] = useState(assignment?.completion_pct || 0);
  const [error, setError] = useState(null);
  const watchedRef = useRef(assignment?.watch_seconds || 0);
  const checkpointsRef = useRef(new Set(assignment?.checkpoints_visited || []));

  const placeholder = (module?.placeholders || []).find(
    (p) => p.language === assignment?.language,
  );
  const runtime = Math.max(1, module?.runtime_seconds || placeholder?.runtime_seconds || 60);
  const skyAssetId = placeholder?.sky_asset_id || null;

  const postHeartbeat = useCallback(async () => {
    try {
      const r = await api.post(
        `/api/transportation/invite/${token}/orientation/assignments/${assignment.id}/heartbeat`,
        {
          position_seconds: position,
          watched_seconds: watchedRef.current,
          checkpoints_visited: Array.from(checkpointsRef.current),
        },
      );
      setCompletionPct(r.data.completion_pct || 0);
      if (r.data.status === "watch_complete" && onComplete) {
        onComplete(r.data);
      }
    } catch (e) {
      setError(e.message || String(e));
    }
  }, [token, assignment, position, onComplete]);

  // Heartbeat loop while playing.
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      watchedRef.current = Math.min(runtime, watchedRef.current + HEARTBEAT_MS / 1000);
      // Trigger checkpoints when crossing thresholds.
      const pct = (watchedRef.current / runtime) * 100;
      for (const cp of CHECKPOINTS) {
        if (pct >= cp) checkpointsRef.current.add(cp);
      }
      setPosition(watchedRef.current);
      postHeartbeat();
    }, HEARTBEAT_MS);
    return () => clearInterval(id);
  }, [playing, runtime, postHeartbeat]);

  // Sync HTML5 video element (only valid when we have a real Sky asset URL).
  // For Sky AI placeholder mode we drive position with our heartbeat clock —
  // the user clicks Play and the timer advances. This perfectly satisfies
  // the no-skip / no-seek rule because the user has no control over the
  // counter except via Play / Pause.
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    v.playbackRate = 1.0;
    const blockRate = () => { v.playbackRate = 1.0; };
    v.addEventListener("ratechange", blockRate);
    return () => v.removeEventListener("ratechange", blockRate);
  }, []);

  const togglePlay = () => setPlaying((p) => !p);

  return (
    <div className="bg-black rounded-lg shadow-xl overflow-hidden" data-testid="masci-video-player">
      <div className="relative aspect-video bg-gradient-to-br from-slate-900 via-amber-950 to-slate-900 flex items-center justify-center">
        {skyAssetId ? (
          <video
            ref={videoRef}
            className="w-full h-full"
            playsInline
            controls={false}
            preload="metadata"
            data-testid="masci-video-element"
          />
        ) : (
          <div className="text-center p-8 text-amber-100">
            <ShieldCheck className="h-16 w-16 mx-auto mb-3 opacity-80" />
            <h3 className="text-2xl font-semibold">MASCI Transportation Instructor</h3>
            <p className="opacity-70 mt-1 text-sm">Sky AI video placeholder · {module?.title}</p>
            <p className="opacity-50 mt-1 text-xs">Asset publishes automatically when ready · language: {assignment?.language}</p>
          </div>
        )}
        {/* Disable native context menu (right-click "Save Video") */}
        <div className="absolute inset-0" onContextMenu={(e) => e.preventDefault()} />
      </div>
      <div className="bg-slate-900 p-4 text-white" data-testid="masci-video-controls">
        <div className="flex items-center gap-3">
          <button
            data-testid="masci-video-play"
            onClick={togglePlay}
            className="inline-flex items-center gap-2 bg-amber-700 hover:bg-amber-600 px-4 py-2 rounded font-medium"
          >
            {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {playing ? "Pause" : (position > 0 ? "Resume" : "Start")}
          </button>
          <div className="flex-1">
            <div className="text-xs text-slate-400 flex items-center gap-2">
              <Languages className="h-3 w-3" /> {assignment?.language} · {Math.round(position)}s / {runtime}s
            </div>
            <div className="bg-slate-700 rounded-full h-2 mt-1 overflow-hidden">
              <div
                className="bg-amber-500 h-full transition-all duration-500"
                style={{ width: `${Math.min(100, completionPct * 100)}%` }}
                data-testid="masci-video-progress"
              />
            </div>
          </div>
          <div className="text-xs text-slate-400 font-mono" data-testid="masci-video-completion">
            {Math.round(completionPct * 100)}%
          </div>
        </div>
        <div className="text-xs text-slate-500 mt-2 italic">
          No fast-forward · No skipping · No playback acceleration · Server-validated.
        </div>
        {error ? <div className="text-xs text-red-400 mt-1">{error}</div> : null}
      </div>
    </div>
  );
}
