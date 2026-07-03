// Track 19.55 · Universal Operational Threads Foundation.
//
// OperationalThreadPage — the ONE reusable 10-section page shell.
// Every future Operational Thread (Employee, Project, Incident,
// Vendor, Asset) will render itself as an <OperationalThreadPage>
// with domain-specific data slots. If a domain builds a bespoke
// page layout for a thread, the platform has drifted.
//
// Section order (immutable per Track 19.55 doctrine):
//   1  Mission Overview
//   2  Attention
//   3  Operational Guidance (opens the Track 19.54 Guidance Card)
//   4  Timeline (uses the Track 19.54 OperationalThread rendering primitive)
//   5  Relationships (uses the Track 19.55 RelationshipGraph primitive)
//   6  Documents
//   7  Photos
//   8  Operational Intelligence
//   9  History
//  10  Audit
//
// Zero-drift guarantees:
//   • Never re-derives scoring.
//   • Never fetches — the caller supplies data.
//   • Never mutates state.
//   • Never renders a duplicate timeline / relationship framework
//     (uses the shared primitives).

import React, { useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, Users, Layers, FileText, Image as ImageIcon, Activity, Clock, ShieldCheck, ExternalLink } from "lucide-react";
import AttentionChip from "./AttentionChip";
import TrendChip from "./TrendChip";
import GuidanceCard from "./GuidanceCard";
import OperationalThread from "./OperationalThread";
import RelationshipGraph from "./RelationshipGraph";

const HEALTH_TONE = {
  Excellent:        { chip: "bg-emerald-100 text-emerald-900 border-emerald-300" },
  Good:             { chip: "bg-emerald-100 text-emerald-900 border-emerald-300" },
  "Attention Needed": { chip: "bg-amber-100 text-amber-900 border-amber-300" },
  Critical:         { chip: "bg-red-100 text-red-900 border-red-300" },
};

function SectionHeader({ index, title, icon: Icon }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      {Icon && <Icon className="w-4 h-4 text-slate-600" />}
      <span className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500">
        {String(index).padStart(2, "0")} · {title}
      </span>
    </div>
  );
}

