// HrMotiveDrivers.jsx — MCC-1 HR Access Extension
// Mounts the existing MappingCleanupTab inside the HR portal in HR scope.
// UXS-11E: wrapped in PortalShell (HR Portal).
import React from "react";
import { PortalShell } from "@/design-system";
import HrSideNavV2 from "@/components/hr/sidebar/HrSideNavV2";
import { usePageTitle } from "@/lib/usePageTitle";
import MappingCleanupTab from "@/components/admin/MappingCleanupTab";

export default function HrMotiveDrivers() {
  usePageTitle("Motive Driver Cleanup · HR · MASCI");
  return (
    <PortalShell
      portalName="MASCI"
      portalRole="HR Portal · Motive"
      pageTitle="Driver Cleanup"
      subtitle="Reconcile Motive drivers with employee directory"
      sideNav={<HrSideNavV2 />}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6" data-testid="hr-motive-drivers-page">
        <MappingCleanupTab mode="hr" />
      </div>
    </PortalShell>
  );
}
