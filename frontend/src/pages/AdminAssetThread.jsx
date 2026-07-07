// Track 19.61 · Asset / Equipment Operational Thread PROMOTION.
//
// Frontend-only promotion. Same pattern as Tracks 19.55 (Fleet pilot),
// 19.56 (Employee), 19.57 (Project), 19.58 (Incident), 19.60 (Vendor).
// Consumes ONLY certified endpoints identified by the Track 20.5
// forensic audit and unlocked by the Track 19.61 extensions:
//
//   • GET /api/asset-spine/resolve?ref=…                       (universal identifier resolver — Track 19.61)
//   • GET /api/asset-spine/assets/{asset_id}                   (canonical asset)
//   • GET /api/asset-spine/assets/{asset_id}/profile           (fused profile)
//   • GET /api/assets/{unit_number}/timeline                   (Track 13.26 backbone)
//   • GET /api/operational-intelligence/summary                (OI products; class-aware routing)
//   • GET /api/employee-records/records?entity_kind=asset&asset_id=…
//                                                              (legacy paper for asset — Track 19.61 lane)
//   • GET /api/asset-spine/assets/{asset_id}/documents         (native asset documents)
//
// Route: /admin/assets/:assetRef/thread
// Auth : Admin only (initial owner-portal placement per Track 20.5 doctrine).
//
// Zero-drift guarantees:
//   • No new backend collection.
//   • No new score model / OI product / PDF renderer / email path.
//   • Read-only — no POST/PUT/PATCH/DELETE anywhere in this component.
//   • No permission widening beyond the Admin gate.
//   • Operational Health is a qualitative label ("Good / Attention
//     Needed / Critical") derived ONLY from backbone events. No %,
//     no compliance or legal claims.
//   • OI product is chosen from EXISTING products; missing → honest empty.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useParams, Link } from "react-router-dom";
import { isAdmin, getAdminToken } from "@/lib/adminAuth";
import { operationalError } from "@/lib/errors";
import AccessDenied from "@/pages/AccessDenied";
import OperationalThreadPage from "@/components/operational_intelligence/OperationalThreadPage";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function adminHeaders() {
  const h = {};
  const a = getAdminToken();
  if (a) h["X-Admin-Token"] = a;
  return h;
}

// Class-aware OI routing (existing products only — no new products).
// Falls back to null so the shell renders an honest "no product" state.
function oiProductForClass(assetClass) {
  const cls = (assetClass || "").toLowerCase();
  if (cls.includes("truck") || cls.includes("trailer") || cls.includes("heavy")
      || cls.includes("trench") || cls.includes("roadway")) {
    return "fleet_intelligence";
  }
  if (cls.includes("survey") || cls.includes("gps") || cls.includes("technology")
      || cls.includes("safety equipment") || cls.includes("support")
      || cls.includes("facility") || cls.includes("temporary")) {
    return "shop_intelligence";
  }
  // Track 19.62 · Phase A — Fire Protection routes to fleet_intelligence
  // when the extinguisher is truck/equipment-mounted, otherwise
  // shop_intelligence for stationed. Honest empty otherwise.
  if (cls.includes("fire protection")) {
    return "shop_intelligence";
  }
  return null;
}

// Asset document type slugs from Track 19.61 catalog.
const ASSET_TYPE_LABEL = {
  warranty: "Warranty",
  purchase_agreement: "Purchase Agreement",
  bill_of_sale: "Bill of Sale",
  title_registration: "Title / Registration",
  insurance_policy: "Insurance Policy",
  calibration_certificate: "Calibration Certificate",
  operator_manual: "Operator Manual",
  spec_sheet: "Spec Sheet",
  historical_inspection_report: "Historical Inspection Report",
  historical_maintenance_record: "Historical Maintenance Record",
  asset_photo: "Asset Photo",
  other_asset_document: "Other Asset Document",
};

// ─────────────────────────────────────────────────────────────
// Backbone event mapping — reused verbatim from FleetUnitThread
// (same taxonomy from Track 13.26).
// ─────────────────────────────────────────────────────────────

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
  "defect|acknowledged": "Defect acknowledged",
  "defect|repaired": "Defect repaired",
  "repair|started": "Repair started",
  "repair|completed": "Repair complete",
  "oos|preop": "Out of service · Pre-Op",
  "oos|dvir": "Out of service · DVIR",
  "oos|cleared": "Returned to service",
  "transfer|assigned": "Assigned to project",
  "transfer|returned": "Returned from project",
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
    summary: e.actor_name
      ? `by ${e.actor_name}${e.actor_role ? ` (${e.actor_role})` : ""}`
      : null,
    deep_link: e.related_work_order_id
      ? `/shop/units/${encodeURIComponent(e.unit_number || "")}/history`
      : null,
  }));
}

