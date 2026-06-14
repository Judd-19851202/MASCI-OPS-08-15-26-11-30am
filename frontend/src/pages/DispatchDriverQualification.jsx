// iter353b · Dispatch Portal · Approved Drivers / CDL Readiness page.
// Route: /dispatch-portal/driver-qualification
// Read-only view backed by GET /api/dispatch/driver-qualification.
// UXS-11E: wrapped in PortalShell (Dispatch Portal).
import React from "react";
import { PortalShell } from "@/design-system";
import DispatchSideNavV2 from "@/components/dispatch/sidebar/DispatchSideNavV2";
import DriverQualificationReadOnlyView from "@/components/DriverQualificationReadOnlyView";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { useT } from "@/lib/i18n";

export default function DispatchDriverQualification() {
  const { t } = useT();
  const authHeaders = () => ({ "X-Dispatch-Token": getDispatchToken() || "" });

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Dispatch Portal · Approved Drivers / CDL Readiness"
      pageTitle={t("Driver Qualification")}
      subtitle={t("Dispatch read-only view of approved drivers and CDL readiness.")}
      sideNav={<DispatchSideNavV2 />}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-5" data-testid="dispatch-driver-qualification-page">
        <DriverQualificationReadOnlyView
          endpoint="/dispatch/driver-qualification"
          authHeaders={authHeaders}
          accent="orange"
          testidPrefix="dq-disp"
        />
      </div>
    </PortalShell>
  );
}
