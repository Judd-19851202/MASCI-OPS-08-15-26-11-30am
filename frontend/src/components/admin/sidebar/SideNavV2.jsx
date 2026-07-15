// Phase IV.A.1 — Admin Sidebar V2 (domain-grouped, two-tier, behind feature flag)
//
// Visual contract: SIDEBAR_REARCHITECTURE.md (Tier 1 domain row + Tier 2 children)
// Verbiage: OPERATIONAL_VERBIAGE_DOCTRINE.md (coaching sublines, calm tone)
// Hierarchy: COMPONENT_HIERARCHY_STANDARD.md (z-index, badge, red-color restraint)
// Mobile contract: MOBILE_NAVIGATION_STANDARD.md (drawer scroll, touch targets)
//
// This component is rendered only when the V2 feature flag is on.
// The legacy <SideNav> in AdminShell.jsx remains the default until reviewed.

import React, { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { DOMAINS_V2, FOOTER_RAIL_V2, findActiveDomainId } from "./domainMap";

const STORAGE_KEY_OPEN = "masci.admin.sidebar.openDomains";

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
      data-testid={`admin-nav-v2-domain-${domain.id}`}
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
      data-testid={`admin-nav-v2-route-${route.to}`}
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
    // Default: operations expanded · active domain (if any) also expanded
    return Array.from(new Set(["operations", activeDomainId].filter(Boolean)));
  });

  // Auto-expand the active domain when route changes (don't auto-collapse others)
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
    <nav className="space-y-3 p-3" data-testid="admin-side-nav admin-side-nav-v2">
      {DOMAINS_V2.map((domain) => {
        const open = openDomains.includes(domain.id);
        return (
          <div key={domain.id} className="space-y-1">
            <DomainRow domain={domain} open={open} onToggle={toggle} activeId={activeDomainId} />
            {open && (
              <div className="space-y-0.5" data-testid={`admin-nav-v2-children-${domain.id}`}>
                {domain.routes.map((r) => (
                  <ChildRow key={r.to} route={r} onNavigate={onNavigate} />
                ))}
              </div>
            )}
          </div>
        );
      })}

      <div className="pt-3 mt-3 border-t border-slate-800 space-y-0.5" data-testid="admin-nav-v2-footer-rail">
        <div className="px-3 pb-1 text-[10px] font-mono uppercase tracking-wider text-slate-500">Pinned</div>
        {FOOTER_RAIL_V2.map((r) => (
          <ChildRow key={r.to} route={r} onNavigate={onNavigate} />
        ))}
      </div>
    </nav>
  );
}

// Feature-flag resolver. The V2 nav renders ONLY when this returns true.
// Sources (in priority order):
//   1. localStorage `masci.admin.sidebar.v2` ("1" → on · "0" → off)
//   2. URL query `?adminSidebarV2=1` (sticky · persisted to localStorage)
//   3. env REACT_APP_ADMIN_SIDEBAR_V2 ("1" / "true" → on)
//   4. default: off (legacy nav)
//
// This makes the rollout manually reversible without a redeploy.
export function isAdminSidebarV2Enabled() {
  if (typeof window === "undefined") return false;
  try {
    const qs = new URLSearchParams(window.location.search);
    if (qs.has("adminSidebarV2")) {
      const v = qs.get("adminSidebarV2");
      const on = v === "1" || v === "true";
      try { localStorage.setItem("masci.admin.sidebar.v2", on ? "1" : "0"); } catch { /* ignore */ }
      return on;
    }
    const ls = localStorage.getItem("masci.admin.sidebar.v2");
    if (ls === "1") return true;
    if (ls === "0") return false;
  } catch { /* ignore */ }
  const env = (process.env.REACT_APP_ADMIN_SIDEBAR_V2 || "").toLowerCase();
  return env === "1" || env === "true";
}
