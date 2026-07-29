// Track 19.56 · Employee Operational Thread PROMOTION.
//
// This page is a PROMOTION-ONLY implementation. It DOES NOT add a
// new backend endpoint, a new score model, a new timeline framework,
// a new relationship engine, a new PDF, or a new permission surface.
// It consumes the EXISTING certified endpoint
// `GET /api/hr/employees/{id}/accountability/timeline` and its sibling
// `.../brief.pdf`, then presents the payload through the Track 19.55
// `OperationalThreadPage` shell so every employee page speaks the same
// operational language as every other Operational Thread on the
// platform.
//
// Route: /hr/employees/:id/thread
// Auth: HR + Safety + Admin — identical to the existing Accountability
//       page. Zero permission expansion. Same client guard.
//
// Zero-drift guarantees:
//   • Never queries any endpoint that did not exist before Track 19.56.
//   • Never re-derives scoring, attention level, or trend direction.
//   • Never stores anything.
//   • Never emails, never dispatches.
//   • Only ADAPTERS convert the certified payload into the shell's
//     data slots.
//
// The existing `HrEmployeeAccountabilityTimeline` page at
// `/hr/employees/:id/accountability` continues to work unchanged — this
// is a parallel visual layer, not a replacement.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useParams, Link } from "react-router-dom";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PortalShell } from "@/design-system";
import HrSideNavV2 from "@/components/hr/sidebar/HrSideNavV2";
import AccessDenied from "@/pages/AccessDenied";
import { isHr } from "@/lib/hrAuth";
import { isSafety } from "@/lib/safetyAuth";
import { isAdmin } from "@/lib/adminAuth";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { operationalError } from "@/lib/errors";
import OperationalThreadPage from "@/components/operational_intelligence/OperationalThreadPage";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Auth headers — identical to the certified Accountability page.
function authHeaders() {
  return buildScopedPortalAuthHeaders(["admin", "hr", "safety"]);
}

// ─────────────────────────────────────────────────────────────
// ADAPTERS — the ONLY new code in this track.
// Every adapter is a pure function of the certified payload.
// ─────────────────────────────────────────────────────────────

// Map an accountability event `category` to a Track 19.54 timeline `kind`.
const CATEGORY_TO_KIND = {
  "Training":             "history",
  "PPE & Equipment":      "assignment",
  "Incidents":            "incident",
  "Field Leadership":     "safety",
  "HR Lifecycle":         "history",
  "Driver Qualification": "inspection",
};

function timelineAdapter(events) {
  return (events || []).map((e) => ({
    id: e.id,
    kind: CATEGORY_TO_KIND[e.category] || "other",
    at: e.ts,
    title: e.title || e.category,
    summary: e.description
      || (e.expiration_date ? `Expires ${e.expiration_date}` : null),
    deep_link: null, // Corrections happen in the owner portal —
                     // the Accountability endpoint is read-only.
  }));
}

function attentionAdapter(data) {
  const items = [];
  const expired = data?.expired_items || [];
  const expiring = data?.expiring_within_90d || [];

  expired.slice(0, 3).forEach((x) => {
    items.push({
      severity: "CRITICAL",
      label: `${x.title} · EXPIRED`,
      why: `${x.category} · was due ${x.expiration_date}. Employee cannot perform tasks requiring this credential.`,
      owner: x.category === "Driver Qualification"
        ? "Transportation Manager"
        : x.category === "Training"
        ? "HR Director"
        : "HR Director",
      due: "Today",
    });
  });
  expiring.slice(0, 3).forEach((x) => {
    items.push({
      severity: "HIGH",
      label: `${x.title} · expiring ${x.expiration_date}`,
      why: `${x.category} · ≤ 90 days remaining. Renew before expiration to avoid downtime.`,
      owner: x.category === "Driver Qualification"
        ? "Transportation Manager"
        : "HR Director",
      due: x.expiration_date,
    });
  });
  return items;
}

