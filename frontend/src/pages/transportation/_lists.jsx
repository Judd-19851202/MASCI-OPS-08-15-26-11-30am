/**
 * TRACK 16.06 · Transportation Experience · Lists & Workspaces.
 * CarriersList · DriversList · TrucksList
 * CarrierWorkspace · DriverWorkspace · TruckWorkspace
 */
import React, { useEffect, useState, useCallback } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  Building2, UserRound, Truck as TruckIcon, ArrowLeft, ExternalLink,
  RefreshCw, Phone, Mail, FileText, ClipboardCheck, DollarSign,
  ShieldCheck, Search, UserPlus, Pencil, Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Chip, PageHeader, ComingSoon, EmptyState, txGet, txPost, txPatch, isTxRestricted,
} from "./_shared";
import {
  DocumentDropzone, InspectionWizard, ComplianceTimeline, PacketChecklist,
} from "./_widgets";
import { TxOpsRestrictedData } from "@/components/transportation/TxOpsRestricted";
import {
  LinkHRDriverModal, AddLeasedDriverModal, AddCarrierModal, EditCarrierModal,
} from "./_modals";

const CARRIER_DOC_TYPES = [
  "sunbiz_certificate", "mcs_company_snapshot", "w9", "insurance_certificate",
  "hauling_agreement", "vehicle_registration", "lien_release_authorization",
  "payment_pickup_authorization", "other",
];
const DRIVER_DOC_TYPES = [
  "cdl", "medical_card", "clearinghouse", "driver_license",
  "dot_certification", "drug_alcohol_acknowledgement",
  "orientation_acknowledgement_placeholder", "other",
];

function useStateFilter() {
  const [params] = useSearchParams();
  return {
    state: params.get("state") || "",
    status: params.get("status") || "",
  };
}

function buildEligibilityMap(target_type, items, dashboard) {
  // We pull eligibility states from the dashboard.buckets when possible;
  // a per-row lookup happens when the workspace is opened.
  const _ = dashboard?.buckets?.[target_type] || {};
  void _;
  return new Map();
}

// ───────────────────────── Carriers list ─────────────────────────
function CarrierStatusSummary({ rows }) {
  if (!rows || rows.length === 0) return null;
  const counts = rows.reduce((acc, c) => {
    const k = c.status || "unknown";
    acc[k] = (acc[k] || 0) + 1;
    acc.holds = (acc.holds || 0) + (c.safety_hold ? 1 : 0);
    return acc;
  }, {});
  const total = rows.length;
  const pending = counts.pending_review || 0;
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs" data-testid="tx-carriers-summary">
      <span className="px-2 py-1 rounded bg-slate-50 border border-slate-200" data-testid="tx-carriers-summary-total">
        <strong className="text-slate-900">{total}</strong> <span className="text-slate-500">total</span>
      </span>
      <span className="px-2 py-1 rounded bg-emerald-50 border border-emerald-200 text-emerald-800">
        <strong>{counts.active || 0}</strong> active
      </span>
      {pending > 0 && (
        <span
          className="px-2 py-1 rounded bg-amber-50 border border-amber-300 text-amber-900 font-medium"
          data-testid="tx-carriers-summary-pending"
          title="Carriers awaiting documentation, insurance, or driver linkage"
        >
          <strong>{pending}</strong> pending review
        </span>
      )}
      {(counts.holds || 0) > 0 && (
        <span className="px-2 py-1 rounded bg-rose-50 border border-rose-200 text-rose-900" data-testid="tx-carriers-summary-holds">
          <strong>{counts.holds}</strong> on safety hold
        </span>
      )}
    </div>
  );
}

