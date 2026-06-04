// PortalUsersAccordion.jsx — iter505 · OMEGA Admin IAM Screen Completion Sprint
//
// Read-only UI accordion wrapper. Renders the portal-specific user-management
// panel inside a collapsible section with a count badge. Collapsed by default.
//
// Zero behaviour change: child panels render identically inside; this wrapper
// only adds a click-to-toggle header + count display. No DB writes, no auth
// changes, no portal-data mutations.
import React, { useEffect, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";

const STATS_PATH = "/admin/directory/k4/stats";

let _statsCache = null;
let _statsPromise = null;

/**
 * Fetches K4 portal counts once and shares the result between every
 * accordion section on the same page render. Read-only call.
 */
async function loadPortalCounts() {
  if (_statsCache) return _statsCache;
  if (_statsPromise) return _statsPromise;
  _statsPromise = (async () => {
    try {
      const { data } = await api.get(STATS_PATH);
      _statsCache = (data && data.by_portal) || {};
      return _statsCache;
    } catch {
      _statsCache = {};
      return _statsCache;
    } finally {
      _statsPromise = null;
    }
  })();
  return _statsPromise;
}

/**
 * <PortalUsersAccordion> — collapsible wrapper around a portal-specific user panel.
 *
 * Props:
 *   portalKey   — e.g. "hr", "pm", "shop", "safety", "dispatch", "field_leadership"
 *   title       — section title (e.g. "HR Users & Logins")
 *   defaultOpen — boolean (default false)
 *   children    — the existing portal panel component
 *
 * Behaviour:
 *   - Collapsed by default → 48 px header
 *   - Click header to expand → renders children below
 *   - Loads K4 portal count once (shared cache) for the count badge
 *   - data-testid="portal-accordion-<portalKey>"
 */
export default function PortalUsersAccordion({
  portalKey,
  title,
  defaultOpen = false,
  children,
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [count, setCount] = useState(null);

  useEffect(() => {
    let alive = true;
    loadPortalCounts().then((by_portal) => {
      if (!alive) return;
      const c = by_portal?.[portalKey];
      setCount(typeof c === "number" ? c : null);
    });
    return () => { alive = false; };
  }, [portalKey]);

  return (
    <section
      className="bg-white border border-slate-200 rounded-md overflow-hidden"
      data-testid={`portal-accordion-${portalKey}`}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        data-testid={`portal-accordion-toggle-${portalKey}`}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors"
      >
        {open ? (
          <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-500 shrink-0" />
        )}
        <span className="font-display text-sm sm:text-base font-black tracking-tight text-slate-900 flex-1">
          {title}
        </span>
        <span
          className="inline-flex items-center justify-center min-w-[2rem] h-6 px-2 rounded-full bg-slate-900 text-white font-mono text-[11px] font-bold tabular-nums"
          data-testid={`portal-accordion-count-${portalKey}`}
        >
          {count == null ? "·" : count}
        </span>
      </button>
      {open && (
        <div className="border-t border-slate-200 p-3 sm:p-4" data-testid={`portal-accordion-body-${portalKey}`}>
          {children}
        </div>
      )}
    </section>
  );
}