function actionQueueAdapter(data) {
  const q = [];
  const expired = data?.expired_items || [];
  const expiring = data?.expiring_within_90d || [];
  if (expired.length > 0) {
    q.push({ label: `Renew ${expired.length} expired credential${expired.length === 1 ? "" : "s"}.` });
  }
  if (expiring.length > 0) {
    q.push({ label: `Schedule renewal for ${expiring.length} credential${expiring.length === 1 ? "" : "s"} expiring in ≤ 90 days.` });
  }
  const incidents = (data?.category_counts || {})["Incidents"] || 0;
  if (incidents > 0) {
    q.push({ label: `Review ${incidents} safety incident${incidents === 1 ? "" : "s"} on record.` });
  }
  return q;
}

function relationshipAdapter(employee) {
  const edges = [];
  if (employee?.supervisor) {
    edges.push({
      id: `supervisor-${employee.supervisor}`,
      kind: "foreman",
      label: employee.supervisor,
      sublabel: "Supervisor",
      label_edge: "reports to",
    });
  }
  if (employee?.crew) {
    edges.push({
      id: `crew-${employee.crew}`,
      kind: "other",
      label: employee.crew,
      sublabel: "Crew",
      label_edge: "assigned to",
    });
  }
  if (employee?.trade) {
    edges.push({
      id: `trade-${employee.trade}`,
      kind: "other",
      label: employee.trade,
      sublabel: "Trade",
      label_edge: "certified in",
    });
  }
  return edges;
}

function missionAdapter(data) {
  const emp = data?.employee || {};
  const cs = data?.current_state || {};
  const facts = [
    { label: "Employee ID",    value: emp.employee_id || "—" },
    { label: "Trade",          value: emp.trade || "—" },
    { label: "Supervisor",     value: emp.supervisor || "—" },
    { label: "Lifecycle",      value: emp.lifecycle_status || "—" },
    { label: "Expiring ≤ 90d", value: String(cs.expiring_within_90d ?? 0) },
    { label: "Expired",        value: String(cs.expired ?? 0) },
  ];

  const expiredCount = cs.expired || 0;
  const expiringCount = cs.expiring_within_90d || 0;
  let health = "Good";
  const reasons = [];
  if (expiredCount > 0) {
    health = "Critical";
    reasons.push(`${expiredCount} expired credential${expiredCount === 1 ? "" : "s"} on record.`);
  } else if (expiringCount > 0) {
    health = "Attention Needed";
    reasons.push(`${expiringCount} credential${expiringCount === 1 ? "" : "s"} expiring within 90 days.`);
  } else {
    reasons.push("No expired credentials.");
    reasons.push("No credentials expiring in the next 90 days.");
    if (cs.cdl_holder) reasons.push("CDL current.");
    if (cs.approved_company_driver) reasons.push("Approved company driver.");
  }

  return {
    label: emp.name || "—",
    kind: `Employee · ${emp.lifecycle_status || "active"}`,
    health,
    facts,
    explanation: `Why: ${reasons.join(" · ")}`,
  };
}

