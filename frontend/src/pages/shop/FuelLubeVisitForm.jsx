// Track 13.29 — Fuel/Lube Visit form.
//
// MOUNTED AT: /shop/fuel-lube/new (behind RequireShop).
// Backend: POST /api/shop/fuel-lube/visits.
//
// One visit = one project/job stop. Multiple equipment lines per visit.
// Issue lines spawn `fleet_defects` rows + notifications. Service lines
// project into Asset Service Event Backbone (Track 13.26).
//
// Hard locks honored:
//   - No cost / no accounting fields.
//   - No driver login (read-write via Shop auth or Admin override only).
//   - Issues do NOT clear the unit (Shop Repair ≠ RTS doctrine).
import React, { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import SubmissionConfirmation from "@/components/submission/SubmissionConfirmation";
import { buildSubmissionConfirmation } from "@/lib/submissionConfirmation";
import { PortalShell, Card } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";
import ShopSelector from "@/components/shop/ShopSelector";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  return buildScopedPortalAuthHeaders(["admin", "shop"], { "Content-Type": "application/json" });
}

const EMPTY_LINE = {
  unit_number: "", equipment_name: "",
  meter_hours: "", odometer_miles: "",
  red_diesel_gallons: 0, clear_diesel_gallons: 0, gasoline_gallons: 0, def_gallons: 0,
  engine_oil_quarts: 0, hydraulic_oil_quarts: 0, coolant_quarts: 0,
  transmission_fluid_quarts: 0, gear_oil_quarts: 0,
  greased: false, not_greased_reason: "",
  issue_found: false, issue_severity: "", issue_category: "", issue_description: "",
  issue_photo_ids: "",
  line_notes: "",
};

const SEVERITIES = ["Monitor", "Needs Review", "Out of Service Recommended", "Critical"];

function Num({ value, onChange, testid, step = "1", placeholder = "0", style = {} }) {
  return (
    <input
      data-testid={testid}
      type="number" min="0" step={step}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
      style={{ padding: 5, fontSize: 12, width: "100%", ...style }}
    />
  );
}

