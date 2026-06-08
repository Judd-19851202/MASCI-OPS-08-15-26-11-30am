/**
 * MappingCleanupTab.jsx · MCC-1 · Motive Mapping Cleanup Center
 * ─────────────────────────────────────────────────────────────
 * Mounted as the "Mapping Cleanup" tab inside AdminIntegrationCenter.
 *
 * Sub-sections (top → bottom):
 *   MCC-1D · Trust Score header (green/amber/red)
 *   MCC-1A · Driver cleanup queue
 *   MCC-1B · Asset cleanup queue
 *   MCC-1C · Conflict resolution
 *
 * Doctrine: reuses existing mapping endpoints + employees /
 * equipment_master pickers. No automation. Every action is a
 * single explicit operator click.
 */
import React, { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, ShieldCheck, Truck, Users, RefreshCcw,
  Link2, Ban, UserX, Archive, Layers, CheckCircle2, X, Loader2, IdCard,
} from "lucide-react";
import { Link as RouterLink } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { toast } from "sonner";

const BAND_PILL = {
  green: "bg-emerald-100 text-emerald-900 border-emerald-300",
  amber: "bg-amber-100 text-amber-900 border-amber-300",
  red:   "bg-rose-100 text-rose-900 border-rose-300",
};

function pct(n) {
  if (n == null || Number.isNaN(n)) return "—";
  return `${n}%`;
}

function TrustScoreHeader({ data, onRefresh, refreshing, mode = "admin" }) {
  if (!data) return null;
  const isHR = mode === "hr";
  const bandCls = BAND_PILL[data.trust?.band] || BAND_PILL.red;
  return (
    <section
      className="bg-white border border-slate-200 border-l-4 border-l-emerald-700 rounded-md p-5"
      data-testid="mcc-trust-header"
    >
      <div className="flex items-start gap-3 flex-wrap">
        <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white shrink-0">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-700 font-bold">
            MCC-1D · Motive Mapping Health
            {isHR ? <span className="ml-2 px-1.5 py-0.5 rounded border border-emerald-300 bg-emerald-50 text-emerald-900" data-testid="mcc-hr-scope-badge">HR scope</span> : null}
          </span>
          <h3 className="font-display text-2xl font-black tracking-tight text-slate-900 mt-0.5">
            {isHR ? "Motive Driver Cleanup" : "Mapping Cleanup Center"}
          </h3>
          <p className="text-xs text-slate-600 mt-1 max-w-2xl">
            {isHR
              ? "Resolve every Motive driver mapping issue without admin intervention — link, mark former, or ignore. Asset cleanup remains with Admin."
              : "Single screen to close the remaining trust gap with Motive — link unmapped drivers, link unmapped assets, resolve mapping conflicts. Watch the trust score climb to 100%."}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={refreshing}
          data-testid="mcc-refresh"
        >
          <RefreshCcw className={`w-3.5 h-3.5 mr-1 ${refreshing ? "animate-spin" : ""}`} /> Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mt-4">
        {/* Drivers linked */}
        <div className="rounded-md border-2 border-slate-200 bg-slate-50 p-3" data-testid="mcc-drivers-tile">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold text-slate-600">Drivers Linked</div>
          <div className="text-3xl font-black leading-none mt-1">
            {data.drivers.linked}
            <span className="text-base font-bold text-slate-500"> / {data.drivers.total}</span>
          </div>
          <span className={`inline-block mt-2 px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${BAND_PILL[data.drivers.band]}`}>
            {pct(data.drivers.pct)}
          </span>
        </div>
        {/* Assets linked */}
        <div className="rounded-md border-2 border-slate-200 bg-slate-50 p-3" data-testid="mcc-assets-tile">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold text-slate-600">Assets Linked</div>
          <div className="text-3xl font-black leading-none mt-1">
            {data.assets.linked}
            <span className="text-base font-bold text-slate-500"> / {data.assets.total}</span>
          </div>
          <span className={`inline-block mt-2 px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${BAND_PILL[data.assets.band]}`}>
            {pct(data.assets.pct)}
          </span>
        </div>
        {/* Conflicts */}
        <div className="rounded-md border-2 border-slate-200 bg-slate-50 p-3" data-testid="mcc-conflicts-tile">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold text-slate-600">Open Conflicts</div>
          <div className={`text-3xl font-black leading-none mt-1 ${data.conflicts.total > 0 ? "text-rose-700" : "text-slate-900"}`}>
            {data.conflicts.total}
          </div>
          <div className="text-[10px] font-mono text-slate-500 mt-2">
            {data.conflicts.asset} assets · {data.conflicts.driver} drivers
          </div>
        </div>
        {/* Trust */}
        <div className={`rounded-md border-2 ${bandCls.split(" ")[2]} ${bandCls.split(" ")[0]} ${bandCls.split(" ")[1]} p-3`} data-testid="mcc-trust-tile">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold opacity-80">Trust Score</div>
          <div className="text-3xl font-black leading-none mt-1">{pct(data.trust.pct)}</div>
          <div className="text-[10px] font-mono mt-2 font-bold uppercase tracking-wider">
            {data.trust.label}
          </div>
        </div>
      </div>
    </section>
  );
}

