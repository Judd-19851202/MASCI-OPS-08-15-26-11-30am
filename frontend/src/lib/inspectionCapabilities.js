// inspectionCapabilities.js — Phase STABILIZATION-FINAL · 2026-05-28.
//
// Capability-scoped rendering for the universal Job Site Safety
// Inspection detail page (`/admin/inspections/:id` and
// `/pm/inspections/:id`). Doctrine mirrors `poCapabilities.js`.
//
// Capabilities
// ------------
//   inspection.view             · see the inspection record
//   inspection.create           · file a new inspection (Foreman/Sup)
//   inspection.edit             · adjust project linkage on existing record
//   inspection.delete           · destructive · remove an inspection
//   inspection.email            · send the record via EmailReportDialog
//   inspection.print            · render / print the PDF
//   inspection.signoff          · close-out signoff (admin-only currently)
//
// Backend parity
// --------------
//   * GET  /api/inspections/:id          · admin OR PM
//   * DEL  /api/inspections/:id          · admin OR PM (gated by require_admin)
//   * POST /api/inspections (public)     · field crews submit unauthenticated
//   * Signoff hooks belong to admin only.
//
// Context lockdown
// ----------------
//   * `field-leadership` context: VIEW + PRINT + EMAIL only.
//   * `pm`     context: VIEW + EDIT + DELETE + EMAIL + PRINT.
//   * `admin`  context: full bundle including signoff.
//   * `safety` context: VIEW + PRINT + EMAIL (read-only cross-portal).
//   * `hr`     context: VIEW + PRINT + EMAIL.
//   * Unknown: VIEW + PRINT only if any portal token exists.

import { isPm } from "@/lib/pmAuth";
import { isHr } from "@/lib/hrAuth";
import { isAdmin } from "@/lib/adminAuth";
import { isLeadershipAuthed } from "@/lib/leadershipAuth";
import { isSafety as isSafetyAuthed } from "@/lib/safetyAuth";
import { getPortalContext } from "@/lib/portalContext";

const CAPS = [
  "inspection.view",
  "inspection.create",
  "inspection.edit",
  "inspection.delete",
  "inspection.email",
  "inspection.print",
  "inspection.signoff",
];

function _allOff() {
  return Object.fromEntries(CAPS.map((k) => [k, false]));
}

export function getInspectionCapabilities() {
  const ctx = getPortalContext();
  const hasPm = isPm();
  const hasHr = isHr();
  const hasAdmin = isAdmin();
  const hasSafety = isSafetyAuthed();
  const hasLeadership = isLeadershipAuthed();
  const caps = _allOff();

  if (ctx === "field-leadership") {
    if (hasLeadership || hasPm || hasHr || hasAdmin || hasSafety) {
      caps["inspection.view"] = true;
      caps["inspection.print"] = true;
      caps["inspection.email"] = true;
    }
    return caps;
  }

  if (ctx === "pm" && (hasPm || hasAdmin)) {
    caps["inspection.view"] = true;
    caps["inspection.create"] = true;
    caps["inspection.edit"] = true;
    caps["inspection.delete"] = true;
    caps["inspection.email"] = true;
    caps["inspection.print"] = true;
    return caps;
  }

  if (ctx === "safety" && (hasSafety || hasAdmin)) {
    caps["inspection.view"] = true;
    caps["inspection.email"] = true;
    caps["inspection.print"] = true;
    return caps;
  }

  if (ctx === "hr" && (hasHr || hasAdmin)) {
    caps["inspection.view"] = true;
    caps["inspection.print"] = true;
    caps["inspection.email"] = true;
    return caps;
  }

  if (ctx === "admin" && hasAdmin) {
    caps["inspection.view"] = true;
    caps["inspection.create"] = true;
    caps["inspection.edit"] = true;
    caps["inspection.delete"] = true;
    caps["inspection.email"] = true;
    caps["inspection.print"] = true;
    caps["inspection.signoff"] = true;
    return caps;
  }

  // Conservative fallback.
  if (hasPm || hasHr || hasAdmin || hasSafety) {
    caps["inspection.view"] = true;
    caps["inspection.print"] = true;
  }
  return caps;
}

// Test seam.
export const __TESTING__ = { CAPS };
