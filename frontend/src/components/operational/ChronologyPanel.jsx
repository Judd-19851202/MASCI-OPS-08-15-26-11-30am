// ChronologyPanel.jsx — Phase V-Prelude · Wave 1 · Substrate.
//
// Text-only, calm chronology rendering. NEVER a chart, NEVER a gantt,
// NEVER a swimlane. Slate text. See
// /app/memory/OPERATIONAL_TIMELINE_FOUNDATION.md for the doctrine.
//
// Props:
//   items       — array of { kind, id, at, title, subtitle, relationship,
//                            linked_to: [{kind, id}] }
//   emptyText   — copy shown when no rows exist
//   labelDate   — true → use formatLocalDate (no time); else short

import React from "react";
import { formatLocalShort, formatLocalDate } from "@/lib/dateUtils";

const _KIND_LABEL = {
  operational_constraint: "constraint",
  daily_report: "report",
  incident: "incident",
  inspection: "inspection",
  meeting: "meeting",
  photo: "photo",
  attachment: "attachment",
  field_note: "field note",
  qa_qc_record: "QA/QC",
  safety_record: "safety",
  trench_record: "trench",
  jha_record: "JHA",
  dispatch_event: "dispatch",
  equipment_record: "equipment",
  future_rfi: "RFI",
  future_schedule_activity: "schedule",
  future_external_response: "response",
};

function _kindLabel(k) {
  return _KIND_LABEL[k] || (k || "item").replace(/_/g, " ");
}

export default function ChronologyPanel({ items, emptyText, labelDate }) {
  const rows = Array.isArray(items) ? items : [];
  if (!rows.length) {
    return (
      <div
        data-testid="chronology-panel-empty"
        className="text-sm text-slate-500 italic py-4"
      >
        {emptyText || "No chronology yet."}
      </div>
    );
  }
  const fmt = labelDate ? formatLocalDate : formatLocalShort;

  return (
    <ol
      data-testid="chronology-panel"
      className="space-y-2 text-sm text-slate-700"
    >
      {rows.map((r, idx) => {
        const lbl = _kindLabel(r.kind);
        const link = r.linked_to && r.linked_to[0];
        return (
          <li
            key={`${r.kind}-${r.id}-${idx}`}
            data-testid="chronology-row"
            className="flex gap-3 leading-snug"
          >
            <span
              className="shrink-0 text-slate-500 tabular-nums"
              data-testid="chronology-row-time"
            >
              {fmt(r.at)}
            </span>
            <span className="text-slate-400">·</span>
            <span className="text-slate-500 shrink-0">{lbl}:</span>
            <span className="text-slate-800 break-words">
              {r.title || r.subtitle || r.relationship || ""}
              {r.subtitle && r.title && r.subtitle !== r.title && (
                <span className="text-slate-500 ml-1">
                  · {r.subtitle}
                </span>
              )}
              {link && (
                <span className="text-slate-500 ml-1">
                  → {_kindLabel(link.kind)}
                </span>
              )}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
