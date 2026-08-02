// DCP-1 · Driver Command Profile · Dispatch view.
// Dispatch only sees identity / operations / equipment per role redactor.
// UXS-11E: wrapped in PortalShell (Dispatch Portal).
import React from "react";
import { useParams } from "react-router-dom";
import { PortalShell } from "@/design-system";
import DispatchSideNavV2 from "@/components/dispatch/sidebar/DispatchSideNavV2";
import DriverCommandProfile from "@/components/DriverCommandProfile";
import { useT } from "@/lib/i18n";
import { usePageTitle } from "@/lib/usePageTitle";

export default function DispatchDriverProfile() {
  const { t } = useT();
  const { driverKey } = useParams();
  usePageTitle("Driver Command Profile · Dispatch · MASCI");
  return (
    <PortalShell
      portalName="MASCI"
      portalRole={t("Dispatch Portal · Driver")}
      pageTitle={t("Driver Command Profile")}
      subtitle={t("Identity · operations · equipment")}
      sideNav={<DispatchSideNavV2 />}
    >
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6" data-testid="dispatch-driver-profile-page">
        <DriverCommandProfile driverKey={driverKey} />
      </div>
    </PortalShell>
  );
}
