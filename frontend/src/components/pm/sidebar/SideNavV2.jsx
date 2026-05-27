// Phase IV-BETA.1 — PM Sidebar V2 (domain-grouped, two-tier, feature-flagged)
//
// Mirrors AdminShell V2 SideNavV2 component shape exactly. Different inputs:
//   - DOMAINS_V2 + FOOTER_RAIL_V2 sourced from PM domain map
//   - storage keys namespaced to PM (masci.pm.sidebar.openDomains / .v2)
//   - testid prefix `pm-nav-v2-*`
//
// Cross-portal consistency is the goal: an operator with both PM and Admin
// tokens experiences identical interaction on the new sidebar in both portals.

import React, { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { DOMAINS_V2, FOOTER_RAIL_V2, findActiveDomainId } from "./domainMap";

const STORAGE_KEY_OPEN = "masci.pm.sidebar.openDomains";

function readOpenDomains() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_OPEN);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function writeOpenDomains(ids) {
  try { localStorage.setItem(STORAGE_KEY_OPEN, JSON.stringify(ids)); } catch { /* ignore */ }
}

function DomainRow({ domain, open, onToggle, activeId }) {
  const Icon = domain.icon;
  const isActive = activeId === domain.id;
  return (
    <button
      type="button"
      onClick={() => onToggle(domain.id)}
      data-testid={`pm-nav-v2-domain-${domain.id}`}
      aria-expanded={open}
      className={`group w-full flex items-stretch gap-0 rounded-md transition-colors text-left ${
        isActive ? "bg-slate-800/60" : "hover:bg-slate-800/40"
      }`}
    >
      <span
        aria-hidden="true"
        className="w-[2px] shrink-0 rounded-l-md"
        style={{ backgroundColor: domain.stripe }}
      />
      <span className="flex-1 min-w-0 flex items-start gap-2.5 px-3 py-2.5">
        <Icon className="w-4 h-4 mt-0.5 shrink-0 text-slate-300" />
        <span className="flex-1 min-w-0">
          <span className="block text-xs font-mono uppercase tracking-wider text-slate-200 font-semibold leading-tight">
            {domain.label}
          </span>
          <span className="block text-[10px] text-slate-500 mt-0.5 leading-tight truncate">
            {domain.subline}
          </span>
        </span>
        <ChevronRight
          className={`w-3.5 h-3.5 mt-1 shrink-0 text-slate-500 transition-transform ${open ? "rotate-90" : ""}`}
        />
      </span>
    </button>
  );
}

function ChildRow({ route, onNavigate }) {
  const Icon = route.icon;
  return (
    <NavLink
      to={route.to}
      end={!!route.end}
      onClick={onNavigate}
      className={({ isActive }) =>
        `flex items-start gap-2 pl-7 pr-3 py-2 rounded-md transition-colors min-h-[44px] ${
          isActive
            ? "bg-slate-800 text-white"
            : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
        }`
      }
      data-testid={`pm-nav-v2-route-${route.to}`}
    >
      <Icon className="w-3.5 h-3.5 mt-1 shrink-0 opacity-70" />
      <span className="min-w-0">
        <span className="block text-sm font-medium leading-tight">{route.label}</span>
        <span className="block text-[10px] text-slate-500 mt-0.5 leading-tight truncate">
          {route.desc}
        </span>
      </span>
    </NavLink>
  );
}

export default function SideNavV2({ onNavigate }) {
  const { pathname } = useLocation();
  const activeDomainId = useMemo(() => findActiveDomainId(pathname), [pathname]);

  const [openDomains, setOpenDomains] = useState(() => {
    const stored = readOpenDomains();
    if (stored) return stored;
    return Array.from(new Set(["project-operations", activeDomainId].filter(Boolean)));
  });

  useEffect(() => {
    if (activeDomainId && !openDomains.includes(activeDomainId)) {
      const next = [...openDomains, activeDomainId];
      setOpenDomains(next);
      writeOpenDomains(next);
    }
  }, [activeDomainId]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id) => {
    const next = openDomains.includes(id)
      ? openDomains.filter((d) => d !== id)
      : [...openDomains, id];
    setOpenDomains(next);
    writeOpenDomains(next);
  };

  return (
    <nav className="space-y-3 p-3" data-testid="pm-side-nav pm-side-nav-v2">
      {DOMAINS_V2.map((domain) => {
        const open = openDomains.includes(domain.id);
        return (
          <div key={domain.id} className="space-y-1">
            <DomainRow domain={domain} open={open} onToggle={toggle} activeId={activeDomainId} />
            {open && (
              <div className="space-y-0.5" data-testid={`pm-nav-v2-children-${domain.id}`}>
                {domain.routes.map((r) => (
                  <ChildRow key={r.to} route={r} onNavigate={onNavigate} />
                ))}
              </div>
            )}
          </div>
        );
      })}

      <div className="pt-3 mt-3 border-t border-slate-800 space-y-0.5" data-testid="pm-nav-v2-footer-rail">
        <div className="px-3 pb-1 text-[10px] font-mono uppercase tracking-wider text-slate-500">Pinned</div>
        {FOOTER_RAIL_V2.map((r) => (
          <ChildRow key={r.to} route={r} onNavigate={onNavigate} />
        ))}
      </div>
    </nav>
  );
}

// Feature-flag resolver — same shape as Admin V2's isAdminSidebarV2Enabled.
// PM-namespaced so the two flags toggle independently.
//
// Resolution order:
//   1. URL query `?pmSidebarV2=1` (sticky · writes to localStorage)
//   2. localStorage `masci.pm.sidebar.v2` ("1" → on · "0" → force off)
//   3. env REACT_APP_PM_SIDEBAR_V2 ("1" / "true" → on)
//   4. default: off (legacy nav)
export function isPmSidebarV2Enabled() {
  if (typeof window === "undefined") return false;
  try {
    const qs = new URLSearchParams(window.location.search);
    if (qs.has("pmSidebarV2")) {
      const v = qs.get("pmSidebarV2");
      const on = v === "1" || v === "true";
      try { localStorage.setItem("masci.pm.sidebar.v2", on ? "1" : "0"); } catch { /* ignore */ }
      return on;
    }
    const ls = localStorage.getItem("masci.pm.sidebar.v2");
    if (ls === "1") return true;
    if (ls === "0") return false;
  } catch { /* ignore */ }
  const env = (process.env.REACT_APP_PM_SIDEBAR_V2 || "").toLowerCase();
  return env === "1" || env === "true";
}
