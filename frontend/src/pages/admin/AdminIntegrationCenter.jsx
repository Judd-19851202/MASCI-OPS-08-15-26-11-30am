// AdminIntegrationCenter — central command for Motive + MaintainX
// integration framework. Tabs: Overview · Motive · MaintainX · Asset
// Mapping · Employee/Driver Mapping · Sync Logs · Error Logs · CSV
// Import/Export.
//
// IMPORTANT: This is the ONLY place in the app that talks directly to
// the integration management endpoints. Every portal-facing view reads
// from /api/integrations/health or /api/integrations/{motive,maintainx}/*
// — never the /admin/integrations/* surface.
import React, { useEffect, useState } from "react";
import {
  Cable, Plug, Truck, Users, FileText, AlertOctagon, FileUp, FileDown,
  Loader2, RefreshCcw, Save, X, Pencil, Trash2, AlertTriangle,
  CheckCircle2, ExternalLink, Eye, EyeOff, Wand2, ChevronRight, Undo2,
  MapPin, Zap, Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Tabs, TabsList, TabsTrigger, TabsContent,
} from "@/components/ui/tabs";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import AdminShell from "@/components/AdminShell";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";
import MaintainxP0Tab from "@/components/admin/MaintainxP0Tab";
import MaintainxDefectCoverageSection from "@/components/admin/MaintainxDefectCoverageSection";

const STATUS_COLOR = {
  Connected:               "bg-emerald-100 text-emerald-900 border-emerald-300",
  "Ready for Credentials": "bg-amber-100 text-amber-900 border-amber-300",
  Syncing:                 "bg-blue-100 text-blue-900 border-blue-300",
  Error:                   "bg-red-100 text-red-900 border-red-300",
  Disabled:                "bg-slate-200 text-slate-700 border-slate-300",
  "Not Connected":         "bg-slate-100 text-slate-600 border-slate-200",
};
const inputCls = "h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-slate-700";

export default function AdminIntegrationCenter() {
  return (
    <AdminShell title="Integration Center" kicker="ADMIN · INTEGRATION CENTER">
      <div className="bg-white border border-slate-200 rounded-md p-5 mb-5">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-900 text-white shrink-0">
            <Cable className="w-6 h-6" />
          </div>
          <div>
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-700 font-bold">
              Central Integration Layer
            </span>
            <h2 className="font-display text-2xl font-black mt-1 leading-tight">
              Motive · MaintainX · Integration Framework
            </h2>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              All third-party logic flows through this single layer — Safety, Shop, HR, and Admin portals
              read from it, never directly from Motive or MaintainX. Set the toggles + paste credentials here
              once the Motive / MaintainX accounts are provisioned.
            </p>
          </div>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="flex-wrap h-auto gap-1">
          <TabsTrigger value="overview" data-testid="ic-tab-overview"><Plug className="w-3.5 h-3.5 mr-1" /> Overview</TabsTrigger>
          <TabsTrigger value="motive" data-testid="ic-tab-motive">Motive</TabsTrigger>
          <TabsTrigger value="maintainx" data-testid="ic-tab-maintainx">MaintainX</TabsTrigger>
          <TabsTrigger value="maintainx-p0" data-testid="ic-tab-maintainx-p0">MaintainX · Read-First</TabsTrigger>
          <TabsTrigger value="assets" data-testid="ic-tab-assets"><Truck className="w-3.5 h-3.5 mr-1" /> Asset Mapping</TabsTrigger>
          <TabsTrigger value="employees" data-testid="ic-tab-employees"><Users className="w-3.5 h-3.5 mr-1" /> Employee Mapping</TabsTrigger>
          <TabsTrigger value="sync" data-testid="ic-tab-sync"><FileText className="w-3.5 h-3.5 mr-1" /> Sync Logs</TabsTrigger>
          <TabsTrigger value="errors" data-testid="ic-tab-errors"><AlertOctagon className="w-3.5 h-3.5 mr-1" /> Error Logs</TabsTrigger>
          <TabsTrigger value="csv" data-testid="ic-tab-csv"><FileUp className="w-3.5 h-3.5 mr-1" /> CSV Import / Export</TabsTrigger>
          <TabsTrigger value="wizard" data-testid="ic-tab-wizard"><Wand2 className="w-3.5 h-3.5 mr-1" /> Mappings Wizard</TabsTrigger>
          <TabsTrigger value="geofences" data-testid="ic-tab-geofences"><MapPin className="w-3.5 h-3.5 mr-1" /> Geofences</TabsTrigger>
        </TabsList>

        <TabsContent value="overview"><OverviewTab /></TabsContent>
        <TabsContent value="motive"><ProviderTab provider="motive" /></TabsContent>
        <TabsContent value="maintainx"><ProviderTab provider="maintainx" /></TabsContent>
        <TabsContent value="maintainx-p0">
          <MaintainxP0Tab />
          <div className="mt-4">
            <MaintainxDefectCoverageSection />
          </div>
        </TabsContent>
        <TabsContent value="assets"><AssetMappingTab /></TabsContent>
        <TabsContent value="employees"><EmployeeMappingTab /></TabsContent>
        <TabsContent value="sync"><SyncLogsTab /></TabsContent>
        <TabsContent value="errors"><ErrorLogsTab /></TabsContent>
        <TabsContent value="csv"><CsvTab /></TabsContent>
        <TabsContent value="wizard"><WizardTab /></TabsContent>
        <TabsContent value="geofences"><GeofencesTab /></TabsContent>
      </Tabs>
    </AdminShell>
  );
}

/* ──────────────────────────────────────────────────────────────────
   Overview tab — two big status cards
   ────────────────────────────────────────────────────────────────── */
function OverviewTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true);
    try { setData((await api.get("/admin/integrations/overview")).data); }
    catch (e) { toast.error(operationalError(e, "Could not load overview")); }
    finally { setLoading(false); }
  };
  useEffect(() => { refresh(); }, []);

  if (loading || !data) return <div className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
      {data.providers.map((p) => <ProviderStatusCard key={p.provider} p={p} onRefresh={refresh} />)}
    </div>
  );
}

