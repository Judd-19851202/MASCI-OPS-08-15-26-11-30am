// Track 19.54 · Operational Guidance System (OGS).
//
// OperationalThread — the one reusable read-only aggregation primitive.
//
// A Thread is a timeline view of related operational events tied to a
// single object (equipment unit · employee · project · incident).
// Zero new backend, zero new storage — the caller provides an array of
// events already fetched from existing endpoints, and this primitive
// renders them in a consistent operational-timeline shape.
//
// Every event on the thread MUST answer, from the caller's payload:
//   • kind   — inspection · repair · safety · incident · po · assignment · photo · history · other
//   • at     — ISO-8601 timestamp (used for chronological sort)
//   • title  — short one-line label
//   • summary (optional)
//   • deep_link (optional · React Router path)
//
// Consumers pass a resolved array. This primitive does not fetch. That
// keeps the thread purely read-only and prevents domain-collection
// duplication.

import React from "react";
import { Link } from "react-router-dom";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const KIND_TONE = {
  inspection: { label: "Inspection",  cls: "bg-sky-100 text-sky-900 border-sky-300" },
  repair:     { label: "Repair",      cls: "bg-orange-100 text-orange-900 border-orange-300" },
  safety:     { label: "Safety",      cls: "bg-red-100 text-red-900 border-red-300" },
  incident:   { label: "Incident",    cls: "bg-red-100 text-red-900 border-red-300" },
  po:         { label: "Purchase",    cls: "bg-emerald-100 text-emerald-900 border-emerald-300" },
  assignment: { label: "Assignment",  cls: "bg-indigo-100 text-indigo-900 border-indigo-300" },
  photo:      { label: "Photo",       cls: "bg-slate-100 text-slate-800 border-slate-300" },
  history:    { label: "History",     cls: "bg-slate-100 text-slate-800 border-slate-300" },
  other:      { label: "Event",       cls: "bg-slate-100 text-slate-800 border-slate-300" },
};

function fmt(dt) {
  if (!dt) return "—";
  try {
    return formatPlatformTime(dt);
  } catch {
    return String(dt);
  }
}

export default function OperationalThread({
  title = "Operational thread",
  subject,
  events = [],
  emptyLabel = "No related operational events on record yet.",
  testId = "operational-thread",
}) {
  const sorted = [...events].sort((a, b) =>
    (b.at || "").localeCompare(a.at || "")
  );

  return (
    <section
      data-testid={testId}
      className="rounded-md border-2 border-slate-200 bg-white"
    >
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-slate-200">
        <div className="min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-widest font-bold text-slate-500">
            {title}
          </div>
          {subject && (
            <div className="text-sm font-bold text-slate-900 truncate">{subject}</div>
          )}
        </div>
        <span
          data-testid={`${testId}-count`}
          className="text-[11px] font-mono font-bold text-slate-500"
        >
          {sorted.length} event{sorted.length === 1 ? "" : "s"}
        </span>
      </div>

      {sorted.length === 0 ? (
        <div
          data-testid={`${testId}-empty`}
          className="px-4 py-6 text-xs text-slate-500 italic text-center"
        >
          {emptyLabel}
        </div>
      ) : (
        <ol className="divide-y divide-slate-100">
          {sorted.map((e, i) => {
            const tone = KIND_TONE[e.kind] || KIND_TONE.other;
            const eventKey = [e.id || "event", e.kind || "other", e.at || "na", e.title || "untitled", i].join("::");
            return (
              <li
                key={eventKey}
                data-testid={`${testId}-event-${i}`}
                className="px-4 py-3"
              >
                <div className="flex items-baseline gap-2 mb-0.5">
                  <span
                    className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-mono font-bold uppercase tracking-wider ${tone.cls}`}
                  >
                    {tone.label}
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">{fmt(e.at)}</span>
                </div>
                <div className="text-sm font-semibold text-slate-900">
                  {e.deep_link ? (
                    <Link
                      to={e.deep_link}
                      className="hover:underline"
                      data-testid={`${testId}-event-${i}-link`}
                    >
                      {e.title}
                    </Link>
                  ) : (
                    e.title
                  )}
                </div>
                {e.summary && (
                  <p className="text-xs text-slate-600 mt-0.5 leading-snug">{e.summary}</p>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
