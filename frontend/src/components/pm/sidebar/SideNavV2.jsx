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
      className={`group w-full flex items-stretch gap-0 rounded-xl transition-colors text-left glass-blur glass-bg glass-dark ${
        isActive ? "bg-slate-800/60" : "hover:bg-slate-800/40"
      }`}
    >
      <span
        aria-hidden="true"
        className="w-[2px] shrink-0 rounded-l-md"
        style={{ backgroundColor: domain.stripe }}
      />
      <span className="flex-1 min-w-0 flex items-start gap-2.5 px-3 py-2.5">
        <Icon className="w-4 h-4 mt-0.5 shrink-0 text-slate-100 drop-shadow-[0_2px_8px_rgba(15,23,42,0.5)]" />
        <span className="flex-1 min-w-0">
          <span className="block text-xs font-mono uppercase tracking-wider font-semibold leading-tight glass-text-light">
            {domain.label}
          </span>
          <span className="block text-[10px] mt-0.5 leading-tight truncate glass-text-muted-light">
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
        `flex items-start gap-2 pl-7 pr-3 py-2 rounded-xl transition-colors min-h-[44px] glass-blur glass-bg glass-dark ${
          isActive
            ? "bg-slate-800 text-white"
            : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
        }`
      }
      data-testid={`pm-nav-v2-route-${route.to}`}
    >
      <Icon className="w-3.5 h-3.5 mt-1 shrink-0 opacity-70" />
      <span className="min-w-0">
        <span className="block text-sm font-medium leading-tight glass-text-light">{route.label}</span>
        <span className="block text-[10px] mt-0.5 leading-tight truncate glass-text-muted-light">
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
  }, [activeDomainId, openDomains]);  

  const toggle = (id) => {
    const next = openDomains.includes(id)
      ? openDomains.filter((d) => d !== id)
      : [...openDomains, id];
    setOpenDomains(next);
    writeOpenDomains(next);
  };

  return (
    <nav className="space-y-3 p-3 glass-blur glass-bg glass-dark elite-glass-sidebar rounded-[1.75rem]" data-testid="pm-side-nav pm-side-nav-v2">
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

      <div className="pt-3 mt-3 border-t border-slate-700/70 space-y-0.5" data-testid="pm-nav-v2-footer-rail">
        <div className="px-3 pb-1 text-[10px] font-mono uppercase tracking-wider glass-text-muted-light">Pinned</div>
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
// iter437 IV-BETA.5A-P2B · PM V2 is now the DEFAULT layout. The flag
// still resolves cleanly so operators can opt out via `?pmSidebarV2=0`
// (or localStorage `masci.pm.sidebar.v2=0`) without redeploying.
//
// Resolution order:
//   1. URL query `?pmSidebarV2=0|1` (sticky · writes to localStorage)
//   2. localStorage `masci.pm.sidebar.v2` ("0" → force OFF · "1" → on)
//   3. env REACT_APP_PM_SIDEBAR_V2 ("0" → off)
//   4. default: **ON** (V2 default · iter437 IV-BETA.5A-P2B)
export function isPmSidebarV2Enabled() {
  if (typeof window === "undefined") return true;
  try {
    const qs = new URLSearchParams(window.location.search);
    if (qs.has("pmSidebarV2")) {
      const v = qs.get("pmSidebarV2");
      const on = !(v === "0" || v === "false");
      try { localStorage.setItem("masci.pm.sidebar.v2", on ? "1" : "0"); } catch { /* ignore */ }
      return on;
    }
    const ls = localStorage.getItem("masci.pm.sidebar.v2");
    if (ls === "1") return true;
    if (ls === "0") return false;
  } catch { /* ignore */ }
  const env = (process.env.REACT_APP_PM_SIDEBAR_V2 || "").toLowerCase();
  if (env === "0" || env === "false") return false;
  return true; // V2 default · escape hatch via ?pmSidebarV2=0
}
