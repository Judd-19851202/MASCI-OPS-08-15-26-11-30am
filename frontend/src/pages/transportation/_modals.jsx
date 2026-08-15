/**
 * TRACK 19.00 · Transportation Driver + Carrier Operations modals.
 *
 *   • LinkHRDriverModal     — picks an eligible HR CDL employee and
 *                             idempotently creates a transport_persons
 *                             shell (kind=masci_employee).
 *   • AddLeasedDriverModal  — creates a transport_persons leased driver
 *                             under a chosen carrier.
 *   • AddCarrierModal       — creates a carrier (legal_name, type, DOT,
 *                             MC, contact).
 *   • EditCarrierModal      — edits a carrier's operational fields.
 *
 * All modals send both X-Admin-Token AND X-Dispatch-Token, so they work
 * for Super Admin and Dispatch users (Track 19.00 policy: dispatcher
 * can create/edit drivers and carriers from inside Transportation
 * Operations — Visible = Usable).
 *
 * HR identity stays HR-owned. The link flow copies a minimal identity
 * snapshot into the operational shell (name, phone, license, CDL
 * class) but never round-trips identity back to HR.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { X, Search, Loader2, UserPlus, Building2, Truck as TruckIcon, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { txGet, txPost, txPatch } from "./_shared";

// ─────────────────────────── Shell ───────────────────────────

function ModalShell({ open, title, subtitle, onClose, children, testid, wide = false }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => { if (e.key === "Escape") onClose?.(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      data-testid={`${testid}-backdrop`}
      onClick={onClose}
    >
      <div
        className={`bg-white rounded-lg shadow-2xl w-full ${wide ? "max-w-3xl" : "max-w-xl"} max-h-[90vh] overflow-hidden flex flex-col`}
        data-testid={testid}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between px-6 py-4 border-b border-slate-200">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
            {subtitle ? <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p> : null}
          </div>
          <button
            type="button"
            className="text-slate-400 hover:text-slate-700 p-1"
            onClick={onClose}
            data-testid={`${testid}-close`}
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-4">{children}</div>
      </div>
    </div>
  );
}

function Field({ label, required, hint, children, testid }) {
  return (
    <div className="space-y-1" data-testid={testid ? `${testid}-field` : undefined}>
      <Label className="text-xs font-medium text-slate-700">
        {label}
        {required ? <span className="text-red-600 ml-0.5">*</span> : null}
      </Label>
      {children}
      {hint ? <p className="text-[11px] text-slate-500">{hint}</p> : null}
    </div>
  );
}

function ErrorBanner({ message, testid }) {
  if (!message) return null;
  return (
    <div
      className="rounded border border-red-200 bg-red-50 text-red-800 text-sm px-3 py-2"
      data-testid={testid}
    >
      {message}
    </div>
  );
}

// ───────────────── LinkHRDriverModal ─────────────────

export function LinkHRDriverModal({ open, onClose, onLinked }) {
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [linking, setLinking] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await txGet("/admin/transportation/eligible-hr-cdl-drivers", { q: q || undefined, limit: 50 });
      setItems(r.data?.items || []);
    } catch (e) {
      setError("Could not load HR CDL drivers right now.");
    } finally {
      setLoading(false);
    }
  }, [q]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  const link = useCallback(async (employeeId) => {
    setLinking(employeeId);
    setError("");
    try {
      const r = await txPost("/admin/transportation/persons/link-from-hr", {
        employee_id: employeeId,
      });
      if (onLinked) onLinked(r.data);
      // Refresh the list so the linked record disappears (or marks as already_linked).
      await load();
    } catch (e) {
      const detail = e?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not link driver right now.");
    } finally {
      setLinking(null);
    }
  }, [load, onLinked]);

  return (
    <ModalShell
      open={open}
      title="Link MASCI CDL Driver from HR"
      subtitle="Only HR employees with cdl_holder = true appear here. Non-CDL approved drivers stay in HR."
      onClose={onClose}
      testid="link-hr-driver-modal"
      wide
    >
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="h-4 w-4 absolute left-2 top-2.5 text-slate-400" />
            <Input
              data-testid="link-hr-driver-search"
              placeholder="Search HR name, employee id, license…"
              className="pl-8"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && load()}
            />
          </div>
          <Button variant="outline" onClick={load} data-testid="link-hr-driver-refresh">Refresh</Button>
        </div>
        <ErrorBanner message={error} testid="link-hr-driver-error" />
        {loading ? (
          <div className="flex items-center gap-2 text-slate-500 text-sm py-8 justify-center" data-testid="link-hr-driver-loading">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading eligible CDL drivers…
          </div>
        ) : items.length === 0 ? (
          <div className="text-sm text-slate-500 py-8 text-center" data-testid="link-hr-driver-empty">
            No eligible HR CDL drivers found. (Approved non-CDL drivers do not appear here by design.)
          </div>
        ) : (
          <div className="border border-slate-200 rounded overflow-hidden">
            <table className="w-full text-sm" data-testid="link-hr-driver-list">
              <thead className="bg-slate-50 text-left">
                <tr>
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">CDL</th>
                  <th className="px-3 py-2">State</th>
                  <th className="px-3 py-2">Lifecycle</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr key={r.employee_id} className="border-t border-slate-100" data-testid={`link-hr-driver-row-${r.employee_id}`}>
                    <td className="px-3 py-2 font-medium">{r.name || r.employee_id}</td>
                    <td className="px-3 py-2 text-slate-600">{r.cdl_class || "—"} {r.cdl_expiration_date ? `· exp ${r.cdl_expiration_date}` : ""}</td>
                    <td className="px-3 py-2 text-slate-600">{r.cdl_state || "—"}</td>
                    <td className="px-3 py-2 text-slate-600">{r.lifecycle_status || "—"}</td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        size="sm"
                        onClick={() => link(r.employee_id)}
                        disabled={linking === r.employee_id}
                        data-testid={`link-hr-driver-link-${r.employee_id}`}
                      >
                        {linking === r.employee_id ? <Loader2 className="h-3 w-3 animate-spin" /> : (<><UserPlus className="h-3 w-3 mr-1" />Link</>)}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="flex justify-end pt-2 border-t border-slate-200">
          <Button variant="outline" onClick={onClose} data-testid="link-hr-driver-done">Done</Button>
        </div>
      </div>
    </ModalShell>
  );
}

// ───────────────── AddLeasedDriverModal ─────────────────

export function AddLeasedDriverModal({ open, onClose, onCreated }) {
  const [carriers, setCarriers] = useState([]);
  const [form, setForm] = useState({
    carrier_id: "",
    first_name: "",
    last_name: "",
    phone: "",
    email: "",
    license_number: "",
    cdl_class: "",
    status: "pending_review",
    notes: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setError("");
    txGet("/admin/transportation/carriers", { limit: 500 }).then((r) => {
      setCarriers(r.data?.items || []);
    }).catch(() => setCarriers([]));
  }, [open]);

  const onChange = (key, value) => setForm((p) => ({ ...p, [key]: value }));

  const canSubmit = useMemo(() => (
    form.carrier_id && form.first_name.trim() && form.last_name.trim()
  ), [form]);

  const submit = useCallback(async () => {
    if (!canSubmit) {
      setError("Carrier, first name, and last name are required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const r = await txPost("/admin/transportation/persons", {
        kind: "leased_driver",
        carrier_id: form.carrier_id,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        phone: form.phone || null,
        email: form.email || null,
        license_number: form.license_number || null,
        cdl_class: form.cdl_class || null,
        status: form.status,
        notes: form.notes || null,
      });
      if (onCreated) onCreated(r.data);
      onClose();
    } catch (e) {
      const detail = e?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not create leased driver right now.");
    } finally {
      setSaving(false);
    }
  }, [canSubmit, form, onClose, onCreated]);

  return (
    <ModalShell open={open} title="Add Leased Driver" subtitle="A driver working under an outside carrier." onClose={onClose} testid="add-leased-driver-modal">
      <div className="space-y-4">
        <ErrorBanner message={error} testid="add-leased-driver-error" />
        <Field label="Carrier" required>
          <select
            data-testid="add-leased-driver-carrier"
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm bg-white"
            value={form.carrier_id}
            onChange={(e) => onChange("carrier_id", e.target.value)}
          >
            <option value="">Choose carrier…</option>
            {carriers.map((c) => (
              <option key={c.id} value={c.id}>{`${c.legal_name}${c.dot_number ? ` · DOT ${c.dot_number}` : ""}`}</option>
            ))}
          </select>
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="First name" required>
            <Input data-testid="add-leased-driver-first" value={form.first_name} onChange={(e) => onChange("first_name", e.target.value)} />
          </Field>
          <Field label="Last name" required>
            <Input data-testid="add-leased-driver-last" value={form.last_name} onChange={(e) => onChange("last_name", e.target.value)} />
          </Field>
          <Field label="Phone"><Input data-testid="add-leased-driver-phone" value={form.phone} onChange={(e) => onChange("phone", e.target.value)} /></Field>
          <Field label="Email"><Input type="email" data-testid="add-leased-driver-email" value={form.email} onChange={(e) => onChange("email", e.target.value)} /></Field>
          <Field label="License number"><Input data-testid="add-leased-driver-license" value={form.license_number} onChange={(e) => onChange("license_number", e.target.value)} /></Field>
          <Field label="CDL class"><Input placeholder="A · B · C" data-testid="add-leased-driver-cdl-class" value={form.cdl_class} onChange={(e) => onChange("cdl_class", e.target.value)} /></Field>
        </div>
        <Field label="Notes">
          <Textarea rows={2} data-testid="add-leased-driver-notes" value={form.notes} onChange={(e) => onChange("notes", e.target.value)} />
        </Field>
        <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
          <Button variant="outline" onClick={onClose} data-testid="add-leased-driver-cancel" disabled={saving}>Cancel</Button>
          <Button onClick={submit} disabled={!canSubmit || saving} data-testid="add-leased-driver-submit">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Check className="h-4 w-4 mr-1" />Create</>}
          </Button>
        </div>
      </div>
    </ModalShell>
  );
}

// ───────────────── Carrier modals ─────────────────

const CARRIER_TYPES = ["leased_hauler", "owner_operator", "supplier", "masci_internal", "other"];
const CARRIER_STATUSES = ["pending_review", "active", "suspended", "inactive"];

function CarrierForm({ value, onChange }) {
  const set = (k, v) => onChange({ ...value, [k]: v });
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <Field label="Legal name" required>
          <Input data-testid="carrier-form-legal-name" value={value.legal_name || ""} onChange={(e) => set("legal_name", e.target.value)} />
        </Field>
        <Field label="DBA / Display name">
          <Input data-testid="carrier-form-dba-name" value={value.dba_name || ""} onChange={(e) => set("dba_name", e.target.value)} />
        </Field>
        <Field label="Type" required>
          <select data-testid="carrier-form-type" className="w-full border border-slate-300 rounded px-3 py-2 text-sm bg-white" value={value.carrier_type || "leased_hauler"} onChange={(e) => set("carrier_type", e.target.value)}>
            {CARRIER_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </Field>
        <Field label="Status">
          <select data-testid="carrier-form-status" className="w-full border border-slate-300 rounded px-3 py-2 text-sm bg-white" value={value.status || "pending_review"} onChange={(e) => set("status", e.target.value)}>
            {CARRIER_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </Field>
        <Field label="DOT number"><Input data-testid="carrier-form-dot" value={value.dot_number || ""} onChange={(e) => set("dot_number", e.target.value)} /></Field>
        <Field label="MC number"><Input data-testid="carrier-form-mc" value={value.mc_number || ""} onChange={(e) => set("mc_number", e.target.value)} /></Field>
        <Field label="Contact name"><Input data-testid="carrier-form-contact-name" value={value.contact_name || ""} onChange={(e) => set("contact_name", e.target.value)} /></Field>
        <Field label="Contact phone"><Input data-testid="carrier-form-contact-phone" value={value.contact_phone || ""} onChange={(e) => set("contact_phone", e.target.value)} /></Field>
        <Field label="Contact email"><Input type="email" data-testid="carrier-form-contact-email" value={value.contact_email || ""} onChange={(e) => set("contact_email", e.target.value)} /></Field>
        <Field label="Safety hold">
          <label className="inline-flex items-center gap-2 text-sm">
            <input type="checkbox" data-testid="carrier-form-safety-hold" checked={!!value.safety_hold} onChange={(e) => set("safety_hold", e.target.checked)} />
            <span className="text-slate-700">Hold from dispatch</span>
          </label>
        </Field>
      </div>
      <Field label="Notes">
        <Textarea rows={2} data-testid="carrier-form-notes" value={value.notes || ""} onChange={(e) => set("notes", e.target.value)} />
      </Field>
    </div>
  );
}

export function AddCarrierModal({ open, onClose, onCreated }) {
  const [form, setForm] = useState({ legal_name: "", carrier_type: "leased_hauler", status: "pending_review" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (open) { setForm({ legal_name: "", carrier_type: "leased_hauler", status: "pending_review" }); setError(""); }
  }, [open]);

  const submit = useCallback(async () => {
    if (!form.legal_name?.trim()) { setError("Legal name is required."); return; }
    setSaving(true);
    setError("");
    try {
      const r = await txPost("/admin/transportation/carriers", form);
      if (onCreated) onCreated(r.data);
      onClose();
    } catch (e) {
      const detail = e?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not create carrier right now.");
    } finally {
      setSaving(false);
    }
  }, [form, onClose, onCreated]);

  return (
    <ModalShell open={open} title="Add Carrier" subtitle="Add a leased hauler, owner-operator, supplier, or MASCI-internal carrier." onClose={onClose} testid="add-carrier-modal">
      <div className="space-y-4">
        <ErrorBanner message={error} testid="add-carrier-error" />
        <CarrierForm value={form} onChange={setForm} />
        <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
          <Button variant="outline" onClick={onClose} data-testid="add-carrier-cancel" disabled={saving}>Cancel</Button>
          <Button onClick={submit} disabled={saving} data-testid="add-carrier-submit">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Building2 className="h-4 w-4 mr-1" />Create</>}
          </Button>
        </div>
      </div>
    </ModalShell>
  );
}

export function EditCarrierModal({ open, carrier, onClose, onUpdated }) {
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (open && carrier) {
      setForm({
        legal_name: carrier.legal_name || "",
        dba_name: carrier.dba_name || "",
        carrier_type: carrier.carrier_type || "leased_hauler",
        status: carrier.status || "pending_review",
        dot_number: carrier.dot_number || "",
        mc_number: carrier.mc_number || "",
        contact_name: carrier.contact_name || "",
        contact_phone: carrier.contact_phone || "",
        contact_email: carrier.contact_email || "",
        safety_hold: !!carrier.safety_hold,
        notes: carrier.notes || "",
      });
      setError("");
    }
  }, [open, carrier]);

  const submit = useCallback(async () => {
    if (!carrier?.id) return;
    setSaving(true);
    setError("");
    try {
      const r = await txPatch(`/admin/transportation/carriers/${carrier.id}`, form);
      if (onUpdated) onUpdated(r.data);
      onClose();
    } catch (e) {
      const detail = e?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not update carrier right now.");
    } finally {
      setSaving(false);
    }
  }, [carrier, form, onClose, onUpdated]);

  return (
    <ModalShell open={open} title={`Edit Carrier · ${carrier?.legal_name || ""}`} subtitle="Update operational and contact fields. HR identity is not touched." onClose={onClose} testid="edit-carrier-modal">
      <div className="space-y-4">
        <ErrorBanner message={error} testid="edit-carrier-error" />
        <CarrierForm value={form} onChange={setForm} />
        <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
          <Button variant="outline" onClick={onClose} data-testid="edit-carrier-cancel" disabled={saving}>Cancel</Button>
          <Button onClick={submit} disabled={saving} data-testid="edit-carrier-submit">
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Check className="h-4 w-4 mr-1" />Save</>}
          </Button>
        </div>
      </div>
    </ModalShell>
  );
}
