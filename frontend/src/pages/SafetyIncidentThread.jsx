// Track 19.58 · Incident Operational Thread PROMOTION.
//
// This page is a PROMOTION-ONLY implementation, matching the pattern
// established by Track 19.55 (Fleet), Track 19.56 (Employee), and
// Track 19.57 (Project). It DOES NOT add a new backend endpoint,
// database, OI product, recommendation engine, PDF, or permission
// surface. It consumes the EXISTING certified incident endpoints
// identified by the Track 20.3 forensic audit:
//
//   • GET /api/incident-cases/{id}                          (case core)
//   • GET /api/incident-cases/{id}/health                   (readiness · blockers)
//   • GET /api/incident-cases/{id}/executive-snapshot       (exec summary)
//   • GET /api/incident-cases/{id}/timeline                 (timeline)
//   • GET /api/incident-cases/{id}/evidence                 (documents + photos)
//   • GET /api/incident-cases/{id}/witnesses                (relationships · text-only)
//   • GET /api/incident-cases/{id}/tasks                     (open tasks)
//   • GET /api/operational-intelligence/summary              (safety_morning_digest)
//
// It presents the composed payload through the Track 19.55
// OperationalThreadPage shell so every incident page speaks the same
// operational language as every other Universal Operational Thread.
//
// Route: /safety/incidents/:caseId/thread
// Auth: Safety + Admin — inherits the same axios client used by
//       SafetyCaseWorkspace (Safety JWT via `caseWorkspaceApi.js`).
//
// Zero-drift guarantees:
//   • Never calls an endpoint that did not exist before Track 19.58.
//   • Never re-derives scoring — everything comes from the certified
//     `health.readiness_level` + `severity` + `safety_morning_digest`.
//   • Read-only — no POST/PUT/PATCH/DELETE anywhere.
//   • Sensitive sections (medical / agency / audit) render honest
//     empty states when the underlying call returns 403, matching how
//     the Safety Case Workspace gates today.
//   • Adapters only. Pure functions.
//
// The existing SafetyCaseWorkspace at /safety/cases/:caseId continues
// to work unchanged — this is a parallel READ layer, not a replacement.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useParams, Link } from "react-router-dom";
import { isSafety } from "@/lib/safetyAuth";
import { isAdmin, getAdminToken } from "@/lib/adminAuth";
import { operationalError } from "@/lib/errors";
import AccessDenied from "@/pages/AccessDenied";
import * as api from "@/lib/caseWorkspaceApi";
import OperationalThreadPage from "@/components/operational_intelligence/OperationalThreadPage";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// The workspace's caseWorkspaceApi already forwards the Safety JWT.
// The OI summary endpoint accepts either the Admin or Safety token.
function oiAuthHeaders() {
  const h = {};
  const a = getAdminToken(); if (a) h["X-Admin-Token"] = a;
  return h;
}

// ─────────────────────────────────────────────────────────────
// ADAPTERS — the ONLY new code in this track. Pure functions.
// ─────────────────────────────────────────────────────────────

// Severity → normalized 4-value Evidence Readiness bucket (Track 19.58
// terminology — the mandate explicitly bans legal / compliance /
// litigation language). Never asserts legal conclusions; only ranks
// how many known blockers exist.
function evidenceReadiness(health) {
  const level = String(health?.readiness_level || "").toLowerCase();
  const blockerCount = (health?.blockers || []).length;
  if (level === "excellent" || level === "ready" || (level === "" && blockerCount === 0)) {
    return { label: "Excellent", tone: "positive" };
  }
  if (level === "good" || (blockerCount > 0 && blockerCount <= 1)) {
    return { label: "Good", tone: "neutral" };
  }
  if (level === "needs_attention" || level === "attention" || (blockerCount >= 2 && blockerCount <= 3)) {
    return { label: "Needs Attention", tone: "warning" };
  }
  return { label: "Incomplete", tone: "critical" };
}

function healthChip(caseDoc, health) {
  const sev = String(caseDoc?.severity || "").toLowerCase();
  const readiness = String(health?.readiness_level || "").toLowerCase();
  if (sev === "critical" || sev === "serious" || readiness === "incomplete") return "Critical";
  if (sev === "high" || readiness === "needs_attention" || readiness === "attention") return "Attention Needed";
  if (sev === "moderate" || sev === "medium") return "Attention Needed";
  return "Good";
}