function EquipmentLineRow({ line, idx, onPatch, onRemove }) {
  const setField = (field) => (value) => onPatch(idx, { ...line, [field]: value });
  const isCriticalIssue = line.issue_found && ["Out of Service Recommended", "Critical"].includes(line.issue_severity);
  return (
    <Card data-testid={`fuel-lube-line-${idx}`}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <div style={{ fontSize: 12, fontWeight: 700 }}>Equipment line #{idx + 1}</div>
        <button
          data-testid={`fuel-lube-line-remove-${idx}`}
          type="button"
          onClick={() => onRemove(idx)}
          style={{ padding: "3px 8px", fontSize: 11 }}
        >Remove</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 6, marginBottom: 6 }}>
        <label style={{ fontSize: 11 }}>Unit*
          <ShopSelector
            kind="unit"
            testIdPrefix={`fuel-lube-line-unit-${idx}`}
            value={line.unit_number}
            onChange={(row) => {
              onPatch(idx, "unit_number", row?.unit_number || "");
              if (row?.equipment_name) onPatch(idx, "equipment_name", row.equipment_name);
            }}
            required
          />
        </label>
        <label style={{ fontSize: 11 }}>Equipment name (auto-fills)
          <input value={line.equipment_name} onChange={(e) => setField("equipment_name")(e.target.value)} style={{ padding: 5, fontSize: 12, width: "100%" }} placeholder="CAT 336" />
        </label>
        <label style={{ fontSize: 11 }}>Meter hours
          <Num value={line.meter_hours} onChange={setField("meter_hours")} step="0.1" testid={`fuel-lube-line-meter-${idx}`} />
        </label>
        <label style={{ fontSize: 11 }}>Odometer miles
          <Num value={line.odometer_miles} onChange={setField("odometer_miles")} step="1" testid={`fuel-lube-line-odo-${idx}`} />
        </label>
      </div>

      <div style={{ fontSize: 11, fontWeight: 700, color: "#666", marginTop: 4 }}>Fuel (gallons)</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 6 }}>
        <label style={{ fontSize: 11 }}>Red diesel
          <Num value={line.red_diesel_gallons} onChange={setField("red_diesel_gallons")} step="0.1" testid={`fuel-lube-line-red-diesel-${idx}`} />
        </label>
        <label style={{ fontSize: 11 }}>Clear diesel
          <Num value={line.clear_diesel_gallons} onChange={setField("clear_diesel_gallons")} step="0.1" testid={`fuel-lube-line-clear-diesel-${idx}`} />
        </label>
        <label style={{ fontSize: 11 }}>Gasoline
          <Num value={line.gasoline_gallons} onChange={setField("gasoline_gallons")} step="0.1" />
        </label>
        <label style={{ fontSize: 11 }}>DEF
          <Num value={line.def_gallons} onChange={setField("def_gallons")} step="0.1" testid={`fuel-lube-line-def-${idx}`} />
        </label>
      </div>

      <div style={{ fontSize: 11, fontWeight: 700, color: "#666", marginTop: 8 }}>Fluids (quarts)</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr", gap: 6 }}>
        <label style={{ fontSize: 11 }}>Engine oil
          <Num value={line.engine_oil_quarts} onChange={setField("engine_oil_quarts")} step="0.1" />
        </label>
        <label style={{ fontSize: 11 }}>Hyd oil
          <Num value={line.hydraulic_oil_quarts} onChange={setField("hydraulic_oil_quarts")} step="0.1" />
        </label>
        <label style={{ fontSize: 11 }}>Coolant
          <Num value={line.coolant_quarts} onChange={setField("coolant_quarts")} step="0.1" />
        </label>
        <label style={{ fontSize: 11 }}>Trans fluid
          <Num value={line.transmission_fluid_quarts} onChange={setField("transmission_fluid_quarts")} step="0.1" />
        </label>
        <label style={{ fontSize: 11 }}>Gear oil
          <Num value={line.gear_oil_quarts} onChange={setField("gear_oil_quarts")} step="0.1" />
        </label>
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 8 }}>
        <label style={{ fontSize: 12 }}>
          <input data-testid={`fuel-lube-line-greased-${idx}`} type="checkbox" checked={line.greased} onChange={(e) => setField("greased")(e.target.checked)} />
          {" "}Greased
        </label>
        {!line.greased && (
          <input
            placeholder="Reason not greased (e.g. fittings stripped)"
            value={line.not_greased_reason}
            onChange={(e) => setField("not_greased_reason")(e.target.value)}
            style={{ padding: 5, fontSize: 12, flex: 1 }}
          />
        )}
      </div>

      <label style={{ fontSize: 11, display: "block", marginTop: 8 }}>Line notes
        <input value={line.line_notes} onChange={(e) => setField("line_notes")(e.target.value)} style={{ padding: 5, fontSize: 12, width: "100%" }} placeholder="Optional — observed leaks, anything noteworthy…" />
      </label>

      <div style={{ marginTop: 10, padding: 8, background: line.issue_found ? "#fdf3f0" : "#f4f6f8", borderRadius: 4 }}>
        <label style={{ fontSize: 12, fontWeight: 700 }}>
          <input data-testid={`fuel-lube-line-issue-found-${idx}`} type="checkbox" checked={line.issue_found} onChange={(e) => setField("issue_found")(e.target.checked)} />
          {" "}Issue found
        </label>
        {line.issue_found && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginTop: 6 }}>
            <label style={{ fontSize: 11 }}>Severity*
              <select data-testid={`fuel-lube-line-issue-severity-${idx}`} value={line.issue_severity} onChange={(e) => setField("issue_severity")(e.target.value)} style={{ padding: 5, fontSize: 12, width: "100%" }}>
                <option value="">Choose…</option>
                {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <label style={{ fontSize: 11 }}>Category*
              <input data-testid={`fuel-lube-line-issue-category-${idx}`} value={line.issue_category} onChange={(e) => setField("issue_category")(e.target.value)} style={{ padding: 5, fontSize: 12, width: "100%" }} placeholder="e.g. hydraulic, brakes, electrical" />
            </label>
            <label style={{ fontSize: 11, gridColumn: "1 / span 2" }}>Description* {isCriticalIssue ? "(min 25 chars)" : "(min 10 chars)"}
              <textarea data-testid={`fuel-lube-line-issue-description-${idx}`} rows={2} value={line.issue_description} onChange={(e) => setField("issue_description")(e.target.value)} style={{ padding: 5, fontSize: 12, width: "100%", fontFamily: "inherit" }} placeholder="Describe what you saw. 'broken' alone is not enough." />
              <div style={{ fontSize: 10, color: "#666" }}>{(line.issue_description || "").trim().length} characters</div>
            </label>
            <label style={{ fontSize: 11, gridColumn: "1 / span 2" }}>Photo ids* (comma-separated, ≥1 required)
              <input data-testid={`fuel-lube-line-issue-photos-${idx}`} value={line.issue_photo_ids} onChange={(e) => setField("issue_photo_ids")(e.target.value)} style={{ padding: 5, fontSize: 12, width: "100%" }} placeholder="att-1, att-2 — operational_attachments.id values" />
            </label>
          </div>
        )}
      </div>
    </Card>
  );
}

