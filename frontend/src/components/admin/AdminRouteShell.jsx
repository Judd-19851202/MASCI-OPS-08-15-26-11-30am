import React from "react";
import { PortalShell } from "@/design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";

export function renderAdminRouteSideNav() {
  return <SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />;
}

export function AdminRouteShell({
  pageTitle,
  subtitle,
  portalRole = "Admin",
  primaryActions = null,
  crumbs = [],
  contentClassName = "max-w-7xl mx-auto px-4 sm:px-6 py-6",
  children,
  testId = "admin-route-shell",
}) {
  return (
    <PortalShell
      portalName="MASCI"
      portalRole={portalRole}
      pageTitle={pageTitle}
      subtitle={subtitle}
      primaryActions={primaryActions}
      sideNav={renderAdminRouteSideNav()}
    >
      <div className={contentClassName} data-testid={testId}>
        {crumbs?.length ? <AdminBreadcrumb crumbs={crumbs} /> : null}
        {children}
      </div>
    </PortalShell>
  );
}
