// Track 13.30 — Service Truck Daily Reconciliation · start + close form.
// Route: /shop/service-truck-reconciliation/new (RequireShop).
// Endpoints: POST /api/shop/service-truck-reconciliation/start
//            POST /api/shop/service-truck-reconciliation/close
// Doctrine: NO accounting · NO cost · NO fuel tax. Operational accountability only.
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, Card } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";
import ShopSelector from "@/components/shop/ShopSelector";

const API = process.env.REACT_APP_BACKEND_URL;

const FUEL_FIELDS = [
  { key: "red_diesel_gallons",   label: "Red diesel",      unit: "gal" },
  { key: "clear_diesel_gallons", label: "Clear diesel",    unit: "gal" },
  { key: "gasoline_gallons",     label: "Gasoline",        unit: "gal" },
  { key: "def_gallons",          label: "DEF",             unit: "gal" },
];
const FLUID_FIELDS = [
  { key: "engine_oil_quarts",         label: "Engine oil",         unit: "qt" },
  { key: "hydraulic_oil_quarts",      label: "Hydraulic oil",      unit: "qt" },
  { key: "coolant_quarts",            label: "Coolant",            unit: "qt" },
  { key: "transmission_fluid_quarts", label: "Transmission fluid", unit: "qt" },
  { key: "gear_oil_quarts",           label: "Gear oil",           unit: "qt" },
];
const ALL_FIELDS = [...FUEL_FIELDS, ...FLUID_FIELDS];

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken(); const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}
function emptyQ() {
  const o = {};
  for (const f of ALL_FIELDS) o[f.key] = "";
  return o;
}
function numOrZero(v) { const n = Number(v); return Number.isFinite(n) && n >= 0 ? n : 0; }

const STATUS_MAP = {
  green:      { bg: "#d4edda", fg: "#155724", label: "Within expected range" },
  yellow:     { bg: "#fff3cd", fg: "#856404", label: "Needs review" },
  red:        { bg: "#f8d7da", fg: "#721c24", label: "Significant variance" },
  incomplete: { bg: "#e2e3e5", fg: "#383d41", label: "Incomplete" },
};
function StatusChip({ status }) {
  const s = STATUS_MAP[status] || { bg: "#eee", fg: "#222", label: status || "—" };
  return (
    <span data-testid={`strr-variance-chip-${status || "unknown"}`}
          style={{ padding: "2px 8px", borderRadius: 3, background: s.bg, color: s.fg, fontSize: 11, fontWeight: 700 }}>
      {s.label.toUpperCase()}
    </span>
  );
}
function ProductInput({ field, valueObj, onSet, testidPrefix }) {
  return (
    <label data-testid={`${testidPrefix}-label-${field.key}`}
           style={{ fontSize: 12, color: "#222", display: "flex", flexDirection: "column", gap: 2 }}>
      <span>{field.label} ({field.unit})</span>
      <input data-testid={`${testidPrefix}-input-${field.key}`} type="number" min="0" step="0.1"
             value={valueObj[field.key]} onChange={(e) => onSet(field.key, e.target.value)}
             style={{ padding: 5, fontSize: 12 }} />
    </label>
  );
}