function mapDocsToTimeline(docs) {
  return (docs || [])
    .filter((d) => d.approval_status === "linked")
    .map((d) => ({
      id: `doc-${d.id}`,
      kind: "history",
      at: d.effective_date || d.approved_at || d.created_at,
      title: `Document · ${ASSET_TYPE_LABEL[d.record_type] || d.record_type || "Asset paper"}`,
      summary: d.source_file_name || d.notes || "Historical Records",
      deep_link: null,
    }));
}

// ─────────────────────────────────────────────────────────────
// ADAPTERS — pure functions of the certified payloads.
// ─────────────────────────────────────────────────────────────

function deriveHealth(events, asset) {
  const openOos = (events || []).some(
    (e) => e.event_type === "oos" && e.subtype !== "cleared" &&
      !(events || []).some((x) => x.event_type === "oos" &&
        x.subtype === "cleared" && x.timestamp > e.timestamp),
  );
  const openDefects = (events || []).some(
    (e) => e.event_type === "defect" &&
      (e.subtype === "opened" || e.subtype === "acknowledged"),
  );
  const recentFailure = (events || []).some(
    (e) => ["preop|failed", "dvir|failed"].includes(`${e.event_type}|${e.subtype || ""}`),
  );
  const retired = (asset?.status || "").toLowerCase() === "retired";

  const reasons = [];
  if (retired) reasons.push("Asset is retired.");
  if (openOos) reasons.push("Currently out of service.");
  if (openDefects) reasons.push("Open defect on record.");
  if (recentFailure) reasons.push("Recent inspection failure.");

  let tier = "Good";
  if (retired) tier = "Restricted";
  else if (openOos) tier = "Critical";
  else if (openDefects || recentFailure) tier = "Attention Needed";

  if (!retired && !openOos && !openDefects && !recentFailure) {
    reasons.push("No safety holds on record.");
    reasons.push("No active defects.");
    reasons.push("No recent inspection failures.");
  }
  return { tier, reasons };
}

function missionAdapter({ asset, docs, events, assetRef }) {
  const health = deriveHealth(events, asset);
  const linkedCount = (docs || []).filter((d) => d.approval_status === "linked").length;
  const label = asset?.asset_number || asset?.unit_number
    || asset?.serial_number || asset?.asset_id || assetRef || "—";
  const cls = asset?.asset_class || asset?.type || "Asset";

  // Track 19.62 · Phase A · Fire Protection fact panel.
  const isFire = (asset?.asset_class || "").toLowerCase().includes("fire protection");
  if (isFire) {
    const assignedLabel = asset?.assigned_target_label
      || asset?.assigned_facility_name
      || asset?.assigned_room_name
      || asset?.assigned_unit_number
      || asset?.assigned_location_detail
      || "—";
    return {
      label,
      kind: `${cls} · ${asset?.asset_type || "Fire Extinguisher"}`,
      health: health.tier,
      facts: [
        { label: "Extinguisher",           value: label },
        { label: "Type",                   value: asset?.asset_type || asset?.type || "—" },
        { label: "Serial",                 value: asset?.serial_number || "—" },
        { label: "Assignment",             value: assignedLabel },
        { label: "Assignment kind",        value: asset?.assigned_target_kind || asset?.location_kind || "—" },
        { label: "Location detail",        value: asset?.assigned_location_detail || "—" },
        { label: "Last inspection",        value: asset?.last_inspection_date || "—" },
        { label: "Next due",               value: asset?.next_due_date || "—" },
        { label: "Last inspection status", value: asset?.last_status || "—" },
        { label: "Timeline events",        value: String((events || []).length) },
        { label: "Documents linked",       value: String(linkedCount) },
      ],
      explanation: health.reasons.length > 0 ? `Why: ${health.reasons.join(" · ")}` : null,
    };
  }

  return {
    label,
    kind: `${cls}${asset?.department ? " · " + asset.department : ""} · owned by Admin`,
    health: health.tier,
    facts: [
      { label: "Asset",            value: label },
      { label: "Class",            value: asset?.asset_class || "—" },
      { label: "Type",             value: asset?.asset_type || asset?.type || "—" },
      { label: "Serial",           value: asset?.serial_number || "—" },
      { label: "VIN",              value: asset?.vin || "—" },
      { label: "Status",           value: asset?.status || (asset?.retired_at ? "retired" : "active") },
      { label: "Department",       value: asset?.department || "—" },
      { label: "Timeline events",  value: String((events || []).length) },
      { label: "Documents linked", value: String(linkedCount) },
    ],
    explanation: health.reasons.length > 0 ? `Why: ${health.reasons.join(" · ")}` : null,
  };
}

