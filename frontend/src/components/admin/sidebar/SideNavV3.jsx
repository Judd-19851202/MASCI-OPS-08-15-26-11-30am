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
      className={`group w-full flex items-stretch gap-0 rounded-sm border transition-colors text-left wp16-focus-ring ${
        isActive ? "border-orange-500 bg-orange-50" : "border-zinc-300 bg-white hover:bg-zinc-50"
      }`}
    >
      <span aria-hidden="true" className="w-[4px] shrink-0 rounded-l-sm" style={{ backgroundColor: domain.stripe }} />
      <span className="flex-1 min-w-0 flex items-start gap-2.5 px-3 py-3">
        <Icon className="w-4 h-4 mt-0.5 shrink-0 text-zinc-900" />
        <span className="flex-1 min-w-0">
          <span className="block text-xs uppercase tracking-[0.16em] font-semibold leading-tight text-zinc-950">
            {domain.label}
          </span>
          <span className="block text-[11px] mt-0.5 leading-snug text-zinc-600">
            {domain.subline}
          </span>
        </span>
        <ChevronRight className={`w-3.5 h-3.5 mt-1 shrink-0 text-zinc-500 transition-transform ${open ? "rotate-90" : ""}`} />
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
        `flex items-start gap-2 pl-5 pr-3 py-2.5 rounded-sm border transition-colors min-h-[44px] wp16-focus-ring ${
          isActive
            ? "border-orange-500 bg-orange-50 text-zinc-950"
            : "border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 hover:text-zinc-950"
        }`
      }
      data-testid={`admin-nav-v3-route-${route.to}`}
    >
      {Icon ? <Icon className="w-3.5 h-3.5 mt-1 shrink-0 opacity-80" /> : null}
      <span className="min-w-0">
        <span className="block text-sm font-semibold leading-tight">{route.label}</span>
        {route.desc ? <span className="block text-[11px] mt-0.5 leading-snug text-zinc-500">{route.desc}</span> : null}
      </span>
    </NavLink>
  );
}

export default function SideNavV3({ onNavigate, onOpenPalette }) {
  const { pathname } = useLocation();
  const activeDomainId = useMemo(() => findActiveDomainIdV3(pathname), [pathname]);

  const [openDomains, setOpenDomains] = useState(() => {
    const stored = readOpenDomains();
    if (stored) return stored;
    return Array.from(new Set(["home", "operations-control", activeDomainId].filter(Boolean)));
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
      ? openDomains.filter((domainId) => domainId !== id)
      : [...openDomains, id];
    setOpenDomains(next);
    writeOpenDomains(next);
  };

  return (
    <nav className="space-y-3 p-3 wp16-card wp16-shell-shadow" data-testid="admin-side-nav-v3" aria-label="Administrative navigation">
      <button
        type="button"
        onClick={onOpenPalette}
        className="w-full flex items-center gap-2 px-3 py-3 rounded-sm border border-zinc-300 bg-white hover:bg-zinc-50 transition-colors wp16-focus-ring"
        data-testid="admin-nav-v3-open-palette"
        aria-label="Open universal search"
      >
        <Search className="w-3.5 h-3.5 shrink-0" />
        <span className="text-xs font-semibold uppercase tracking-[0.14em] flex-1 text-left text-zinc-950">
          Search everything
        </span>
        <kbd className="text-[10px] px-1.5 py-0.5 rounded-sm border border-zinc-300 font-mono text-zinc-500">
          ⌘K
        </kbd>
      </button>

      {DOMAINS_V3.map((domain) => {
        const open = openDomains.includes(domain.id);
        return (
          <div key={domain.id} className="space-y-1.5">
            <DomainRow domain={domain} open={open} onToggle={toggle} activeId={activeDomainId} />
            {open ? (
              <div className="space-y-1" data-testid={`admin-nav-v3-children-${domain.id}`}>
                {domain.visibleRoutes.map((route) => (
                  <ChildRow key={route.to} route={route} onNavigate={onNavigate} />
                ))}
              </div>
            ) : null}
          </div>
        );
      })}
    </nav>
  );
}