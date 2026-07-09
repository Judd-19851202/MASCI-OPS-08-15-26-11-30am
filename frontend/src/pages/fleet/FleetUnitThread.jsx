// Track 19.55 · Universal Operational Threads Foundation.
//
// FLEET UNIT THREAD — PILOT.
//
// Route: /fleet/unit/:unit_number
//
// This page is the pilot implementation of the Universal Operational
// Thread doctrine. It composes the 10-section shell
// (`OperationalThreadPage`) with Fleet-Unit-specific data pulled from
// endpoints that ALREADY EXIST:
//
//   • GET /api/assets/{unit_number}/timeline   — Track 13.26 backbone
//     (the certified single source of truth for unit timelines).
//   • GET /api/operational-intelligence/summary — filter to
//     fleet_intelligence for Section 8 + Section 3 guidance card.
//
// Zero new backend. Zero new score model. Zero duplicate timeline
// framework. Operational Health is computed client-side from the
// backbone events with an explanatory statement (mandate: "Never
// summarise with numbers alone").

import React, { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import OperationalThreadPage from "@/components/operational_intelligence/OperationalThreadPage";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}

async function _get(path) {
  try {
    const r = await fetch(`${API}${path}`, { headers: authHeaders() });
    const body = r.ok ? await r.json().catch(() => null) : null;
    return { ok: r.ok, status: r.status, body };
  } catch {
    return { ok: false, status: 0, body: null };
  }
}

// Map a Track 13.26 backbone event → OperationalThread event schema.
const BACKBONE_KIND = {
  preop: "inspection",
  dvir: "inspection",
  defect: "safety",
  repair: "repair",
  oos: "safety",
  assignment: "assignment",
  transfer: "assignment",
  photo: "photo",
  document: "history",
  po: "po",
  incident: "incident",
};

const BACKBONE_LABEL = {
  "preop|submitted": "Pre-Op submitted",
  "preop|failed": "Pre-Op needs review",
  "dvir|submitted": "DVIR submitted",
  "dvir|failed": "DVIR needs review",
  "defect|opened": "Defect opened",
  "defect|assigned": "Repair assigned",
  "defect|accepted": "Mechanic accepted",
  "defect|acknowledged": "Defect acknowledged",
  "defect|repaired": "Defect repaired",
  "repair|started": "Repair started",
  "repair|completed": "Repair complete",
  "repair|manager_reviewed": "Manager reviewed",
  "oos|preop": "Unit out of service · Pre-Op",
  "oos|dvir": "Unit out of service · DVIR",
  "oos|cleared": "Unit returned to service",
};

function eventLabel(ev) {
  const key = `${ev.event_type}|${ev.subtype || ""}`;
  return BACKBONE_LABEL[key] || `${ev.event_type}${ev.subtype ? " · " + ev.subtype : ""}`;
}

function mapBackboneToTimeline(events) {
  return (events || []).map((e) => ({
    id: e.event_id,
    kind: BACKBONE_KIND[e.event_type] || "other",
    at: e.timestamp,
    title: eventLabel(e),
    summary: e.actor_name ? `by ${e.actor_name}${e.actor_role ? ` (${e.actor_role})` : ""}` : null,
    deep_link: e.related_work_order_id ? `/shop/units/${encodeURIComponent(e.unit_number || "")}/history` : null,
  }));
}

// Compute Operational Health from backbone events. Explanatory: the
// UI shows both the tier AND a plain-English "why" list.
function deriveHealth(events) {
  const openOos = events.some((e) => e.event_type === "oos" && e.subtype !== "cleared" && !events.some(x => x.event_type === "oos" && x.subtype === "cleared" && x.timestamp > e.timestamp));
  const openDefects = events.some((e) => e.event_type === "defect" && (e.subtype === "opened" || e.subtype === "acknowledged"));
  const recentFailure = events.some((e) => ["preop|failed", "dvir|failed"].includes(`${e.event_type}|${e.subtype || ""}`));

  const reasons = [];
  if (openOos) reasons.push("Currently out of service.");
  if (openDefects) reasons.push("Open defect on record.");
  if (recentFailure) reasons.push("Recent inspection failure.");

  let tier = "Good";
  if (openOos) tier = "Critical";
  else if (openDefects || recentFailure) tier = "Attention Needed";
  else if (events.length === 0) tier = "Good";

  if (!openOos && !openDefects && !recentFailure) {
    reasons.push("No safety holds on record.");
    reasons.push("No active defects.");
    reasons.push("No recent inspection failures.");
  }
  return { tier, reasons };
}