function PillCount({ label, value, tone = "slate", testid }) {
  const cls = {
    slate:   "bg-slate-100 text-slate-700 border-slate-300",
    emerald: "bg-emerald-100 text-emerald-900 border-emerald-300",
    rose:    "bg-rose-100 text-rose-900 border-rose-300",
    amber:   "bg-amber-100 text-amber-900 border-amber-300",
  }[tone] || "bg-slate-100 text-slate-700 border-slate-300";
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded border text-[11px] font-mono uppercase tracking-wider font-bold ${cls}`}
      data-testid={testid}
    >
      <span>{label}</span>
      <span className="text-sm font-black">{value}</span>
    </span>
  );
}

// Modal for picking a MASCI employee / equipment manually
function PickerDialog({ open, kind, onClose, onPick }) {
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        const path = kind === "asset"
          ? "/admin/integrations/asset-mappings/unmapped"
          : "/admin/integrations/employee-mappings/unmapped";
        const r = await api.get(path);
        if (alive) setItems(Array.isArray(r.data) ? r.data : []);
      } catch {
        if (alive) setItems([]);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [open, kind]);

  const filtered = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return items.slice(0, 200);
    return items.filter((it) => {
      const hay = kind === "asset"
        ? `${it.unit_number || ""} ${it.name || ""} ${it.vin || ""} ${it.make || ""} ${it.model || ""}`
        : `${it.name || ""} ${it.email || ""} ${it.trade || ""} ${it.employee_id || ""}`;
      return hay.toLowerCase().includes(term);
    }).slice(0, 200);
  }, [q, items, kind]);

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto" data-testid="mcc-picker-dialog">
        <DialogHeader>
          <DialogTitle>Pick {kind === "asset" ? "MASCI equipment" : "MASCI employee"}</DialogTitle>
          <DialogDescription>
            Only unmapped {kind === "asset" ? "equipment" : "employees"} appear here.
            Start typing to filter.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Input
            placeholder={kind === "asset" ? "Search unit number / VIN / make / model…" : "Search name / email / employee ID…"}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            data-testid="mcc-picker-search"
          />
          <div className="border border-slate-200 rounded-md max-h-[50vh] overflow-y-auto">
            {loading ? (
              <div className="text-center text-slate-500 text-sm py-6"><Loader2 className="w-4 h-4 inline animate-spin mr-2" /> Loading…</div>
            ) : filtered.length === 0 ? (
              <div className="text-center text-slate-500 text-sm py-6 italic">No matches.</div>
            ) : filtered.map((it) => (
              <button
                key={it.id}
                type="button"
                onClick={() => onPick(it)}
                className="w-full text-left px-3 py-2 border-b border-slate-100 hover:bg-emerald-50 text-xs"
                data-testid={`mcc-picker-row-${it.id}`}
              >
                {kind === "asset" ? (
                  <>
                    <div className="font-bold text-slate-900">{it.unit_number || "—"} · {it.name || it.make_model || "(unnamed)"}</div>
                    <div className="text-slate-500">VIN {it.vin || "—"} · {it.equipment_type || it.category || "—"}</div>
                  </>
                ) : (
                  <>
                    <div className="font-bold text-slate-900">{it.name || "—"}</div>
                    <div className="text-slate-500">{it.email || "—"}{it.trade ? ` · ${it.trade}` : ""}{it.employee_id ? ` · #${it.employee_id}` : ""}</div>
                  </>
                )}
              </button>
            ))}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function DriverQueue({ data, onRefresh, mode = "admin" }) {
  const isHR = mode === "hr";
  const profileBase = isHR ? "/hr/driver" : "/admin/driver-intel";
  const [filter, setFilter] = useState("all");
  const [picker, setPicker] = useState({ open: false, mappingId: null });
  const counts = data?.counts || { active_unlinked: 0, deactivated: 0, resolved: 0 };
  const rows = useMemo(() => {
    if (!data?.rows) return [];
    if (filter === "active_unlinked") return data.rows.filter((r) => !r.is_resolved && r.motive_status !== "deactivated");
    if (filter === "deactivated") return data.rows.filter((r) => !r.is_resolved && r.motive_status === "deactivated");
    if (filter === "resolved") return data.rows.filter((r) => r.is_resolved);
    if (filter === "unresolved") return data.rows.filter((r) => !r.is_resolved);
    return data.rows;
  }, [data, filter]);

  const act = async (path, mappingId, payload = {}) => {
    try {
      await api.post(`/admin/integrations/cleanup/drivers/${mappingId}/${path}`, payload);
      toast.success("Driver updated");
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Action failed");
    }
  };

  const doLink = async (mappingId, employeeId) => {
    try {
      await api.post(`/admin/integrations/cleanup/drivers/${mappingId}/link`, { employee_id: employeeId });
      toast.success("Driver linked");
      setPicker({ open: false, mappingId: null });
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Link failed");
    }
  };

  return (
    <section className="bg-white border border-slate-200 rounded-md p-5" data-testid="mcc-driver-queue">
      <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-slate-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-700 font-bold">MCC-1A · Motive Driver Cleanup</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <PillCount label="Active unlinked" value={counts.active_unlinked} tone={counts.active_unlinked > 0 ? "rose" : "slate"} testid="mcc-drv-cnt-active" />
          <PillCount label="Deactivated" value={counts.deactivated} tone={counts.deactivated > 0 ? "amber" : "slate"} testid="mcc-drv-cnt-deactivated" />
          <PillCount label="Resolved" value={counts.resolved} tone="emerald" testid="mcc-drv-cnt-resolved" />
        </div>
      </div>

      <div className="flex items-center gap-2 mb-3 text-xs">
        <span className="text-slate-500 font-mono">Filter:</span>
        {[
          ["all", "All"],
          ["unresolved", "Unresolved"],
          ["active_unlinked", "Active unlinked"],
          ["deactivated", "Deactivated"],
          ["resolved", "Resolved"],
        ].map(([k, label]) => (
          <button
            key={k}
            type="button"
            onClick={() => setFilter(k)}
            data-testid={`mcc-drv-filter-${k}`}
            className={`px-2 py-1 rounded border text-[11px] font-mono uppercase tracking-wider ${filter === k ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"}`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider text-[10px]">
            <tr>
              <th className="text-left px-2 py-1">Driver</th>
              <th className="text-left px-2 py-1">Email / Phone</th>
              <th className="text-left px-2 py-1">Motive Status</th>
              <th className="text-left px-2 py-1">Existing MASCI Match</th>
              <th className="text-left px-2 py-1">Candidate</th>
              <th className="text-right px-2 py-1">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 300).map((r) => (
              <tr key={r.mapping_id} className="border-t border-slate-100" data-testid={`mcc-drv-row-${r.mapping_id}`}>
                <td className="px-2 py-2 align-top">
                  <div className="font-bold text-slate-900">{r.motive_name}</div>
                  <div className="text-[10px] text-slate-500 font-mono">{r.motive_driver_id}</div>
                  {(r.existing_employee_id || r.motive_driver_id || r.motive_user_id) ? (
                    <RouterLink
                      to={`${profileBase}/${encodeURIComponent(r.existing_employee_id || r.motive_user_id || r.motive_driver_id)}`}
                      className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-indigo-700 hover:text-indigo-900 mt-1"
                      data-testid={`mcc-drv-profile-${r.mapping_id}`}
                    >
                      <IdCard className="w-3 h-3" /> Profile
                    </RouterLink>
                  ) : null}
                </td>
                <td className="px-2 py-2 align-top">
                  <div className="text-slate-700">{r.motive_email || <span className="text-slate-400 italic">—</span>}</div>
                  <div className="text-[10px] text-slate-500 font-mono">{r.motive_phone || ""}</div>
                </td>
                <td className="px-2 py-2 align-top">
                  <span className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${r.motive_status === "active" ? "bg-emerald-100 text-emerald-900 border-emerald-300" : r.motive_status === "deactivated" ? "bg-amber-100 text-amber-900 border-amber-300" : "bg-slate-100 text-slate-600 border-slate-300"}`}>
                    {r.motive_status}
                  </span>
                </td>
                <td className="px-2 py-2 align-top">
                  {r.existing_employee_id ? (
                    <div>
                      <div className="text-slate-900">{r.existing_employee_name || "(linked)"}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{r.existing_employee_id.slice(0, 8)}…</div>
                    </div>
                  ) : <span className="text-slate-400 italic">unlinked</span>}
                </td>
                <td className="px-2 py-2 align-top">
                  {r.candidate_employee_id && r.candidate_employee_id !== r.existing_employee_id ? (
                    <div>
                      <div className="text-slate-900">{r.candidate_employee_name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{r.match_method} · {r.match_confidence}</div>
                    </div>
                  ) : <span className="text-slate-400 italic">—</span>}
                </td>
                <td className="px-2 py-2 align-top text-right">
                  {r.is_resolved ? (
                    <span className="inline-flex items-center text-emerald-700 text-[10px] font-bold font-mono uppercase tracking-wider">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> {r.cleanup_status || "linked"}
                    </span>
                  ) : (
                    <div className="inline-flex gap-1 flex-wrap justify-end">
                      {r.candidate_employee_id ? (
                        <Button size="sm" variant="outline" className="h-7 px-2 text-[10px] border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                          onClick={() => doLink(r.mapping_id, r.candidate_employee_id)}
                          data-testid={`mcc-drv-link-candidate-${r.mapping_id}`}
                        >
                          <Link2 className="w-3 h-3 mr-0.5" /> Link Candidate
                        </Button>
                      ) : null}
                      <Button size="sm" variant="outline" className="h-7 px-2 text-[10px]"
                        onClick={() => setPicker({ open: true, mappingId: r.mapping_id })}
                        data-testid={`mcc-drv-link-existing-${r.mapping_id}`}
                      >
                        Link Existing
                      </Button>
                      <Button size="sm" variant="outline" className="h-7 px-2 text-[10px] border-amber-300 text-amber-800 hover:bg-amber-50"
                        onClick={() => act("former-employee", r.mapping_id)}
                        data-testid={`mcc-drv-former-${r.mapping_id}`}
                      >
                        <UserX className="w-3 h-3 mr-0.5" /> Former
                      </Button>
                      <Button size="sm" variant="outline" className="h-7 px-2 text-[10px] border-slate-300 text-slate-600 hover:bg-slate-50"
                        onClick={() => act("ignore", r.mapping_id)}
                        data-testid={`mcc-drv-ignore-${r.mapping_id}`}
                      >
                        <Ban className="w-3 h-3 mr-0.5" /> Ignore
                      </Button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <PickerDialog
        open={picker.open}
        kind="driver"
        onClose={() => setPicker({ open: false, mappingId: null })}
        onPick={(emp) => doLink(picker.mappingId, emp.id)}
      />
    </section>
  );
}

function AssetQueue({ data, onRefresh, mode = "admin" }) {
  const isHR = mode === "hr";
  const [filter, setFilter] = useState("unresolved");
  const [picker, setPicker] = useState({ open: false, mappingId: null });
  const counts = data?.counts || { operational: 0, retired: 0, unlinked: 0, resolved: 0 };
  const rows = useMemo(() => {
    if (!data?.rows) return [];
    if (filter === "operational") return data.rows.filter((r) => r.is_operational && !r.is_resolved);
    if (filter === "retired") return data.rows.filter((r) => r.cleanup_status === "retired");
    if (filter === "unlinked") return data.rows.filter((r) => !r.is_resolved);
    if (filter === "resolved") return data.rows.filter((r) => r.is_resolved);
    if (filter === "unresolved") return data.rows.filter((r) => !r.is_resolved);
    return data.rows;
  }, [data, filter]);

  const act = async (path, mappingId, payload = {}) => {
    try {
      await api.post(`/admin/integrations/cleanup/assets/${mappingId}/${path}`, payload);
      toast.success("Asset updated");
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Action failed");
    }
  };

  const doLink = async (mappingId, equipmentId) => {
    try {
      await api.post(`/admin/integrations/cleanup/assets/${mappingId}/link`, { equipment_id: equipmentId });
      toast.success("Asset linked");
      setPicker({ open: false, mappingId: null });
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Link failed");
    }
  };

  return (
    <section className="bg-white border border-slate-200 rounded-md p-5" data-testid="mcc-asset-queue">
      <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Truck className="w-4 h-4 text-slate-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-700 font-bold">MCC-1B · Motive Asset Cleanup</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <PillCount label="Operational unlinked" value={data?.rows?.filter((r) => r.is_operational && !r.is_resolved).length || 0} tone="rose" testid="mcc-ast-cnt-operational" />
          <PillCount label="Retired" value={counts.retired} tone="amber" testid="mcc-ast-cnt-retired" />
          <PillCount label="Unlinked" value={counts.unlinked} tone={counts.unlinked > 0 ? "rose" : "slate"} testid="mcc-ast-cnt-unlinked" />
          <PillCount label="Resolved" value={counts.resolved} tone="emerald" testid="mcc-ast-cnt-resolved" />
        </div>
      </div>

      <div className="flex items-center gap-2 mb-3 text-xs">
        <span className="text-slate-500 font-mono">Filter:</span>
        {[
          ["all", "All"],
          ["unresolved", "Unresolved"],
          ["operational", "Operational"],
          ["retired", "Retired"],
          ["resolved", "Resolved"],
        ].map(([k, label]) => (
          <button
            key={k}
            type="button"
            onClick={() => setFilter(k)}
            data-testid={`mcc-ast-filter-${k}`}
            className={`px-2 py-1 rounded border text-[11px] font-mono uppercase tracking-wider ${filter === k ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300"}`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider text-[10px]">
            <tr>
              <th className="text-left px-2 py-1">Unit / Name</th>
              <th className="text-left px-2 py-1">VIN / Type</th>
              <th className="text-left px-2 py-1">GPS · Last Seen</th>
              <th className="text-left px-2 py-1">Existing MASCI Match</th>
              <th className="text-left px-2 py-1">Candidate</th>
              <th className="text-right px-2 py-1">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 300).map((r) => (
              <tr key={r.mapping_id} className="border-t border-slate-100" data-testid={`mcc-ast-row-${r.mapping_id}`}>
                <td className="px-2 py-2 align-top">
                  <div className="font-bold text-slate-900 font-mono">{r.unit_number}</div>
                  <div className="text-[10px] text-slate-500">{r.motive_name || r.asset_kind}</div>
                </td>
                <td className="px-2 py-2 align-top">
                  <div className="text-slate-700 font-mono">{r.vin || <span className="text-slate-400 italic">—</span>}</div>
                  <div className="text-[10px] text-slate-500">{r.equipment_type || ""}</div>
                </td>
                <td className="px-2 py-2 align-top">
                  <span className={`inline-block px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold ${r.gps_enabled ? "bg-emerald-100 text-emerald-900 border-emerald-300" : "bg-slate-100 text-slate-600 border-slate-300"}`}>
                    {r.gps_enabled ? "GPS" : "No GPS"}
                  </span>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                    {r.located_at ? new Date(r.located_at).toLocaleDateString() : "—"}
                  </div>
                </td>
                <td className="px-2 py-2 align-top">
                  {r.existing_equipment_id ? (
                    <div>
                      <div className="text-slate-900">{r.existing_equipment_name || "(linked)"}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{r.existing_equipment_id.slice(0, 8)}…</div>
                    </div>
                  ) : <span className="text-slate-400 italic">unlinked</span>}
                </td>
                <td className="px-2 py-2 align-top">
                  {r.candidate_equipment_id && r.candidate_equipment_id !== r.existing_equipment_id ? (
                    <div>
                      <div className="text-slate-900">{r.candidate_unit_number} · {r.candidate_display || ""}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{r.match_method} · {r.match_confidence}</div>
                    </div>
                  ) : <span className="text-slate-400 italic">—</span>}
                </td>
                <td className="px-2 py-2 align-top text-right">
                  {r.is_resolved ? (
                    <span className="inline-flex items-center text-emerald-700 text-[10px] font-bold font-mono uppercase tracking-wider">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> {r.cleanup_status || "linked"}
                    </span>
                  ) : isHR ? (
                    <span
                      className="inline-flex items-center text-slate-400 text-[10px] font-mono uppercase tracking-wider italic"
                      data-testid={`mcc-ast-view-only-${r.mapping_id}`}
                    >
                      view only · admin owns
                    </span>
                  ) : (
                    <div className="inline-flex gap-1 flex-wrap justify-end">
                      {r.candidate_equipment_id ? (
                        <Button size="sm" variant="outline" className="h-7 px-2 text-[10px] border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                          onClick={() => doLink(r.mapping_id, r.candidate_equipment_id)}
                          data-testid={`mcc-ast-link-candidate-${r.mapping_id}`}
                        >
                          <Link2 className="w-3 h-3 mr-0.5" /> Link Candidate
                        </Button>
                      ) : null}
                      <Button size="sm" variant="outline" className="h-7 px-2 text-[10px]"
                        onClick={() => setPicker({ open: true, mappingId: r.mapping_id })}
                        data-testid={`mcc-ast-link-existing-${r.mapping_id}`}
                      >
                        Link Existing
                      </Button>
                      <Button size="sm" variant="outline" className="h-7 px-2 text-[10px] border-amber-300 text-amber-800 hover:bg-amber-50"
                        onClick={() => act("retire", r.mapping_id)}
                        data-testid={`mcc-ast-retire-${r.mapping_id}`}
                      >
                        <Archive className="w-3 h-3 mr-0.5" /> Retire
                      </Button>
                      <Button size="sm" variant="outline" className="h-7 px-2 text-[10px] border-slate-300 text-slate-600 hover:bg-slate-50"
                        onClick={() => act("ignore-gateway", r.mapping_id)}
                        data-testid={`mcc-ast-ignore-${r.mapping_id}`}
                      >
                        <Ban className="w-3 h-3 mr-0.5" /> Ignore Gateway
                      </Button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <PickerDialog
        open={picker.open}
        kind="asset"
        onClose={() => setPicker({ open: false, mappingId: null })}
        onPick={(eq) => doLink(picker.mappingId, eq.id)}
      />
    </section>
  );
}

function ConflictPanel({ data, onRefresh }) {
  const all = useMemo(() => {
    if (!data) return [];
    return [...(data.asset_conflicts || []), ...(data.driver_conflicts || [])];
  }, [data]);

  const resolve = async (c, action, manualTargetId = null) => {
    try {
      await api.post("/admin/integrations/cleanup/conflicts/resolve", {
        kind: c.kind,
        action,
        mapping_a_id: c.mapping_a?.id || "",
        mapping_b_id: c.mapping_b?.id || "",
        manual_target_id: manualTargetId || "",
      });
      toast.success("Conflict resolved");
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Resolution failed");
    }
  };

  return (
    <section className="bg-white border border-slate-200 rounded-md p-5" data-testid="mcc-conflict-panel">
      <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-700" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-700 font-bold">MCC-1C · Mapping Conflicts</span>
        </div>
        <PillCount label="Open" value={all.length} tone={all.length > 0 ? "rose" : "emerald"} testid="mcc-conflict-cnt" />
      </div>

      {all.length === 0 ? (
        <div className="text-sm text-slate-500 italic py-4" data-testid="mcc-conflict-empty">
          No open mapping conflicts. Every MASCI record currently has at most one Motive owner.
        </div>
      ) : (
        <div className="space-y-3">
          {all.map((c) => (
            <div key={c.conflict_id} className="bg-rose-50/40 border border-rose-200 rounded-md p-3" data-testid={`mcc-conflict-${c.conflict_id}`}>
              <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold text-rose-700 mb-1">
                {c.kind} · {c.conflict_type} · {c.reason}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="bg-white border border-slate-200 rounded p-2">
                  <div className="font-mono text-[9px] uppercase tracking-wider text-slate-500">Mapping A</div>
                  <div className="font-bold text-slate-900 mt-0.5">
                    {c.mapping_a?.motive_vehicle_id || c.mapping_a?.motive_driver_id || "—"} · {c.mapping_a?.motive_unit || c.mapping_a?.motive_name || ""}
                  </div>
                  <div className="text-[10px] text-slate-500">→ {c.mapping_a?.masci_unit_number || c.mapping_a?.masci_employee_name || "—"}</div>
                </div>
                <div className="bg-white border border-slate-200 rounded p-2">
                  <div className="font-mono text-[9px] uppercase tracking-wider text-slate-500">Mapping B</div>
                  <div className="font-bold text-slate-900 mt-0.5">
                    {c.mapping_b?.motive_vehicle_id || c.mapping_b?.motive_driver_id || "—"} · {c.mapping_b?.motive_unit || c.mapping_b?.motive_name || ""}
                  </div>
                  <div className="text-[10px] text-slate-500">→ {c.mapping_b?.masci_unit_number || c.mapping_b?.masci_employee_name || "—"}</div>
                </div>
              </div>
              <div className="flex gap-2 mt-3 flex-wrap">
                <Button size="sm" variant="outline" className="h-7 px-2 text-[10px] border-emerald-300 text-emerald-700"
                  onClick={() => resolve(c, "keep_a")}
                  data-testid={`mcc-conflict-keepa-${c.conflict_id}`}
                >Keep Mapping A</Button>
                <Button size="sm" variant="outline" className="h-7 px-2 text-[10px] border-emerald-300 text-emerald-700"
                  onClick={() => resolve(c, "keep_b")}
                  data-testid={`mcc-conflict-keepb-${c.conflict_id}`}
                >Keep Mapping B</Button>
                <Button size="sm" variant="outline" className="h-7 px-2 text-[10px] border-slate-300 text-slate-600"
                  onClick={() => resolve(c, "dismiss")}
                  data-testid={`mcc-conflict-dismiss-${c.conflict_id}`}
                >Dismiss</Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default function MappingCleanupTab({ mode = "admin" }) {
  const isHR = mode === "hr";
  const [trust, setTrust] = useState(null);
  const [drivers, setDrivers] = useState(null);
  const [assets, setAssets] = useState(null);
  const [conflicts, setConflicts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [err, setErr] = useState("");

  const load = async () => {
    setRefreshing(true);
    try {
      const [t, d, a, c] = await Promise.all([
        api.get("/admin/integrations/cleanup/trust-score"),
        api.get("/admin/integrations/cleanup/drivers"),
        api.get("/admin/integrations/cleanup/assets"),
        api.get("/admin/integrations/cleanup/conflicts"),
      ]);
      setTrust(t.data);
      setDrivers(d.data);
      setAssets(a.data);
      setConflicts(c.data);
      setErr("");
    } catch (e) {
      setErr(e?.response?.data?.detail || "Failed to load Mapping Cleanup Center");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div className="text-center text-slate-500 py-12" data-testid="mcc-loading">
      <Loader2 className="w-5 h-5 inline animate-spin mr-2" /> Loading Mapping Cleanup Center…
    </div>
  );
  if (err) return (
    <div className="bg-rose-50 border-2 border-rose-200 rounded-md p-4 text-sm text-rose-800" data-testid="mcc-error">
      <AlertTriangle className="w-4 h-4 inline -mt-0.5 mr-1" /> {err}
    </div>
  );

  return (
    <div className="space-y-5" data-testid={isHR ? "mcc-cleanup-tab-hr" : "mcc-cleanup-tab"}>
      <TrustScoreHeader data={trust} onRefresh={load} refreshing={refreshing} mode={mode} />
      <DriverQueue data={drivers} onRefresh={load} mode={mode} />
      <AssetQueue data={assets} onRefresh={load} mode={mode} />
      {!isHR ? <ConflictPanel data={conflicts} onRefresh={load} /> : null}
    </div>
  );
}
