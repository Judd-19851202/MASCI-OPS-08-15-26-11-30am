// Track 13.31 — PM Templates list + create/edit form.
// Route: /shop/pm/templates (RequireShop).
import React, { useEffect, useState } from "react";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, Card } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";

const API = process.env.REACT_APP_BACKEND_URL;
const INTERVAL_TYPES = ["hours", "miles", "days"];

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken(); const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}
function emptyForm() {
  return {
    name: "", asset_type: "", interval_type: "hours",
    interval_value: 250, warning_threshold: 25, description: "",
    checklist_items: [{ label: "", required: true }],
    default_parts: [{ name: "", part_number: "", manufacturer: "", supplier: "", quantity: 1 }],
    active: true,
  };
}

export default function PmTemplates() {
  const [items, setItems] = useState([]);
  const [form, setForm]   = useState(emptyForm());
  const [editingId, setEditingId] = useState("");
  const [err, setErr]     = useState("");
  const [busy, setBusy]   = useState(false);
  // Track 13.31B-D5 · canonical asset_type selector backed by the spine.
  const [taxonomy, setTaxonomy] = useState(null);

  async function refresh() {
    try {
      const r = await fetch(`${API}/api/shop/pm/templates`, { headers: authHeaders() });
      const b = await r.json();
      setItems(b.items || []);
    } catch (e) { setErr(e.message); }
  }
  useEffect(() => {
    refresh();
    fetch(`${API}/api/asset-spine/taxonomy`, { headers: authHeaders() })
      .then(r => r.json()).then(setTaxonomy).catch(() => {});
  }, []);

  function startEdit(t) {
    setEditingId(t.id);
    setForm({
      name: t.name, asset_type: t.asset_type,
      interval_type: t.interval_type, interval_value: t.interval_value,
      warning_threshold: t.warning_threshold, description: t.description || "",
      checklist_items: t.checklist_items?.length ? t.checklist_items : [{ label: "", required: true }],
      default_parts: t.default_parts?.length ? t.default_parts : [{ name: "", part_number: "", manufacturer: "", supplier: "", quantity: 1 }],
      active: t.active,
    });
    window.scrollTo(0, 0);
  }
  function reset() { setEditingId(""); setForm(emptyForm()); }

  async function save(e) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const body = { ...form,
        interval_value: Number(form.interval_value) || 0,
        warning_threshold: Number(form.warning_threshold) || 0,
        checklist_items: form.checklist_items.filter(c => c.label.trim()),
        default_parts: form.default_parts.filter(p => p.name.trim()).map(p => ({ ...p, quantity: Number(p.quantity) || 1 })),
      };
      const url = editingId ? `${API}/api/shop/pm/templates/${editingId}` : `${API}/api/shop/pm/templates`;
      const method = editingId ? "PUT" : "POST";
      const r = await fetch(url, { method, headers: authHeaders(), body: JSON.stringify(body) });
      const b = await r.json();
      if (!r.ok) throw new Error(b.detail || `HTTP ${r.status}`);
      reset();
      await refresh();
    } catch (e) { setErr(e.message); }
    setBusy(false);
  }

  const lblStyle = { display: "block", fontSize: 11, fontWeight: 700, letterSpacing: ".04em",
                     textTransform: "uppercase", color: "var(--ink-soft)", marginBottom: 4 };
  const inpStyle = { width: "100%", padding: "8px 10px", fontSize: 13,
                     border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
                     background: "var(--paper-card)", color: "var(--ink-strong)" };

  return (
    <div data-testid="pm-templates-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell portalName="MASCI" portalRole="Shop Operations"
                   pageTitle="PM Templates"
                   subtitle="Operator-defined PM intervals by asset type. No fake manufacturer schedules.">
        <BackToShopLink />
        {err && <div data-testid="pm-templates-error" style={{ padding: 12, background: "#fee2e2", color: "#7f1d1d", borderRadius: 4, marginBottom: 12 }}>{err}</div>}

        <Card title={editingId ? "Edit template" : "New PM template"}>
          <form onSubmit={save} data-testid="pm-templates-form" style={{ display: "grid", gap: 14 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
              <div>
                <label style={lblStyle}>Template name *</label>
                <input data-testid="pm-templates-input-name" required minLength={1} maxLength={200}
                       value={form.name} onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
                       style={inpStyle} placeholder="250-Hour Excavator Service" />
              </div>
              <div>
                <label style={lblStyle}>Asset type *</label>
                <select data-testid="pm-templates-input-asset-type" required
                       value={form.asset_type} onChange={(e) => setForm(f => ({ ...f, asset_type: e.target.value }))}
                       style={inpStyle}>
                  <option value="">— select canonical asset type —</option>
                  {taxonomy?.asset_types_by_class
                    ? Object.entries(taxonomy.asset_types_by_class).flatMap(([cls, types]) => [
                        <optgroup key={cls} label={cls}>
                          {types.map(t => <option key={`${cls}|${t}`} value={t}>{t}</option>)}
                        </optgroup>,
                      ])
                    : null}
                </select>
              </div>
              <div>
                <label style={lblStyle}>Interval type *</label>
                <select data-testid="pm-templates-input-interval-type" value={form.interval_type}
                        onChange={(e) => setForm(f => ({ ...f, interval_type: e.target.value }))}
                        style={inpStyle}>
                  {INTERVAL_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label style={lblStyle}>Interval value *</label>
                <input data-testid="pm-templates-input-interval-value" type="number" min="1" step="any" required
                       value={form.interval_value} onChange={(e) => setForm(f => ({ ...f, interval_value: e.target.value }))}
                       style={inpStyle} />
              </div>
              <div>
                <label style={lblStyle}>Warning threshold</label>
                <input data-testid="pm-templates-input-warning" type="number" min="0" step="any"
                       value={form.warning_threshold} onChange={(e) => setForm(f => ({ ...f, warning_threshold: e.target.value }))}
                       style={inpStyle} />
              </div>
            </div>
            <div>
              <label style={lblStyle}>Description</label>
              <textarea data-testid="pm-templates-input-description" rows={3} maxLength={2000}
                        value={form.description} onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))}
                        style={{ ...inpStyle, fontFamily: "inherit" }} />
            </div>
            <div>
              <label style={lblStyle}>Checklist items</label>
              {form.checklist_items.map((c, i) => (
                <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6 }}>
                  <input data-testid={`pm-templates-checklist-${i}`} value={c.label} maxLength={200}
                         onChange={(e) => setForm(f => ({ ...f, checklist_items: f.checklist_items.map((x, j) => j === i ? { ...x, label: e.target.value } : x) }))}
                         style={{ ...inpStyle, flex: 1 }} placeholder={`Step ${i + 1}`} />
                  <button type="button" data-testid={`pm-templates-checklist-remove-${i}`}
                          onClick={() => setForm(f => ({ ...f, checklist_items: f.checklist_items.filter((_, j) => j !== i) }))}
                          style={{ padding: "0 10px", border: "1px solid var(--border-bold)", borderRadius: 3, background: "var(--paper-card)", cursor: "pointer" }}>×</button>
                </div>
              ))}
              <button type="button" data-testid="pm-templates-checklist-add"
                      onClick={() => setForm(f => ({ ...f, checklist_items: [...f.checklist_items, { label: "", required: true }] }))}
                      style={{ padding: "6px 12px", fontSize: 12, fontWeight: 600,
                               background: "var(--paper-card)", color: "var(--ink-strong)",
                               border: "1px solid var(--border-bold)", borderRadius: 3, cursor: "pointer" }}>+ Add step</button>
            </div>
            <div>
              <label style={lblStyle}>Default parts</label>
              {form.default_parts.map((p, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 80px 36px", gap: 6, marginBottom: 6 }}>
                  <input data-testid={`pm-templates-part-name-${i}`} placeholder="Part name" value={p.name} maxLength={200}
                         onChange={(e) => setForm(f => ({ ...f, default_parts: f.default_parts.map((x, j) => j === i ? { ...x, name: e.target.value } : x) }))} style={inpStyle} />
                  <input data-testid={`pm-templates-part-pn-${i}`} placeholder="Part #" value={p.part_number} maxLength={100}
                         onChange={(e) => setForm(f => ({ ...f, default_parts: f.default_parts.map((x, j) => j === i ? { ...x, part_number: e.target.value } : x) }))} style={inpStyle} />
                  <input data-testid={`pm-templates-part-mfr-${i}`} placeholder="Manufacturer" value={p.manufacturer} maxLength={100}
                         onChange={(e) => setForm(f => ({ ...f, default_parts: f.default_parts.map((x, j) => j === i ? { ...x, manufacturer: e.target.value } : x) }))} style={inpStyle} />
                  <input data-testid={`pm-templates-part-qty-${i}`} type="number" min="0" step="any" value={p.quantity}
                         onChange={(e) => setForm(f => ({ ...f, default_parts: f.default_parts.map((x, j) => j === i ? { ...x, quantity: e.target.value } : x) }))} style={inpStyle} />
                  <button type="button" onClick={() => setForm(f => ({ ...f, default_parts: f.default_parts.filter((_, j) => j !== i) }))}
                          style={{ padding: "0 10px", border: "1px solid var(--border-bold)", borderRadius: 3, background: "var(--paper-card)", cursor: "pointer" }}>×</button>
                </div>
              ))}
              <button type="button" data-testid="pm-templates-part-add"
                      onClick={() => setForm(f => ({ ...f, default_parts: [...f.default_parts, { name: "", part_number: "", manufacturer: "", supplier: "", quantity: 1 }] }))}
                      style={{ padding: "6px 12px", fontSize: 12, fontWeight: 600,
                               background: "var(--paper-card)", color: "var(--ink-strong)",
                               border: "1px solid var(--border-bold)", borderRadius: 3, cursor: "pointer" }}>+ Add part</button>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button data-testid="pm-templates-submit" type="submit" disabled={busy}
                      style={{ padding: "10px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer",
                               background: "var(--brand-primary)", color: "var(--brand-on-primary)",
                               border: "1px solid var(--brand-primary)", borderRadius: "var(--radius-card)" }}>
                {busy ? "Saving…" : (editingId ? "Update template" : "Create template")}
              </button>
              {editingId && <button type="button" data-testid="pm-templates-cancel" onClick={reset}
                      style={{ padding: "10px 20px", fontSize: 13, fontWeight: 600,
                               background: "var(--paper-card)", color: "var(--ink-strong)",
                               border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)", cursor: "pointer" }}>Cancel</button>}
            </div>
          </form>
        </Card>

        <section data-testid="pm-templates-list" style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 18, fontWeight: 800, marginBottom: 10 }}>Active templates ({items.length})</h2>
          {items.length === 0 && <div data-testid="pm-templates-empty" style={{ padding: 12, background: "var(--paper-card)", border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)", fontSize: 12, color: "var(--ink-soft)" }}>No PM templates yet. Create one above.</div>}
          {items.map((t) => (
            <button key={t.id} type="button" data-testid={`pm-templates-row-${t.id}`} onClick={() => startEdit(t)}
                    style={{ display: "block", width: "100%", textAlign: "left", padding: "10px 14px", marginBottom: 6,
                             background: "var(--paper-card)", border: "1px solid var(--border-bold)",
                             borderRadius: "var(--radius-card)", cursor: "pointer" }}>
              <strong style={{ fontSize: 13 }}>{t.name}</strong>
              <span style={{ marginLeft: 8, fontSize: 11, color: "var(--ink-soft)" }}>
                {t.asset_type} · every {t.interval_value} {t.interval_type} · warn {t.warning_threshold}
              </span>
            </button>
          ))}
        </section>
      </PortalShell>
    </div>
  );
}
