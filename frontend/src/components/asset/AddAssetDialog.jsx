// Track 13.31B-D7 · Add Asset admin form.
// Mounted from /admin/asset-admin header. Uses existing POST
// /api/asset-spine/assets endpoint — no new collection. Operator-friendly
// language throughout. Photos/documents NEVER required.

import { useEffect, useMemo, useRef, useState } from "react";
import { X as XIcon, Loader2, Plus, CheckCircle2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

const LIFECYCLE_OPTIONS = [
  "Active",
  "In Repair",
  "Reserved",
  "Awaiting Setup",
  "Retired",
  "Disposed",
];

export default function AddAssetDialog({ open, onClose, onCreated }) {
  const [taxonomy, setTaxonomy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const firstRef = useRef(null);

  // Form state
  const [assetNumber, setAssetNumber] = useState("");
  const [assetName, setAssetName] = useState("");
  const [assetClass, setAssetClass] = useState("");
  const [assetType, setAssetType] = useState("");
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [year, setYear] = useState("");
  const [serial, setSerial] = useState("");
  const [vin, setVin] = useState("");
  const [plate, setPlate] = useState("");
  const [lifecycle, setLifecycle] = useState("Active");
  const [division, setDivision] = useState("");
  const [notes, setNotes] = useState("");
  // Renewals
  const [registrationExp, setRegistrationExp] = useState("");
  const [insuranceExp, setInsuranceExp] = useState("");
  const [warrantyExp, setWarrantyExp] = useState("");
  const [calibrationExp, setCalibrationExp] = useState("");
  const [dotExp, setDotExp] = useState("");
  // Verify intent
  const [verifyTaxonomy, setVerifyTaxonomy] = useState(true);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const r = await api.get("/asset-spine/taxonomy");
        if (cancelled) return;
        setTaxonomy(r.data);
      } catch {
        toast.error("Unable to load asset taxonomy.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    setTimeout(() => firstRef.current?.focus(), 150);
    return () => { cancelled = true; };
  }, [open]);

  const types = useMemo(() => {
    if (!taxonomy || !assetClass) return [];
    return taxonomy.asset_types_by_class[assetClass] || [];
  }, [taxonomy, assetClass]);

  const behavior = useMemo(() => {
    if (!taxonomy || !assetType) return {};
    return taxonomy.behaviors?.[assetType] || {};
  }, [taxonomy, assetType]);

  const warnings = useMemo(() => {
    const w = [];
    if (behavior.calibration_required && !calibrationExp) {
      w.push("Calibration tracking is suggested for this asset type — upload a Calibration Certificate later.");
    }
    if (behavior.requires_registration && !registrationExp) {
      w.push("Registration tracking is suggested — upload a Registration document later.");
    }
    if (behavior.dot_required && !dotExp) {
      w.push("DOT tracking is suggested — upload a DOT Document later.");
    }
    if ((assetClass === "Truck" || assetClass === "Trailer") && !vin) {
      w.push("VIN is strongly suggested for trucks and trailers.");
    }
    if ((assetClass === "GPS / Machine Control" ||
         assetClass === "Survey Equipment" ||
         assetClass === "Technology Equipment") && !serial) {
      w.push("Serial number is strongly suggested for this asset type.");
    }
    return w;
  }, [behavior, calibrationExp, registrationExp, dotExp, vin, serial, assetClass]);

  if (!open) return null;

  const reset = () => {
    setAssetNumber(""); setAssetName(""); setAssetClass(""); setAssetType("");
    setMake(""); setModel(""); setYear(""); setSerial(""); setVin(""); setPlate("");
    setLifecycle("Active"); setDivision(""); setNotes("");
    setRegistrationExp(""); setInsuranceExp(""); setWarrantyExp("");
    setCalibrationExp(""); setDotExp(""); setVerifyTaxonomy(true);
  };

  const submit = async (e) => {
    e.preventDefault();
    if (busy) return;
    if (!assetNumber.trim()) return toast.error("Unit Number / Asset Tag is required.");
    if (!assetClass) return toast.error("Asset Class is required.");
    if (!assetType) return toast.error("Asset Type is required.");
    if (!lifecycle) return toast.error("Lifecycle Status is required.");
    setBusy(true);
    try {
      const body = {
        asset_number: assetNumber.trim(),
        asset_name: assetName.trim() || assetNumber.trim(),
        asset_class: assetClass,
        asset_type: assetType,
        taxonomy_verified: verifyTaxonomy,
        taxonomy_source: "manual_admin",
        lifecycle_status: lifecycle,
        make: make.trim() || null,
        model: model.trim() || null,
        year: year ? parseInt(year, 10) : null,
        serial_number: serial.trim() || null,
        vin: vin.trim() || null,
        license_plate: plate.trim() || null,
        division: division.trim() || null,
        notes: notes.trim() || null,
        registration_expiration: registrationExp || null,
        insurance_expiration: insuranceExp || null,
        warranty_expiration: warrantyExp || null,
        calibration_expiration: calibrationExp || null,
        dot_expiration: dotExp || null,
      };
      const r = await api.post("/asset-spine/assets", body);
      toast.success(`Added ${assetType} · ${assetNumber.trim()}`);
      reset();
      onCreated?.(r.data);
      onClose();
    } catch (e2) {
      toast.error(e2?.response?.data?.detail || "Unable to add asset.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
      data-testid="add-asset-dialog"
    >
      <form
        onSubmit={submit}
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
      >
        <div className="sticky top-0 bg-white border-b border-slate-200 px-5 py-3 flex items-center justify-between">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">
              Asset Administration
            </div>
            <div className="font-bold text-lg">Add Asset</div>
          </div>
          <Button type="button" size="sm" variant="ghost" onClick={onClose} data-testid="add-asset-close">
            <XIcon className="w-4 h-4" />
          </Button>
        </div>

        <div className="p-5 space-y-3">
          {loading ? (
            <div className="text-center text-slate-500 py-10">
              <Loader2 className="w-5 h-5 animate-spin mx-auto" />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Field label="Unit Number / Asset Tag *" required>
                  <input
                    ref={firstRef}
                    type="text" value={assetNumber} onChange={(e) => setAssetNumber(e.target.value)}
                    placeholder="e.g. EX-101 · TS-04 · IT-iPad-01"
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                    data-testid="add-asset-number"
                  />
                </Field>
                <Field label="Display Name (optional)">
                  <input
                    type="text" value={assetName} onChange={(e) => setAssetName(e.target.value)}
                    placeholder="Defaults to Unit Number"
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                    data-testid="add-asset-name"
                  />
                </Field>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Field label="Asset Class *" required>
                  <select
                    value={assetClass}
                    onChange={(e) => { setAssetClass(e.target.value); setAssetType(""); }}
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                    data-testid="add-asset-class"
                  >
                    <option value="">— Select class —</option>
                    {(taxonomy?.asset_classes || []).map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </Field>
                <Field label="Asset Type *" required>
                  <select
                    value={assetType} onChange={(e) => setAssetType(e.target.value)}
                    disabled={!assetClass}
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm disabled:bg-slate-100"
                    data-testid="add-asset-type"
                  >
                    <option value="">— Select type —</option>
                    {types.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </Field>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <Field label="Make">
                  <input type="text" value={make} onChange={(e) => setMake(e.target.value)}
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                    data-testid="add-asset-make" />
                </Field>
                <Field label="Model">
                  <input type="text" value={model} onChange={(e) => setModel(e.target.value)}
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                    data-testid="add-asset-model" />
                </Field>
                <Field label="Year">
                  <input type="number" value={year} onChange={(e) => setYear(e.target.value)}
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                    data-testid="add-asset-year" />
                </Field>
                <Field label="Lifecycle *" required>
                  <select value={lifecycle} onChange={(e) => setLifecycle(e.target.value)}
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                    data-testid="add-asset-lifecycle">
                    {LIFECYCLE_OPTIONS.map((l) => <option key={l} value={l}>{l}</option>)}
                  </select>
                </Field>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <Field label="Serial Number">
                  <input type="text" value={serial} onChange={(e) => setSerial(e.target.value)}
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                    data-testid="add-asset-serial" />
                </Field>
                <Field label="VIN">
                  <input type="text" value={vin} onChange={(e) => setVin(e.target.value)}
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                    data-testid="add-asset-vin" />
                </Field>
                <Field label="License Plate">
                  <input type="text" value={plate} onChange={(e) => setPlate(e.target.value)}
                    className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                    data-testid="add-asset-plate" />
                </Field>
              </div>

              <Field label="Division / Company">
                <input type="text" value={division} onChange={(e) => setDivision(e.target.value)}
                  placeholder="e.g. MASCI Asphalt · MASCI Earthwork"
                  className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                  data-testid="add-asset-division" />
              </Field>

              <details className="rounded border border-slate-200 bg-slate-50/50 px-3 py-2" data-testid="add-asset-renewals-section">
                <summary className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold cursor-pointer">
                  Optional renewals
                </summary>
                <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <Field label="Registration Expires"><input type="date" value={registrationExp} onChange={(e) => setRegistrationExp(e.target.value)} className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm" data-testid="add-asset-reg-exp" /></Field>
                  <Field label="Insurance Expires"><input type="date" value={insuranceExp} onChange={(e) => setInsuranceExp(e.target.value)} className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm" data-testid="add-asset-ins-exp" /></Field>
                  <Field label="DOT Expires"><input type="date" value={dotExp} onChange={(e) => setDotExp(e.target.value)} className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm" data-testid="add-asset-dot-exp" /></Field>
                  <Field label="Calibration Expires"><input type="date" value={calibrationExp} onChange={(e) => setCalibrationExp(e.target.value)} className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm" data-testid="add-asset-cal-exp" /></Field>
                  <Field label="Warranty Expires"><input type="date" value={warrantyExp} onChange={(e) => setWarrantyExp(e.target.value)} className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm" data-testid="add-asset-war-exp" /></Field>
                </div>
              </details>

              <Field label="Notes (optional)">
                <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2}
                  className="w-full border-2 border-slate-300 rounded px-2 py-2 text-sm"
                  data-testid="add-asset-notes" />
              </Field>

              {warnings.length > 0 && (
                <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm" data-testid="add-asset-warnings">
                  <div className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-amber-900 font-bold mb-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Suggestions
                  </div>
                  <ul className="list-disc pl-5 space-y-0.5 text-amber-900">
                    {warnings.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                  <div className="text-[11px] text-amber-700 mt-1">
                    These are suggestions only. The asset can still be added.
                  </div>
                </div>
              )}

              <label className="flex items-start gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={verifyTaxonomy} onChange={(e) => setVerifyTaxonomy(e.target.checked)}
                  className="mt-1" data-testid="add-asset-verify" />
                <span>
                  <span className="font-bold">Mark classification as verified.</span>
                  {" "}Uncheck if this asset still needs review.
                </span>
              </label>
            </>
          )}
        </div>

        <div className="sticky bottom-0 bg-white border-t border-slate-200 px-5 py-3 flex items-center justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={busy}>Cancel</Button>
          <Button type="submit" disabled={busy || loading}
            className="bg-red-700 hover:bg-red-800 text-white"
            data-testid="add-asset-submit">
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Plus className="w-3.5 h-3.5 mr-1" />}
            Add Asset
          </Button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, required, children }) {
  return (
    <label className="block">
      <div className={`text-[10px] font-mono uppercase tracking-[0.16em] font-bold mb-1 ${required ? "text-slate-700" : "text-slate-600"}`}>
        {label}
      </div>
      {children}
    </label>
  );
}