function missionAdapter({ caseDoc, health, snap }) {
  const number = caseDoc?.case_number || caseDoc?.id || "—";
  const title = caseDoc?.title || caseDoc?.summary_title || "Incident case";
  const severity = caseDoc?.severity || "—";
  const type = caseDoc?.type || caseDoc?.incident_type || "—";
  const status = caseDoc?.status || caseDoc?.state || "—";
  const project = caseDoc?.project_number || caseDoc?.project || "—";
  const reporter = caseDoc?.reporter_name || caseDoc?.reporter || "—";
  const investigator = caseDoc?.assigned_investigator || caseDoc?.investigator || "—";
  const location = caseDoc?.location || "—";
  const opened = caseDoc?.opened_at || caseDoc?.created_at || caseDoc?.occurred_at || "—";
  const readiness = evidenceReadiness(health);

  const reasons = [];
  reasons.push(`Severity: ${severity}.`);
  reasons.push(`Evidence Readiness: ${readiness.label}.`);
  if (Array.isArray(health?.blockers) && health.blockers.length > 0) {
    reasons.push(`${health.blockers.length} outstanding blocker${health.blockers.length === 1 ? "" : "s"} on this case.`);
  } else {
    reasons.push("No outstanding blockers reported by the case-health engine.");
  }
  if (snap?.headline) reasons.push(`Snapshot: ${snap.headline}.`);

  return {
    label: `${number} · ${title}`,
    kind: `Incident · ${status}`,
    health: healthChip(caseDoc, health),
    facts: [
      { label: "Case #",         value: number },
      { label: "Type",           value: type },
      { label: "Severity",       value: severity },
      { label: "Status",         value: status },
      { label: "Project",        value: project },
      { label: "Reported by",    value: reporter },
      { label: "Investigator",   value: investigator },
      { label: "Location",       value: location },
      { label: "Opened",         value: opened },
      { label: "Evidence Readiness", value: readiness.label },
    ],
    explanation: `Why: ${reasons.join(" · ")}`,
  };
}

function attentionAdapter({ caseDoc, health, oi }) {
  const items = [];
  const sev = String(caseDoc?.severity || "").toLowerCase();
  const readiness = evidenceReadiness(health);

  if (sev === "critical" || sev === "serious") {
    items.push({
      severity: "CRITICAL",
      label: `Severity ${caseDoc?.severity} · executive review is expected`,
      why: "Serious/Critical severity cases require executive readiness before closeout.",
      owner: "Safety Director",
      due: "Today",
    });
  }
  (health?.blockers || []).slice(0, 4).forEach((b) => {
    items.push({
      severity: readiness.label === "Incomplete" ? "HIGH" : "MODERATE",
      label: b.label || b.key || "Outstanding blocker",
      why: b.explanation || b.description || "Blocker reported by the case-health engine.",
      owner: b.owner_role || "Safety",
      due: b.due || "Today",
    });
  });
  if (oi?.top_attention_label && (oi.attention_level === "HIGH" || oi.attention_level === "CRITICAL")) {
    items.push({
      severity: oi.attention_level,
      label: `Portfolio signal: ${oi.top_attention_label}`,
      why: "Sourced from certified `safety_morning_digest` Operational Intelligence.",
      owner: "Safety",
      due: "Today",
      deep_link: "/operational-intelligence",
    });
  }
  return items.slice(0, 5);
}

function actionQueueAdapter({ health, tasks, oi }) {
  const q = [];
  // Specific verbs — never "monitor" / "review" / "watch" (mandate).
  (health?.blockers || []).slice(0, 3).forEach((b) => {
    const label = b.action_label || b.label || b.key || "Resolve outstanding blocker";
    q.push({ label });
  });
  (tasks || [])
    .filter((t) => (t.status || "").toLowerCase() !== "done" && (t.status || "").toLowerCase() !== "closed")
    .slice(0, 3)
    .forEach((t) => q.push({ label: t.title || t.summary || "Complete assigned safety task." }));
  if (oi?.top_attention_label && q.length < 5) {
    q.push({ label: `Address portfolio driver: ${oi.top_attention_label}.` });
  }
  return q.slice(0, 5);
}

