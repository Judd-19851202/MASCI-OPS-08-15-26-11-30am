// PortalSwitcher.jsx — Dropdown in portal headers (iter82)
//
// Shows a "Switch portal" pill in any portal header that lets a multi-
// portal user jump to another portal they have access to. Reads the
// directory user from localStorage; if the user only has one portal (or
// none — anonymous), the widget renders nothing.
//
// Drop into any portal hub/header with:
//   <PortalSwitcher current="admin" />

import React from "react";
import { Link } from "react-router-dom";
import { getDirectoryUser } from "@/lib/directoryAuth";
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
  admin: "Admin Console",
  pm: "PM Portal",
  shop: "Shop Portal",
  hr: "HR Portal",
};

const PORTAL_HOME = {
  admin: "/admin",
  pm: "/pm",
  shop: "/shop",
  hr: "/hr",
};

const PORTAL_DOT_COLOR = {
  admin: "bg-red-700",
  pm: "bg-red-600",
  shop: "bg-orange-600",
  hr: "bg-purple-700",
};

/**
 * @param {Object} props
 * @param {"admin"|"pm"|"shop"|"hr"|undefined} props.current — current portal name
 * @param {string} props.className — wrapper class overrides
 */
export default function PortalSwitcher({ current, className = "" }) {
  const user = getDirectoryUser();
  if (!user || !Array.isArray(user.portals) || user.portals.length < 2) {
    return null;
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
