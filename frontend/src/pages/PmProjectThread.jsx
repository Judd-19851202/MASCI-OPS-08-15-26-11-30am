// Track 19.57 · Project Operational Thread PROMOTION.
//
// This page is a PROMOTION-ONLY implementation. It DOES NOT add a
// new backend endpoint, a new project score model, a new project
// timeline framework, a new relationship engine, a new PDF, or a
// new permission surface. It consumes the EXISTING certified project
// endpoints identified by the Track 20.2 forensic audit:
//
//   • GET /api/pm/jobs                                        (project record)
//   • GET /api/jobs/{project_number}/recent-context           (recent crew · equipment · superintendent)
//   • GET /api/operational-events/project-day/{pn}/{date}     (per-day asset events)
//   • GET /api/material-movement/daily/{pn}/{date}            (per-day haul cycles · scale tickets)
//   • GET /api/job-hazard-files/by-project/{pn}               (project documents · JHAs)
//   • GET /api/operational-intelligence/summary               (project_intelligence OI product)
//
// It presents the composed payload through the Track 19.55
// OperationalThreadPage shell so every project page speaks the
// same operational language as every other Operational Thread on
// the platform.
//
// Route: /pm/project/:projectNumber/thread
// Auth: PM + Admin — identical to the existing PmProjectDetail
//       page (RequirePm gate in App.js). Zero permission expansion.
//
// Zero-drift guarantees:
//   • Never queries any endpoint that did not exist before Track 19.57.
//   • Never re-derives scoring, attention level, or trend direction —
//     both come verbatim from `project_intelligence` in the OI summary.
//   • Never stores anything.
//   • Never emails, never dispatches, never writes.
//   • Only ADAPTERS convert the certified payloads into the shell's
//     data slots. Adapters are pure functions.
//
// The existing PmProjectDetail page at /pm/project/:projectNumber
// continues to work unchanged — this is a parallel visual layer, not
// a replacement.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useParams, Link } from "react-router-dom";
import PmShell from "@/components/PmShell";
import AccessDenied from "@/pages/AccessDenied";
import { isPm } from "@/lib/pmAuth";
import { isAdmin } from "@/lib/adminAuth";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { operationalError } from "@/lib/errors";
import OperationalThreadPage from "@/components/operational_intelligence/OperationalThreadPage";
import { formatOperatorJobLabel, sanitizeOperatorProjectNumber, sanitizeOperatorReference } from "@/lib/operatorLanguage";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Auth headers — identical envelope to the certified PM pages.
// PM portal is the primary caller; Admin token accepted for
// cross-portal reads (matches PmJobsRead + PmProjectStaffing).
function authHeaders() {
  return buildScopedPortalAuthHeaders(["admin", "pm"]);
}

// Render YYYY-MM-DD for the local user's calendar day. Same helper
// pattern the certified PmProjectDetail page uses for its endpoints.
function todayYyyyMmDd() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// ─────────────────────────────────────────────────────────────
// ADAPTERS — the ONLY new code in this track.
// Every adapter is a pure function of the certified payload(s).
// ─────────────────────────────────────────────────────────────

function missionAdapter({ job, recent, oi }) {
  const projectName = sanitizeOperatorReference(job?.project_name, "Operations support work") || "—";
  const location    = job?.location || "—";
  const client      = job?.client || "—";
  const pm          = job?.project_manager || "—";
  const superintendent = recent?.superintendent || "—";
  const sourceDate = recent?.source_report_date || null;
  const safeProjectNumber = sanitizeOperatorProjectNumber(job?.project_number, "Operations support");

  // Health derives client-side ONLY from the certified OI attention
  // level — no new scoring is invented. Plain-English "Why" mirrors
  // the OI top_attention_label so the number always has narration.
  let health = "Good";
  const reasons = [];
  const attn = (oi?.attention_level || "").toUpperCase();
  if (attn === "CRITICAL") {
    health = "Critical";
    reasons.push(`Project Intelligence flags CRITICAL attention.`);
  } else if (attn === "HIGH") {
    health = "Attention Needed";
    reasons.push(`Project Intelligence flags HIGH attention.`);
  } else if (attn === "MODERATE" || attn === "ELEVATED") {
    health = "Attention Needed";
    reasons.push(`Project Intelligence flags elevated attention.`);
  } else if (attn) {
    reasons.push(`Project Intelligence attention: ${attn}.`);
  }
  if (oi?.top_attention_label) {
    reasons.push(`Top driver: ${oi.top_attention_label}.`);
  }
  if (sourceDate) {
    reasons.push(`Last Daily Report source: ${sourceDate}.`);
  } else {
    reasons.push("No recent Daily Report source found for this project.");
  }
  if (job && job.active === false) {
    health = "Attention Needed";
    reasons.push("Job is currently marked INACTIVE.");
  }

  const facts = [
    { label: "Project #",       value: safeProjectNumber || "—" },
    { label: "Client / Owner",  value: client },
    { label: "Location",        value: location },
    { label: "Project Manager", value: pm },
    { label: "Superintendent",  value: superintendent },
    { label: "Last Report",     value: sourceDate || "—" },
  ];

  return {
    label: projectName,
    kind: `Project · ${job?.active === false ? "inactive" : "active"}`,
    health,
    facts,
    explanation: `Why: ${reasons.join(" · ")}`,
  };
}

