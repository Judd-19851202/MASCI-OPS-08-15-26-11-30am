// IamUserDetailDrawer.jsx — iter506 · OMEGA Unified User Detail Drawer Sprint
//
// Read-only canonical drawer for ANY user surface (Admin People & Access,
// HR Field Leadership management, portal-specific panels). Reads only user
// fields already in scope; performs ZERO backend writes; reuses the same
// IamBadges + userBadges reducers as the row strip.
//
// Open contract:
//   window.__openIamUserDrawer({ user, portal })
//
// The host page mounts <IamUserDetailDrawerHost /> once. Every IamStandard
// row exposes a "View Details" button that calls the open contract.
import React, { useEffect, useState, useCallback } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Link } from "react-router-dom";
import {
  Mail,
  Shield,
  KeyRound,
  Activity,
  History,
  Briefcase,
  ExternalLink,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import {
  ACCESS_BADGE_CLASS,
  ACCESS_BADGE_LABEL,
  PASSWORD_BADGE_CLASS,
  PASSWORD_BADGE_LABEL,
  normalizeAccessStatus,
  normalizePasswordStatus,
  normalizeActivity,
  formatRelative,
} from "@/lib/iam/userBadges";

const ALL_PORTALS = ["admin", "pm", "hr", "safety", "dispatch", "shop", "field_leadership"];
const PORTAL_LABEL = {
  admin: "Admin",
  pm: "Project Manager",
  hr: "HR",
  safety: "Safety",
  dispatch: "Dispatch",
  shop: "Shop",
  field_leadership: "Field Leadership",
};

const TOOLTIP_UNAVAILABLE = "Not tracked by this login source yet.";

/** Single labelled metadata row inside the drawer. */
function Metric({ icon: Icon, label, value, tooltip }) {
  return (
    <div className="flex items-start gap-2 py-1.5">
      <Icon className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-slate-500 font-bold">
          {label}
        </div>
        <div
          className="text-sm text-slate-800 break-words"
          title={value === "—" && tooltip ? tooltip : undefined}
        >
          {value || "—"}
        </div>
      </div>
    </div>
  );
}

function PortalGrants({ user, portal }) {
  // Per-portal panels pass `portal` (single portal). The Access Control / Unified
  // Directory panels pass user.portals as an array. Normalise.
  // Some surfaces use kebab-case "field-leadership"; canonical key is snake_case.
  const normPortal = (portal || "").replace(/-/g, "_");
  let assigned = [];
  if (Array.isArray(user?.portals) && user.portals.length > 0) {
    assigned = user.portals.map((p) => String(p).replace(/-/g, "_"));
  } else if (normPortal) {
    assigned = [normPortal];
  }
  const assignedSet = new Set(assigned);
  return (
    <div className="grid grid-cols-2 gap-1.5">
      {ALL_PORTALS.map((p) => {
        const granted = assignedSet.has(p);
        return (
          <div
            key={p}
            data-testid={`iam-drawer-portal-${p}`}
            className={`flex items-center gap-2 px-2 py-1.5 rounded border ${
              granted
                ? "bg-emerald-50 border-emerald-300 text-emerald-800"
                : "bg-slate-50 border-slate-200 text-slate-400"
            }`}
          >
            {granted ? (
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            ) : (
              <XCircle className="w-3.5 h-3.5 shrink-0" />
            )}
            <span className="text-sm font-medium truncate">{PORTAL_LABEL[p]}</span>
          </div>
        );
      })}
    </div>
  );
}

export function IamUserDetailDrawerHost() {
  const [state, setState] = useState({ open: false, user: null, portal: null });

  const close = useCallback(() => setState((s) => ({ ...s, open: false })), []);

  useEffect(() => {
    const openFn = ({ user, portal }) => setState({ open: true, user, portal });
    if (typeof window !== "undefined") {
      window.__openIamUserDrawer = openFn;
    }
    return () => {
      if (typeof window !== "undefined" && window.__openIamUserDrawer === openFn) {
        delete window.__openIamUserDrawer;
      }
    };
  }, []);

  const { open, user, portal } = state;
  if (!user) {
    return (
      <Sheet open={open} onOpenChange={(v) => !v && close()}>
        <SheetContent side="right" className="w-full sm:max-w-md">
          <SheetHeader>
            <SheetTitle>No user selected</SheetTitle>
          </SheetHeader>
        </SheetContent>
      </Sheet>
    );
  }

  const access = normalizeAccessStatus(user);
  const password = normalizePasswordStatus(user);
  const activity = normalizeActivity(user);
  const email = user.email || "";
  const auditHref = email
    ? `/admin/audit?actor=${encodeURIComponent(email)}`
    : "/admin/audit";
  const sourceLabel = user.mirrored
    ? `Mirrored from ${portal || "portal"}`
    : portal
    ? PORTAL_LABEL[portal] || portal
    : "Managed";

  return (
    <Sheet open={open} onOpenChange={(v) => !v && close()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-md overflow-y-auto"
        data-testid="iam-user-detail-drawer"
      >
        <SheetHeader>
          <SheetTitle className="font-display text-lg font-black tracking-tight text-slate-900">
            {user.name || email.split("@")[0] || "User"}
          </SheetTitle>
          <SheetDescription className="text-xs font-mono text-slate-500 break-all">
            <Mail className="inline w-3 h-3 mr-1" />
            {email}
          </SheetDescription>
        </SheetHeader>

        {/* IDENTITY ----------------------------------------------------- */}
        <section className="mt-4 border-t border-slate-200 pt-3" data-testid="iam-drawer-identity">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-600 font-bold mb-1">
            Identity
          </div>
          <Metric icon={Briefcase} label="Employee ID" value={user.employee_id || "—"} tooltip={TOOLTIP_UNAVAILABLE} />
          <Metric icon={Shield} label="Source" value={sourceLabel} />
          <div className="flex items-center gap-2 mt-1">
            <span
              data-testid="iam-drawer-access-badge"
              className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold uppercase tracking-wide ${ACCESS_BADGE_CLASS[access]}`}
            >
              {ACCESS_BADGE_LABEL[access]}
            </span>
            <span
              data-testid="iam-drawer-password-badge"
              className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold uppercase tracking-wide ${PASSWORD_BADGE_CLASS[password]}`}
            >
              {PASSWORD_BADGE_LABEL[password]}
            </span>
          </div>
        </section>

        {/* PORTAL ACCESS ------------------------------------------------ */}
        <section className="mt-4 border-t border-slate-200 pt-3" data-testid="iam-drawer-portals">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-600 font-bold mb-2">
            Portal Access
          </div>
          <PortalGrants user={user} portal={portal} />
        </section>

        {/* ACTIVITY ----------------------------------------------------- */}
        <section className="mt-4 border-t border-slate-200 pt-3" data-testid="iam-drawer-activity">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-600 font-bold mb-1">
            Activity
          </div>
          <Metric
            icon={Activity}
            label="Last Login"
            value={activity.last_login ? formatRelative(activity.last_login) : "—"}
            tooltip={TOOLTIP_UNAVAILABLE}
          />
          <Metric
            icon={Activity}
            label="Last Activity"
            value={activity.last_activity ? formatRelative(activity.last_activity) : "—"}
            tooltip={TOOLTIP_UNAVAILABLE}
          />
          <Metric
            icon={KeyRound}
            label="Last Password Issued"
            value={activity.last_password_issued ? formatRelative(activity.last_password_issued) : "—"}
            tooltip={TOOLTIP_UNAVAILABLE}
          />
          <Metric
            icon={KeyRound}
            label="Issued By"
            value={activity.issued_by || "—"}
            tooltip={TOOLTIP_UNAVAILABLE}
          />
        </section>

        {/* AUDIT -------------------------------------------------------- */}
        <section className="mt-4 border-t border-slate-200 pt-3" data-testid="iam-drawer-audit">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-600 font-bold mb-2">
            Audit
          </div>
          <Link
            to={auditHref}
            onClick={close}
            data-testid="iam-drawer-audit-link"
            className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold"
          >
            <History className="w-4 h-4" />
            View Full Audit History
            <ExternalLink className="w-3 h-3 opacity-70" />
          </Link>
        </section>
      </SheetContent>
    </Sheet>
  );
}

/** Imperative open helper for callers (re-exported convenience). */
export function openIamUserDrawer(user, portal) {
  if (typeof window === "undefined") return;
  if (typeof window.__openIamUserDrawer !== "function") {
    // Host not mounted on this page — surface gracefully.
    console.warn("[iam] User Detail Drawer host not mounted on this page.");
    return;
  }
  window.__openIamUserDrawer({ user, portal });
}

export default IamUserDetailDrawerHost;
