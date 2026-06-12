// Track 13.6F · Phase 3 — PM-2 Unified Holds (real data, real workflows).
//
// MOUNTED AT: /pm/holds (behind RequirePm — same gate as the rest of the PM portal).
//
// This page is a thin, honest aggregator over real existing hold engines:
//   • equipment_master        — Maintenance / Safety / Down / OOS
//   • operational_constraints — open / monitoring
//   • fleet_defects           — open / acknowledged (PM-impacted trucks)
//
// Source ownership preserved. Every row links to the real source
// workflow (no placeholders). Empty states are honest.
//
// Backend: GET /api/pm/command-center/holds  (Track 13.6F · Phase 3).

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import {
  PortalShell,
  StatusChip,
  Card,
  EmptyState,
  DataTable,
} from "../design-system";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const p = getPmToken();
  if (a) h["X-Admin-Token"] = a;
  if (p) h["X-PM-Token"] = p;
  return h;
}

function severityChip(sev) {
  const v = String(sev || "medium").toLowerCase();
  if (v === "high") return <StatusChip statusKey="overdue" compact label="High" />;
  if (v === "low")  return <StatusChip statusKey="verified" compact label="Low" />;
  return <StatusChip statusKey="pending_verification" compact label="Medium" />;
}

function kindLabel(kind) {
  if (kind === "equipment_hold") return "Equipment Hold";
  if (kind === "constraint") return "Operational Constraint";
  if (kind === "fleet_defect") return "Fleet Defect";
  return kind || "—";
}

function sourceLabel(source) {
  // honest source attribution — preserves source ownership.
  if (source === "equipment_master") return "Source: equipment_master";
  if (source === "operational_constraints") return "Source: operational_constraints";
  if (source === "fleet_defects") return "Source: fleet_defects";
  return `Source: ${source || "—"}`;
}

