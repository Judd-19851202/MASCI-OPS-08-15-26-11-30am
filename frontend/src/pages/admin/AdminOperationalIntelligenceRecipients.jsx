// AdminOperationalIntelligenceRecipients.jsx — Track 19.48.
// Dedicated admin CRUD surface for Operational Intelligence recipients
// and groups. Consumes existing Track 19.45A endpoints — zero drift,
// no duplicate recipient system, no live-send path from this page.
//
// Route: /admin/operational-intelligence/recipients
// Gate:  admin-only (shared A(...) wrapper in App.js)
// Endpoints consumed:
//   GET    /api/operational-intelligence/recipients
//   POST   /api/operational-intelligence/recipients
//   PATCH  /api/operational-intelligence/recipients/{id}
//   DELETE /api/operational-intelligence/recipients/{id}   (soft deactivate)
//   GET    /api/operational-intelligence/groups
//   GET    /api/operational-intelligence/products          (product list)

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Users, UserPlus, Pencil, ShieldCheck, RotateCcw, Ban, Loader2,
  RefreshCcw, ArrowLeft, Info, AlertTriangle, Search, X,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";

function StatusChip({ active }) {
  return (
    <span
      data-testid={active ? "oi-recipient-status-active" : "oi-recipient-status-inactive"}
      className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] font-semibold ${
        active
          ? "bg-emerald-100 text-emerald-800 border-emerald-300"
          : "bg-slate-100 text-slate-600 border-slate-300"
      }`}
    >
      {active ? "Active" : "Inactive"}
    </span>
  );
}

function SummaryStrip({ recipients, groups }) {
  const totals = useMemo(() => {
    const total = recipients.length;
    const active = recipients.filter((r) => r.active).length;
    const inactive = total - active;
    const products = new Set(recipients.map((r) => r.digest_type).filter(Boolean));
    return { total, active, inactive, groups: groups.length, products: products.size };
  }, [recipients, groups]);
  return (
    <div
      data-testid="oi-recipients-summary-strip"
      className="grid grid-cols-2 md:grid-cols-5 gap-3 rounded-lg border bg-white p-4 shadow-sm"
    >
      <Stat label="Total recipients"   value={totals.total} testid="oi-summary-total" />
      <Stat label="Active"             value={totals.active}   tone="emerald" testid="oi-summary-active" />
      <Stat label="Inactive"           value={totals.inactive} tone="slate"   testid="oi-summary-inactive" />
      <Stat label="Groups"             value={totals.groups}                  testid="oi-summary-groups" />
      <Stat label="Products represented" value={totals.products}              testid="oi-summary-products" />
    </div>
  );
}

function Stat({ label, value, tone, testid }) {
  const cls =
    tone === "emerald" ? "text-emerald-700" :
    tone === "slate"   ? "text-slate-500"   :
                         "text-slate-900";
  return (
    <div className="rounded-md bg-slate-50 border p-2" data-testid={testid}>
      <div className="text-[10px] font-semibold tracking-wider text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${cls}`}>{value}</div>
    </div>
  );
}