export default function ServiceTruckReconciliationForm() {
  const navigate = useNavigate();
  const today = new Date().toISOString().slice(0, 10);

  const [mode, setMode] = useState("start"); // "start" | "close"
  const [date, setDate] = useState(today);
  const [truck, setTruck] = useState("");
  const [techId, setTechId] = useState("");
  const [techName, setTechName] = useState("");
  const [reconciliationId, setReconciliationId] = useState("");
  const [startQ, setStartQ] = useState(emptyQ());
  const [endQ, setEndQ] = useState(emptyQ());
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  function setProductQty(setter, key, v) { setter((prev) => ({ ...prev, [key]: v })); }
  const setStart = (key, v) => setProductQty(setStartQ, key, v);
  const setEnd   = (key, v) => setProductQty(setEndQ, key, v);

  async function submitStart(e) {
    e.preventDefault(); setError(""); setResult(null);
    if (!truck.trim() || !techName.trim()) { setError("Truck and tech name are required."); return; }
    setSubmitting(true);
    try {
      const body = {
        date,
        service_truck_unit: truck.trim(),
        tech_id: techId.trim(),
        tech_name: techName.trim(),
        start_quantities: Object.fromEntries(ALL_FIELDS.map((f) => [f.key, numOrZero(startQ[f.key])])),
        notes: notes,
      };
      const r = await fetch(`${API}/api/shop/service-truck-reconciliation/start`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(body),
      });
      const data = await r.json().catch(() => null);
      if (!r.ok) throw new Error((data && data.detail) || `HTTP ${r.status}`);
      setReconciliationId(data.id);
      setResult({ kind: "start", body: data });
    } catch (err) { setError(err.message || "Failed to log start of day."); }
    setSubmitting(false);
  }

  async function submitClose(e) {
    e.preventDefault(); setError(""); setResult(null);
    if (!truck.trim() && !reconciliationId.trim()) { setError("Provide reconciliation id, or date + truck."); return; }
    setSubmitting(true);
    try {
      const body = {
        reconciliation_id: reconciliationId.trim() || undefined,
        date: reconciliationId.trim() ? undefined : date,
        service_truck_unit: reconciliationId.trim() ? undefined : truck.trim(),
        end_quantities: Object.fromEntries(ALL_FIELDS.map((f) => [f.key, numOrZero(endQ[f.key])])),
        notes: notes,
        submitted_by: techName.trim(),
      };
      const r = await fetch(`${API}/api/shop/service-truck-reconciliation/close`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(body),
      });
      const data = await r.json().catch(() => null);
      if (!r.ok) throw new Error((data && data.detail) || `HTTP ${r.status}`);
      setResult({ kind: "close", body: data });
    } catch (err) { setError(err.message || "Failed to close day."); }
    setSubmitting(false);
  }

  return (
    <div data-testid="strr-form-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI" portalRole="Shop Portal · Service Truck Reconciliation"
        pageTitle="Service Truck Daily Reconciliation"
        subtitle="Start-of-day and end-of-day fuel and fluid accountability by truck and day. Operational accountability — not accounting."
        primaryActions={<BackToShopLink testId="strr-form-back-to-shop" />}
      >
        <div data-testid="strr-form-mode-toggle" style={{ display: "flex", gap: 6, marginBottom: 12 }}>
          {[
            { id: "start", label: "Start of Day" },
            { id: "close", label: "Close of Day" },
          ].map((m) => (
            <button key={m.id} data-testid={`strr-form-mode-${m.id}`} type="button" onClick={() => setMode(m.id)}
                    style={{ padding: "6px 12px", fontSize: 12, fontWeight: 700,
                             background: mode === m.id ? "var(--brand-primary,#1b4965)" : "#ddd",
                             color: mode === m.id ? "#fff" : "#222", border: "none", borderRadius: 4 }}>{m.label}</button>
          ))}
        </div>

        <Card>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 8, marginBottom: 12 }}>
            <label data-testid="strr-form-date-label" style={{ fontSize: 12, display: "flex", flexDirection: "column", gap: 2 }}>
              <span>Date</span>
              <input data-testid="strr-form-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} style={{ padding: 5, fontSize: 12 }} />
            </label>
            <label data-testid="strr-form-truck-label" style={{ fontSize: 12, display: "flex", flexDirection: "column", gap: 2 }}>
              <span>Service truck unit*</span>
              <ShopSelector
                kind="unit"
                testIdPrefix="strr-form-truck"
                value={truck}
                onChange={(row) => setTruck(row?.unit_number || "")}
                required
              />
            </label>
            <label data-testid="strr-form-tech-id-label" style={{ fontSize: 12, display: "flex", flexDirection: "column", gap: 2 }}>
              <span>Tech employee id</span>
              <input data-testid="strr-form-tech-id" value={techId} onChange={(e) => setTechId(e.target.value)} style={{ padding: 5, fontSize: 12 }} />
            </label>
            <label data-testid="strr-form-tech-name-label" style={{ fontSize: 12, display: "flex", flexDirection: "column", gap: 2 }}>
              <span>Tech name</span>
              <input data-testid="strr-form-tech-name" value={techName} onChange={(e) => setTechName(e.target.value)} style={{ padding: 5, fontSize: 12 }} />
            </label>
            {mode === "close" && (
              <label data-testid="strr-form-rec-id-label" style={{ fontSize: 12, display: "flex", flexDirection: "column", gap: 2 }}>
                <span>Reconciliation id (optional)</span>
                <input data-testid="strr-form-rec-id" placeholder="strr-…" value={reconciliationId}
                       onChange={(e) => setReconciliationId(e.target.value)} style={{ padding: 5, fontSize: 12 }} />
              </label>
            )}
          </div>

          <h3 style={{ marginTop: 0, fontSize: 12, textTransform: "uppercase", letterSpacing: ".05em", color: "#666" }}>
            {mode === "start" ? "Start-of-Day quantities" : "End-of-Day quantities"}
          </h3>
          <div data-testid={`strr-form-${mode}-grid`}
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 6 }}>
            {ALL_FIELDS.map((f) => (
              <ProductInput key={f.key} field={f}
                valueObj={mode === "start" ? startQ : endQ}
                onSet={mode === "start" ? setStart : setEnd}
                testidPrefix={`strr-form-${mode}`} />
            ))}
          </div>

          <label data-testid="strr-form-notes-label" style={{ marginTop: 12, fontSize: 12, display: "flex", flexDirection: "column", gap: 2 }}>
            <span>Notes (optional · operational context only · NOT disciplinary)</span>
            <textarea data-testid="strr-form-notes" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} style={{ padding: 6, fontSize: 12, resize: "vertical" }} />
          </label>

          {error && (
            <div data-testid="strr-form-error" style={{ marginTop: 12, padding: 10, background: "#fae2e0", color: "#a33", fontSize: 12, borderRadius: 4 }}>
              {error}
            </div>
          )}

          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
            {mode === "start" ? (
              <button data-testid="strr-form-submit-start" type="button" onClick={submitStart} disabled={submitting}
                      style={{ padding: "6px 14px", fontSize: 13, background: "var(--brand-primary,#1b4965)", color: "#fff", border: "none", borderRadius: 4 }}>
                {submitting ? "Submitting…" : "Log Start of Day"}
              </button>
            ) : (
              <button data-testid="strr-form-submit-close" type="button" onClick={submitClose} disabled={submitting}
                      style={{ padding: "6px 14px", fontSize: 13, background: "var(--brand-primary,#1b4965)", color: "#fff", border: "none", borderRadius: 4 }}>
                {submitting ? "Closing…" : "Close Day & Compute Variance"}
              </button>
            )}
            <button data-testid="strr-form-records-link" type="button" onClick={() => navigate("/shop/service-truck-reconciliation")}
                    style={{ padding: "6px 14px", fontSize: 13 }}>View Records</button>
          </div>
        </Card>

        {result && result.kind === "start" && (
          <Card data-testid="strr-form-start-result" style={{ marginTop: 12 }}>
            <div style={{ fontSize: 13 }}>
              <strong>Start of day logged.</strong> Reconciliation id <code>{result.body.id}</code>. Close at end of day to compute variance.
            </div>
          </Card>
        )}

        {result && result.kind === "close" && result.body.reconciliation && (
          <Card data-testid="strr-form-close-result" style={{ marginTop: 12 }}>
            <div style={{ fontSize: 13, marginBottom: 6 }}>
              <strong>Day closed.</strong> Reconciliation id <code>{result.body.id}</code> · status <strong>{result.body.status}</strong> ·{" "}
              <StatusChip status={result.body.variance_status} />
            </div>
            <div data-testid="strr-form-close-result-grid"
                 style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr", gap: 4, fontSize: 11, marginTop: 8 }}>
              <div style={{ fontWeight: 700 }}>Product</div>
              <div style={{ fontWeight: 700 }}>Start</div>
              <div style={{ fontWeight: 700 }}>Dispensed</div>
              <div style={{ fontWeight: 700 }}>Expected end</div>
              <div style={{ fontWeight: 700 }}>Actual end · variance</div>
              {(result.body.reconciliation.variance?.rows || []).map((row) => (
                <React.Fragment key={row.field}>
                  <div>{row.field}</div>
                  <div>{row.start}</div>
                  <div>{(result.body.reconciliation.dispensed_quantities || {})[row.field] || 0}</div>
                  <div>{row.expected_end}</div>
                  <div>
                    {row.actual_end} · <span style={{ color: row.status === "red" ? "#a33" : row.status === "yellow" ? "#856404" : "#155724" }}>
                      Δ {row.variance} {row.unit} ({(row.variance_pct * 100).toFixed(1)}%)
                    </span>
                  </div>
                </React.Fragment>
              ))}
            </div>
            <div style={{ marginTop: 10, fontSize: 11, color: "#666" }}>
              Linked fuel/lube visits: <strong>{result.body.reconciliation.dispensed_quantities?.visit_count ?? 0}</strong>. {" "}
              <button data-testid="strr-form-close-result-open-detail" type="button"
                      onClick={() => navigate(`/shop/service-truck-reconciliation/${result.body.id}`)}
                      style={{ padding: "2px 8px", fontSize: 11 }}>Open detail →</button>
            </div>
          </Card>
        )}

        <div data-testid="strr-form-doctrine" style={{ marginTop: 24, padding: 12, fontSize: 11, color: "#666",
              background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: 4 }}>
          Doctrine · Operational accountability only · NO accounting · NO cost · NO fuel tax · NO PO numbers · NO theft accusations.
          Dispensed totals are pulled from submitted Fuel/Lube Visit Records for the same truck and date. Variance language: <em>Within expected range</em> / <em>Needs review</em> / <em>Significant variance</em> / <em>Incomplete</em>.
        </div>
      </PortalShell>
    </div>
  );
}