export default function PmHoldsV2() {
  const [state, setState] = useState({ loaded: false, body: null, error: null });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${API}/api/pm/command-center/holds`, { headers: authHeaders() });
        const body = r.ok ? await r.json() : null;
        if (!cancelled) setState({ loaded: true, body, error: r.ok ? null : `HTTP ${r.status}` });
      } catch (e) {
        if (!cancelled) setState({ loaded: true, body: null, error: String(e) });
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const rows = state.body?.rows || [];
  const counts = state.body?.counts || {};

  const columns = [
    {
      key: "kind",
      header: "Kind",
      render: (row) => (
        <span data-testid={`pm-holds-row-kind-${row.id}`} style={{ fontWeight: 600, color: "var(--ink-strong)" }}>
          {kindLabel(row.kind)}
        </span>
      ),
    },
    {
      key: "title",
      header: "Title",
      render: (row) => (
        <div>
          <div style={{ fontWeight: 600, color: "var(--ink-strong)" }}>{row.title || "—"}</div>
          <div style={{ fontSize: 11, color: "var(--ink-soft)" }}>{row.subtitle || ""}</div>
          <div style={{ fontSize: 10, color: "var(--ink-faint)", fontStyle: "italic", marginTop: 2 }}>
            {sourceLabel(row.source)}
          </div>
        </div>
      ),
    },
    {
      key: "severity",
      header: "Severity",
      render: (row) => severityChip(row.severity),
      width: 110,
    },
    {
      // Track 13.6H — operational-truth SLA chip (real timestamps).
      key: "sla_label",
      header: "Age",
      render: (row) => (
        row.sla_label
          ? <span data-testid={`pm-holds-sla-${row.id}`} style={{
              display: "inline-block", padding: "2px 8px",
              background: (row.age_days || 0) >= 7 ? "#fef3c7" : "#f1f5f9",
              color: (row.age_days || 0) >= 7 ? "#92400e" : "#334155",
              border: "1px solid var(--border-bold)",
              borderRadius: 999, fontSize: 11, fontWeight: 600,
              whiteSpace: "nowrap",
            }}>{row.sla_label}</span>
          : <span style={{ color: "var(--ink-faint)" }}>—</span>
      ),
      width: 130,
    },
    {
      key: "project_number",
      header: "Project",
      render: (row) => row.project_number || <span style={{ color: "var(--ink-faint)" }}>—</span>,
      width: 110,
    },
    {
      key: "age_days",
      header: "Held",
      render: (row) => `${row.age_days ?? 0}d`,
      width: 70,
      align: "right",
    },
    {
      // Already shown by the Age chip above — kept for back-compat.
      key: "destination_path",
      header: "Open",
      render: (row) => (
        <Link
          to={row.destination_path || "/pm/hub"}
          data-testid={`pm-holds-open-${row.id}`}
          title={`Source: ${row.source_engine || row.source} · ID: ${row.source_id || row.id}`}
          style={{
            display: "inline-block", padding: "4px 10px",
            background: "var(--paper-card)", color: "var(--ink-strong)",
            border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
            fontSize: 11, fontWeight: 600, textDecoration: "none", whiteSpace: "nowrap",
          }}
        >
          {row.destination_label || "Open"}
        </Link>
      ),
      width: 200,
    },
  ];

  return (
    <div data-testid="pm-holds-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole="PM Portal · Unified Holds"
        pageTitle="What is currently held up on your projects?"
        subtitle="Live aggregation of real hold engines · equipment holds · operational constraints · fleet defects. Every row links back to its source workflow."
        primaryActions={
          <div style={{ display: "flex", gap: 8 }}>
            <Link to="/pm/hub" data-testid="pm-holds-back-hub" style={{
              display: "inline-block", padding: "6px 12px", background: "var(--paper-card)",
              color: "var(--ink-strong)", border: "1px solid var(--border-bold)",
              borderRadius: "var(--radius-card)", fontSize: 12, fontWeight: 600, textDecoration: "none",
            }}>← Back to PM Hub</Link>
          </div>
        }
        lastActivity={
          <span data-testid="pm-holds-last-activity">
            {state.loaded ? (state.body ? `Refreshed ${new Date(state.body.as_of).toLocaleTimeString()}` : "Could not load") : "Loading…"}
          </span>
        }
      >
        {/* Summary tiles — REAL counts from real sources. */}
        <div
          data-testid="pm-holds-summary-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 16,
            marginBottom: 24,
          }}
        >
          <Card
            title="Equipment Holds"
            description="Maintenance Hold · Safety Hold · Down · Out of Service"
            metric={state.loaded ? (counts.equipment_holds ?? "—") : "…"}
            status={<StatusChip statusKey={counts.equipment_holds ? "pending_verification" : "verified"} compact />}
            data-testid="pm-holds-tile-equipment"
          >
            <p style={{ margin: "6px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
              Source: equipment_master
            </p>
          </Card>
          <Card
            title="Operational Constraints"
            description="Open + monitoring constraints on your projects"
            metric={state.loaded ? (counts.constraint_holds ?? "—") : "…"}
            status={<StatusChip statusKey={counts.constraint_holds ? "pending_verification" : "verified"} compact />}
            data-testid="pm-holds-tile-constraints"
          >
            <p style={{ margin: "6px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
              Source: operational_constraints
            </p>
          </Card>
          <Card
            title="Fleet Defects"
            description="Open · acknowledged defects on trucks bound to your projects"
            metric={state.loaded ? (counts.fleet_defects ?? "—") : "…"}
            status={<StatusChip statusKey={counts.fleet_defects ? "pending_verification" : "verified"} compact />}
            data-testid="pm-holds-tile-defects"
          >
            <p style={{ margin: "6px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
              Source: fleet_defects
            </p>
          </Card>
        </div>

        <DataTable
          columns={columns}
          rows={rows}
          rowKey={(r) => `${r.kind}:${r.id}`}
          loading={!state.loaded}
          empty={
            <EmptyState
              testId="pm-holds-empty"
              title="No holds on your projects."
              explanation="No equipment in hold status, no open operational constraints, and no open fleet defects on trucks bound to your projects."
              severity="good"
            />
          }
          density="regular"
        />

        <div
          data-testid="pm-holds-trace-note"
          style={{
            marginTop: 16, padding: "var(--pad-card)",
            background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
            borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12,
          }}
        >
          <strong style={{ color: "var(--ink-strong)" }}>PM-2 · Unified Holds · Track 13.6F.</strong>{" "}
          This surface aggregates only real, currently-existing hold engines (no RFIs, no Submittals).
          Every count traces to a real source · every row opens its own real workflow.
        </div>
      </PortalShell>
    </div>
  );
}
