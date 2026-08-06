// constraintCapabilities.js — Phase V-Prelude · Wave 1 · 2026-05-28.
//
// Capability-scoped rendering for Operational Constraints. Mirrors the
// `poCapabilities.js` and `safetyCapabilities.js` doctrine VERBATIM:
//
//   * Portal context is the FIRST gate (NOT token presence).
//   * Backend is the source of truth — UI capabilities only decide
//     what to RENDER, never what's authorised.
//   * Field Leadership context is locked down to a calm submitter
//     bundle (view + create + chronology note) — never edit/resolve
//     a constraint that's not theirs from the FL portal.
//
// Capabilities
// ------------
//   constraint.view              · see list + detail
//   constraint.create            · file a new constraint
//   constraint.edit              · adjust fields on an open constraint
//   constraint.resolve           · mark resolved with a 1-line note
//   constraint.chronology_note   · append an operator note to chronology
//   constraint.link_photo        · attach photo evidence (operational_links)
//   constraint.read_cross_portal · read across portals (admin/exec lens)

import { isPm } from "@/lib/pmAuth";
import { isHr } from "@/lib/hrAuth";
import { isAdmin } from "@/lib/adminAuth";
import { isLeadershipAuthed } from "@/lib/leadershipAuth";
import { isSafety as isSafetyAuthed } from "@/lib/safetyAuth";
import { isFl } from "@/lib/flAuth";
import { getPortalContext, setPortalContext } from "@/lib/portalContext";

const CAPS = [
  "constraint.view",
  "constraint.create",
  "constraint.edit",
  "constraint.resolve",
  "constraint.chronology_note",
  "constraint.link_photo",
  "constraint.read_cross_portal",
];

function _allOff() {
  return Object.fromEntries(CAPS.map((k) => [k, false]));
}

export function getConstraintCapabilities() {
  const ctx = getPortalContext();
  const hasPm = isPm();
  const hasHr = isHr();
  const hasAdmin = isAdmin();
  const hasSafety = isSafetyAuthed();
  const hasLeadership = isLeadershipAuthed();
  const hasFl = typeof isFl === "function" ? isFl() : false;
  const caps = _allOff();

  // ── Field Leadership lockdown ──────────────────────────────────────
  // FL operators see + file constraints, drop in chronology notes,
  // attach photo evidence. They DO NOT edit fields or resolve other
  // operators' constraints — that stays with PM / Safety / Admin.
  if (ctx === "field-leadership") {
    if (hasFl || hasLeadership || hasAdmin) {
      caps["constraint.view"] = true;
      caps["constraint.create"] = true;
      caps["constraint.chronology_note"] = true;
      caps["constraint.link_photo"] = true;
    }
    return caps;
  }

  // PM context — full write surface for their own jobs (backend
  // applies project scoping).
  if (ctx === "pm" && (hasPm || hasAdmin)) {
    caps["constraint.view"] = true;
    caps["constraint.create"] = true;
    caps["constraint.edit"] = true;
    caps["constraint.resolve"] = true;
    caps["constraint.chronology_note"] = true;
    caps["constraint.link_photo"] = true;
    return caps;
  }

  // Safety context — safety-owned constraints (QC fails, FAA, JHA).
  if (ctx === "safety" && (hasSafety || hasAdmin)) {
    caps["constraint.view"] = true;
    caps["constraint.create"] = true;
    caps["constraint.edit"] = true;
    caps["constraint.resolve"] = true;
    caps["constraint.chronology_note"] = true;
    caps["constraint.link_photo"] = true;
    return caps;
  }

  // HR context — view-only (HR doesn't manage field constraints).
  if (ctx === "hr" && (hasHr || hasAdmin)) {
    caps["constraint.view"] = true;
    caps["constraint.read_cross_portal"] = true;
    return caps;
  }

  // Admin context — full bundle, all portals.
  if (ctx === "admin" && hasAdmin) {
    caps["constraint.view"] = true;
    caps["constraint.create"] = true;
    caps["constraint.edit"] = true;
    caps["constraint.resolve"] = true;
    caps["constraint.chronology_note"] = true;
    caps["constraint.link_photo"] = true;
    caps["constraint.read_cross_portal"] = true;
    return caps;
  }

  // Unknown / deep-link fallback — conservative VIEW only.
  if (hasPm || hasHr || hasAdmin || hasSafety || hasLeadership || hasFl) {
    caps["constraint.view"] = true;
  }
  return caps;
}

export function ensureConstraintPortalContext() {
  const ctx = getPortalContext();
  if (ctx && ctx !== "unknown" && ctx !== "public") return ctx;
  if (isAdmin()) {
    setPortalContext("admin");
    return "admin";
  }
  if (isPm()) {
    setPortalContext("pm");
    return "pm";
  }
  if (isSafetyAuthed()) {
    setPortalContext("safety");
    return "safety";
  }
  if (typeof isFl === "function" && isFl()) {
    setPortalContext("field-leadership");
    return "field-leadership";
  }
  if (isHr()) {
    setPortalContext("hr");
    return "hr";
  }
  return ctx;
}

// Test seam.
export const __TESTING__ = { CAPS };