function RecipientForm({ initial, products, onCancel, onSubmit, saving }) {
  const [form, setForm] = useState({
    email: "", display_name: "", role_label: "",
    department: "", notes: "", digest_type: "",
    active: true, ...(initial || {}),
  });
  const isEdit = !!initial?.id;
  const emailInvalid = form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email);
  const disableSubmit = !form.email || !form.digest_type || emailInvalid;
  return (
    <form
      data-testid={isEdit ? "oi-recipient-edit-form" : "oi-recipient-add-form"}
      className="grid grid-cols-1 md:grid-cols-2 gap-3 p-4 border rounded-lg bg-white shadow-sm"
      onSubmit={(e) => { e.preventDefault(); onSubmit(form); }}
    >
      <div>
        <Label>Email</Label>
        <Input
          type="email" required value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          data-testid="oi-recipient-email-input"
          aria-invalid={emailInvalid ? "true" : "false"}
        />
        {emailInvalid && (
          <div className="text-xs text-red-700 mt-1" data-testid="oi-recipient-email-error">
            Enter a valid email address.
          </div>
        )}
      </div>
      <div>
        <Label>Display name</Label>
        <Input value={form.display_name}
               onChange={(e) => setForm({ ...form, display_name: e.target.value })}
               data-testid="oi-recipient-display-name-input" />
      </div>
      <div>
        <Label>Role label</Label>
        <Input value={form.role_label}
               onChange={(e) => setForm({ ...form, role_label: e.target.value })}
               data-testid="oi-recipient-role-input" />
      </div>
      <div>
        <Label>Department</Label>
        <Input value={form.department}
               onChange={(e) => setForm({ ...form, department: e.target.value })}
               data-testid="oi-recipient-department-input" />
      </div>
      <div>
        <Label>Digest / product</Label>
        <select
          value={form.digest_type}
          onChange={(e) => setForm({ ...form, digest_type: e.target.value })}
          className="w-full mt-1 border rounded px-2 py-1.5 text-sm bg-white"
          data-testid="oi-recipient-digest-select"
          required
        >
          <option value="">— Select product —</option>
          {products.map((p) => (
            <option key={p.product_id} value={p.product_id}>
              {p.display_name} ({p.product_id})
            </option>
          ))}
        </select>
      </div>
      <div>
        <Label>Notes</Label>
        <Input value={form.notes}
               onChange={(e) => setForm({ ...form, notes: e.target.value })}
               data-testid="oi-recipient-notes-input" />
      </div>
      <div className="md:col-span-2 flex items-center gap-2">
        <input type="checkbox" id="active"
               checked={!!form.active}
               onChange={(e) => setForm({ ...form, active: e.target.checked })}
               data-testid="oi-recipient-active-checkbox" />
        <Label htmlFor="active">Active</Label>
      </div>
      <div className="md:col-span-2 flex justify-end gap-2 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}
                data-testid="oi-recipient-form-cancel">
          Cancel
        </Button>
        <Button type="submit" disabled={disableSubmit || saving}
                data-testid="oi-recipient-form-submit">
          {saving ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
          {isEdit ? "Save changes" : "Add recipient"}
        </Button>
      </div>
    </form>
  );
}

