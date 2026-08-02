/**
 * FieldMemoryGlance.jsx · iter432 · Phase 30 · Part 6 · Option iii.
 *
 * ONE calm, read-only operational-attention surface that lives on
 * role hubs (Field Leadership · Dispatch · PM · Shop · Safety). It
 * surfaces the most recent UNRESOLVED field memory notes for the
 * tenant so operators see institutional wisdom at a glance — never
 * as a dashboard, never as a feed, never as analytics.
 *
 * Doctrine
 * --------
 * - Read-only. NO add affordance here · creation lives inside the
 *   subject screens (project / equipment / assignment / recovery).
 * - 3 lines max by default · empty state is a single calm line.
 * - One network call · silent on 4xx/5xx (do not nag).
 * - No charts · no scoring · no ranking · no "AI suggestions".
 * - Self-gates: renders nothing if no portal token is present OR
 *   the endpoint returns 401 (e.g. on logout race).
 */
import React, { useEffect, useState } from "react";
import { ScrollText } from "lucide-react";
import { useT } from "@/lib/i18n";
import { buildPortalAuthHeaders, hasAnyPortalAuthToken } from "@/lib/authHeaders";

const API = process.env.REACT_APP_BACKEND_URL;

function _portalHeaders() {
  return buildPortalAuthHeaders();
}

function _relative(iso, t) {
  if (!iso) return "";
  try {
    const then = new Date(iso).getTime();
    const now = Date.now();
    const mins = Math.max(0, Math.round((now - then) / 60000));
    if (mins < 1) return t("just now");
    if (mins < 60) return `${mins} ${t("min ago")}`;
    const hrs = Math.round(mins / 60);
    if (hrs < 24) return `${hrs} ${t("hr ago")}`;
    const days = Math.round(hrs / 24);
    return `${days} ${t("d ago")}`;
  } catch {
    return iso;
  }
}

const KIND_LABEL = {
  project:         "Project",
  equipment:       "Equipment",
  assignment:      "Assignment",
  recovery_event:  "Recovery",
};

export function FieldMemoryGlance({ limit = 3 }) {
  const { t } = useT();
  const [items, setItems] = useState(null); // null = loading · [] = empty
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!hasAnyPortalAuthToken()) { setLoaded(true); return; }
      try {
        const res = await fetch(
          `${API}/api/field-memory/recent?limit=${encodeURIComponent(limit)}`,
          {
            headers: _portalHeaders(),
            cache: "no-store",
          },
        );
        if (!res.ok) { if (!cancelled) { setLoaded(true); setItems([]); } return; }
        const body = await res.json();
        if (cancelled) return;
        setItems(Array.isArray(body.items) ? body.items : []);
        setLoaded(true);
      } catch {
        if (!cancelled) { setLoaded(true); setItems([]); }
      }
    })();
    return () => { cancelled = true; };
  }, [limit]);

  // Hide entirely if no portal token at all (logged-out edge cases).
  if (!hasAnyPortalAuthToken()) return null;
  // Until the first fetch resolves, render nothing (calm · no skeleton).
  if (!loaded) return null;
  // iter504 · OMEGA Dispatch Production Readiness Sprint:
  // Suppress the entire card when there is no operational signal. Empty
  // "No recent operational notes." sections were consuming vertical space
  // on every role hub. The dispatcher gets no value from a card that has
  // nothing in it — collapse it completely.
  if (!items || items.length === 0) return null;

  return (
    <section
      data-testid="field-memory-glance"
      className="rounded-lg border border-slate-200 bg-white px-4 py-3"
    >
      <header className="flex items-center gap-2 text-slate-700">
        <ScrollText className="h-4 w-4" aria-hidden="true" />
        <h3 className="text-sm font-medium">{t("Recent field memory")}</h3>
      </header>

      <ul
        data-testid="field-memory-glance-list"
        className="mt-2 space-y-1.5"
      >
        {items.map((it) => {
          const kindLabel = t(KIND_LABEL[it.subject_kind] || "Note");
          const subject = (it.subject_label || it.subject_id || "").trim();
          const excerpt = (it.body || "").length > 90
            ? (it.body.slice(0, 90).trim() + "…")
            : (it.body || "").trim();
          return (
            <li
              key={it.id}
              data-testid={`field-memory-glance-item-${it.id}`}
              className="text-xs leading-snug text-slate-700"
            >
              <span className="text-slate-400 uppercase tracking-wide mr-1.5">
                {kindLabel}
              </span>
              {subject ? (
                <span className="font-medium mr-1.5">{subject}</span>
              ) : null}
              <span className="text-slate-600">— {excerpt}</span>
              <span className="ml-2 text-slate-400">
                {_relative(it.captured_at, t)}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export default FieldMemoryGlance;
