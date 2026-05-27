// PM section pages — each is a thin wrapper over PmShell + the existing
// admin/PM-scoped panels that previously lived in PmHub as one tall scroll.
//
// (iter105 · iter437/IV-BETA.2 coaching cleanup — doctrine-compliant sublines
//  per CROSS_PORTAL_COACHING_STANDARD.md §V · ≤14 words · sentence-case ·
//  no "PMs have read-only access — edits live in…" feature-listing · no
//  forbidden "Pull" / casual verbs · ends with a period.)

import React from "react";
import PmShell from "@/components/PmShell";
import AdminJobMasterPanel from "@/components/AdminJobMasterPanel";
import EquipmentStatusBoard from "@/components/EquipmentStatusBoard";
import EquipmentMasterPanel from "@/components/EquipmentMasterPanel";
import EquipmentPartsPanel from "@/components/EquipmentPartsPanel";
import EmployeeMasterPanel from "@/components/EmployeeMasterPanel";
import SupplierMasterPanel from "@/components/SupplierMasterPanel";
import SitePostersPanel from "@/components/SitePostersPanel";
import TrainingStatsStripe from "@/components/TrainingStatsStripe";
import AutoEmailRoutingPanel from "@/components/AutoEmailRoutingPanel";
import ComplianceExportPanel from "@/components/ComplianceExportPanel";

// Calm doctrine-compliant subline — sentence-case slate-500, ≤14 words.
const Subline = ({ children }) => (
  <p className="text-xs text-slate-500 leading-relaxed">{children}</p>
);

export function PmJobs() {
  return (
    <PmShell title="Jobs" section="jobs"
      intro={<Subline>Active jobs assigned to you and the master roster.</Subline>}>
      <AdminJobMasterPanel />
    </PmShell>
  );
}

export function PmFleet() {
  return (
    <PmShell title="Equipment Fleet" section="fleet"
      intro={<Subline>Status board, master roster, and parts across your fleet.</Subline>}>
      <EquipmentStatusBoard />
      <div className="mt-6">
        <EquipmentMasterPanel />
      </div>
      <div className="mt-6">
        <EquipmentPartsPanel />
      </div>
    </PmShell>
  );
}

export function PmPeople() {
  return (
    <PmShell title="People" section="people"
      intro={<Subline>Employee master roster (read-only).</Subline>}>
      <EmployeeMasterPanel />
    </PmShell>
  );
}

export function PmSuppliers() {
  return (
    <PmShell title="Suppliers" section="suppliers"
      intro={<Subline>Approved supplier roster with contacts (read-only).</Subline>}>
      <SupplierMasterPanel />
    </PmShell>
  );
}

export function PmPosters() {
  return (
    <PmShell title="Site Posters" section="posters"
      intro={<Subline>Printable JHA, trench box, and inspection QR posters for the trailer.</Subline>}>
      <SitePostersPanel />
      <div className="mt-6">
        <TrainingStatsStripe />
      </div>
    </PmShell>
  );
}

export function PmRouting() {
  return (
    <PmShell title="Email Routing" section="routing"
      intro={<Subline>Active auto-routing rules per form (admin-edited).</Subline>}>
      <AutoEmailRoutingPanel />
    </PmShell>
  );
}

export function PmComplianceExport() {
  return (
    <PmShell title="Compliance Export" section="compliance-export"
      intro={<Subline>Date-range CSV of safety records for audits and insurance reviews.</Subline>}>
      <ComplianceExportPanel hideBackupTools />
    </PmShell>
  );
}
