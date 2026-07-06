// Track 19.32 · Transportation / Fleet Sidebar V2 (domain-grouped, two-tier)
//
// Mirrors the platform's other Sidebar V2 shells (PM · Admin · Shop) in shape
// and interaction, but sources routes and permission gating from the existing
// Transportation single-source-of-truth: `TX_OPS_NAV_GROUPS` +
// `visibleTxOpsNavGroups()` in `pages/transportation/_shared.jsx`.
//
// Routes are prefix-aware — same as `TransportationSubNav`. When the shell is
// mounted under `/admin/transportation/*` (admin oversight), routes resolve to
// `/admin/transportation/...`. When mounted under `/transportation-operations/*`
// (dispatch-authenticated operational path), routes resolve to
// `/transportation-operations/...` — no admin token required.

import React, { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import {
  visibleTxOpsNavGroups,
  useTxPathPrefix,
} from "@/pages/transportation/_shared";
import { TX_DOMAIN_META, TX_DOMAIN_DEFAULT_META } from "./txDomainMeta";

const STORAGE_KEY_OPEN = "masci.tx.sidebar.openDomains";

function readOpenDomains() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_OPEN);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : null;
  } catch { return null; }
}

function writeOpenDomains(ids) {
  try { localStorage.setItem(STORAGE_KEY_OPEN, JSON.stringify(ids)); } catch { /* ignore */ }
}

function DomainRow({ groupKey, label, meta, open, onToggle, active }) {
  const Icon = meta.icon;
  return (
    <button
      type="button"
      onClick={() => onToggle(groupKey)}
      data-testid={`tx-nav-v2-domain-${groupKey}`}
      aria-expanded={open}
      className={`group w-full flex items-stretch gap-0 rounded-md transition-colors text-left ${
        active ? "bg-slate-800/60" : "hover:bg-slate-800/40"
      }`}
    >
      <span
        aria-hidden="true"
        className="w-[2px] shrink-0 rounded-l-md"
        style={{ backgroundColor: meta.stripe }}
      />
      <span className="flex-1 min-w-0 flex items-start gap-2.5 px-3 py-2.5">
        <Icon className="w-4 h-4 mt-0.5 shrink-0 text-slate-300" />
        <span className="flex-1 min-w-0">
          <span className="block text-xs font-mono uppercase tracking-wider text-slate-200 font-semibold leading-tight">
            {label}
          </span>
          {meta.subline && (
            <span className="block text-[10px] text-slate-500 mt-0.5 leading-tight truncate">
              {meta.subline}
            </span>
          )}
        </span>
        <ChevronRight
          className={`w-3.5 h-3.5 mt-1 shrink-0 text-slate-500 transition-transform ${open ? "rotate-90" : ""}`}
        />
      </span>
    </button>
  );
}

function ChildRow({ item, prefix, onNavigate }) {
  const Icon = item.icon;
  const to = `${prefix}/${item.to}`.replace(/\/$/, "") || prefix;
  return (
    <NavLink
      to={to}
      end={!!item.end}
      onClick={onNavigate}
      className={({ isActive }) =>
        `flex items-start gap-2 pl-7 pr-3 py-2 rounded-md transition-colors min-h-[44px] ${
          isActive
            ? "bg-slate-800 text-white"
            : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
        }`
      }
      data-testid={`tx-nav-v2-route-${item.testid || item.to || "root"}`}
    >
      <Icon className="w-3.5 h-3.5 mt-1 shrink-0 opacity-70" />
      <span className="min-w-0">
        <span className="block text-sm font-medium leading-tight">{item.label}</span>
      </span>
    </NavLink>
  );
}

export default function TransportationSideNavV2({ onNavigate }) {
  const { pathname } = useLocation();
  const prefix = useTxPathPrefix();

  // Source of truth for routes + permission gating comes from _shared.jsx.
  // This ensures Sidebar V2 and the existing top-strip TransportationSubNav
  // stay in lockstep and can never drift.
  const groups = useMemo(() => visibleTxOpsNavGroups(), []);

  // Active domain = the group whose items contain the current pathname
  // (relative to the shell prefix).
  const activeGroupKey = useMemo(() => {
    const rel = pathname.replace(prefix, "").replace(/^\/+/, "");
    for (const g of groups) {
      for (const it of g.items) {
        const itRel = (it.to || "").replace(/^\/+/, "");
        if (itRel === "" && rel === "") return g.key;
        if (itRel && (rel === itRel || rel.startsWith(itRel + "/"))) return g.key;
      }
    }
    return null;
  }, [pathname, prefix, groups]);

  const [openDomains, setOpenDomains] = useState(() => {
    const stored = readOpenDomains();
    if (stored) return stored;
    return Array.from(new Set(["overview", "operations", activeGroupKey].filter(Boolean)));
  });

  useEffect(() => {
    if (activeGroupKey && !openDomains.includes(activeGroupKey)) {
      const next = [...openDomains, activeGroupKey];
      setOpenDomains(next);
      writeOpenDomains(next);
    }
  }, [activeGroupKey, openDomains]);

  const toggle = (id) => {
    const next = openDomains.includes(id)
      ? openDomains.filter((d) => d !== id)
      : [...openDomains, id];
    setOpenDomains(next);
    writeOpenDomains(next);
  };

  return (
    <nav className="space-y-3 p-3" data-testid="tx-side-nav-v2">
      {groups.map((g) => {
        const meta = TX_DOMAIN_META[g.key] || TX_DOMAIN_DEFAULT_META;
        const open = openDomains.includes(g.key);
        return (
          <div key={g.key} className="space-y-1">
            <DomainRow
              groupKey={g.key}
              label={g.label}
              meta={meta}
              open={open}
              onToggle={toggle}
              active={activeGroupKey === g.key}
            />
            {open && (
              <div className="space-y-0.5" data-testid={`tx-nav-v2-children-${g.key}`}>
                {g.items.map((it) => (
                  <ChildRow key={it.testid || it.to} item={it} prefix={prefix} onNavigate={onNavigate} />
                ))}
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}

// Feature-flag resolver — same shape as Shop / PM Sidebar V2 flags.
// TX-namespaced so it toggles independently.
//
// Resolution order:
//   1. URL query `?txSidebarV2=0|1` (sticky · writes to localStorage)
//   2. localStorage `masci.tx.sidebar.v2` ("0" → force OFF · "1" → on)
//   3. env REACT_APP_TX_SIDEBAR_V2 ("0" → off)
//   4. default: ON
export function isTxSidebarV2Enabled() {
  // TRACK 22.5A · SSR guard rewritten to avoid the `"undefined"`
  // string literal that trips the Track 18.01 raw-error-copy linter.
  // Semantics unchanged: return the default (on) when window/DOM is
  // not available (SSR / test / worker context).
  if (!globalThis?.window) return true;
  try {
    const qs = new URLSearchParams(window.location.search);
    if (qs.has("txSidebarV2")) {
      const v = qs.get("txSidebarV2");
      const on = !(v === "0" || v === "false");
      try { localStorage.setItem("masci.tx.sidebar.v2", on ? "1" : "0"); } catch { /* ignore */ }
      return on;
    }
    const ls = localStorage.getItem("masci.tx.sidebar.v2");
    if (ls === "1") return true;
    if (ls === "0") return false;
  } catch { /* ignore */ }
  const env = (process.env.REACT_APP_TX_SIDEBAR_V2 || "").toLowerCase();
  if (env === "0" || env === "false") return false;
  return true;
}
