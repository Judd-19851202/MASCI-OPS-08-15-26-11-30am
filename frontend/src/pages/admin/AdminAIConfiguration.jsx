// AdminAIConfiguration.jsx — AI-ADMIN-001 · Admin AI Configuration Center
//
// Admin-only surface for managing tenant AI capabilities.
// - Section 1: System Status (gateway + provider readiness)
// - Section 2: Provider Routing (read-only defaults)
// - Section 3: Tenant Selector
// - Section 4: Tenant AI Enablement toggles
// - Section 5: Disabled-Mode Proof panel (invariants)
// - Section 6: Audit Log for the selected tenant
//
// Zero raw secrets are ever rendered. All writes are audit-logged
// server-side. Field/PM users cannot reach this route — the strict
// admin token gate enforces access at the API layer.
import React, { useEffect, useMemo, useState } from "react";
import { formatPlatformTimeOnly } from "@/lib/platformTime";
import {
  Sparkles,
  Shield,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCcw,
  Save,
  Loader2,
  Cpu,
  Globe2,
  History,
  Users,
  KeyRound,
  Info,
} from "lucide-react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";

// ── Module display metadata ─────────────────────────────────────────
const MODULE_META = [
  {
    key: "daily_report_summary",
    field: "daily_report_summary_enabled",
    label: "Daily Report Summary",
    desc: "Optional narrative summary generated from V1 daily reports.",
  },
  {
    key: "photo_intelligence",
    field: "photo_intelligence_enabled",
    label: "Photo Intelligence",
    desc: "Vision-based observation extraction on uploaded jobsite photos.",
  },
  {
    key: "pm_intelligence",
    field: "pm_intelligence_enabled",
    label: "PM Intelligence",
    desc: "Project-manager briefings assembled from ODS facts.",
  },
  {
    key: "admin_intelligence",
    field: "admin_intelligence_enabled",
    label: "Admin Intelligence",
    desc: "Executive rollups across projects.",
  },
  {
    key: "safety_intelligence",
    field: "safety_intelligence_enabled",
    label: "Safety Intelligence",
    desc: "Safety-signal detection and pattern surfacing.",
  },
  {
    key: "translation",
    field: "translation_enabled",
    label: "Translation (EN ↔ ES)",
    desc: "Field-form translation assistance.",
  },
];

const PROVIDER_META = [
  { key: "anthropic", label: "Claude / Anthropic", icon: Sparkles },
  { key: "openai", label: "OpenAI", icon: Cpu },
  { key: "google", label: "Google Gemini", icon: Globe2 },
];

// ── Helpers ─────────────────────────────────────────────────────────
function providerStatus(p) {
  if (!p) return { label: "Unknown", tone: "slate" };
  if (p.enabled && p.key_present) return { label: "Configured", tone: "emerald" };
  if (p.enabled && !p.key_present) return { label: "Missing key", tone: "amber" };
  if (!p.enabled && p.key_present) return { label: "Globally disabled", tone: "slate" };
  return { label: "Unavailable", tone: "slate" };
}

const TONE_CLS = {
  emerald: "border-emerald-300 bg-emerald-50 text-emerald-800",
  amber: "border-amber-300 bg-amber-50 text-amber-800",
  red: "border-red-300 bg-red-50 text-red-800",
  rose: "border-rose-300 bg-rose-50 text-rose-800",
  slate: "border-slate-300 bg-slate-50 text-slate-700",
};

