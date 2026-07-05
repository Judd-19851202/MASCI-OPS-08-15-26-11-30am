import React from "react";
import { SectionCard } from "../_ui";
import {
  fetchDrV2PhotoIntel,
  acceptDrV2PhotoLink,
  dismissDrV2PhotoLink,
  resolveDrV2PhotoQuestion,
} from "@/lib/drV2Api";

/**
 * DR-ROI-001D · Photo Intelligence Panel.
 *
 * Invisible Intelligence: shows suggested links, items to verify, and
 * detected observations without ever surfacing model/provider names or
 * cost meters. Photos remain source-of-truth; every suggestion needs a
 * supervisor click to become a link.
 */
export default function PhotoIntelligencePanel({ draft }) {
  const photos = React.useMemo(() => (draft?.photos || []).map((p, i) => {
    if (typeof p === "string") return { id: p, ref: p, label: `Photo ${i + 1}` };
    return { id: p.id || p.ref || `photo-${i}`, ref: p.ref || p.url || p.id, label: p.label || `Photo ${i + 1}` };
  }), [draft?.photos]);

  const [selectedIdx, setSelectedIdx] = React.useState(0);
  const [intel, setIntel] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState(null);

  const current = photos[selectedIdx];

  React.useEffect(() => {
    let alive = true;
    async function load() {
      if (!current) { setIntel(null); return; }
      try {
        setLoading(true);
        const data = await fetchDrV2PhotoIntel(current.id, draft?.report_id);
        if (alive) setIntel(data.intel || null);
      } catch (e) {
        if (alive) setErr(e?.message || "photo intel load failed");
      } finally {
        if (alive) setLoading(false);
      }
    }
    load();
    return () => { alive = false; };
  }, [current, draft?.report_id]);

  const suggested = intel?.suggested_links || [];
  const questions = intel?.questions || [];
  const observations = intel?.observations || [];

  async function onAccept(link) {
    try {
      const res = await acceptDrV2PhotoLink({ photo_id: current.id, link_id: link.link_id });
      if (res?.intel) setIntel(res.intel);
    } catch (e) { setErr(e?.message || "accept failed"); }
  }
  async function onDismiss(link) {
    try {
      const res = await dismissDrV2PhotoLink({ photo_id: current.id, link_id: link.link_id });
      if (res?.intel) setIntel(res.intel);
    } catch (e) { setErr(e?.message || "dismiss failed"); }
  }
  async function onResolveQ(q, resolution) {
    try {
      const res = await resolveDrV2PhotoQuestion({
        photo_id: current.id, question_id: q.question_id, resolution,
      });
      if (res?.intel) setIntel(res.intel);
    } catch (e) { setErr(e?.message || "resolve failed"); }
  }

  return (
    <SectionCard
      id="panel-photo-intel"
      title="Photo Evidence"
      badge={photos.length ? `${photos.length} photo${photos.length === 1 ? "" : "s"}` : "empty"}
    >
      <div className="space-y-3" data-testid="dr-v2-panel-photo-intel">
        {photos.length === 0 ? (
          <div className="text-xs opacity-70 rounded-md border border-dashed border-neutral-700 bg-neutral-950/40 px-3 py-4" data-testid="dr-v2-photo-empty">
            Photos you add to Section 8 will appear here as evidence. Suggestions and items to verify appear when the platform detects operational cues.
          </div>
        ) : (
          <>
            {/* Photo strip selector */}
            <div className="flex gap-1 overflow-x-auto pb-1" data-testid="dr-v2-photo-strip">
              {photos.map((p, i) => (
                <button
                  key={p.id}
                  className={`shrink-0 rounded-md border px-2 py-1 text-xs ${
                    i === selectedIdx ? "border-red-500 bg-neutral-800" : "border-neutral-700 hover:border-neutral-500"
                  }`}
                  onClick={() => setSelectedIdx(i)}
                  data-testid={`dr-v2-photo-select-${i}`}
                  title={p.label}
                >
                  #{i + 1}
                </button>
              ))}
            </div>

            {/* Selected photo intelligence */}
            <div className="rounded-md border border-neutral-800 bg-neutral-950/40 p-2 space-y-2 text-xs" data-testid="dr-v2-photo-intel-body">
              <div className="opacity-70 flex items-center justify-between">
                <span>Analyzing: <span className="font-mono">{current?.label}</span></span>
                {loading ? <span>· loading…</span> : intel ? <span>· ready</span> : <span>· not yet analyzed</span>}
              </div>
              {err ? <div className="text-red-300 text-[10px]">{err}</div> : null}

              {observations.length ? (
                <div data-testid="dr-v2-photo-observations">
                  <div className="font-semibold opacity-80 mb-1">Detected</div>
                  <ul className="grid grid-cols-1 gap-1">
                    {observations.slice(0, 6).map((o, i) => (
                      <li key={i} className="flex items-center justify-between gap-2 opacity-90">
                        <span className="truncate">· {o.label}{o.category ? ` (${o.category})` : ""}</span>
                        <span className="opacity-60">{Math.round(((o.confidence ?? 0) * 100))}%</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {suggested.length ? (
                <div data-testid="dr-v2-photo-suggestions">
                  <div className="font-semibold opacity-80 mb-1">Suggested links</div>
                  <ul className="space-y-1">
                    {suggested.slice(0, 6).map((s) => (
                      <li key={s.link_id} className="rounded-md border border-neutral-800 bg-neutral-900/40 p-1.5 flex items-center gap-2" data-testid={`dr-v2-photo-suggest-${s.link_id}`}>
                        <span className="truncate flex-1">
                          <span className="opacity-70">{s.target_type}:</span> {s.target_label || s.target_id}
                        </span>
                        {s.status === "suggested" ? (
                          <>
                            <button className="text-[10px] rounded bg-emerald-800 hover:bg-emerald-700 px-1.5 py-0.5" onClick={() => onAccept(s)} data-testid={`dr-v2-photo-accept-${s.link_id}`}>Accept</button>
                            <button className="text-[10px] rounded border border-neutral-700 hover:border-red-500 px-1.5 py-0.5" onClick={() => onDismiss(s)} data-testid={`dr-v2-photo-dismiss-${s.link_id}`}>Dismiss</button>
                          </>
                        ) : (
                          <span className={`text-[10px] uppercase tracking-wider ${s.status === "accepted" ? "text-emerald-300" : "text-neutral-500"}`}>{s.status}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {questions.length ? (
                <div data-testid="dr-v2-photo-questions">
                  <div className="font-semibold opacity-80 mb-1">Items to verify</div>
                  <ul className="space-y-1">
                    {questions.slice(0, 3).map((q) => (
                      <li key={q.question_id} className="rounded-md border border-amber-800/60 bg-amber-950/20 p-1.5" data-testid={`dr-v2-photo-question-${q.question_id}`}>
                        <div className="opacity-90">{q.prompt}</div>
                        {q.status === "open" ? (
                          <div className="mt-1 flex gap-1">
                            <button className="text-[10px] rounded border border-neutral-700 hover:border-emerald-500 px-1.5 py-0.5" onClick={() => onResolveQ(q, "confirmed")}>Confirm</button>
                            <button className="text-[10px] rounded border border-neutral-700 hover:border-red-500 px-1.5 py-0.5" onClick={() => onResolveQ(q, "not applicable")}>Not applicable</button>
                          </div>
                        ) : (
                          <div className="text-[10px] uppercase tracking-wider opacity-60 mt-1">{q.status}{q.resolution ? ` · ${q.resolution}` : ""}</div>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </>
        )}
      </div>
    </SectionCard>
  );
}
