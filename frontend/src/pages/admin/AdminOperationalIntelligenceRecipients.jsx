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
  Upload, Copy, Plus, UserCog,
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
              {`${p.display_name} (${p.product_id})`}
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

function BulkImportPanel({ products, onClose, onImported, defaultProductId, existingRecipients }) {
  const [mode, setMode] = useState("directory");    // "directory" | "paste" | "copy"
  const [productId, setProductId] = useState(defaultProductId || "");
  const [rawText, setRawText] = useState("");
  const [copySource, setCopySource] = useState("");
  const [active, setActive] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  // Directory-picker state.
  const [dirQuery, setDirQuery] = useState("");
  const [dirPortal, setDirPortal] = useState("");
  const [dirUsers, setDirUsers] = useState([]);
  const [dirLoading, setDirLoading] = useState(false);
  const [dirSelected, setDirSelected] = useState({}); // { userId: {email,name,role,source_id} }

  // Emails already subscribed to the target product — for dedupe hinting.
  const existingForTarget = useMemo(() => {
    const s = new Set();
    for (const r of (existingRecipients || [])) {
      if (r.digest_type === productId && r.email) {
        s.add(r.email.toLowerCase());
      }
    }
    return s;
  }, [existingRecipients, productId]);

  // Live search against the canonical platform directory
  // (`/admin/directory/k4/users`). Read-only; no HR / user mutations.
  useEffect(() => {
    if (mode !== "directory") return;
    let cancelled = false;
    const t = setTimeout(async () => {
      setDirLoading(true);
      try {
        const r = await api.get("/admin/directory/k4/users", {
          params: {
            q: dirQuery || undefined,
            portal: dirPortal || undefined,
            disabled: false,
            limit: 100,
          },
        });
        if (!cancelled) setDirUsers(r.data?.users || []);
      } catch (e) {
        if (!cancelled) toast.error(operationalError(e, "Directory search failed"));
      } finally {
        if (!cancelled) setDirLoading(false);
      }
    }, 220);
    return () => { cancelled = true; clearTimeout(t); };
  }, [mode, dirQuery, dirPortal]);

  const toggleDirUser = (u) => {
    setDirSelected((prev) => {
      const next = { ...prev };
      if (next[u.id]) delete next[u.id];
      else next[u.id] = {
        email: (u.email || "").toLowerCase(),
        display_name: u.name || "",
        role_label: `directory · ${(u.portals || []).join("/") || "user"}${u.is_super_admin ? " · super_admin" : ""}`,
        source_reference: u.id,
      };
      return next;
    });
  };

  const submitDirectory = async () => {
    setSubmitting(true);
    setResult(null);
    try {
      const rows = Object.values(dirSelected).map((s) => ({
        email: s.email,
        display_name: s.display_name,
        role_label: s.role_label,
        notes: `Sourced from platform directory (user_id: ${s.source_reference})`,
        digest_type: productId,
        active: true,
      }));
      if (rows.length === 0) {
        toast.error("Select at least one person.");
        setSubmitting(false);
        return;
      }
      const r = await api.post(
        "/operational-intelligence/recipients/bulk-import",
        { rows, default_product_id: productId },
      );
      setResult(r.data);
      toast.success(`Directory import: ${r.data.inserted} added · ${r.data.duplicate} already existed · ${r.data.skipped} skipped`);
      setDirSelected({});
      onImported?.();
    } catch (e) {
      const msg = operationalError(e, "Directory import failed");
      setResult({ error: msg });
      toast.error(msg);
    } finally { setSubmitting(false); }
  };

  const parsedRows = useMemo(() => {
    if (mode !== "paste") return [];
    const emailRe = /^[^\s@,;]+@[^\s@,;]+\.[^\s@,;]+$/;
    return rawText
      .split(/[\n,;]+/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        // Support "Name <email@x>" and "email,role,name" and plain email.
        const angle = line.match(/<([^>]+)>/);
        const email = (angle ? angle[1] : line.split(",")[0] || line).trim().toLowerCase();
        const parts = line.includes(",") ? line.split(",").map((s) => s.trim()) : [];
        const displayName = angle ? line.split("<")[0].trim() : (parts[2] || "");
        const roleLabel = parts[1] || "";
        return {
          email,
          display_name: displayName,
          role_label: roleLabel,
          digest_type: productId,
          active,
          valid: emailRe.test(email),
        };
      });
  }, [rawText, productId, active, mode]);

  const validRows = parsedRows.filter((r) => r.valid);
  const invalidRows = parsedRows.filter((r) => !r.valid);

  const canPasteSubmit = mode === "paste" && productId && validRows.length > 0 && !submitting;
  const canCopySubmit = mode === "copy" && productId && copySource && copySource !== productId && !submitting;

  const submitPaste = async () => {
    setSubmitting(true);
    setResult(null);
    try {
      const rows = validRows.map(({ valid, ...r }) => r);
      const r = await api.post(
        "/operational-intelligence/recipients/bulk-import",
        { rows, default_product_id: productId },
      );
      setResult(r.data);
      toast.success(`Bulk import: ${r.data.inserted} inserted · ${r.data.duplicate} duplicate · ${r.data.skipped} skipped`);
      onImported?.();
    } catch (e) {
      const msg = operationalError(e, "Bulk import failed");
      setResult({ error: msg });
      toast.error(msg);
    } finally { setSubmitting(false); }
  };

  const submitCopy = async () => {
    setSubmitting(true);
    setResult(null);
    try {
      const src = await api.get("/operational-intelligence/recipients", {
        params: { product_id: copySource, active_only: true, limit: 500 },
      });
      const srcRows = (src.data?.recipients || [])
        .filter((r) => r.active)
        .map((r) => ({
          email: r.email,
          display_name: r.display_name || "",
          role_label: r.role_label || "",
          department: r.department || "",
          notes: `Copied from ${copySource}${r.notes ? " · " + r.notes : ""}`,
          digest_type: productId,
          active: true,
        }));
      if (srcRows.length === 0) {
        setResult({ error: "Source product has no active recipients to copy." });
        toast.error("Source product has no active recipients to copy.");
        setSubmitting(false);
        return;
      }
      const r = await api.post(
        "/operational-intelligence/recipients/bulk-import",
        { rows: srcRows, default_product_id: productId },
      );
      setResult({ ...r.data, source_total: srcRows.length });
      toast.success(`Copied ${r.data.inserted} recipient(s) from ${copySource} → ${productId} (${r.data.duplicate} already existed)`);
      onImported?.();
    } catch (e) {
      const msg = operationalError(e, "Copy from product failed");
      setResult({ error: msg });
      toast.error(msg);
    } finally { setSubmitting(false); }
  };

  return (
    <div className="rounded-lg border bg-white shadow-sm p-4 space-y-3"
         data-testid="oi-bulk-import-panel">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Upload className="h-4 w-4 text-slate-700" />
          <span className="font-semibold text-slate-900">Bulk recipient management</span>
        </div>
        <Button size="sm" variant="ghost" onClick={onClose}
                data-testid="oi-bulk-close">
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex gap-1 border-b" data-testid="oi-bulk-tabs">
        <button
          className={`px-3 py-1 text-xs border-b-2 ${mode === "directory" ? "border-slate-900 font-semibold text-slate-900" : "border-transparent text-slate-500"}`}
          onClick={() => { setMode("directory"); setResult(null); }}
          data-testid="oi-bulk-tab-directory"
        >
          <Users className="h-3 w-3 inline mr-1" /> From platform directory
        </button>
        <button
          className={`px-3 py-1 text-xs border-b-2 ${mode === "paste" ? "border-slate-900 font-semibold text-slate-900" : "border-transparent text-slate-500"}`}
          onClick={() => { setMode("paste"); setResult(null); }}
          data-testid="oi-bulk-tab-paste"
        >
          <Upload className="h-3 w-3 inline mr-1" /> Paste email list
        </button>
        <button
          className={`px-3 py-1 text-xs border-b-2 ${mode === "copy" ? "border-slate-900 font-semibold text-slate-900" : "border-transparent text-slate-500"}`}
          onClick={() => { setMode("copy"); setResult(null); }}
          data-testid="oi-bulk-tab-copy"
        >
          <Copy className="h-3 w-3 inline mr-1" /> Copy from another product
        </button>
      </div>

      <div className="text-[11px] text-emerald-800 bg-emerald-50 border border-emerald-200 rounded p-2 flex items-start gap-2"
           data-testid="oi-bulk-safety-note">
        <ShieldCheck className="h-3 w-3 mt-0.5" />
        <span>
          Bulk operations <strong>do not send email</strong> and <strong>do not
          mutate HR or platform-user records</strong>. Duplicates are skipped
          by <code>(email, product)</code>. Invalid emails are shown for
          correction before submit. Prefer the <strong>platform directory</strong>
          tab — it uses canonical, already-authorized user emails.
        </span>
      </div>

      <div>
        <Label>Target product</Label>
        <select value={productId}
                onChange={(e) => setProductId(e.target.value)}
                className="w-full mt-1 border rounded px-2 py-1.5 text-sm bg-white"
                data-testid="oi-bulk-target-product">
          <option value="">— Select target product —</option>
          {products.map((p) => (
            <option key={p.product_id} value={p.product_id}>
              {`${p.display_name} (${p.product_id})`}
            </option>
          ))}
        </select>
      </div>

      {mode === "directory" && (
        <>
          <div className="flex flex-wrap gap-2 items-center">
            <div className="flex items-center gap-1 flex-1 min-w-[220px] border rounded px-2 py-1">
              <Search className="h-3 w-3 text-slate-500" />
              <input
                type="text"
                placeholder="Search by name or email…"
                value={dirQuery}
                onChange={(e) => setDirQuery(e.target.value)}
                className="text-sm border-0 outline-0 w-full py-1 bg-transparent"
                data-testid="oi-directory-search-input"
              />
            </div>
            <select value={dirPortal}
                    onChange={(e) => setDirPortal(e.target.value)}
                    className="text-sm border rounded px-2 py-1 bg-white"
                    data-testid="oi-directory-portal-filter">
              <option value="">All portals</option>
              {["admin","safety","pm","field","shop","hr","dispatch"].map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            <span className="text-[11px] text-slate-500" data-testid="oi-directory-count">
              {dirLoading ? "searching…" : `${dirUsers.length} found`}
            </span>
            <span className="text-[11px] text-emerald-700"
                  data-testid="oi-directory-selected-count">
              · {Object.keys(dirSelected).length} selected
            </span>
          </div>

          <div className="overflow-auto max-h-[300px] border rounded"
               data-testid="oi-directory-picker-list">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-slate-100">
                <tr>
                  <Th></Th>
                  <Th>Name</Th>
                  <Th>Email</Th>
                  <Th>Portals</Th>
                  <Th>Source</Th>
                </tr>
              </thead>
              <tbody>
                {dirUsers.length === 0 && !dirLoading && (
                  <tr>
                    <td colSpan={5} className="p-3 text-center text-slate-500 italic"
                        data-testid="oi-directory-empty">
                      No platform users match this search.
                    </td>
                  </tr>
                )}
                {dirUsers.map((u) => {
                  const already = existingForTarget.has((u.email || "").toLowerCase());
                  const selected = !!dirSelected[u.id];
                  return (
                    <tr key={u.id}
                        className={`border-t align-top ${selected ? "bg-emerald-50" : "hover:bg-slate-50"} ${already ? "opacity-60" : ""}`}
                        data-testid={`oi-directory-row-${u.id}`}>
                      <Td>
                        <input type="checkbox"
                               checked={selected}
                               disabled={already || !u.email}
                               onChange={() => toggleDirUser(u)}
                               data-testid={`oi-directory-check-${u.id}`} />
                      </Td>
                      <Td>{u.name || "—"}{u.is_super_admin ? " ★" : ""}</Td>
                      <Td className="font-mono">{u.email || <span className="italic text-slate-400">no email</span>}</Td>
                      <Td>{(u.portals || []).join(", ") || "—"}</Td>
                      <Td>
                        {already
                          ? <span className="text-slate-500 italic">already subscribed</span>
                          : (u.mirrored ? "mirrored" : "managed")}
                      </Td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="text-[11px] text-slate-600">
            <span className="font-semibold">Source:</span> canonical platform
            user directory (<code>/api/admin/directory/k4/users</code>).
            This picker reads directory records only — it never creates or
            mutates platform user accounts or HR employee data.
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose} disabled={submitting}
                    data-testid="oi-directory-cancel">
              Cancel
            </Button>
            <Button
              disabled={!productId || Object.keys(dirSelected).length === 0 || submitting}
              onClick={submitDirectory}
              data-testid="oi-directory-submit">
              {submitting ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> :
                            <UserPlus className="h-3 w-3 mr-1" />}
              Add {Object.keys(dirSelected).length} selected
            </Button>
          </div>
        </>
      )}

      {mode === "paste" && (
        <>
          <div>
            <Label>Emails (one per line, comma-separated, or &quot;Name &lt;email&gt;&quot;)</Label>
            <textarea
              className="w-full mt-1 border rounded px-2 py-2 text-xs font-mono min-h-[140px]"
              placeholder={"alice@masci.com\nbob@masci.com, Field Ops, Bob Jones\nCarol Judd <carol@masci.com>"}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              data-testid="oi-bulk-paste-textarea"
            />
          </div>
          <label className="text-xs text-slate-700 flex items-center gap-1">
            <input type="checkbox" checked={active}
                   onChange={(e) => setActive(e.target.checked)}
                   data-testid="oi-bulk-active-checkbox" />
            Active on creation
          </label>
          {parsedRows.length > 0 && (
            <div className="text-xs text-slate-700 bg-slate-50 border rounded p-2"
                 data-testid="oi-bulk-parse-summary">
              <span className="font-semibold text-slate-900">{parsedRows.length}</span> total ·{" "}
              <span className="text-emerald-700 font-semibold">{validRows.length}</span> valid ·{" "}
              <span className="text-red-700 font-semibold">{invalidRows.length}</span> invalid
              {invalidRows.length > 0 && (
                <div className="mt-1 text-red-800" data-testid="oi-bulk-invalid-list">
                  Invalid: {invalidRows.slice(0, 5).map((r) => r.email).join(", ")}
                  {invalidRows.length > 5 ? "…" : ""}
                </div>
              )}
            </div>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose} disabled={submitting}
                    data-testid="oi-bulk-cancel">
              Cancel
            </Button>
            <Button disabled={!canPasteSubmit} onClick={submitPaste}
                    data-testid="oi-bulk-paste-submit">
              {submitting ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> :
                            <Upload className="h-3 w-3 mr-1" />}
              Import {validRows.length} recipient{validRows.length === 1 ? "" : "s"}
            </Button>
          </div>
        </>
      )}

      {mode === "copy" && (
        <>
          <div>
            <Label>Copy active recipients from</Label>
            <select value={copySource}
                    onChange={(e) => setCopySource(e.target.value)}
                    className="w-full mt-1 border rounded px-2 py-1.5 text-sm bg-white"
                    data-testid="oi-bulk-copy-source">
              <option value="">— Select source product —</option>
              {products.filter((p) => p.product_id !== productId).map((p) => (
                <option key={p.product_id} value={p.product_id}>
                  {`${p.display_name} (${p.product_id})`}
                </option>
              ))}
            </select>
          </div>
          <div className="text-[11px] text-slate-600 bg-slate-50 border rounded p-2">
            Only active recipients are copied. Duplicates
            (<code>email, product</code> already exists) are skipped safely.
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose} disabled={submitting}
                    data-testid="oi-bulk-cancel-copy">
              Cancel
            </Button>
            <Button disabled={!canCopySubmit} onClick={submitCopy}
                    data-testid="oi-bulk-copy-submit">
              {submitting ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> :
                            <Copy className="h-3 w-3 mr-1" />}
              Copy recipients
            </Button>
          </div>
        </>
      )}

      {result && (
        <div className="rounded border p-2 text-xs" data-testid="oi-bulk-result">
          {result.error ? (
            <div className="text-red-800 bg-red-50 border border-red-200 rounded p-2">
              <AlertTriangle className="inline h-3 w-3 mr-1" />
              {result.error}
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-2">
              <Stat label="Inserted" value={result.inserted ?? 0} tone="emerald" testid="oi-bulk-result-inserted" />
              <Stat label="Duplicate (skipped)" value={result.duplicate ?? 0} testid="oi-bulk-result-duplicate" />
              <Stat label="Errors" value={result.skipped ?? 0} tone="slate" testid="oi-bulk-result-errors" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function GroupCreatePanel({ products, onClose, onCreated }) {
  const [groupId, setGroupId] = useState("");
  const [groupName, setGroupName] = useState("");
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (!groupId || !groupName) return;
    setSaving(true);
    try {
      await api.post("/operational-intelligence/groups", {
        group_id: groupId,
        group_name: groupName,
        products: selectedProducts,
      });
      toast.success(`Group ${groupId} created`);
      onCreated?.();
    } catch (e) {
      toast.error(operationalError(e, "Create group failed"));
    } finally { setSaving(false); }
  };

  return (
    <div className="rounded-lg border bg-white shadow-sm p-4 space-y-3"
         data-testid="oi-group-create-panel">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Plus className="h-4 w-4 text-slate-700" />
          <span className="font-semibold text-slate-900">New recipient group</span>
        </div>
        <Button size="sm" variant="ghost" onClick={onClose}
                data-testid="oi-group-create-close">
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <Label>Group ID (lowercase, no spaces)</Label>
          <Input value={groupId}
                 onChange={(e) => setGroupId(e.target.value.toLowerCase().replace(/\s+/g, "-"))}
                 placeholder="e.g. executive_leadership"
                 data-testid="oi-group-create-id" />
        </div>
        <div>
          <Label>Display name</Label>
          <Input value={groupName}
                 onChange={(e) => setGroupName(e.target.value)}
                 placeholder="e.g. Executive Leadership"
                 data-testid="oi-group-create-name" />
        </div>
      </div>
      <div>
        <Label>Subscribed products (multi-select)</Label>
        <select multiple value={selectedProducts}
                onChange={(e) => setSelectedProducts(
                  Array.from(e.target.selectedOptions).map((o) => o.value))}
                className="w-full mt-1 border rounded px-2 py-1.5 text-xs bg-white min-h-[110px]"
                data-testid="oi-group-create-products">
          {products.map((p) => (
            <option key={p.product_id} value={p.product_id}>
              {`${p.display_name} (${p.product_id})`}
            </option>
          ))}
        </select>
        <div className="text-[11px] text-slate-500 mt-1">
          Hold <kbd>Cmd</kbd>/<kbd>Ctrl</kbd> to select multiple.
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose} disabled={saving}
                data-testid="oi-group-create-cancel">
          Cancel
        </Button>
        <Button onClick={submit}
                disabled={!groupId || !groupName || saving}
                data-testid="oi-group-create-submit">
          {saving ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> :
                    <Plus className="h-3 w-3 mr-1" />}
          Create group
        </Button>
      </div>
    </div>
  );
}

function GroupMemberEditor({ group, onClose, onChanged }) {
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [roleLabel, setRoleLabel] = useState("");
  const [active, setActive] = useState(true);
  const [saving, setSaving] = useState(false);
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  const submit = async () => {
    if (!emailRe.test(email)) {
      toast.error("Enter a valid email address.");
      return;
    }
    setSaving(true);
    try {
      await api.post(
        `/operational-intelligence/groups/${group.group_id}/members`,
        { email, display_name: displayName, role_label: roleLabel, active },
      );
      toast.success(`${email} added to ${group.group_id}`);
      setEmail("");
      setDisplayName("");
      setRoleLabel("");
      onChanged?.();
    } catch (e) {
      toast.error(operationalError(e, "Add member failed"));
    } finally { setSaving(false); }
  };

  return (
    <div className="rounded-lg border bg-white shadow-sm p-4 space-y-3"
         data-testid={`oi-group-member-editor-${group.group_id}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <UserCog className="h-4 w-4 text-slate-700" />
          <span className="font-semibold text-slate-900">
            Members · {group.group_name}
          </span>
          <span className="text-[10px] font-mono text-slate-500">({group.group_id})</span>
        </div>
        <Button size="sm" variant="ghost" onClick={onClose}
                data-testid={`oi-group-member-close-${group.group_id}`}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      <div className="text-[11px] text-slate-600 bg-slate-50 border rounded p-2">
        Group is subscribed to:{" "}
        <span className="font-mono">{(group.products || []).join(", ") || "no products"}</span>.
        Every active member of this group receives digests for those products.
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <Label>Email</Label>
          <Input type="email" value={email}
                 onChange={(e) => setEmail(e.target.value)}
                 data-testid={`oi-group-member-email-${group.group_id}`} />
        </div>
        <div>
          <Label>Display name</Label>
          <Input value={displayName}
                 onChange={(e) => setDisplayName(e.target.value)}
                 data-testid={`oi-group-member-name-${group.group_id}`} />
        </div>
        <div>
          <Label>Role label</Label>
          <Input value={roleLabel}
                 onChange={(e) => setRoleLabel(e.target.value)}
                 data-testid={`oi-group-member-role-${group.group_id}`} />
        </div>
      </div>
      <div className="flex items-center justify-between">
        <label className="text-xs text-slate-700 flex items-center gap-1">
          <input type="checkbox" checked={active}
                 onChange={(e) => setActive(e.target.checked)}
                 data-testid={`oi-group-member-active-${group.group_id}`} />
          Active
        </label>
        <Button size="sm" onClick={submit} disabled={saving}
                data-testid={`oi-group-member-submit-${group.group_id}`}>
          {saving ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> :
                    <UserPlus className="h-3 w-3 mr-1" />}
          Add member
        </Button>
      </div>
      {(group.members || []).length > 0 && (
        <div>
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Current members ({(group.members || []).length})
          </div>
          <div className="overflow-auto max-h-[220px] border rounded">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-100">
                  <Th>Email</Th>
                  <Th>Name</Th>
                  <Th>Role</Th>
                  <Th>Active</Th>
                  <Th>Added</Th>
                </tr>
              </thead>
              <tbody>
                {(group.members || []).map((m, i) => (
                  <tr key={i} className="border-t align-top"
                      data-testid={`oi-group-member-row-${group.group_id}-${i}`}>
                    <Td className="font-mono">{m.email}</Td>
                    <Td>{m.display_name || "—"}</Td>
                    <Td>{m.role_label || "—"}</Td>
                    <Td>{m.active ? "yes" : "no"}</Td>
                    <Td>{m.added_at ? new Date(m.added_at).toLocaleDateString() : "—"}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="text-[10px] text-slate-500 mt-1">
            Member removal is not yet exposed via the API — deactivate the individual
            recipient instead, or open a Track 19.49 follow-up.
          </div>
        </div>
      )}
    </div>
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
  const [showBulk, setShowBulk] = useState(false);
  const [showGroupCreate, setShowGroupCreate] = useState(false);
  const [editingGroupMembers, setEditingGroupMembers] = useState(null);
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
            <Button size="sm" variant="outline"
                    onClick={() => { setShowBulk(true); setShowAdd(false); setEditing(null); }}
                    data-testid="oi-recipients-bulk-btn">
              <Upload className="h-3 w-3 mr-1" /> Bulk / Directory
            </Button>
            <Button size="sm" onClick={() => { setShowAdd(true); setEditing(null); setShowBulk(false); }}
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

            {showBulk && (
              <BulkImportPanel
                products={products}
                existingRecipients={recipients}
                onClose={() => setShowBulk(false)}
                onImported={load}
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
                <Button size="sm" variant="outline"
                        onClick={() => setShowGroupCreate(true)}
                        data-testid="oi-groups-create-btn">
                  <Plus className="h-3 w-3 mr-1" /> New group
                </Button>
              </div>
              {showGroupCreate && (
                <div className="mb-3">
                  <GroupCreatePanel
                    products={products}
                    onClose={() => setShowGroupCreate(false)}
                    onCreated={() => { setShowGroupCreate(false); load(); }}
                  />
                </div>
              )}
              {editingGroupMembers && (
                <div className="mb-3">
                  <GroupMemberEditor
                    group={editingGroupMembers}
                    onClose={() => setEditingGroupMembers(null)}
                    onChanged={load}
                  />
                </div>
              )}
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
                      <Th align="right">Actions</Th>
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
                        <Td align="right">
                          <Button size="sm" variant="ghost"
                                  onClick={() => setEditingGroupMembers(g)}
                                  data-testid={`oi-group-members-btn-${g.group_id || g.id}`}>
                            <UserCog className="h-3 w-3 mr-1" /> Members
                          </Button>
                        </Td>
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