export default function OperationalThreadPage({
  // Section 1 — Mission Overview
  mission,
  // Section 2 — Attention
  attention = { items: [] },
  // Section 3 — Guidance product (OI product row from /summary)
  guidanceProduct = null,
  // Section 4 — Timeline events (schema per OperationalThread contract)
  timelineEvents = [],
  timelineTitle = "Timeline",
  // Section 5 — Relationships
  relationships = { subject: null, edges: [] },
  // Section 6 — Documents (array of { id, name, deep_link? })
  documents = [],
  // Section 7 — Photos (array of { id, url, caption?, taken_at? })
  photos = [],
  // Section 8 — OI product row (score, attention level, trend, top_attention_label)
  oiProduct = null,
  // Section 9 — History rows (array of { id, generated_at, score, attention_level })
  history = [],
  // Section 10 — Audit rows (array of { id, at, actor, action, detail? })
  audit = [],
  // Universal action queue (max 5)
  actionQueue = [],
  // Root testid
  testId = "operational-thread-page",
}) {
  const [openGuidanceProduct, setOpenGuidanceProduct] = useState(null);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-5" data-testid={testId}>
      {/* Section 1 — Mission Overview */}
      <section
        data-testid={`${testId}-section-1-mission`}
        className="rounded-md border-2 border-slate-200 bg-white"
      >
        <div className="px-4 py-3 border-b border-slate-200">
          <SectionHeader index={1} title="Mission overview" icon={Activity} />
          <div className="flex flex-wrap items-baseline gap-3">
            <h1 className="font-display text-2xl font-black text-slate-900" data-testid={`${testId}-title`}>
              {mission?.label || "—"}
            </h1>
            {mission?.kind && (
              <span className="font-mono text-[11px] uppercase tracking-widest text-slate-500">
                {mission.kind}
              </span>
            )}
            {mission?.health && (
              <span
                data-testid={`${testId}-health`}
                className={`inline-flex items-center rounded border px-2 py-0.5 text-[11px] font-mono font-bold uppercase tracking-wider ${(HEALTH_TONE[mission.health] || HEALTH_TONE.Good).chip}`}
              >
                {mission.health}
              </span>
            )}
          </div>
        </div>
        <dl className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {(mission?.facts || []).map((f, i) => (
            <div key={i} data-testid={`${testId}-fact-${i}`}>
              <dt className="font-mono text-[10px] uppercase tracking-widest text-slate-500">{f.label}</dt>
              <dd className="text-sm font-semibold text-slate-900 leading-snug">{f.value || "—"}</dd>
            </div>
          ))}
        </dl>
        {mission?.explanation && (
          <div
            data-testid={`${testId}-health-explanation`}
            className="px-4 pb-4 text-xs text-slate-600 leading-relaxed"
          >
            {mission.explanation}
          </div>
        )}
      </section>

      {/* Universal Action Queue (max 5) */}
      {actionQueue.length > 0 && (
        <section
          data-testid={`${testId}-action-queue`}
          className="rounded-md border-2 border-amber-300 bg-amber-50 px-4 py-3"
        >
          <SectionHeader index={2} title="Today's actions · max 5" icon={AlertTriangle} />
          <ol className="space-y-1 text-sm text-slate-900">
            {actionQueue.slice(0, 5).map((a, i) => (
              <li
                key={i}
                data-testid={`${testId}-action-${i}`}
                className="flex items-start gap-2"
              >
                <span className="font-mono text-xs font-bold text-slate-500 shrink-0 mt-0.5">
                  {i + 1}.
                </span>
                {a.deep_link ? (
                  <Link to={a.deep_link} className="hover:underline">{a.label}</Link>
                ) : (
                  <span>{a.label}</span>
                )}
              </li>
            ))}
          </ol>
        </section>
      )}

      {/* Section 2 — Attention */}
      <section
        data-testid={`${testId}-section-2-attention`}
        className="rounded-md border-2 border-slate-200 bg-white px-4 py-3"
      >
        <SectionHeader index={2} title="Attention · needs action" icon={AlertTriangle} />
        {attention.items.length === 0 ? (
          <div
            data-testid={`${testId}-attention-empty`}
            className="text-xs text-slate-500 italic"
          >
            No operational items currently require attention.
          </div>
        ) : (
          <ul className="space-y-2">
            {attention.items.map((a, i) => (
              <li
                key={i}
                data-testid={`${testId}-attention-${i}`}
                className="flex items-start gap-2 text-sm"
              >
                <AttentionChip level={a.severity} testId={`${testId}-attention-${i}-severity`} />
                <div className="min-w-0 flex-1">
                  <div className="font-semibold text-slate-900">{a.label}</div>
                  {a.why && <div className="text-xs text-slate-600 leading-snug">{a.why}</div>}
                  {(a.owner || a.due) && (
                    <div className="text-[11px] font-mono text-slate-500">
                      {a.owner ? `Owner: ${a.owner}` : ""}
                      {a.owner && a.due ? " · " : ""}
                      {a.due ? `Due: ${a.due}` : ""}
                    </div>
                  )}
                </div>
                {a.deep_link && (
                  <Link
                    to={a.deep_link}
                    data-testid={`${testId}-attention-${i}-action`}
                    className="text-xs font-mono font-bold text-slate-900 border-b border-slate-300 hover:border-slate-900 whitespace-nowrap"
                  >
                    Take action
                  </Link>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Section 3 — Operational Guidance */}
      <section
        data-testid={`${testId}-section-3-guidance`}
        className="rounded-md border-2 border-slate-200 bg-white px-4 py-3"
      >
        <SectionHeader index={3} title="Operational guidance" icon={ShieldCheck} />
        {guidanceProduct ? (
          <button
            type="button"
            data-testid={`${testId}-open-guidance`}
            onClick={() => setOpenGuidanceProduct(guidanceProduct)}
            className="inline-flex items-center gap-2 text-xs font-mono font-bold text-slate-900 border-2 border-slate-300 hover:border-slate-900 rounded px-3 py-1.5 uppercase tracking-widest"
          >
            Open Guidance Card <ExternalLink className="w-3 h-3" />
          </button>
        ) : (
          <div className="text-xs text-slate-500 italic">
            No Operational Intelligence product mapped for this subject.
          </div>
        )}
      </section>

      {/* Section 4 — Timeline */}
      <div data-testid={`${testId}-section-4-timeline`}>
        <SectionHeader index={4} title={timelineTitle} icon={Clock} />
        <OperationalThread
          events={timelineEvents}
          testId={`${testId}-timeline`}
          emptyLabel="No timeline events on record yet."
          title={timelineTitle}
        />
      </div>

      {/* Section 5 — Relationships */}
      <div data-testid={`${testId}-section-5-relationships`}>
        <SectionHeader index={5} title="Relationships" icon={Users} />
        <RelationshipGraph
          subject={relationships.subject}
          edges={relationships.edges}
          testId={`${testId}-relationships`}
        />
      </div>

      {/* Section 6 — Documents */}
      <section
        data-testid={`${testId}-section-6-documents`}
        className="rounded-md border-2 border-slate-200 bg-white px-4 py-3"
      >
        <SectionHeader index={6} title="Documents" icon={FileText} />
        {documents.length === 0 ? (
          <div
            data-testid={`${testId}-documents-empty`}
            className="text-xs text-slate-500 italic"
          >
            No documents on record.
          </div>
        ) : (
          <ul className="text-sm text-slate-900 space-y-1">
            {documents.map((d, i) => (
              <li key={d.id || i} data-testid={`${testId}-document-${i}`} className="flex items-start gap-2">
                <FileText className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
                {d.deep_link ? (
                  <Link to={d.deep_link} className="hover:underline">{d.name}</Link>
                ) : (
                  <span>{d.name}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Section 7 — Photos */}
      <section
        data-testid={`${testId}-section-7-photos`}
        className="rounded-md border-2 border-slate-200 bg-white px-4 py-3"
      >
        <SectionHeader index={7} title="Photos" icon={ImageIcon} />
        {photos.length === 0 ? (
          <div
            data-testid={`${testId}-photos-empty`}
            className="text-xs text-slate-500 italic"
          >
            No photos on record.
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {photos.slice(0, 8).map((p, i) => (
              <div key={p.id || i} data-testid={`${testId}-photo-${i}`} className="aspect-square bg-slate-100 rounded overflow-hidden">
                {p.url && <img src={p.url} alt={p.caption || ""} className="w-full h-full object-cover" />}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Section 8 — Operational Intelligence */}
      <section
        data-testid={`${testId}-section-8-oi`}
        className="rounded-md border-2 border-slate-200 bg-white px-4 py-3"
      >
        <SectionHeader index={8} title="Operational Intelligence" icon={Layers} />
        {oiProduct ? (
          <div className="flex flex-wrap items-baseline gap-3">
            <AttentionChip level={oiProduct.attention_level} showHint />
            <TrendChip
              direction={oiProduct.trend_direction}
              percent={oiProduct.trend_percent}
              score={oiProduct.score}
            />
            {oiProduct.top_attention_label && (
              <div className="text-sm text-slate-800 basis-full">
                <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500 mr-2">Top driver:</span>
                {oiProduct.top_attention_label}
              </div>
            )}
          </div>
        ) : (
          <div className="text-xs text-slate-500 italic">
            No Operational Intelligence signal is mapped for this subject.
          </div>
        )}
      </section>

      {/* Section 9 — History */}
      <section
        data-testid={`${testId}-section-9-history`}
        className="rounded-md border-2 border-slate-200 bg-white px-4 py-3"
      >
        <SectionHeader index={9} title="History" icon={Clock} />
        {history.length === 0 ? (
          <div
            data-testid={`${testId}-history-empty`}
            className="text-xs text-slate-500 italic"
          >
            No historical snapshots on record.
          </div>
        ) : (
          <ul className="text-sm space-y-1">
            {history.map((h, i) => (
              <li key={h.id || i} data-testid={`${testId}-history-${i}`} className="flex items-baseline gap-2">
                <span className="font-mono text-[10px] text-slate-500 shrink-0">{h.generated_at || ""}</span>
                <span className="font-semibold text-slate-900">{h.label || h.subject || "Snapshot"}</span>
                {typeof h.score === "number" && (
                  <span className="font-mono text-xs text-slate-600">· score {h.score}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Section 10 — Audit */}
      <section
        data-testid={`${testId}-section-10-audit`}
        className="rounded-md border-2 border-slate-200 bg-white px-4 py-3"
      >
        <SectionHeader index={10} title="Audit · read-only" icon={ShieldCheck} />
        {audit.length === 0 ? (
          <div
            data-testid={`${testId}-audit-empty`}
            className="text-xs text-slate-500 italic"
          >
            No audit entries on record.
          </div>
        ) : (
          <ul className="text-xs space-y-1">
            {audit.map((a, i) => (
              <li key={a.id || i} data-testid={`${testId}-audit-${i}`} className="flex items-baseline gap-2">
                <span className="font-mono text-[10px] text-slate-500 shrink-0">{a.at || ""}</span>
                <span className="font-semibold text-slate-900">{a.actor || "—"}</span>
                <span className="text-slate-700">— {a.action || a.detail || "change"}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {openGuidanceProduct && (
        <GuidanceCard
          product={openGuidanceProduct}
          onClose={() => setOpenGuidanceProduct(null)}
        />
      )}
    </div>
  );
}