// Assemble the attention list from open backbone signals.
function deriveAttention(events, unitNumber) {
  const items = [];
  const openOos = events.find((e) => e.event_type === "oos" && e.subtype !== "cleared");
  if (openOos) {
    items.push({
      severity: "CRITICAL",
      label: `Unit ${unitNumber} is out of service`,
      why: `Triggered ${openOos.subtype || "OOS"} on ${openOos.timestamp || "unknown date"}.`,
      owner: "Shop Manager",
      due: "Today",
      deep_link: `/shop/units/${encodeURIComponent(unitNumber)}/history`,
    });
  }
  const openDefects = events.filter((e) => e.event_type === "defect" && (e.subtype === "opened" || e.subtype === "acknowledged"));
  openDefects.slice(0, 3).forEach((d) => {
    items.push({
      severity: "HIGH",
      label: `Open defect · ${d.subtype === "opened" ? "not yet acknowledged" : "acknowledged, awaiting repair"}`,
      why: "Blocks unit availability until repaired.",
      owner: "Shop Manager",
      deep_link: `/shop/units/${encodeURIComponent(unitNumber)}/history`,
    });
  });
  const recentFailures = events.filter((e) => ["preop|failed", "dvir|failed"].includes(`${e.event_type}|${e.subtype || ""}`));
  if (recentFailures.length > 0) {
    items.push({
      severity: "MEDIUM",
      label: `${recentFailures.length} inspection failure${recentFailures.length === 1 ? "" : "s"} on record`,
      why: "Review with the mechanic to confirm root cause.",
      owner: "Mechanic",
      deep_link: `/shop/units/${encodeURIComponent(unitNumber)}/history`,
    });
  }
  return items;
}

// Universal action queue (max 5) — extracted from live events.
function deriveActionQueue(events, unitNumber) {
  const q = [];
  const openOos = events.find((e) => e.event_type === "oos" && e.subtype !== "cleared");
  if (openOos) q.push({
    label: "Clear the OOS state (repair + manager review + RTS).",
    deep_link: `/shop/units/${encodeURIComponent(unitNumber)}/history`,
  });
  const openDefects = events.filter((e) => e.event_type === "defect" && (e.subtype === "opened" || e.subtype === "acknowledged"));
  if (openDefects.length > 0) q.push({
    label: `Assign or complete ${openDefects.length} open defect${openDefects.length === 1 ? "" : "s"}.`,
    deep_link: `/shop/units/${encodeURIComponent(unitNumber)}/history`,
  });
  const failed = events.filter((e) => ["preop|failed", "dvir|failed"].includes(`${e.event_type}|${e.subtype || ""}`));
  if (failed.length > 0) q.push({
    label: "Review recent inspection failure with mechanic.",
    deep_link: `/shop/units/${encodeURIComponent(unitNumber)}/history`,
  });
  return q;
}

// Extract related-object relationship edges from event payload.
function deriveRelationships(events, unitNumber) {
  const seen = new Set();
  const edges = [];

  // Newest project association from a preop / dvir / defect.
  const projectEv = events.find((e) => e.project_number);
  if (projectEv && !seen.has(`project:${projectEv.project_number}`)) {
    seen.add(`project:${projectEv.project_number}`);
    edges.push({
      kind: "project",
      id: `project-${projectEv.project_number}`,
      label: `Project ${projectEv.project_number}`,
      sublabel: "assigned to project",
      deep_link: `/pm/command-center`,
    });
  }
  const operatorEv = events.find((e) => e.actor_name && (e.actor_role === "operator" || e.event_type === "preop"));
  if (operatorEv && !seen.has(`operator:${operatorEv.actor_name}`)) {
    seen.add(`operator:${operatorEv.actor_name}`);
    edges.push({
      kind: "operator",
      id: `operator-${operatorEv.actor_name}`,
      label: operatorEv.actor_name,
      sublabel: operatorEv.actor_role || "Operator",
      deep_link: null,
    });
  }
  const woEv = events.find((e) => e.related_work_order_id);
  if (woEv) {
    edges.push({
      kind: "wo",
      id: `wo-${woEv.related_work_order_id}`,
      label: `WO ${woEv.related_work_order_id.slice(-8)}`,
      sublabel: "work order",
      deep_link: `/shop/units/${encodeURIComponent(unitNumber)}/history`,
    });
  }
  const openOos = events.find((e) => e.event_type === "oos" && e.subtype !== "cleared");
  if (openOos) {
    edges.push({
      kind: "hold",
      id: "hold-oos",
      label: "Out of service",
      sublabel: "requires repair · current status",
      deep_link: `/shop/units/${encodeURIComponent(unitNumber)}/history`,
    });
  }
  edges.push({
    kind: "shop",
    id: "shop-history",
    label: "Shop history timeline",
    sublabel: "Asset service backbone",
    deep_link: `/shop/units/${encodeURIComponent(unitNumber)}/history`,
  });
  return edges;
}

