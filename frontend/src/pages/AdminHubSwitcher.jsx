// TRACK 25.02 · Admin Operating System — Phase D · Hub Switcher.
//
// Mounted at /admin. Reads the `masci.admin.nav.v3` feature flag and
// renders the V3 Executive Home when ON, otherwise the legacy V2 hub.
// The router doesn't have to know about V2/V3.
import React from "react";
import AdminHubV2 from "@/pages/AdminHubV2";
import AdminHubV3 from "@/pages/AdminHubV3";
import { isAdminNavV3Enabled } from "@/lib/featureFlags";

export default function AdminHubSwitcher() {
  return isAdminNavV3Enabled() ? <AdminHubV3 /> : <AdminHubV2 />;
}
