/* eslint-env jest */
/* global describe, test, expect, jest */
// TD-0007 — Maintenance domain mapping truth.
//
// Live production evidence (mascidocs.com, read-only) — 16 registered ops:
//   health: health.system_overview(warning), deploy.readiness_check(warning),
//           deploy.recovery_playbook(warning), integrations.probe_all(healthy)
//   queues: queues.scheduler_runs(healthy)
//   storage: storage.audit(warning), storage.safe_cleanup(-), storage.r2_migration(-)
//   governance: governance.employee_link_backfill(warning), governance.issue_missing_ppe(warning)
//   r2: r2.health(healthy) · backups: backups.health(warning)
//   daily_reports: daily_reports.health(healthy) · ai: ai.health(healthy)
//   email: email.health(healthy) · security: security.posture(healthy)
//
// Defects proven:
//   A) "Deployment Maintenance" filtered category "deployment" — a value that
//      does NOT exist in OperationCategory (deploy ops are category "health"),
//      so it always rendered false UNKNOWN.
//   B) Governance maintenance ops (2 warnings) had no card => invisible.

jest.mock("lucide-react", () => new Proxy({}, { get: () => () => null }));
jest.mock("@/components/admin/trust/DomainLandingShell", () => ({ __esModule: true, default: () => null }));

import { matchMaintenanceOps } from "../AdminMaintenance";

function op(id, category, status) {
  return { id, category, status_snapshot: status ? { status } : {} };
}

const OPS = [
  op("health.system_overview", "health", "warning"),
  op("deploy.readiness_check", "health", "warning"),
  op("deploy.recovery_playbook", "health", "warning"),
  op("integrations.probe_all", "health", "healthy"),
  op("queues.scheduler_runs", "queues", "healthy"),
  op("storage.audit", "storage", "warning"),
  op("storage.safe_cleanup", "storage", null),
  op("storage.r2_migration", "storage", null),
  op("governance.employee_link_backfill", "governance", "warning"),
  op("governance.issue_missing_ppe", "governance", "warning"),
  op("r2.health", "r2", "healthy"),
  op("backups.health", "backups", "warning"),
  op("daily_reports.health", "daily_reports", "healthy"),
  op("ai.health", "ai", "healthy"),
  op("email.health", "email", "healthy"),
  op("security.posture", "security", "healthy"),
];

const probes = { occ: { ok: true, body: { operations: OPS } } };

test("Deployment Maintenance matches deploy.* ops and is NOT unknown", () => {
  const r = matchMaintenanceOps(probes, { idPrefixes: ["deploy."] });
  expect(r.status).toBe("yellow");
  expect(r.summary).toMatch(/2 operation\(s\) · 0 critical · 2 attention/);
  expect(r.status).not.toBe("unknown");
});

test("Health Maintenance excludes deploy.* to avoid double counting", () => {
  const r = matchMaintenanceOps(probes, { categories: ["health"], excludePrefixes: ["deploy."] });
  // system_overview(warning) + integrations.probe_all(healthy)
  expect(r.summary).toMatch(/2 operation\(s\) · 0 critical · 1 attention/);
});

test("Governance Maintenance surfaces the previously-orphaned governance ops", () => {
  const r = matchMaintenanceOps(probes, { categories: ["governance"] });
  expect(r.summary).toMatch(/2 operation\(s\) · 0 critical · 2 attention/);
  expect(r.status).toBe("yellow");
});

test("every one of the 16 ops is covered by exactly one card predicate", () => {
  const cards = [
    { categories: ["storage"] },
    { categories: ["backups"] },
    { categories: ["r2"] },
    { categories: ["email"] },
    { categories: ["ai"] },
    { categories: ["daily_reports"] },
    { categories: ["security"] },
    { idPrefixes: ["deploy."] },
    { categories: ["health"], excludePrefixes: ["deploy."] },
    { categories: ["governance"] },
    { categories: ["queues"] },
  ];
  const counts = {};
  for (const c of cards) {
    const r = matchMaintenanceOps(probes, c);
    for (const row of r.evidence.operations_summary) {
      counts[row.id] = (counts[row.id] || 0) + 1;
    }
  }
  for (const o of OPS) {
    expect(counts[o.id]).toBe(1); // present exactly once — no orphan, no double count
  }
});

test("unreachable OCC probe yields honest unknown", () => {
  const r = matchMaintenanceOps({ occ: { ok: false, error: "timeout" } }, { idPrefixes: ["deploy."] });
  expect(r.status).toBe("unknown");
});