function StatusBadge({ tone = "slate", children, testid }) {
  return (
    <span
      data-testid={testid}
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold border ${TONE_CLS[tone]}`}
    >
      {children}
    </span>
  );
}

function humanReason(reason) {
  if (!reason) return "";
  if (reason === "ai_gateway_disabled_global") return "Global AI gateway is disabled.";
  if (reason === "tenant_ai_disabled") return "Tenant AI envelope is off.";
  if (reason.startsWith("module_disabled_global:"))
    return "Deployment flag for this module is off.";
  if (reason.startsWith("module_disabled_tenant:"))
    return "Tenant flag for this module is off.";
  if (reason === "no_provider_available")
    return "No provider is ready (flag off or key missing).";
  if (reason === "unknown_module") return "Unknown module.";
  return reason;
}

export default function AdminAIConfiguration() {
  const [status, setStatus] = useState(null);
  const [health, setHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [tenants, setTenants] = useState([]);
  const [activeTenant, setActiveTenant] = useState("masci");
  const [tenantCaps, setTenantCaps] = useState(null);
  const [pendingPatch, setPendingPatch] = useState({});
  const [note, setNote] = useState("");
  const [audit, setAudit] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const loadStatus = async () => {
    try {
      const { data } = await api.get("/admin/ai/config/status");
      setStatus(data);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load AI status"));
    }
  };

  const loadHealth = async (opts = { force: false }) => {
    setHealthLoading(true);
    try {
      const url = opts.force ? "/ai/health/refresh" : "/ai/health";
      const { data } = opts.force ? await api.post(url) : await api.get(url);
      setHealth(data);
    } catch (e) {
      setHealth({ error: operationalError(e, "Failed to load AI health") });
    } finally {
      setHealthLoading(false);
    }
  };

  const loadTenants = async () => {
    try {
      const { data } = await api.get("/admin/ai/tenants");
      setTenants(data.tenants || []);
    } catch (e) {
      toast.error(operationalError(e, "Failed to load tenants"));
    }
  };

  const loadTenantCaps = async (tid) => {
    try {
      const { data } = await api.get(`/admin/ai/tenants/${encodeURIComponent(tid)}/capabilities`);
      setTenantCaps(data);
      setPendingPatch({});
    } catch (e) {
      toast.error(operationalError(e, "Failed to load tenant capabilities"));
    }
  };

  const loadAudit = async (tid) => {
    try {
      const { data } = await api.get(`/admin/ai/tenants/${encodeURIComponent(tid)}/audit`);
      setAudit(data.entries || []);
    } catch {
      setAudit([]);
    }
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      await Promise.all([loadStatus(), loadTenants(), loadHealth({ force: false })]);
      setLoading(false);
    })();
  }, []);

  useEffect(() => {
    if (!activeTenant) return;
    loadTenantCaps(activeTenant);
    loadAudit(activeTenant);
  }, [activeTenant]);

  const effective = useMemo(() => {
    const base = tenantCaps?.overrides || {};
    return { ...base, ...pendingPatch };
  }, [tenantCaps, pendingPatch]);

  const hasChanges = Object.keys(pendingPatch).length > 0;

  const setField = (field, value) => {
    setPendingPatch((prev) => ({ ...prev, [field]: value }));
  };

  const save = async () => {
    if (!hasChanges) return;
    setSaving(true);
    try {
      const payload = { ...pendingPatch };
      if (note.trim()) payload.note = note.trim();
      const { data } = await api.put(
        `/admin/ai/tenants/${encodeURIComponent(activeTenant)}/capabilities`,
        payload,
      );
      setTenantCaps((prev) => ({
        ...(prev || {}),
        overrides: data.overrides,
        modules: data.modules,
        has_override_doc: true,
      }));
      setPendingPatch({});
      setNote("");
      await Promise.all([loadTenants(), loadAudit(activeTenant)]);
      toast.success("Tenant AI settings saved.");
    } catch (e) {
      toast.error(operationalError(e, "Failed to save tenant settings"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <LegacyAdminModernShell
      title="AI Configuration"
      subtitle="Optional intelligence · tenant AI switchboard."
      breadcrumb={[
        { label: "AI Operations", to: "/admin/ai-operations" },
        { label: "AI Configuration" },
      ]}
      testidPrefix="admin-ai-configuration"
    >
      <div className="max-w-7xl mx-auto space-y-6" data-testid="admin-ai-configuration-page">
        {/* ── Header ─────────────────────────────────────────── */}
        <div className="bg-white border border-slate-200 rounded-md p-5 flex items-start gap-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-indigo-700 text-white shrink-0">
            <Sparkles className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
              AI-ADMIN-001 · Optional Intelligence Controls
            </span>
            <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
              AI Configuration
            </h1>
            <p className="text-sm text-slate-600 mt-1 leading-relaxed">
              Manage AI availability per tenant and per module. AI is
              optional — the platform runs 100% with every switch off.
              Field users see no AI chrome regardless of these settings.
            </p>
            <div className="mt-2 inline-flex items-center gap-1.5 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-md px-2 py-1">
              <KeyRound className="w-3.5 h-3.5" />
              API keys are managed in <span className="font-semibold">Emergent Secrets</span>.
              Keys are never displayed here.
            </div>
          </div>
          <Button
            onClick={() => Promise.all([loadStatus(), loadTenantCaps(activeTenant), loadAudit(activeTenant)])}
            variant="outline"
            size="sm"
            data-testid="admin-ai-refresh"
            disabled={loading}
          >
            <RefreshCcw className="w-3.5 h-3.5 mr-1.5" />
            Refresh
          </Button>
        </div>

        {loading && (
          <div className="flex items-center gap-2 text-slate-600 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading AI configuration…
          </div>
        )}

        {/* ── Section 1: System Status ──────────────────────── */}
        <section className="bg-white border border-slate-200 rounded-md p-5" data-testid="admin-ai-system-status">
          <SectionHeader icon={Shield} label="System Status" desc="Deployment-wide switchboard state." />
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mt-3">
            <SysCard
              label="AI Gateway"
              value={status?.gateway_enabled ? "Enabled" : "Disabled"}
              tone={status?.gateway_enabled ? "emerald" : "slate"}
              testid="admin-ai-gateway-status"
            />
            {PROVIDER_META.map(({ key, label, icon: Icon }) => {
              const p = status?.providers?.[key];
              const s = providerStatus(p);
              return (
                <SysCard
                  key={key}
                  Icon={Icon}
                  label={label}
                  value={s.label}
                  tone={s.tone}
                  testid={`admin-ai-provider-${key}`}
                />
              );
            })}
            <SysCard
              label="Failover"
              value={status?.transport?.failover_enabled ? "Enabled" : "Disabled"}
              tone={status?.transport?.failover_enabled ? "emerald" : "slate"}
              testid="admin-ai-failover-status"
            />
          </div>
        </section>

        {/* ── Section 1B: Live AI Health (real provider pings) ── */}
        <AIHealthCard
          health={health}
          loading={healthLoading}
          onRefresh={() => loadHealth({ force: true })}
        />

        {/* ── Section 2: Provider Routing (read-only) ───────── */}
        <section className="bg-white border border-slate-200 rounded-md p-5" data-testid="admin-ai-routing">
          <SectionHeader
            icon={Cpu}
            label="Provider Routing"
            desc="Deployment defaults. Editable via Emergent Secrets. Read-only here."
          />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-3 text-sm">
            <RoField label="Default text provider" value={status?.default_provider} />
            <RoField label="Default text model" value={status?.default_text_model || "—"} />
            <RoField label="Default vision provider" value={status?.default_vision_provider || "—"} />
            <RoField label="Default vision model" value={status?.default_vision_model || "—"} />
            <RoField label="Timeout" value={status ? `${status.transport?.timeout_ms} ms` : "—"} />
            <RoField label="Max retries" value={status?.transport?.max_retries ?? "—"} />
            <RoField
              label="Selected provider"
              value={status?.resolved_selected_provider || "—"}
            />
            <RoField
              label="Fallback provider"
              value={status?.resolved_fallback_provider || "—"}
            />
          </div>
        </section>

        {/* ── Section 3: Tenant selector ────────────────────── */}
        <section className="bg-white border border-slate-200 rounded-md p-5" data-testid="admin-ai-tenants">
          <SectionHeader icon={Users} label="Tenant" desc="Choose a tenant to configure AI capabilities." />
          <div className="mt-3 flex flex-wrap gap-2">
            {tenants.map((t) => {
              const active = t.tenant_id === activeTenant;
              return (
                <button
                  key={t.tenant_id}
                  data-testid={`admin-ai-tenant-btn-${t.tenant_id}`}
                  onClick={() => setActiveTenant(t.tenant_id)}
                  className={`text-left border rounded-md px-3 py-2 transition ${
                    active
                      ? "border-indigo-500 bg-indigo-50 shadow-sm"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <div className="font-semibold text-sm">{t.tenant_name || t.tenant_id}</div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    <span className="font-mono">{t.tenant_id}</span>
                    {" · "}
                    <span>{t.tenant_ai_enabled ? "AI on" : "AI off"}</span>
                    {!t.has_override_doc && <span className="ml-1">(default)</span>}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* ── Section 4: Tenant AI Enablement ──────────────── */}
        <section className="bg-white border border-slate-200 rounded-md p-5" data-testid="admin-ai-tenant-toggles">
          <SectionHeader
            icon={Sparkles}
            label={`Tenant AI Enablement · ${tenantCaps?.tenant_name || activeTenant}`}
            desc="Master envelope + per-module toggles. Deployment gates dominate — a module shows a reason when it can't be enabled."
          />
          <div className="mt-4">
            <ToggleRow
              testid="admin-ai-toggle-master"
              label="AI enabled for this tenant"
              desc="Master switch. When off, every module for this tenant is off."
              enabled={!!effective.tenant_ai_enabled}
              onChange={(v) => setField("tenant_ai_enabled", v)}
            />
          </div>
          <div className="mt-3 grid grid-cols-1 lg:grid-cols-2 gap-3">
            {MODULE_META.map(({ key, field, label, desc }) => {
              const mod = tenantCaps?.modules?.[key];
              const disabled = !effective.tenant_ai_enabled;
              return (
                <ToggleRow
                  key={key}
                  testid={`admin-ai-toggle-${key}`}
                  label={label}
                  desc={desc}
                  enabled={!!effective[field]}
                  onChange={(v) => setField(field, v)}
                  reasonDisabled={
                    mod && !mod.enabled && effective[field]
                      ? humanReason(mod.reason_disabled)
                      : null
                  }
                  greyed={disabled}
                />
              );
            })}
          </div>
          <div className="mt-4">
            <Label htmlFor="admin-ai-note" className="text-xs font-mono uppercase tracking-wider text-slate-600">
              Change note (optional, recorded in audit)
            </Label>
            <Textarea
              id="admin-ai-note"
              data-testid="admin-ai-change-note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. Enabling Photo Intelligence for pilot on 2026-02-14."
              className="mt-1"
              rows={2}
            />
          </div>
          <div className="mt-4 flex items-center justify-between">
            <div className="text-xs text-slate-500">
              {hasChanges
                ? `${Object.keys(pendingPatch).length} unsaved change${Object.keys(pendingPatch).length === 1 ? "" : "s"}.`
                : "No pending changes."}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setPendingPatch({});
                  setNote("");
                }}
                disabled={!hasChanges || saving}
                data-testid="admin-ai-discard"
              >
                Discard
              </Button>
              <Button
                size="sm"
                onClick={save}
                disabled={!hasChanges || saving}
                data-testid="admin-ai-save"
              >
                {saving ? <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Save className="w-3.5 h-3.5 mr-1.5" />}
                Save changes
              </Button>
            </div>
          </div>
        </section>

        {/* ── Section 5: Disabled Mode Proof ────────────────── */}
        <section className="bg-white border border-slate-200 rounded-md p-5" data-testid="admin-ai-disabled-mode-proof">
          <SectionHeader
            icon={Info}
            label="Disabled-Mode Guarantees"
            desc="Locked invariants — always true regardless of AI state."
          />
          <ul className="mt-3 grid grid-cols-1 lg:grid-cols-2 gap-2 text-sm">
            <ProofRow>Daily Reports submit without AI.</ProofRow>
            <ProofRow>ODS spine emits facts without AI.</ProofRow>
            <ProofRow>PM &amp; Admin dashboards render deterministic data.</ProofRow>
            <ProofRow>PDFs, HR, Safety, Equipment, Photos untouched by AI state.</ProofRow>
            <ProofRow>Field UI is byte-identical whether AI is on or off.</ProofRow>
            <ProofRow>Provider API keys never appear in this UI.</ProofRow>
          </ul>
        </section>

        {/* ── Section 6: Audit Log ─────────────────────────── */}
        <section className="bg-white border border-slate-200 rounded-md p-5" data-testid="admin-ai-audit-log">
          <SectionHeader
            icon={History}
            label="Audit Log"
            desc={`Recent AI configuration changes for ${activeTenant}.`}
          />
          {audit.length === 0 ? (
            <div className="mt-3 text-sm text-slate-500">No recorded changes yet.</div>
          ) : (
            <div className="mt-3 border border-slate-200 rounded-md divide-y">
              {audit.map((e, i) => (
                <div key={i} className="p-3 text-sm" data-testid={`admin-ai-audit-entry-${i}`}>
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-slate-500">
                        {e.timestamp}
                      </span>
                      <span className="font-semibold">{e.actor}</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {(e.changed_fields || []).map((f) => (
                        <span key={f} className="text-[10px] font-mono uppercase bg-slate-100 border border-slate-200 rounded px-1.5 py-0.5">
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                  {e.note && (
                    <div className="text-xs text-slate-600 mt-1 italic">“{e.note}”</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </LegacyAdminModernShell>
  );
}

// ── Presentational sub-components ────────────────────────────────────
function SectionHeader({ icon: Icon, label, desc }) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-9 h-9 rounded-md bg-slate-900 text-white inline-flex items-center justify-center shrink-0">
        <Icon className="w-4 h-4" />
      </div>
      <div>
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
          Section
        </div>
        <h2 className="font-display text-lg font-black tracking-tight">{label}</h2>
        {desc && <p className="text-xs text-slate-500 mt-0.5">{desc}</p>}
      </div>
    </div>
  );
}

function SysCard({ label, value, tone = "slate", Icon, testid }) {
  return (
    <div className={`border rounded-md p-3 ${TONE_CLS[tone]}`} data-testid={testid}>
      <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider opacity-80">
        {Icon && <Icon className="w-3 h-3" />}
        {label}
      </div>
      <div className="mt-0.5 font-semibold text-sm">{value}</div>
    </div>
  );
}

function RoField({ label, value }) {
  return (
    <div className="border border-slate-200 rounded-md p-3 bg-slate-50/50">
      <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
        {label}
      </div>
      <div className="mt-0.5 font-mono text-sm text-slate-800 truncate">
        {String(value ?? "—")}
      </div>
    </div>
  );
}

function ToggleRow({ label, desc, enabled, onChange, testid, reasonDisabled, greyed }) {
  return (
    <div
      className={`border rounded-md p-3 flex items-start gap-3 transition ${
        greyed ? "border-slate-200 bg-slate-50/60 opacity-60" : "border-slate-200 bg-white"
      }`}
    >
      <Switch
        checked={!!enabled}
        onCheckedChange={onChange}
        data-testid={testid}
      />
      <div className="flex-1">
        <div className="font-semibold text-sm">{label}</div>
        {desc && <div className="text-xs text-slate-500 mt-0.5">{desc}</div>}
        {reasonDisabled && (
          <div className="mt-1.5 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-2 py-1 inline-flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            {reasonDisabled}
          </div>
        )}
      </div>
      <StatusBadge tone={enabled ? "emerald" : "slate"} testid={`${testid}-badge`}>
        {enabled ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
        {enabled ? "Enabled" : "Disabled"}
      </StatusBadge>
    </div>
  );
}

function ProofRow({ children }) {
  return (
    <li className="flex items-start gap-2">
      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
      <span className="text-slate-700">{children}</span>
    </li>
  );
}


// ── Live AI Health card ────────────────────────────────────
// Runs a real ping against every registered provider so silent
// failures (401, quota, network) are visible before the field
// team hits a broken summary in the daily report.
const HEALTH_TONE = {
  ok: "emerald",
  degraded: "amber",
  not_wired: "slate",
  unauthorized: "rose",
  no_key: "rose",
  missing_adapter: "rose",
  error: "rose",
  timeout: "rose",
};

function AIHealthCard({ health, loading, onRefresh }) {
  const providers = health?.providers || [];
  const summary = health?.summary || { ok: 0, degraded: 0, failed: 0, total: 0 };
  const banner = summary.failed > 0
    ? { tone: "rose", text: `${summary.failed} provider(s) failed — AI summary will fall back to deterministic template.` }
    : summary.ok === 0
    ? { tone: "amber", text: "No provider is fully green. AI summary quality may degrade." }
    : { tone: "emerald", text: `${summary.ok}/${summary.total} providers healthy. Failover ready.` };

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-5"
      data-testid="admin-ai-health"
    >
      <div className="flex items-start justify-between gap-3">
        <SectionHeader
          icon={Sparkles}
          label="AI Health (Live Ping)"
          desc="Real request against each provider — surfaces 401 / quota / timeout that would otherwise silently drop to the deterministic summary."
        />
        <Button
          onClick={onRefresh}
          variant="outline"
          size="sm"
          disabled={loading}
          data-testid="admin-ai-health-refresh"
        >
          {loading ? (
            <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
          ) : (
            <RefreshCcw className="w-3.5 h-3.5 mr-1.5" />
          )}
          {loading ? "Pinging…" : "Ping now"}
        </Button>
      </div>

      <div
        className={`mt-3 px-3 py-2 rounded-md border text-sm ${TONE_CLS[banner.tone]}`}
        data-testid="admin-ai-health-banner"
      >
        {banner.text}
      </div>

      {health?.error && (
        <div className="mt-3 p-3 rounded-md border border-rose-200 bg-rose-50 text-rose-800 text-sm" role="alert">
          {String(health.error)}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3">
        {providers.map((p) => {
          const tone = HEALTH_TONE[p.status] || "slate";
          return (
            <div
              key={p.name}
              className={`border rounded-md p-3 ${TONE_CLS[tone]}`}
              data-testid={`admin-ai-health-provider-${p.name}`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="font-semibold text-sm capitalize">{p.name}</div>
                <StatusBadge tone={tone} testid={`admin-ai-health-status-${p.name}`}>
                  {p.status}
                </StatusBadge>
              </div>
              <dl className="mt-2 space-y-1 text-xs">
                <div className="flex justify-between">
                  <dt className="text-slate-600">Key present</dt>
                  <dd className="font-mono">{p.key_present ? "yes" : "no"}</dd>
                </div>
                {p.model && (
                  <div className="flex justify-between">
                    <dt className="text-slate-600">Model</dt>
                    <dd className="font-mono truncate max-w-[10rem]" title={p.model}>{p.model}</dd>
                  </div>
                )}
                {typeof p.latency_ms === "number" && (
                  <div className="flex justify-between">
                    <dt className="text-slate-600">Latency</dt>
                    <dd className="font-mono">{p.latency_ms} ms</dd>
                  </div>
                )}
                {p.reason && (
                  <div className="flex justify-between">
                    <dt className="text-slate-600">Reason</dt>
                    <dd className="font-mono truncate max-w-[10rem]" title={p.reason}>{p.reason}</dd>
                  </div>
                )}
              </dl>
              {p.detail && (
                <div className="mt-2 text-[11px] text-rose-800/90 bg-rose-100/60 border border-rose-200 rounded px-2 py-1 truncate" title={p.detail}>
                  {p.detail}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {health?.primary_route && (
        <div className="mt-3 text-xs text-slate-500">
          Primary route: <span className="font-mono">{health.primary_route.provider} · {health.primary_route.model}</span>
          {" · "}
          Failover order: <span className="font-mono">anthropic → openai → google</span>
          {" · "}
          Last check: <span className="font-mono">{formatPlatformTimeOnly(health.generated_at)}</span>
        </div>
      )}
    </section>
  );
}
