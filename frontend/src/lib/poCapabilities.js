// poCapabilities.js — TRUST-PO-1 · 2026-05-28.
//
// Capability-scoped rendering for the universal PO Requests page. The
// page (`/po-requests`) is shared across portals; the SAME React tree
// renders for Field Leadership, PM, HR, Admin, and Super Admin. The
// component MUST decide what to show by consulting EXPLICIT capability
// flags, not by checking which token happens to live in browser
// storage.
//
// Doctrine
// --------
//   * Each capability is an explicit, named permission for a UI block.
//   * Capabilities are computed from (portal context) × (token presence).
//   * Portal context is the FIRST gate: when context = "field-leadership"
//     every approver capability is FORCED OFF — even if an admin token
//     happens to coexist in storage (Super Admin testing scenario).
//   * Backend remains the source of truth for actual authorisation —
//     the capabilities object ONLY decides what to RENDER. A user
//     who somehow saw an approval button would still be 403'd by the
//     backend. UI capability gating is a TRUST surface, not a SECURITY
//     surface.
//
// Names mirror the backend role model:
//   po.request.create           · submit a PO request
//   po.request.view             · see the universal list / drawer
//   po.request.receipt_upload   · upload a receipt against an approved PO
//   po.request.respond_clarify  · respond when a PO is in Clarification Needed
//   po.approve                  · approver action: Approve
//   po.reject                   · approver action: Reject
//   po.clarify                  · approver action: Request clarification
//   po.issue_number             · assign a manual official PO number on approval
//   po.set_approved_amount      · enter approved amount on approval
//   po.close                    · close an approved PO
//   po.cancel                   · cancel a PO mid-workflow

import { isPm } from "@/lib/pmAuth";
import { isHr } from "@/lib/hrAuth";
import { isAdmin } from "@/lib/adminAuth";
import { isLeadershipAuthed } from "@/lib/leadershipAuth";
import { getPortalContext } from "@/lib/portalContext";

const APPROVER_CAPS = [
  "po.approve",
  "po.reject",
  "po.clarify",
  "po.issue_number",
  "po.set_approved_amount",
  "po.close",
  "po.cancel",
];

const SUBMITTER_CAPS = [
  "po.request.create",
  "po.request.view",
  "po.request.receipt_upload",
  "po.request.respond_clarify",
];

function _allOff() {
  return Object.fromEntries([...APPROVER_CAPS, ...SUBMITTER_CAPS].map((k) => [k, false]));
}

/**
 * Compute the capability bundle for the current operator + portal.
 *
 * Returns a flat `{ "po.approve": bool, ... }` object. Components
 * read it via `caps["po.approve"]` (preferred — keeps the lookup
 * grep-able for the audit trail).
 */
export function getPoCapabilities() {
  const ctx = getPortalContext();
  const hasPm = isPm();
  const hasHr = isHr();
  const hasAdmin = isAdmin();
  const hasLeadership = isLeadershipAuthed();

  const caps = _allOff();

  // ── Field Leadership context lockdown ─────────────────────────────
  // Capability-scoped doctrine: when the operator is INSIDE the Field
  // Leadership portal, approver controls are FORCED OFF regardless of
  // any other token in storage. This is the surgical fix for the
  // "Super Admin pollutes FL UX" trust failure.
  if (ctx === "field-leadership") {
    // Submitter caps — Field Leadership is the primary submitter.
    caps["po.request.create"] = true;
    caps["po.request.view"] = true;
    caps["po.request.receipt_upload"] = true;
    caps["po.request.respond_clarify"] = true;
    return caps;
  }

  // ── Approver contexts ────────────────────────────────────────────
  // PM / HR / Admin portal contexts grant approver capabilities to
  // whichever tokens the operator holds. The capability gate aligns
  // with the backend `_can_approve` allowlist (pm, hr, admin).
  const canApprove = hasPm || hasHr || hasAdmin;
  if (canApprove && (ctx === "pm" || ctx === "hr" || ctx === "admin")) {
    caps["po.approve"] = true;
    caps["po.reject"] = true;
    caps["po.clarify"] = true;
    caps["po.issue_number"] = true;
    caps["po.set_approved_amount"] = true;
    // Close + cancel are admin-only on the current backend.
    caps["po.close"] = hasAdmin && ctx === "admin";
    caps["po.cancel"] = hasAdmin && ctx === "admin";
  }

  // Submitter caps are universal for any authenticated portal context.
  if (hasPm || hasHr || hasAdmin || hasLeadership) {
    caps["po.request.create"] = true;
    caps["po.request.view"] = true;
    caps["po.request.receipt_upload"] = true;
    caps["po.request.respond_clarify"] = true;
  }

  // ── Unknown context fallback ─────────────────────────────────────
  // First-load before any hub has mounted (deep link to /po-requests).
  // Conservative posture: grant submitter caps if a token exists, but
  // do NOT grant approver caps until the user demonstrably enters an
  // approver portal hub.
  return caps;
}

// Test-only seam.
export const __TESTING__ = { APPROVER_CAPS, SUBMITTER_CAPS };
