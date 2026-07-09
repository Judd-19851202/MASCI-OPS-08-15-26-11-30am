/**
 * OA-1 · HistoryFeed.jsx
 * Append-only audit ledger view. Each entry shows actor + kind + when.
 * No interactivity — pure transparency.
 */
import React from "react";
import { History, User } from "lucide-react";
import { useT } from "@/lib/i18n";
// TRACK 27.03 · Phase 3 · Canonical local-time formatter.
import { formatPlatformTime } from "@/lib/platformTime";

const KIND_LABEL = {
  created: "Created",
  updated: "Updated",
  assigned: "Assigned",
  status_changed: "Status changed",
  note_added: "Note added",
  photo_added: "Photo added",
  photo_deleted: "Photo deleted",
};

function describe(entry) {
  const { kind, after } = entry;
  if (kind === "status_changed" && after?.status) {
    return `→ ${after.status}`;
  }
  if (kind === "assigned" && after?.owner?.name) {
    return `→ ${after.owner.name}`;
  }
  if (kind === "updated" && after && typeof after === "object") {
    const fields = Object.keys(after);
    return fields.length ? `· ${fields.join(", ")}` : "";
  }
  return "";
}

export default function HistoryFeed({ entries }) {
  const { t } = useT();
  const items = Array.isArray(entries) ? entries : [];
  if (!items.length) {
    return (
      <div className="text-xs text-slate-500 italic" data-testid="oa-history-empty">
        {t("No actions yet.")}
      </div>
    );
  }
  // Render newest first
  const sorted = [...items].sort((a, b) => (a.at > b.at ? -1 : 1));
  return (
    <ol
      data-testid="oa-history-list"
      className="bg-white border border-slate-200 rounded-md divide-y divide-slate-100 max-h-72 overflow-auto"
    >
      {sorted.map((e) => (
        <li key={e.id} className="px-3 py-2 flex items-start gap-2 text-xs" data-testid={`oa-history-${e.id}`}>
          <History className="w-3.5 h-3.5 text-slate-500 mt-0.5 shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-bold text-slate-900">{t(KIND_LABEL[e.kind] || e.kind)}</span>
              <span className="text-slate-600">{describe(e)}</span>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5 flex items-center gap-1.5">
              <User className="w-3 h-3" />
              {e.actor?.name || "—"}
              <span className="opacity-50">·</span>
              <span className="font-mono">{formatPlatformTime(e.at)}</span>
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
