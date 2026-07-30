// Track 19.60 · Vendor Operational Thread PROMOTION.
//
// Frontend-only promotion. Same pattern as Tracks 19.55 (Fleet),
// 19.56 (Employee), 19.57 (Project), 19.58 (Incident). Consumes ONLY
// certified endpoints identified by the Track 20.4 forensic audit and
// unlocked by the Track 19.59 vendor lane extension:
//
//   • GET /api/suppliers                                                 (supplier master · name + is_active + id)
//   • GET /api/employee-records/records?entity_kind=vendor&vendor_id=…   (vendor documents · Track 19.59 lane)
//   • GET /api/employee-records/records?entity_kind=vendor&vendor_name=… (fallback when id absent)
//   • GET /api/employee-records/records/{id}/file                        (original file download · reused verbatim)
//
// Route: /admin/vendors/:vendorId/thread
// Auth: Admin only (initial owner-portal placement per Track 20.4 doctrine).
//
// Zero-drift guarantees:
//   • No new backend route.
//   • No new collection.
//   • No new score model / OI product / PDF renderer / email path.
//   • Read-only — no POST/PUT/PATCH/DELETE anywhere.
//   • No permission widening beyond the existing Admin gate.
//   • Vendor operational health is a client-side qualitative label
//     ("Excellent · Good · Attention Needed · Restricted") derived
//     ONLY from certified fields — no compliance / legal / OSHA
//     claims.
//   • Photos / OI / History sections render honest-empty states.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useParams, Link } from "react-router-dom";
import { toast } from "sonner";
import { isAdmin, getAdminToken } from "@/lib/adminAuth";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { operationalError } from "@/lib/errors";
import AccessDenied from "@/pages/AccessDenied";
import OperationalThreadPage from "@/components/operational_intelligence/OperationalThreadPage";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function adminHeaders() {
  return buildScopedPortalAuthHeaders(["admin"]);
}

// Vendor document type slugs from Track 19.59 catalog.
const VENDOR_TYPE_LABEL = {
  w9: "W-9",
  certificate_of_insurance: "Certificate of Insurance / COI",
  contract_agreement: "Contract / Agreement",
  subcontract: "Subcontract",
  rental_agreement: "Rental Agreement",
  service_agreement: "Service Agreement",
  business_license: "Business License",
  prequalification: "Prequalification",
  vendor_packet: "Vendor Packet",
  quote_proposal: "Quote / Proposal",
  pricing_sheet: "Pricing Sheet",
  safety_document: "Safety Document",
  material_certification: "Material Certification",
  correspondence: "Correspondence",
  other_vendor_document: "Other Vendor Document",
};

// ─────────────────────────────────────────────────────────────
// ADAPTERS — pure functions of the certified payloads.
// ─────────────────────────────────────────────────────────────

function vendorHealth(vendor, docs) {
  const activeFlag = vendor?.is_active !== false;
  if (!activeFlag) return { label: "Restricted", reason: "Vendor is inactive in the supplier master." };
  const types = new Set((docs || []).filter((d) => d.approval_status === "linked").map((d) => d.record_type));
  const hasW9 = types.has("w9");
  const hasCOI = types.has("certificate_of_insurance");
  const hasContract = types.has("contract_agreement") || types.has("subcontract") || types.has("service_agreement");
  const missing = [];
  if (!hasW9) missing.push("W-9 not on file");
  if (!hasCOI) missing.push("Certificate of Insurance not on file");
  if (!hasContract) missing.push("Contract / Agreement not on file");
  const pendingCount = (docs || []).filter((d) => (d.approval_status || "").startsWith("pending")).length;
  if (missing.length === 0 && pendingCount === 0) return { label: "Excellent", reason: "Vendor active. Key documents on file." };
  if (missing.length <= 1 && pendingCount === 0) return { label: "Good", reason: `Vendor active. ${missing.join(" · ") || "1 document to verify."}` };
  const reasonParts = [];
  if (missing.length > 0) reasonParts.push(missing.join(" · "));
  if (pendingCount > 0) reasonParts.push(`${pendingCount} vendor document${pendingCount === 1 ? "" : "s"} awaiting approval`);
  return { label: "Attention Needed", reason: reasonParts.join(" · ") };
}