function attentionAdapter({ oi, mm, recent }) {
  const items = [];
  const attn = (oi?.attention_level || "").toUpperCase();
  if (oi?.top_attention_label && (attn === "CRITICAL" || attn === "HIGH")) {
    items.push({
      severity: attn,
      label: oi.top_attention_label,
      why: "Sourced from certified Project Intelligence — reviewed in the OI cockpit.",
      owner: "Project Manager",
      due: "Today",
      deep_link: "/operational-intelligence",
    });
  }
  const missing = mm?.proof_summary?.missing_proof_count || 0;
  if (missing > 0) {
    items.push({
      severity: "HIGH",
      label: `${missing} scale-ticket proof${missing === 1 ? "" : "s"} missing today`,
      why: "Material moved without a matching scale ticket — reconcile before end of shift.",
      owner: "Superintendent",
      due: "Today",
    });
  }
  const vs = mm?.verification_status;
  if (vs === "mismatch" || vs === "needs_review") {
    items.push({
      severity: "HIGH",
      label: `Material movement verification: ${vs.replace("_", " ")}`,
      why: "Haul cycle vs. scale-ticket reconciliation flagged for review.",
      owner: "Project Manager",
      due: "Today",
    });
  }
  if (!recent?.source_report_date) {
    items.push({
      severity: "MODERATE",
      label: "No recent Daily Report on record",
      why: "No Daily Report has been submitted for this project — verify field activity.",
      owner: "Superintendent",
      due: "Today",
    });
  }
  return items.slice(0, 5);
}

function actionQueueAdapter({ oi, mm, jhaCount, recent }) {
  const q = [];
  if (oi?.top_attention_label) {
    q.push({ label: `Review Project Intelligence driver: ${oi.top_attention_label}.` });
  }
  const missing = mm?.proof_summary?.missing_proof_count || 0;
  if (missing > 0) {
    q.push({ label: `Reconcile ${missing} missing scale-ticket proof${missing === 1 ? "" : "s"} for today.` });
  }
  if (mm?.verification_status === "needs_review") {
    q.push({ label: "Resolve material-movement items flagged Needs Review." });
  }
  if (!recent?.source_report_date) {
    q.push({ label: "Confirm today's Daily Report is submitted." });
  }
  if (jhaCount === 0) {
    q.push({ label: "Upload / verify project JHA on file." });
  }
  return q;
}

// Timeline schema per Track 19.54 OperationalThread contract:
// { id, kind, at, title, summary, deep_link? }
const KIND_ASSET      = "assignment";
const KIND_HAUL       = "assignment";
const KIND_DOC        = "history";

function timelineAdapter({ projectDay, mm, jhaItems, recent }) {
  const events = [];

  // 1. Per-asset arrivals for today (from certified project-day endpoint).
  const assets = projectDay?.assets || [];
  assets.slice(0, 20).forEach((a) => {
    events.push({
      id: `asset-${a.asset_key}-first`,
      kind: KIND_ASSET,
      at: a.first_seen || null,
      title: `${a.asset_label || a.asset_key} · arrived on site`,
      summary: a.still_on_site
        ? "Still on site."
        : (a.last_seen ? `Departed ${a.last_seen}` : "Departed."),
    });
  });

  // 2. Haul cycles completed today (from certified material-movement endpoint).
  const cycles = mm?.haul_cycles || [];
  cycles.slice(0, 20).forEach((c, i) => {
    const src = [c.source_location, c.destination].filter(Boolean).join(" → ");
    events.push({
      id: `haul-${c.id || i}`,
      kind: KIND_HAUL,
      at: c.completed_at || null,
      title: `Haul · ${c.material || "material"}${c.truck_id ? ` · ${c.truck_id}` : ""}`,
      summary: src || (c.haul_type || "Material"),
    });
  });

  // 3. JHA / project documents uploaded (from certified job-hazard-files endpoint).
  jhaItems.slice(0, 10).forEach((f, i) => {
    events.push({
      id: `jha-${f.file_id || f.id || i}`,
      kind: KIND_DOC,
      at: f.uploaded_at || null,
      title: `JHA / project document uploaded`,
      summary: f.filename || f.notes || "Project document on file.",
    });
  });

  // 4. Last-known Daily Report source (from recent-context).
  if (recent?.source_report_date) {
    events.push({
      id: `dr-source-${recent.source_report_date}`,
      kind: "history",
      at: `${recent.source_report_date}T12:00:00Z`,
      title: "Daily Report source",
      summary: `Most recent Daily Report captured for this project.`,
    });
  }

  // Newest first — most `at` values are ISO strings; sort defensively.
  events.sort((a, b) => (b.at || "").localeCompare(a.at || ""));
  return events;
}