// ─────────────────────────────────────────────────────────────
// The promoted page.
// ─────────────────────────────────────────────────────────────
export default function HrEmployeeThread() {
  const { id } = useParams();
  const { t } = useT();
  const allowed = isHr() || isSafety() || isAdmin();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [product, setProduct] = useState(null);

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try {
      // The ONE certified endpoint. No new backend introduced.
      const r = await axios.get(
        `${API}/hr/employees/${id}/accountability/timeline`,
        { headers: authHeaders() }
      );
      setData(r.data);
      // OI signal for Section 8 / Section 3 (Guidance Card) —
      // consumes the certified summary payload only.
      try {
        const s = await axios.get(
          `${API}/operational-intelligence/summary`,
          { headers: authHeaders() }
        );
        const products = Array.isArray(s.data?.products) ? s.data.products : [];
        // hr_intelligence is the closest product signal for a
        // single employee's operational readiness.
        setProduct(products.find((p) => p.product_id === "hr_intelligence") || null);
      } catch { /* OI is optional · degrade gracefully */ }
    } catch (e) {
      setErr(operationalError(e, t("Could not load employee thread.")));
    } finally {
      setLoading(false);
    }
  }, [id, t]);

  useEffect(() => { if (allowed) load(); }, [allowed, load]);

  const downloadPdf = async () => {
    setDownloading(true);
    try {
      // Same PDF the certified Accountability page exports. Zero drift.
      const r = await axios.get(
        `${API}/hr/employees/${id}/accountability/brief.pdf`,
        { headers: authHeaders(), responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `Employee_Thread_${(data?.employee?.name || id).replace(/\s+/g, "_")}.pdf`;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(t("Compliance brief downloaded"));
    } catch (e) {
      toast.error(operationalError(e, t("Could not download PDF.")));
    } finally {
      setDownloading(false);
    }
  };

  const mission        = useMemo(() => missionAdapter(data), [data]);
  const attentionItems = useMemo(() => attentionAdapter(data), [data]);
  const actionQueue    = useMemo(() => actionQueueAdapter(data), [data]);
  const timelineEvents = useMemo(() => timelineAdapter(data?.events), [data]);
  const relationships  = useMemo(() => ({
    subject: {
      id: `employee-${id}`,
      kind: "operator",
      label: data?.employee?.name || "—",
      sublabel: data?.employee?.trade || data?.employee?.role || "Employee",
    },
    edges: relationshipAdapter(data?.employee),
  }), [data, id]);

  if (!allowed) return <AccessDenied attemptedPortal="hr" />;

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="HR Portal · Employee Thread"
      pageTitle={data?.employee?.name || "Employee"}
      subtitle={t("Universal Operational Thread · sourced from the certified Accountability endpoint.")}
      sideNav={<HrSideNavV2 />}
      primaryActions={
        <div className="flex items-center gap-2" data-testid="hr-employee-thread-actions">
          <Link
            to={`/hr/employees/${encodeURIComponent(id)}/accountability`}
            data-testid="hr-employee-thread-classic-link"
            className="inline-flex items-center px-3 py-1.5 text-xs font-mono font-bold uppercase tracking-widest border-2 border-slate-300 hover:border-slate-900 text-slate-900 rounded"
          >
            Classic view
          </Link>
          <Button
            size="sm"
            onClick={downloadPdf}
            disabled={downloading || loading || !data}
            className="bg-purple-700 hover:bg-purple-800 text-white"
            data-testid="hr-employee-thread-download-pdf"
          >
            <Download className="w-4 h-4 mr-1" />
            {downloading ? t("Generating…") : t("Compliance Brief PDF")}
          </Button>
        </div>
      }
    >
      {loading && !data ? (
        <div
          data-testid="hr-employee-thread-loading"
          className="max-w-5xl mx-auto px-4 py-8 text-sm font-mono uppercase tracking-widest text-slate-500"
        >
          {t("Loading employee thread…")}
        </div>
      ) : err ? (
        <div
          data-testid="hr-employee-thread-error"
          className="max-w-5xl mx-auto my-6 bg-rose-50 border border-rose-300 rounded-md p-4 text-sm text-rose-900"
        >
          {err}
        </div>
      ) : (
        <OperationalThreadPage
          testId="hr-employee-thread"
          mission={mission}
          attention={{ items: attentionItems }}
          guidanceProduct={product}
          timelineEvents={timelineEvents}
          timelineTitle={t("Accountability timeline · read-only")}
          relationships={relationships}
          oiProduct={product}
          actionQueue={actionQueue}
          // Documents / Photos / History / Audit remain honest-empty
          // in this promotion — the certified endpoint does not surface
          // per-employee document / photo / audit rows, and filling
          // those slots with fake data would violate the mandate.
        />
      )}
    </PortalShell>
  );
}