export default function FleetUnitThread() {
  const { unit_number } = useParams();
  const [state, setState] = useState({ loaded: false, ok: false, events: [], product: null, extinguishers: [] });

  useEffect(() => {
    if (!unit_number) return;
    let cancelled = false;
    (async () => {
      // Track 19.62 · Phase A · surface linked fire extinguishers on parent asset.
      const [tl, summary, fe] = await Promise.all([
        _get(`/api/assets/${encodeURIComponent(unit_number)}/timeline`),
        _get(`/api/operational-intelligence/summary`),
        _get(`/api/safety/fire-extinguishers?assigned_target_ref=${encodeURIComponent(unit_number)}`),
      ]);
      if (cancelled) return;
      const events = (tl.body && (tl.body.events || tl.body.timeline || tl.body)) || [];
      const products = (summary.body && Array.isArray(summary.body.products)) ? summary.body.products : [];
      const fleetProduct = products.find((p) => p.product_id === "fleet_intelligence") || null;
      const extinguishers = Array.isArray(fe.body) ? fe.body : [];
      setState({
        loaded: true,
        ok: tl.ok,
        events: Array.isArray(events) ? events : (events.events || []),
        product: fleetProduct,
        extinguishers,
      });
    })();
    return () => { cancelled = true; };
  }, [unit_number]);

  const timelineEvents = useMemo(() => mapBackboneToTimeline(state.events), [state.events]);
  const health = useMemo(() => deriveHealth(state.events), [state.events]);
  const attentionItems = useMemo(() => {
    const base = deriveAttention(state.events, unit_number);
    // Track 19.62 · Phase A · overdue linked-extinguisher attention.
    const today = new Date().toISOString().slice(0, 10);
    (state.extinguishers || []).forEach((fe) => {
      if (fe.next_due_date && String(fe.next_due_date).slice(0, 10) < today) {
        base.push({
          severity: "HIGH",
          label: `Fire extinguisher ${fe.unit_id || ""} overdue`,
          why: `Next inspection was due ${fe.next_due_date}.`,
          owner: "Safety",
          deep_link: "/safety-portal/fire-extinguishers",
        });
      }
    });
    return base.slice(0, 5);
  }, [state.events, state.extinguishers, unit_number]);
  const actionQueue = useMemo(() => deriveActionQueue(state.events, unit_number), [state.events, unit_number]);
  const relationships = useMemo(() => {
    const baseEdges = deriveRelationships(state.events, unit_number);
    // Track 19.62 · Phase A · surface each linked fire extinguisher as a
    // relationship edge on the parent asset thread.
    const feEdges = (state.extinguishers || []).map((fe) => {
      const today = new Date().toISOString().slice(0, 10);
      const overdue = fe.next_due_date && String(fe.next_due_date).slice(0, 10) < today;
      const label = `Fire Ext ${fe.unit_id || fe.id?.slice(-8) || ""}`.trim();
      const sub = `${fe.type || "ABC"}${fe.next_due_date ? " · next due " + fe.next_due_date : ""}${overdue ? " · OVERDUE" : ""}`;
      return {
        label,
        kind: "fire_ext",
        id: `fe-${fe.id || fe.unit_id}`,
        sublabel: sub,
        deep_link: `/admin/assets/${encodeURIComponent(fe.unit_id || fe.id)}/thread`,
      };
    });
    return {
      subject: {
        id: `unit-${unit_number}`,
        kind: "unit",
        label: `Unit ${unit_number}`,
        sublabel: state.events[0]?.equipment_type || "Fleet asset",
      },
      edges: [...baseEdges, ...feEdges],
    };
  }, [state.events, state.extinguishers, unit_number]);

  const lastUpdatedIso = state.events[0]?.timestamp || null;
  const lastUpdated = lastUpdatedIso ? formatPlatformTime(lastUpdatedIso) : "—";

  const mission = {
    label: `Unit ${unit_number}`,
    kind: "Fleet asset",
    health: health.tier,
    facts: [
      { label: "Current status", value: health.tier },
      { label: "Last updated", value: lastUpdated },
      { label: "Timeline events", value: String(state.events.length) },
      { label: "Attention items", value: String(attentionItems.length) },
    ],
    explanation: health.reasons.length > 0
      ? `Why: ${health.reasons.join(" · ")}`
      : null,
  };

  // Every fleet unit uses the fleet_intelligence OI product for
  // Section 3 (Guidance Card) and Section 8 (Operational Intelligence).
  const guidanceProduct = state.product;

  if (!state.loaded) {
    return (
      <div
        data-testid="fleet-unit-thread-loading"
        className="max-w-5xl mx-auto px-4 py-8 text-sm font-mono uppercase tracking-widest text-slate-500"
      >
        Loading unit {unit_number}…
      </div>
    );
  }

  return (
    <div>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 pt-4">
        <Link
          to="/shop/fleet"
          data-testid="fleet-unit-thread-back"
          className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-widest font-bold text-slate-600 hover:text-slate-900"
        >
          ← Back to Fleet Visibility
        </Link>
      </div>
      <OperationalThreadPage
        testId="fleet-unit-thread"
        mission={mission}
        attention={{ items: attentionItems }}
        guidanceProduct={guidanceProduct}
        timelineEvents={timelineEvents}
        timelineTitle="Unit timeline · Asset service backbone"
        relationships={relationships}
        oiProduct={guidanceProduct}
        actionQueue={actionQueue}
        // Documents / Photos / History / Audit are honestly empty for
        // the pilot — the shared shell surfaces the sections with the
        // correct empty states rather than filling with fake data.
      />
    </div>
  );
}
