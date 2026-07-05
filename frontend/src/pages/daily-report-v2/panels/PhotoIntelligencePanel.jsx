import React from "react";
import { Section } from "@/components/Section";
import {
  StatusChip, secondaryBtn,
} from "../_ui";
import {
  fetchDrV2PhotoIntel,
  acceptDrV2PhotoLink,
  dismissDrV2PhotoLink,
  resolveDrV2PhotoQuestion,
} from "@/lib/drV2Api";

/**
 * DR-ROI-001D · Photo Evidence panel · DR-ROI-001F platform styling pass.
 *
 * Invisible Intelligence: shows suggested links, items to verify, and
 * detected observations. Never surfaces model or provider names or cost
 * meters. Photos remain source-of-truth — every suggestion needs a
 * supervisor click to become a link.
 */
export default function PhotoIntelligencePanel({ draft }) {
  const photos = React.useMemo(
    () =>
      (draft?.photos || []).map((p, i) => {
        if (typeof p === "string") {
          return { id: p, ref: p, label: `Photo ${i + 1}` };
        }
        return {
          id: p.id || p.ref || `photo-${i}`,
          ref: p.ref || p.url || p.id,
          label: p.label || `Photo ${i + 1}`,
        };
      }),
    [draft?.photos],
  );

  const [selectedIdx, setSelectedIdx] = React.useState(0);
  const [intel, setIntel] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState(null);

  const current = photos[selectedIdx];

  React.useEffect(() => {
    let alive = true;
    async function load() {
      if (!current) {
        setIntel(null);
        return;
      }
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
    return () => {
      alive = false;
    };
  }, [current, draft?.report_id]);

  const suggested = intel?.suggested_links || [];
  const questions = intel?.questions || [];
  const observations = intel?.observations || [];

  async function onAccept(link) {
    try {
      const res = await acceptDrV2PhotoLink({
        photo_id: current.id,
        link_id: link.link_id,
      });
      if (res?.intel) setIntel(res.intel);
    } catch (e) {
      setErr(e?.message || "accept failed");
    }
  }
  async function onDismiss(link) {
    try {
      const res = await dismissDrV2PhotoLink({
        photo_id: current.id,
        link_id: link.link_id,
      });
      if (res?.intel) setIntel(res.intel);
    } catch (e) {
      setErr(e?.message || "dismiss failed");
    }
  }
  async function onResolveQ(q, resolution) {
    try {
      const res = await resolveDrV2PhotoQuestion({
        photo_id: current.id,
        question_id: q.question_id,
        resolution,
      });
      if (res?.intel) setIntel(res.intel);
    } catch (e) {
      setErr(e?.message || "resolve failed");
    }
  }

  return (
    <Section
      number="08b"
      title="Photo Evidence"
      testId="dr-v2-section-photo-evidence"
      dense
      aside={
        <StatusChip tone={photos.length ? "slate" : "amber"}>
          {photos.length
            ? `${photos.length} photo${photos.length === 1 ? "" : "s"}`
            : "empty"}
        </StatusChip>
      }
    >
      <div className="space-y-3" data-testid="dr-v2-panel-photo-intel">
        {photos.length === 0 ? (
          <div
            className="text-sm text-slate-600 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6"
            data-testid="dr-v2-photo-empty"
          >
            No photos yet. Add at least six field photos in Section 8 to
            unlock evidence linking.
          </div>
        ) : (
          <>
            <div
              className="flex gap-1 overflow-x-auto pb-1"
              data-testid="dr-v2-photo-strip"
            >
              {photos.map((p, i) => (
                <button
                  key={p.id}
                  type="button"
                  className={`shrink-0 rounded-md border-2 px-2 h-9 text-xs font-semibold ${
                    i === selectedIdx
                      ? "border-red-600 bg-red-50 text-red-800"
                      : "border-slate-300 bg-white text-slate-700 hover:border-slate-500"
                  }`}
                  onClick={() => setSelectedIdx(i)}
                  data-testid={`dr-v2-photo-select-${i}`}
                  title={p.label}
                >
                  #{i + 1}
                </button>
              ))}
            </div>

            <div
              className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-3 text-sm"
              data-testid="dr-v2-photo-intel-body"
            >
              <div className="text-xs text-slate-600 flex items-center justify-between">
                <span>
                  Analyzing:{" "}
                  <span className="font-mono text-slate-800">
                    {current?.label}
                  </span>
                </span>
                {loading ? (
                  <span>· loading…</span>
                ) : intel ? (
                  <StatusChip tone="green">ready</StatusChip>
                ) : (
                  <StatusChip tone="slate">not yet analyzed</StatusChip>
                )}
              </div>
              {err ? (
                <div className="text-red-700 text-xs">{err}</div>
              ) : null}

              {observations.length ? (
                <div data-testid="dr-v2-photo-observations">
                  <div className="font-semibold text-slate-800 mb-1">
                    Detected
                  </div>
                  <ul className="space-y-1">
                    {observations.slice(0, 6).map((o, i) => (
                      <li
                        key={i}
                        className="flex items-center justify-between gap-2 text-slate-700"
                      >
                        <span className="truncate">
                          · {o.label}
                          {o.category ? ` (${o.category})` : ""}
                        </span>
                        <span className="text-xs text-slate-500">
                          {Math.round((o.confidence ?? 0) * 100)}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {suggested.length ? (
                <div data-testid="dr-v2-photo-suggestions">
                  <div className="font-semibold text-slate-800 mb-1">
                    Suggested links
                  </div>
                  <ul className="space-y-1">
                    {suggested.slice(0, 6).map((s) => (
                      <li
                        key={s.link_id}
                        className="rounded-md border border-slate-200 bg-white p-2 flex items-center gap-2"
                        data-testid={`dr-v2-photo-suggest-${s.link_id}`}
                      >
                        <span className="truncate flex-1 text-sm text-slate-800">
                          <span className="text-slate-500 text-xs mr-1">
                            {s.target_type}:
                          </span>
                          {s.target_label || s.target_id}
                        </span>
                        {s.status === "suggested" ? (
                          <>
                            <button
                              type="button"
                              className="text-xs rounded bg-emerald-700 hover:bg-emerald-600 text-white px-2 h-8 font-semibold"
                              onClick={() => onAccept(s)}
                              data-testid={`dr-v2-photo-accept-${s.link_id}`}
                            >
                              Accept
                            </button>
                            <button
                              type="button"
                              className={secondaryBtn + " h-8 px-2 text-xs"}
                              onClick={() => onDismiss(s)}
                              data-testid={`dr-v2-photo-dismiss-${s.link_id}`}
                            >
                              Dismiss
                            </button>
                          </>
                        ) : (
                          <StatusChip
                            tone={s.status === "accepted" ? "green" : "slate"}
                          >
                            {s.status}
                          </StatusChip>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {questions.length ? (
                <div data-testid="dr-v2-photo-questions">
                  <div className="font-semibold text-slate-800 mb-1">
                    Items to verify
                  </div>
                  <ul className="space-y-1">
                    {questions.slice(0, 3).map((q) => (
                      <li
                        key={q.question_id}
                        className="rounded-md border border-amber-300 bg-amber-50 p-2"
                        data-testid={`dr-v2-photo-question-${q.question_id}`}
                      >
                        <div className="text-slate-800 text-sm">
                          {q.prompt}
                        </div>
                        {q.status === "open" ? (
                          <div className="mt-1 flex gap-1">
                            <button
                              type="button"
                              className="text-xs rounded border-2 border-slate-300 bg-white hover:border-emerald-500 hover:text-emerald-700 px-2 h-8 font-semibold"
                              onClick={() => onResolveQ(q, "confirmed")}
                            >
                              Confirm
                            </button>
                            <button
                              type="button"
                              className="text-xs rounded border-2 border-slate-300 bg-white hover:border-red-500 hover:text-red-700 px-2 h-8 font-semibold"
                              onClick={() => onResolveQ(q, "not applicable")}
                            >
                              Not applicable
                            </button>
                          </div>
                        ) : (
                          <div className="text-[11px] uppercase tracking-wider text-slate-500 mt-1">
                            {q.status}
                            {q.resolution ? ` · ${q.resolution}` : ""}
                          </div>
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
    </Section>
  );
}
