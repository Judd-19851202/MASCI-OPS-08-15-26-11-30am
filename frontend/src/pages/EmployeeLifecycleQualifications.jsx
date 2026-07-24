// TRACK 23.10-B · Employee Lifecycle · Professional Qualifications tab.
// Single source of truth = the Qualifications Engine registry.
// HR / Safety Training Admin / Admin can create · edit · suspend ·
// revoke · reinstate · renew qualifications. Everyone else: read-only.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Loader2, ShieldCheck, AlertTriangle, PauseCircle, Ban,
  RotateCw, Plus, ArrowLeft, Search, GraduationCap, ChevronDown,
  ChevronUp, X, RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import HrPageShell from "@/components/HrPageShell";
import {
  listQualificationTypes,
  qualificationSummary,
  employeeQualifications,
  createQualification,
  transitionQualification,
  renewQualification,
  listActiveQualifications,
} from "@/lib/qualificationsApi";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";

const inputCls =
  "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-600";

const STATUS_STYLE = {
  active:    "bg-emerald-100 text-emerald-900 border-emerald-300",
  expired:   "bg-red-100 text-red-900 border-red-300",
  suspended: "bg-amber-100 text-amber-900 border-amber-300",
  revoked:   "bg-slate-800 text-white border-slate-900",
  pending:   "bg-slate-100 text-slate-700 border-slate-300",
};