function ProviderStatusCard({ p, onRefresh }) {
  const [testing, setTesting] = useState(false);
  const cls = STATUS_COLOR[p.status] || STATUS_COLOR["Not Connected"];
  const test = async () => {
    setTesting(true);
    try {
      const r = await api.post(`/admin/integrations/${p.provider}/test`);
      if (r.data?.ok) toast.success(r.data?.message || "Connection OK");
      else toast.warning(r.data?.message || r.data?.status || "Test returned no-op (stub)");
    } catch (e) { toast.error(operationalError(e, "Test failed")); }
    finally { setTesting(false); onRefresh(); }
  };
  return (
    <div className="bg-white border border-slate-200 rounded-md p-5" data-testid={`ic-status-${p.provider}`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
            {p.provider === "motive" ? "Telematics · Driver Safety" : "Work Orders · PMs"}
          </div>
          <h3 className="font-display text-2xl font-black text-slate-900 capitalize">{p.provider}</h3>
        </div>
        <span className={`px-2 py-1 rounded border text-xs font-mono uppercase tracking-[0.15em] font-bold ${cls}`}>{p.status}</span>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm mb-3">
        <Stat label="Records mapped" value={p.records_mapped} />
        <Stat label="Last sync" value={p.last_sync_at ? p.last_sync_at.slice(0, 16).replace("T", " ") : "—"} />
        <Stat label="Last success" value={p.last_successful_sync_at ? p.last_successful_sync_at.slice(0, 16).replace("T", " ") : "—"} />
        <Stat label="Last failure" value={p.last_failed_sync_at ? p.last_failed_sync_at.slice(0, 16).replace("T", " ") : "—"} />
      </div>
      <div className="flex items-center gap-2 text-xs text-slate-600 mb-3">
        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-[0.18em] font-bold ${p.api_key_present ? "bg-emerald-100 text-emerald-900" : "bg-slate-100 text-slate-600"}`}>
          API Key {p.api_key_present ? "Set" : "Not Set"}
        </span>
        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-[0.18em] font-bold ${p.webhook_secret_present ? "bg-emerald-100 text-emerald-900" : "bg-slate-100 text-slate-600"}`}>
          Webhook Secret {p.webhook_secret_present ? "Set" : "Not Set"}
        </span>
        {p.demo_mode && <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 text-[10px] font-mono uppercase tracking-[0.18em] font-bold">Demo Mode</span>}
      </div>
      <div className="flex gap-2">
        <Button size="sm" onClick={test} disabled={testing} className="bg-slate-900 hover:bg-slate-800 text-white h-9" data-testid={`ic-status-test-${p.provider}`}>
          {testing ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <CheckCircle2 className="w-3.5 h-3.5 mr-1" />} Test connection
        </Button>
        <Button size="sm" variant="outline" disabled={!p.enabled} className="h-9" title={p.enabled ? "Awaiting API Credentials" : "Disabled"} data-testid={`ic-status-sync-${p.provider}`}>
          <RefreshCcw className="w-3.5 h-3.5 mr-1" /> Sync now
        </Button>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-slate-500">{label}</div>
      <div className="text-slate-900 font-bold text-sm font-mono">{value}</div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────
   Provider settings tab (Motive / MaintainX)
   ────────────────────────────────────────────────────────────────── */
function ProviderTab({ provider }) {
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [showSecrets, setShowSecrets] = useState(false);
  const [notes, setNotes] = useState("");

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get(`/admin/integrations/${provider}`);
      setDoc(r.data); setNotes(r.data.notes || "");
    } catch { toast.error("Could not load settings"); }
    finally { setLoading(false); }
  };
  useEffect(() => { refresh(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [provider]);

  const save = async (patch) => {
    setSaving(true);
    try {
      const r = await api.patch(`/admin/integrations/${provider}`, patch);
      setDoc(r.data); setApiKey(""); setWebhookSecret("");
      toast.success("Saved");
    } catch (e) { toast.error(operationalError(e, "Save failed")); }
    finally { setSaving(false); }
  };

  if (loading || !doc) return <div className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>;

  const webhookFullUrl = `${window.location.origin}${doc.webhook_url_path}`;

  return (
    <div className="space-y-4">
      <div className="bg-white border border-slate-200 rounded-md p-5">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4">
          <ToggleBlock
            label="Integration enabled" sub="When off, no syncs run and webhooks reject."
            checked={doc.enabled} onChange={(v) => save({ enabled: v })}
            testId={`ic-${provider}-enabled`}
          />
          <ToggleBlock
            label="Demo mode" sub="Show sample records to portals for screenshots."
            checked={doc.demo_mode} onChange={(v) => save({ demo_mode: v })}
            testId={`ic-${provider}-demo`}
          />
          <ToggleBlock
            label="Status" sub={doc.status} checked={doc.status === "Connected"} readOnly
          />
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-display text-lg font-black">Credentials</h3>
          <Button size="sm" variant="outline" onClick={() => setShowSecrets((s) => !s)} className="h-8">
            {showSecrets ? <><EyeOff className="w-3.5 h-3.5 mr-1" /> Hide</> : <><Eye className="w-3.5 h-3.5 mr-1" /> Show input</>}
          </Button>
        </div>
        <p className="text-sm text-slate-600 mb-4">
          Secrets are stored server-side and never returned to this UI after save — only a masked indicator
          is shown so you can confirm the right value is in place.
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
          <SecretField
            label="API Key"
            present={doc.api_key_present}
            masked={doc.api_key_masked}
            value={apiKey}
            onChange={setApiKey}
            show={showSecrets}
            onSave={() => save({ api_key: apiKey })}
            saving={saving}
            testId={`ic-${provider}-api-key`}
          />
          <SecretField
            label="Webhook Secret"
            present={doc.webhook_secret_present}
            masked={doc.webhook_secret_masked}
            value={webhookSecret}
            onChange={setWebhookSecret}
            show={showSecrets}
            onSave={() => save({ webhook_secret: webhookSecret })}
            saving={saving}
            testId={`ic-${provider}-webhook-secret`}
          />
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-5">
        <h3 className="font-display text-lg font-black mb-2">Webhook endpoint</h3>
        <p className="text-sm text-slate-600 mb-2">
          Configure {provider === "motive" ? "Motive" : "MaintainX"} to deliver events to this URL.
          {!doc.webhook_secret_present && <span className="text-amber-700 font-bold"> Configure the webhook secret first — deliveries without a valid signature are rejected.</span>}
        </p>
        <div className="font-mono text-xs bg-slate-50 border-2 border-slate-200 rounded p-3 select-all break-all" data-testid={`ic-${provider}-webhook-url`}>
          {webhookFullUrl}
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-5">
        <h3 className="font-display text-lg font-black mb-2">Internal notes</h3>
        <Textarea
          value={notes} onChange={(e) => setNotes(e.target.value)}
          rows={3} className="text-sm border-2 border-slate-300 mb-2"
          placeholder="Free-form notes for the next admin who picks this up…"
          data-testid={`ic-${provider}-notes`}
        />
        <Button size="sm" onClick={() => save({ notes })} disabled={saving} className="bg-slate-900 hover:bg-slate-800 text-white h-9">
          <Save className="w-3.5 h-3.5 mr-1" /> Save notes
        </Button>
      </div>
    </div>
  );
}

function ToggleBlock({ label, sub, checked, onChange, readOnly = false, testId }) {
  return (
    <div className="border border-slate-200 rounded-md p-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{label}</div>
          <div className="text-xs text-slate-500 mt-0.5">{sub}</div>
        </div>
        {readOnly ? (
          <span className={`px-2 py-0.5 rounded border text-[10px] font-mono uppercase font-bold ${checked ? STATUS_COLOR.Connected : STATUS_COLOR["Not Connected"]}`}>
            {checked ? "ON" : "OFF"}
          </span>
        ) : (
          <Switch checked={!!checked} onCheckedChange={onChange} data-testid={testId} />
        )}
      </div>
    </div>
  );
}

function SecretField({ label, present, masked, value, onChange, show, onSave, saving, testId }) {
  return (
    <div>
      <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{label}</Label>
      <div className="text-xs text-slate-500 mt-0.5">
        {present ? <>Current: <span className="font-mono">{masked}</span></> : "Not set"}
      </div>
      <div className="flex gap-1 mt-2">
        <Input
          type={show ? "text" : "password"}
          value={value} onChange={(e) => onChange(e.target.value)}
          placeholder={`Paste new ${label.toLowerCase()}`}
          className={`${inputCls} flex-1`}
          data-testid={testId}
        />
        <Button size="sm" onClick={onSave} disabled={saving || !value} className="bg-slate-900 hover:bg-slate-800 text-white h-10" data-testid={`${testId}-save`}>
          {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
        </Button>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────
   Asset mapping tab
   ────────────────────────────────────────────────────────────────── */
function AssetMappingTab() {
  return <MappingTab kind="asset" />;
}
function EmployeeMappingTab() {
  return <MappingTab kind="employee" />;
}

function MappingTab({ kind }) {
  const isAsset = kind === "asset";
  const listUrl = isAsset ? "/admin/integrations/asset-mappings" : "/admin/integrations/employee-mappings";
  const unmappedUrl = isAsset
    ? "/admin/integrations/asset-mappings/unmapped"
    : "/admin/integrations/employee-mappings/unmapped";
  const masciIdField = isAsset ? "masci_equipment_id" : "masci_employee_id";

  const [mappings, setMappings] = useState([]);
  const [unmapped, setUnmapped] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dlg, setDlg] = useState({ open: false, mode: "create", id: null, form: {} });
  const [saving, setSaving] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const [m, u] = await Promise.all([api.get(listUrl), api.get(unmappedUrl)]);
      setMappings(Array.isArray(m.data) ? m.data : []);
      setUnmapped(Array.isArray(u.data) ? u.data : []);
    } catch (e) { toast.error(operationalError(e, "Could not load")); }
    finally { setLoading(false); }
  };
  useEffect(() => { refresh(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [kind]);

  const openCreate = () => setDlg({ open: true, mode: "create", id: null, form: { [masciIdField]: "" } });
  const openEdit = (m) => {
    const form = isAsset ? {
      motive_vehicle_id: m.motive?.vehicle_id || "",
      motive_asset_id: m.motive?.asset_id || "",
      motive_driver_id: m.motive?.driver_id || "",
      motive_device_id: m.motive?.device_id || "",
      maintainx_asset_id: m.maintainx?.asset_id || "",
      maintainx_location_id: m.maintainx?.location_id || "",
      mapping_confidence: m.mapping_confidence || "medium",
      mapping_notes: m.mapping_notes || "",
    } : {
      motive_driver_id: m.motive?.driver_id || "",
      motive_driver_name: m.motive?.driver_name || "",
      motive_email: m.motive?.email || "",
      maintainx_user_id: m.maintainx?.user_id || "",
      maintainx_name: m.maintainx?.name || "",
      maintainx_email: m.maintainx?.email || "",
      maintainx_role: m.maintainx?.role || "",
      mapping_notes: m.mapping_notes || "",
    };
    setDlg({ open: true, mode: "edit", id: m.id, form });
  };
  const close = () => setDlg((d) => ({ ...d, open: false }));

  const save = async () => {
    setSaving(true);
    try {
      if (dlg.mode === "create") {
        await api.post(listUrl, dlg.form);
        toast.success("Mapping created");
      } else {
        await api.patch(`${listUrl}/${dlg.id}`, dlg.form);
        toast.success("Mapping updated");
      }
      close(); refresh();
    } catch (e) { toast.error(operationalError(e, "Save failed")); }
    finally { setSaving(false); }
  };

  const remove = async (m) => {
    if (!window.confirm(`Delete this mapping?`)) return;
    try {
      await api.delete(`${listUrl}/${m.id}`);
      toast.success("Removed"); refresh();
    } catch (e) { toast.error(operationalError(e, "Delete failed")); }
  };

  if (loading) return <div className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>;

  return (
    <div className="space-y-4">
      <div className="bg-white border border-slate-200 rounded-md p-4">
        <div className="flex items-center justify-between gap-3 mb-2">
          <div>
            <h3 className="font-display text-lg font-black">
              {isAsset ? "Master Asset Mapping" : "Master Employee / Driver Mapping"}
            </h3>
            <p className="text-sm text-slate-600">
              {isAsset
                ? "Links db.equipment_master records to Motive vehicles + MaintainX assets. No duplicate records."
                : "Links db.employees records to Motive drivers + MaintainX users."}
              {" · "}
              <strong>{mappings.length}</strong> mapped · <strong>{unmapped.length}</strong> awaiting mapping
            </p>
          </div>
          <Button onClick={openCreate} className="bg-slate-900 hover:bg-slate-800 text-white h-10" data-testid={`ic-${kind}-new`}>
            + Add Mapping
          </Button>
          <AutoLinkButton kind={kind} onDone={refresh} />
        </div>
      </div>

      <div className="overflow-x-auto bg-white border border-slate-200 rounded-md">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
            <tr>
              <th className="text-left px-3 py-2">{isAsset ? "Unit / Equipment" : "Employee"}</th>
              <th className="text-left px-3 py-2">Motive {isAsset ? "Vehicle" : "Driver"}</th>
              <th className="text-left px-3 py-2">MaintainX {isAsset ? "Asset" : "User"}</th>
              <th className="text-center px-3 py-2">Status</th>
              <th className="text-right px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {mappings.length === 0 ? (
              <tr><td colSpan={5} className="text-center text-slate-500 py-8">No mappings yet. Add one above or use CSV Import.</td></tr>
            ) : mappings.map((m) => (
              <tr key={m.id} className="border-t border-slate-100" data-testid={`ic-${kind}-row-${m.id}`}>
                <td className="px-3 py-2">
                  {isAsset ? (
                    <>
                      <div className="font-bold">{m.masci_unit_number || "—"}</div>
                      <div className="text-xs text-slate-500">{m.masci_equipment_name}</div>
                    </>
                  ) : (
                    <>
                      <div className="font-bold">{m.masci_employee_name}</div>
                      <div className="text-xs text-slate-500">{m.masci_employee_trade}{m.masci_employee_role ? ` · ${m.masci_employee_role}` : ""}</div>
                    </>
                  )}
                </td>
                <td className="px-3 py-2 font-mono text-xs">
                  {isAsset
                    ? (m.motive?.vehicle_id || m.motive?.asset_id || <span className="text-slate-400">—</span>)
                    : (m.motive?.driver_name || m.motive?.driver_id || <span className="text-slate-400">—</span>)}
                </td>
                <td className="px-3 py-2 font-mono text-xs">
                  {isAsset
                    ? (m.maintainx?.asset_id || <span className="text-slate-400">—</span>)
                    : (m.maintainx?.name || m.maintainx?.user_id || <span className="text-slate-400">—</span>)}
                </td>
                <td className="px-3 py-2 text-center text-xs font-mono">
                  <div className="flex flex-col gap-0.5 items-center">
                    <span className={`px-1.5 py-0.5 rounded ${m.motive?.mapping_status === "Mapped" ? "bg-emerald-100 text-emerald-900" : "bg-slate-100 text-slate-500"}`}>M: {m.motive?.mapping_status || "—"}</span>
                    <span className={`px-1.5 py-0.5 rounded ${m.maintainx?.mapping_status === "Mapped" ? "bg-emerald-100 text-emerald-900" : "bg-slate-100 text-slate-500"}`}>X: {m.maintainx?.mapping_status || "—"}</span>
                  </div>
                </td>
                <td className="px-3 py-2 text-right">
                  <div className="inline-flex gap-1">
                    <Button size="sm" variant="outline" onClick={() => openEdit(m)} className="h-8" data-testid={`ic-${kind}-edit-${m.id}`}><Pencil className="w-3.5 h-3.5" /></Button>
                    <Button size="sm" variant="outline" onClick={() => remove(m)} className="h-8 border-red-300 text-red-700" data-testid={`ic-${kind}-delete-${m.id}`}><Trash2 className="w-3.5 h-3.5" /></Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {unmapped.length > 0 && (
        <div className="bg-amber-50 border-2 border-amber-200 rounded-md p-4">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-4 h-4 text-amber-700" />
            <h4 className="font-display font-black text-amber-900">{unmapped.length} {isAsset ? "equipment" : "employee"} record{unmapped.length === 1 ? "" : "s"} awaiting mapping</h4>
          </div>
          <p className="text-sm text-amber-800 mb-2">Either map them one-by-one above or paste a CSV under the <strong>CSV Import / Export</strong> tab.</p>
        </div>
      )}

      <Dialog open={dlg.open} onOpenChange={(o) => !o && close()}>
        <DialogContent className="sm:max-w-xl max-h-[92vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{dlg.mode === "create" ? "New mapping" : "Edit mapping"}</DialogTitle>
            <DialogDescription>
              {isAsset
                ? "Link a MASCI equipment record to Motive + MaintainX IDs. One mapping per equipment."
                : "Link a MASCI employee to Motive driver + MaintainX user. One mapping per employee."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 pt-2">
            {dlg.mode === "create" && (
              <div>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">
                  {isAsset ? "Equipment" : "Employee"} *
                </Label>
                <Select
                  value={dlg.form[masciIdField] || ""}
                  onValueChange={(v) => setDlg((d) => ({ ...d, form: { ...d.form, [masciIdField]: v } }))}
                >
                  <SelectTrigger className={`${inputCls} mt-1`} data-testid={`ic-${kind}-form-master`}><SelectValue placeholder="Pick from unmapped list" /></SelectTrigger>
                  <SelectContent className="max-h-80">
                    {unmapped.map((u) => (
                      <SelectItem key={u.id} value={u.id}>
                        {isAsset ? (u.unit_number || u.name || u.id) : u.name}
                        {isAsset && u.name && u.unit_number ? ` · ${u.name}` : ""}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {(isAsset ? [
              ["motive_vehicle_id", "Motive Vehicle ID"],
              ["motive_asset_id", "Motive Asset ID"],
              ["motive_driver_id", "Motive Driver ID (optional)"],
              ["motive_device_id", "Motive Device ID"],
              ["maintainx_asset_id", "MaintainX Asset ID"],
              ["maintainx_location_id", "MaintainX Location ID"],
            ] : [
              ["motive_driver_id", "Motive Driver ID"],
              ["motive_driver_name", "Motive Driver Name"],
              ["motive_email", "Motive Email"],
              ["maintainx_user_id", "MaintainX User ID"],
              ["maintainx_name", "MaintainX Name"],
              ["maintainx_email", "MaintainX Email"],
              ["maintainx_role", "MaintainX Role"],
            ]).map(([key, label]) => (
              <div key={key}>
                <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{label}</Label>
                <Input value={dlg.form[key] || ""} onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, [key]: e.target.value } }))} className={`${inputCls} mt-1`} data-testid={`ic-${kind}-form-${key}`} />
              </div>
            ))}
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Mapping notes</Label>
              <Textarea value={dlg.form.mapping_notes || ""} onChange={(e) => setDlg((d) => ({ ...d, form: { ...d.form, mapping_notes: e.target.value } }))} rows={2} className="text-sm border-2 border-slate-300 mt-1" />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={close} disabled={saving}><X className="w-4 h-4 mr-1" /> Cancel</Button>
            <Button onClick={save} disabled={saving} className="bg-slate-900 hover:bg-slate-800 text-white" data-testid={`ic-${kind}-form-save`}>
              {saving ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Save className="w-4 h-4 mr-1" />} Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────
   Sync logs / Error logs
   ────────────────────────────────────────────────────────────────── */
function SyncLogsTab() {
  return <LogTable url="/admin/integrations/sync-logs" kind="sync" />;
}
function ErrorLogsTab() {
  return <LogTable url="/admin/integrations/error-logs" kind="error" />;
}

function LogTable({ url, kind }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  const refresh = async () => {
    setLoading(true);
    try {
      const params = filter ? `?integration=${filter}` : "";
      const r = await api.get(`${url}${params}`);
      setRows(Array.isArray(r.data) ? r.data : []);
    } catch (e) { toast.error("Could not load logs"); }
    finally { setLoading(false); }
  };
  useEffect(() => { refresh(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [filter, url]);

  return (
    <div className="space-y-3" data-testid={`ic-${kind}-log-table`}>
      <div className="flex items-center gap-2">
        <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Filter</Label>
        <Select value={filter || "all"} onValueChange={(v) => setFilter(v === "all" ? "" : v)}>
          <SelectTrigger className={`${inputCls} max-w-xs`} data-testid={`ic-${kind}-filter`}><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All integrations</SelectItem>
            <SelectItem value="motive">Motive</SelectItem>
            <SelectItem value="maintainx">MaintainX</SelectItem>
          </SelectContent>
        </Select>
        <Button size="sm" variant="outline" onClick={refresh} disabled={loading} className="h-9 ml-auto">
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
        </Button>
      </div>
      <div className="overflow-x-auto bg-white border border-slate-200 rounded-md">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
            <tr>
              <th className="text-left px-3 py-2">When</th>
              <th className="text-left px-3 py-2">Integration</th>
              {kind === "sync" ? (
                <>
                  <th className="text-left px-3 py-2">Type</th>
                  <th className="text-left px-3 py-2">Status</th>
                  <th className="text-right px-3 py-2">Records</th>
                </>
              ) : (
                <>
                  <th className="text-left px-3 py-2">Kind</th>
                  <th className="text-left px-3 py-2">Message</th>
                  <th className="text-center px-3 py-2">Resolved</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td colSpan={5} className="text-center text-slate-500 py-8">No {kind} log entries yet.</td></tr>
            ) : rows.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                <td className="px-3 py-2 font-mono text-xs">{(r.started_at || r.occurred_at || "").slice(0, 16).replace("T", " ")}</td>
                <td className="px-3 py-2 capitalize">{r.integration}</td>
                {kind === "sync" ? (
                  <>
                    <td className="px-3 py-2 font-mono text-xs">{r.sync_type}</td>
                    <td className="px-3 py-2">
                      <span className={`px-1.5 py-0.5 rounded border text-[10px] font-mono uppercase font-bold ${STATUS_COLOR[r.status] || STATUS_COLOR["Not Connected"]}`}>{r.status}</span>
                    </td>
                    <td className="px-3 py-2 text-right text-xs font-mono">
                      +{r.records_created} ~{r.records_updated} ↓{r.records_skipped} ✗{r.records_failed}
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-3 py-2 font-mono text-xs">{r.kind}</td>
                    <td className="px-3 py-2 text-xs text-slate-700 truncate max-w-md" title={r.message}>{r.message}</td>
                    <td className="px-3 py-2 text-center">
                      {r.resolved ? <CheckCircle2 className="w-4 h-4 text-emerald-600 inline" /> : (
                        <Button size="sm" variant="outline" onClick={async () => { await api.post(`/admin/integrations/error-logs/${r.id}/resolve`); refresh(); }} className="h-7 text-[10px]">Resolve</Button>
                      )}
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────
   CSV import / export
   ────────────────────────────────────────────────────────────────── */
function CsvTab() {
  const [kind, setKind] = useState("motive_vehicles");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  const apiBase = `${process.env.REACT_APP_BACKEND_URL}/api`;

  const upload = async () => {
    if (!file) { toast.error("Choose a CSV first"); return; }
    setUploading(true); setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("kind", kind);
      const r = await api.post("/admin/integrations/import-csv", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(r.data);
      toast.success(`Imported · created ${r.data.records_created}, updated ${r.data.records_updated}`);
    } catch (e) { toast.error(operationalError(e, "Import failed")); }
    finally { setUploading(false); }
  };

  const adminToken = (typeof window !== "undefined" && window.localStorage)
    ? localStorage.getItem("masci.admin.token") : "";

  const exportButtons = [
    { label: "Asset mappings (all)", path: "/admin/integrations/export/asset-mappings" },
    { label: "Employee mappings (all)", path: "/admin/integrations/export/employee-mappings" },
    { label: "Unmapped equipment", path: "/admin/integrations/export/unmapped-equipment" },
    { label: "Unmapped employees", path: "/admin/integrations/export/unmapped-employees" },
  ];

  const downloadExport = async (path, label) => {
    try {
      const r = await api.get(path, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement("a");
      a.href = url; a.download = path.split("/").pop() + ".csv";
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`${label} exported`);
    } catch (e) { toast.error(operationalError(e, "Export failed")); }
  };

  return (
    <div className="space-y-4">
      <div className="bg-white border border-slate-200 rounded-md p-5">
        <h3 className="font-display text-lg font-black mb-2 flex items-center gap-2"><FileUp className="w-5 h-5" /> Import mappings from CSV</h3>
        <p className="text-sm text-slate-600 mb-4">
          Bulk-create / bulk-update mappings before the live API is wired. Each CSV must include a <code>masci_equipment_id</code>
          (for asset rows) or <code>masci_employee_id</code> (for driver/user rows) plus the relevant provider ID columns.
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4 items-end">
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">CSV kind</Label>
            <Select value={kind} onValueChange={setKind}>
              <SelectTrigger className={`${inputCls} mt-1`} data-testid="ic-csv-kind"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="motive_vehicles">Motive · Vehicles (asset mappings)</SelectItem>
                <SelectItem value="motive_drivers">Motive · Drivers (employee mappings)</SelectItem>
                <SelectItem value="maintainx_assets">MaintainX · Assets (asset mappings)</SelectItem>
                <SelectItem value="maintainx_users">MaintainX · Users (employee mappings)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">File</Label>
            <Input type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} className={`${inputCls} mt-1`} data-testid="ic-csv-file" />
          </div>
          <Button onClick={upload} disabled={uploading || !file} className="bg-slate-900 hover:bg-slate-800 text-white h-10" data-testid="ic-csv-upload">
            {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <FileUp className="w-3.5 h-3.5 mr-1" />} Import
          </Button>
        </div>
        {result && (
          <div className="mt-4 bg-slate-50 border-2 border-slate-200 rounded p-3 text-sm" data-testid="ic-csv-result">
            <div className="font-mono text-xs">
              <span className="font-bold">{result.records_created}</span> created · <span className="font-bold">{result.records_updated}</span> updated · <span className="font-bold">{result.records_skipped}</span> skipped · <span className="font-bold text-red-700">{result.records_failed}</span> failed
            </div>
            {result.errors?.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-xs text-red-700 space-y-0.5">
                {result.errors.slice(0, 10).map((er, i) => <li key={i}>{er}</li>)}
              </ul>
            )}
          </div>
        )}
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-5">
        <h3 className="font-display text-lg font-black mb-2 flex items-center gap-2"><FileDown className="w-5 h-5" /> Export to CSV</h3>
        <p className="text-sm text-slate-600 mb-4">
          Hand the unmapped-equipment / unmapped-employees CSV to your Motive or MaintainX account manager
          so they can pre-populate IDs on their side.
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
          {exportButtons.map((b) => (
            <Button
              key={b.path}
              variant="outline"
              onClick={() => downloadExport(b.path, b.label)}
              className="h-10 justify-start"
              data-testid={`ic-csv-export-${b.path.split("/").pop()}`}
            >
              <FileDown className="w-3.5 h-3.5 mr-2" /> {b.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}


/* ──────────────────────────────────────────────────────────────────
   Mappings Wizard — paste/upload a CSV of provider IDs, match by
   unit_number, REVIEW EVERY ROW, then commit. Never overwrites
   existing mappings without explicit force-overwrite per row.
   ────────────────────────────────────────────────────────────────── */
const STATUS_PILL = {
  ready:              { cls: "bg-emerald-100 text-emerald-900 border-emerald-300", label: "Ready" },
  noop:               { cls: "bg-slate-200 text-slate-700 border-slate-300",       label: "Already linked" },
  conflict:           { cls: "bg-amber-100 text-amber-900 border-amber-300",       label: "Conflict" },
  duplicate:          { cls: "bg-violet-100 text-violet-900 border-violet-300",    label: "Duplicate unit" },
  external_collision: { cls: "bg-red-100 text-red-900 border-red-300",             label: "External collision" },
  unmatched:          { cls: "bg-slate-100 text-slate-500 border-slate-200",       label: "No match" },
};

function WizardTab() {
  const [kind, setKind] = useState("motive_vehicles");
  const [sourceLabel, setSourceLabel] = useState("paste");
  const [paste, setPaste] = useState("");
  const [unitCol, setUnitCol] = useState("unit_number");
  const [extIdCol, setExtIdCol] = useState("external_id");
  const [extNameCol, setExtNameCol] = useState("external_name");
  const [previewing, setPreviewing] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [preview, setPreview] = useState(null);
  const [decisions, setDecisions] = useState({}); // row_index → {action, masci_equipment_id?, force_overwrite?}
  const [runs, setRuns] = useState([]);
  const [lastRun, setLastRun] = useState(null);
  const [runsLoadError, setRunsLoadError] = useState("");

  const loadRuns = async () => {
    try {
      setRuns((await api.get("/admin/integrations/mappings/wizard/runs?limit=10")).data || []);
      setRunsLoadError("");
    } catch (err) {
      // iter308 · admin-visible failure handling (per stabilization-posture
      // trust-refinement principle: admin surfaces should fail loudly, never
      // crew surfaces). Was previously a silent swallow that hid integration
      // outages from the only operator who can fix them.
      console.error("[admin/integrations] wizard runs load failed:", err);
      setRunsLoadError(err?.response?.data?.detail || err?.message || "Failed to load recent runs");
    }
  };
  useEffect(() => { loadRuns(); }, []);

  const parseRows = () => {
    // Accept CSV or TSV. First line is treated as header IFF it contains
    // at least one of the named columns; otherwise we fall back to the
    // first three columns being [unit, ext_id, ext_name].
    const lines = paste.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) return [];
    const sniff = lines[0].includes("\t") ? "\t" : ",";
    const headerParts = lines[0].split(sniff).map((s) => s.trim().replace(/^"|"$/g, ""));
    const lower = headerParts.map((h) => h.toLowerCase());
    const hasHeader = lower.includes(unitCol) || lower.includes(extIdCol) || lower.includes(extNameCol);
    let dataLines = lines;
    let cols;
    if (hasHeader) {
      cols = {
        unit: lower.indexOf(unitCol),
        ext: lower.indexOf(extIdCol),
        name: lower.indexOf(extNameCol),
      };
      dataLines = lines.slice(1);
    } else {
      cols = { unit: 0, ext: 1, name: 2 };
    }
    return dataLines.map((l) => {
      const parts = l.split(sniff).map((s) => s.trim().replace(/^"|"$/g, ""));
      return {
        unit_number: cols.unit >= 0 ? (parts[cols.unit] || "") : "",
        external_id: cols.ext >= 0 ? (parts[cols.ext] || "") : "",
        external_name: cols.name >= 0 ? (parts[cols.name] || "") : "",
      };
    });
  };

  const runPreview = async () => {
    const rows = parseRows();
    if (rows.length === 0) { toast.error("Paste at least one row of CSV/TSV data"); return; }
    setPreviewing(true);
    setPreview(null);
    setLastRun(null);
    setDecisions({});
    try {
      const r = await api.post("/admin/integrations/mappings/wizard/preview", { kind, rows });
      setPreview(r.data);
      // Seed default per-row decisions: ready → suggested_action;
      // conflict → skip (force_overwrite off); everything else → skip
      const seed = {};
      (r.data.rows || []).forEach((row) => {
        if (row.status === "ready") {
          seed[row.row_index] = {
            action: row.suggested_action || "create",
            masci_equipment_id: row.matches?.[0]?.masci_equipment_id || null,
            mapping_id: row.current_mapping_id || null,
            external_id: row.input_external_id,
            force_overwrite: false,
          };
        } else if (row.status === "conflict") {
          seed[row.row_index] = {
            action: "skip",
            masci_equipment_id: row.matches?.[0]?.masci_equipment_id || null,
            mapping_id: row.current_mapping_id || null,
            external_id: row.input_external_id,
            force_overwrite: false,
          };
        } else {
          seed[row.row_index] = {
            action: "skip",
            masci_equipment_id: row.matches?.[0]?.masci_equipment_id || null,
            external_id: row.input_external_id,
            force_overwrite: false,
          };
        }
      });
      setDecisions(seed);
      toast.success(`Preview ready — ${r.data.totals.ready} ready · ${r.data.totals.conflict} conflict · ${r.data.totals.unmatched} unmatched`);
    } catch (e) {
      const d = e?.response?.data?.detail;
      toast.error(typeof d === "string" ? d : (d ? JSON.stringify(d).slice(0, 200) : "Preview failed"));
    } finally { setPreviewing(false); }
  };

  const commit = async () => {
    if (!preview) return;
    const decisionList = (preview.rows || []).map((row) => {
      const d = decisions[row.row_index] || { action: "skip" };
      return {
        action: d.action,
        masci_equipment_id: d.masci_equipment_id || null,
        mapping_id: d.mapping_id || null,
        external_id: d.external_id || row.input_external_id || "",
        external_name: row.input_external_name || "",
        force_overwrite: !!d.force_overwrite,
      };
    });
    const willWrite = decisionList.filter((d) => d.action !== "skip").length;
    if (willWrite === 0) {
      toast.error("All rows are set to Skip — nothing to commit");
      return;
    }
    if (!window.confirm(
      `Commit ${willWrite} mapping change${willWrite === 1 ? "" : "s"}?\n\n` +
      "This will write to the asset_mappings collection.\n" +
      "Master equipment records are NOT touched."
    )) return;
    setCommitting(true);
    try {
      const r = await api.post("/admin/integrations/mappings/wizard/commit", {
        kind, source_label: sourceLabel, decisions: decisionList,
      });
      setLastRun(r.data);
      toast.success(`Run complete · ${r.data.totals.created} created · ${r.data.totals.updated} updated · ${r.data.totals.blocked} blocked`);
      setPreview(null); setDecisions({}); setPaste("");
      loadRuns();
    } catch (e) {
      const d = e?.response?.data?.detail;
      toast.error(typeof d === "string" ? d : (d ? JSON.stringify(d).slice(0, 200) : "Commit failed"));
    } finally { setCommitting(false); }
  };

  const updateDecision = (row_index, patch) => {
    setDecisions((d) => ({ ...d, [row_index]: { ...(d[row_index] || {}), ...patch } }));
  };

  const reset = () => {
    setPreview(null); setDecisions({}); setLastRun(null); setPaste("");
  };

  return (
    <div className="space-y-4">
      {/* Header / safety banner */}
      <div className="bg-white border border-slate-200 rounded-md p-5">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-slate-900 text-white shrink-0">
            <Wand2 className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
              Two-step · review-before-commit
            </span>
            <h3 className="font-display text-lg font-black mt-0.5 leading-tight">
              Mappings Wizard
            </h3>
            <p className="text-sm text-slate-600 mt-1">
              Paste rows from a Motive or MaintainX export, match by MASCI unit number,
              <strong> review every row</strong>, then commit. Master equipment records are never
              modified — only the <code className="text-xs">asset_mappings</code> collection is written.
              Existing mappings will <strong>not</strong> be overwritten unless you explicitly toggle
              force-overwrite on that row.
            </p>
          </div>
        </div>
      </div>

      {/* Step 1 — pick source kind + column hints + paste */}
      <div className="bg-white border border-slate-200 rounded-md p-5">
        <h4 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-3">
          Step 1 · Configure & paste rows
        </h4>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-8 gap-y-4">
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Provider</Label>
            <Select value={kind} onValueChange={setKind}>
              <SelectTrigger className={`${inputCls} mt-1`} data-testid="ic-wizard-kind"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="motive_vehicles">Motive · Vehicles</SelectItem>
                <SelectItem value="maintainx_assets">MaintainX · Assets</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Source label (for audit log)</Label>
            <Input value={sourceLabel} onChange={(e) => setSourceLabel(e.target.value)} className={`${inputCls} mt-1`} placeholder="paste, csv, motive-export-20260514" data-testid="ic-wizard-source" />
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Unit col</Label>
              <Input value={unitCol} onChange={(e) => setUnitCol(e.target.value.toLowerCase())} className={`${inputCls} mt-1`} data-testid="ic-wizard-col-unit" />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">ID col</Label>
              <Input value={extIdCol} onChange={(e) => setExtIdCol(e.target.value.toLowerCase())} className={`${inputCls} mt-1`} data-testid="ic-wizard-col-ext" />
            </div>
            <div>
              <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Name col</Label>
              <Input value={extNameCol} onChange={(e) => setExtNameCol(e.target.value.toLowerCase())} className={`${inputCls} mt-1`} data-testid="ic-wizard-col-name" />
            </div>
          </div>
        </div>

        <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mt-3 block">
          Paste CSV / TSV (header row optional — falls back to first 3 columns)
        </Label>
        <Textarea
          value={paste}
          onChange={(e) => setPaste(e.target.value)}
          rows={8}
          className="text-xs font-mono border-2 border-slate-300 mt-1"
          placeholder={`unit_number,external_id,external_name\nEXC-8614,mv-100,Excavator 8614\nBH004-3882,mv-101,Backhoe 3882`}
          data-testid="ic-wizard-paste"
        />
        <div className="flex items-center gap-2 mt-3">
          <Button onClick={runPreview} disabled={previewing || !paste.trim()} className="bg-slate-900 hover:bg-slate-800 text-white h-10" data-testid="ic-wizard-preview">
            {previewing ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Wand2 className="w-3.5 h-3.5 mr-1" />} Preview matches
          </Button>
          {(preview || lastRun) && (
            <Button onClick={reset} variant="outline" className="h-10" data-testid="ic-wizard-reset">
              <Undo2 className="w-3.5 h-3.5 mr-1" /> Reset
            </Button>
          )}
        </div>
      </div>

      {/* Step 2 — review */}
      {preview && (
        <div className="bg-white border border-slate-200 rounded-md p-5" data-testid="ic-wizard-preview-panel">
          <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
            <div>
              <h4 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">
                Step 2 · Review every row before committing
              </h4>
              <p className="text-xs text-slate-500 mt-0.5">
                {preview.totals.input_rows} input rows ·
                <strong className="text-emerald-700"> {preview.totals.ready} ready</strong> ·
                <strong className="text-amber-700"> {preview.totals.conflict} conflicts</strong> ·
                <strong className="text-violet-700"> {preview.totals.duplicate} duplicates</strong> ·
                <strong className="text-red-700"> {preview.totals.external_collision} ID collisions</strong> ·
                <strong className="text-slate-700"> {preview.totals.unmatched} unmatched</strong> ·
                <strong className="text-slate-700"> {preview.totals.noop} already linked</strong>
              </p>
            </div>
            <Button onClick={commit} disabled={committing} className="bg-emerald-700 hover:bg-emerald-800 text-white h-10" data-testid="ic-wizard-commit">
              {committing ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Save className="w-3.5 h-3.5 mr-1" />} Commit reviewed rows
            </Button>
          </div>

          <div className="overflow-x-auto bg-slate-50 border border-slate-200 rounded-md max-h-[480px]">
            <table className="w-full text-xs">
              <thead className="bg-slate-100 text-slate-700 uppercase tracking-[0.15em] font-mono sticky top-0">
                <tr>
                  <th className="text-left px-2 py-2">#</th>
                  <th className="text-left px-2 py-2">Status</th>
                  <th className="text-left px-2 py-2">Unit</th>
                  <th className="text-left px-2 py-2">External ID</th>
                  <th className="text-left px-2 py-2">Matched master</th>
                  <th className="text-left px-2 py-2">Action</th>
                  <th className="text-left px-2 py-2">Force</th>
                </tr>
              </thead>
              <tbody>
                {(preview.rows || []).map((r) => {
                  const pill = STATUS_PILL[r.status] || STATUS_PILL.unmatched;
                  const d = decisions[r.row_index] || {};
                  const isDup = r.status === "duplicate";
                  const canForce = r.status === "conflict";
                  return (
                    <tr key={r.row_index} className="border-t border-slate-100" data-testid={`ic-wizard-row-${r.row_index}`}>
                      <td className="px-2 py-2 font-mono text-slate-500">{r.row_index + 1}</td>
                      <td className="px-2 py-2">
                        <span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${pill.cls}`}>{pill.label}</span>
                        {r.reason && <div className="text-[10px] text-slate-500 mt-1 max-w-xs">{r.reason}</div>}
                      </td>
                      <td className="px-2 py-2 font-mono">{r.input_unit_number || <span className="text-slate-400">—</span>}</td>
                      <td className="px-2 py-2 font-mono">{r.input_external_id || <span className="text-slate-400">—</span>}</td>
                      <td className="px-2 py-2">
                        {isDup ? (
                          <Select
                            value={d.masci_equipment_id || ""}
                            onValueChange={(v) => updateDecision(r.row_index, { masci_equipment_id: v })}
                          >
                            <SelectTrigger className="h-7 text-xs"><SelectValue placeholder="Pick one" /></SelectTrigger>
                            <SelectContent>
                              {(r.matches || []).map((m) => (
                                <SelectItem key={m.masci_equipment_id} value={m.masci_equipment_id}>
                                  {m.unit_number} · {m.make || ""} {m.model || ""}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : r.matches?.length ? (
                          <div>
                            <div className="font-bold">{r.matches[0].unit_number}</div>
                            <div className="text-[10px] text-slate-500">{r.matches[0].make} {r.matches[0].model}</div>
                            {r.current_external_id && <div className="text-[10px] text-amber-700 font-mono">current: {r.current_external_id}</div>}
                          </div>
                        ) : <span className="text-slate-400">—</span>}
                      </td>
                      <td className="px-2 py-2">
                        <Select
                          value={d.action || "skip"}
                          onValueChange={(v) => updateDecision(r.row_index, { action: v })}
                        >
                          <SelectTrigger className="h-7 text-xs w-28" data-testid={`ic-wizard-action-${r.row_index}`}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="skip">Skip</SelectItem>
                            <SelectItem value="create" disabled={r.status === "unmatched" || r.status === "noop" || (isDup && !d.masci_equipment_id) || r.status === "external_collision" || !!r.current_mapping_id}>Create</SelectItem>
                            <SelectItem value="update" disabled={!r.current_mapping_id && !(isDup && d.masci_equipment_id) && r.status !== "ready"}>Update</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="px-2 py-2 text-center">
                        {canForce ? (
                          <Switch
                            checked={!!d.force_overwrite}
                            onCheckedChange={(v) => updateDecision(r.row_index, { force_overwrite: v, action: v ? "update" : (d.action || "skip") })}
                            data-testid={`ic-wizard-force-${r.row_index}`}
                          />
                        ) : (
                          <span className="text-[9px] text-slate-300">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Last run summary */}
      {lastRun && (
        <div className="bg-emerald-50 border-2 border-emerald-300 rounded-md p-4" data-testid="ic-wizard-last-run">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 className="w-4 h-4 text-emerald-700" />
            <h4 className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-900 font-bold">
              Run complete
            </h4>
          </div>
          <div className="text-xs text-emerald-900 font-mono">
            +{lastRun.totals.created} created · ~{lastRun.totals.updated} updated · skipped {lastRun.totals.skipped} · blocked {lastRun.totals.blocked} · errored {lastRun.totals.errored}
          </div>
        </div>
      )}

      {/* Recent runs (audit) */}
      <div className="bg-white border border-slate-200 rounded-md p-4">
        <h4 className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold mb-2">
          Recent wizard runs (audit)
        </h4>
        {runsLoadError ? (
          <p
            className="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded px-2 py-1.5"
            data-testid="ic-wizard-runs-load-error"
          >
            {runsLoadError}
          </p>
        ) : runs.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No wizard runs yet.</p>
        ) : (
          <ul className="divide-y divide-slate-100" data-testid="ic-wizard-runs-list">
            {runs.map((r) => (
              <li key={r.id} className="py-2 text-xs flex items-center gap-3">
                <span className="font-mono text-slate-500 w-32 shrink-0">{(r.started_at || "").slice(0, 16).replace("T", " ")}</span>
                <span className="font-mono text-slate-700 w-32 shrink-0">{r.kind}</span>
                <span className="text-slate-700 w-36 shrink-0 truncate" title={r.actor}>{r.actor}</span>
                <span className="font-mono text-[10px] text-slate-600">
                  +{r.totals.created} ~{r.totals.updated} skip {r.totals.skipped} block {r.totals.blocked}
                </span>
                <ChevronRight className="w-3 h-3 text-slate-300 ml-auto" />
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────
 * P1-A / P1-B · Motive ↔ MASCI Auto-Link button.
 * Re-uses POST /api/admin/integrations/motive/auto-link?kind={assets|drivers}
 * Idempotent · never overwrites manual mappings · logs to sync_logs.
 * ────────────────────────────────────────────────────────────────── */
function AutoLinkButton({ kind, onDone }) {
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState(null);
  const target = kind === "asset" ? "assets" : "drivers";

  const doPreview = async () => {
    setBusy(true);
    try {
      const r = await api.get(`/admin/integrations/motive/auto-link/preview?kind=${target}`);
      setPreview(r.data);
    } catch (e) { toast.error(operationalError(e, "Preview failed")); }
    finally { setBusy(false); }
  };
  const doRun = async () => {
    setBusy(true);
    try {
      const r = await api.post(`/admin/integrations/motive/auto-link?kind=${target}`);
      toast.success(`Auto-linked ${r.data.linked} · ${r.data.skipped_manual} kept · ${r.data.conflicts} conflict${r.data.conflicts === 1 ? "" : "s"}`);
      setPreview(null);
      onDone && onDone();
    } catch (e) { toast.error(operationalError(e, "Auto-link failed")); }
    finally { setBusy(false); }
  };

  return (
    <>
      <Button
        onClick={doPreview}
        disabled={busy}
        variant="outline"
        className="h-10 border-emerald-300 text-emerald-800 hover:bg-emerald-50"
        data-testid={`ic-${kind}-autolink-preview`}
      >
        <Zap className="w-3.5 h-3.5 mr-1.5" /> Auto-Link from Motive
      </Button>
      {preview && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setPreview(null)}>
          <div className="bg-white rounded-md max-w-xl w-full p-5 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()} data-testid={`ic-${kind}-autolink-dialog`}>
            <div className="flex items-start gap-3 mb-3">
              <Zap className="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-display text-lg font-black">Auto-Link Preview · {target}</h3>
                <p className="text-xs text-slate-600 mt-1">
                  This will link Motive {target} to MASCI {kind === "asset" ? "equipment" : "employees"} using
                  high-confidence matches only (VIN / unit-number for assets · email / full-name for drivers).
                  <strong> Existing manual links are never overwritten.</strong>
                </p>
              </div>
              <button onClick={() => setPreview(null)} className="text-slate-400 hover:text-slate-700"><X className="w-4 h-4" /></button>
            </div>
            <div className="grid grid-cols-4 gap-2 mb-4">
              <AutoLinkStat label="Will Link" value={preview.counts?.link ?? 0} cls="bg-emerald-50 border-emerald-300 text-emerald-900" />
              <AutoLinkStat label="Manual (skip)" value={preview.counts?.skip_manual_link ?? 0} cls="bg-amber-50 border-amber-300 text-amber-900" />
              <AutoLinkStat label="Same (noop)" value={preview.counts?.skip_already_linked_same ?? 0} cls="bg-slate-50 border-slate-300 text-slate-800" />
              <AutoLinkStat label="No Match" value={preview.counts?.no_match ?? 0} cls="bg-slate-50 border-slate-300 text-slate-700" />
            </div>
            <div className="border border-slate-200 rounded-md overflow-x-auto max-h-72">
              <table className="w-full text-xs">
                <thead className="bg-slate-100 text-[10px] uppercase tracking-[0.15em] font-mono text-slate-700">
                  <tr>
                    <th className="text-left px-2 py-1.5">Motive</th>
                    <th className="text-left px-2 py-1.5">MASCI</th>
                    <th className="text-left px-2 py-1.5">Method</th>
                    <th className="text-left px-2 py-1.5">Decision</th>
                  </tr>
                </thead>
                <tbody>
                  {(preview.proposals || []).slice(0, 50).map((p, i) => (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="px-2 py-1 font-mono">{p.motive_number || p.motive_name || p.motive_vehicle_id || p.motive_driver_id}</td>
                      <td className="px-2 py-1 font-mono">{p.candidate_unit_number || p.candidate_employee_name || <span className="text-slate-400">—</span>}</td>
                      <td className="px-2 py-1 font-mono uppercase tracking-[0.1em]">{p.match_method || "—"}</td>
                      <td className="px-2 py-1">
                        {p.decision === "link" && <span className="text-emerald-700 font-bold">Link</span>}
                        {p.decision === "skip_manual_link" && <span className="text-amber-700">Manual</span>}
                        {p.decision === "skip_already_linked_same" && <span className="text-slate-500">Same</span>}
                        {p.decision === "no_match" && <span className="text-slate-400">—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-end gap-2 mt-4">
              <Button variant="outline" onClick={() => setPreview(null)} disabled={busy} data-testid={`ic-${kind}-autolink-cancel`}>Cancel</Button>
              <Button onClick={doRun} disabled={busy || (preview.counts?.link ?? 0) === 0} className="bg-emerald-700 hover:bg-emerald-800 text-white" data-testid={`ic-${kind}-autolink-confirm`}>
                {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : <Zap className="w-3.5 h-3.5 mr-1.5" />}
                Link {preview.counts?.link ?? 0} now
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function AutoLinkStat({ label, value, cls }) {
  return (
    <div className={`rounded-md border-2 px-2 py-2 ${cls}`}>
      <div className="font-mono text-[9px] uppercase tracking-[0.15em] font-bold">{label}</div>
      <div className="font-display text-xl font-black mt-0.5">{value}</div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────
 * P1-G · Geofences tab (read-only). Surfaces the 67 ingested
 * Motive geofences with their "currently inside" vehicle count
 * (point-in-polygon at request time — no schema changes).
 * ────────────────────────────────────────────────────────────────── */
function GeofencesTab() {
  const [rows, setRows] = useState(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("all");
  const [category, setCategory] = useState("all");

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (status !== "all") params.set("status", status);
      if (category !== "all") params.set("category", category);
      const r = await api.get(`/integrations/motive/geofences${params.toString() ? `?${params}` : ""}`);
      setRows(Array.isArray(r.data) ? r.data : []);
    } catch (e) { toast.error(operationalError(e, "Could not load geofences")); setRows([]); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [status, category]);

  const categories = ["all", ...Array.from(new Set((rows || []).map((g) => g.category).filter(Boolean)))];
  const totalActive = (rows || []).filter((g) => g.status === "active").length;
  const totalInside = (rows || []).reduce((acc, g) => acc + (g.linked_assets_count || 0), 0);

  return (
    <div className="space-y-4" data-testid="ic-geofences">
      <div className="bg-white border border-slate-200 rounded-md p-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h3 className="font-display text-lg font-black">Motive Geofences</h3>
            <p className="text-sm text-slate-600">
              {rows ? rows.length : "…"} geofences synced · {totalActive} active · <strong>{totalInside}</strong> vehicle{totalInside === 1 ? "" : "s"} currently inside a polygon. Read-only.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-36 h-9" data-testid="ic-geofence-status"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="deactivated">Deactivated</SelectItem>
              </SelectContent>
            </Select>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="w-44 h-9" data-testid="ic-geofence-category"><SelectValue /></SelectTrigger>
              <SelectContent>
                {categories.map((c) => <SelectItem key={c} value={c}>{c === "all" ? "All Categories" : c}</SelectItem>)}
              </SelectContent>
            </Select>
            <Button size="sm" variant="outline" onClick={load} className="h-9" data-testid="ic-geofence-refresh">
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
            </Button>
          </div>
        </div>
      </div>

      {loading && !rows ? (
        <div className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>
      ) : !rows || rows.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-md p-8 text-center text-slate-500">
          No geofences match the current filter.
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-[10px] uppercase tracking-[0.15em] font-mono text-slate-700">
              <tr>
                <th className="text-left px-3 py-2">Name</th>
                <th className="text-left px-3 py-2">Category</th>
                <th className="text-left px-3 py-2">Status</th>
                <th className="text-left px-3 py-2">Address</th>
                <th className="text-right px-3 py-2">Inside Now</th>
                <th className="text-left px-3 py-2">Last Activity</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((g) => (
                <tr key={g.id} className="border-t border-slate-100" data-testid={`ic-geofence-row-${g.id}`}>
                  <td className="px-3 py-2 font-bold">{g.name || <span className="text-slate-400">—</span>}</td>
                  <td className="px-3 py-2 text-xs">{g.category || "Uncategorized"}</td>
                  <td className="px-3 py-2 text-xs">
                    <span className={`px-1.5 py-0.5 rounded font-mono uppercase tracking-[0.12em] text-[10px] font-bold ${g.status === "active" ? "bg-emerald-100 text-emerald-900 border border-emerald-300" : "bg-slate-100 text-slate-600 border border-slate-300"}`}>{g.status}</span>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-600">{g.address || "—"}</td>
                  <td className="px-3 py-2 text-right">
                    {g.linked_assets_count > 0
                      ? <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-100 text-blue-900 border border-blue-300 font-mono text-[11px] font-bold"><Activity className="w-3 h-3" /> {g.linked_assets_count}</span>
                      : <span className="text-slate-300 font-mono text-xs">0</span>}
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-500 font-mono">
                    {g.last_activity_at ? new Date(g.last_activity_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

