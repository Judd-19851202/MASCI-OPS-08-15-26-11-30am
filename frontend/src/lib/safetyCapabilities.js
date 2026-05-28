// safetyCapabilities.js — Phase STABILIZATION-FINAL · 2026-05-28.
//
// Capability-scoped rendering for shared safety surfaces — Safety
// Meetings, Tailgates, Safety Records detail pages. Same doctrine as
// `poCapabilities.js`: portal context is the FIRST gate, token
// presence is the SECOND, backend remains the source of truth.
//
// Capabilities
// ------------
//   meeting.view              · see the safety meeting record (universal w/ token)
//   meeting.create            · file a new safety meeting / tailgate
//   meeting.edit              · adjust project linkage / dates on an existing record
//   meeting.delete            · destructive · remove a safety meeting record
//   meeting.email             · send the record via the EmailReportDialog
//   meeting.print             · render / print the PDF
//   safety.read_cross_portal  · read safety records from HR / PM read view
//
// Context lockdown
// ----------------
//   * `field-leadership` context: VIEW + PRINT + EMAIL only. Field
//     Leadership operators do NOT delete or edit safety records
//     regardless of which tokens coexist in storage.
//   * `pm` context: VIEW + EMAIL + PRINT + DELETE (backend allows PM
//     to delete records on their own jobs via `require_admin` accept).
//   * `safety` context: full capability bundle (their domain).
//   * `admin` context: full capability bundle.
//   * `hr` context: VIEW + PRINT + EMAIL + safety.read_cross_portal.
//   * Unknown context: VIEW + PRINT only — conservative fallback.

import { isPm } from "@/lib/pmAuth";
import { isHr } from "@/lib/hrAuth";
import { isAdmin } from "@/lib/adminAuth";
import { isLeadershipAuthed } from "@/lib/leadershipAuth";
import { isSafety as isSafetyAuthed } from "@/lib/safetyAuth";
import { getPortalContext } from "@/lib/portalContext";

const CAPS = [
  "meeting.view",
  "meeting.create",
  "meeting.edit",
  "meeting.delete",
  "meeting.email",
  "meeting.print",
  "safety.read_cross_portal",
];

function _allOff() {
  return Object.fromEntries(CAPS.map((k) => [k, false]));
}

export function getSafetyCapabilities() {
  const ctx = getPortalContext();
  const hasPm = isPm();
  const hasHr = isHr();
  const hasAdmin = isAdmin();
  const hasSafety = isSafetyAuthed();
  const hasLeadership = isLeadershipAuthed();
  const caps = _allOff();

  // Field Leadership lockdown — view-only on safety records.
  if (ctx === "field-leadership") {
    if (hasLeadership || hasPm || hasHr || hasAdmin || hasSafety) {
      caps["meeting.view"] = true;
      caps["meeting.print"] = true;
      caps["meeting.email"] = true;
    }
    return caps;
  }

  // PM context.
  if (ctx === "pm" && (hasPm || hasAdmin)) {
    caps["meeting.view"] = true;
    caps["meeting.create"] = true;
    caps["meeting.edit"] = true;
    caps["meeting.delete"] = true;
    caps["meeting.email"] = true;
    caps["meeting.print"] = true;
    return caps;
  }

  // HR context — cross-portal read view (writes stay safety-only).
  if (ctx === "hr" && (hasHr || hasAdmin)) {
    caps["meeting.view"] = true;
    caps["meeting.print"] = true;
    caps["meeting.email"] = true;
    caps["safety.read_cross_portal"] = true;
    return caps;
  }

  // Safety context — full domain.
  if (ctx === "safety" && (hasSafety || hasAdmin)) {
    caps["meeting.view"] = true;
    caps["meeting.create"] = true;
    caps["meeting.edit"] = true;
    caps["meeting.delete"] = true;
    caps["meeting.email"] = true;
    caps["meeting.print"] = true;
    caps["safety.read_cross_portal"] = true;
    return caps;
  }

  // Admin context — full bundle.
  if (ctx === "admin" && hasAdmin) {
    caps["meeting.view"] = true;
    caps["meeting.create"] = true;
    caps["meeting.edit"] = true;
    caps["meeting.delete"] = true;
    caps["meeting.email"] = true;
    caps["meeting.print"] = true;
    caps["safety.read_cross_portal"] = true;
    return caps;
  }

  // Unknown / unauthenticated context — conservative.
  if (hasPm || hasHr || hasAdmin || hasSafety) {
    caps["meeting.view"] = true;
    caps["meeting.print"] = true;
  }
  return caps;
}

// Test seam.
export const __TESTING__ = { CAPS };
