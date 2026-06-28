/**
 * TRACK 18.00 · Phase A · Operations group · Live Operations workspace.
 *
 * Admin-side mirror of the three Track 16.16 awareness widgets that
 * already render inside PmProjectDetail / PmCommandCenter /
 * OperationsCenterCommand. By embedding them ALSO inside
 * Transportation Operations, an admin can see exactly what PMs see
 * without leaving the parent workspace.
 *
 * Zero new backend (reuses `/api/operations/transportation/readiness`).
 */
import React from "react";
import TransportationWorkspaceShell from "./TransportationWorkspaceShell";
import {
  TransportationReadinessCard,
  TransportationRiskBanner,
  OperationsTransportationHealthWidget,
  TransportationCloseoutAwareness,
} from "@/components/operations_transportation_integration";

export default function LiveOperationsWorkspace() {
  return (
    <TransportationWorkspaceShell
      workspace="Operations"
      title="Live Operations"
      subtitle="Active operational awareness — admin mirror of the PM and Operations Center Transportation widgets."
    >
      <div data-testid="txops-live-operations" className="space-y-4">
        <TransportationRiskBanner />
        <OperationsTransportationHealthWidget />
        <TransportationReadinessCard />
        <TransportationCloseoutAwareness />
      </div>
    </TransportationWorkspaceShell>
  );
}