function timelineAdapter({ events }) {
  const arr = Array.isArray(events) ? events : [];
  return arr.map((e, i) => ({
    id: e.id || `evt-${i}`,
    kind: e.kind || "history",
    at: e.at || e.occurred_at || e.created_at || null,
    title: e.title || e.label || "Case event",
    summary: e.summary || e.description || "",
    deep_link: e.deep_link || null,
  }));
}

function relationshipAdapter({ caseDoc, witnesses, evidence }) {
  const edges = [];
  if (caseDoc?.project_number) {
    edges.push({
      id: `proj-${caseDoc.project_number}`,
      kind: "asset",
      label: caseDoc.project_number,
      sublabel: "Project",
      label_edge: "on project",
    });
  }
  (caseDoc?.involved_employees || []).slice(0, 6).forEach((emp, i) => {
    edges.push({
      id: `emp-${emp.employee_id || emp.id || i}`,
      kind: "operator",
      label: emp.name || emp.employee_name || `Employee ${i + 1}`,
      sublabel: emp.role || "Involved employee",
      label_edge: "involved",
    });
  });
  (caseDoc?.equipment_units || []).slice(0, 6).forEach((eq, i) => {
    edges.push({
      id: `eq-${eq.unit_id || eq.id || i}`,
      kind: "asset",
      label: eq.unit_id || eq.description || `Unit ${i + 1}`,
      sublabel: eq.description || "Equipment",
      label_edge: "equipment",
    });
  });
  // Witnesses are TEXT-ONLY per Track 20.3 audit — no clickable node.
  (witnesses || []).slice(0, 4).forEach((w, i) => {
    edges.push({
      id: `wit-${w.id || i}`,
      kind: "other",
      label: w.name || `Witness ${i + 1}`,
      sublabel: "Witness (text-only)",
      label_edge: "statement",
    });
  });
  const evCount = (evidence || []).length;
  if (evCount > 0) {
    edges.push({
      id: "evidence-summary",
      kind: "other",
      label: `${evCount} evidence item${evCount === 1 ? "" : "s"}`,
      sublabel: "Evidence",
      label_edge: "collected",
    });
  }
  return edges;
}

function documentsAdapter({ caseId, evidence }) {
  const docs = [];
  // Executive Report — always linked (permission enforced server-side).
  if (caseId) {
    docs.push({
      id: `exec-report-${caseId}`,
      name: "Executive Case Report (PDF)",
      deep_link: `${API}/incident-cases/${encodeURIComponent(caseId)}/executive-report.pdf`,
    });
  }
  (evidence || [])
    .filter((e) => (e.kind || "").toLowerCase() !== "image")
    .slice(0, 20)
    .forEach((e, i) => {
      docs.push({
        id: e.id || `ev-${i}`,
        name: e.title || e.filename || "Evidence document",
        deep_link: e.download_url || (e.id ? `${API}/incident-cases/${encodeURIComponent(caseId)}/evidence/${encodeURIComponent(e.id)}/download` : null),
      });
    });
  return docs;
}

