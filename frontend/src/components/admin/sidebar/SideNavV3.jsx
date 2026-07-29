// TRACK 25.02 · Admin Operating System — Phase D · SideNavV3.
//
// The 12-domain sidebar rendered behind the `masci.admin.nav.v3`
// feature flag. Human-first labels · one-line business purpose ·
// active-domain auto-expand · sessionStorage remembers what the
// operator had open.
//
// Every visible admin destination in the platform lives under one of
// these domains. Detail pages (like /admin/incidents/:id) are hidden
// from the nav to keep it scannable, but the Command Palette still
// surfaces them via search.

import React, { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ChevronRight, Search } from "lucide-react";
import { DOMAINS_V3, findActiveDomainIdV3 } from "@/app/admin/domainMapV3";

const STORAGE_KEY_OPEN = "masci.admin.sidebar.v3.openDomains";

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
  try {
    localStorage.setItem(STORAGE_KEY_OPEN, JSON.stringify(ids));
  } catch {
    /* ignore */
  }
}

function DomainRow({ domain, open, onToggle, activeId }) {
  const Icon = domain.icon;
  const isActive = activeId === domain.id;
  return (
    <button
      type="button"
      onClick={() => onToggle(domain.id)}
      data-testid={`admin-nav-v3-domain-${domain.id}`}
      aria-expanded={open}
      className={`group w-full flex items-stretch gap-0 rounded-xl transition-colors text-left glass-blur glass-bg glass-dark ${
        isActive ? "bg-slate-800/70" : "hover:bg-slate-800/40"
      }`}
    >
      <span
        aria-hidden="true"
        className="w-[3px] shrink-0 rounded-l-md"
        style={{ backgroundColor: domain.stripe }}
      />
      <span className="flex-1 min-w-0 flex items-start gap-2.5 px-3 py-2.5">
        <Icon className="w-4 h-4 mt-0.5 shrink-0 text-slate-100 drop-shadow-[0_2px_8px_rgba(15,23,42,0.5)]" />
        <span className="flex-1 min-w-0">
          <span className="block text-xs uppercase tracking-wider font-semibold leading-tight glass-text-light">
            {domain.label}
          </span>
          <span className="block text-[10.5px] mt-0.5 leading-tight truncate glass-text-muted-light">
            {domain.subline}
          </span>
        </span>
        <ChevronRight
          className={`w-3.5 h-3.5 mt-1 shrink-0 text-slate-500 transition-transform ${
            open ? "rotate-90" : ""
          }`}
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
        `flex items-start gap-2 pl-8 pr-3 py-2 rounded-xl transition-colors min-h-[40px] glass-blur glass-bg glass-dark ${
          isActive
            ? "bg-slate-800 text-white"
            : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
        }`
      }
      data-testid={`admin-nav-v3-route-${route.to}`}
    >
      {Icon ? <Icon className="w-3.5 h-3.5 mt-1 shrink-0 opacity-70" /> : null}
      <span className="min-w-0">
        <span className="block text-sm font-medium leading-tight glass-text-light">
          {route.label}
        </span>
        {route.desc ? (
          <span className="block text-[10.5px] mt-0.5 leading-tight truncate glass-text-muted-light">
            {route.desc}
          </span>
        ) : null}
      </span>
    </NavLink>
  );
}

export default function SideNavV3({ onNavigate, onOpenPalette }) {
  const { pathname } = useLocation();
  const activeDomainId = useMemo(
    () => findActiveDomainIdV3(pathname),
    [pathname],
  );

  const [openDomains, setOpenDomains] = useState(() => {
    const stored = readOpenDomains();
    if (stored) return stored;
    // Default open: Home + OCC + active domain.
    return Array.from(
      new Set(["home", "operations-control", activeDomainId].filter(Boolean)),
    );
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
    <nav
      className="space-y-3 p-3 elite-fluid-stack glass-blur glass-bg glass-dark elite-glass-sidebar rounded-[1.75rem]"
      data-testid="admin-side-nav-v3"
      aria-label="Administrative navigation"
    >
      <button
        type="button"
        onClick={onOpenPalette}
        className="w-full flex items-center gap-2 px-3 py-2 rounded-[1rem] bg-slate-900/60 border border-white/15 hover:bg-slate-800 transition-colors elite-glass-panel glass-blur glass-bg glass-dark"
        data-testid="admin-nav-v3-open-palette"
        aria-label="Open universal search"
      >
        <Search className="w-3.5 h-3.5 shrink-0" />
        <span className="text-xs font-medium flex-1 text-left glass-text-light">
          Search everything
        </span>
        <kbd className="text-[10px] px-1.5 py-0.5 rounded border border-slate-700 font-mono glass-text-muted-light">
          ⌘K
        </kbd>
      </button>

      {DOMAINS_V3.map((domain) => {
        const open = openDomains.includes(domain.id);
        return (
          <div key={domain.id} className="space-y-1">
            <DomainRow
              domain={domain}
              open={open}
              onToggle={toggle}
              activeId={activeDomainId}
            />
            {open && (
              <div
                className="space-y-0.5"
                data-testid={`admin-nav-v3-children-${domain.id}`}
              >
                {domain.visibleRoutes.map((r) => (
                  <ChildRow key={r.to} route={r} onNavigate={onNavigate} />
                ))}
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}
