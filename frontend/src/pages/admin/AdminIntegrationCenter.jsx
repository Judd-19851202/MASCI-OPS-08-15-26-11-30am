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
  CheckCircle2, ExternalLink, Eye, EyeOff,
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
      <div className="bg-white border-2 border-slate-300 rounded-md p-5 mb-5">
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
          <TabsTrigger value="assets" data-testid="ic-tab-assets"><Truck className="w-3.5 h-3.5 mr-1" /> Asset Mapping</TabsTrigger>
          <TabsTrigger value="employees" data-testid="ic-tab-employees"><Users className="w-3.5 h-3.5 mr-1" /> Employee Mapping</TabsTrigger>
          <TabsTrigger value="sync" data-testid="ic-tab-sync"><FileText className="w-3.5 h-3.5 mr-1" /> Sync Logs</TabsTrigger>
          <TabsTrigger value="errors" data-testid="ic-tab-errors"><AlertOctagon className="w-3.5 h-3.5 mr-1" /> Error Logs</TabsTrigger>
          <TabsTrigger value="csv" data-testid="ic-tab-csv"><FileUp className="w-3.5 h-3.5 mr-1" /> CSV Import / Export</TabsTrigger>
        </TabsList>

        <TabsContent value="overview"><OverviewTab /></TabsContent>
        <TabsContent value="motive"><ProviderTab provider="motive" /></TabsContent>
        <TabsContent value="maintainx"><ProviderTab provider="maintainx" /></TabsContent>
        <TabsContent value="assets"><AssetMappingTab /></TabsContent>
        <TabsContent value="employees"><EmployeeMappingTab /></TabsContent>
        <TabsContent value="sync"><SyncLogsTab /></TabsContent>
        <TabsContent value="errors"><ErrorLogsTab /></TabsContent>
        <TabsContent value="csv"><CsvTab /></TabsContent>
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
    catch (e) { toast.error(e?.response?.data?.detail || "Could not load overview"); }
    finally { setLoading(false); }
  };
  useEffect(() => { refresh(); }, []);

  if (loading || !data) return <div className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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
    } catch (e) { toast.error(e?.response?.data?.detail || "Test failed"); }
    finally { setTesting(false); onRefresh(); }
  };
  return (
    <div className="bg-white border-2 border-slate-300 rounded-md p-5" data-testid={`ic-status-${p.provider}`}>
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
    } catch (e) { toast.error(e?.response?.data?.detail || "Save failed"); }
    finally { setSaving(false); }
  };

  if (loading || !doc) return <div className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>;

  const webhookFullUrl = `${window.location.origin}${doc.webhook_url_path}`;

  return (
    <div className="space-y-4">
      <div className="bg-white border-2 border-slate-300 rounded-md p-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

      <div className="bg-white border-2 border-slate-300 rounded-md p-5">
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
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

      <div className="bg-white border-2 border-slate-300 rounded-md p-5">
        <h3 className="font-display text-lg font-black mb-2">Webhook endpoint</h3>
        <p className="text-sm text-slate-600 mb-2">
          Configure {provider === "motive" ? "Motive" : "MaintainX"} to deliver events to this URL.
          {!doc.webhook_secret_present && <span className="text-amber-700 font-bold"> Configure the webhook secret first — deliveries without a valid signature are rejected.</span>}
        </p>
        <div className="font-mono text-xs bg-slate-50 border-2 border-slate-200 rounded p-3 select-all break-all" data-testid={`ic-${provider}-webhook-url`}>
          {webhookFullUrl}
        </div>
      </div>

      <div className="bg-white border-2 border-slate-300 rounded-md p-5">
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
    <div className="border-2 border-slate-200 rounded-md p-3">
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
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not load"); }
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
    } catch (e) { toast.error(e?.response?.data?.detail || "Save failed"); }
    finally { setSaving(false); }
  };

  const remove = async (m) => {
    if (!window.confirm(`Delete this mapping?`)) return;
    try {
      await api.delete(`${listUrl}/${m.id}`);
      toast.success("Removed"); refresh();
    } catch (e) { toast.error(e?.response?.data?.detail || "Delete failed"); }
  };

  if (loading) return <div className="text-center py-12"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>;

  return (
    <div className="space-y-4">
      <div className="bg-white border-2 border-slate-300 rounded-md p-4">
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
        </div>
      </div>

      <div className="overflow-x-auto bg-white border-2 border-slate-200 rounded-md">
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
      <div className="overflow-x-auto bg-white border-2 border-slate-200 rounded-md">
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
    } catch (e) { toast.error(e?.response?.data?.detail || "Import failed"); }
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
    } catch (e) { toast.error(e?.response?.data?.detail || "Export failed"); }
  };

  return (
    <div className="space-y-4">
      <div className="bg-white border-2 border-slate-300 rounded-md p-5">
        <h3 className="font-display text-lg font-black mb-2 flex items-center gap-2"><FileUp className="w-5 h-5" /> Import mappings from CSV</h3>
        <p className="text-sm text-slate-600 mb-4">
          Bulk-create / bulk-update mappings before the live API is wired. Each CSV must include a <code>masci_equipment_id</code>
          (for asset rows) or <code>masci_employee_id</code> (for driver/user rows) plus the relevant provider ID columns.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
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

      <div className="bg-white border-2 border-slate-300 rounded-md p-5">
        <h3 className="font-display text-lg font-black mb-2 flex items-center gap-2"><FileDown className="w-5 h-5" /> Export to CSV</h3>
        <p className="text-sm text-slate-600 mb-4">
          Hand the unmapped-equipment / unmapped-employees CSV to your Motive or MaintainX account manager
          so they can pre-populate IDs on their side.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
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
