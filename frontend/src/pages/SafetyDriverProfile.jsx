// DCP-1 · Driver Command Profile · Safety view.
// Safety sees identity / operations / safety / training / equipment / motive.
// (No mapping_health — that's admin-only.)
// UXS-11E: wrapped in PortalShell (Safety Portal).
import React from "react";
import { useParams } from "react-router-dom";
import { PortalShell } from "@/design-system";
import SafetySideNavV2 from "@/components/safety/sidebar/SafetySideNavV2";
import DriverCommandProfile from "@/components/DriverCommandProfile";
import { usePageTitle } from "@/lib/usePageTitle";

export default function SafetyDriverProfile() {
  const { driverKey } = useParams();
  usePageTitle("Driver Profile · Safety · MASCI");
  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Safety Portal · Driver"
      pageTitle="Driver Profile"
      subtitle="Identity, safety, training, and equipment"
      sideNav={<SafetySideNavV2 />}
    >
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6" data-testid="safety-driver-profile-page">
        <DriverCommandProfile driverKey={driverKey} />
      </div>
    </PortalShell>
  );
}
