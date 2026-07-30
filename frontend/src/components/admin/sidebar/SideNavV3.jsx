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
      className={`wp16-focus-ring group relative flex w-full items-stretch gap-0 overflow-hidden rounded-[calc(var(--radius-card)-0.125rem)] border text-left transition-[background-color,border-color,box-shadow,transform] duration-[140ms] ${isActive ? "border-[color:rgba(185,28,28,0.25)] bg-[color:var(--brand-primary-soft)] shadow-sm" : "border-[color:var(--border-hairline)] bg-white hover:border-[color:var(--border-bold)] hover:bg-[color:var(--paper-card-muted)]"}`}
    >
      <span aria-hidden="true" className="w-1.5 shrink-0" style={{ backgroundColor: domain.stripe }} />
      <span className="flex min-w-0 flex-1 items-start gap-3 px-3 py-3">
        <span className={`mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${isActive ? "border-[color:rgba(185,28,28,0.18)] bg-white text-[color:var(--brand-primary)]" : "border-[color:var(--border-hairline)] bg-[color:var(--paper-card-muted)] text-[color:var(--ink-regular)]"}`}>
          <Icon className="h-4 w-4" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-[11px] font-semibold uppercase tracking-[0.14em] text-[color:var(--ink-strong)]">
            {domain.label}
          </span>
          <span className="mt-1 block truncate text-xs leading-5 text-[color:var(--ink-soft)]">
            {domain.subline}
          </span>
        </span>
        <ChevronRight className={`mt-1 h-4 w-4 shrink-0 text-[color:var(--ink-faint)] transition-transform duration-[140ms] ${open ? "rotate-90" : ""}`} />
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
        `wp16-focus-ring flex min-h-[44px] items-start gap-2 rounded-[0.9rem] border px-3 py-2.5 transition-[background-color,border-color,color,transform] duration-[140ms] ${isActive ? "border-[color:rgba(185,28,28,0.22)] bg-white text-[color:var(--ink-strong)] shadow-sm" : "border-transparent text-[color:var(--ink-soft)] hover:border-[color:var(--border-hairline)] hover:bg-white hover:text-[color:var(--ink-strong)]"}`
      }
      data-testid={`admin-nav-v3-route-${route.to}`}
    >
      {Icon ? <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0 opacity-70" /> : null}
      <span className="min-w-0">
        <span className="block text-sm font-semibold leading-tight">{route.label}</span>
        {route.desc ? <span className="mt-0.5 block truncate text-[11px] leading-tight text-[color:var(--ink-soft)]">{route.desc}</span> : null}
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
    const next = openDomains.includes(id) ? openDomains.filter((value) => value !== id) : [...openDomains, id];
    setOpenDomains(next);
    writeOpenDomains(next);
  };

  return (
    <nav
      className="space-y-3 rounded-[calc(var(--radius-card)+0.125rem)] border border-[color:var(--border-soft)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(250,250,249,0.94))] p-3 shadow-[var(--shadow-panel)]"
      data-testid="admin-side-nav-v3"
      aria-label="Administrative navigation"
    >
      <button
        type="button"
        onClick={onOpenPalette}
        className="wp16-focus-ring flex min-h-[44px] w-full items-center gap-2 rounded-[calc(var(--radius-card)-0.125rem)] border border-[color:var(--border-hairline)] bg-[color:var(--paper-card-muted)] px-3 py-2.5 text-left transition-[background-color,border-color,color] duration-[140ms] hover:border-[color:var(--border-bold)] hover:bg-white"
        data-testid="admin-nav-v3-open-palette"
        aria-label="Open universal search"
      >
        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-[color:var(--border-hairline)] bg-white text-[color:var(--ink-regular)]">
          <Search className="h-3.5 w-3.5" />
        </span>
        <span className="flex-1 text-sm font-semibold text-[color:var(--ink-strong)]">Search everything</span>
        <kbd className="rounded-md border border-[color:var(--border-bold)] bg-white px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-[0.16em] text-[color:var(--ink-soft)]">
          ⌘K
        </kbd>
      </button>

      {DOMAINS_V3.map((domain) => {
        const open = openDomains.includes(domain.id);
        return (
          <div key={domain.id} className="space-y-1.5">
            <DomainRow domain={domain} open={open} onToggle={toggle} activeId={activeDomainId} />
            {open ? (
              <div className="space-y-1 pl-2" data-testid={`admin-nav-v3-children-${domain.id}`}>
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