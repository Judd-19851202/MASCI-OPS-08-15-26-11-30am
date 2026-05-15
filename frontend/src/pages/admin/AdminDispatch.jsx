// Admin Dispatch Portal — equipment availability, transfers, holds,
// utilization. Admin-token gated for now; will accept dispatch_users
// tokens in the follow-on iteration.
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Truck, Send, AlertTriangle, ShieldAlert, Wrench, Activity, Loader2,
  CheckCircle2, XCircle, Calendar, RefreshCcw, Plus, Search,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";

const STATUS_PILL = {
  Available:         "bg-emerald-100 text-emerald-900 border-emerald-300",
  Assigned:          "bg-blue-100 text-blue-900 border-blue-300",
  "In Transit":      "bg-violet-100 text-violet-900 border-violet-300",
  "Pending Transfer":"bg-cyan-100 text-cyan-900 border-cyan-300",
  "Safety Hold":     "bg-red-100 text-red-900 border-red-300",
  "Maintenance Hold":"bg-amber-100 text-amber-900 border-amber-300",
  Down:              "bg-slate-300 text-slate-900 border-slate-400",
  Unknown:           "bg-slate-200 text-slate-700 border-slate-300",
};

const TRANSFER_PILL = {
  Submitted:        "bg-amber-100 text-amber-900 border-amber-300",
  "Pending Review": "bg-amber-100 text-amber-900 border-amber-300",
  Approved:         "bg-blue-100 text-blue-900 border-blue-300",
  Scheduled:        "bg-violet-100 text-violet-900 border-violet-300",
  "In Transit":     "bg-cyan-100 text-cyan-900 border-cyan-300",
  Completed:        "bg-emerald-100 text-emerald-900 border-emerald-300",
  Denied:           "bg-red-100 text-red-900 border-red-300",
  Cancelled:        "bg-slate-200 text-slate-700 border-slate-300",
};

export default function AdminDispatch() {
  const [tab, setTab] = useState("overview");
  return (
    <AdminShell title="Dispatch Portal">
      <div className="max-w-7xl mx-auto" data-testid="admin-dispatch-page">
        <div className="bg-white border-2 border-slate-300 rounded-md p-5 mb-4">
          <div className="flex items-start gap-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-900 text-white shrink-0">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
                Dispatch Portal · iter124
              </span>
              <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
                Equipment Movement Command Center
              </h1>
              <p className="text-sm text-slate-600 mt-1">
                Availability · transfers · holds · utilization. Admin-gated for now;
                dedicated dispatch users (mirror of Safety / HR / Shop / PM portals) ship in the next pass.
              </p>
            </div>
          </div>
        </div>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="flex-wrap h-auto">
            <TabsTrigger value="overview" data-testid="dp-tab-overview"><Activity className="w-3.5 h-3.5 mr-1" /> Overview</TabsTrigger>
            <TabsTrigger value="utilization" data-testid="dp-tab-utilization"><Activity className="w-3.5 h-3.5 mr-1" /> Utilization</TabsTrigger>
            <TabsTrigger value="transfers" data-testid="dp-tab-transfers"><Send className="w-3.5 h-3.5 mr-1" /> Transfers</TabsTrigger>
            <TabsTrigger value="holds" data-testid="dp-tab-holds"><ShieldAlert className="w-3.5 h-3.5 mr-1" /> Holds</TabsTrigger>
          </TabsList>

          <TabsContent value="overview"><OverviewTab /></TabsContent>
          <TabsContent value="utilization"><UtilizationTab /></TabsContent>
          <TabsContent value="transfers"><TransfersTab /></TabsContent>
          <TabsContent value="holds"><HoldsTab /></TabsContent>
        </Tabs>
      </div>
    </AdminShell>
  );
}