function attentionAdapter({ events, docs, assetRef, asset }) {
  const items = [];

  // Track 19.62 · Phase A · Fire Protection attention rules.
  const isFire = (asset?.asset_class || "").toLowerCase().includes("fire protection");
  if (isFire) {
    const today = new Date().toISOString().slice(0, 10);
    if (asset?.next_due_date && String(asset.next_due_date).slice(0, 10) < today) {
      items.push({
        severity: "HIGH",
        label: "Inspection Overdue",
        why: `Next inspection was due ${asset.next_due_date}.`,
        owner: "Safety",
        deep_link: "/safety-portal/fire-extinguishers",
      });
    }
    if (!asset?.assigned_target_ref && !asset?.assigned_target_kind
        && !asset?.assigned_unit_number && !asset?.assigned_facility_name) {
      items.push({
        severity: "MEDIUM",
        label: "Assignment Missing",
        why: "This extinguisher has no linked target (vehicle, equipment, room, facility, or project).",
        owner: "Safety",
        deep_link: "/safety-portal/fire-extinguishers",
      });
    }
    if (!asset?.serial_number && !asset?.asset_tag) {
      items.push({
        severity: "MEDIUM",
        label: "Record Missing",
        why: "Serial number and asset tag are both empty — cannot uniquely identify this extinguisher.",
        owner: "Safety",
        deep_link: "/safety-portal/fire-extinguishers",
      });
    }
    if ((asset?.last_status || "").toLowerCase() === "fail") {
      items.push({
        severity: "CRITICAL",
        label: "Failed Inspection",
        why: "The most recent inspection recorded Fail. Needs Attention until re-inspected.",
        owner: "Safety",
        deep_link: "/safety-portal/fire-extinguishers",
      });
    }
    const pendingDocs = (docs || []).filter((d) => (d.approval_status || "").startsWith("pending"));
    if (pendingDocs.length > 0) {
      items.push({
        severity: "MEDIUM",
        label: `${pendingDocs.length} fire document${pendingDocs.length === 1 ? "" : "s"} awaiting HR/Admin approval`,
        why: "Historical Records queue holds fire paper until reviewed.",
        owner: "HR / Admin",
        deep_link: "/hr/historical-records/queue",
      });
    }
    return items.slice(0, 5);
  }

  const openOos = (events || []).find((e) => e.event_type === "oos" && e.subtype !== "cleared");
  if (openOos) {
    items.push({
      severity: "CRITICAL",
      label: `Unit ${assetRef} is out of service`,
      why: `Triggered ${openOos.subtype || "OOS"} on ${openOos.timestamp || "unknown date"}.`,
      owner: "Shop Manager",
      due: "Today",
      deep_link: `/shop/units/${encodeURIComponent(assetRef)}/history`,
    });
  }
  const openDefects = (events || []).filter(
    (e) => e.event_type === "defect" && (e.subtype === "opened" || e.subtype === "acknowledged"),
  );
  openDefects.slice(0, 3).forEach((d) => {
    items.push({
      severity: "HIGH",
      label: `Open defect · ${d.subtype === "opened" ? "not yet acknowledged" : "acknowledged, awaiting repair"}`,
      why: "Blocks unit availability until repaired.",
      owner: "Shop Manager",
      deep_link: `/shop/units/${encodeURIComponent(assetRef)}/history`,
    });
  });
  const pendingDocs = (docs || []).filter((d) => (d.approval_status || "").startsWith("pending"));
  if (pendingDocs.length > 0) {
    items.push({
      severity: "MEDIUM",
      label: `${pendingDocs.length} asset document${pendingDocs.length === 1 ? "" : "s"} awaiting HR/Admin approval`,
      why: "Historical Records queue holds asset paper until reviewed.",
      owner: "HR / Admin",
      deep_link: "/hr/historical-records/queue",
    });
  }
  return items.slice(0, 5);
}

