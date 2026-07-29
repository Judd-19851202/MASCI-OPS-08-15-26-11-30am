import React from "react";

import OperationalHealthDashboardShell from "@/components/admin/operational-health/OperationalHealthDashboardShell";
import { usePageTitle } from "@/lib/usePageTitle";

export default function AdminGovernanceOperatingSystem() {
  usePageTitle("Operational Health Dashboard · Admin");
  return <OperationalHealthDashboardShell moduleId="enterprise-governance" />;
}