/* ════════════ OVERVIEW ════════════ */
function OverviewTab() {
  const [util, setUtil] = useState(null);
  const [xfers, setXfers] = useState([]);
  const [holds, setHolds] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [u, t, h] = await Promise.all([
        api.get("/operations/utilization"),
        api.get("/operations/transfers"),
        api.get("/operations/holds?active_only=true"),
      ]);
      setUtil(u.data); setXfers(t.data || []); setHolds(h.data || []);
    } catch (e) { toast.error("Failed to load dispatch overview"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  if (loading) return <div className="text-center text-slate-500 py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>;

  const totals = util?.totals || {};
  const cards = [
    { label: "Total Active Assets", value: util?.fleet_size || 0, cls: "border-slate-300" },
    { label: "Available",           value: totals.Available || 0, cls: "border-emerald-300" },
    { label: "Assigned",            value: totals.Assigned || 0,  cls: "border-blue-300" },
    { label: "Pending Transfer",    value: totals["Pending Transfer"] || 0, cls: "border-cyan-300" },
    { label: "In Transit",          value: totals["In Transit"] || 0, cls: "border-violet-300" },
    { label: "Safety Hold",         value: totals["Safety Hold"] || 0, cls: "border-red-300" },
    { label: "Maintenance Hold",    value: totals["Maintenance Hold"] || 0, cls: "border-amber-300" },
    { label: "Open Transfers",      value: xfers.filter(x => !["Completed","Denied","Cancelled"].includes(x.status)).length, cls: "border-slate-300" },
  ];
  return (
    <div className="space-y-4" data-testid="dp-overview">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {cards.map((c) => (
          <div key={c.label} className={`bg-white border-2 ${c.cls} rounded-md p-4`}>
            <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">{c.label}</div>
            <div className="font-display text-3xl font-black text-slate-900 mt-1">{c.value}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white border-2 border-slate-200 rounded-md p-4">
          <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">Recent transfers</h3>
          {xfers.length === 0 ? <p className="text-sm text-slate-500 italic">No transfers yet.</p> : (
            <ul className="divide-y divide-slate-100 text-xs max-h-64 overflow-y-auto">
              {xfers.slice(0, 10).map((x) => (
                <li key={x.id} className="py-2 flex items-center gap-2 flex-wrap">
                  <span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${TRANSFER_PILL[x.status] || "bg-slate-100"}`}>{x.status}</span>
                  <span className="font-mono text-slate-500">{x.masci_unit_number || x.asset_id?.slice(0,6)}</span>
                  <span>{x.from_project_number || "—"} → {x.to_project_number || "—"}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="bg-white border-2 border-slate-200 rounded-md p-4">
          <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">Active holds</h3>
          {holds.length === 0 ? <p className="text-sm text-slate-500 italic">No active holds.</p> : (
            <ul className="divide-y divide-slate-100 text-xs max-h-64 overflow-y-auto">
              {holds.slice(0, 10).map((h) => (
                <li key={h.id} className="py-2 flex items-center gap-2 flex-wrap">
                  <span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${h.kind === "safety" ? "bg-red-100 text-red-900 border-red-300" : "bg-amber-100 text-amber-900 border-amber-300"}`}>{h.kind}</span>
                  <span className="font-bold truncate">{h.reason}</span>
                  <span className="text-slate-500 ml-auto font-mono text-[10px]">{h.severity}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

/* ════════════ UTILIZATION ════════════ */
function UtilizationTab() {
  const [util, setUtil] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("All");
  const [search, setSearch] = useState("");

  const load = async () => {
    setLoading(true);
    try { setUtil((await api.get("/operations/utilization")).data); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const rows = useMemo(() => {
    const all = util?.rows || [];
    return all.filter((r) => {
      if (filter !== "All" && r.status !== filter) return false;
      if (search && !`${r.unit_number} ${r.equipment_name}`.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [util, filter, search]);

  const filters = ["All", "Available", "Assigned", "Pending Transfer", "In Transit", "Safety Hold", "Maintenance Hold"];

  if (loading) return <div className="text-center text-slate-500 py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>;
  return (
    <div className="space-y-3" data-testid="dp-utilization">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex items-center gap-1 flex-wrap">
          {filters.map((f) => (
            <Button key={f} size="sm" variant={filter === f ? "default" : "outline"} onClick={() => setFilter(f)} className="h-8" data-testid={`util-filter-${f.replace(/\s+/g,"-").toLowerCase()}`}>
              {f} {util?.totals[f] !== undefined ? `(${util.totals[f]})` : ""}
            </Button>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <Input placeholder="Search unit / name" className="pl-7 h-8 w-56" value={search} onChange={(e) => setSearch(e.target.value)} data-testid="util-search" />
          </div>
          <Button onClick={load} size="sm" variant="outline" className="h-8"><RefreshCcw className="w-3.5 h-3.5" /></Button>
        </div>
      </div>
      <div className="bg-white border-2 border-slate-200 rounded-md overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em]">
            <tr>
              <th className="text-left px-3 py-2">Unit</th>
              <th className="text-left px-3 py-2">Name</th>
              <th className="text-left px-3 py-2">Type</th>
              <th className="text-left px-3 py-2">Status</th>
              <th className="text-left px-3 py-2">Project</th>
              <th className="text-left px-3 py-2">Operator</th>
              <th className="text-left px-3 py-2"></th>
            </tr>
          </thead>
          <tbody data-testid="util-table">
            {rows.slice(0, 200).map((r) => (
              <tr key={r.asset_id} className="border-t border-slate-100">
                <td className="px-3 py-2 font-mono font-bold">{r.unit_number || "—"}</td>
                <td className="px-3 py-2 truncate max-w-xs">{r.equipment_name || "—"}</td>
                <td className="px-3 py-2 text-slate-500">{r.equipment_type || "—"}</td>
                <td className="px-3 py-2"><span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${STATUS_PILL[r.status] || ""}`}>{r.status}</span></td>
                <td className="px-3 py-2">{r.assigned_project_number || "—"}</td>
                <td className="px-3 py-2">{r.assigned_operator_name || "—"}</td>
                <td className="px-3 py-2 text-right">
                  <Link to={`/admin/assets/${r.asset_id}`} className="text-slate-700 hover:text-slate-900 font-bold underline">Profile →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length > 200 && <div className="px-3 py-2 text-xs text-slate-500 italic">Showing first 200 of {rows.length}. Refine filters.</div>}
      </div>
    </div>
  );
}

/* ════════════ TRANSFERS ════════════ */
function TransfersTab() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const load = async () => {
    setLoading(true);
    try { setList((await api.get("/operations/transfers")).data || []); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const decide = async (xid, decision, extra = {}) => {
    try {
      await api.post(`/operations/transfers/${xid}/decide`, { decision, ...extra });
      toast.success(`Transfer ${decision}d`);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Decision failed");
    }
  };

  return (
    <div className="space-y-3" data-testid="dp-transfers">
      <div className="flex items-center gap-2">
        <Button onClick={() => setCreating(true)} className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="dp-transfer-new"><Plus className="w-3.5 h-3.5 mr-1" /> New Transfer</Button>
        <Button onClick={load} variant="outline" size="sm"><RefreshCcw className="w-3.5 h-3.5 mr-1" />Refresh</Button>
      </div>
      <div className="bg-white border-2 border-slate-200 rounded-md overflow-x-auto">
        {loading ? (
          <div className="text-center py-8 text-slate-500"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
        ) : list.length === 0 ? (
          <p className="p-5 text-sm text-slate-500 italic">No transfer requests yet.</p>
        ) : (
          <table className="w-full text-xs">
            <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em]">
              <tr>
                <th className="text-left px-3 py-2">When</th>
                <th className="text-left px-3 py-2">Unit</th>
                <th className="text-left px-3 py-2">Status</th>
                <th className="text-left px-3 py-2">From → To</th>
                <th className="text-left px-3 py-2">Reason</th>
                <th className="text-left px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {list.map((x) => (
                <tr key={x.id} className="border-t border-slate-100" data-testid={`dp-transfer-row-${x.id}`}>
                  <td className="px-3 py-2 font-mono text-slate-500">{(x.created_at || "").slice(0,16).replace("T"," ")}</td>
                  <td className="px-3 py-2 font-mono font-bold">{x.masci_unit_number || x.asset_id?.slice(0,6)}</td>
                  <td className="px-3 py-2"><span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${TRANSFER_PILL[x.status] || ""}`}>{x.status}</span></td>
                  <td className="px-3 py-2">{x.from_project_number || "—"} → {x.to_project_number || "—"}</td>
                  <td className="px-3 py-2 truncate max-w-xs text-slate-500">{x.reason || ""}</td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {x.status === "Submitted" && (<>
                        <Button size="sm" variant="outline" className="h-7 px-2" onClick={() => decide(x.id, "approve")} data-testid={`dp-xfer-approve-${x.id}`}><CheckCircle2 className="w-3 h-3 mr-1 text-emerald-700" />Approve</Button>
                        <Button size="sm" variant="outline" className="h-7 px-2" onClick={() => { const r = window.prompt("Deny reason"); if (r !== null) decide(x.id, "deny", { decision_reason: r }); }} data-testid={`dp-xfer-deny-${x.id}`}><XCircle className="w-3 h-3 mr-1 text-red-700" />Deny</Button>
                      </>)}
                      {x.status === "Approved" && (
                        <Button size="sm" variant="outline" className="h-7 px-2" onClick={() => { const d = window.prompt("Scheduled move date (YYYY-MM-DD)"); if (d) decide(x.id, "schedule", { scheduled_move_date: d }); }} data-testid={`dp-xfer-schedule-${x.id}`}><Calendar className="w-3 h-3 mr-1" />Schedule</Button>
                      )}
                      {(x.status === "Scheduled" || x.status === "Approved") && (
                        <Button size="sm" variant="outline" className="h-7 px-2" onClick={() => decide(x.id, "complete")} data-testid={`dp-xfer-complete-${x.id}`}><CheckCircle2 className="w-3 h-3 mr-1 text-emerald-700" />Complete</Button>
                      )}
                      {!["Completed","Denied","Cancelled"].includes(x.status) && (
                        <Button size="sm" variant="outline" className="h-7 px-2" onClick={() => decide(x.id, "cancel")}>Cancel</Button>
                      )}
                      <Link to={`/admin/assets/${x.asset_id}`} className="text-xs text-slate-700 hover:text-slate-900 font-bold underline pt-1">Asset →</Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {creating && <CreateTransferDialog open={creating} onClose={() => { setCreating(false); load(); }} />}
    </div>
  );
}

function CreateTransferDialog({ open, onClose }) {
  const [assetId, setAssetId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [reason, setReason] = useState("");
  const [needDate, setNeedDate] = useState("");
  const [priority, setPriority] = useState("normal");
  const [equipment, setEquipment] = useState([]);
  const [search, setSearch] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get("/equipment-master").then((r) => {
      const items = r.data?.items || (Array.isArray(r.data) ? r.data : []);
      setEquipment(items.filter((e) => (e.unit_number || "").trim()));
    }).catch(() => {});
  }, []);

  const filtered = useMemo(() => {
    if (!search) return equipment.slice(0, 50);
    const s = search.toLowerCase();
    return equipment.filter((e) => `${e.unit_number} ${e.name}`.toLowerCase().includes(s)).slice(0, 50);
  }, [equipment, search]);

  const submit = async () => {
    if (!assetId) { toast.error("Pick an asset"); return; }
    setSubmitting(true);
    try {
      await api.post("/operations/transfers", {
        asset_id: assetId, from_project_number: from, to_project_number: to,
        reason, need_date: needDate || null, priority,
      });
      toast.success("Transfer request created");
      onClose();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Create failed");
    } finally { setSubmitting(false); }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg" data-testid="dp-transfer-create-dialog">
        <DialogHeader><DialogTitle>New transfer request</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div>
            <Label>Asset</Label>
            <Input placeholder="Search unit # or name" value={search} onChange={(e) => setSearch(e.target.value)} data-testid="dp-create-search" />
            <div className="border border-slate-200 rounded mt-1 max-h-44 overflow-y-auto">
              {filtered.map((e) => (
                <button key={e.id} onClick={() => setAssetId(e.id)} className={`block w-full text-left px-2 py-1 text-xs hover:bg-slate-100 ${assetId === e.id ? "bg-slate-200 font-bold" : ""}`}>
                  {e.unit_number} · {e.name}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div><Label>From project #</Label><Input value={from} onChange={(e) => setFrom(e.target.value)} /></div>
            <div><Label>To project #</Label><Input value={to} onChange={(e) => setTo(e.target.value)} data-testid="dp-create-to" /></div>
            <div><Label>Need date</Label><Input type="date" value={needDate} onChange={(e) => setNeedDate(e.target.value)} /></div>
            <div><Label>Priority</Label>
              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="normal">Normal</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div><Label>Reason / notes</Label><Textarea rows={3} value={reason} onChange={(e) => setReason(e.target.value)} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} disabled={submitting || !assetId} className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="dp-create-submit">
            {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : null} Create request
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/* ════════════ HOLDS ════════════ */
function HoldsTab() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const load = async () => {
    setLoading(true);
    try { setList((await api.get("/operations/holds?active_only=true")).data || []); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const release = async (hid) => {
    const note = window.prompt("Resolution note (optional)") || "";
    try { await api.post(`/operations/holds/${hid}/release`, { resolution: note }); toast.success("Hold released"); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Release failed"); }
  };

  return (
    <div className="space-y-3" data-testid="dp-holds">
      <div className="flex items-center gap-2">
        <Button onClick={() => setCreating(true)} className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="dp-hold-new"><Plus className="w-3.5 h-3.5 mr-1" /> Apply hold</Button>
        <Button onClick={load} variant="outline" size="sm"><RefreshCcw className="w-3.5 h-3.5 mr-1" />Refresh</Button>
      </div>
      <div className="bg-white border-2 border-slate-200 rounded-md overflow-x-auto">
        {loading ? <div className="text-center py-8 text-slate-500"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div> :
          list.length === 0 ? <p className="p-5 text-sm text-slate-500 italic">No active holds.</p> : (
          <table className="w-full text-xs">
            <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em]">
              <tr>
                <th className="text-left px-3 py-2">Applied</th>
                <th className="text-left px-3 py-2">Asset</th>
                <th className="text-left px-3 py-2">Kind</th>
                <th className="text-left px-3 py-2">Severity</th>
                <th className="text-left px-3 py-2">Reason</th>
                <th className="text-left px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {list.map((h) => (
                <tr key={h.id} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-mono text-slate-500">{(h.created_at || "").slice(0,16).replace("T"," ")}</td>
                  <td className="px-3 py-2"><Link to={`/admin/assets/${h.asset_id}`} className="font-mono font-bold underline">{h.asset_id?.slice(0,8)}</Link></td>
                  <td className="px-3 py-2"><span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${h.kind === "safety" ? "bg-red-100 text-red-900 border-red-300" : "bg-amber-100 text-amber-900 border-amber-300"}`}>{h.kind}</span></td>
                  <td className="px-3 py-2 font-mono text-[10px]">{h.severity}</td>
                  <td className="px-3 py-2">{h.reason}</td>
                  <td className="px-3 py-2 text-right">
                    <Button size="sm" variant="outline" className="h-7" onClick={() => release(h.id)} data-testid={`dp-hold-release-${h.id}`}>Release</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {creating && <CreateHoldDialog open={creating} onClose={() => { setCreating(false); load(); }} />}
    </div>
  );
}

function CreateHoldDialog({ open, onClose }) {
  const [assetId, setAssetId] = useState("");
  const [kind, setKind] = useState("safety");
  const [reason, setReason] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [equipment, setEquipment] = useState([]);
  const [search, setSearch] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get("/equipment-master").then((r) => {
      const items = r.data?.items || (Array.isArray(r.data) ? r.data : []);
      setEquipment(items.filter((e) => (e.unit_number || "").trim()));
    }).catch(() => {});
  }, []);
  const filtered = useMemo(() => {
    if (!search) return equipment.slice(0, 50);
    return equipment.filter((e) => `${e.unit_number} ${e.name}`.toLowerCase().includes(search.toLowerCase())).slice(0, 50);
  }, [equipment, search]);

  const submit = async () => {
    if (!assetId || !reason) { toast.error("Asset and reason required"); return; }
    setSubmitting(true);
    try { await api.post("/operations/holds", { asset_id: assetId, kind, reason, severity }); toast.success("Hold applied"); onClose(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Apply failed"); }
    finally { setSubmitting(false); }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg" data-testid="dp-hold-create-dialog">
        <DialogHeader><DialogTitle>Apply operational hold</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div>
            <Label>Asset</Label>
            <Input placeholder="Search unit / name" value={search} onChange={(e) => setSearch(e.target.value)} />
            <div className="border border-slate-200 rounded mt-1 max-h-40 overflow-y-auto">
              {filtered.map((e) => (
                <button key={e.id} onClick={() => setAssetId(e.id)} className={`block w-full text-left px-2 py-1 text-xs hover:bg-slate-100 ${assetId === e.id ? "bg-slate-200 font-bold" : ""}`}>{e.unit_number} · {e.name}</button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div><Label>Kind</Label>
              <Select value={kind} onValueChange={setKind}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="safety">Safety</SelectItem>
                  <SelectItem value="maintenance">Maintenance</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label>Severity</Label>
              <Select value={severity} onValueChange={setSeverity}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div><Label>Reason</Label><Textarea rows={3} value={reason} onChange={(e) => setReason(e.target.value)} data-testid="dp-hold-reason" /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} disabled={submitting} className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="dp-hold-submit">
            {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : null} Apply hold
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
