import React from "react";
import { PortalShell } from "@/design-system";

export default function OdrPageShell({
  portalRole,
  pageTitle,
  subtitle,
  children,
  backHref = null,
  showBack = false,
}) {
  return (
    <PortalShell
      portalRole={portalRole}
      pageTitle={pageTitle}
      subtitle={subtitle}
      showSearch={false}
      showNotifications={false}
      showBack={showBack}
      backHref={backHref}
    >
      {children}
    </PortalShell>
  );
}