function missionAdapter({ vendor, docs, vendorId }) {
  const name = vendor?.name || vendor?.display_name || vendorId || "—";
  const active = vendor?.is_active !== false;
  const health = vendorHealth(vendor, docs);
  const linkedCount = (docs || []).filter((d) => d.approval_status === "linked").length;

  return {
    label: name,
    kind: `Vendor · ${active ? "active" : "inactive"} · owned by HR/Admin`,
    health: health.label,
    facts: [
      { label: "Vendor",         value: name },
      { label: "Vendor ID",      value: vendorId || "—" },
      { label: "Status",         value: active ? "Active" : "Inactive" },
      { label: "Documents on file", value: String(linkedCount) },
      { label: "Awaiting approval", value: String((docs || []).filter((d) => (d.approval_status || "").startsWith("pending")).length) },
      { label: "Ownership",      value: "HR / Admin" },
    ],
    explanation: `Why: ${health.reason}. Vendor identity is matched by supplier name — treat cross-portal joins as name-based, not FK-integrity.`,
  };
}

function attentionAdapter({ vendor, docs }) {
  const items = [];
  if (vendor?.is_active === false) {
    items.push({
      severity: "CRITICAL",
      label: "Vendor is inactive in the supplier master",
      why: "This vendor is soft-archived. Treat as restricted for new work.",
      owner: "HR / Admin",
      due: "Today",
    });
  }
  const linkedTypes = new Set((docs || []).filter((d) => d.approval_status === "linked").map((d) => d.record_type));
  if (!linkedTypes.has("w9")) {
    items.push({
      severity: "HIGH",
      label: "W-9 not on file",
      why: "Federal tax reporting form is missing. Required before payments in most jurisdictions.",
      owner: "HR / Admin",
      due: "This week",
    });
  }
  if (!linkedTypes.has("certificate_of_insurance")) {
    items.push({
      severity: "HIGH",
      label: "Certificate of Insurance not on file",
      why: "Insurance evidence missing. Required before jobsite access in most cases.",
      owner: "HR / Admin",
      due: "This week",
    });
  }
  const pending = (docs || []).filter((d) => (d.approval_status || "").startsWith("pending"));
  if (pending.length > 0) {
    items.push({
      severity: "MODERATE",
      label: `${pending.length} vendor document${pending.length === 1 ? "" : "s"} awaiting approval`,
      why: "Vendor-lane records staged for HR/Admin approval in the Historical Records Queue.",
      owner: "HR / Admin",
      due: "Today",
      deep_link: "/hr/historical-records/queue",
    });
  }
  return items.slice(0, 5);
}

function actionQueueAdapter({ vendor, docs }) {
  const q = [];
  const linkedTypes = new Set((docs || []).filter((d) => d.approval_status === "linked").map((d) => d.record_type));
  if (!linkedTypes.has("w9")) q.push({ label: "Upload W-9 for this vendor." });
  if (!linkedTypes.has("certificate_of_insurance")) q.push({ label: "Upload Certificate of Insurance." });
  if (!linkedTypes.has("contract_agreement") && !linkedTypes.has("subcontract") && !linkedTypes.has("service_agreement")) {
    q.push({ label: "Upload contract / agreement." });
  }
  const pending = (docs || []).filter((d) => (d.approval_status || "").startsWith("pending"));
  if (pending.length > 0) q.push({ label: `Approve ${pending.length} pending vendor document${pending.length === 1 ? "" : "s"} in the queue.` });
  if (vendor?.is_active === false) q.push({ label: "Verify vendor should remain inactive or restore in supplier master." });
  return q.slice(0, 5);
}

function timelineAdapter({ docs }) {
  return (docs || []).map((d, i) => ({
    id: d.id || `doc-${i}`,
    kind: d.approval_status === "linked" ? "history" : "assignment",
    at: d.approved_at || d.updated_at || d.created_at || null,
    title: `${VENDOR_TYPE_LABEL[d.record_type] || d.record_type} · ${d.approval_status || "staged"}`,
    summary: d.source_file_name ? `Source: ${d.source_file_name}` : (d.notes || ""),
    deep_link: d.id ? `${API}/employee-records/records/${encodeURIComponent(d.id)}/file` : null,
  })).sort((a, b) => (b.at || "").localeCompare(a.at || ""));
}

