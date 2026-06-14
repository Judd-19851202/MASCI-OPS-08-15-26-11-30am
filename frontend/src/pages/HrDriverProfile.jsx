// DCP-1 · Driver Command Profile · HR view.
// Reuses the shared <DriverCommandProfile /> component. Role redaction
// happens server-side based on the X-HR-Token attached by api.js.
// UXS-11E: wrapped in PortalShell (HR Portal).
import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { PortalShell } from "@/design-system";
import HrSideNavV2 from "@/components/hr/sidebar/HrSideNavV2";
import DriverCommandProfile from "@/components/DriverCommandProfile";
import { usePageTitle } from "@/lib/usePageTitle";

export default function HrDriverProfile() {
  const { driverKey } = useParams();
  const nav = useNavigate();
  usePageTitle("Driver Command Profile · HR · MASCI");
  return (
    <PortalShell
      portalName="MASCI"
      portalRole="HR Portal · Driver"
      pageTitle="Driver Command Profile"
      subtitle="Identity · qualification · readiness"
      sideNav={<HrSideNavV2 />}
      primaryActions={
        <Button
          variant="outline"
          size="sm"
          onClick={() => nav("/hr/motive-drivers")}
          data-testid="hr-driver-profile-cleanup"
        >
          Motive Driver Cleanup
        </Button>
      }
    >
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6" data-testid="hr-driver-profile-page">
        <DriverCommandProfile driverKey={driverKey} />
      </div>
    </PortalShell>
  );
}