function relationshipAdapter({ job, recent }) {
  const edges = [];
  if (job?.project_manager) {
    edges.push({
      id: `pm-${job.project_manager}`,
      kind: "operator",
      label: job.project_manager,
      sublabel: "Project Manager",
      label_edge: "managed by",
    });
  }
  if (recent?.superintendent) {
    edges.push({
      id: `sup-${recent.superintendent}`,
      kind: "foreman",
      label: recent.superintendent,
      sublabel: "Superintendent",
      label_edge: "led by",
    });
  }
  if (job?.client) {
    edges.push({
      id: `client-${job.client}`,
      kind: "other",
      label: job.client,
      sublabel: "Owner / Client",
      label_edge: "owned by",
    });
  }
  (recent?.masci_crews || []).slice(0, 4).forEach((c, i) => {
    const name = c?.name || c?.employee_name || c?.crew_role || `Crew ${i + 1}`;
    edges.push({
      id: `crew-${c?.employee_id || i}`,
      kind: "operator",
      label: name,
      sublabel: c?.crew_role || "Crew",
      label_edge: "recent crew",
    });
  });
  (recent?.equipment || []).slice(0, 4).forEach((e, i) => {
    const label = e?.unit_id || e?.description || `Unit ${i + 1}`;
    edges.push({
      id: `eq-${e?.unit_id || i}`,
      kind: "asset",
      label,
      sublabel: e?.description || "Equipment",
      label_edge: "recent equipment",
    });
  });
  return edges;
}

function documentsAdapter(jhaItems) {
  return (jhaItems || []).slice(0, 20).map((f, i) => ({
    id: f.file_id || f.id || `jha-${i}`,
    name: f.filename || f.notes || "Project document",
    deep_link: f.file_id
      ? `${API}/job-hazard-files/${encodeURIComponent(f.file_id)}/download`
      : null,
  }));
}

