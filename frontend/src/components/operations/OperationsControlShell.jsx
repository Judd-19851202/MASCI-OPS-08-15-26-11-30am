import React from "react";
import { PortalShell } from "@/design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";

export function OperationsControlShell({
  pageTitle,
  subtitle,
  crumbs,
  primaryActions,
  children,
  testId = "operations-control-shell",
}) {
  return (
    <div className="min-h-screen bg-slate-50" data-testid={testId}>
      <PortalShell
        portalName="MASCI"
        portalRole="Admin"
        pageTitle={pageTitle}
        subtitle={subtitle}
        primaryActions={primaryActions}
        sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
      >
        <AdminBreadcrumb crumbs={crumbs} testidPrefix={`${testId}-breadcrumb`} />
        {children}
      </PortalShell>
    </div>
  );
}