// src/components/team/AssignmentHistoryDrawer.jsx
// TRACK 15.39A · Read-only Assignment History drawer (admin only).
//
// Replaces the legacy inline audit list with a right-side Sheet so the
// roster grid keeps its full width on iPad portrait and desktop. The
// audit feed is already newest-first from the backend; we defensively
// re-sort on `at` in case the response order ever drifts.
//
// Action types and their visual treatment line up with the Track 15.39
// backend taxonomy: assign · role_change · update · remove.

import React, { useMemo } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";

const ACTION_META = {
  assign: {
    label: "ASSIGNED",
    classes: "bg-emerald-100 text-emerald-800 border-emerald-200",
  },
  role_change: {
    label: "ROLE CHANGED",
    classes: "bg-amber-100 text-amber-800 border-amber-200",
  },
  update: {
    label: "UPDATED",
    classes: "bg-blue-100 text-blue-800 border-blue-200",
  },
  remove: {
    label: "REMOVED",
    classes: "bg-red-100 text-red-800 border-red-200",
  },
};

function safeDate(at) {
  if (!at) return "";
  try {
    return new Date(at).toLocaleString();
  } catch {
    return String(at);
  }
}

export function AssignmentHistoryDrawer({ open, onOpenChange, items }) {
  const sorted = useMemo(() => {
    const list = Array.isArray(items) ? items.slice() : [];
    return list.sort((a, b) => (b?.at || "").localeCompare(a?.at || ""));
  }, [items]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-xl overflow-y-auto"
        data-testid="assignment-history-drawer"
      >
        <SheetHeader>
          <SheetTitle>Assignment History</SheetTitle>
          <SheetDescription>
            Read-only audit · newest first · {sorted.length}{" "}
            {sorted.length === 1 ? "entry" : "entries"}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-4 space-y-2" data-testid="history-list">
          {sorted.length === 0 && (
            <p
              className="text-sm text-slate-500"
              data-testid="history-empty"
            >
              No history yet.
            </p>
          )}
          {sorted.map((ev) => {
            const meta = ACTION_META[ev.action] || ACTION_META.update;
            const oldRole =
              ev.before?.role_label ||
              ev.before?.assignment_role ||
              null;
            const newRole =
              ev.after?.role_label || ev.after?.assignment_role || null;
            const displayRole =
              ev.assignment_role_label ||
              ev.after?.role_label ||
              ev.before?.role_label ||
              ev.assignment_role ||
              null;
            const who =
              ev.target_display_name ||
              ev.before?.display_name ||
              ev.after?.display_name ||
              ev.target_email ||
              ev.before?.email ||
              ev.after?.email ||
              ev.target_user_id ||
              "(unknown)";
            return (
              <div
                key={ev.id}
                className="border rounded p-3 bg-white"
                data-testid={`history-row-${ev.action}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <Badge
                    variant="outline"
                    className={`${meta.classes} text-[10px] font-mono`}
                  >
                    {meta.label}
                  </Badge>
                  <span className="text-xs text-slate-500">
                    {safeDate(ev.at)}
                  </span>
                </div>
                <p className="mt-2 text-sm font-medium break-words">{who}</p>
                {ev.action === "role_change" ? (
                  <p className="text-xs text-slate-600">
                    {oldRole || "—"} →{" "}
                    <strong>{newRole || "—"}</strong>
                  </p>
                ) : (
                  displayRole && (
                    <p className="text-xs text-slate-600">{displayRole}</p>
                  )
                )}
                {ev.notes && (
                  <p className="text-xs text-slate-700 mt-1 italic break-words">
                    {ev.notes}
                  </p>
                )}
                <p className="text-xs text-slate-500 mt-1">
                  by {ev.actor_email || ev.actor_name || ev.actor_role || ev.actor_id || "—"}
                </p>
              </div>
            );
          })}
        </div>
      </SheetContent>
    </Sheet>
  );
}

export default AssignmentHistoryDrawer;
