// PM section pages — each is a thin wrapper over PmShell + read-only views
// of the shared masters PMs are allowed to see.
//
// iter437 P0 Auth Routing Hardening (2026-02):
//   Shared admin panels that hardcode `/api/admin/*` endpoints (Job master,
//   Equipment status board, Auto-email routing, Compliance export, Training
//   stats) are NOT mounted here anymore — they require an Admin token by
//   contract and were emitting "Admin login required" toasts for PMs.
//   See /app/memory/PORTAL_AUTH_TOKEN_AUDIT.md for the full matrix.
//
//   PMs retain read-only access to: Employees · Suppliers · Equipment
//   Master · Equipment Parts · Site Posters · Compliance Export landing.
//   Each panel below either uses a public endpoint or is rendered with
//   `readOnly` so it never fires a request the PM token cannot satisfy.
//
// (iter105 · iter437/IV-BETA.2 coaching cleanup — doctrine-compliant sublines
//  per CROSS_PORTAL_COACHING_STANDARD.md §V · ≤14 words · sentence-case ·
//  no "PMs have read-only access — edits live in…" feature-listing · no
//  forbidden "Pull" / casual verbs · ends with a period.)

import React from "react";
import PmShell from "@/components/PmShell";
import EquipmentMasterPanel from "@/components/EquipmentMasterPanel";
import EquipmentPartsPanel from "@/components/EquipmentPartsPanel";
import EmployeeMasterPanel from "@/components/EmployeeMasterPanel";
import SupplierMasterPanel from "@/components/SupplierMasterPanel";
import SitePostersPanel from "@/components/SitePostersPanel";

// Calm doctrine-compliant subline — sentence-case slate-500, ≤14 words.
const Subline = ({ children }) => (
  <p className="text-xs text-slate-500 leading-relaxed">{children}</p>
);

export function PmFleet() {
  return (
    <PmShell title="Equipment Fleet" section="fleet"
      intro={<Subline>Equipment master and per-unit parts catalog (read-only).</Subline>}>
      <EquipmentMasterPanel readOnly />
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
      <EmployeeMasterPanel readOnly />
    </PmShell>
  );
}

export function PmSuppliers() {
  return (
    <PmShell title="Suppliers" section="suppliers"
      intro={<Subline>Approved supplier roster with contacts (read-only).</Subline>}>
      <SupplierMasterPanel readOnly />
    </PmShell>
  );
}

export function PmPosters() {
  return (
    <PmShell title="Site Posters" section="posters"
      intro={<Subline>Printable JHA, trench box, and inspection QR posters for the trailer.</Subline>}>
      <SitePostersPanel />
    </PmShell>
  );
}
