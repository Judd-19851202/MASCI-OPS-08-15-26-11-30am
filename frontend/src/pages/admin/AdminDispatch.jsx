// Admin Dispatch Portal — equipment availability, transfers, holds,
// utilization. Admin-token gated for now; will accept dispatch_users
// tokens in the follow-on iteration.
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Truck, Send, AlertTriangle, ShieldAlert, Wrench, Activity, Loader2,
  CheckCircle2, XCircle, Calendar, RefreshCcw, Plus, Search, Clock,
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
import { operationalError } from "@/lib/errors";
import { HelpTipBlock } from "@/components/HelpTip";
import { isOperatorVisibleTransfer } from "@/lib/transferVisibility";

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
    <AdminShell title="Transportation Operations">
      <div className="max-w-7xl mx-auto" data-testid="admin-dispatch-page">
        <div className="bg-white border border-slate-200 rounded-md p-5 mb-4">
          <div className="flex items-start gap-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-900 text-white shrink-0">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
                Dispatch Portal
              </span>
              <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
                Equipment Movement Command Center
              </h1>
              <p className="text-sm text-slate-600 mt-1">
                Availability · transfers · holds · utilization.
              </p>
            </div>
          </div>
        </div>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="flex-wrap h-auto">
            <TabsTrigger value="overview" data-testid="dp-tab-overview"><Activity className="w-3.5 h-3.5 mr-1" /> Overview</TabsTrigger>
            <TabsTrigger value="utilization" data-testid="dp-tab-utilization"><Activity className="w-3.5 h-3.5 mr-1" /> Utilization</TabsTrigger>
            <TabsTrigger value="idle" data-testid="dp-tab-idle"><Clock className="w-3.5 h-3.5 mr-1" /> Idle Alerts</TabsTrigger>
            <TabsTrigger value="transfers" data-testid="dp-tab-transfers"><Send className="w-3.5 h-3.5 mr-1" /> Transfers</TabsTrigger>
            <TabsTrigger value="holds" data-testid="dp-tab-holds"><ShieldAlert className="w-3.5 h-3.5 mr-1" /> Holds</TabsTrigger>
          </TabsList>

          <TabsContent value="overview"><DispatchOverviewTab /></TabsContent>
          <TabsContent value="utilization"><DispatchUtilizationTab /></TabsContent>
          <TabsContent value="idle"><DispatchIdleAlertsTab /></TabsContent>
          <TabsContent value="transfers"><DispatchTransfersTab /></TabsContent>
          <TabsContent value="holds"><DispatchHoldsTab /></TabsContent>
        </Tabs>
      </div>
    </AdminShell>
  );
}