export default function AdminOperationalIntelligenceRecipients() {
  const [recipients, setRecipients] = useState([]);
  const [groups, setGroups] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [productFilter, setProductFilter] = useState("");
  const [activeOnly, setActiveOnly] = useState(false);

  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [r, g, p] = await Promise.all([
        api.get("/operational-intelligence/recipients", { params: { limit: 500 } }),
        api.get("/operational-intelligence/groups"),
        api.get("/operational-intelligence/products"),
      ]);
      setRecipients(r.data?.recipients || []);
      setGroups(g.data?.groups || []);
      setProducts(p.data?.products || []);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load recipient data"));
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const submitAdd = async (form) => {
    setSaving(true);
    try {
      await api.post("/operational-intelligence/recipients", form);
      toast.success(`Recipient ${form.email} added`);
      setShowAdd(false);
      await load();
    } catch (e) {
      toast.error(operationalError(e, "Add recipient failed"));
    } finally { setSaving(false); }
  };

  const submitEdit = async (form) => {
    setSaving(true);
    try {
      await api.patch(`/operational-intelligence/recipients/${editing.id}`, form);
      toast.success(`Recipient ${form.email} updated`);
      setEditing(null);
      await load();
    } catch (e) {
      toast.error(operationalError(e, "Update recipient failed"));
    } finally { setSaving(false); }
  };

  const deactivate = async (r) => {
    if (!window.confirm(`Deactivate ${r.email}? They will stop receiving digests but the record is preserved for regulatory replay.`))
      return;
    try {
      await api.delete(`/operational-intelligence/recipients/${r.id}`);
      toast.success(`Recipient ${r.email} deactivated`);
      await load();
    } catch (e) {
      toast.error(operationalError(e, "Deactivate failed"));
    }
  };

  const reactivate = async (r) => {
    try {
      await api.patch(`/operational-intelligence/recipients/${r.id}`, { active: true });
      toast.success(`Recipient ${r.email} reactivated`);
      await load();
    } catch (e) {
      toast.error(operationalError(e, "Reactivate failed"));
    }
  };

  const filteredRecipients = useMemo(() => {
    let out = recipients;
    if (activeOnly) out = out.filter((r) => r.active);
    if (productFilter) out = out.filter((r) => r.digest_type === productFilter);
    if (search.trim()) {
      const s = search.trim().toLowerCase();
      out = out.filter((r) =>
        (r.email || "").toLowerCase().includes(s) ||
        (r.display_name || "").toLowerCase().includes(s) ||
        (r.role_label || "").toLowerCase().includes(s));
    }
    return out;
  }, [recipients, activeOnly, productFilter, search]);

  return (
    <AdminShell
      title="Operational Intelligence Recipients"
      section="operational-intelligence"
    >
      <div className="p-4 space-y-4"
           data-testid="admin-operational-intelligence-recipients">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Users className="h-5 w-5 text-slate-700" />
              Operational Intelligence Recipients
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Manage who receives intelligence digests and briefings. Recipient
              changes affect future scheduled sends only. This page does not
              send email.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/admin/operational-intelligence"
              className="inline-flex items-center gap-1 text-xs text-slate-700 hover:text-slate-900 underline"
              data-testid="oi-recipients-back-to-cockpit"
            >
              <ArrowLeft className="h-3 w-3" /> Back to Cockpit
            </Link>
            <Button size="sm" variant="outline" onClick={load}
                    data-testid="oi-recipients-refresh">
              <RefreshCcw className="h-3 w-3 mr-1" /> Refresh
            </Button>
            <Button size="sm" onClick={() => { setShowAdd(true); setEditing(null); }}
                    data-testid="oi-recipients-add-btn">
              <UserPlus className="h-3 w-3 mr-1" /> Add recipient
            </Button>
          </div>
        </div>

        <div
          className="rounded-lg border-l-4 border-emerald-500 bg-emerald-50 p-3 text-xs text-emerald-900 flex items-start gap-2"
          data-testid="oi-recipients-dry-run-notice"
        >
          <ShieldCheck className="h-4 w-4 mt-0.5" />
          <div>
            <span className="font-semibold">Dry-run safety:</span>{" "}
            Managing recipients does not send email. Live sends remain
            controlled by the scheduled digest workflow. Deactivation is
            preferred over deletion for regulatory replay.
          </div>
        </div>

        {loading ? (
          <div className="p-6 text-slate-500 flex items-center gap-2"
               data-testid="oi-recipients-loading">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading…
          </div>
        ) : (
          <>
            <SummaryStrip recipients={recipients} groups={groups} />

            {(showAdd || editing) && (
              <RecipientForm
                initial={editing}
                products={products}
                saving={saving}
                onCancel={() => { setShowAdd(false); setEditing(null); }}
                onSubmit={editing ? submitEdit : submitAdd}
              />
            )}

            {/* Filters */}
            <div className="flex flex-wrap items-center gap-2 border rounded-lg bg-white p-2 shadow-sm">
              <div className="flex items-center gap-1 flex-1 min-w-[220px]">
                <Search className="h-3 w-3 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search email / name / role…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="text-sm border-0 outline-0 w-full py-1"
                  data-testid="oi-recipients-search-input"
                />
              </div>
              <select
                value={productFilter}
                onChange={(e) => setProductFilter(e.target.value)}
                className="text-sm border rounded px-2 py-1 bg-white"
                data-testid="oi-recipients-product-filter"
              >
                <option value="">All products</option>
                {products.map((p) => (
                  <option key={p.product_id} value={p.product_id}>
                    {p.display_name}
                  </option>
                ))}
              </select>
              <label className="text-xs text-slate-700 flex items-center gap-1"
                     data-testid="oi-recipients-active-filter-label">
                <input type="checkbox" checked={activeOnly}
                       onChange={(e) => setActiveOnly(e.target.checked)}
                       data-testid="oi-recipients-active-filter" />
                Active only
              </label>
            </div>

            {/* Table */}
            <div className="rounded-lg border bg-white shadow-sm overflow-auto">
              <table className="w-full text-xs" data-testid="oi-recipients-table">
                <thead>
                  <tr className="bg-slate-100">
                    <Th>Email</Th>
                    <Th>Display name</Th>
                    <Th>Role</Th>
                    <Th>Product</Th>
                    <Th>Status</Th>
                    <Th>Updated</Th>
                    <Th>Notes</Th>
                    <Th align="right">Actions</Th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRecipients.length === 0 && (
                    <tr>
                      <td colSpan={8} className="p-4 text-center text-slate-500 italic"
                          data-testid="oi-recipients-empty">
                        No recipients match the current filters.
                      </td>
                    </tr>
                  )}
                  {filteredRecipients.map((r) => (
                    <tr key={r.id}
                        data-testid={`oi-recipient-row-${r.id}`}
                        className="border-t hover:bg-slate-50 align-top">
                      <Td className="font-mono">{r.email}</Td>
                      <Td>{r.display_name || "—"}</Td>
                      <Td>{r.role_label || "—"}</Td>
                      <Td>{r.digest_type || "—"}</Td>
                      <Td><StatusChip active={!!r.active} /></Td>
                      <Td>{r.updated_at ? new Date(r.updated_at).toLocaleString() : "—"}</Td>
                      <Td className="max-w-[240px] truncate" title={r.notes || ""}>{r.notes || "—"}</Td>
                      <Td align="right">
                        <div className="flex justify-end gap-1">
                          <Button size="sm" variant="ghost"
                                  onClick={() => { setEditing(r); setShowAdd(false); }}
                                  data-testid={`oi-recipient-edit-btn-${r.id}`}>
                            <Pencil className="h-3 w-3 mr-1" /> Edit
                          </Button>
                          {r.active ? (
                            <Button size="sm" variant="ghost"
                                    onClick={() => deactivate(r)}
                                    data-testid={`oi-recipient-deactivate-btn-${r.id}`}>
                              <Ban className="h-3 w-3 mr-1" /> Deactivate
                            </Button>
                          ) : (
                            <Button size="sm" variant="ghost"
                                    onClick={() => reactivate(r)}
                                    data-testid={`oi-recipient-reactivate-btn-${r.id}`}>
                              <RotateCcw className="h-3 w-3 mr-1" /> Reactivate
                            </Button>
                          )}
                        </div>
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Groups panel */}
            <div className="rounded-lg border bg-white shadow-sm p-3"
                 data-testid="oi-groups-panel">
              <div className="flex items-center justify-between mb-2">
                <div className="font-semibold text-slate-900">Recipient Groups</div>
                <div className="text-[11px] text-slate-500">
                  Group creation is served by the Track 19.45A admin API.
                  A dedicated group-membership editor is deferred.
                </div>
              </div>
              {groups.length === 0 ? (
                <div className="text-xs text-slate-500 italic p-2"
                     data-testid="oi-groups-empty">
                  No groups defined yet.
                </div>
              ) : (
                <table className="w-full text-xs" data-testid="oi-groups-table">
                  <thead>
                    <tr className="bg-slate-100">
                      <Th>Group ID</Th>
                      <Th>Name</Th>
                      <Th>Products</Th>
                      <Th>Members</Th>
                      <Th>Created</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {groups.map((g) => (
                      <tr key={g.group_id || g.id} className="border-t align-top"
                          data-testid={`oi-group-row-${g.group_id || g.id}`}>
                        <Td className="font-mono">{g.group_id || "—"}</Td>
                        <Td>{g.group_name || "—"}</Td>
                        <Td>{(g.products || []).join(", ") || "—"}</Td>
                        <Td>{(g.members || []).length}</Td>
                        <Td>{g.created_at ? new Date(g.created_at).toLocaleString() : "—"}</Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="rounded-lg border bg-slate-50 p-3 text-xs text-slate-700 flex items-start gap-2"
                 data-testid="oi-recipients-governance-note">
              <Info className="h-4 w-4 mt-0.5 text-slate-500" />
              <div>
                <div className="font-semibold text-slate-900">Governance</div>
                Recipient changes affect future scheduled sends. Dry-runs
                remain safe — this page cannot trigger live email. Deactivation
                is preferred over deletion to preserve the regulatory replay
                trail. All mutations are captured in the shared Operational
                Intelligence audit collection.
              </div>
            </div>
          </>
        )}
      </div>
    </AdminShell>
  );
}

function Th({ children, align }) {
  return (
    <th
      className={`border p-2 font-semibold text-slate-700 uppercase tracking-wider text-[10px] ${align === "right" ? "text-right" : "text-left"}`}
    >
      {children}
    </th>
  );
}
function Td({ children, className, align }) {
  return (
    <td
      className={`border p-2 text-slate-900 ${align === "right" ? "text-right" : ""} ${className || ""}`}
    >
      {children}
    </td>
  );
}
