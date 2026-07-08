// TRACK 25.02 · Admin Operating System — Phase D · Command Palette.
//
// Universal ⌘K search across:
//   · Every visible + hidden admin route (from domainMapV3)
//   · Every registered OCC operation (fetched from
//     /api/admin/operations-control/overview)
//   · A soft-fetched entity slice (projects · employees · equipment)
//     via best-effort admin search endpoints. If those endpoints are
//     unavailable, the palette degrades gracefully (route search
//     still works) — no hard dependency.
//
// Opens on:
//   · Cmd/Ctrl + K
//   · Cmd/Ctrl + /
//   · Sidebar `Search everything` button
//
// Feature-flag guarded so users on legacy V2 never see it.

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, X } from "lucide-react";
import {
  DOMAINS_V3,
  buildSearchIndex,
} from "@/app/admin/domainMapV3";

const API = process.env.REACT_APP_BACKEND_URL;

function adminToken() {
  try {
    return (
      localStorage.getItem("masci.admin.token") ||
      localStorage.getItem("adminToken") ||
      localStorage.getItem("admin_token") ||
      ""
    );
  } catch {
    return "";
  }
}

function authHeaders() {
  const t = adminToken();
  return t ? { "X-Admin-Token": t, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

// Lightweight scoring: substring on label/desc/keywords + domain match.
function scoreItem(item, q) {
  if (!q) return 1; // show everything when empty (grouped by domain)
  const qLower = q.toLowerCase();
  const tokens = qLower.split(/\s+/).filter(Boolean);
  const bag = [
    item.label,
    item.description,
    item.domainLabel,
    ...(item.keywords || []),
  ]
    .filter(Boolean)
    .join(" · ")
    .toLowerCase();
  let score = 0;
  for (const t of tokens) {
    if (!bag.includes(t)) return 0;
    // exact label word matches are worth more
    if (item.label.toLowerCase().split(/\s+/).includes(t)) score += 5;
    // start-of-label matches also worth more
    if (item.label.toLowerCase().startsWith(t)) score += 3;
    score += 1;
  }
  return score;
}

function CommandPaletteInner({ open, onClose }) {
  const [q, setQ] = useState("");
  const [occOps, setOccOps] = useState([]);
  const [entityHits, setEntityHits] = useState([]);
  const [entityLoading, setEntityLoading] = useState(false);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const staticIndex = useMemo(() => buildSearchIndex(), []);

  // Reset when opened / closed.
  useEffect(() => {
    if (open) {
      setQ("");
      setEntityHits([]);
      // Focus after paint.
      requestAnimationFrame(() => {
        try { inputRef.current?.focus(); } catch { /* ignore */ }
      });
    }
  }, [open]);

  // Lazily fetch OCC ops the first time the palette opens per session.
  useEffect(() => {
    if (!open || occOps.length > 0) return;
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(
          `${API}/api/admin/operations-control/overview`,
          { headers: authHeaders() },
        );
        if (!r.ok) return;
        const data = await r.json();
        if (cancelled) return;
        const ops = (data?.operations || []).map((op) => ({
          id: `occ:${op.id}`,
          kind: "operation",
          domain: "operations-control",
          domainLabel: "Operations Control Center",
          stripe: "#dc2626",
          label: op.title || op.id,
          description: op.description || "OCC operation",
          route: `/admin/operations-control?highlight=${encodeURIComponent(op.id)}`,
          keywords: ["occ", "operation", op.id, op.category].filter(Boolean),
        }));
        setOccOps(ops);
      } catch {
        /* palette must never crash the app */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, occOps.length]);

  // Debounced entity fetch (projects / employees / equipment) via the
  // existing admin search endpoint `/api/admin/search`. Returns
  // `{groups: [{label, rows: [{id,title,subtitle,link,...}]}]}`.
  useEffect(() => {
    if (!open) return;
    if (!q || q.length < 2) {
      setEntityHits([]);
      return;
    }
    const handle = setTimeout(async () => {
      setEntityLoading(true);
      try {
        const r = await fetch(
          `${API}/api/admin/search?q=${encodeURIComponent(q)}&limit=6`,
          { headers: authHeaders() },
        );
        if (!r.ok) {
          setEntityHits([]);
          setEntityLoading(false);
          return;
        }
        const data = await r.json();
        const groups = Array.isArray(data?.groups) ? data.groups : [];
        const mapped = [];
        for (const g of groups) {
          const groupLabel = g.label || "Entity";
          for (const row of g.rows || []) {
            mapped.push({
              id: `entity:${groupLabel}:${row.id}`,
              kind: "entity",
              domain: "entity",
              domainLabel: groupLabel,
              stripe: "#334155",
              label: row.title || String(row.id),
              description: row.subtitle || "",
              route: row.link || "/admin",
              keywords: [],
            });
          }
        }
        setEntityHits(mapped);
      } catch {
        setEntityHits([]);
      } finally {
        setEntityLoading(false);
      }
    }, 200);
    return () => clearTimeout(handle);
  }, [q, open]);

  // Merge + rank.
  const results = useMemo(() => {
    const all = [...staticIndex, ...occOps, ...entityHits];
    const scored = all
      .map((item) => ({ item, score: scoreItem(item, q) }))
      .filter((r) => r.score > 0);
    scored.sort((a, b) => b.score - a.score);
    // Cap results — always show at least all 12 domain heads even
    // when the query is empty.
    return scored.slice(0, 60).map((r) => r.item);
  }, [staticIndex, occOps, entityHits, q]);

  // Group by domain for display.
  const grouped = useMemo(() => {
    const bucket = {};
    for (const r of results) {
      const key = r.domain || "misc";
      bucket[key] = bucket[key] || { label: r.domainLabel, stripe: r.stripe, items: [] };
      bucket[key].items.push(r);
    }
    // Preserve DOMAINS_V3 order.
    const ordered = [];
    for (const d of DOMAINS_V3) {
      if (bucket[d.id]) ordered.push({ id: d.id, ...bucket[d.id] });
      delete bucket[d.id];
    }
    // Any remaining buckets appended at the end.
    for (const k of Object.keys(bucket)) {
      ordered.push({ id: k, ...bucket[k] });
    }
    return ordered;
  }, [results]);

  const activate = useCallback(
    (item) => {
      if (!item) return;
      onClose?.();
      // Small delay so React unmounts the palette before navigation.
      setTimeout(() => {
        try {
          navigate(item.route);
        } catch {
          window.location.assign(item.route);
        }
      }, 0);
    },
    [navigate, onClose],
  );

  const onKeyDown = useCallback(
    (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose?.();
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        const first = results[0];
        if (first) activate(first);
      }
    },
    [activate, onClose, results],
  );

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-start justify-center bg-slate-950/70 backdrop-blur-sm px-4 pt-[8vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Universal search"
      data-testid="admin-command-palette"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl rounded-xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 border-b border-slate-800 px-3 py-2.5">
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Search pages · operations · projects · employees · equipment…"
            className="flex-1 bg-transparent outline-none text-sm text-slate-100 placeholder-slate-500"
            data-testid="admin-command-palette-input"
            autoComplete="off"
            spellCheck="false"
          />
          <kbd className="text-[10px] px-1.5 py-0.5 rounded border border-slate-700 text-slate-400 font-mono">
            Esc
          </kbd>
          <button
            type="button"
            onClick={onClose}
            className="ml-1 rounded p-1 hover:bg-slate-800 text-slate-400"
            aria-label="Close search"
            data-testid="admin-command-palette-close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div
          className="max-h-[60vh] overflow-y-auto"
          data-testid="admin-command-palette-results"
        >
          {grouped.length === 0 && (
            <div className="px-4 py-8 text-center text-sm text-slate-500" data-testid="admin-command-palette-empty">
              {entityLoading ? "Searching…" : "No matches. Try a different search."}
            </div>
          )}
          {grouped.map((g) => (
            <div key={g.id} className="py-1">
              <div
                className="flex items-center gap-2 px-3 pt-2 pb-1 text-[10px] uppercase tracking-widest text-slate-500 font-semibold"
                data-testid={`admin-command-palette-group-${g.id}`}
              >
                <span
                  className="inline-block w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: g.stripe }}
                  aria-hidden="true"
                />
                {g.label}
              </div>
              {g.items.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => activate(item)}
                  className="w-full flex items-start gap-3 px-3 py-2 hover:bg-slate-800/70 text-left"
                  data-testid={`admin-command-palette-item-${item.id}`}
                  data-route={item.route}
                >
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-slate-100 font-medium truncate">
                      {item.label}
                    </div>
                    {item.description ? (
                      <div className="text-[11px] text-slate-500 truncate">
                        {item.description}
                      </div>
                    ) : null}
                  </div>
                  <div className="text-[10px] text-slate-500 shrink-0 mt-1 font-mono">
                    {item.kind === "operation" ? "OCC" : item.kind === "page" ? "Page" : "Entity"}
                  </div>
                </button>
              ))}
            </div>
          ))}
        </div>

        <div className="border-t border-slate-800 px-3 py-2 flex items-center justify-between text-[10px] text-slate-500">
          <span>
            <kbd className="px-1 py-0.5 rounded border border-slate-700 mr-1">↵</kbd>
            open the top match
          </span>
          <span>Tip: type a page, an operation, a project, or a person.</span>
        </div>
      </div>
    </div>
  );
}

// Global provider — wires the ⌘K / ⌘/ keyboard shortcut and the
// palette itself. Wrap the admin surface with <CommandPaletteProvider>
// so every admin route inherits the palette.
export function CommandPaletteProvider({ children }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    function onKey(e) {
      const meta = e.metaKey || e.ctrlKey;
      if (!meta) return;
      if (e.key === "k" || e.key === "K" || e.key === "/") {
        e.preventDefault();
        setOpen((v) => !v);
      }
    }
    window.addEventListener("keydown", onKey);
    // Expose an imperative opener for the sidebar button.
    window.__masciAdminOpenPalette = () => setOpen(true);
    return () => {
      window.removeEventListener("keydown", onKey);
      try { delete window.__masciAdminOpenPalette; } catch { /* ignore */ }
    };
  }, []);
  return (
    <>
      {children}
      <CommandPaletteInner open={open} onClose={() => setOpen(false)} />
    </>
  );
}

export default CommandPaletteInner;
