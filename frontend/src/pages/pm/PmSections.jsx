// PM section pages — each is a thin wrapper over PmShell + the existing
// admin/PM-scoped panels that previously lived in PmHub as one tall scroll.
// (iter105 — PM Portal cleanup mirroring AdminConsole architecture.)

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

export function PmJobs() {
  return (
    <PmShell title="Jobs" section="jobs"
      intro={<p className="text-sm text-slate-700">Active jobs assigned to you, plus the master job list. Add new jobs from here — they auto-appear in every form picker on the platform.</p>}>
      <AdminJobMasterPanel />
    </PmShell>
  );
}

export function PmFleet() {
  return (
    <PmShell title="Equipment Fleet" section="fleet"
      intro={<p className="text-sm text-slate-700">Live status of every piece of equipment across your jobs. Below is the master fleet roster and parts catalog (read-only from this view).</p>}>
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
      intro={<p className="text-sm text-slate-700">Master roster of every MASCI employee. PMs have read-only access — additions and edits live in the Admin Console.</p>}>
      <EmployeeMasterPanel />
    </PmShell>
  );
}

export function PmSuppliers() {
  return (
    <PmShell title="Suppliers" section="suppliers"
      intro={<p className="text-sm text-slate-700">Approved supplier list with contacts. PMs have read-only access — additions and edits live in the Admin Console.</p>}>
      <SupplierMasterPanel />
    </PmShell>
  );
}

export function PmPosters() {
  return (
    <PmShell title="Site Posters" section="posters"
      intro={<p className="text-sm text-slate-700">Generate printable posters for the site trailer — JHP cover sheet, Trench Box data, Inspection-QR for field crews. Training QR scan analytics live here too, so you can see at-a-glance how the posted QR codes are being used.</p>}>
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
      intro={<p className="text-sm text-slate-700">Auto-routing rules — when a form is submitted, this is the people who get the email. Edits are admin-only; PMs see the current rules so they can confirm who's in the loop.</p>}>
      <AutoEmailRoutingPanel />
    </PmShell>
  );
}

export function PmComplianceExport() {
  return (
    <PmShell title="Compliance Export" section="compliance-export"
      intro={<p className="text-sm text-slate-700">Pull a CSV of every safety record (Daily Reports, Inspections, Meetings, Incidents, JHPs, QA/QC) inside a date window — ready for compliance audits or insurance reviews. PM portal NEVER exposes backup/restore tools.</p>}>
      <ComplianceExportPanel hideBackupTools />
    </PmShell>
  );
}
