// Track 13.28 Phase 2 — Repair completion form.
//
// Captures repair notes (minimum 10 chars) + multi-row parts_used.
// Parts data is per-repair-event historical capture (not inventory).
// Cost / accounting fields intentionally omitted (out of scope).
//
// Posts to: POST /api/shop/fleet/defects/{id}/repair
// Backend payload model: DefectRepairPayload (fleet_ops.py).
import React, { useState } from "react";

const EMPTY_PART = { part_name: "", part_number: "", manufacturer: "", supplier: "", quantity: 1, notes: "" };
const EMPTY_ORDER = {
  part_name: "", part_number: "", manufacturer: "", supplier: "",
  quantity: 1, ordered_date: "", expected_date: "", order_status: "open", notes: "",
};

export default function RepairCompletionForm({
  defect,
  actorName,
  onSubmit,        // async ({notes, photos, parts_used, parts_on_order}) => void
  onCancel,
  submitting = false,
  testidPrefix = "repair-form",
}) {
  const [notes, setNotes] = useState("");
  const [partsUsed, setPartsUsed] = useState([{ ...EMPTY_PART }]);
  const [partsOnOrder, setPartsOnOrder] = useState([]);
  const [error, setError] = useState("");

  const validPartsUsed = partsUsed.filter((p) => (p.part_name || "").trim().length > 0);
  const validPartsOnOrder = partsOnOrder.filter((p) => (p.part_name || "").trim().length > 0);

  const noteOk = (notes || "").trim().length >= 10;
  const partsOk = validPartsUsed.length > 0;
  const canSubmit = (noteOk || partsOk) && !submitting;

  const addPartUsed = () => setPartsUsed((cur) => [...cur, { ...EMPTY_PART }]);
  const removePartUsed = (i) => setPartsUsed((cur) => cur.filter((_, idx) => idx !== i));
  const updatePartUsed = (i, field, val) =>
    setPartsUsed((cur) => cur.map((p, idx) => (idx === i ? { ...p, [field]: val } : p)));

  const addPartOrder = () => setPartsOnOrder((cur) => [...cur, { ...EMPTY_ORDER }]);
  const removePartOrder = (i) => setPartsOnOrder((cur) => cur.filter((_, idx) => idx !== i));
  const updatePartOrder = (i, field, val) =>
    setPartsOnOrder((cur) => cur.map((p, idx) => (idx === i ? { ...p, [field]: val } : p)));

  const handleSubmit = async () => {
    setError("");
    if (!canSubmit) {
      setError("Add at least 10 characters of repair notes or one parts-used row.");
      return;
    }
    try {
      await onSubmit({
        notes: (notes || "").trim(),
        photos: [],
        parts_used: validPartsUsed,
        parts_on_order: validPartsOnOrder,
      });
    } catch (e) {
      setError((e && e.message) || "Repair completion failed.");
    }
  };

  return (
    <div data-testid={`${testidPrefix}-root`} style={{ display: "grid", gap: 12 }}>
      <div>
        <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 4 }}>Defect</div>
        <div data-testid={`${testidPrefix}-defect-summary`} style={{ fontSize: 13 }}>
          {(defect.item_text || defect.category || "(no description)")} · severity {defect.severity || "—"} ·
          unit {defect.trailer_unit_number || defect.truck_unit_number || "—"}
        </div>
      </div>

      <label style={{ display: "block" }}>
        <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 4 }}>
          Repair notes <span style={{ color: noteOk ? "var(--brand-success, #137a48)" : "#a33" }}>· min 10 chars (or 1 parts row)</span>
        </div>
        <textarea
          data-testid={`${testidPrefix}-notes`}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          placeholder="What was inspected and what was done (parts replaced, adjustments, torque values, etc.)"
          style={{ width: "100%", padding: 8, fontSize: 13, fontFamily: "inherit" }}
        />
        <div style={{ fontSize: 11, color: "#666" }}>{(notes || "").trim().length} characters</div>
      </label>

      <section data-testid={`${testidPrefix}-parts-used-section`} style={{ borderTop: "1px solid #ddd", paddingTop: 8 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
          <div style={{ fontSize: 12, fontWeight: 700 }}>Parts used ({validPartsUsed.length})</div>
          <button
            data-testid={`${testidPrefix}-parts-used-add`}
            type="button"
            onClick={addPartUsed}
            style={{ fontSize: 12, padding: "4px 8px" }}
          >+ Add part</button>
        </div>
        {partsUsed.map((p, i) => (
          <div key={i} data-testid={`${testidPrefix}-parts-used-row-${i}`} style={{
            display: "grid",
            gridTemplateColumns: "2fr 1.4fr 1.2fr 1.2fr 0.6fr 0.6fr",
            gap: 6, marginBottom: 4,
          }}>
            <input data-testid={`${testidPrefix}-parts-used-name-${i}`} placeholder="Part name (e.g. fuel filter)" value={p.part_name} onChange={(e) => updatePartUsed(i, "part_name", e.target.value)} style={{ padding: 6, fontSize: 12 }} />
            <input data-testid={`${testidPrefix}-parts-used-number-${i}`} placeholder="Part #" value={p.part_number} onChange={(e) => updatePartUsed(i, "part_number", e.target.value)} style={{ padding: 6, fontSize: 12 }} />
            <input data-testid={`${testidPrefix}-parts-used-mfr-${i}`} placeholder="Manufacturer" value={p.manufacturer} onChange={(e) => updatePartUsed(i, "manufacturer", e.target.value)} style={{ padding: 6, fontSize: 12 }} />
            <input data-testid={`${testidPrefix}-parts-used-supplier-${i}`} placeholder="Supplier" value={p.supplier} onChange={(e) => updatePartUsed(i, "supplier", e.target.value)} style={{ padding: 6, fontSize: 12 }} />
            <input data-testid={`${testidPrefix}-parts-used-qty-${i}`} type="number" min="0" step="1" value={p.quantity} onChange={(e) => updatePartUsed(i, "quantity", parseFloat(e.target.value) || 0)} style={{ padding: 6, fontSize: 12 }} />
            <button data-testid={`${testidPrefix}-parts-used-remove-${i}`} type="button" onClick={() => removePartUsed(i)} style={{ fontSize: 11 }}>×</button>
          </div>
        ))}
      </section>

      <section data-testid={`${testidPrefix}-parts-order-section`} style={{ borderTop: "1px solid #ddd", paddingTop: 8 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
          <div style={{ fontSize: 12, fontWeight: 700 }}>
            Parts on order / waiting parts ({validPartsOnOrder.length})
            <span style={{ fontWeight: 400, fontSize: 11, color: "#666", marginLeft: 6 }}>
              · operational only · no cost · no purchasing
            </span>
          </div>
          <button
            data-testid={`${testidPrefix}-parts-order-add`}
            type="button"
            onClick={addPartOrder}
            style={{ fontSize: 12, padding: "4px 8px" }}
          >+ Add waiting part</button>
        </div>
        {partsOnOrder.length === 0 && (
          <div style={{ fontSize: 11, color: "#888" }}>No parts on order.</div>
        )}
        {partsOnOrder.map((p, i) => (
          <div key={i} data-testid={`${testidPrefix}-parts-order-row-${i}`} style={{
            display: "grid",
            gridTemplateColumns: "2fr 1.2fr 1.2fr 1.2fr 0.6fr 1fr 1fr 0.6fr",
            gap: 6, marginBottom: 4,
          }}>
            <input data-testid={`${testidPrefix}-parts-order-name-${i}`} placeholder="Part name" value={p.part_name} onChange={(e) => updatePartOrder(i, "part_name", e.target.value)} style={{ padding: 6, fontSize: 12 }} />
            <input placeholder="Part #" value={p.part_number} onChange={(e) => updatePartOrder(i, "part_number", e.target.value)} style={{ padding: 6, fontSize: 12 }} />
            <input placeholder="Manufacturer" value={p.manufacturer} onChange={(e) => updatePartOrder(i, "manufacturer", e.target.value)} style={{ padding: 6, fontSize: 12 }} />
            <input placeholder="Supplier" value={p.supplier} onChange={(e) => updatePartOrder(i, "supplier", e.target.value)} style={{ padding: 6, fontSize: 12 }} />
            <input type="number" min="0" step="1" value={p.quantity} onChange={(e) => updatePartOrder(i, "quantity", parseFloat(e.target.value) || 0)} style={{ padding: 6, fontSize: 12 }} />
            <input type="date" value={p.ordered_date} onChange={(e) => updatePartOrder(i, "ordered_date", e.target.value)} style={{ padding: 6, fontSize: 12 }} />
            <input type="date" value={p.expected_date} onChange={(e) => updatePartOrder(i, "expected_date", e.target.value)} style={{ padding: 6, fontSize: 12 }} />
            <button type="button" onClick={() => removePartOrder(i)} style={{ fontSize: 11 }}>×</button>
          </div>
        ))}
      </section>

      <div style={{ display: "flex", alignItems: "center", gap: 8, paddingTop: 4 }}>
        <span style={{ fontSize: 11, color: "#666", marginRight: "auto" }}>
          Actor: <strong>{actorName || "—"}</strong> · Repair Complete ≠ RTS · Dispatch must verify before unit returns to service.
        </span>
        {onCancel && (
          <button data-testid={`${testidPrefix}-cancel`} onClick={onCancel} type="button" disabled={submitting} style={{ padding: "6px 10px", fontSize: 12 }}>
            Cancel
          </button>
        )}
        <button
          data-testid={`${testidPrefix}-submit`}
          onClick={handleSubmit}
          type="button"
          disabled={!canSubmit}
          style={{
            padding: "6px 14px", fontSize: 13, fontWeight: 700,
            background: canSubmit ? "var(--brand-primary, #1b4965)" : "#aaa",
            color: "#fff", border: "none", borderRadius: 4,
            cursor: canSubmit ? "pointer" : "not-allowed",
          }}
        >
          {submitting ? "Saving…" : "Submit repair complete"}
        </button>
      </div>

      {error && (
        <div data-testid={`${testidPrefix}-error`} style={{ color: "#a33", fontSize: 12 }}>
          {error}
        </div>
      )}
    </div>
  );
}
