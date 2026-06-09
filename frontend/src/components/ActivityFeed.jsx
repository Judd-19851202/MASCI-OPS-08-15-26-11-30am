import React, { useEffect, useState } from "react";
import {
  Activity,
  MessageSquare,
  ListChecks,
  Calendar,
  FileText,
  TrendingUp,
  Loader2,
} from "lucide-react";
import { api } from "@/lib/api";
import { UserAvatar, relativeTime, apiErr } from "@/lib/crewHubUi";
import { toast } from "sonner";

const KIND_META = {
  message: { Icon: MessageSquare, color: "text-red-700", bg: "bg-red-50" },
  comment: { Icon: MessageSquare, color: "text-red-700", bg: "bg-red-50" },
  todo: { Icon: ListChecks, color: "text-amber-700", bg: "bg-amber-50" },
  event: { Icon: Calendar, color: "text-emerald-700", bg: "bg-emerald-50" },
  doc: { Icon: FileText, color: "text-blue-700", bg: "bg-blue-50" },
  hill: { Icon: TrendingUp, color: "text-slate-700", bg: "bg-slate-100" },
};

/**
 * ActivityFeed — list of recent activity items for a project.
 * Pass `projectId` for per-project, or `scope="me"` for the viewer's feed
 * across every project they're in.
 */
export function ActivityFeed({ projectId, scope, limit = 15, compact = false }) {
  const [items, setItems] = useState(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const url = scope === "me"
          ? `/me/activity?limit=${limit}`
          : `/projects/${projectId}/activity?limit=${limit}`;
        const r = await api.get(url);
        if (alive) setItems(r.data || []);
      } catch (e) {
        if (alive) {
          setItems([]);
          toast.error(apiErr(e?.response?.data?.detail, "Failed to load activity"));
        }
      }
    })();
    return () => { alive = false; };
  }, [projectId, scope, limit]);

  if (items === null) {
    return (
      <div className="flex justify-center py-6" data-testid="activity-loading">
        <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-sm text-slate-400 italic py-4" data-testid="activity-empty">
        No activity yet. New messages, completed to-dos, events and uploads will appear here.
      </div>
    );
  }

  return (
    <ul className="divide-y divide-slate-100" data-testid="activity-feed">
      {items.map((it) => {
        const meta = KIND_META[it.kind] || KIND_META.message;
        const Icon = meta.Icon;
        return (
          <li key={it.id} className={`flex items-start gap-3 py-3 ${compact ? "" : "sm:py-3.5"}`} data-testid={`activity-item-${it.id}`}>
            <UserAvatar name={it.actor_name} userId={it.actor_id} size="sm" />
            <div className="flex-1 min-w-0">
              <div className="text-sm text-slate-800 leading-snug">
                <span className="font-bold text-slate-900">{it.actor_name}</span>{" "}
                <span className="text-slate-600">{it.verb}</span>{" "}
                <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-[0.1em] font-bold ${meta.bg} ${meta.color}`}>
                  <Icon className="w-3 h-3" /> {it.kind}
                </span>{" "}
                <span className="font-semibold text-slate-900">{it.target_label}</span>
                {scope === "me" && it.project_name && (
                  <>
                    <span className="text-slate-500"> · in </span>
                    <span className="text-slate-700 font-semibold">{it.project_name}</span>
                  </>
                )}
              </div>
              {it.preview && (
                <div className="text-xs text-slate-500 mt-0.5 line-clamp-1">{it.preview}</div>
              )}
              {it.image_url && (
                <img src={it.image_url} alt="" loading="lazy" decoding="async" className="mt-2 max-h-28 rounded border border-slate-200" />
              )}
              <div className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-400 mt-1">
                {relativeTime(it.created_at)}
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
