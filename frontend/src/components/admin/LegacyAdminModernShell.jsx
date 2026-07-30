// TRACK 25C · ADMIN OS FINAL UNIFICATION
// ────────────────────────────────────────────────────────────────
// One shell to modernize every legacy admin page.
//
// The Admin OS ships one shell — PortalShell + SideNavV3 +
// AdminBreadcrumb. Domain landings (Sprint 3-6) use
// `DomainLandingShell` which composes those primitives on top of a
// declarative manifest. Legacy admin pages predate that shell and
// still render inside `components/AdminShell.jsx` (red top-bar,
// bespoke sidebar, breadcrumb chip).
//
// This shell is the light-touch wrapper legacy pages swap into so
// they instantly inherit the modern chrome without a rewrite of
// their bodies. Every legacy page becomes:
//
//   <LegacyAdminModernShell
//     title="Sessions"
//     subtitle="Read-only forensic view — last 50 portal sessions."
//     breadcrumb={[
//       { label: "Identity & Security", to: "/admin/identity-security" },
//       { label: "Sessions" },
//     ]}
//     testidPrefix="admin-sessions"
//     primaryActions={<RefreshButton />}
//   >
//     {/* original body — unchanged panels / tables / forms */}
//   </LegacyAdminModernShell>
//
// Zero behavioural change to the body — just consistent shell.
// Zero-UTC compliant (no timestamps rendered here).
//
// Rule #7 · single action engine: legacy pages MUST NOT execute
// destructive actions inline. If a legacy page had a "run backup",
// "clear cache", "prune…" button it should be redirected to
// `/admin/operations-control?highlight=<op-id>` via a deep-link chip
// during modernization. The shell does not enforce this — it's a
// per-page decision recorded in TRACK_25B_IA_AUDIT.md.
//
import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PortalShell } from "@/design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";
import { Button } from "@/components/ui/button";

export default function LegacyAdminModernShell({
  title,
  subtitle = null,
  breadcrumb = [],
  primaryActions = null,
  testidPrefix = "legacy-admin-modern",
  onSignOut = null,
  signOutCapability = null,
  children,
}) {
  const actions = (
    <div className="flex items-center gap-2">
      <Button
        asChild
        variant="outline"
        size="sm"
        data-testid={`${testidPrefix}-back-adminos`}
      >
        <Link to="/admin">
          <ArrowLeft className="w-3.5 h-3.5" />
          Admin OS
        </Link>
      </Button>
      {primaryActions}
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50" data-testid={`${testidPrefix}-root`}>
      <PortalShell
        portalName="MASCI"
        portalRole="Admin"
        pageTitle={title}
        subtitle={subtitle}
        primaryActions={actions}
        onSignOut={onSignOut}
        signOutCapability={signOutCapability}
        sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
      >
        <AdminBreadcrumb
          crumbs={breadcrumb}
          testidPrefix={`${testidPrefix}-breadcrumb`}
        />
        {children}
      </PortalShell>
    </div>
  );
}
