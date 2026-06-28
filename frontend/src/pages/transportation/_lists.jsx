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
  ShieldCheck, Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Chip, PageHeader, ComingSoon, EmptyState, txGet, isTxRestricted,
} from "./_shared";
import {
  DocumentDropzone, InspectionWizard, ComplianceTimeline, PacketChecklist,
} from "./_widgets";
import { TxOpsRestrictedData } from "@/components/transportation/TxOpsRestricted";

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
export function CarriersList() {
  const [rows, setRows] = useState([]);
  const [restricted, setRestricted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
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
        right={<Button variant="outline" onClick={load} data-testid="carriers-list-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>}
      />
      {restricted ? <TxOpsRestrictedData testid="tx-carriers-list-restricted" /> : (
        <>
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
                    <td className="px-3 py-2 text-right">
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
    </div>
  );
}

// ───────────────────────── Drivers list ─────────────────────────
export function DriversList() {
  const [rows, setRows] = useState([]);
  const [restricted, setRestricted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
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
      <PageHeader title="Drivers" subtitle="MASCI employees and leased drivers." right={
        <Button variant="outline" onClick={load} data-testid="drivers-list-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
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
    </div>
  );
}

// ───────────────────────── Trucks list ─────────────────────────
export function TrucksList() {
  const [rows, setRows] = useState([]);
  const [restricted, setRestricted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const { status } = useStateFilter();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (status) params.status = status;
      if (q) params.q = q;
      const r = await txGet("/admin/transportation/trucks", params);
      if (isTxRestricted(r)) { setRestricted(true); setRows([]); return; }
      setRestricted(false);
      setRows(r.data.items || []);
    } finally {
      setLoading(false);
    }
  }, [q, status]);
  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid="tx-trucks-list" className="space-y-4">
      <PageHeader title="Trucks" subtitle="MASCI-owned and leased trucks." right={
        <Button variant="outline" onClick={load} data-testid="trucks-list-refresh"><RefreshCw className="h-4 w-4 mr-1" />Refresh</Button>
      } />
      {restricted ? <TxOpsRestrictedData testid="tx-trucks-list-restricted" /> : (
        <>
      <div className="flex items-center gap-2">
        <div className="relative">
          <Search className="h-4 w-4 absolute left-2 top-2.5 text-slate-400" />
          <Input
            data-testid="trucks-search"
            placeholder="Search truck #, VIN, plate…"
            className="pl-8 w-72"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
          />
        </div>
      </div>
      {loading ? <div data-testid="trucks-list-loading">Loading…</div> : (
        rows.length === 0 ? (
          <EmptyState title="No trucks match" testid="trucks-list-empty" />
        ) : (
          <div className="overflow-x-auto border border-slate-200 rounded">
            <table className="w-full text-sm" data-testid="trucks-list-table">
              <thead className="bg-slate-50 text-left">
                <tr>
                  <th className="px-3 py-2">Truck #</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Ownership</th>
                  <th className="px-3 py-2">Reference</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t) => (
                  <tr key={t.id} className="border-t border-slate-100" data-testid={`trucks-list-row-${t.id}`}>
                    <td className="px-3 py-2 font-medium">{t.truck_number}</td>
                    <td className="px-3 py-2 text-slate-600">{t.truck_type}</td>
                    <td className="px-3 py-2 text-slate-600">{t.ownership}</td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {t.ownership === "masci_owned" ? (t.equipment_id || "—") : (t.carrier_id || "—")}
                    </td>
                    <td className="px-3 py-2"><Chip value={t.status} /></td>
                    <td className="px-3 py-2 text-right">
                      <Link to={`/admin/transportation/trucks/${t.id}`} className="text-blue-600 hover:underline text-xs" data-testid={`truck-open-${t.id}`}>
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