function relationshipAdapter({ vendor, docs, vendorId }) {
  const edges = [];
  edges.push({
    id: "owner-hr",
    kind: "operator",
    label: "HR / Admin",
    sublabel: "Owner (source-of-truth for vendor master)",
    label_edge: "owned by",
  });
  const linked = (docs || []).filter((d) => d.approval_status === "linked");
  if (linked.length > 0) {
    edges.push({
      id: "docs-linked",
      kind: "other",
      label: `${linked.length} vendor document${linked.length === 1 ? "" : "s"} on file`,
      sublabel: "Historical Records · vendor lane",
      label_edge: "documents",
    });
  }
  const pending = (docs || []).filter((d) => (d.approval_status || "").startsWith("pending"));
  if (pending.length > 0) {
    edges.push({
      id: "docs-pending",
      kind: "other",
      label: `${pending.length} pending approval`,
      sublabel: "Historical Records Queue",
      label_edge: "queue",
    });
  }
  // PO / project linkage is name-based today (Track 20.4 audit finding).
  edges.push({
    id: "po-history",
    kind: "asset",
    label: "PO history",
    sublabel: `Matched by supplier name${vendor?.name ? ` (${vendor.name})` : ""}`,
    label_edge: "POs",
  });
  if (vendorId) {
    edges.push({
      id: `supplier-${vendorId}`,
      kind: "asset",
      label: vendor?.name || vendorId,
      sublabel: "Supplier master record",
      label_edge: "master",
    });
  }
  return edges;
}

function documentsAdapter({ docs }) {
  // Group by record_type; keep display flat per Track 19.55 shell.
  return (docs || []).map((d, i) => {
    const typeLabel = VENDOR_TYPE_LABEL[d.record_type] || d.record_type || "Vendor document";
    const status = d.approval_status || "staged";
    const parts = [typeLabel, `state: ${status}`];
    if (d.effective_date) parts.push(`eff: ${d.effective_date}`);
    if (d.source_file_name) parts.push(d.source_file_name);
    return {
      id: d.id || `doc-${i}`,
      name: parts.join(" · "),
      deep_link: d.id ? `${API}/employee-records/records/${encodeURIComponent(d.id)}/file` : null,
    };
  });
}

