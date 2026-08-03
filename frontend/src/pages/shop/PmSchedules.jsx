// Track 13.31 — PM Schedules list + per-unit create form.
// Route: /shop/pm/schedules (RequireShop).
import React, { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { PortalShell, Card } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";

const API = process.env.REACT_APP_BACKEND_URL;
function authHeaders() {
  return buildScopedPortalAuthHeaders(["admin", "shop"], { "Content-Type": "application/json" });
}

const STATUS_TONE = {
  overdue:       { bg: "#fef2f2", border: "#fecaca", text: "#991b1b", label: "Overdue" },
  due:           { bg: "#fffbeb", border: "#fde68a", text: "#92400e", label: "Due now" },
  due_soon:      { bg: "#eff6ff", border: "#bfdbfe", text: "#1e40af", label: "Due soon" },
  ok:            { bg: "var(--paper-card)", border: "var(--border-bold)", text: "var(--ink-strong)", label: "On track" },
  paused:        { bg: "#f5f3ff", border: "#ddd6fe", text: "#5b21b6", label: "Paused" },
  unknown_meter: { bg: "#f1f5f9", border: "#cbd5e1", text: "#475569", label: "Needs meter" },
};

export default function PmSchedules() {
  const [params] = useSearchParams();
  const statusFilter = params.get("status") || "";
  const focusId = params.get("focus") || "";
  const [items, setItems] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [form, setForm] = useState({
    unit_number: "", template_id: "", last_completed_meter: "", last_completed_at: "",
    active: true, paused: false, override_reason: "",
  });
  const [editingId, setEditingId] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const q = statusFilter ? `?status=${statusFilter}` : "";
      const [s, t] = await Promise.all([
        fetch(`${API}/api/shop/pm/schedules${q}`, { headers: authHeaders() }).then(r => r.json()),
        fetch(`${API}/api/shop/pm/templates?active=true`, { headers: authHeaders() }).then(r => r.json()),
      ]);
      setItems(s.items || []);
      setTemplates(t.items || []);
    } catch (e) { setErr(e.message); }
  }, [statusFilter]);
  useEffect(() => { refresh(); }, [refresh]);

  function startEdit(s) {
    setEditingId(s.id);
    setForm({
      unit_number: s.unit_number, template_id: s.template_id,
      last_completed_meter: s.last_completed_meter ?? "",
      last_completed_at: s.last_completed_at || "",
      active: s.active, paused: s.paused, override_reason: s.override_reason || "",
    });
    window.scrollTo(0, 0);
  }
  function reset() {
    setEditingId(""); setForm({
      unit_number: "", template_id: "", last_completed_meter: "", last_completed_at: "",
      active: true, paused: false, override_reason: "",
    });
  }

  async function save(e) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const body = { ...form,
        last_completed_meter: form.last_completed_meter === "" ? null : Number(form.last_completed_meter),
      };
      const url = editingId ? `${API}/api/shop/pm/schedules/${editingId}` : `${API}/api/shop/pm/schedules`;
      const method = editingId ? "PUT" : "POST";
      const r = await fetch(url, { method, headers: authHeaders(), body: JSON.stringify(body) });
      const b = await r.json();
      if (!r.ok) throw new Error(b.detail || `HTTP ${r.status}`);
      reset();
      await refresh();
    } catch (e) { setErr(e.message); }
    setBusy(false);
  }

  async function generate(sched) {
    setErr("");
    try {
      const r = await fetch(`${API}/api/shop/pm/work-orders`, {
        method: "POST", headers: authHeaders(),
        body: JSON.stringify({ schedule_id: sched.id }),
      });
      const b = await r.json();
      if (!r.ok) throw new Error(b.detail || `HTTP ${r.status}`);
      alert(`PM work order created (id: ${b.work_order.id}). Open the Work Orders queue to assign.`);
    } catch (e) { setErr(e.message); }
  }

  const lblStyle = { display: "block", fontSize: 11, fontWeight: 700, letterSpacing: ".04em", textTransform: "uppercase", color: "var(--ink-soft)", marginBottom: 4 };
  const inpStyle = { width: "100%", padding: "8px 10px", fontSize: 13, border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)", background: "var(--paper-card)", color: "var(--ink-strong)" };

  return (
    <div data-testid="pm-schedules-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell portalName="MASCI" portalRole="Shop Operations"
                   pageTitle="PM Schedules"
                   subtitle="Per-unit PM cadence. Status recomputes live from latest meter/odometer.">
        <BackToShopLink />
        {err && <div data-testid="pm-schedules-error" style={{ padding: 12, background: "#fee2e2", color: "#7f1d1d", borderRadius: 4, marginBottom: 12 }}>{err}</div>}

        <Card title={editingId ? "Edit schedule" : "Assign template to a unit"}>
          <form onSubmit={save} data-testid="pm-schedules-form" style={{ display: "grid", gap: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
              <div>
                <label style={lblStyle}>Unit number *</label>
                <input data-testid="pm-schedules-input-unit" required value={form.unit_number}
                       onChange={(e) => setForm(f => ({ ...f, unit_number: e.target.value }))}
                       style={inpStyle} placeholder="EXC-8614" />
              </div>
              <div>
                <label style={lblStyle}>Template *</label>
                <select data-testid="pm-schedules-input-template" required value={form.template_id}
                        onChange={(e) => setForm(f => ({ ...f, template_id: e.target.value }))}
                        style={inpStyle}>
                  <option value="">Choose template…</option>
                  {templates.map(t => <option key={t.id} value={t.id}>{`${t.name} · ${t.asset_type} · ${t.interval_value}${t.interval_type[0]}`}</option>)}
                </select>
              </div>
              <div>
                <label style={lblStyle}>Last completed meter</label>
                <input data-testid="pm-schedules-input-last-meter" type="number" min="0" step="any"
                       value={form.last_completed_meter}
                       onChange={(e) => setForm(f => ({ ...f, last_completed_meter: e.target.value }))}
                       style={inpStyle} placeholder="optional · leave blank for first cycle" />
              </div>
              <div>
                <label style={lblStyle}>Last completed at</label>
                <input data-testid="pm-schedules-input-last-at" type="date"
                       value={(form.last_completed_at || "").slice(0, 10)}
                       onChange={(e) => setForm(f => ({ ...f, last_completed_at: e.target.value ? `${e.target.value}T00:00:00Z` : "" }))}
                       style={inpStyle} />
              </div>
            </div>
            <div style={{ display: "flex", gap: 18, alignItems: "center", flexWrap: "wrap" }}>
              <label data-testid="pm-schedules-active-row" style={{ fontSize: 13, color: "var(--ink-strong)" }}>
                <input data-testid="pm-schedules-input-active" type="checkbox" checked={form.active}
                       onChange={(e) => setForm(f => ({ ...f, active: e.target.checked }))} /> Active
              </label>
              <label data-testid="pm-schedules-paused-row" style={{ fontSize: 13, color: "var(--ink-strong)" }}>
                <input data-testid="pm-schedules-input-paused" type="checkbox" checked={form.paused}
                       onChange={(e) => setForm(f => ({ ...f, paused: e.target.checked }))} /> Paused
              </label>
              {form.paused && (
                <input data-testid="pm-schedules-input-pause-reason" placeholder="Pause reason (saved to history)"
                       value={form.override_reason}
                       onChange={(e) => setForm(f => ({ ...f, override_reason: e.target.value }))}
                       style={{ ...inpStyle, maxWidth: 360 }} />
              )}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button data-testid="pm-schedules-submit" type="submit" disabled={busy}
                      style={{ padding: "10px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer",
                               background: "var(--brand-primary)", color: "var(--brand-on-primary)",
                               border: "1px solid var(--brand-primary)", borderRadius: "var(--radius-card)" }}>
                {busy ? "Saving…" : (editingId ? "Update schedule" : "Create schedule")}
              </button>
              {editingId && <button type="button" data-testid="pm-schedules-cancel" onClick={reset}
                      style={{ padding: "10px 20px", fontSize: 13, fontWeight: 600,
                               background: "var(--paper-card)", color: "var(--ink-strong)",
                               border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)", cursor: "pointer" }}>Cancel</button>}
            </div>
          </form>
        </Card>

        <section data-testid="pm-schedules-list" style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 18, fontWeight: 800, marginBottom: 10 }}>
            Schedules {statusFilter ? `· ${STATUS_TONE[statusFilter]?.label || statusFilter}` : ""} ({items.length})
          </h2>
          {items.length === 0 && <div data-testid="pm-schedules-empty"
            style={{ padding: 12, background: "var(--paper-card)", border: "1px solid var(--border-bold)",
                     borderRadius: "var(--radius-card)", fontSize: 12, color: "var(--ink-soft)" }}>
            No PM schedules matching the current filter.
          </div>}
          {items.map((s) => {
            const tone = STATUS_TONE[s.status] || STATUS_TONE.ok;
            const highlight = focusId === s.id;
            return (
              <div key={s.id} data-testid={`pm-schedules-row-${s.id}`}
                   style={{ padding: "12px 14px", marginBottom: 8,
                            background: tone.bg, border: `${highlight ? 2 : 1}px solid ${highlight ? "#fb923c" : tone.border}`,
                            borderRadius: "var(--radius-card)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
                  <div>
                    <strong style={{ fontSize: 14, color: tone.text }}>{s.unit_number}</strong>
                    <span style={{ marginLeft: 8, fontSize: 12, color: "var(--ink-strong)" }}>· {s.template_name}</span>
                  </div>
                  <span data-testid={`pm-schedules-row-status-${s.id}`}
                        style={{ padding: "3px 10px", borderRadius: 3, background: tone.bg, color: tone.text, fontSize: 11, fontWeight: 700, textTransform: "uppercase", border: `1px solid ${tone.border}` }}>
                    {tone.label}
                  </span>
                </div>
                <div style={{ fontSize: 11, color: "var(--ink-soft)", marginTop: 4 }}>{s.explanation}</div>
                <div style={{ fontSize: 11, color: "var(--ink-faint, #6b7280)", marginTop: 4 }}>
                  Current meter: {s.current_meter?.meter_hours ?? "—"}{s.interval_type === "hours" ? " hr" : ""}
                  {s.current_meter?.odometer_miles != null ? ` · ${s.current_meter.odometer_miles} mi` : ""}
                  {" · "}Source: {s.current_meter?.source || "—"}
                </div>
                <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <button data-testid={`pm-schedules-row-edit-${s.id}`} type="button" onClick={() => startEdit(s)}
                          style={{ padding: "6px 12px", fontSize: 11, fontWeight: 600,
                                   background: "var(--paper-card)", color: "var(--ink-strong)",
                                   border: "1px solid var(--border-bold)", borderRadius: 3, cursor: "pointer" }}>Edit</button>
                  <button data-testid={`pm-schedules-row-generate-${s.id}`} type="button" onClick={() => generate(s)}
                          style={{ padding: "6px 12px", fontSize: 11, fontWeight: 700,
                                   background: tone.text === "var(--ink-strong)" ? "var(--brand-primary)" : tone.text,
                                   color: "white", border: "none", borderRadius: 3, cursor: "pointer" }}>
                    Generate PM work order
                  </button>
                </div>
              </div>
            );
          })}
        </section>
      </PortalShell>
    </div>
  );
}
