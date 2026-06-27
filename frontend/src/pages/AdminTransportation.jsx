import React, { useEffect, useState, useCallback } from "react";
import { Truck, Building2, UserRound, ShieldCheck, RefreshCw, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { PortalShell } from "@/design-system";
import AdminSideNavV2 from "@/components/admin/sidebar/SideNavV2";
import { api } from "@/lib/api";
import { getAdminToken } from "@/lib/adminAuth";

const STATUSES = ["pending_review", "active", "needs_correction", "suspended", "expired", "inactive"];
const STATUS_LABEL = {
  pending_review: "Pending Review",
  active: "Active",
  needs_correction: "Needs Correction",
  suspended: "Suspended",
  expired: "Expired",
  inactive: "Inactive",
};
const ELIGIBILITY_LABEL = {
  eligible: "Eligible",
  pending_review: "Pending Review",
  needs_correction: "Needs Correction",
  expired: "Expired",
  suspended: "Suspended",
  not_dispatchable: "Not Dispatchable",
};
const CARRIER_TYPES = ["leased_hauler", "owner_operator", "supplier", "masci_internal", "other"];
const PERSON_KINDS = ["masci_employee", "leased_driver"];
const TRUCK_OWNERSHIPS = ["masci_owned", "leased_carrier", "owner_operator", "unknown"];
const TRUCK_TYPES = ["dump_truck", "flow_boy", "lowboy", "tanker", "roll_off", "service_truck", "other"];

const ELIG_BADGE = {
  eligible: "bg-emerald-100 text-emerald-800 border-emerald-200",
  pending_review: "bg-amber-100 text-amber-800 border-amber-200",
  needs_correction: "bg-amber-100 text-amber-800 border-amber-200",
  expired: "bg-rose-100 text-rose-800 border-rose-200",
  suspended: "bg-rose-100 text-rose-800 border-rose-200",
  not_dispatchable: "bg-slate-200 text-slate-700 border-slate-300",
};

function adminHeaders() {
  return { "X-Admin-Token": getAdminToken() || "" };
}

function StatusBadge({ value }) {
  return (
    <Badge variant="outline" className="text-xs" data-testid={`status-badge-${value}`}>
      {STATUS_LABEL[value] || value}
    </Badge>
  );
}

function EligibilityBadge({ value }) {
  return (
    <span
      data-testid={`eligibility-badge-${value}`}
      className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium ${ELIG_BADGE[value] || "bg-slate-100 text-slate-700"}`}
    >
      {ELIGIBILITY_LABEL[value] || value}
    </span>
  );
}

// ───────────────────────────── Carriers ─────────────────────────────
function CarriersTab() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState({ legal_name: "", carrier_type: "leased_hauler" });
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/transportation/carriers", { headers: adminHeaders() });
      setRows(res.data.items || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function onCreate() {
    setErr(null);
    try {
      await api.post("/admin/transportation/carriers", draft, { headers: adminHeaders() });
      setDraft({ legal_name: "", carrier_type: "leased_hauler" });
      setShowForm(false);
      load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Create failed");
    }
  }

  return (
    <div className="space-y-4" data-testid="carriers-tab">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Carriers</h3>
        <div className="flex gap-2">
          <Button variant="outline" onClick={load} data-testid="carriers-refresh-btn">
            <RefreshCw className="h-4 w-4 mr-1" />Refresh
          </Button>
          <Button onClick={() => setShowForm(s => !s)} data-testid="carriers-add-btn">
            <Plus className="h-4 w-4 mr-1" />Add Carrier
          </Button>
        </div>
      </div>

      {showForm && (
        <div className="border rounded p-4 bg-slate-50 space-y-3" data-testid="carriers-form">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Label>Legal name *</Label>
              <Input
                data-testid="carrier-legal-name-input"
                value={draft.legal_name}
                onChange={e => setDraft({ ...draft, legal_name: e.target.value })}
              />
            </div>
            <div>
              <Label>Carrier type</Label>
              <Select value={draft.carrier_type} onValueChange={v => setDraft({ ...draft, carrier_type: v })}>
                <SelectTrigger data-testid="carrier-type-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {CARRIER_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>DOT number</Label>
              <Input value={draft.dot_number || ""} onChange={e => setDraft({ ...draft, dot_number: e.target.value })} />
            </div>
            <div>
              <Label>MC number</Label>
              <Input value={draft.mc_number || ""} onChange={e => setDraft({ ...draft, mc_number: e.target.value })} />
            </div>
            <div>
              <Label>Contact email</Label>
              <Input value={draft.contact_email || ""} onChange={e => setDraft({ ...draft, contact_email: e.target.value })} />
            </div>
            <div>
              <Label>Contact phone</Label>
              <Input value={draft.contact_phone || ""} onChange={e => setDraft({ ...draft, contact_phone: e.target.value })} />
            </div>
          </div>
          {err && <div className="text-rose-700 text-sm" data-testid="carriers-form-error">{err}</div>}
          <div className="flex gap-2">
            <Button onClick={onCreate} data-testid="carriers-create-submit-btn">Create</Button>
            <Button variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {loading ? (
        <div data-testid="carriers-loading">Loading…</div>
      ) : (
        <div className="overflow-x-auto border rounded">
          <table className="w-full text-sm" data-testid="carriers-table">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Legal Name</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">DOT</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Safety Hold</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr><td colSpan={5} className="px-3 py-4 text-center text-slate-500" data-testid="carriers-empty">
                  No carriers yet.
                </td></tr>
              )}
              {rows.map(c => (
                <tr key={c.id} className="border-t" data-testid={`carrier-row-${c.id}`}>
                  <td className="px-3 py-2 font-medium">{c.legal_name}</td>
                  <td className="px-3 py-2">{c.carrier_type}</td>
                  <td className="px-3 py-2">{c.dot_number || "—"}</td>
                  <td className="px-3 py-2"><StatusBadge value={c.status} /></td>
                  <td className="px-3 py-2">{c.safety_hold ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ───────────────────────────── Drivers ─────────────────────────────
function DriversTab() {
  const [rows, setRows] = useState([]);
  const [carriers, setCarriers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState({ kind: "masci_employee", first_name: "", last_name: "" });
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [p, c] = await Promise.all([
        api.get("/admin/transportation/persons", { headers: adminHeaders() }),
        api.get("/admin/transportation/carriers", { headers: adminHeaders() }),
      ]);
      setRows(p.data.items || []);
      setCarriers(c.data.items || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  async function onCreate() {
    setErr(null);
    try {
      await api.post("/admin/transportation/persons", draft, { headers: adminHeaders() });
      setDraft({ kind: "masci_employee", first_name: "", last_name: "" });
      setShowForm(false);
      load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Create failed");
    }
  }

  return (
    <div className="space-y-4" data-testid="drivers-tab">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Drivers</h3>
        <div className="flex gap-2">
          <Button variant="outline" onClick={load} data-testid="drivers-refresh-btn"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
          <Button onClick={() => setShowForm(s => !s)} data-testid="drivers-add-btn"><Plus className="h-4 w-4 mr-1" />Add Driver</Button>
        </div>
      </div>

      {showForm && (
        <div className="border rounded p-4 bg-slate-50 space-y-3" data-testid="drivers-form">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Label>Kind</Label>
              <Select value={draft.kind} onValueChange={v => setDraft({ ...draft, kind: v })}>
                <SelectTrigger data-testid="driver-kind-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {PERSON_KINDS.map(k => <SelectItem key={k} value={k}>{k}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              {draft.kind === "masci_employee" ? (
                <>
                  <Label>HR employee_id *</Label>
                  <Input data-testid="driver-employee-id-input" value={draft.employee_id || ""} onChange={e => setDraft({ ...draft, employee_id: e.target.value })} />
                </>
              ) : (
                <>
                  <Label>Carrier *</Label>
                  <Select value={draft.carrier_id || ""} onValueChange={v => setDraft({ ...draft, carrier_id: v })}>
                    <SelectTrigger data-testid="driver-carrier-select"><SelectValue placeholder="Select carrier" /></SelectTrigger>
                    <SelectContent>
                      {carriers.map(c => <SelectItem key={c.id} value={c.id}>{c.legal_name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </>
              )}
            </div>
            <div>
              <Label>First name *</Label>
              <Input data-testid="driver-first-name-input" value={draft.first_name} onChange={e => setDraft({ ...draft, first_name: e.target.value })} />
            </div>
            <div>
              <Label>Last name *</Label>
              <Input data-testid="driver-last-name-input" value={draft.last_name} onChange={e => setDraft({ ...draft, last_name: e.target.value })} />
            </div>
            <div>
              <Label>License #</Label>
              <Input value={draft.license_number || ""} onChange={e => setDraft({ ...draft, license_number: e.target.value })} />
            </div>
            <div>
              <Label>CDL class</Label>
              <Input value={draft.cdl_class || ""} onChange={e => setDraft({ ...draft, cdl_class: e.target.value })} />
            </div>
          </div>
          {err && <div className="text-rose-700 text-sm" data-testid="drivers-form-error">{err}</div>}
          <div className="flex gap-2">
            <Button onClick={onCreate} data-testid="drivers-create-submit-btn">Create</Button>
            <Button variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {loading ? (
        <div data-testid="drivers-loading">Loading…</div>
      ) : (
        <div className="overflow-x-auto border rounded">
          <table className="w-full text-sm" data-testid="drivers-table">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Kind</th>
                <th className="px-3 py-2">Carrier / Employee</th>
                <th className="px-3 py-2">License</th>
                <th className="px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr><td colSpan={5} className="px-3 py-4 text-center text-slate-500" data-testid="drivers-empty">
                  No drivers yet.
                </td></tr>
              )}
              {rows.map(p => (
                <tr key={p.id} className="border-t" data-testid={`driver-row-${p.id}`}>
                  <td className="px-3 py-2 font-medium">{p.first_name} {p.last_name}</td>
                  <td className="px-3 py-2">{p.kind}</td>
                  <td className="px-3 py-2">{p.kind === "leased_driver" ? (p.carrier_id || "—") : (p.employee_id || "—")}</td>
                  <td className="px-3 py-2">{p.license_number || "—"}</td>
                  <td className="px-3 py-2"><StatusBadge value={p.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ───────────────────────────── Trucks ─────────────────────────────
function TrucksTab() {
  const [rows, setRows] = useState([]);
  const [carriers, setCarriers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState({ ownership: "masci_owned", truck_type: "dump_truck", truck_number: "" });
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [t, c] = await Promise.all([
        api.get("/admin/transportation/trucks", { headers: adminHeaders() }),
        api.get("/admin/transportation/carriers", { headers: adminHeaders() }),
      ]);
      setRows(t.data.items || []);
      setCarriers(c.data.items || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  async function onCreate() {
    setErr(null);
    try {
      await api.post("/admin/transportation/trucks", draft, { headers: adminHeaders() });
      setDraft({ ownership: "masci_owned", truck_type: "dump_truck", truck_number: "" });
      setShowForm(false);
      load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Create failed");
    }
  }

  const isLeased = draft.ownership === "leased_carrier" || draft.ownership === "owner_operator";

  return (
    <div className="space-y-4" data-testid="trucks-tab">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Trucks</h3>
        <div className="flex gap-2">
          <Button variant="outline" onClick={load} data-testid="trucks-refresh-btn"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
          <Button onClick={() => setShowForm(s => !s)} data-testid="trucks-add-btn"><Plus className="h-4 w-4 mr-1" />Add Truck</Button>
        </div>
      </div>

      {showForm && (
        <div className="border rounded p-4 bg-slate-50 space-y-3" data-testid="trucks-form">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Label>Ownership</Label>
              <Select value={draft.ownership} onValueChange={v => setDraft({ ...draft, ownership: v })}>
                <SelectTrigger data-testid="truck-ownership-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TRUCK_OWNERSHIPS.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Truck type</Label>
              <Select value={draft.truck_type} onValueChange={v => setDraft({ ...draft, truck_type: v })}>
                <SelectTrigger data-testid="truck-type-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TRUCK_TYPES.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Truck number *</Label>
              <Input data-testid="truck-number-input" value={draft.truck_number} onChange={e => setDraft({ ...draft, truck_number: e.target.value })} />
            </div>
            {isLeased && (
              <div>
                <Label>Carrier *</Label>
                <Select value={draft.carrier_id || ""} onValueChange={v => setDraft({ ...draft, carrier_id: v })}>
                  <SelectTrigger data-testid="truck-carrier-select"><SelectValue placeholder="Select carrier" /></SelectTrigger>
                  <SelectContent>
                    {carriers.map(c => <SelectItem key={c.id} value={c.id}>{c.legal_name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            )}
            {!isLeased && (
              <div>
                <Label>Equipment ID (optional)</Label>
                <Input value={draft.equipment_id || ""} onChange={e => setDraft({ ...draft, equipment_id: e.target.value })} />
              </div>
            )}
            <div>
              <Label>VIN</Label>
              <Input value={draft.vin || ""} onChange={e => setDraft({ ...draft, vin: e.target.value })} />
            </div>
            <div>
              <Label>Plate</Label>
              <Input value={draft.plate || ""} onChange={e => setDraft({ ...draft, plate: e.target.value })} />
            </div>
          </div>
          {err && <div className="text-rose-700 text-sm" data-testid="trucks-form-error">{err}</div>}
          <div className="flex gap-2">
            <Button onClick={onCreate} data-testid="trucks-create-submit-btn">Create</Button>
            <Button variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {loading ? (
        <div data-testid="trucks-loading">Loading…</div>
      ) : (
        <div className="overflow-x-auto border rounded">
          <table className="w-full text-sm" data-testid="trucks-table">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Truck #</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Ownership</th>
                <th className="px-3 py-2">Carrier / Equipment</th>
                <th className="px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr><td colSpan={5} className="px-3 py-4 text-center text-slate-500" data-testid="trucks-empty">
                  No trucks yet.
                </td></tr>
              )}
              {rows.map(t => (
                <tr key={t.id} className="border-t" data-testid={`truck-row-${t.id}`}>
                  <td className="px-3 py-2 font-medium">{t.truck_number}</td>
                  <td className="px-3 py-2">{t.truck_type}</td>
                  <td className="px-3 py-2">{t.ownership}</td>
                  <td className="px-3 py-2">{t.ownership === "masci_owned" ? (t.equipment_id || "—") : (t.carrier_id || "—")}</td>
                  <td className="px-3 py-2"><StatusBadge value={t.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ───────────────────────────── Eligibility ─────────────────────────────
function EligibilityTab() {
  const [persons, setPersons] = useState([]);
  const [trucks, setTrucks] = useState([]);
  const [carriers, setCarriers] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [p, t, c] = await Promise.all([
        api.get("/admin/transportation/persons", { headers: adminHeaders() }),
        api.get("/admin/transportation/trucks", { headers: adminHeaders() }),
        api.get("/admin/transportation/carriers", { headers: adminHeaders() }),
      ]);
      const ps = p.data.items || [];
      const ts = t.data.items || [];
      const cs = c.data.items || [];
      // Fetch eligibility per record (Phase 1: simple, additive)
      const ep = await Promise.all(ps.map(x => api.get(`/admin/transportation/eligibility/person/${x.id}`, { headers: adminHeaders() }).then(r => ({ rec: x, elig: r.data })).catch(() => ({ rec: x, elig: null }))));
      const et = await Promise.all(ts.map(x => api.get(`/admin/transportation/eligibility/truck/${x.id}`, { headers: adminHeaders() }).then(r => ({ rec: x, elig: r.data })).catch(() => ({ rec: x, elig: null }))));
      const ec = await Promise.all(cs.map(x => api.get(`/admin/transportation/eligibility/carrier/${x.id}`, { headers: adminHeaders() }).then(r => ({ rec: x, elig: r.data })).catch(() => ({ rec: x, elig: null }))));
      setPersons(ep);
      setTrucks(et);
      setCarriers(ec);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4" data-testid="eligibility-tab">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Eligibility</h3>
        <Button variant="outline" onClick={load} data-testid="eligibility-refresh-btn"><RefreshCw className="h-4 w-4 mr-1" />Recompute</Button>
      </div>
      {loading ? (
        <div data-testid="eligibility-loading">Loading…</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <EligColumn title="Carriers" testid="elig-carriers" rows={carriers.map(r => ({ key: r.rec.id, label: r.rec.legal_name, state: r.elig?.state || "pending_review", reasons: r.elig?.reasons || [] }))} />
          <EligColumn title="Drivers" testid="elig-drivers" rows={persons.map(r => ({ key: r.rec.id, label: `${r.rec.first_name} ${r.rec.last_name}`, state: r.elig?.state || "pending_review", reasons: r.elig?.reasons || [] }))} />
          <EligColumn title="Trucks" testid="elig-trucks" rows={trucks.map(r => ({ key: r.rec.id, label: r.rec.truck_number, state: r.elig?.state || "pending_review", reasons: r.elig?.reasons || [] }))} />
        </div>
      )}
    </div>
  );
}

function EligColumn({ title, testid, rows }) {
  return (
    <div className="border rounded p-3 bg-white" data-testid={testid}>
      <div className="font-medium mb-2">{title} <span className="text-xs text-slate-500">({rows.length})</span></div>
      <div className="space-y-2">
        {rows.length === 0 && <div className="text-xs text-slate-500" data-testid={`${testid}-empty`}>No records yet.</div>}
        {rows.map(r => (
          <div key={r.key} className="border rounded p-2 text-sm" data-testid={`${testid}-row-${r.key}`}>
            <div className="flex items-center justify-between">
              <span className="font-medium truncate">{r.label}</span>
              <EligibilityBadge value={r.state} />
            </div>
            {r.reasons && r.reasons.length > 0 && (
              <ul className="mt-1 text-xs text-slate-600 list-disc ml-4">
                {r.reasons.slice(0, 3).map((x, i) => <li key={i}>{x.label || x.code}</li>)}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ───────────────────────────── Page shell ─────────────────────────────
export default function AdminTransportation() {
  return (
    <PortalShell
      portalName="MASCI"
      portalSubtitle="Admin Console"
      sideNav={<AdminSideNavV2 />}
    >
      <div className="space-y-6" data-testid="admin-transportation-page">
        <div>
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <Truck className="h-6 w-6" />
            Transportation Foundation
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Phase 1 — carriers, drivers, trucks, and dispatch eligibility skeleton.
            Hauler packets, orientation, quizzes, and certificates ship in later phases.
          </p>
        </div>

        <Tabs defaultValue="carriers" data-testid="transportation-tabs">
          <TabsList>
            <TabsTrigger value="carriers" data-testid="tab-carriers"><Building2 className="h-4 w-4 mr-1" />Carriers</TabsTrigger>
            <TabsTrigger value="drivers" data-testid="tab-drivers"><UserRound className="h-4 w-4 mr-1" />Drivers</TabsTrigger>
            <TabsTrigger value="trucks" data-testid="tab-trucks"><Truck className="h-4 w-4 mr-1" />Trucks</TabsTrigger>
            <TabsTrigger value="eligibility" data-testid="tab-eligibility"><ShieldCheck className="h-4 w-4 mr-1" />Eligibility</TabsTrigger>
          </TabsList>
          <TabsContent value="carriers" className="mt-4"><CarriersTab /></TabsContent>
          <TabsContent value="drivers" className="mt-4"><DriversTab /></TabsContent>
          <TabsContent value="trucks" className="mt-4"><TrucksTab /></TabsContent>
          <TabsContent value="eligibility" className="mt-4"><EligibilityTab /></TabsContent>
        </Tabs>
      </div>
    </PortalShell>
  );
}