function StatusChip({ status }) {
  const cls = STATUS_STYLE[status] || STATUS_STYLE.pending;
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${cls}`}
      data-testid={`qual-status-${status}`}
    >
      {status || "unknown"}
    </span>
  );
}

async function fetchEmployees() {
  try {
    const url = `${process.env.REACT_APP_BACKEND_URL}/api/hr/employee-roster`;
    const hr = window.localStorage.getItem("hr_token") || "";
    const r = await fetch(url, { headers: buildScopedPortalAuthHeaders(["hr"]) });
    if (!r.ok) return [];
    const data = await r.json();
    return data.items || data || [];
  } catch {
    return [];
  }
}

// ─── Create/Edit modal ──────────────────────────────────────────────
function QualForm({ types, employees, onClose, onSaved, prefillEmployeeId }) {
  const [type, setType] = useState("COMPETENT_PERSON");
  const [employeeId, setEmployeeId] = useState(prefillEmployeeId || "");
  const [completedDate, setCompletedDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [expirationDate, setExpirationDate] = useState("");
  const [issuer, setIssuer] = useState("");
  const [certNo, setCertNo] = useState("");
  const [standard, setStandard] = useState("");
  const [notes, setNotes] = useState("");
  const [subCode, setSubCode] = useState("");
  const [manufacturer, setManufacturer] = useState("");
  const [productModel, setProductModel] = useState("");
  const [programName, setProgramName] = useState("");
  const [saving, setSaving] = useState(false);

  const spec = (types?.type_metadata_spec || {})[type];
  const requiresSubCode = (spec?.required || []).includes("sub_code");
  const requiresManufacturer = (spec?.required || []).includes("manufacturer");
  const requiresProgramName = (spec?.required || []).includes("program_name");

  const submit = async () => {
    if (!employeeId) {
      toast.error("Choose an employee");
      return;
    }
    const type_metadata = {};
    if (requiresSubCode) type_metadata.sub_code = subCode;
    if (requiresManufacturer) {
      type_metadata.manufacturer = manufacturer;
      type_metadata.product_model = productModel;
    }
    if (requiresProgramName) type_metadata.program_name = programName;
    setSaving(true);
    try {
      const row = await createQualification({
        employee_id: employeeId,
        qualification_type: type,
        completed_date: completedDate,
        expiration_date: expirationDate || null,
        issuing_organization: issuer,
        certificate_number: certNo,
        training_standard: standard,
        notes,
        type_metadata: Object.keys(type_metadata).length ? type_metadata : null,
      });
      toast.success("Qualification created");
      onSaved(row);
      onClose();
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || "Save failed";
      toast.error(String(msg));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/70 flex items-center justify-center z-50 p-4"
      data-testid="qual-form-overlay"
    >
      <Card className="max-w-2xl w-full p-5 bg-white overflow-y-auto max-h-[92vh]">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-mono uppercase tracking-[0.15em] font-bold text-lg">
            New Professional Qualification
          </h2>
          <button
            type="button"
            onClick={onClose}
            data-testid="qual-form-close"
            className="text-slate-500 hover:text-slate-900"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold">
            Qualification type
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className={`${inputCls} w-full mt-1 rounded px-2`}
              data-testid="qual-form-type"
            >
              {(types?.types || []).map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
          </label>
          <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold">
            Employee
            <select
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              className={`${inputCls} w-full mt-1 rounded px-2`}
              data-testid="qual-form-employee"
            >
              <option value="">— select —</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name || e.display_identity || e.id}
                </option>
              ))}
            </select>
          </label>

          <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold">
            Completed date
            <Input
              type="date"
              value={completedDate}
              onChange={(e) => setCompletedDate(e.target.value)}
              className={inputCls}
              data-testid="qual-form-completed"
            />
          </label>
          <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold">
            Expiration date <span className="text-slate-500">(optional)</span>
            <Input
              type="date"
              value={expirationDate}
              onChange={(e) => setExpirationDate(e.target.value)}
              className={inputCls}
              data-testid="qual-form-expiration"
            />
          </label>

          <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold md:col-span-2">
            Issuing organisation
            <Input
              value={issuer}
              onChange={(e) => setIssuer(e.target.value)}
              placeholder="MASCI, OSHA, CIT, etc."
              className={inputCls}
              data-testid="qual-form-issuer"
            />
          </label>

          <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold">
            Certificate number
            <Input
              value={certNo}
              onChange={(e) => setCertNo(e.target.value)}
              className={inputCls}
              data-testid="qual-form-cert-no"
            />
          </label>
          <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold">
            Training standard
            <Input
              value={standard}
              onChange={(e) => setStandard(e.target.value)}
              placeholder="e.g. OSHA 29 CFR 1926.651"
              className={inputCls}
              data-testid="qual-form-standard"
            />
          </label>

          {requiresSubCode && (
            <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-red-800">
              CDL Endorsement code *
              <Input
                value={subCode}
                onChange={(e) => setSubCode(e.target.value.toUpperCase())}
                maxLength={4}
                className={inputCls}
                data-testid="qual-form-sub-code"
              />
            </label>
          )}
          {requiresManufacturer && (
            <>
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-red-800">
                Manufacturer *
                <Input
                  value={manufacturer}
                  onChange={(e) => setManufacturer(e.target.value)}
                  className={inputCls}
                  data-testid="qual-form-manufacturer"
                />
              </label>
              <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold text-red-800">
                Product model *
                <Input
                  value={productModel}
                  onChange={(e) => setProductModel(e.target.value)}
                  className={inputCls}
                  data-testid="qual-form-product-model"
                />
              </label>
            </>
          )}
          {requiresProgramName && (
            <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold md:col-span-2 text-red-800">
              Program name *
              <Input
                value={programName}
                onChange={(e) => setProgramName(e.target.value)}
                className={inputCls}
                data-testid="qual-form-program-name"
              />
            </label>
          )}

          <label className="text-xs font-mono uppercase tracking-[0.15em] font-bold md:col-span-2">
            Notes
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className={inputCls}
              data-testid="qual-form-notes"
            />
          </label>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            data-testid="qual-form-cancel"
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={submit}
            disabled={saving}
            className="bg-purple-700 hover:bg-purple-800 text-white"
            data-testid="qual-form-save"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <Plus className="w-4 h-4 mr-1" />
            )}
            Save
          </Button>
        </div>
      </Card>
    </div>
  );
}

// ─── Row action buttons ─────────────────────────────────────────────
function RowActions({ row, onChange }) {
  const [busy, setBusy] = useState(false);

  const act = async (action) => {
    const reason = window.prompt(`Reason for ${action}?`) || "";
    if (!reason) return;
    setBusy(true);
    try {
      await transitionQualification(row.id, action, reason);
      toast.success(`Qualification ${action}d`);
      onChange();
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || `${action} failed`;
      toast.error(String(msg));
    } finally {
      setBusy(false);
    }
  };

  const renew = async () => {
    const d = window.prompt("New expiration date (YYYY-MM-DD)?") || "";
    if (!d) return;
    setBusy(true);
    try {
      await renewQualification(row.id, {
        expiration_date: d,
        reason: "renewal",
      });
      toast.success("Qualification renewed");
      onChange();
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || "renew failed";
      toast.error(String(msg));
    } finally {
      setBusy(false);
    }
  };

  const isActive = row.verification_status === "active";
  return (
    <div className="flex flex-wrap gap-1" data-testid={`qual-row-actions-${row.id}`}>
      {isActive && (
        <Button
          type="button" size="sm" variant="outline"
          onClick={() => act("suspend")} disabled={busy}
          data-testid={`qual-btn-suspend-${row.id}`}
        >
          <PauseCircle className="w-3.5 h-3.5 mr-1" /> Suspend
        </Button>
      )}
      {isActive && (
        <Button
          type="button" size="sm" variant="outline"
          onClick={() => act("revoke")} disabled={busy}
          data-testid={`qual-btn-revoke-${row.id}`}
        >
          <Ban className="w-3.5 h-3.5 mr-1" /> Revoke
        </Button>
      )}
      {!isActive && (
        <Button
          type="button" size="sm" variant="outline"
          onClick={() => act("reinstate")} disabled={busy}
          data-testid={`qual-btn-reinstate-${row.id}`}
        >
          <RotateCw className="w-3.5 h-3.5 mr-1" /> Reinstate
        </Button>
      )}
      <Button
        type="button" size="sm" variant="outline"
        onClick={renew} disabled={busy}
        data-testid={`qual-btn-renew-${row.id}`}
      >
        <RefreshCw className="w-3.5 h-3.5 mr-1" /> Renew
      </Button>
    </div>
  );
}

// ─── Main page ──────────────────────────────────────────────────────
export default function EmployeeLifecycleQualifications() {
  const [types, setTypes] = useState({ types: [], statuses: [], type_metadata_spec: {} });
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [rows, setRows] = useState([]);
  const [activeRegistry, setActiveRegistry] = useState({ count: 0, items: [] });
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedType, setSelectedType] = useState("COMPETENT_PERSON");

  const loadEmployeeRows = useCallback(async (empId) => {
    if (!empId) {
      setRows([]);
      return;
    }
    try {
      const r = await employeeQualifications(empId, { includeHistory: true });
      setRows(r.items || []);
    } catch (err) {
      toast.error("Could not load employee qualifications");
      setRows([]);
    }
  }, []);

  const loadRegistry = useCallback(async (type) => {
    try {
      const [reg, sum] = await Promise.all([
        listActiveQualifications(type, 30),
        qualificationSummary(type, 30),
      ]);
      setActiveRegistry(reg);
      setSummary(sum);
    } catch (err) {
      // Non-fatal — the tab still renders.
    }
  }, []);

  useEffect(() => {
    let cancel = false;
    (async () => {
      setLoading(true);
      try {
        const [t, emps] = await Promise.all([
          listQualificationTypes(),
          fetchEmployees(),
        ]);
        if (cancel) return;
        setTypes(t);
        setEmployees(emps);
      } catch (err) {
        toast.error("Could not load qualifications catalogue");
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, []);

  useEffect(() => { loadRegistry(selectedType); }, [selectedType, loadRegistry]);
  useEffect(() => { loadEmployeeRows(selectedEmployee); }, [selectedEmployee, loadEmployeeRows]);

  const refreshAll = () => {
    loadEmployeeRows(selectedEmployee);
    loadRegistry(selectedType);
  };

  return (
    <HrPageShell
      title="Professional Qualifications"
      kicker="HR · Qualifications Engine"
    >
      <div className="flex items-center justify-between mb-4">
        <Link
          to="/hr/employees"
          className="text-xs font-mono uppercase tracking-[0.15em] text-purple-700 hover:text-purple-900 inline-flex items-center gap-1"
          data-testid="qual-back-to-employees"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Employees
        </Link>
        <Button
          onClick={() => setShowForm(true)}
          className="bg-purple-700 hover:bg-purple-800 text-white"
          data-testid="qual-open-form"
        >
          <Plus className="w-4 h-4 mr-1" /> New qualification
        </Button>
      </div>

      {/* Registry summary card */}
      <Card
        className="p-4 mb-4 border-2 border-purple-200 bg-purple-50/40"
        data-testid="qual-registry-summary"
      >
        <div className="flex flex-wrap gap-3 items-end">
          <div className="min-w-[220px]">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold block mb-1">
              Qualification type
            </label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className={`${inputCls} rounded px-2 min-w-[220px]`}
              data-testid="qual-type-select"
            >
              {(types.types || []).map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          {summary && (
            <div
              className="flex flex-wrap gap-2 text-[11px] font-mono uppercase tracking-[0.15em]"
              data-testid="qual-summary-chips"
            >
              <span className="px-2 py-1 rounded bg-emerald-100 border border-emerald-300 text-emerald-900">
                <strong>{summary.active_count}</strong> ACTIVE
              </span>
              <span className="px-2 py-1 rounded bg-amber-100 border border-amber-300 text-amber-900">
                <strong>{summary.expiring_within_count}</strong> ≤ 30D
              </span>
              <span className="px-2 py-1 rounded bg-red-100 border border-red-300 text-red-900">
                <strong>{summary.expired_count}</strong> EXPIRED
              </span>
              <span className="px-2 py-1 rounded bg-slate-100 border border-slate-300 text-slate-700">
                <strong>{summary.suspended_count}</strong> SUSPENDED
              </span>
              <span className="px-2 py-1 rounded bg-slate-800 border border-slate-900 text-white">
                <strong>{summary.revoked_count}</strong> REVOKED
              </span>
            </div>
          )}
          <Button
            variant="outline" size="sm"
            onClick={refreshAll}
            className="ml-auto"
            data-testid="qual-refresh"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
          </Button>
        </div>
      </Card>

      {/* Active registry list — the read-through for consumers */}
      <Card
        className="mb-5 overflow-x-auto"
        data-testid="qual-active-registry"
      >
        <div className="p-3 bg-slate-100 border-b border-slate-200 font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
          Active registry · {activeRegistry.count} people · read-through for
          Trench Safety · Daily Report · Scheduling · Safety Portal
        </div>
        {loading ? (
          <div className="p-10 text-center text-slate-500">
            <Loader2 className="w-6 h-6 mx-auto animate-spin" />
          </div>
        ) : (activeRegistry.items || []).length === 0 ? (
          <div
            className="p-10 text-center text-slate-500"
            data-testid="qual-registry-empty"
          >
            <ShieldCheck className="w-10 h-10 mx-auto text-slate-400 mb-3" />
            <div className="font-bold text-base text-slate-900">
              No active qualifications of this type
            </div>
            <p className="text-sm text-slate-600 mt-2 max-w-md mx-auto">
              When HR or Training Admin issues a qualification, it appears here
              automatically. The registry is a query — not a stored list — so
              expired · suspended · revoked · pending rows never leak into
              consumer surfaces.
            </p>
          </div>
        ) : (
          <table className="w-full text-sm min-w-[720px]">
            <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">Employee</th>
                <th className="text-left px-3 py-2">Trade / Crew</th>
                <th className="text-left px-3 py-2">Issuer</th>
                <th className="text-left px-3 py-2">Expires</th>
                <th className="text-center px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {(activeRegistry.items || []).map((r) => (
                <tr
                  key={r.qualification_id}
                  className="border-t border-slate-100 hover:bg-slate-50"
                  data-testid={`qual-registry-row-${r.qualification_id}`}
                >
                  <td className="px-3 py-2 font-semibold">
                    <button
                      type="button"
                      className="text-purple-700 hover:text-purple-900 underline"
                      onClick={() => setSelectedEmployee(r.employee_id)}
                      data-testid={`qual-registry-select-${r.qualification_id}`}
                    >
                      {r.employee_name || r.employee_id}
                    </button>
                  </td>
                  <td className="px-3 py-2 text-xs">
                    {r.employee_trade}{r.employee_crew ? ` · ${r.employee_crew}` : ""}
                  </td>
                  <td className="px-3 py-2 text-xs">{r.issuing_organization}</td>
                  <td className="px-3 py-2 font-mono text-xs">
                    {r.expires_at || "—"}
                    {r.warning && (
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600 inline ml-1" />
                    )}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <StatusChip status={r.verification_status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Per-employee detail */}
      <Card className="p-4" data-testid="qual-employee-panel">
        <div className="flex flex-wrap gap-3 items-end mb-3">
          <div className="min-w-[280px] flex-1">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold block mb-1">
              Employee history
            </label>
            <select
              value={selectedEmployee}
              onChange={(e) => setSelectedEmployee(e.target.value)}
              className={`${inputCls} rounded px-2 w-full`}
              data-testid="qual-employee-select"
            >
              <option value="">— pick an employee —</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name || e.display_identity || e.id}
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedEmployee && rows.length === 0 ? (
          <div
            className="p-6 text-center text-slate-500"
            data-testid="qual-employee-empty"
          >
            <GraduationCap className="w-8 h-8 mx-auto text-slate-400 mb-2" />
            <div className="font-bold text-sm text-slate-900">
              No qualifications on file
            </div>
            <p className="text-xs text-slate-600 mt-2">
              Add one with the button above.
            </p>
          </div>
        ) : rows.length > 0 ? (
          <div className="overflow-x-auto" data-testid="qual-employee-table-wrap">
            <table className="w-full text-sm min-w-[900px]">
              <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                <tr>
                  <th className="text-left px-3 py-2">Type</th>
                  <th className="text-left px-3 py-2">Issued</th>
                  <th className="text-left px-3 py-2">Expires</th>
                  <th className="text-left px-3 py-2">Issuer</th>
                  <th className="text-center px-3 py-2">Status</th>
                  <th className="text-left px-3 py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr
                    key={r.id}
                    className="border-t border-slate-100"
                    data-testid={`qual-emp-row-${r.id}`}
                  >
                    <td className="px-3 py-2 font-semibold text-xs">
                      {(r.qualification_type || r.certification_type || "").replace(/_/g, " ")}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {(r.completed_date || "").slice(0, 10) || "—"}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {r.expiration_date || "—"}
                    </td>
                    <td className="px-3 py-2 text-xs">
                      {r.issuing_organization || r.issued_by || "—"}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <StatusChip status={r.verification_status} />
                    </td>
                    <td className="px-3 py-2">
                      <RowActions row={r} onChange={refreshAll} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6 text-center text-slate-400 text-sm">
            Pick an employee to see their qualification history.
          </div>
        )}
      </Card>

      {showForm && (
        <QualForm
          types={types}
          employees={employees}
          onClose={() => setShowForm(false)}
          onSaved={refreshAll}
          prefillEmployeeId={selectedEmployee}
        />
      )}
    </HrPageShell>
  );
}
