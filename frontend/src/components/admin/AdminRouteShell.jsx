import React from "react";
import { PortalShell } from "@/design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";
import { useT } from "@/lib/i18n";

export function renderAdminRouteSideNav() {
  return <SideNavV3 variant="admin" onOpenPalette={() => window.__masciAdminOpenPalette?.()} />;
}

export function AdminRouteShell({
  pageTitle,
  subtitle,
  portalRole = "Admin",
  primaryActions = null,
  crumbs = [],
  showShellHeader = true,
  showBreadcrumbs = true,
  contentClassName = "max-w-7xl mx-auto px-4 sm:px-6 py-6",
  children,
  testId = "admin-route-shell",
}) {
  const { t } = useT();
  return (
    <PortalShell
      portalName="MASCI"
      portalRole={t(portalRole)}
      shellTheme="admin"
      pageTitle={typeof pageTitle === "string" ? t(pageTitle) : pageTitle}
      subtitle={typeof subtitle === "string" ? t(subtitle) : subtitle}
      primaryActions={primaryActions}
      showPageHeader={showShellHeader}
      sideNav={renderAdminRouteSideNav()}
    >
      <div className={`admin-route-shell-canvas ${contentClassName}`} data-testid={testId}>
        {showBreadcrumbs && crumbs?.length ? <AdminBreadcrumb crumbs={crumbs} /> : null}
        {children}
      </div>
    </PortalShell>
  );
}
