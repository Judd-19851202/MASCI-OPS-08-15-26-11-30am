import React from "react";
import { Link } from "react-router-dom";
import { ChevronDown, LayoutGrid } from "lucide-react";
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
  pm: "bg-emerald-700",
  shop: "bg-orange-600",
  hr: "bg-violet-700",
  safety: "bg-teal-700",
  dispatch: "bg-amber-700",
};

const PORTAL_USER_LOADER = {
  hr: getHrUser,
  safety: getSafetyUser,
  dispatch: getDispatchUser,
};

function emailOf(user) {
  return (user?.email || "").toString().trim().toLowerCase();
}

export default function PortalSwitcher({ current, className = "", variant = "dark" }) {
  const user = getDirectoryUser();
  const dirToken = getDirectoryToken();

  if (!dirToken || !user || !Array.isArray(user.portals) || user.portals.length < 2) {
    return null;
  }

  if (current && !user.portals.includes(current)) {
    try { clearDirectorySession(); } catch { /* ignore */ }
    return null;
  }

  if (current && PORTAL_USER_LOADER[current]) {
    let portalUser = null;
    try { portalUser = PORTAL_USER_LOADER[current](); } catch { portalUser = null; }
    const portalEmail = emailOf(portalUser);
    const dirEmail = emailOf(user);
    if (portalEmail && dirEmail && portalEmail !== dirEmail) {
      try { clearDirectorySession(); } catch { /* ignore */ }
      return null;
    }
  }

  const triggerClasses = variant === "light"
    ? "bg-white/90 text-[color:var(--ink-strong)] border-[color:var(--border-bold)] hover:bg-[color:var(--paper-card-muted)] shadow-sm"
    : "bg-white/10 hover:bg-white/20 text-white border-white/20";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className={`wp16-focus-ring inline-flex items-center gap-1.5 rounded-[var(--radius-control)] border px-3 h-[var(--control-height-sm)] text-xs font-semibold uppercase tracking-[0.14em] transition-[background-color,border-color,color,box-shadow] duration-[140ms] ${triggerClasses} ${className}`}
          data-testid="portal-switcher-trigger"
        >
          <LayoutGrid className="h-3.5 w-3.5" />
          Switch portal
          <ChevronDown className="h-3.5 w-3.5 opacity-70" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64" data-testid="portal-switcher-menu">
        <DropdownMenuLabel className="font-mono text-[10px] uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
          {user.name || user.email} · Access
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {user.portals.map((portal) => {
          const isCurrent = portal === current;
          return (
            <DropdownMenuItem
              key={portal}
              asChild
              disabled={isCurrent}
              className={isCurrent ? "opacity-60" : ""}
            >
              <Link
                to={PORTAL_HOME[portal] || "/"}
                className="flex items-center justify-between gap-2 cursor-pointer"
                data-testid={`portal-switcher-${portal}`}
              >
                <span className="inline-flex items-center gap-2">
                  <span className={`inline-block h-2.5 w-2.5 rounded-full ${PORTAL_DOT_COLOR[portal] || "bg-stone-500"}`} />
                  <span className="font-semibold text-[color:var(--ink-strong)]">{PORTAL_LABEL[portal] || portal}</span>
                </span>
                {isCurrent && (
                  <span className="text-[9px] font-mono uppercase tracking-[0.16em] text-[color:var(--ink-soft)]">
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