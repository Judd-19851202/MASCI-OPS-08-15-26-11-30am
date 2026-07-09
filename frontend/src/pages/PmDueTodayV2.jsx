// Track 13.6F · Phase 4 — PM-3 Due Today (real deadlines, real workflows).
//
// MOUNTED AT: /pm/due-today (behind RequirePm).
//
// Aggregates only items with REAL existing deadlines whose due/expiration
// date matches today (UTC) from real engines:
//   • corrective_actions.due_date == today  →  /pm/incidents?tab=capas
//   • daily_reports.report_date == today
//       AND lifecycle_state == 'PENDING_REVIEW'  →  /pm/daily
//
// No invented urgency. No invented dates. Empty states are honest.
//
// Backend: GET /api/pm/command-center/due-today  (Track 13.6F · Phase 4).

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
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const p = getPmToken();
  if (a) h["X-Admin-Token"] = a;
  if (p) h["X-PM-Token"] = p;
  return h;
}

function kindLabel(kind) {
  if (kind === "capa") return "CAPA";
  if (kind === "daily_report_pending") return "Daily Report";
  return kind || "—";
}

function sourceLabel(source) {
  if (source === "corrective_actions") return "Source: corrective_actions";
  if (source === "daily_reports") return "Source: daily_reports";
  return `Source: ${source || "—"}`;
}

export default function PmDueTodayV2() {
  const [state, setState] = useState({ loaded: false, body: null, error: null });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${API}/api/pm/command-center/due-today`, { headers: authHeaders() });
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
  const asOfDate = state.body?.as_of_date || "";

  const columns = [
    {
      key: "kind",
      header: "Kind",
      render: (row) => (
        <span data-testid={`pm-due-row-kind-${row.id}`} style={{ fontWeight: 600, color: "var(--ink-strong)" }}>
          {kindLabel(row.kind)}
        </span>
      ),
      width: 130,
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
      key: "due_date",
      header: "Due",
      render: (row) => row.due_date || <span style={{ color: "var(--ink-faint)" }}>—</span>,
      width: 110,
    },
    {
      // Track 13.6H — operational-truth SLA chip.
      key: "sla_label",
      header: "When",
      render: (row) => (
        row.sla_label
          ? <span data-testid={`pm-due-sla-${row.id}`} style={{
              display: "inline-block", padding: "2px 8px",
              background: row.sla_label.startsWith("Overdue") ? "#fee2e2" : "#fef3c7",
              color: row.sla_label.startsWith("Overdue") ? "#991b1b" : "#92400e",
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
      key: "status",
      header: "Status",
      render: (row) => <StatusChip statusKey="pending_verification" compact label={row.status || "open"} />,
      width: 120,
    },
    {
      key: "destination_path",
      header: "Open",
      render: (row) => (
        <Link
          to={row.destination_path || "/pm/hub"}
          data-testid={`pm-due-open-${row.id}`}
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
      width: 220,
    },
  ];

  return (
    <div data-testid="pm-due-today-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole="PM Portal · Due Today"
        pageTitle={`What is due today on your projects?${asOfDate ? ` · ${asOfDate}` : ""}`}
        subtitle="Live aggregation of real deadlines · CAPAs due today + daily reports awaiting PM verify for today. Every count traces to a real source field."
        primaryActions={
          <div style={{ display: "flex", gap: 8 }}>
            <Link to="/pm/hub" data-testid="pm-due-back-hub" style={{
              display: "inline-block", padding: "6px 12px", background: "var(--paper-card)",
              color: "var(--ink-strong)", border: "1px solid var(--border-bold)",
              borderRadius: "var(--radius-card)", fontSize: 12, fontWeight: 600, textDecoration: "none",
            }}>← Back to PM Hub</Link>
          </div>
        }
        lastActivity={
          <span data-testid="pm-due-last-activity">
            {state.loaded ? (state.body ? `Refreshed ${formatPlatformTimeOnly(state.body.as_of)}` : "Could not load") : "Loading…"}
          </span>
        }
      >
        <div
          data-testid="pm-due-summary-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 16,
            marginBottom: 24,
          }}
        >
          <Card
            title="CAPAs Due Today"
            description="Corrective actions with due_date == today (not closed)"
            metric={state.loaded ? (counts.capas_due_today ?? "—") : "…"}
            status={<StatusChip statusKey={counts.capas_due_today ? "pending_verification" : "verified"} compact />}
            data-testid="pm-due-tile-capas"
          >
            <p style={{ margin: "6px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
              Source: corrective_actions.due_date
            </p>
          </Card>
          <Card
            title="Daily Reports Pending Review (Today)"
            description="Foreman-submitted reports for today awaiting PM verify"
            metric={state.loaded ? (counts.daily_reports_pending_today ?? "—") : "…"}
            status={<StatusChip statusKey={counts.daily_reports_pending_today ? "pending_verification" : "verified"} compact />}
            data-testid="pm-due-tile-daily"
          >
            <p style={{ margin: "6px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
              Source: daily_reports.lifecycle_state
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
              testId="pm-due-empty"
              title="Nothing due today."
              explanation="No CAPAs are dated due today and no daily reports for today are awaiting your verify."
              severity="good"
            />
          }
          density="regular"
        />

        <div
          data-testid="pm-due-trace-note"
          style={{
            marginTop: 16, padding: "var(--pad-card)",
            background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
            borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12,
          }}
        >
          <strong style={{ color: "var(--ink-strong)" }}>Due Today · PM.</strong>{" "}
          Only items whose real-source deadline matches today are listed.
          No invented urgency · empty state is honest · every row opens its own real workflow.
        </div>
      </PortalShell>
    </div>
  );
}