/* ════════════ OVERVIEW ════════════ */
export function DispatchOverviewTab() {
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
    } catch (e) { toast.error("Could not load dispatch overview. Try again."); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  if (loading) return <div className="text-center text-slate-500 py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>;

  const totals = util?.totals || {};
  // iter330 · pre-deploy KPI normalization · convert heavy `border-2 border-<accent>-300`
  // chrome to family-contract calm pattern: `border border-slate-200` + left-edge stripe
  // + colored value text. Matches iter317c HR · iter318 Safety · iter320 Shop KPI strips.
  const cards = [
    { label: "Total Active Assets", value: util?.fleet_size || 0, stripe: "border-l-slate-500",   valueCls: "text-slate-900" },
    { label: "Available",           value: totals.Available || 0, stripe: "border-l-emerald-500", valueCls: "text-emerald-700" },
    { label: "Assigned",            value: totals.Assigned || 0,  stripe: "border-l-blue-500",    valueCls: "text-blue-700" },
    { label: "Pending Transfer",    value: totals["Pending Transfer"] || 0, stripe: "border-l-cyan-500",   valueCls: "text-cyan-700" },
    { label: "In Transit",          value: totals["In Transit"] || 0,       stripe: "border-l-violet-500", valueCls: "text-violet-700" },
    { label: "Safety Hold",         value: totals["Safety Hold"] || 0,      stripe: "border-l-red-500",    valueCls: "text-red-700" },
    { label: "Maintenance Hold",    value: totals["Maintenance Hold"] || 0, stripe: "border-l-amber-500",  valueCls: "text-amber-700" },
    { label: "Open Transfers",      value: xfers.filter(x => !["Completed","Denied","Cancelled"].includes(x.status)).length, stripe: "border-l-slate-500", valueCls: "text-slate-900" },
  ];
  return (
    <div className="space-y-4" data-testid="dp-overview">
      {/* iter226 · end-of-day handoff coaching · Tier-2 dispatch+admin.
          Anchor: "The handoff is a conversation, not a calendar invite." */}
      <HelpTipBlock formKey="dispatch.handoff" showCounter />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
        {cards.map((c) => (
          <div key={c.label} className={`bg-white border border-slate-200 border-l-4 ${c.stripe} rounded-md p-4`}>
            <div className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">{c.label}</div>
            <div className={`font-display text-3xl font-black mt-1 ${c.valueCls}`}>{c.value}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        <div className="bg-white border border-slate-200 rounded-md p-4">
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
        <div className="bg-white border border-slate-200 rounded-md p-4">
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
export function DispatchUtilizationTab() {
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
      {/* iter226 · utilization coaching · Tier-2 dispatch+admin.
          Anchor: "Utilization is a decision tool, not a scoreboard." */}
      <HelpTipBlock formKey="dispatch.utilization" showCounter />
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
      <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
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
export function DispatchTransfersTab() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  // iter504 · OMEGA Dispatch Production Readiness Sprint:
  // Terminal-state rows (Completed · Denied · Cancelled) are HIDDEN by
  // default — they are historical / audit residue, not actionable work.
  // Dispatcher sees only Submitted / Approved / Scheduled rows on the
  // active queue. "Show history" toggle reveals them when needed.
  const [showHistory, setShowHistory] = useState(false);
  // TRACK 15.83B — backend-canonical suppressed count (from
  // ?audience=operator response). 0 when admin/audit consumers call
  // without the audience query (legacy contract preserved).
  const [backendSuppressed, setBackendSuppressed] = useState(0);

  const load = async () => {
    setLoading(true);
    try {
      // TRACK 15.83B — request the canonical operator audience so
      // backend `lib/transfer_visibility.py` does the AUDIT/TEST/DEMO/
      // VALIDATION/SMOKE/SAMPLE suppression. Response shape:
      //   { items: [...], total, audience, suppressed_count }
      // We continue accepting the legacy flat-list shape so this is a
      // safe rollout (admin/audit callers without ?audience= still get
      // the unfiltered list).
      const r = await api.get("/operations/transfers?audience=operator");
      const data = r.data;
      if (Array.isArray(data)) {
        setList(data);
        setBackendSuppressed(0);
      } else if (data && Array.isArray(data.items)) {
        setList(data.items);
        setBackendSuppressed(Number(data.suppressed_count || 0));
      } else {
        setList([]);
        setBackendSuppressed(0);
      }
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const decide = async (xid, decision, extra = {}) => {
    try {
      await api.post(`/operations/transfers/${xid}/decide`, { decision, ...extra });
      toast.success(`Transfer ${decision}d`);
      load();
    } catch (e) {
      toast.error(operationalError(e, "Decision temporarily unavailable. Try again in a moment.", "Your Dispatch session expired. Please sign in again."));
    }
  };

  const TERMINAL = ["Completed", "Denied", "Cancelled"];
  // TRACK 15.83 + 15.83B — backend canonical operator filter is applied
  // upstream when we call `?audience=operator`. We still run the
  // frontend `isOperatorVisibleTransfer` defensively so that if the
  // backend ever falls back to the legacy flat list (older deploy,
  // direct admin call, etc.) the dispatcher surface still hides
  // obvious audit residue. `auditSuppressed` shown to operators is
  // backend count + any defensive-only frontend hits.
  const operatorVisible = list.filter(isOperatorVisibleTransfer);
  const frontendSuppressed = list.length - operatorVisible.length;
  const auditSuppressed = backendSuppressed + frontendSuppressed;
  const activeRows = operatorVisible.filter((x) => !TERMINAL.includes(x.status));
  const historyRows = operatorVisible.filter((x) => TERMINAL.includes(x.status));
  const visible = showHistory ? operatorVisible : activeRows;

  return (
    <div className="space-y-3" data-testid="dp-transfers">
      {/* iter216 · Tier-2 dispatcher coaching — protects schedule,
          equipment, and the crew's day. */}
      <HelpTipBlock formKey="dispatch.transfers" showCounter />
      <div className="flex items-center gap-2 flex-wrap">
        <Button onClick={() => setCreating(true)} className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="dp-transfer-new"><Plus className="w-3.5 h-3.5 mr-1" /> New Transfer</Button>
        <Button onClick={load} variant="outline" size="sm"><RefreshCcw className="w-3.5 h-3.5 mr-1" />Refresh</Button>
        {historyRows.length > 0 && (
          <Button
            onClick={() => setShowHistory((v) => !v)}
            variant="outline"
            size="sm"
            data-testid="dp-transfer-history-toggle"
            className="ml-auto text-slate-600"
          >
            {showHistory
              ? `Hide history (${historyRows.length})`
              : `Show history (${historyRows.length})`}
          </Button>
        )}
        {/* TRACK 15.83 — calm operator-trust signal when audit / validation
            rows were suppressed. Operators can still reach the full
            unfiltered list at /asset-transfers (Admin / PM). */}
        {auditSuppressed > 0 && (
          <span
            data-testid="dp-transfer-audit-suppressed"
            className="text-[10px] font-mono uppercase tracking-[0.15em] text-slate-500 ml-2"
            title="Audit / validation rows suppressed from the operator view"
          >
            · {auditSuppressed} audit row{auditSuppressed === 1 ? "" : "s"} hidden
          </span>
        )}
      </div>
      <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
        {loading ? (
          <div className="text-center py-8 text-slate-500"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
        ) : visible.length === 0 ? (
          <p className="px-4 py-3 text-xs text-slate-500 italic" data-testid="dp-transfer-empty">
            {activeRows.length === 0 && historyRows.length === 0
              ? "No transfer requests yet."
              : "No active transfers. Tap “Show history” to view past moves."}
          </p>
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
              {visible.map((x) => (
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
                      {!TERMINAL.includes(x.status) && (
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
      toast.error(operationalError(e, "Create temporarily unavailable. Try again in a moment.", "Your Dispatch session expired. Please sign in again."));
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
export function DispatchHoldsTab() {
  const [list, setList] = useState([]);
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [active, pend] = await Promise.all([
        api.get("/operations/holds?active_only=true"),
        api.get("/operations/holds?status=pending"),
      ]);
      setList(active.data || []);
      setPending(pend.data || []);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const release = async (hid) => {
    const note = window.prompt("Resolution note (optional)") || "";
    try { await api.post(`/operations/holds/${hid}/release`, { resolution: note }); toast.success("Hold released"); load(); }
    catch (e) { toast.error(operationalError(e, "Release temporarily unavailable. Try again in a moment.", "Your Dispatch session expired. Please sign in again.")); }
  };

  const approve = async (hid) => {
    if (!window.confirm("Approve this pending hold? The asset will be marked Maintenance/Safety Hold immediately.")) return;
    try { await api.post(`/operations/holds/${hid}/approve`, { note: "" }); toast.success("Hold approved"); load(); }
    catch (e) { toast.error(operationalError(e, "Approve temporarily unavailable. Try again in a moment.", "Your Dispatch session expired. Please sign in again.")); }
  };

  const dismiss = async (hid) => {
    const reason = window.prompt("Reason for dismissing this pending hold (REQUIRED):");
    if (!reason || !reason.trim()) { toast.error("Dismissal reason required"); return; }
    try { await api.post(`/operations/holds/${hid}/dismiss`, { reason }); toast.success("Hold dismissed"); load(); }
    catch (e) { toast.error(operationalError(e, "Dismiss temporarily unavailable. Try again in a moment.", "Your Dispatch session expired. Please sign in again.")); }
  };

  return (
    <div className="space-y-4" data-testid="dp-holds">
      {/* iter218 · Tier-2 dispatcher coaching — Safety/Shop place
          holds, Dispatch routes around them. Coaching anchor: "don't
          second-guess; see, route around, and watch for patterns." */}
      <HelpTipBlock formKey="dispatch.holds" showCounter />
      {/* Pending review queue */}
      {pending.length > 0 && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-md p-4" data-testid="dp-pending-holds">
          {/* Pending-specific coaching surface — only shown when there
              IS a pending queue, since that's when the coaching matters. */}
          <div className="mb-3">
            <HelpTipBlock formKey="dispatch.holds.pending" />
          </div>
          <div className="flex items-start gap-3 mb-3">
            <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-900 font-bold">
                Pending Maintenance / Safety Holds — admin review required
              </h3>
              <p className="text-xs text-amber-900 mt-0.5">
                These are auto-generated from failed pre-ops or other field signals. Equipment status is <strong>NOT</strong> changed
                until you approve. Dismissal requires a reason.
              </p>
            </div>
          </div>
          <table className="w-full text-xs">
            <thead className="text-amber-900 font-mono uppercase tracking-[0.15em]">
              <tr>
                <th className="text-left px-2 py-1">When</th>
                <th className="text-left px-2 py-1">Asset</th>
                <th className="text-left px-2 py-1">Kind</th>
                <th className="text-left px-2 py-1">Reason</th>
                <th className="text-left px-2 py-1">Source</th>
                <th className="text-left px-2 py-1">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((h) => (
                <tr key={h.id} className="border-t border-amber-200" data-testid={`dp-pending-row-${h.id}`}>
                  <td className="px-2 py-2 font-mono text-amber-900/70">{(h.created_at || "").slice(0,16).replace("T"," ")}</td>
                  <td className="px-2 py-2"><Link to={`/admin/assets/${h.asset_id}`} className="font-mono font-bold underline">{h.asset_id?.slice(0,8)}</Link></td>
                  <td className="px-2 py-2"><span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${h.kind === "safety" ? "bg-red-100 text-red-900 border-red-300" : "bg-amber-200 text-amber-900 border-amber-400"}`}>{h.kind}</span></td>
                  <td className="px-2 py-2">{h.reason}<div className="text-[10px] text-amber-900/70">{h.notes}</div></td>
                  <td className="px-2 py-2 font-mono text-[10px] text-amber-900/80">{h.source_module || "—"}</td>
                  <td className="px-2 py-2">
                    <div className="flex gap-1">
                      <Button size="sm" className="h-7 bg-emerald-700 hover:bg-emerald-800 text-white" onClick={() => approve(h.id)} data-testid={`dp-pending-approve-${h.id}`}>
                        <CheckCircle2 className="w-3 h-3 mr-1" />Approve
                      </Button>
                      <Button size="sm" variant="outline" className="h-7" onClick={() => dismiss(h.id)} data-testid={`dp-pending-dismiss-${h.id}`}>
                        <XCircle className="w-3 h-3 mr-1" />Dismiss
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-center gap-2">
        <Button onClick={() => setCreating(true)} className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="dp-hold-new"><Plus className="w-3.5 h-3.5 mr-1" /> Apply hold</Button>
        <Button onClick={load} variant="outline" size="sm"><RefreshCcw className="w-3.5 h-3.5 mr-1" />Refresh</Button>
      </div>
      <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
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
    catch (e) { toast.error(operationalError(e, "Apply temporarily unavailable. Try again in a moment.", "Your Dispatch session expired. Please sign in again.")); }
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

/* ════════════ IDLE EQUIPMENT ALERTS ════════════
   Read-only visibility layer. NEVER auto-changes status. NEVER notifies.
   Uses operations_events + asset_assignments only. Future Motive / preop
   / daily-report / maintenance signals can plug in via the operations
   event log without changing this UI. */
export function DispatchIdleAlertsTab() {
  const [minDays, setMinDays] = useState(14);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get(`/operations/idle-equipment?min_days=${minDays}&limit=500`);
      setData(r.data);
    } catch {
      setData({ rows: [], totals: { d7: 0, d14: 0, d30: 0, matched: 0 }, min_days: minDays });
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [minDays]);

  const totals = data?.totals || { d7: 0, d14: 0, d30: 0, matched: 0 };
  const rows = data?.rows || [];

  return (
    <div className="space-y-3" data-testid="dp-idle">
      {/* iter218 · Tier-2 dispatcher coaching — idle alerts are
          opportunity, not blame. Don't auto-recall; call the foreman. */}
      <HelpTipBlock formKey="dispatch.idle-alerts" showCounter />
      <div className="bg-amber-50 border-2 border-amber-300 rounded-md p-4 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-900">
          <strong>Read-only visibility layer.</strong> Idle alerts surface assigned assets that
          haven&apos;t produced an operations event (preop, transfer, hold change, daily-report
          reference) within the threshold. <strong>This widget never auto-changes equipment
          status, never reassigns, and never sends notifications.</strong>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Threshold</span>
        {[7, 14, 30].map((d) => (
          <Button
            key={d} size="sm" variant={minDays === d ? "default" : "outline"}
            onClick={() => setMinDays(d)} className="h-8"
            data-testid={`idle-filter-${d}d`}
          >
            &gt; {d} days {totals[`d${d}`] ? <span className="ml-1 font-mono text-[10px]">({totals[`d${d}`]})</span> : null}
          </Button>
        ))}
        <Button onClick={load} size="sm" variant="outline" className="h-8 ml-auto"><RefreshCcw className="w-3.5 h-3.5" /></Button>
      </div>

      <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
        {loading ? (
          <div className="text-center py-8 text-slate-500"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
        ) : rows.length === 0 ? (
          <p className="p-6 text-sm text-slate-500 italic text-center" data-testid="idle-empty">
            No assigned assets idle &gt; {minDays} days. Either nothing has been assigned long
            enough, or every assigned asset has had recent operational activity.
          </p>
        ) : (
          <table className="w-full text-xs" data-testid="idle-table">
            <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em]">
              <tr>
                <th className="text-left px-3 py-2">Days Idle</th>
                <th className="text-left px-3 py-2">Unit</th>
                <th className="text-left px-3 py-2">Equipment</th>
                <th className="text-left px-3 py-2">Project</th>
                <th className="text-left px-3 py-2">Operator</th>
                <th className="text-left px-3 py-2">Assigned</th>
                <th className="text-left px-3 py-2">Last activity</th>
                <th className="text-left px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const sev = r.days_inactive >= 30 ? "bg-red-100 text-red-900 border-red-300"
                  : r.days_inactive >= 14 ? "bg-amber-100 text-amber-900 border-amber-300"
                  : "bg-slate-100 text-slate-700 border-slate-300";
                return (
                  <tr key={r.asset_id} className="border-t border-slate-100" data-testid={`idle-row-${r.asset_id}`}>
                    <td className="px-3 py-2">
                      <span className={`px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.12em] font-bold ${sev}`}>
                        {r.days_inactive}d
                      </span>
                    </td>
                    <td className="px-3 py-2 font-mono font-bold">{r.unit_number || r.asset_id?.slice(0, 8)}</td>
                    <td className="px-3 py-2">
                      <div className="font-bold truncate max-w-xs">{r.equipment_name || "—"}</div>
                      {r.equipment_type && <div className="text-[10px] text-slate-500">{r.equipment_type}</div>}
                    </td>
                    <td className="px-3 py-2">{r.project_number || r.project_name || <span className="text-slate-400">—</span>}</td>
                    <td className="px-3 py-2">{r.operator_name || <span className="text-slate-400">—</span>}</td>
                    <td className="px-3 py-2 font-mono text-slate-500 whitespace-nowrap">{(r.assigned_at || "").slice(0, 10)}</td>
                    <td className="px-3 py-2">
                      {r.had_events ? (
                        <>
                          <div className="font-mono text-slate-700 text-[10px]">{r.last_activity_type}</div>
                          <div className="text-slate-500 text-[10px]">{(r.last_activity_at || "").slice(0, 16).replace("T", " ")}</div>
                        </>
                      ) : (
                        <span className="text-slate-400 italic text-[10px]">no events since assignment</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Link
                        to={`/admin/assets/${r.asset_id}`}
                        className="text-slate-700 hover:text-slate-900 font-bold underline whitespace-nowrap"
                        data-testid={`idle-profile-link-${r.asset_id}`}
                      >Profile →</Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {data && data.now && (
        <p className="text-[10px] font-mono text-slate-400 text-right">
          Computed at {(data.now || "").slice(0, 16).replace("T", " ")} · {totals.matched} match{totals.matched === 1 ? "" : "es"} for &gt; {minDays}d
        </p>
      )}
    </div>
  );
}