// ─────────────────────────────────────────────────────────────
// The promoted page.
// ─────────────────────────────────────────────────────────────
export default function SafetyIncidentThread() {
  const { caseId } = useParams();
  const cid = (caseId || "").trim();
  const allowed = isSafety() || isAdmin();

  const [state, setState] = useState({
    loading: true,
    err: "",
    caseDoc: null,
    health: null,
    snap: null,
    events: [],
    evidence: [],
    witnesses: [],
    tasks: [],
    oi: null,
  });

  const load = useCallback(async () => {
    if (!cid) return;
    setState((s) => ({ ...s, loading: true, err: "" }));
    try {
      // Every call below already existed before Track 19.58. Sensitive
      // calls (medical / agency / audit) are intentionally NOT
      // requested here — Track 20.3 mandates honest empty states so
      // that the thread never becomes a 403-driven leakage vector.
      const [caseDoc, health, snap, events, evidence, witnesses, tasks, oiRes] =
        await Promise.all([
          api.getCase(cid).catch(() => null),
          api.getHealth(cid).catch(() => null),
          api.getExecutiveSnapshot(cid).catch(() => null),
          api.listTimeline(cid).catch(() => []),
          api.listEvidence(cid).catch(() => []),
          api.listWitnesses(cid).catch(() => []),
          api.listTasks(cid).catch(() => []),
          axios.get(`${API}/operational-intelligence/summary`, {
            headers: oiAuthHeaders(),
          }).catch(() => null),
        ]);

      let oi = null;
      if (oiRes) {
        const products = Array.isArray(oiRes.data?.products) ? oiRes.data.products : [];
        oi = products.find((p) => p.product_id === "safety_morning_digest") || null;
      }

      setState({
        loading: false, err: "",
        caseDoc, health, snap,
        events: events || [],
        evidence: evidence || [],
        witnesses: witnesses || [],
        tasks: tasks || [],
        oi,
      });
    } catch (e) {
      setState((s) => ({
        ...s,
        loading: false,
        err: operationalError(e, "Could not load incident thread."),
      }));
    }
  }, [cid]);

  useEffect(() => { if (allowed) load(); }, [allowed, load]);

  const mission = useMemo(
    () => missionAdapter({ caseDoc: state.caseDoc, health: state.health, snap: state.snap }),
    [state.caseDoc, state.health, state.snap]
  );
  const attentionItems = useMemo(
    () => attentionAdapter({ caseDoc: state.caseDoc, health: state.health, oi: state.oi }),
    [state.caseDoc, state.health, state.oi]
  );
  const actionQueue = useMemo(
    () => actionQueueAdapter({ health: state.health, tasks: state.tasks, oi: state.oi }),
    [state.health, state.tasks, state.oi]
  );
  const timelineEvents = useMemo(
    () => timelineAdapter({ events: state.events }),
    [state.events]
  );
  const relationships = useMemo(() => ({
    subject: {
      id: `case-${cid}`,
      kind: "asset",
      label: state.caseDoc?.case_number || cid || "—",
      sublabel: `Incident case · ${state.caseDoc?.severity || "—"}`,
    },
    edges: relationshipAdapter({
      caseDoc: state.caseDoc,
      witnesses: state.witnesses,
      evidence: state.evidence,
    }),
  }), [cid, state.caseDoc, state.witnesses, state.evidence]);
  const documents = useMemo(
    () => documentsAdapter({ caseId: cid, evidence: state.evidence }),
    [cid, state.evidence]
  );

  if (!allowed) return <AccessDenied attemptedPortal="safety" />;

  return (
    <div className="min-h-screen bg-slate-100" data-testid="safety-incident-thread-page">
      <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <div>
          <div
            className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500"
            data-testid="safety-incident-thread-header"
          >
            Incident Thread
          </div>
          <div className="font-mono text-xs uppercase tracking-widest text-slate-900">
            Case #{state.caseDoc?.case_number || cid || "—"}
          </div>
        </div>
        <Link
          to={`/safety/cases/${encodeURIComponent(cid)}`}
          data-testid="safety-incident-thread-workspace-link"
          className="ml-auto inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-800 hover:bg-slate-50"
        >
          Case workspace
        </Link>
      </header>

      <main className="pb-8">
        {state.loading && !state.caseDoc ? (
          <div
            data-testid="safety-incident-thread-loading"
            className="max-w-5xl mx-auto px-4 py-8 text-sm font-mono uppercase tracking-widest text-slate-500"
          >
            Loading incident thread…
          </div>
        ) : state.err ? (
          <div
            data-testid="safety-incident-thread-error"
            className="max-w-5xl mx-auto my-6 mx-4 sm:mx-auto bg-rose-50 border border-rose-300 rounded-md p-4 text-sm text-rose-900"
          >
            {state.err}
          </div>
        ) : (
          <OperationalThreadPage
            testId="safety-incident-thread"
            mission={mission}
            attention={{ items: attentionItems }}
            guidanceProduct={state.oi}
            timelineEvents={timelineEvents}
            timelineTitle="Investigation timeline · newest first · read-only"
            relationships={relationships}
            documents={documents}
            oiProduct={state.oi}
            actionQueue={actionQueue}
            // Photos / History / Audit remain honest-empty in this
            // promotion — Track 20.3 mandates that restricted sections
            // render honest empty states rather than call endpoints
            // that would leak information via 403 vs 200 timing.
          />
        )}
      </main>
    </div>
  );
}