// ─────────────────────────────────────────────────────────────
// The promoted page.
// ─────────────────────────────────────────────────────────────
export default function PmProjectThread() {
  const { projectNumber } = useParams();
  const pn = (projectNumber || "").trim();
  const safePn = sanitizeOperatorProjectNumber(pn, "Operations support");
  const allowed = isPm() || isAdmin();

  const [state, setState] = useState({
    loading: true,
    err: "",
    job: null,
    recent: null,
    projectDay: null,
    mm: null,
    jhaItems: [],
    oi: null,
  });

  const load = useCallback(async () => {
    if (!pn) return;
    setState((s) => ({ ...s, loading: true, err: "" }));
    const today = todayYyyyMmDd();
    try {
      // Every endpoint below already existed before Track 19.57.
      // No new backend introduced.
      const [jobsRes, recentRes, dayRes, mmRes, jhaRes, oiRes] =
        await Promise.allSettled([
          axios.get(`${API}/pm/jobs`, { headers: authHeaders() }),
          axios.get(`${API}/jobs/${encodeURIComponent(pn)}/recent-context`),
          axios.get(`${API}/operational-events/project-day/${encodeURIComponent(pn)}/${today}`),
          axios.get(`${API}/material-movement/daily/${encodeURIComponent(pn)}/${today}`),
          axios.get(`${API}/job-hazard-files/by-project/${encodeURIComponent(pn)}`),
          axios.get(`${API}/operational-intelligence/summary`, { headers: authHeaders() }),
        ]);

      const jobItems = jobsRes.status === "fulfilled"
        ? (jobsRes.value.data?.items || []) : [];
      const job = jobItems.find((j) => (j.project_number || "") === pn) || null;

      const recent  = recentRes.status === "fulfilled" ? recentRes.value.data  : null;
      const projectDay = dayRes.status === "fulfilled"  ? dayRes.value.data     : null;
      const mm      = mmRes.status === "fulfilled"      ? mmRes.value.data      : null;
      const jhaItems = jhaRes.status === "fulfilled"
        ? (jhaRes.value.data?.items || []) : [];

      let oi = null;
      if (oiRes.status === "fulfilled") {
        const products = Array.isArray(oiRes.value.data?.products)
          ? oiRes.value.data.products : [];
        oi = products.find((p) => p.product_id === "project_intelligence") || null;
      }

      setState({ loading: false, err: "", job, recent, projectDay, mm, jhaItems, oi });
    } catch (e) {
      setState((s) => ({
        ...s,
        loading: false,
        err: operationalError(e, "Could not load project thread."),
      }));
    }
  }, [pn]);

  useEffect(() => { if (allowed) load(); }, [allowed, load]);

  const mission        = useMemo(
    () => missionAdapter({ job: state.job, recent: state.recent, oi: state.oi }),
    [state.job, state.recent, state.oi]
  );
  const attentionItems = useMemo(
    () => attentionAdapter({ oi: state.oi, mm: state.mm, recent: state.recent }),
    [state.oi, state.mm, state.recent]
  );
  const actionQueue = useMemo(
    () => actionQueueAdapter({
      oi: state.oi,
      mm: state.mm,
      jhaCount: (state.jhaItems || []).length,
      recent: state.recent,
    }),
    [state.oi, state.mm, state.jhaItems, state.recent]
  );
  const timelineEvents = useMemo(
    () => timelineAdapter({
      projectDay: state.projectDay,
      mm: state.mm,
      jhaItems: state.jhaItems || [],
      recent: state.recent,
    }),
    [state.projectDay, state.mm, state.jhaItems, state.recent]
  );
  const relationships = useMemo(() => ({
    subject: {
      id: `project-${pn}`,
      kind: "asset",
      label: formatOperatorJobLabel(pn, state.job?.project_name || pn || "—"),
      sublabel: `Project · ${safePn || "—"}`,
    },
    edges: relationshipAdapter({ job: state.job, recent: state.recent }),
  }), [pn, safePn, state.job, state.recent]);
  const documents = useMemo(
    () => documentsAdapter(state.jhaItems || []),
    [state.jhaItems]
  );

  if (!allowed) return <AccessDenied attemptedPortal="pm" />;

  return (
    <PmShell
      title="Project Thread"
      section="jobs"
      intro={
        <p className="text-xs text-slate-500">
          Operational thread for the selected project. Read-only timeline,
          field activity, materials, JHA, and project intelligence context.
        </p>
      }
    >
      <div className="max-w-5xl mx-auto flex items-center justify-between gap-2 mb-2 px-4 sm:px-0">
        <div
          className="font-mono text-xs uppercase tracking-widest text-slate-500"
          data-testid="pm-project-thread-header"
        >
          Project #{safePn || "—"}
        </div>
        <Link
          to={`/pm/project/${encodeURIComponent(pn)}`}
          data-testid="pm-project-thread-classic-link"
          className="inline-flex items-center px-3 py-1.5 text-xs font-mono font-bold uppercase tracking-widest border-2 border-slate-300 hover:border-slate-900 text-slate-900 rounded"
        >
          Classic project view
        </Link>
      </div>

      {state.loading && !state.job ? (
        <div
          data-testid="pm-project-thread-loading"
          className="max-w-5xl mx-auto px-4 py-8 text-sm font-mono uppercase tracking-widest text-slate-500"
        >
          Loading project thread…
        </div>
      ) : state.err ? (
        <div
          data-testid="pm-project-thread-error"
          className="max-w-5xl mx-auto my-6 bg-rose-50 border border-rose-300 rounded-md p-4 text-sm text-rose-900"
        >
          {state.err}
        </div>
      ) : (
        <OperationalThreadPage
          testId="pm-project-thread"
          mission={mission}
          attention={{ items: attentionItems }}
          guidanceProduct={state.oi}
          timelineEvents={timelineEvents}
          timelineTitle="Project timeline · today · read-only"
          relationships={relationships}
          documents={documents}
          oiProduct={state.oi}
          actionQueue={actionQueue}
          // Photos / History / Audit remain honest-empty in this
          // promotion — the certified project endpoints surveyed by
          // Track 20.2 do not expose per-project photo, history, or
          // audit rows in a shape safe to render here. Filling those
          // slots with fake data would violate the mandate.
        />
      )}
    </PmShell>
  );
}