// ─────────────────────────────────────────────────────────────
// The promoted page.
// ─────────────────────────────────────────────────────────────
export default function AdminVendorThread() {
  const { vendorId } = useParams();
  const vid = (vendorId || "").trim();
  const allowed = isAdmin();

  const [state, setState] = useState({
    loading: true,
    err: "",
    vendor: null,
    docs: [],
  });

  // Track 19.60 amendment · HR/Admin edit UI state.
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({});

  const startEdit = useCallback(() => {
    setForm({
      name:            state.vendor?.name || "",
      display_name:    state.vendor?.display_name || "",
      dba:             state.vendor?.dba || "",
      vendor_type:     state.vendor?.vendor_type || "",
      primary_contact: state.vendor?.primary_contact || "",
      phone:           state.vendor?.phone || "",
      email:           state.vendor?.email || "",
      address:         state.vendor?.address || "",
      notes:           state.vendor?.notes || "",
      is_active:       state.vendor?.is_active !== false,
      do_not_use:      !!state.vendor?.do_not_use,
    });
    setEditing(true);
  }, [state.vendor]);

  const cancelEdit = useCallback(() => { setEditing(false); }, []);

  const saveEdit = useCallback(async () => {
    if (!vid) return;
    if (!(form.name || "").trim()) {
      toast.error("Vendor name is required.");
      return;
    }
    setSaving(true);
    try {
      const res = await axios.put(
        `${API}/admin/suppliers/${encodeURIComponent(vid)}`,
        form,
        { headers: adminHeaders() },
      );
      const updated = res.data || null;
      setState((s) => ({ ...s, vendor: updated || s.vendor }));
      setEditing(false);
      toast.success("Vendor saved.");
    } catch (e) {
      toast.error(operationalError(e, "Could not save vendor."));
    } finally {
      setSaving(false);
    }
  }, [vid, form]);

  const load = useCallback(async () => {
    if (!vid) return;
    setState((s) => ({ ...s, loading: true, err: "" }));
    try {
      // Suppliers endpoint is public (public read). Vendor documents
      // require the Admin token via the certified employee-records
      // gate. Both endpoints already existed before Track 19.60.
      const [suppRes, docsByIdRes] = await Promise.all([
        axios.get(`${API}/suppliers`).catch(() => null),
        axios.get(`${API}/employee-records/records`, {
          headers: adminHeaders(),
          params: { entity_kind: "vendor", vendor_id: vid, limit: 200 },
        }).catch(() => null),
      ]);

      const suppliers = suppRes?.data?.items || suppRes?.data?.suppliers || [];
      const vendor = Array.isArray(suppliers)
        ? (suppliers.find((s) => s?.id === vid) || suppliers.find((s) => s?.name === vid) || null)
        : null;

      let docs = docsByIdRes?.data?.records || [];
      // Fallback — if the record was staged with vendor_name only (no
      // vendor_id) we look it up by the matched supplier name.
      if (docs.length === 0 && vendor?.name) {
        const byName = await axios.get(`${API}/employee-records/records`, {
          headers: adminHeaders(),
          params: { entity_kind: "vendor", vendor_name: vendor.name, limit: 200 },
        }).catch(() => null);
        docs = byName?.data?.records || [];
      }

      setState({ loading: false, err: "", vendor, docs });
    } catch (e) {
      setState((s) => ({
        ...s,
        loading: false,
        err: operationalError(e, "Could not load vendor thread."),
      }));
    }
  }, [vid]);

  useEffect(() => { if (allowed) load(); }, [allowed, load]);

  const mission = useMemo(
    () => missionAdapter({ vendor: state.vendor, docs: state.docs, vendorId: vid }),
    [state.vendor, state.docs, vid]
  );
  const attentionItems = useMemo(
    () => attentionAdapter({ vendor: state.vendor, docs: state.docs }),
    [state.vendor, state.docs]
  );
  const actionQueue = useMemo(
    () => actionQueueAdapter({ vendor: state.vendor, docs: state.docs }),
    [state.vendor, state.docs]
  );
  const timelineEvents = useMemo(
    () => timelineAdapter({ docs: state.docs }),
    [state.docs]
  );
  const relationships = useMemo(() => ({
    subject: {
      id: `vendor-${vid}`,
      kind: "asset",
      label: state.vendor?.name || vid || "—",
      sublabel: "Vendor / supplier",
    },
    edges: relationshipAdapter({ vendor: state.vendor, docs: state.docs, vendorId: vid }),
  }), [vid, state.vendor, state.docs]);
  const documents = useMemo(
    () => documentsAdapter({ docs: state.docs }),
    [state.docs]
  );

  if (!allowed) return <AccessDenied attemptedPortal="admin" />;

  return (
    <AdminRouteShell
      pageTitle="Vendor Thread"
      subtitle="Supplier record, document posture, and operational follow-up in one Admin workspace."
      portalRole="Admin · Vendor Intelligence"
      crumbs={[
        { label: "Equipment & Assets", href: "/admin/equipment" },
        { label: state.vendor?.name || vid || "Vendor Thread" },
      ]}
      contentClassName="px-0 py-0"
      testId="admin-vendor-thread-shell"
    >
      <div className="min-h-screen bg-slate-100" data-testid="admin-vendor-thread-page">
      <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <div>
          <div
            className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500"
            data-testid="admin-vendor-thread-header"
          >
            Vendor Thread · HR/Admin
          </div>
          <div className="font-mono text-xs uppercase tracking-widest text-slate-900">
            {state.vendor?.name || vid || "—"}
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {/* Track 19.60 amendment · HR/Admin edit action. */}
          <button
            type="button"
            onClick={startEdit}
            data-testid="admin-vendor-thread-edit-button"
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-emerald-400 bg-emerald-50 text-sm font-semibold text-emerald-900 hover:bg-emerald-100"
          >
            Edit vendor
          </button>
          <Link
            to={`/hr/historical-records/intake?entity_kind=vendor&vendor_id=${encodeURIComponent(vid)}`}
            data-testid="admin-vendor-thread-upload-link"
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-800 hover:bg-slate-50"
          >
            Add vendor document
          </Link>
          <Link
            to="/hr/historical-records/queue"
            data-testid="admin-vendor-thread-queue-link"
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-800 hover:bg-slate-50"
          >
            Vendor queue
          </Link>
          <Link
            to="/admin"
            data-testid="admin-vendor-thread-master-link"
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-300 bg-white text-sm font-semibold text-slate-800 hover:bg-slate-50"
          >
            Supplier master
          </Link>
        </div>
      </header>

      <main className="pb-8">
        {/* Track 19.60 amendment · HR/Admin inline edit panel. */}
        {editing && (
          <div className="max-w-5xl mx-auto my-4 px-4" data-testid="admin-vendor-thread-edit-panel">
            <div className="rounded-xl border-2 border-emerald-300 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-800">Edit vendor · HR / Admin</div>
                <div className="flex gap-2">
                  <button type="button" onClick={cancelEdit} disabled={saving}
                          data-testid="admin-vendor-thread-edit-cancel"
                          className="h-8 px-3 text-xs font-semibold rounded-md border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-50">
                    Cancel
                  </button>
                  <button type="button" onClick={saveEdit} disabled={saving}
                          data-testid="admin-vendor-thread-edit-save"
                          className="h-8 px-3 text-xs font-semibold rounded-md border border-emerald-500 bg-emerald-500 text-white hover:bg-emerald-600 disabled:opacity-50">
                    {saving ? "Saving…" : "Save vendor"}
                  </button>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  ["name",            "Legal name (required)"],
                  ["display_name",    "Display name"],
                  ["dba",             "DBA / trade name"],
                  ["vendor_type",     "Vendor type / category"],
                  ["primary_contact", "Primary contact"],
                  ["phone",           "Phone"],
                  ["email",           "Email"],
                  ["address",         "Address"],
                ].map(([key, label]) => (
                  <label key={key} className="text-xs text-slate-600 font-mono uppercase tracking-widest">
                    {label}
                    <input
                      type="text"
                      value={form[key] || ""}
                      onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                      data-testid={`admin-vendor-thread-edit-${key}`}
                      className="mt-1 w-full px-2 py-1.5 text-sm font-mono border-2 border-slate-300 rounded focus:outline-none focus:border-emerald-500"
                    />
                  </label>
                ))}
                <label className="text-xs text-slate-600 font-mono uppercase tracking-widest sm:col-span-2">
                  Notes
                  <textarea
                    value={form.notes || ""}
                    onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                    data-testid="admin-vendor-thread-edit-notes"
                    rows={2}
                    className="mt-1 w-full px-2 py-1.5 text-sm font-mono border-2 border-slate-300 rounded focus:outline-none focus:border-emerald-500"
                  />
                </label>
                <label className="text-xs text-slate-700 font-mono flex items-center gap-2">
                  <input type="checkbox" checked={form.is_active !== false}
                         onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                         data-testid="admin-vendor-thread-edit-is-active" />
                  Active
                </label>
                <label className="text-xs text-slate-700 font-mono flex items-center gap-2">
                  <input type="checkbox" checked={!!form.do_not_use}
                         onChange={(e) => setForm((f) => ({ ...f, do_not_use: e.target.checked }))}
                         data-testid="admin-vendor-thread-edit-do-not-use" />
                  Do-not-use flag
                </label>
              </div>
            </div>
          </div>
        )}
        {state.loading && !state.vendor ? (
          <div
            data-testid="admin-vendor-thread-loading"
            className="max-w-5xl mx-auto px-4 py-8 text-sm font-mono uppercase tracking-widest text-slate-500"
          >
            Loading vendor thread…
          </div>
        ) : state.err ? (
          <div
            data-testid="admin-vendor-thread-error"
            className="max-w-5xl mx-auto my-6 bg-rose-50 border border-rose-300 rounded-md p-4 text-sm text-rose-900"
          >
            {state.err}
          </div>
        ) : (
          <OperationalThreadPage
            testId="admin-vendor-thread"
            mission={mission}
            attention={{ items: attentionItems }}
            guidanceProduct={null}
            timelineEvents={timelineEvents}
            timelineTitle="Vendor timeline · newest first · read-only"
            relationships={relationships}
            documents={documents}
            oiProduct={null}
            actionQueue={actionQueue}
            // Photos / OI / History / Audit render honest-empty here.
            // Vendors do not have photos. No vendor OI product exists.
            // History and audit live in the Historical Records queue.
          />
        )}
      </main>
      </div>
    </AdminRouteShell>
  );
}