function actionQueueAdapter({ events, docs, assetRef }) {
  const q = [];
  const openOos = (events || []).find((e) => e.event_type === "oos" && e.subtype !== "cleared");
  if (openOos) q.push({
    label: "Clear the OOS state (repair + manager review + RTS).",
    deep_link: `/shop/units/${encodeURIComponent(assetRef)}/history`,
  });
  const openDefects = (events || []).filter(
    (e) => e.event_type === "defect" && (e.subtype === "opened" || e.subtype === "acknowledged"),
  );
  if (openDefects.length > 0) q.push({
    label: `Assign or complete ${openDefects.length} open defect${openDefects.length === 1 ? "" : "s"}.`,
    deep_link: `/shop/units/${encodeURIComponent(assetRef)}/history`,
  });
  const pendingDocs = (docs || []).filter((d) => (d.approval_status || "").startsWith("pending"));
  if (pendingDocs.length > 0) q.push({
    label: `Review ${pendingDocs.length} pending asset document${pendingDocs.length === 1 ? "" : "s"} in the Historical Records queue.`,
    deep_link: "/hr/historical-records/queue",
  });
  return q;
}

function relationshipAdapter({ asset, events, docs, assetRef }) {
  const seen = new Set();
  const edges = [];

  // Track 19.62 · Phase A · Fire Protection parent-asset edge.
  const isFire = (asset?.asset_class || "").toLowerCase().includes("fire protection");
  if (isFire) {
    const parentUnit = asset?.assigned_unit_number || asset?.equipment_master_id;
    if (parentUnit) {
      edges.push({
        kind: "parent_asset",
        id: `parent-${parentUnit}`,
        label: asset?.assigned_target_label || `Unit ${parentUnit}`,
        sublabel: `mounted on · ${asset?.assigned_target_kind || "asset"}`,
        deep_link: `/admin/assets/${encodeURIComponent(parentUnit)}/thread`,
      });
    }
    if (asset?.assigned_facility_name) {
      edges.push({
        kind: "facility",
        id: `facility-${asset.assigned_facility_name}`,
        label: asset.assigned_facility_name,
        sublabel: `stationed in facility${asset?.assigned_room_name ? " · " + asset.assigned_room_name : ""}`,
        deep_link: null,
      });
    }
    if (asset?.assigned_project_number) {
      edges.push({
        kind: "project",
        id: `project-${asset.assigned_project_number}`,
        label: `Project ${asset.assigned_project_number}`,
        sublabel: "assigned to project",
        deep_link: `/pm/command-center`,
      });
    }
    edges.push({
      kind: "safety_portal",
      id: "safety-portal-fire",
      label: "Safety Portal · Fire Extinguishers",
      sublabel: "inspection authoritative surface",
      deep_link: "/safety-portal/fire-extinguishers",
    });
    const linkedDocs = (docs || []).filter((d) => d.approval_status === "linked");
    if (linkedDocs.length > 0) {
      edges.push({
        kind: "historical_records",
        id: "hr-records",
        label: `${linkedDocs.length} fire document${linkedDocs.length === 1 ? "" : "s"}`,
        sublabel: "Historical Records · asset lane",
        deep_link: "/hr/historical-records/queue",
      });
    }
    return edges;
  }

  const projectEv = (events || []).find((e) => e.project_number);
  if (projectEv && !seen.has(`project:${projectEv.project_number}`)) {
    seen.add(`project:${projectEv.project_number}`);
    edges.push({
      kind: "project",
      id: `project-${projectEv.project_number}`,
      label: `Project ${projectEv.project_number}`,
      sublabel: "assigned to",
      deep_link: `/pm/command-center`,
    });
  }
  const operatorEv = (events || []).find(
    (e) => e.actor_name && (e.actor_role === "operator" || e.event_type === "preop"),
  );
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
  const woEv = (events || []).find((e) => e.related_work_order_id);
  if (woEv) {
    edges.push({
      kind: "wo",
      id: `wo-${woEv.related_work_order_id}`,
      label: `WO ${woEv.related_work_order_id.slice(-8)}`,
      sublabel: "shop work order",
      deep_link: `/shop/units/${encodeURIComponent(assetRef)}/history`,
    });
  }
  const openOos = (events || []).find((e) => e.event_type === "oos" && e.subtype !== "cleared");
  if (openOos) {
    edges.push({
      kind: "hold",
      id: "hold-oos",
      label: "Out of service",
      sublabel: "requires repair",
      deep_link: `/shop/units/${encodeURIComponent(assetRef)}/history`,
    });
  }
  const linkedDocs = (docs || []).filter((d) => d.approval_status === "linked");
  if (linkedDocs.length > 0) {
    edges.push({
      kind: "historical_records",
      id: "hr-records",
      label: `${linkedDocs.length} historical document${linkedDocs.length === 1 ? "" : "s"}`,
      sublabel: "Historical Records · asset lane",
      deep_link: "/hr/historical-records/queue",
    });
  }
  edges.push({
    kind: "shop",
    id: "shop-history",
    label: "Shop history",
    sublabel: "Asset service backbone",
    deep_link: `/shop/units/${encodeURIComponent(assetRef)}/history`,
  });
  if (asset?.department) {
    edges.push({
      kind: "department",
      id: `dept-${asset.department}`,
      label: asset.department,
      sublabel: "owning department",
      deep_link: null,
    });
  }
  return edges;
}

