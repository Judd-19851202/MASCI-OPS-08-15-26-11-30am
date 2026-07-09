/**
 * <EmailRoutingV2Panel>
 *
 * Track 15.66 Wave 2 — manages the 19 logical routes from the
 * `email_routes` collection (per-tenant, DB-first, audit-logged).
 * Sits alongside the existing AdminEmailRoutingPanel so both the legacy
 * 6-key surface and the new 19-route surface remain editable until the
 * legacy keys are deprecated.
 *
 * Backed by:
 *   GET    /api/admin/email-routing/v2/routes
 *   GET    /api/admin/email-routing/v2/routes/{key}
 *   PUT    /api/admin/email-routing/v2/routes/{key}
 *   POST   /api/admin/email-routing/v2/routes/{key}/test
 *   GET    /api/admin/email-routing/v2/audit?route_key=&limit=
 */
import React, { useEffect, useState, useMemo } from "react";
import {
  Mail,
  Save,
  Loader2,
  Send,
  ShieldAlert,
  CheckCircle2,
  AlertCircle,
  History,
  X,
  Stethoscope,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { toast } from "sonner";
// TRACK 27.03 · Phase 3 · Canonical local-time formatter.
import { formatPlatformTime } from "@/lib/platformTime";

const SEVERITY_PILL = {
  critical: "bg-rose-100 text-rose-800 border-rose-300",
  warn:     "bg-amber-100 text-amber-800 border-amber-300",
  info:     "bg-sky-100 text-sky-800 border-sky-300",
};

function parseList(text) {
  return (text || "")
    .split(/[,\s]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function formatList(arr) {
  return (arr || []).join(", ");
}

function relTime(iso) {
  if (!iso) return "never";
  try {
    const t = new Date(iso).getTime();
    const diff = Math.max(0, Date.now() - t);
    const s = Math.floor(diff / 1000);
    if (s < 60) return `${s}s ago`;
    const m = Math.floor(s / 60);
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    const d = Math.floor(h / 24);
    return `${d}d ago`;
  } catch {
    return iso;
  }
}

export default function EmailRoutingV2Panel() {
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openKey, setOpenKey] = useState(null);
  const [draft, setDraft] = useState(null);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [auditDrawerKey, setAuditDrawerKey] = useState(null);
  const [auditRows, setAuditRows] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/email-routing/v2/routes");
      setRoutes(r?.data?.routes || []);
    } catch (e) {
      toast.error("Failed to load V2 routes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openEditor = (route) => {
    setOpenKey(route.route_key);
    setDraft({
      to: formatList(route.to),
      cc: formatList(route.cc),
      bcc: formatList(route.bcc),
      enabled: !!route.enabled,
      description: route.description || "",
    });
  };

  const cancelEdit = () => {
    setOpenKey(null);
    setDraft(null);
  };

  const save = async (routeKey) => {
    setSaving(true);
    try {
      const body = {
        to: parseList(draft.to),
        cc: parseList(draft.cc),
        bcc: parseList(draft.bcc),
        enabled: draft.enabled,
        description: draft.description,
      };
      await api.put(`/admin/email-routing/v2/routes/${routeKey}`, body);
      toast.success(`Saved ${routeKey}`);
      await load();
      cancelEdit();
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Save failed";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const sendTest = async (routeKey, { dryRun, testRecipient }) => {
    setTesting(true);
    try {
      const r = await api.post(`/admin/email-routing/v2/routes/${routeKey}/test`, {
        dry_run: !!dryRun,
        test_recipient: testRecipient || null,
      });
      const d = r?.data || {};
      if (d.dry_run) {
        const cnt =
          (d.resolved?.to?.length || 0) +
          (d.resolved?.cc?.length || 0) +
          (d.resolved?.bcc?.length || 0);
        toast.success(`${routeKey} dry-run · resolved ${cnt} recipients · audit row written`);
      } else {
        toast.success(`${routeKey} controlled test sent to ${d.test_recipient}`);
      }
      await load();
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Test failed";
      toast.error(msg);
    } finally {
      setTesting(false);
    }
  };

  const openAuditDrawer = async (routeKey) => {
    setAuditDrawerKey(routeKey);
    setAuditLoading(true);
    setAuditRows([]);
    try {
      const r = await api.get(
        `/admin/email-routing/v2/audit?route_key=${encodeURIComponent(routeKey)}&limit=100`
      );
      setAuditRows(r?.data?.rows || []);
    } catch (e) {
      toast.error("Failed to load audit history");
    } finally {
      setAuditLoading(false);
    }
  };

  // Track 15.67 Phase 3 · Route Health — one-click validation of every
  // route for the active tenant. Dry-run only (no Resend send).
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthReport, setHealthReport] = useState(null);
  const runRouteHealth = async () => {
    setHealthLoading(true);
    try {
      const r = await api.post("/admin/email-routing/v2/route-health");
      setHealthReport(r?.data || null);
      const s = r?.data?.summary || {};
      toast.success(
        `Route health: ${s.green || 0} green · ${s.amber || 0} amber · ${s.red || 0} red`
      );
      await load();
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Route health failed";
      toast.error(msg);
    } finally {
      setHealthLoading(false);
    }
  };

  const grouped = useMemo(() => {
    const g = {};
    for (const r of routes) {
      const cat = r.category || "general";
      if (!g[cat]) g[cat] = [];
      g[cat].push(r);
    }
    return g;
  }, [routes]);

  return (
    <section
      data-testid="email-routing-v2-panel"
      className="rounded-2xl border border-slate-200 bg-white shadow-sm"
    >
      <header className="px-5 py-4 border-b border-slate-200 flex items-center gap-3">
        <div className="flex-1">
          <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <Mail className="h-4 w-4 text-rose-600" />
            Routing V2 · 19 logical routes
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            DB-first routes. Editing here updates the route doc; the
            resolver picks it up within 60 seconds. Critical routes cannot be
            disabled or saved with empty recipients.
          </p>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={runRouteHealth}
          disabled={healthLoading || loading}
          data-testid="v2-route-health-run"
          title="Dry-run every route for this tenant. No emails are sent. Each route gets an audit row."
        >
          {healthLoading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
          ) : (
            <Stethoscope className="h-3.5 w-3.5 mr-1" />
          )}
          Run Route Health
        </Button>
        <span
          data-testid="v2-routes-count"
          className="text-xs px-2 py-0.5 rounded-full border border-slate-200 bg-slate-50 text-slate-700"
        >
          {routes.length} routes
        </span>
      </header>

      {healthReport && (
        <div
          data-testid="v2-route-health-summary"
          className="px-5 py-3 border-b border-slate-200 bg-slate-50/50 flex items-center gap-3 flex-wrap"
        >
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-600">
            Last route health
          </span>
          <span
            data-testid="v2-route-health-green"
            className="text-xs px-2 py-0.5 rounded-full border border-emerald-300 bg-emerald-50 text-emerald-800 font-semibold"
          >
            🟢 {healthReport.summary?.green || 0} green
          </span>
          <span
            data-testid="v2-route-health-amber"
            className="text-xs px-2 py-0.5 rounded-full border border-amber-300 bg-amber-50 text-amber-800 font-semibold"
          >
            🟡 {healthReport.summary?.amber || 0} amber
          </span>
          <span
            data-testid="v2-route-health-red"
            className="text-xs px-2 py-0.5 rounded-full border border-rose-300 bg-rose-50 text-rose-800 font-semibold"
          >
            🔴 {healthReport.summary?.red || 0} red
          </span>
          <span className="text-[11px] text-slate-500">
            Tenant {healthReport.tenant_key} · {healthReport.total || 0} routes ·{" "}
            {formatPlatformTime(healthReport.ts)}
          </span>
          {(healthReport.results || []).some((r) => r.status !== "green") && (
            <details className="basis-full mt-1">
              <summary className="text-[11px] text-slate-600 cursor-pointer font-semibold">
                Show failing routes
              </summary>
              <ul className="mt-1.5 text-[11px] font-mono text-slate-700 space-y-0.5">
                {(healthReport.results || [])
                  .filter((r) => r.status !== "green")
                  .map((r) => (
                    <li key={r.route_key} className="flex items-center gap-2">
                      <span
                        className={
                          r.status === "red"
                            ? "text-rose-700"
                            : "text-amber-700"
                        }
                      >
                        {r.status === "red" ? "🔴" : "🟡"}
                      </span>
                      <span className="font-semibold">{r.route_key}</span>
                      <span className="text-slate-500">— {r.reason}</span>
                    </li>
                  ))}
              </ul>
            </details>
          )}
        </div>
      )}

      {loading ? (
        <div className="p-8 flex items-center justify-center text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin mr-2" /> Loading…
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {Object.entries(grouped).map(([cat, rows]) => (
            <div key={cat} className="px-5 py-4">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-2">
                {cat}
              </div>
              <div className="space-y-2">
                {rows.map((r) => (
                  <RouteRow
                    key={r.route_key}
                    route={r}
                    open={openKey === r.route_key}
                    draft={openKey === r.route_key ? draft : null}
                    onOpen={() => openEditor(r)}
                    onCancel={cancelEdit}
                    onChange={setDraft}
                    onSave={() => save(r.route_key)}
                    onDryRun={() => sendTest(r.route_key, { dryRun: true })}
                    onControlledTest={(addr) =>
                      sendTest(r.route_key, { dryRun: false, testRecipient: addr })
                    }
                    onAudit={() => openAuditDrawer(r.route_key)}
                    saving={saving}
                    testing={testing}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {auditDrawerKey && (
        <AuditDrawer
          routeKey={auditDrawerKey}
          rows={auditRows}
          loading={auditLoading}
          onClose={() => {
            setAuditDrawerKey(null);
            setAuditRows([]);
          }}
        />
      )}
    </section>
  );
}

function RouteRow({
  route,
  open,
  draft,
  onOpen,
  onCancel,
  onChange,
  onSave,
  onDryRun,
  onControlledTest,
  onAudit,
  saving,
  testing,
}) {
  const sev = (route.severity || "info").toLowerCase();
  const sevPill = SEVERITY_PILL[sev] || SEVERITY_PILL.info;
  const [controlledAddr, setControlledAddr] = useState("");
  const summary = route.summary || {};
  const recipCount =
    (route.to?.length || 0) + (route.cc?.length || 0) + (route.bcc?.length || 0);

  return (
    <div
      className={`rounded-xl border ${
        open ? "border-rose-300 ring-1 ring-rose-200" : "border-slate-200"
      } bg-slate-50/50`}
      data-testid={`v2-route-${route.route_key}`}
    >
      <button
        type="button"
        onClick={onOpen}
        className="w-full text-left px-3 py-2.5 flex items-center gap-3 hover:bg-slate-100/60 rounded-xl"
      >
        <span
          className={`text-[10px] px-1.5 py-0.5 rounded-full border font-semibold ${sevPill}`}
        >
          {sev}
        </span>
        {route.critical && (
          <span
            title="Critical route — cannot be disabled or emptied"
            className="text-[10px] px-1.5 py-0.5 rounded-full border bg-rose-50 text-rose-700 border-rose-200 font-semibold inline-flex items-center gap-1"
          >
            <ShieldAlert className="h-3 w-3" /> CRITICAL
          </span>
        )}
        {!route.enabled && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-full border bg-slate-100 text-slate-600 border-slate-200">
            disabled
          </span>
        )}
        <span className="font-mono text-[12px] text-slate-700">{route.route_key}</span>
        <span className="flex-1 text-[12px] text-slate-500 truncate ml-2">
          {route.display_name}
        </span>
        <span className="text-[11px] text-slate-500 whitespace-nowrap">
          {recipCount} recipients
        </span>
        <span className="text-[11px] text-slate-400 whitespace-nowrap">
          tested {relTime(route.last_tested_at)}
        </span>
      </button>

      {open && draft && (
        <div className="px-3 pb-3 pt-1 border-t border-slate-200 space-y-2">
          <p className="text-[11px] text-slate-600">{route.description}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            <FieldList
              label="To"
              value={draft.to}
              testId={`v2-edit-${route.route_key}-to`}
              onChange={(v) => onChange({ ...draft, to: v })}
            />
            <FieldList
              label="CC"
              value={draft.cc}
              testId={`v2-edit-${route.route_key}-cc`}
              onChange={(v) => onChange({ ...draft, cc: v })}
            />
            <FieldList
              label="BCC"
              value={draft.bcc}
              testId={`v2-edit-${route.route_key}-bcc`}
              onChange={(v) => onChange({ ...draft, bcc: v })}
            />
          </div>
          {!route.critical && (
            <label className="text-[12px] text-slate-700 inline-flex items-center gap-2">
              <input
                type="checkbox"
                checked={!!draft.enabled}
                onChange={(e) =>
                  onChange({ ...draft, enabled: e.target.checked })
                }
                data-testid={`v2-edit-${route.route_key}-enabled`}
              />
              Enabled
            </label>
          )}
          <div className="flex flex-wrap gap-2 pt-1 items-center">
            <Button
              size="sm"
              onClick={onSave}
              disabled={saving}
              data-testid={`v2-save-${route.route_key}`}
            >
              {saving ? (
                <Loader2 className="h-3 w-3 animate-spin mr-1" />
              ) : (
                <Save className="h-3 w-3 mr-1" />
              )}
              Save
            </Button>
            <Button size="sm" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onDryRun}
              disabled={testing}
              data-testid={`v2-dryrun-${route.route_key}`}
            >
              <CheckCircle2 className="h-3 w-3 mr-1" /> Dry-run test
            </Button>
            <Input
              type="email"
              placeholder="controlled test inbox (you@yourcompany.com)"
              value={controlledAddr}
              onChange={(e) => setControlledAddr(e.target.value)}
              className="h-8 text-xs flex-1 min-w-[200px]"
              data-testid={`v2-controlled-addr-${route.route_key}`}
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                if (!controlledAddr || !controlledAddr.includes("@")) {
                  toast.error("Enter a valid test inbox address");
                  return;
                }
                onControlledTest(controlledAddr);
              }}
              disabled={testing || !controlledAddr}
              data-testid={`v2-controlled-send-${route.route_key}`}
            >
              <Send className="h-3 w-3 mr-1" /> Controlled send
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={onAudit}
              data-testid={`v2-audit-${route.route_key}`}
            >
              <History className="h-3 w-3 mr-1" /> Audit
            </Button>
          </div>
          {summary.last_failure_at && (
            <div
              className="text-[11px] text-rose-700 bg-rose-50 border border-rose-200 rounded px-2 py-1 inline-flex items-center gap-1"
              data-testid={`v2-last-failure-${route.route_key}`}
            >
              <AlertCircle className="h-3 w-3" /> Last failure{" "}
              {relTime(summary.last_failure_at)}: {summary.last_failure_error || "—"}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function FieldList({ label, value, testId, onChange }) {
  return (
    <label className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider">
      {label}
      <textarea
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        rows={2}
        placeholder="one@yourcompany.com, two@yourcompany.com"
        className="mt-1 w-full font-mono text-[12px] px-2 py-1.5 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-rose-400 bg-white text-slate-800 lowercase"
        data-testid={testId}
      />
    </label>
  );
}

function AuditDrawer({ routeKey, rows, loading, onClose }) {
  return (
    <div
      className="fixed inset-0 z-50 bg-black/30 flex items-end md:items-center md:justify-end"
      onClick={onClose}
      data-testid="v2-audit-drawer"
    >
      <div
        className="bg-white w-full md:w-[640px] md:h-[80vh] rounded-t-2xl md:rounded-l-2xl md:rounded-tr-none shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="px-4 py-3 border-b border-slate-200 flex items-center gap-2">
          <History className="h-4 w-4 text-slate-700" />
          <div className="flex-1">
            <h3 className="font-semibold text-sm text-slate-900">
              Audit · <span className="font-mono">{routeKey}</span>
            </h3>
            <p className="text-[11px] text-slate-500">
              Last 100 resolutions. &quot;I never got the email&quot; → answer in 15 seconds.
            </p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={onClose}
            data-testid="v2-audit-drawer-close"
          >
            <X className="h-4 w-4" />
          </Button>
        </header>
        <div className="flex-1 overflow-auto p-2">
          {loading ? (
            <div className="p-8 flex items-center justify-center text-slate-500">
              <Loader2 className="h-4 w-4 animate-spin mr-2" /> Loading…
            </div>
          ) : rows.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500">
              No audit rows for this route yet. Run a dry-run test to create one.
            </div>
          ) : (
            <table className="w-full text-[11px]">
              <thead className="text-slate-500 sticky top-0 bg-white">
                <tr>
                  <th className="text-left px-2 py-1">When</th>
                  <th className="text-left px-2 py-1">Source</th>
                  <th className="text-left px-2 py-1">Status</th>
                  <th className="text-right px-2 py-1">To/CC/BCC</th>
                  <th className="text-left px-2 py-1">Module</th>
                  <th className="text-left px-2 py-1">Resend ID</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-2 py-1 font-mono text-slate-700">
                      {formatPlatformTime(r.ts)}
                    </td>
                    <td className="px-2 py-1">{r.source}</td>
                    <td className="px-2 py-1">
                      <span
                        className={
                          r.status === "failed" || r.status === "error"
                            ? "text-rose-700 font-semibold"
                            : r.status === "dry_run"
                            ? "text-sky-700"
                            : "text-emerald-700"
                        }
                      >
                        {r.status}
                        {r.dry_run ? " (dry)" : ""}
                      </span>
                    </td>
                    <td className="px-2 py-1 text-right font-mono text-slate-700">
                      {r.resolved_to_count}/{r.resolved_cc_count}/{r.resolved_bcc_count}
                    </td>
                    <td className="px-2 py-1 text-slate-600">{r.calling_module || "—"}</td>
                    <td className="px-2 py-1 font-mono text-slate-500 truncate max-w-[120px]">
                      {r.resend_message_id || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
