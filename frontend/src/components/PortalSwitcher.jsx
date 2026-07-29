// PortalSwitcher.jsx — Dropdown in portal headers (iter82)
//
// Shows a "Switch portal" pill in any portal header that lets a multi-
// portal user jump to another portal they have access to. Reads the
// directory user from localStorage; if the user only has one portal (or
// none — anonymous), the widget renders nothing.
//
// Iter179 P0 access-control hardening: previously the widget rendered
// from any non-empty directory user, even if a stale super-admin
// session was sitting in localStorage from a prior multi-login that
// was never cleaned up. We now ALSO require that the currently-active
// portal's user identity matches the directory user — otherwise the
// switcher refuses to render and (defensively) clears the stale
// directory session.
//
// Drop into any portal hub/header with:
//   <PortalSwitcher current="admin" />

import React from "react";
import { Link } from "react-router-dom";
import { getDirectoryToken, getDirectoryUser, clearDirectorySession } from "@/lib/directoryAuth";
import { getHrUser } from "@/lib/hrAuth";
import { getSafetyUser } from "@/lib/safetyAuth";
import { getDispatchUser } from "@/lib/dispatchAuth";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronDown, LayoutGrid } from "lucide-react";

const PORTAL_LABEL = {
  admin: "Administration",
  pm: "Project Management",
  shop: "Shop Operations",
  hr: "Human Resources",
  safety: "Safety Operations",
  dispatch: "Transportation Operations",
};

const PORTAL_HOME = {
  admin: "/admin",
  pm: "/pm",
  shop: "/shop",
  hr: "/hr",
  safety: "/safety-portal",
  dispatch: "/dispatch-portal",
};

const PORTAL_DOT_COLOR = {
  admin: "bg-red-700",
  pm: "bg-red-600",
  shop: "bg-orange-600",
  hr: "bg-purple-700",
  safety: "bg-cyan-700",
  dispatch: "bg-orange-700",
};

// Map "current portal" → loader for the per-portal user object that
// the per-portal login wrote into localStorage. Used to confirm the
// directory user object actually belongs to the human running this
// session (defends against stale cross-session leakage). Portals
// that don't persist a user object (PM, Shop) get a null loader,
// in which case the email-match guard is skipped — the portals-list
// guard above still applies.
const PORTAL_USER_LOADER = {
  hr: getHrUser,
  safety: getSafetyUser,
  dispatch: getDispatchUser,
};

function _emailOf(user) {
  return (user?.email || "").toString().trim().toLowerCase();
}

/**
 * @param {Object} props
 * @param {"admin"|"pm"|"shop"|"hr"|"safety"|"dispatch"|undefined} props.current
 * @param {string} props.className — wrapper class overrides
 */
export default function PortalSwitcher({ current, className = "" }) {
  const user = getDirectoryUser();
  const dirToken = getDirectoryToken();
  if (!dirToken || !user || !Array.isArray(user.portals) || user.portals.length < 2) {
    return null;
  }

  // Iter179 P0 hardening — the directory user must (a) own the
  // current portal AND (b) match the per-portal user object on
  // record. If either check fails the directory session is stale
  // from a prior login that wasn't fully cleared. Clear it now and
  // render nothing.
  if (current && !user.portals.includes(current)) {
    try { clearDirectorySession(); } catch { /* ignore */ }
    return null;
  }
  if (current && PORTAL_USER_LOADER[current]) {
    let portalUser = null;
    try { portalUser = PORTAL_USER_LOADER[current](); } catch { portalUser = null; }
    const portalEmail = _emailOf(portalUser);
    const dirEmail = _emailOf(user);
    if (portalEmail && dirEmail && portalEmail !== dirEmail) {
      // The stored multi-portal directory user is a DIFFERENT human
      // from the one currently signed into this portal — i.e. stale
      // state. Refuse to render and defensively wipe the directory
      // session so the next render is clean.
      try { clearDirectorySession(); } catch { /* ignore */ }
      return null;
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className={`inline-flex items-center gap-1.5 px-3 h-8 rounded-md bg-white/10 hover:bg-white/20 text-white text-xs font-bold uppercase tracking-wide border border-white/20 transition-colors ${className}`}
          data-testid="portal-switcher-trigger"
        >
          <LayoutGrid className="w-3.5 h-3.5" />
          Switch portal
          <ChevronDown className="w-3.5 h-3.5 opacity-70" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56" data-testid="portal-switcher-menu">
        <DropdownMenuLabel className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
          {user.name || user.email} · Access
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {user.portals.map((p) => {
          const isCurrent = p === current;
          return (
            <DropdownMenuItem
              key={p}
              asChild
              disabled={isCurrent}
              className={isCurrent ? "opacity-50" : ""}
            >
              <Link
                to={PORTAL_HOME[p] || "/"}
                className="flex items-center justify-between gap-2 cursor-pointer"
                data-testid={`portal-switcher-${p}`}
              >
                <span className="inline-flex items-center gap-2">
                  <span className={`inline-block w-2 h-2 rounded-full ${PORTAL_DOT_COLOR[p] || "bg-slate-500"}`} />
                  <span className="font-bold">{PORTAL_LABEL[p] || p}</span>
                </span>
                {isCurrent && (
                  <span className="text-[9px] font-mono uppercase tracking-wider text-slate-500">
                    Current
                  </span>
                )}
              </Link>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