function documentsAdapter({ docs }) {
  return (docs || []).map((d) => ({
    id: d.id,
    name: d.source_file_name || ASSET_TYPE_LABEL[d.record_type] || d.record_type || "Asset document",
    kind: ASSET_TYPE_LABEL[d.record_type] || d.record_type,
    status: d.approval_status,
    deep_link: `/hr/historical-records/queue?record_id=${encodeURIComponent(d.id)}`,
  }));
}

// ─────────────────────────────────────────────────────────────
// The promoted page.
// ─────────────────────────────────────────────────────────────
export default function AdminAssetThread() {
  const { assetRef } = useParams();
  const ref = (assetRef || "").trim();
  const allowed = isAdmin();

  const [state, setState] = useState({
    loading: true,
    err: "",
    asset: null,       // resolver payload (canonical asset identity)
    profile: null,     // full spine profile
    events: [],
    docs: [],
    product: null,
  });

  const load = useCallback(async () => {
    if (!ref) return;
    setState((s) => ({ ...s, loading: true, err: "" }));
    try {
      // Step 1 — resolve the asset ref → canonical asset_id (Track 19.61).
      const resolveRes = await axios
        .get(`${API}/asset-spine/resolve`, {
          headers: adminHeaders(),
          params: { ref },
        })
        .catch(() => null);
      const resolved = resolveRes?.data || null;
      const canonicalId = resolved?.asset_id || ref;
      const canonicalUnit = resolved?.unit_number || ref;
      const isFireRef = resolved?.source === "fire_extinguishers"
        || (resolved?.asset_class || "").toLowerCase().includes("fire protection");

      // Step 2 — fetch profile + timeline + OI summary + documents in parallel.
      // Track 19.62 · Phase A · when the ref is a fire extinguisher, the
      // profile / timeline endpoints (which read equipment_master) return
      // nothing — we rely on the resolver payload itself for identity
      // and skip the spine profile fetch to avoid a 404 spam.
      const [profileRes, timelineRes, summaryRes, docsRes] = await Promise.all([
        isFireRef ? Promise.resolve(null) : axios.get(
          `${API}/asset-spine/assets/${encodeURIComponent(canonicalId)}/profile`,
          { headers: adminHeaders() },
        ).catch(() => null),
        isFireRef ? Promise.resolve(null) : axios.get(
          `${API}/assets/${encodeURIComponent(canonicalUnit)}/timeline`,
          { headers: adminHeaders() },
        ).catch(() => null),
        axios.get(
          `${API}/operational-intelligence/summary`,
          { headers: adminHeaders() },
        ).catch(() => null),
        axios.get(`${API}/employee-records/records`, {
          headers: adminHeaders(),
          params: { entity_kind: "asset", asset_id: canonicalId, limit: 200 },
        }).catch(() => null),
      ]);

      const profileBody = profileRes?.data || null;
      const asset = profileBody?.asset || resolved || null;
      const tlBody = timelineRes?.data || {};
      const events = Array.isArray(tlBody?.events)
        ? tlBody.events
        : Array.isArray(tlBody?.timeline) ? tlBody.timeline : [];
      const products = Array.isArray(summaryRes?.data?.products) ? summaryRes.data.products : [];
      const oiKey = oiProductForClass(asset?.asset_class);
      const product = oiKey ? (products.find((p) => p.product_id === oiKey) || null) : null;
      const docs = docsRes?.data?.records || [];

      setState({
        loading: false,
        err: "",
        asset,
        profile: profileBody,
        events,
        docs,
        product,
      });
    } catch (e) {
      setState((s) => ({
        ...s,
        loading: false,
        err: operationalError(e, "Could not load asset thread."),
      }));
    }
  }, [ref]);

  useEffect(() => { if (allowed) load(); }, [allowed, load]);

  const mission = useMemo(
    () => missionAdapter({ asset: state.asset, docs: state.docs, events: state.events, assetRef: ref }),
    [state.asset, state.docs, state.events, ref],
  );
  const attentionItems = useMemo(
    () => attentionAdapter({ events: state.events, docs: state.docs, assetRef: ref, asset: state.asset }),
    [state.events, state.docs, ref, state.asset],
  );
  const actionQueue = useMemo(
    () => actionQueueAdapter({ events: state.events, docs: state.docs, assetRef: ref }),
    [state.events, state.docs, ref],
  );
  const timelineEvents = useMemo(() => {
    const bk = mapBackboneToTimeline(state.events);
    const dk = mapDocsToTimeline(state.docs);
    // Newest first.
    return [...bk, ...dk].sort((a, b) => String(b.at || "").localeCompare(String(a.at || "")));
  }, [state.events, state.docs]);
  const relationships = useMemo(() => ({
    subject: {
      id: `asset-${state.asset?.asset_id || ref}`,
      kind: "asset",
      label: state.asset?.asset_number || state.asset?.unit_number || ref || "—",
      sublabel: state.asset?.asset_class || state.asset?.type || "Asset",
    },
    edges: relationshipAdapter({
      asset: state.asset,
      events: state.events,
      docs: state.docs,
      assetRef: ref,
    }),
  }), [ref, state.asset, state.events, state.docs]);
  const documents = useMemo(
    () => documentsAdapter({ docs: state.docs }),
    [state.docs],
  );

  if (!allowed) return <AccessDenied attemptedPortal="admin" />;

  return (
    <div className="min-h-screen bg-slate-100" data-testid="admin-asset-thread-page">
      <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <div>
          <div
            className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500"
            data-testid="admin-asset-thread-header"
          >
            Asset Thread · Admin
          </div>
          <div className="font-mono text-xs uppercase tracking-widest text-slate-900">
            {state.asset?.asset_number || state.asset?.unit_number || ref || "—"}
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {(state.asset?.asset_class || "").toLowerCase().includes("fire protection") ? (
            <Link
              to="/safety-portal/fire-extinguishers"
              data-testid="admin-asset-thread-safety-fire-link"
              className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-800 hover:bg-slate-50"
            >
              Manage in Safety Portal
            </Link>
          ) : null}
          <Link
            to={`/hr/historical-records/intake?entity_kind=asset&asset_id=${encodeURIComponent(state.asset?.asset_id || ref)}`}
            data-testid="admin-asset-thread-upload-link"
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-800 hover:bg-slate-50"
          >
            Add asset document
          </Link>
          <Link
            to={`/fleet/unit/${encodeURIComponent(state.asset?.unit_number || ref)}`}
            data-testid="admin-asset-thread-fleet-link"
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-800 hover:bg-slate-50"
          >
            Fleet lens
          </Link>
          <Link
            to="/admin/equipment"
            data-testid="admin-asset-thread-master-link"
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-800 hover:bg-slate-50"
          >
            Asset master
          </Link>
        </div>
      </header>

      <main className="pb-8">
        {state.loading && !state.asset ? (
          <div
            data-testid="admin-asset-thread-loading"
            className="max-w-5xl mx-auto px-4 py-8 text-sm font-mono uppercase tracking-widest text-slate-500"
          >
            Loading asset thread…
          </div>
        ) : state.err ? (
          <div
            data-testid="admin-asset-thread-error"
            className="max-w-5xl mx-auto my-6 bg-rose-50 border border-rose-300 rounded-md p-4 text-sm text-rose-900"
          >
            {state.err}
          </div>
        ) : (
          <OperationalThreadPage
            testId="admin-asset-thread"
            mission={mission}
            attention={{ items: attentionItems }}
            guidanceProduct={state.product}
            timelineEvents={timelineEvents}
            timelineTitle="Asset timeline · newest first · Service backbone + Historical Records"
            relationships={relationships}
            documents={documents}
            oiProduct={state.product}
            actionQueue={actionQueue}
            // Photos / History / Audit render honest-empty states here.
            // Native photos live in asset_documents; legacy paper lives
            // in the Historical Records asset lane and is shown above
            // under Documents / Timeline.
          />
        )}
      </main>
    </div>
  );
}