export function CarriersList() {
  const [rows, setRows] = useState([]);
  const [restricted, setRestricted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState(null);
  const { status } = useStateFilter();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (status) params.status = status;
      if (q) params.q = q;
      const r = await txGet("/admin/transportation/carriers", params);
      if (isTxRestricted(r)) { setRestricted(true); setRows([]); return; }
      setRestricted(false);
      setRows(r.data.items || []);
    } finally {
      setLoading(false);
    }
  }, [q, status]);
  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid="tx-carriers-list" className="space-y-4">
      <PageHeader
        title="Carriers"
        subtitle="Leased haulers, owner-operators, suppliers, and MASCI-internal carriers."
        right={
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={load} data-testid="carriers-list-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
            <Button onClick={() => setShowAdd(true)} data-testid="carriers-list-add"><Plus className="h-4 w-4 mr-1" />Add Carrier</Button>
          </div>
        }
      />
      {restricted ? <TxOpsRestrictedData testid="tx-carriers-list-restricted" /> : (
        <>
      <CarrierStatusSummary rows={rows} />
      <div className="flex items-center gap-2">
        <div className="relative">
          <Search className="h-4 w-4 absolute left-2 top-2.5 text-slate-400" />
          <Input
            data-testid="carriers-search"
            placeholder="Search legal name, DBA, DOT…"
            className="pl-8 w-72"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
          />
        </div>
      </div>
      {loading ? <div data-testid="carriers-list-loading">Loading…</div> : (
        rows.length === 0 ? (
          <EmptyState title="No carriers match" testid="carriers-list-empty" />
        ) : (
          <div className="overflow-x-auto border border-slate-200 rounded">
            <table className="w-full text-sm" data-testid="carriers-list-table">
              <thead className="bg-slate-50 text-left">
                <tr>
                  <th className="px-3 py-2">Legal Name</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">DOT</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Safety Hold</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((c) => (
                  <tr key={c.id} className="border-t border-slate-100" data-testid={`carriers-list-row-${c.id}`}>
                    <td className="px-3 py-2 font-medium">{c.legal_name}</td>
                    <td className="px-3 py-2 text-slate-600">{c.carrier_type}</td>
                    <td className="px-3 py-2 text-slate-600">{c.dot_number || "—"}</td>
                    <td className="px-3 py-2"><Chip value={c.status} /></td>
                    <td className="px-3 py-2 text-slate-600">{c.safety_hold ? "Yes" : "No"}</td>
                    <td className="px-3 py-2 text-right space-x-2">
                      <button
                        type="button"
                        className="text-blue-600 hover:underline text-xs"
                        onClick={() => setEditing(c)}
                        data-testid={`carrier-edit-${c.id}`}
                      >
                        <Pencil className="inline h-3 w-3" /> Edit
                      </button>
                      <Link to={`/admin/transportation/carriers/${c.id}`} className="text-blue-600 hover:underline text-xs" data-testid={`carrier-open-${c.id}`}>
                        Open <ExternalLink className="inline h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
        </>
      )}
      <AddCarrierModal open={showAdd} onClose={() => setShowAdd(false)} onCreated={() => load()} />
      <EditCarrierModal open={!!editing} carrier={editing} onClose={() => setEditing(null)} onUpdated={() => load()} />
    </div>
  );
}

// ───────────────────────── Drivers list ─────────────────────────
export function DriversList() {
  const [rows, setRows] = useState([]);
  const [restricted, setRestricted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [showLink, setShowLink] = useState(false);
  const [showAddLeased, setShowAddLeased] = useState(false);
  const { status } = useStateFilter();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (status) params.status = status;
      if (q) params.q = q;
      const r = await txGet("/admin/transportation/persons", params);
      if (isTxRestricted(r)) { setRestricted(true); setRows([]); return; }
      setRestricted(false);
      setRows(r.data.items || []);
    } finally {
      setLoading(false);
    }
  }, [q, status]);
  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid="tx-drivers-list" className="space-y-4">
      <PageHeader title="Drivers" subtitle="MASCI CDL employees and leased / carrier drivers." right={
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={load} data-testid="drivers-list-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
          <Button variant="outline" onClick={() => setShowAddLeased(true)} data-testid="drivers-list-add-leased"><Plus className="h-4 w-4 mr-1" />Add Leased Driver</Button>
          <Button onClick={() => setShowLink(true)} data-testid="drivers-list-link-hr"><UserPlus className="h-4 w-4 mr-1" />Link MASCI CDL Driver</Button>
        </div>
      } />
      {restricted ? <TxOpsRestrictedData testid="tx-drivers-list-restricted" /> : (
        <>
      <div className="flex items-center gap-2">
        <div className="relative">
          <Search className="h-4 w-4 absolute left-2 top-2.5 text-slate-400" />
          <Input
            data-testid="drivers-search"
            placeholder="Search name, email, license…"
            className="pl-8 w-72"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
          />
        </div>
      </div>
      {loading ? <div data-testid="drivers-list-loading">Loading…</div> : (
        rows.length === 0 ? (
          <EmptyState title="No drivers match" testid="drivers-list-empty" />
        ) : (
          <div className="overflow-x-auto border border-slate-200 rounded">
            <table className="w-full text-sm" data-testid="drivers-list-table">
              <thead className="bg-slate-50 text-left">
                <tr>
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Kind</th>
                  <th className="px-3 py-2">Reference</th>
                  <th className="px-3 py-2">License</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((p) => (
                  <tr key={p.id} className="border-t border-slate-100" data-testid={`drivers-list-row-${p.id}`}>
                    <td className="px-3 py-2 font-medium">{p.first_name} {p.last_name}</td>
                    <td className="px-3 py-2 text-slate-600">{p.kind}</td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {p.kind === "leased_driver" ? (p.carrier_id || "—") : (p.employee_id || "—")}
                    </td>
                    <td className="px-3 py-2 text-slate-600">{p.license_number || "—"}</td>
                    <td className="px-3 py-2"><Chip value={p.status} /></td>
                    <td className="px-3 py-2 text-right">
                      <Link to={`/admin/transportation/drivers/${p.id}`} className="text-blue-600 hover:underline text-xs" data-testid={`driver-open-${p.id}`}>
                        Open <ExternalLink className="inline h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
        </>
      )}
      <LinkHRDriverModal open={showLink} onClose={() => setShowLink(false)} onLinked={() => load()} />
      <AddLeasedDriverModal open={showAddLeased} onClose={() => setShowAddLeased(false)} onCreated={() => load()} />
    </div>
  );
}

// ───────────────────────── Trucks list (Track 19.02 Fleet projection) ─────────────────────────
// Reads from the projection endpoint that joins equipment_master +
// equipment_units + transport_trucks overlay. The Transportation Trucks
// page is a VIEW into the MASCI fleet, not a separate fleet database.
// Track 19.02A adds the bulk adoption flow + per-row operational editor.
export function TrucksList() {
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState(null);
  const [restricted, setRestricted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [ownershipFilter, setOwnershipFilter] = useState("");
  const [showBulk, setShowBulk] = useState(false);
  const [editTarget, setEditTarget] = useState(null); // row to edit
  const { status } = useStateFilter();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 1000 };
      if (status) params.status = status;
      if (q) params.q = q;
      if (categoryFilter) params.category = categoryFilter;
      if (ownershipFilter) params.ownership = ownershipFilter;
      const r = await txGet("/admin/transportation/fleet/equipment", params);
      if (isTxRestricted(r)) { setRestricted(true); setItems([]); setSummary(null); return; }
      setRestricted(false);
      setItems(r.data.items || []);
      setSummary(r.data.summary || null);
    } finally {
      setLoading(false);
    }
  }, [q, status, categoryFilter, ownershipFilter]);
  useEffect(() => { load(); }, [load]);

  const categories = summary?.categories || [];
  const adoptedPct = summary && summary.masci_fleet_total
    ? Math.round(100 * summary.masci_fleet_adopted / summary.masci_fleet_total)
    : 0;

  return (
    <div data-testid="tx-trucks-list" className="space-y-4">
      <PageHeader
        title="Fleet"
        subtitle="Transportation view of the MASCI fleet · one asset, one source of truth."
        right={
          <div className="flex items-center gap-2">
            <Button
              onClick={() => setShowBulk(true)}
              data-testid="tx-fleet-bulk-adopt-btn"
            >
              Adopt All Transportation Assets
            </Button>
            <Button variant="outline" onClick={load} data-testid="trucks-list-refresh">
              <RefreshCw className="h-4 w-4 mr-1" />Refresh
            </Button>
          </div>
        }
      />
      {summary && !restricted && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3" data-testid="tx-fleet-summary">
          <div className="rounded border border-slate-200 px-3 py-2" data-testid="tx-fleet-summary-masci">
            <div className="text-xs text-slate-500">MASCI fleet (transport-capable)</div>
            <div className="text-2xl font-semibold text-slate-900">{summary.masci_fleet_total}</div>
          </div>
          <div className="rounded border border-slate-200 px-3 py-2" data-testid="tx-fleet-summary-adopted">
            <div className="text-xs text-slate-500">Adopted into Transportation</div>
            <div className="text-2xl font-semibold text-slate-900">
              {summary.masci_fleet_adopted}
              <span className="text-sm text-slate-500 font-normal"> · {adoptedPct}%</span>
            </div>
          </div>
          <div className="rounded border border-slate-200 px-3 py-2" data-testid="tx-fleet-summary-leased">
            <div className="text-xs text-slate-500">Leased / owner-operator</div>
            <div className="text-2xl font-semibold text-slate-900">{summary.leased_total}</div>
          </div>
          <div className="rounded border border-slate-200 px-3 py-2" data-testid="tx-fleet-summary-total">
            <div className="text-xs text-slate-500">Surfaced in this view</div>
            <div className="text-2xl font-semibold text-slate-900">{items.length}</div>
          </div>
        </div>
      )}
      {restricted ? <TxOpsRestrictedData testid="tx-trucks-list-restricted" /> : (
        <>
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="h-4 w-4 absolute left-2 top-2.5 text-slate-400" />
          <Input
            data-testid="trucks-search"
            placeholder="Search asset #, VIN, plate, make/model…"
            className="pl-8 w-72"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
          />
        </div>
        <select
          data-testid="tx-fleet-filter-category"
          className="border border-slate-200 rounded px-2 py-2 text-sm"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">All categories</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select
          data-testid="tx-fleet-filter-ownership"
          className="border border-slate-200 rounded px-2 py-2 text-sm"
          value={ownershipFilter}
          onChange={(e) => setOwnershipFilter(e.target.value)}
        >
          <option value="">All ownership</option>
          <option value="masci_owned">MASCI-owned</option>
          <option value="leased_carrier">Leased carrier</option>
          <option value="owner_operator">Owner-operator</option>
        </select>
      </div>
      {loading ? <div data-testid="trucks-list-loading">Loading…</div> : (
        items.length === 0 ? (
          <EmptyState title="No fleet assets match" testid="trucks-list-empty" />
        ) : (
          <div className="overflow-x-auto border border-slate-200 rounded">
            <table className="w-full text-sm" data-testid="trucks-list-table">
              <thead className="bg-slate-50 text-left">
                <tr>
                  <th className="px-3 py-2">Asset</th>
                  <th className="px-3 py-2">Category</th>
                  <th className="px-3 py-2">Ownership</th>
                  <th className="px-3 py-2">VIN / Reference</th>
                  <th className="px-3 py-2">Transport status</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {items.map((t) => {
                  const overlay = t.transport_overlay || {};
                  const rowKey = `${t.source}-${t.id}`;
                  const detailHref = overlay.exists && overlay.truck_id
                    ? `/admin/transportation/trucks/${overlay.truck_id}`
                    : null;
                  return (
                    <tr key={rowKey} className="border-t border-slate-100" data-testid={`trucks-list-row-${rowKey}`}>
                      <td className="px-3 py-2">
                        <div className="font-medium text-slate-900">{t.unit_number || t.asset_id || "—"}</div>
                        <div className="text-xs text-slate-500">{t.label || t.make_model || ""}</div>
                      </td>
                      <td className="px-3 py-2 text-slate-600">{t.category}</td>
                      <td className="px-3 py-2 text-slate-600">{(t.ownership || "").replace(/_/g, " ")}</td>
                      <td className="px-3 py-2 font-mono text-xs">{t.vin || t.plate || "—"}</td>
                      <td className="px-3 py-2">
                        {overlay.exists ? (
                          <Chip value={overlay.status || "pending_review"} />
                        ) : (
                          <span className="text-xs text-slate-500">not adopted</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex items-center gap-3 justify-end">
                          {overlay.exists && t.source === "equipment_master" && (
                            <button
                              onClick={() => setEditTarget(t)}
                              className="text-xs text-blue-600 hover:underline"
                              data-testid={`tx-fleet-edit-${t.id}`}
                            >
                              Edit Transportation Details
                            </button>
                          )}
                          {detailHref ? (
                            <Link to={detailHref} className="text-blue-600 hover:underline text-xs" data-testid={`truck-open-${overlay.truck_id}`}>
                              Open <ExternalLink className="inline h-3 w-3" />
                            </Link>
                          ) : (
                            <AdoptButton equipmentId={t.id} onAdopted={load} />
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )
      )}
        </>
      )}
      {showBulk && (
        <FleetBulkAdoptionModal
          onClose={() => setShowBulk(false)}
          onCompleted={() => { setShowBulk(false); load(); }}
        />
      )}
      {editTarget && (
        <FleetOverlayEditModal
          row={editTarget}
          onClose={() => setEditTarget(null)}
          onSaved={() => { setEditTarget(null); load(); }}
        />
      )}
    </div>
  );
}

function AdoptButton({ equipmentId, onAdopted }) {
  const [busy, setBusy] = useState(false);
  const click = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await txPost(`/admin/transportation/fleet/equipment/${equipmentId}/adopt`, {});
      onAdopted && onAdopted();
    } finally {
      setBusy(false);
    }
  };
  return (
    <button
      onClick={click}
      disabled={busy}
      className="text-xs text-blue-600 hover:underline disabled:opacity-50"
      data-testid={`tx-fleet-adopt-${equipmentId}`}
    >
      {busy ? "Adopting…" : "Adopt into Transportation"}
    </button>
  );
}

// ───────── Track 19.02A · Bulk Adoption modal (preview-first) ─────────
function FleetBulkAdoptionModal({ onClose, onCompleted }) {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);

  const loadPreview = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet("/admin/transportation/fleet/adoption-preview", {});
      setPreview(r.data || null);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { loadPreview(); }, [loadPreview]);

  const execute = async () => {
    if (executing) return;
    setExecuting(true);
    try {
      const r = await txPost("/admin/transportation/fleet/adoption-bulk", {});
      setResult(r.data || null);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4"
         data-testid="tx-fleet-bulk-adopt-modal" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
           onClick={(e) => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Transportation Fleet Adoption</h2>
            <p className="text-xs text-slate-500">
              Preview before execution · equipment records will NOT be duplicated.
            </p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-800" data-testid="tx-fleet-bulk-close">✕</button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500" data-testid="tx-fleet-bulk-loading">Loading preview…</div>
        ) : result ? (
          <div className="p-6 space-y-3" data-testid="tx-fleet-bulk-result">
            <div className="text-emerald-700 text-sm font-medium">
              ✓ Adoption complete
            </div>
            <Row2 k="Scanned" v={result.scanned} />
            <Row2 k="Created" v={result.created} testid="tx-fleet-bulk-result-created" />
            <Row2 k="Already adopted" v={result.skipped_already_adopted} />
            <Row2 k="Retired (skipped)" v={result.skipped_retired} />
            <Row2 k="Errors" v={result.errors} />
            <Row2 k="Elapsed (ms)" v={result.elapsed_ms} />
            <Row2 k="Batch ID" v={<span className="font-mono text-xs">{result.batch_id}</span>} />
            <p className="text-xs text-slate-500 pt-2">
              If you need to undo this batch, an administrator can rollback via{" "}
              <code className="text-xs">POST /admin/transportation/fleet/adoption-bulk/&#123;batch_id&#125;/rollback</code>
            </p>
            <div className="flex justify-end gap-2 pt-3">
              <Button onClick={onCompleted} data-testid="tx-fleet-bulk-done">Done</Button>
            </div>
          </div>
        ) : preview ? (
          <div className="p-6 space-y-4" data-testid="tx-fleet-bulk-preview">
            <div className="grid grid-cols-3 gap-3 text-sm">
              <Tile label="Already adopted" value={preview.summary.already_adopted} />
              <Tile label="Would adopt" value={preview.summary.would_adopt} accent="emerald" testid="tx-fleet-bulk-would-adopt" />
              <Tile label="Skipped (retired/inactive)" value={preview.summary.skipped_retired + preview.summary.skipped_inactive} />
              <Tile label="Conflicts" value={preview.summary.conflicts} accent={preview.summary.conflicts ? "rose" : null} />
              <Tile label="Missing equipment ID" value={preview.summary.missing_equipment_id} />
              <Tile label="Needs operator classification" value={preview.summary.unknown_classification} accent={preview.summary.unknown_classification ? "amber" : null} />
            </div>
            <div className="text-xs text-slate-500">
              Categories in scope: {(preview.categories_in_scope || []).join(" · ")}
            </div>
            <div className="rounded bg-slate-50 border border-slate-200 px-3 py-2 text-xs text-slate-700">
              This operation is completely safe. Equipment records will NOT be
              duplicated. Transportation overlays will simply be created where
              missing. The operation is idempotent — running it again will
              produce zero new overlays.
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={onClose} data-testid="tx-fleet-bulk-cancel">Cancel</Button>
              <Button variant="outline" onClick={loadPreview} data-testid="tx-fleet-bulk-preview-again">Preview Again</Button>
              <Button onClick={execute} disabled={executing || preview.summary.would_adopt === 0} data-testid="tx-fleet-bulk-execute">
                {executing ? "Adopting…" : `Adopt ${preview.summary.would_adopt} assets`}
              </Button>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-rose-600">Failed to load preview.</div>
        )}
      </div>
    </div>
  );
}

function Tile({ label, value, accent, testid }) {
  const colors = {
    emerald: "bg-emerald-50 border-emerald-200 text-emerald-900",
    amber: "bg-amber-50 border-amber-200 text-amber-900",
    rose: "bg-rose-50 border-rose-200 text-rose-900",
  };
  const cls = accent ? colors[accent] : "bg-slate-50 border-slate-200 text-slate-900";
  return (
    <div className={`rounded border px-3 py-2 ${cls}`} data-testid={testid}>
      <div className="text-xs opacity-75">{label}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Row2({ k, v, testid }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-500">{k}</span>
      <span className="text-slate-900" data-testid={testid}>{v}</span>
    </div>
  );
}

// ───── Track 19.02A · Per-row Edit Transportation Details modal ─────
const CLASSIFICATIONS = [
  "heavy_haul", "end_dump", "transfer", "day_cab", "sleeper",
  "lowboy", "equipment_hauler", "equipment_trailer", "tag_trailer",
  "flatbed", "water_truck", "fuel_truck", "service_truck",
  "pole_trailer", "jeep_dolly", "other",
];
const STATUSES = ["pending_review", "active", "on_hold", "inactive", "retired", "out_of_service"];

function FleetOverlayEditModal({ row, onClose, onSaved }) {
  const overlay = row.transport_overlay || {};
  const [form, setForm] = useState({
    transportation_classification: overlay.transportation_classification || "other",
    truck_type: overlay.truck_type || "other",
    status: overlay.status || "pending_review",
    safety_hold: !!overlay.safety_hold,
    dispatch_ready: !!overlay.dispatch_ready,
    active_for_transport: overlay.active_for_transport !== false,
    primary_division: overlay.primary_division || "",
    transportation_notes: overlay.transportation_notes || "",
    operational_tags: (overlay.operational_tags || []).join(", "),
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        transportation_classification: form.transportation_classification,
        truck_type: form.truck_type,
        status: form.status,
        safety_hold: form.safety_hold,
        dispatch_ready: form.dispatch_ready,
        active_for_transport: form.active_for_transport,
        primary_division: form.primary_division || null,
        transportation_notes: form.transportation_notes || null,
        operational_tags: form.operational_tags
          .split(",").map((s) => s.trim()).filter(Boolean),
      };
      const r = await txPatch(
        `/admin/transportation/fleet/equipment/${row.id}/overlay`,
        payload);
      if (r.error) {
        setError(typeof r.error === "string" ? r.error :
          (r.error.message || JSON.stringify(r.error)));
      } else {
        onSaved && onSaved();
      }
    } catch (e) {
      const detail = e?.response?.data?.detail;
      if (detail && typeof detail === "object" && detail.message) {
        setError(detail.message);
      } else if (typeof detail === "string") {
        setError(detail);
      } else {
        setError(String(e?.message || e));
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4"
         data-testid="tx-fleet-edit-modal" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
           onClick={(e) => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-slate-200 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">Edit Transportation Details</h2>
            <p className="text-xs text-slate-500">
              Asset {row.unit_number || row.asset_id} · {row.label || row.make_model}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Enterprise asset fields (VIN · make · model · year · purchase data) are managed by the MASCI Equipment platform.
            </p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-800" data-testid="tx-fleet-edit-close">✕</button>
        </div>

        <div className="p-6 space-y-6">
          <section>
            <h3 className="text-sm font-semibold mb-2 text-slate-700">Transportation Classification</h3>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Transportation classification">
                <select
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                  value={form.transportation_classification}
                  onChange={(e) => setForm({ ...form, transportation_classification: e.target.value })}
                  data-testid="tx-fleet-edit-classification"
                >
                  {CLASSIFICATIONS.map((c) => <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}
                </select>
              </Field>
              <Field label="Truck type">
                <select
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                  value={form.truck_type}
                  onChange={(e) => setForm({ ...form, truck_type: e.target.value })}
                  data-testid="tx-fleet-edit-truck-type"
                >
                  {["dump_truck", "flow_boy", "lowboy", "tanker", "roll_off", "service_truck", "other"].map((c) =>
                    <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}
                </select>
              </Field>
            </div>
          </section>

          <section>
            <h3 className="text-sm font-semibold mb-2 text-slate-700">Dispatch Operations</h3>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Operational status">
                <select
                  className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  data-testid="tx-fleet-edit-status"
                >
                  {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
                </select>
              </Field>
              <Field label="Primary operating division">
                <Input
                  value={form.primary_division}
                  onChange={(e) => setForm({ ...form, primary_division: e.target.value })}
                  placeholder="e.g. North Yard"
                  data-testid="tx-fleet-edit-division"
                />
              </Field>
              <Field label="Dispatch ready" inline>
                <input
                  type="checkbox"
                  checked={form.dispatch_ready}
                  onChange={(e) => setForm({ ...form, dispatch_ready: e.target.checked })}
                  data-testid="tx-fleet-edit-dispatch-ready"
                />
              </Field>
              <Field label="Active for transport" inline>
                <input
                  type="checkbox"
                  checked={form.active_for_transport}
                  onChange={(e) => setForm({ ...form, active_for_transport: e.target.checked })}
                  data-testid="tx-fleet-edit-active"
                />
              </Field>
              <Field label="Safety hold" inline>
                <input
                  type="checkbox"
                  checked={form.safety_hold}
                  onChange={(e) => setForm({ ...form, safety_hold: e.target.checked })}
                  data-testid="tx-fleet-edit-safety-hold"
                />
              </Field>
            </div>
          </section>

          <section>
            <h3 className="text-sm font-semibold mb-2 text-slate-700">Transportation Notes</h3>
            <Field label="Operational tags (comma-separated)">
              <Input
                value={form.operational_tags}
                onChange={(e) => setForm({ ...form, operational_tags: e.target.value })}
                placeholder="e.g. heavy_haul, yard_a, night_shift"
                data-testid="tx-fleet-edit-tags"
              />
            </Field>
            <Field label="Notes">
              <textarea
                className="w-full border border-slate-200 rounded px-2 py-1.5 text-sm"
                rows={3}
                value={form.transportation_notes}
                onChange={(e) => setForm({ ...form, transportation_notes: e.target.value })}
                placeholder="Operational context for dispatch and Transportation leadership."
                data-testid="tx-fleet-edit-notes"
              />
            </Field>
          </section>

          {error && (
            <div className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2" data-testid="tx-fleet-edit-error">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
            <Button variant="outline" onClick={onClose} data-testid="tx-fleet-edit-cancel">Cancel</Button>
            <Button onClick={save} disabled={saving} data-testid="tx-fleet-edit-save">
              {saving ? "Saving…" : "Save Transportation Details"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children, inline }) {
  return (
    <div className={inline ? "flex items-center justify-between" : ""}>
      <label className="text-xs text-slate-500 block mb-1">{label}</label>
      {children}
    </div>
  );
}

// ───────────────────────── Carrier workspace ─────────────────────────
export function CarrierWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [restricted, setRestricted] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet(`/admin/transportation/carriers/${id}/workspace`);
      if (isTxRestricted(r)) { setRestricted(true); setData(null); return; }
      setRestricted(false);
      setData(r.data);
    } finally {
      setLoading(false);
    }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  if (loading && !data) return <div data-testid="carrier-ws-loading">Loading…</div>;
  if (restricted) return <TxOpsRestrictedData testid="tx-carrier-ws-restricted" />;
  if (!data) return null;
  const c = data.carrier || {};

  return (
    <div data-testid="carrier-workspace" className="space-y-4">
      <Button variant="ghost" size="sm" onClick={() => navigate("/admin/transportation/carriers")} data-testid="carrier-back">
        <ArrowLeft className="h-4 w-4 mr-1" />Back to carriers
      </Button>
      <PageHeader
        testid="carrier-workspace-header"
        title={c.legal_name}
        subtitle={`${c.carrier_type} · ${c.dba_name || ""}`.trim()}
        right={<Chip value={c.status} testid="carrier-ws-status-chip" />}
      />

      <Tabs defaultValue="overview" data-testid="carrier-ws-tabs">
        <TabsList>
          <TabsTrigger value="overview" data-testid="carrier-tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="drivers" data-testid="carrier-tab-drivers">Drivers</TabsTrigger>
          <TabsTrigger value="trucks" data-testid="carrier-tab-trucks">Trucks</TabsTrigger>
          <TabsTrigger value="packet" data-testid="carrier-tab-packet">Packet</TabsTrigger>
          <TabsTrigger value="documents" data-testid="carrier-tab-documents">Documents</TabsTrigger>
          <TabsTrigger value="rates" data-testid="carrier-tab-rates">Rates</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4" data-testid="carrier-pane-overview">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card title="Company">
              <Row label="Legal Name" value={c.legal_name} />
              <Row label="DBA" value={c.dba_name || "—"} />
              <Row label="Carrier Type" value={c.carrier_type} />
              <Row label="DOT" value={c.dot_number || "—"} />
              <Row label="MC" value={c.mc_number || "—"} />
            </Card>
            <Card title="Contacts">
              <Row label="Contact" value={c.contact_name || "—"} />
              <Row label="Phone" icon={Phone} value={c.contact_phone || "—"} />
              <Row label="Email" icon={Mail} value={c.contact_email || "—"} />
            </Card>
            <Card title="Eligibility">
              <Row label="State" value={<Chip value={data.eligibility?.state} />} />
              <div className="mt-2 text-xs text-slate-500">
                {(data.eligibility?.reasons || []).map((r, i) => (
                  <div key={i} data-testid={`carrier-ws-reason-${i}`}>• {r.label}</div>
                ))}
              </div>
            </Card>
            <Card title="Active Rate Schedule">
              {data.active_rate ? (
                <>
                  <Row label="Hourly Rate" value={`$${Number(data.active_rate.hourly_rate).toFixed(2)}`} icon={DollarSign} />
                  <Row label="Version" value={`v${data.active_rate.version}`} />
                  <Row label="Effective" value={(data.active_rate.effective_date || "").slice(0, 10)} />
                </>
              ) : <div className="text-sm text-slate-500">No active rate.</div>}
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="drivers" className="mt-4" data-testid="carrier-pane-drivers">
          {data.drivers?.length === 0 ? (
            <EmptyState title="No drivers assigned to this carrier yet" testid="carrier-no-drivers" />
          ) : (
            <div className="overflow-x-auto border border-slate-200 rounded">
              <table className="w-full text-sm" data-testid="carrier-drivers-table">
                <thead className="bg-slate-50 text-left">
                  <tr>
                    <th className="px-3 py-2">Name</th>
                    <th className="px-3 py-2">License</th>
                    <th className="px-3 py-2">CDL Class</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {data.drivers.map((p) => (
                    <tr key={p.id} className="border-t border-slate-100" data-testid={`carrier-driver-row-${p.id}`}>
                      <td className="px-3 py-2 font-medium">{p.first_name} {p.last_name}</td>
                      <td className="px-3 py-2 text-slate-600">{p.license_number || "—"}</td>
                      <td className="px-3 py-2 text-slate-600">{p.cdl_class || "—"}</td>
                      <td className="px-3 py-2"><Chip value={p.status} /></td>
                      <td className="px-3 py-2 text-right">
                        <Link to={`/admin/transportation/drivers/${p.id}`} className="text-blue-600 hover:underline text-xs">
                          Open <ExternalLink className="inline h-3 w-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-3"><ComingSoon feature="Quick-add driver to this carrier" testid="carrier-driver-add-coming-soon" /></div>
        </TabsContent>

        <TabsContent value="trucks" className="mt-4" data-testid="carrier-pane-trucks">
          {data.trucks?.length === 0 ? (
            <EmptyState title="No trucks assigned to this carrier yet" testid="carrier-no-trucks" />
          ) : (
            <div className="overflow-x-auto border border-slate-200 rounded">
              <table className="w-full text-sm" data-testid="carrier-trucks-table">
                <thead className="bg-slate-50 text-left">
                  <tr>
                    <th className="px-3 py-2">Truck #</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Ownership</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {data.trucks.map((t) => (
                    <tr key={t.id} className="border-t border-slate-100" data-testid={`carrier-truck-row-${t.id}`}>
                      <td className="px-3 py-2 font-medium">{t.truck_number}</td>
                      <td className="px-3 py-2 text-slate-600">{t.truck_type}</td>
                      <td className="px-3 py-2 text-slate-600">{t.ownership}</td>
                      <td className="px-3 py-2"><Chip value={t.status} /></td>
                      <td className="px-3 py-2 text-right">
                        <Link to={`/admin/transportation/trucks/${t.id}`} className="text-blue-600 hover:underline text-xs">
                          Open <ExternalLink className="inline h-3 w-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>

        <TabsContent value="packet" className="mt-4" data-testid="carrier-pane-packet">
          <PacketChecklist
            carrierId={id}
            packet={data.packet}
            onChanged={() => load()}
          />
        </TabsContent>

        <TabsContent value="documents" className="mt-4" data-testid="carrier-pane-documents">
          <DocumentDropzone
            kind="carrier"
            parentId={id}
            documentTypes={CARRIER_DOC_TYPES}
            onUploaded={() => load()}
            testid="carrier-doc-dropzone"
          />
          <div className="mt-4">
          {data.documents?.length === 0 ? (
            <EmptyState title="No carrier documents uploaded yet" hint="Drag a file above to upload — every file streams directly to MASCI R2 storage." testid="carrier-no-docs" />
          ) : (
            <div className="overflow-x-auto border border-slate-200 rounded">
              <table className="w-full text-sm" data-testid="carrier-docs-table">
                <thead className="bg-slate-50 text-left">
                  <tr>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Filename</th>
                    <th className="px-3 py-2">Uploaded</th>
                    <th className="px-3 py-2">Expires</th>
                    <th className="px-3 py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.documents.map((d) => (
                    <tr key={d.id} className="border-t border-slate-100" data-testid={`carrier-doc-row-${d.id}`}>
                      <td className="px-3 py-2 font-medium">{d.document_type}</td>
                      <td className="px-3 py-2 truncate max-w-xs">{d.original_filename || "—"}</td>
                      <td className="px-3 py-2 text-slate-600">{(d.uploaded_at || "").slice(0, 10)}</td>
                      <td className="px-3 py-2 text-slate-600">{d.expires_at ? d.expires_at.slice(0, 10) : "—"}</td>
                      <td className="px-3 py-2"><Chip value={d.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          </div>
        </TabsContent>

        <TabsContent value="rates" className="mt-4" data-testid="carrier-pane-rates">
          {data.active_rate ? (
            <Card title="Active Rate Schedule">
              <Row label="Hourly Rate" value={`$${Number(data.active_rate.hourly_rate).toFixed(2)}`} />
              <Row label="Version" value={`v${data.active_rate.version}`} />
              <Row label="Effective" value={(data.active_rate.effective_date || "").slice(0, 10)} />
            </Card>
          ) : <EmptyState title="No active rate schedule" testid="carrier-no-rate" />}
          <div className="mt-3">
            <Link to="/admin/transportation/rate-schedules" className="text-sm text-blue-600 hover:underline" data-testid="carrier-rate-history-link">
              View full rate history →
            </Link>
          </div>
        </TabsContent>
      </Tabs>

      <div className="text-xs text-slate-400 border-t border-slate-100 pt-3" data-testid="carrier-ws-disclaimer">
        {data.disclaimer}
      </div>

      <ComplianceTimeline entityType="carrier" entityId={id} testid="carrier-ws-timeline" />
    </div>
  );
}

// ───────────────────────── Driver workspace ─────────────────────────
export function DriverWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [restricted, setRestricted] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet(`/admin/transportation/persons/${id}/workspace`);
      if (isTxRestricted(r)) { setRestricted(true); setData(null); return; }
      setRestricted(false);
      setData(r.data);
    } finally {
      setLoading(false);
    }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  if (loading && !data) return <div data-testid="driver-ws-loading">Loading…</div>;
  if (restricted) return <TxOpsRestrictedData testid="tx-driver-ws-restricted" />;
  if (!data) return null;
  const d = data.driver || {};

  return (
    <div data-testid="driver-workspace" className="space-y-4">
      <Button variant="ghost" size="sm" onClick={() => navigate("/admin/transportation/drivers")} data-testid="driver-back">
        <ArrowLeft className="h-4 w-4 mr-1" />Back to drivers
      </Button>
      <PageHeader
        testid="driver-workspace-header"
        title={`${d.first_name} ${d.last_name}`}
        subtitle={`${d.kind} · ${d.license_number ? `license ${d.license_number}` : "no license on file"}`}
        right={<Chip value={d.status} testid="driver-ws-status-chip" />}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Identity">
          <Row label="Kind" value={d.kind} />
          {d.kind === "leased_driver" ? (
            <Row label="Carrier" value={data.carrier ? data.carrier.legal_name : "—"} />
          ) : (
            <Row label="Employee ID" value={d.employee_id || "—"} />
          )}
          <Row label="Phone" value={d.phone || "—"} icon={Phone} />
          <Row label="Email" value={d.email || "—"} icon={Mail} />
          <Row label="CDL Class" value={d.cdl_class || "—"} />
        </Card>
        <Card title="Eligibility">
          <Row label="State" value={<Chip value={data.eligibility?.state} />} />
          <div className="mt-2 text-xs text-slate-500">
            {(data.eligibility?.reasons || []).map((r, i) => (
              <div key={i} data-testid={`driver-ws-reason-${i}`}>• {r.label}</div>
            ))}
          </div>
        </Card>
      </div>

      {data.hr_linkage && (
        <Card title="HR linkage" testid="driver-hr-linkage">
          <Row label="Employee ID" value={data.hr_linkage.employee_id || data.hr_linkage.id} />
          <Row label="Name" value={data.hr_linkage.name || `${data.hr_linkage.first_name || ""} ${data.hr_linkage.last_name || ""}`.trim() || "—"} />
          <Row label="HR status" value={data.hr_linkage.lifecycle_status || data.hr_linkage.status || "—"} />
          <Row label="Role / Trade" value={[data.hr_linkage.role, data.hr_linkage.trade].filter(Boolean).join(" · ") || "—"} />
          <Row label="Department" value={data.hr_linkage.department || "—"} />
          <Row label="Driver status" value={data.hr_linkage.driver_status || "—"} />
          {data.hr_linkage.updated_at && (
            <Row label="HR updated" value={data.hr_linkage.updated_at.slice(0, 19).replace("T", " ")} />
          )}
        </Card>
      )}

      {data.hr_projection && (
        <Card title="HR lifecycle projection" testid="driver-hr-lifecycle-panel">
          <div className="text-xs text-slate-500 mb-2" data-testid="driver-hr-lifecycle-disclaimer">
            Read-only snapshot. HR is the source of truth — manage all
            lifecycle changes in HR.
          </div>
          <Row
            label="Transport projection"
            value={<Chip value={data.hr_projection.transport_state} testid="driver-hr-projection-chip" />}
          />
          <Row label="HR source status" value={data.hr_projection.source_status || "—"} />
          {(data.hr_projection.reason_labels || []).length > 0 && (
            <div className="mt-2 text-xs text-slate-600">
              <div className="font-medium text-slate-700 mb-1">Eligibility impact</div>
              {(data.hr_projection.reason_labels || []).map((label, i) => (
                <div key={i} data-testid={`driver-hr-reason-${i}`}>• {label}</div>
              ))}
            </div>
          )}
          {data.hr_projection.synced_at && (
            <div className="mt-2 text-xs text-slate-400" data-testid="driver-hr-synced-at">
              Last synced: {data.hr_projection.synced_at.slice(0, 19).replace("T", " ")} ({data.hr_projection.synced_trigger || "auto"})
            </div>
          )}
        </Card>
      )}

      <Card title="Documents" testid="driver-ws-docs">
        <DocumentDropzone
          kind="driver"
          parentId={id}
          documentTypes={DRIVER_DOC_TYPES}
          onUploaded={() => load()}
          testid="driver-doc-dropzone"
        />
        <div className="mt-4">
        {data.documents?.length === 0 ? (
          <EmptyState title="No driver documents uploaded yet" hint="Drag a file above (CDL, medical card, Clearinghouse query, etc.)." testid="driver-no-docs" />
        ) : (
          <table className="w-full text-sm" data-testid="driver-docs-table">
            <thead className="bg-slate-50 text-left">
              <tr>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Filename</th>
                <th className="px-3 py-2">Expires</th>
                <th className="px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.documents.map((doc) => (
                <tr key={doc.id} className="border-t border-slate-100" data-testid={`driver-doc-row-${doc.id}`}>
                  <td className="px-3 py-2 font-medium">{doc.document_type}</td>
                  <td className="px-3 py-2 truncate max-w-xs">{doc.original_filename || "—"}</td>
                  <td className="px-3 py-2 text-slate-600">{doc.expires_at ? doc.expires_at.slice(0, 10) : "—"}</td>
                  <td className="px-3 py-2"><Chip value={doc.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        </div>
      </Card>

      <ComplianceTimeline entityType="person" entityId={id} testid="driver-ws-timeline" />

      {/* TRACK 16.12 · Driver Operations Intelligence — read-only card
          with explainable score breakdown. Reuses adminHeaders. */}
      <DriverIntelligenceCard driverId={id} />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <ComingSoon feature="Orientation engine" testid="driver-orientation-coming-soon" />
        <ComingSoon feature="Incident history" testid="driver-incident-coming-soon" />
        <ComingSoon feature="Retraining + certificates" testid="driver-retraining-coming-soon" />
      </div>
    </div>
  );
}

// TRACK 16.12 · Driver intelligence card (read-only).
function DriverIntelligenceCard({ driverId }) {
  const [snap, setSnap] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    if (!driverId) return;
    txGet(`/admin/transportation/intelligence/drivers/${driverId}`)
      .then((r) => setSnap(r.data))
      .catch((e) => setErr(e.message));
  }, [driverId]);

  if (err || !snap) return null;
  const palette = {
    excellent: "bg-emerald-100 text-emerald-800 border-emerald-300",
    strong: "bg-emerald-50 text-emerald-800 border-emerald-200",
    fair: "bg-amber-100 text-amber-800 border-amber-300",
    watch: "bg-amber-200 text-amber-900 border-amber-400",
    critical: "bg-rose-100 text-rose-800 border-rose-300",
  };
  const overallCls = palette[snap.overall?.grade] || "bg-slate-100 text-slate-700 border-slate-300";

  return (
    <Card title="Operations Intelligence" testid="driver-ws-intelligence">
      <div className="flex items-center justify-between mb-3">
        <div className="text-[11px] uppercase tracking-wider text-slate-500">
          Overall · explainable score
        </div>
        <span
          data-testid="driver-ws-intelligence-overall-chip"
          className={`px-2 py-0.5 rounded-full border text-[11px] font-medium ${overallCls}`}
        >
          {Math.round(snap.overall?.score ?? 0)} · {snap.overall?.grade}
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
        {Object.entries(snap.indices || {}).map(([k, v]) => (
          <div key={k} className="rounded border border-slate-200 px-2 py-1.5"
               data-testid={`driver-ws-intelligence-index-${k}`}>
            <div className="text-[10px] uppercase tracking-wider text-slate-500">{k}</div>
            <div className="text-sm font-semibold text-slate-900">{Math.round(v.score)} · {v.grade}</div>
          </div>
        ))}
      </div>
      {(snap.explanations || []).length > 0 && (
        <div className="text-xs text-slate-700">
          <div className="font-medium text-slate-700 mb-1">Why</div>
          <ul className="space-y-1 max-h-48 overflow-y-auto">
            {snap.explanations.slice(0, 12).map((e, i) => (
              <li key={i} data-testid={`driver-ws-intelligence-expl-${i}`}
                  className={`flex items-start justify-between rounded px-2 py-1 ${
                    e.impact === "positive" ? "bg-emerald-50" :
                    e.impact === "watch" ? "bg-amber-50" :
                    e.impact === "negative" ? "bg-rose-50" : "bg-slate-50"}`}>
                <div className="flex-1">
                  <div className="text-slate-800">{e.label}</div>
                  {e.fix && (
                    <div className="text-[10px] text-slate-500 mt-0.5">Fix: {e.fix}</div>
                  )}
                </div>
                <span className="ml-2 font-mono text-[10px] text-slate-500">
                  Δ {e.delta > 0 ? "+" : ""}{e.delta}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="text-[10px] uppercase tracking-wide text-slate-400 mt-3">
        Schema {snap.schema_version} · Computed {(snap.computed_at || "").slice(0, 19).replace("T", " ")}
      </div>
    </Card>
  );
}

// ───────────────────────── Truck workspace ─────────────────────────
export function TruckWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [restricted, setRestricted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [wizardOpen, setWizardOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await txGet(`/admin/transportation/trucks/${id}/workspace`);
      if (isTxRestricted(r)) { setRestricted(true); setData(null); return; }
      setRestricted(false);
      setData(r.data);
    } finally {
      setLoading(false);
    }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  if (loading && !data) return <div data-testid="truck-ws-loading">Loading…</div>;
  if (restricted) return <TxOpsRestrictedData testid="tx-truck-ws-restricted" />;
  if (!data) return null;
  const t = data.truck || {};
  const latest = data.inspections?.[0];

  return (
    <div data-testid="truck-workspace" className="space-y-4">
      <Button variant="ghost" size="sm" onClick={() => navigate("/admin/transportation/trucks")} data-testid="truck-back">
        <ArrowLeft className="h-4 w-4 mr-1" />Back to trucks
      </Button>
      <PageHeader
        testid="truck-workspace-header"
        title={`Truck ${t.truck_number}`}
        subtitle={`${t.truck_type} · ${t.ownership}`}
        right={<Chip value={t.status} testid="truck-ws-status-chip" />}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Identity">
          <Row label="Truck #" value={t.truck_number} />
          <Row label="Type" value={t.truck_type} />
          <Row label="Ownership" value={t.ownership} />
          <Row label="VIN" value={t.vin || "—"} />
          <Row label="Plate" value={t.plate || "—"} />
          {t.ownership === "masci_owned"
            ? <Row label="Equipment ID" value={t.equipment_id || "—"} />
            : <Row label="Carrier" value={data.carrier ? data.carrier.legal_name : "—"} />}
        </Card>
        <Card title="Eligibility">
          <Row label="State" value={<Chip value={data.eligibility?.state} />} />
          <div className="mt-2 text-xs text-slate-500">
            {(data.eligibility?.reasons || []).map((r, i) => (
              <div key={i} data-testid={`truck-ws-reason-${i}`}>• {r.label}</div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="Latest Readiness Inspection" testid="truck-latest-insp-card">
        <div className="flex items-center justify-between mb-2">
          <div>
            {latest ? (
              <>
                <Chip value={latest.result} testid="truck-latest-insp-chip" />
                <div className="text-xs text-slate-500 mt-1">
                  {(latest.inspected_at || "").slice(0, 10)} · expires {latest.expires_at ? latest.expires_at.slice(0, 10) : "—"}
                </div>
                <div className="text-xs text-slate-500">Inspector: {latest.inspector_name || "—"}</div>
                <div className="text-xs text-slate-500">Trigger: {(latest.trigger || "—").replace(/_/g, " ")}</div>
              </>
            ) : (
              <div className="text-sm text-slate-500">A MASCI Hauler Truck Readiness Inspection is required before this truck can haul.</div>
            )}
          </div>
          <Button size="sm" onClick={() => setWizardOpen(true)} data-testid="truck-start-inspection-btn">
            <ClipboardCheck className="h-4 w-4 mr-1" />Start New Inspection
          </Button>
        </div>
      </Card>

      {data.inspections && data.inspections.length > 1 && (
        <Card title="Inspection History" testid="truck-insp-history-card">
          <table className="w-full text-sm" data-testid="truck-insp-history-table">
            <thead className="bg-slate-50 text-left">
              <tr>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Trigger</th>
                <th className="px-3 py-2">Inspector</th>
                <th className="px-3 py-2">Result</th>
                <th className="px-3 py-2">Expires</th>
              </tr>
            </thead>
            <tbody>
              {data.inspections.slice(1).map((i) => (
                <tr key={i.id} className="border-t border-slate-100" data-testid={`truck-insp-row-${i.id}`}>
                  <td className="px-3 py-2">{(i.inspected_at || "").slice(0, 10)}</td>
                  <td className="px-3 py-2 text-slate-600">{(i.trigger || "—").replace(/_/g, " ")}</td>
                  <td className="px-3 py-2">{i.inspector_name || "—"}</td>
                  <td className="px-3 py-2"><Chip value={i.result} /></td>
                  <td className="px-3 py-2 text-slate-600">{i.expires_at ? i.expires_at.slice(0, 10) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <div className="text-xs text-slate-400 border-t border-slate-100 pt-3" data-testid="truck-ws-disclaimer">
        {data.disclaimer}
      </div>

      <ComplianceTimeline entityType="truck" entityId={id} testid="truck-ws-timeline" />

      <InspectionWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        truckId={id}
        onComplete={() => load()}
        testid="truck-inspection-wizard"
      />
    </div>
  );
}

// ───────────────────────── small primitives ─────────────────────────
function Card({ title, children, testid }) {
  return (
    <div className="border border-slate-200 rounded-md bg-white p-4" data-testid={testid}>
      <div className="text-xs uppercase tracking-wide text-slate-500 font-medium mb-2">{title}</div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function Row({ label, value, icon: Icon }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-500 inline-flex items-center gap-1">
        {Icon && <Icon className="h-3.5 w-3.5" />}
        {label}
      </span>
      <span className="text-slate-900 font-medium text-right">{value ?? "—"}</span>
    </div>
  );
}