export default function FuelLubeVisitForm() {
  const { t } = useT();
  const navigate = useNavigate();
  const today = new Date().toISOString().slice(0, 10);
  const blankVisit = {
    visit_date: today,
    project_number: "",
    project_name: "",
    fuel_lube_truck_unit: "",
    fuel_lube_tech_id: "",
    fuel_lube_tech_name: "",
    arrival_time: "",
    departure_time: "",
    location_source: "manual",
    submitted_by: "",
  };
  const [visit, setVisit] = useState({
    ...blankVisit,
  });
  const [lines, setLines] = useState([{ ...EMPTY_LINE }]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  const resetForm = () => {
    setVisit({ ...blankVisit });
    setLines([{ ...EMPTY_LINE }]);
    setError("");
    setResult(null);
    setSubmitting(false);
  };

  const confirmation = result ? buildSubmissionConfirmation({
    workflowKey: "fuel-lube-visit",
    documentNumber: result.doc_id || result.id || "",
    submittedAt: result.submitted_at,
    submittedBy: result.submitted_by,
    project: result.project_name
      ? `${result.project_number} · ${result.project_name}`
      : result.project_number,
    startAnother: { label: "Start Another", onClick: resetForm },
    returnToPortal: { label: "Return to Portal", to: "/shop" },
    openRecord: { label: "Open Submitted Record", to: `/shop/fuel-lube/${encodeURIComponent(result.id)}` },
  }) : null;

  const totals = useMemo(() => {
    const sum = (k) => lines.reduce((s, l) => s + (parseFloat(l[k]) || 0), 0);
    return {
      red_diesel: sum("red_diesel_gallons"),
      clear_diesel: sum("clear_diesel_gallons"),
      gasoline: sum("gasoline_gallons"),
      def: sum("def_gallons"),
      engine_oil: sum("engine_oil_quarts"),
      hyd_oil: sum("hydraulic_oil_quarts"),
      coolant: sum("coolant_quarts"),
      trans: sum("transmission_fluid_quarts"),
      gear: sum("gear_oil_quarts"),
      units: lines.length,
      issues: lines.filter((l) => l.issue_found).length,
      greased: lines.filter((l) => l.greased).length,
    };
  }, [lines]);

  const onPatch = (idx, patch) => setLines((cur) => cur.map((l, i) => (i === idx ? patch : l)));
  const onAdd = () => setLines((cur) => [...cur, { ...EMPTY_LINE }]);
  const onRemove = (idx) => setLines((cur) => cur.filter((_, i) => i !== idx));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setSubmitting(true); setResult(null);
    try {
      const equipment_lines = lines.map((l) => ({
        ...l,
        meter_hours: l.meter_hours === "" ? null : parseFloat(l.meter_hours),
        odometer_miles: l.odometer_miles === "" ? null : parseFloat(l.odometer_miles),
        issue_photo_ids: (l.issue_photo_ids || "")
          .split(",").map((s) => s.trim()).filter(Boolean),
      }));
      const body = { ...visit, equipment_lines };
      const r = await fetch(`${API}/api/shop/fuel-lube/visits`, {
        method: "POST", headers: authHeaders(), body: JSON.stringify(body),
      });
      const data = await r.json().catch(() => null);
      if (!r.ok) throw new Error((data && data.detail) || `HTTP ${r.status}`);
      setResult(data);
      // optional: redirect to manager queue to see newly created defects
    } catch (ex) {
      setError(ex.message || "Submit failed.");
    }
    setSubmitting(false);
  };

  if (confirmation) {
    return <SubmissionConfirmation confirmation={confirmation} />;
  }

  return (
    <div data-testid="fuel-lube-visit-form-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole={t("Shop Portal · Fuel / Lube Visit")}
        pageTitle={t("Fuel / Lube Visit Record")}
        subtitle={t("One job visit · multiple equipment lines. Each service entry is saved to the unit's history. Issues create shop defects automatically.")}
        primaryActions={<BackToShopLink testId="fuel-lube-visit-form-back-to-shop" />}
      >
        {result && (
          <div data-testid="fuel-lube-visit-form-success" style={{ background: "#e6f6ec", padding: 12, borderRadius: 4, color: "#137a48", fontSize: 12, marginBottom: 16 }}>
            Visit <code>{result.id}</code> submitted. Units serviced: {result.totals.units_serviced} · Issues found: {result.totals.issues_found_count} · Defects created: {(result.defect_ids || []).length}.
            {" "}<button data-testid="fuel-lube-visit-form-new" type="button" onClick={() => { setResult(null); setLines([{ ...EMPTY_LINE }]); }} style={{ marginLeft: 6 }}>Start another</button>
            {" "}<button type="button" onClick={() => navigate("/shop/manager/queue")}>View manager queue</button>
          </div>
        )}
        {error && (
          <div data-testid="fuel-lube-visit-form-error" style={{ background: "#fae2e0", padding: 12, borderRadius: 4, color: "#a33", fontSize: 12, marginBottom: 16 }}>{error}</div>
        )}

        <form onSubmit={handleSubmit}>
          <Card data-testid="fuel-lube-visit-form-header">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              <label style={{ fontSize: 11 }}>Visit date*
                <input data-testid="fuel-lube-visit-form-date" type="date" value={visit.visit_date} onChange={(e) => setVisit({ ...visit, visit_date: e.target.value })} style={{ padding: 6, fontSize: 12, width: "100%" }} required />
              </label>
              <label style={{ fontSize: 11 }}>Project / Job*
                <ShopSelector
                  kind="project"
                  testIdPrefix="fuel-lube-visit-form-project"
                  value={visit.project_number}
                  onChange={(row) => setVisit({
                    ...visit,
                    project_number: row?.project_number || "",
                    project_name:   row?.project_name   || (row?.manual ? visit.project_name : ""),
                  })}
                  required
                />
              </label>
              <label style={{ fontSize: 11 }}>Project name (auto-fills from selection)
                <input data-testid="fuel-lube-visit-form-project-name" value={visit.project_name} onChange={(e) => setVisit({ ...visit, project_name: e.target.value })} placeholder="e.g. University High School" style={{ padding: 6, fontSize: 12, width: "100%" }} />
              </label>
              <label style={{ fontSize: 11 }}>Fuel/Lube truck*
                <ShopSelector
                  kind="unit"
                  testIdPrefix="fuel-lube-visit-form-truck"
                  value={visit.fuel_lube_truck_unit}
                  onChange={(row) => setVisit({ ...visit, fuel_lube_truck_unit: row?.unit_number || "" })}
                  required
                />
              </label>
              <label style={{ fontSize: 11 }}>Tech name*
                <input data-testid="fuel-lube-visit-form-tech-name" value={visit.fuel_lube_tech_name} onChange={(e) => setVisit({ ...visit, fuel_lube_tech_name: e.target.value })} style={{ padding: 6, fontSize: 12, width: "100%" }} required />
              </label>
              <label style={{ fontSize: 11 }}>Tech employee id
                <input value={visit.fuel_lube_tech_id} onChange={(e) => setVisit({ ...visit, fuel_lube_tech_id: e.target.value })} placeholder="Optional" style={{ padding: 6, fontSize: 12, width: "100%" }} />
              </label>
              <label style={{ fontSize: 11 }}>Arrival time
                <input type="time" value={visit.arrival_time} onChange={(e) => setVisit({ ...visit, arrival_time: e.target.value })} style={{ padding: 6, fontSize: 12, width: "100%" }} />
              </label>
              <label style={{ fontSize: 11 }}>Departure time
                <input type="time" value={visit.departure_time} onChange={(e) => setVisit({ ...visit, departure_time: e.target.value })} style={{ padding: 6, fontSize: 12, width: "100%" }} />
              </label>
              <label style={{ fontSize: 11 }}>Location source
                <select value={visit.location_source} onChange={(e) => setVisit({ ...visit, location_source: e.target.value })} style={{ padding: 6, fontSize: 12, width: "100%" }}>
                  <option value="manual">Manual</option>
                  <option value="motive">Motive geofence</option>
                  <option value="geofence">Custom geofence</option>
                </select>
              </label>
            </div>
          </Card>

          <div style={{ marginTop: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: ".05em", color: "#666" }}>Equipment lines ({lines.length})</h3>
            <button data-testid="fuel-lube-visit-form-add-line" type="button" onClick={onAdd} style={{ padding: "6px 12px", fontSize: 12 }}>+ Add equipment line</button>
          </div>
          <div style={{ display: "grid", gap: 10 }}>
            {lines.map((l, i) => (
              <EquipmentLineRow key={i} line={l} idx={i} onPatch={onPatch} onRemove={onRemove} />
            ))}
          </div>

          <Card data-testid="fuel-lube-visit-form-totals" style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Live totals</div>
            <div data-testid="fuel-lube-visit-form-totals-grid" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 6, fontSize: 11 }}>
              <div data-testid="fuel-lube-totals-red-diesel">Red diesel · {totals.red_diesel.toFixed(1)} gal</div>
              <div data-testid="fuel-lube-totals-clear-diesel">Clear diesel · {totals.clear_diesel.toFixed(1)} gal</div>
              <div>Gasoline · {totals.gasoline.toFixed(1)} gal</div>
              <div data-testid="fuel-lube-totals-def">DEF · {totals.def.toFixed(1)} gal</div>
              <div>Engine oil · {totals.engine_oil.toFixed(1)} qt</div>
              <div>Hyd oil · {totals.hyd_oil.toFixed(1)} qt</div>
              <div>Coolant · {totals.coolant.toFixed(1)} qt</div>
              <div>Trans fluid · {totals.trans.toFixed(1)} qt</div>
              <div>Gear oil · {totals.gear.toFixed(1)} qt</div>
              <div>Units serviced · {totals.units}</div>
              <div>Greased · {totals.greased}</div>
              <div style={{ color: totals.issues > 0 ? "#a33" : "#666", fontWeight: 700 }}>Issues found · {totals.issues}</div>
            </div>
          </Card>

          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 16 }}>
            <button
              data-testid="fuel-lube-visit-form-submit"
              type="submit"
              disabled={submitting}
              style={{
                padding: "8px 16px", fontSize: 13, fontWeight: 700,
                background: submitting ? "#aaa" : "var(--brand-primary, #1b4965)",
                color: "#fff", border: "none", borderRadius: 4,
              }}
            >{submitting ? "Submitting…" : "Submit visit"}</button>
          </div>
        </form>

        <div data-testid="fuel-lube-visit-form-footer" style={{
          marginTop: 24, padding: 12, fontSize: 11, color: "#666",
          background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: 4,
        }}>
          Each service entry is saved to the unit&apos;s history. Issues you flag here become shop defects automatically.
          Repair complete still requires return-to-service verification by Dispatch.
        </div>
      </PortalShell>
    </div>
  );
}
