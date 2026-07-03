// Track 19.31 · Shop Sidebar V2 (domain-grouped, two-tier)
//
// Mirrors PM SideNavV2 / Admin SideNavV2 component shape exactly. Different
// inputs:
//   - DOMAINS_V2 + FOOTER_RAIL_V2 sourced from the Shop domain map
//   - Asset Administrator lane appended conditionally (is_asset_admin flag
//     mirror from directoryAuth.js; admin-token holders always see it)
//   - storage keys namespaced to Shop (masci.shop.sidebar.openDomains)
//   - testid prefix `shop-nav-v2-*`
//
// Cross-portal consistency is the goal: an operator with Shop + HR + Admin
// tokens experiences identical interaction on the new sidebar in every portal.

import React, { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import {
  DOMAINS_V2,
  ASSET_ADMIN_DOMAIN,
  FOOTER_RAIL_V2,
  findActiveDomainId,
} from "./domainMap";
import { getAdminToken } from "@/lib/adminAuth";

const STORAGE_KEY_OPEN = "masci.shop.sidebar.openDomains";

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
      data-testid={`shop-nav-v2-domain-${domain.id}`}
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
      data-testid={`shop-nav-v2-route-${route.to}`}
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

export default function ShopSideNavV2({ onNavigate }) {
  const { pathname } = useLocation();

  // Track 19.31 · Asset Administrator lane visibility.
  // Same rule as ShopHubV2 section 09 (Track 19.28):
  //   - admin-token holders → always see it
  //   - shop users with masci.is_asset_admin=true → see it
  //   - everyone else → hidden
  const isAssetAdmin = useMemo(() => {
    try {
      if (getAdminToken()) return true;
      if (typeof window !== "undefined") {
        return window.localStorage.getItem("masci.is_asset_admin") === "true";
      }
    } catch { /* noop */ }
    return false;
  }, []);

  const effectiveDomains = useMemo(
    () => (isAssetAdmin ? [...DOMAINS_V2, ASSET_ADMIN_DOMAIN] : DOMAINS_V2),
    [isAssetAdmin]
  );

  const activeDomainId = useMemo(
    () => findActiveDomainId(pathname, effectiveDomains),
    [pathname, effectiveDomains]
  );

  const [openDomains, setOpenDomains] = useState(() => {
    const stored = readOpenDomains();
    if (stored) return stored;
    return Array.from(new Set(["recovery-attention", activeDomainId].filter(Boolean)));
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
    <nav className="space-y-3 p-3" data-testid="shop-side-nav-v2">
      {effectiveDomains.map((domain) => {
        const open = openDomains.includes(domain.id);
        return (
          <div key={domain.id} className="space-y-1">
            <DomainRow domain={domain} open={open} onToggle={toggle} activeId={activeDomainId} />
            {open && (
              <div className="space-y-0.5" data-testid={`shop-nav-v2-children-${domain.id}`}>
                {domain.routes.map((r) => (
                  <ChildRow key={r.to} route={r} onNavigate={onNavigate} />
                ))}
              </div>
            )}
          </div>
        );
      })}

      <div className="pt-3 mt-3 border-t border-slate-800 space-y-0.5" data-testid="shop-nav-v2-footer-rail">
        <div className="px-3 pb-1 text-[10px] font-mono uppercase tracking-wider text-slate-500">Pinned</div>
        {FOOTER_RAIL_V2.map((r) => (
          <ChildRow key={r.to} route={r} onNavigate={onNavigate} />
        ))}
      </div>
    </nav>
  );
}

// Feature-flag resolver — same shape as PM V2's isPmSidebarV2Enabled.
// Shop-namespaced so the flag toggles independently.
//
// Track 19.31 · Shop Sidebar V2 rollout. Default: ON. Escape hatch:
//   1. URL query `?shopSidebarV2=0` (sticky · writes to localStorage)
//   2. localStorage `masci.shop.sidebar.v2` ("0" → force OFF · "1" → on)
//   3. env REACT_APP_SHOP_SIDEBAR_V2 ("0" → off)
//   4. default: ON
export function isShopSidebarV2Enabled() {
  if (typeof window === "undefined") return true;
  try {
    const qs = new URLSearchParams(window.location.search);
    if (qs.has("shopSidebarV2")) {
      const v = qs.get("shopSidebarV2");
      const on = !(v === "0" || v === "false");
      try { localStorage.setItem("masci.shop.sidebar.v2", on ? "1" : "0"); } catch { /* ignore */ }
      return on;
    }
    const ls = localStorage.getItem("masci.shop.sidebar.v2");
    if (ls === "1") return true;
    if (ls === "0") return false;
  } catch { /* ignore */ }
  const env = (process.env.REACT_APP_SHOP_SIDEBAR_V2 || "").toLowerCase();
  if (env === "0" || env === "false") return false;
  return true;
}
