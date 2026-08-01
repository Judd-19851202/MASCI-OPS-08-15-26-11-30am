// TRACK 25.01 · Admin Operating System (AOS) — legacy route registry.
//
// Phase B of the AOS rollout. Every admin surface that was consolidated
// into the Operations Control Center (or otherwise renamed to a canonical
// destination) is listed here.
//
// Contract:
//   - The legacy route STILL RENDERS its original page (zero routes
//     deleted in Phase B). A LegacyMovedBanner is prepended so the
//     operator sees exactly where the canonical version lives.
//   - `canonical` is either an absolute app path (e.g.
//     "/admin/operations-control") or an OCC deep-link with an
//     `?highlight=<op-id>` fragment so the target card scrolls into
//     view and pulses.
//   - `reason` is human-first — no engineering terminology. It reads
//     as a subtitle explaining WHY the move helps the operator.
//   - `occOperationId` (optional) is the OCC operation this page's
//     functionality now lives under. Tests use it to prove parity.
//
// If you add a route to this map, also add a test row to
// backend/tests/test_track_25_01_legacy_redirects.py.

export const LEGACY_MOVED_MAP = {
  // ── Platform maintenance (consolidated into OCC) ────────────────
  "/admin/system": {
    canonical: "/admin/operations-control?highlight=storage.audit",
    canonicalTitle: "Operations Control Center · Storage & Backups",
    reason:
      "System & Backups now live inside the Operations Control Center " +
      "alongside every other maintenance action, with dry-run previews " +
      "and an immutable audit trail.",
    occOperationId: "storage.audit",
  },
  "/admin/system-health": {
    canonical: "/admin/operations-control?highlight=health.system_overview",
    canonicalTitle: "Operations Control Center · System Health",
    reason:
      "One red / yellow / green view of disk, database, AI, email, and " +
      "delivery — refreshed on demand and viewable without shell access.",
    occOperationId: "health.system_overview",
  },
  "/admin/operations-dashboard": {
    canonical: "/admin/operations-control?highlight=integrations.probe_all",
    canonicalTitle: "Operations Control Center · Integrations",
    reason:
      "All third-party integration checks (Motive, MaintainX, Resend, " +
      "Cloudflare R2, Emergent LLM) share one home now.",
    occOperationId: "integrations.probe_all",
  },
  "/admin/integration-truth": {
    canonical: "/admin/operations-control?highlight=integrations.probe_all",
    canonicalTitle: "Operations Control Center · Integrations",
    reason:
      "Provider posture, key configuration, and live health probes have " +
      "moved into the Operations Control Center as a single card.",
    occOperationId: "integrations.probe_all",
  },
  "/admin/deploy-readiness": {
    canonical: "/admin/operations-control?highlight=deploy.readiness_check",
    canonicalTitle: "Operations Control Center · Deploy Readiness",
    reason:
      "The pre-deploy checklist now runs from Operations Control Center " +
      "so you see it next to backups, integrations, and system health.",
    occOperationId: "deploy.readiness_check",
  },
  "/admin/deploy-recovery": {
    canonical: "/admin/operations-control?highlight=deploy.recovery_playbook",
    canonicalTitle: "Operations Control Center · Recovery Playbook",
    reason:
      "The recovery playbook is now one click from every other " +
      "operational check, with the latest local backup timestamp " +
      "surfaced in-line.",
    occOperationId: "deploy.recovery_playbook",
  },
  "/admin/recovery": {
    canonical: "/admin/operations-control?highlight=deploy.recovery_playbook",
    canonicalTitle: "Operations Control Center · Recovery Playbook",
    reason:
      "Recovery actions have moved into the Operations Control Center. " +
      "The live recovery stream remains available as a deep-dive tool.",
    occOperationId: "deploy.recovery_playbook",
  },
  "/admin/recovery-stream": {
    canonical: "/admin/operations-control?highlight=deploy.recovery_playbook",
    canonicalTitle: "Operations Control Center · Recovery Playbook",
    reason:
      "The live recovery stream is a deep-dive tool. The canonical home " +
      "for recovery decisions is the Operations Control Center.",
    occOperationId: "deploy.recovery_playbook",
  },
};

// ── Public helpers ──────────────────────────────────────────────────

export function isLegacyMovedRoute(pathname) {
  if (!pathname) return false;
  return Object.prototype.hasOwnProperty.call(LEGACY_MOVED_MAP, pathname);
}

export function lookupLegacyRoute(pathname) {
  if (!pathname) return null;
  return LEGACY_MOVED_MAP[pathname] || null;
}

export function listLegacyRoutes() {
  return Object.keys(LEGACY_MOVED_MAP);
}
