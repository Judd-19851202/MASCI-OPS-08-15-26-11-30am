// capaCapabilities.js — Phase STABILIZATION-FINAL · 2026-05-28.
//
// Capability-scoped rendering for Corrective Actions (CAPAs). CAPAs
// live in the Safety domain — Safety operators create, close, and
// audit them; PM / HR / Admin get cross-portal READ visibility for
// project oversight; Field Leadership sees nothing (CAPAs are a
// safety-officer surface, not a field-foreman surface).
//
// Doctrine mirrors `poCapabilities.js` exactly.
//
// Capabilities
// ------------
//   capa.view              · see a corrective action record
//   capa.create            · open a new CAPA
//   capa.update            · update progress / due date / assignee
//   capa.close             · mark a CAPA as closed / verified
//   capa.delete            · destructive · remove a CAPA (admin only)
//   capa.assign            · re-assign owner
//   capa.cross_portal_read · read CAPAs from a non-safety portal
//
// Backend parity
// --------------
//   * /api/safety-portal/corrective-actions/*  · safety scope (write)
//   * Cross-portal reads served via existing /api/hr/* and /api/operations/*
//     read-multi-portal gates.
//
// Context lockdown
// ----------------
//   * `field-leadership`: NOTHING. CAPAs are not a field surface.
//   * `safety`:  full bundle minus delete (admin-only).
//   * `pm`:      VIEW + cross_portal_read.
//   * `hr`:      VIEW + cross_portal_read.
//   * `admin`:   full bundle.
//   * Unknown:   nothing.

import { isPm } from "@/lib/pmAuth";
import { isHr } from "@/lib/hrAuth";
import { isAdmin } from "@/lib/adminAuth";
import { isSafety as isSafetyAuthed } from "@/lib/safetyAuth";
import { getPortalContext } from "@/lib/portalContext";

const CAPS = [
  "capa.view",
  "capa.create",
  "capa.update",
  "capa.close",
  "capa.delete",
  "capa.assign",
  "capa.cross_portal_read",
];

function _allOff() {
  return Object.fromEntries(CAPS.map((k) => [k, false]));
}

export function getCapaCapabilities() {
  const ctx = getPortalContext();
  const hasPm = isPm();
  const hasHr = isHr();
  const hasAdmin = isAdmin();
  const hasSafety = isSafetyAuthed();
  const caps = _allOff();

  // Field Leadership is locked out entirely — CAPAs are not a field
  // surface. Mirrors the doctrine that approval surfaces are not
  // shown to submitters.
  if (ctx === "field-leadership") {
    return caps;
  }

  if (ctx === "safety" && (hasSafety || hasAdmin)) {
    caps["capa.view"] = true;
    caps["capa.create"] = true;
    caps["capa.update"] = true;
    caps["capa.close"] = true;
    caps["capa.assign"] = true;
    caps["capa.cross_portal_read"] = true;
    if (hasAdmin) caps["capa.delete"] = true;
    return caps;
  }

  if (ctx === "pm" && (hasPm || hasAdmin)) {
    caps["capa.view"] = true;
    caps["capa.cross_portal_read"] = true;
    return caps;
  }

  if (ctx === "hr" && (hasHr || hasAdmin)) {
    caps["capa.view"] = true;
    caps["capa.cross_portal_read"] = true;
    return caps;
  }

  if (ctx === "admin" && hasAdmin) {
    caps["capa.view"] = true;
    caps["capa.create"] = true;
    caps["capa.update"] = true;
    caps["capa.close"] = true;
    caps["capa.delete"] = true;
    caps["capa.assign"] = true;
    caps["capa.cross_portal_read"] = true;
    return caps;
  }

  return caps;
}

// Test seam.
export const __TESTING__ = { CAPS };
