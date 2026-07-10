// AdminDigestConfig.jsx — Iter133. Admin-only config for the Weekly
// Safety Digest. Recipients (comma list) · schedule (weekday+hour UTC) ·
// dashboard URL · enabled toggle · preview · manual send.
import React, { useEffect, useState } from "react";
import {
  Mail, Save, Send, Eye, Loader2, RefreshCcw, ToggleLeft, ToggleRight,
} from "lucide-react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";
// TRACK 27.03 · Canonical local-time formatter.
import { formatPlatformTime, formatPlatformTimeOnly, getPlatformTimezone } from "@/lib/platformTime";

const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function AdminDigestConfig() {
  const [cfg, setCfg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [previewHtml, setPreviewHtml] = useState("");
  const [showPreview, setShowPreview] = useState(false);

  const load = async () => {
    setLoading(true);
    try { setCfg((await api.get("/admin/digest-settings")).data); }
    catch (e) { toast.error(operationalError(e, "Failed to load digest settings")); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const update = (patch) => setCfg((c) => ({ ...c, ...patch }));

  const save = async () => {
    setSaving(true);
    try {
      const r = await api.patch("/admin/digest-settings", {
        enabled: cfg.enabled,
        recipients: cfg.recipients,
        weekday: cfg.weekday,
        hour_utc: cfg.hour_utc,
        dashboard_url: cfg.dashboard_url,
      });
      setCfg(r.data);
      toast.success("Digest settings saved");
    } catch (e) {
      toast.error(operationalError(e, "Save failed"));
    } finally { setSaving(false); }
  };

  const sendNow = async () => {
    if (!window.confirm(
      `Send the weekly digest now to:\n\n${(cfg.recipients || []).join(", ")}\n\nAUTO_EMAIL_REPORTS must be enabled for emails to actually deliver.`
    )) return;
    setSending(true);
    try {
      const r = await api.post("/admin/digest-settings/send-now");
      if (r.data.sent) {
        toast.success(`Sent to ${r.data.sent_to.length} recipient(s)`);
      } else {
        toast.message("Preview-only mode", {
          description: "AUTO_EMAIL_REPORTS is off — payload computed but no email sent. Enable in env to deliver.",
        });
      }
      await load();
    } catch (e) {
      toast.error(operationalError(e, "Send failed"));
    } finally { setSending(false); }
  };

  const preview = async () => {
    try {
      const r = await api.get("/safety/digest/preview");
      setPreviewHtml(r.data?.html || "<p>No preview available.</p>");
      setShowPreview(true);
    } catch (e) {
      toast.error(operationalError(e, "Preview failed"));
    }
  };

  if (loading || !cfg) {
    return (
      <LegacyAdminModernShell
        title="Digest Schedule"
        subtitle="Weekly digest recipients · schedule · preview · send."
        breadcrumb={[
          { label: "Communications", to: "/admin/communications" },
          { label: "Digest Schedule" },
        ]}
        testidPrefix="admin-digest-config"
      >
        <div className="max-w-3xl mx-auto py-12 text-center text-slate-500">
          <Loader2 className="w-6 h-6 animate-spin mx-auto" />
        </div>
      </LegacyAdminModernShell>
    );
  }

  return (
    <LegacyAdminModernShell
      title="Digest Schedule"
      subtitle="Weekly digest recipients · schedule · preview · send."
      breadcrumb={[
        { label: "Communications", to: "/admin/communications" },
        { label: "Digest Schedule" },
      ]}
      testidPrefix="admin-digest-config"
    >
      <div className="max-w-3xl mx-auto" data-testid="admin-digest-config-page">
        <header className="bg-white border border-slate-200 rounded-md p-5 mb-4 flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-cyan-700 text-white shrink-0">
            <Mail className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-cyan-700 font-bold">
              Safety Operations
            </span>
            <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
              Weekly Digest
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              Recipients, schedule, dashboard link, and on-demand send for the weekly safety roll-up.
              DB values override env defaults.
            </p>
          </div>
          <Button onClick={load} variant="outline" size="sm" disabled={loading}>
            <RefreshCcw className="w-3.5 h-3.5" />
          </Button>
        </header>

        {/* Enabled toggle */}
        <div className="bg-white border border-slate-200 rounded-md p-4 mb-3 flex items-center gap-3">
          <div className="flex-1">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 font-bold">Status</div>
            <div className="font-display text-lg font-black">
              {cfg.enabled ? "Enabled" : "Disabled"}
            </div>
            <p className="text-xs text-slate-500">
              {cfg.enabled
                ? "The scheduler will send on the configured day/time. Manual send works too."
                : "The scheduler is paused. Manual send is blocked until you re-enable."}
            </p>
          </div>
          <button
            onClick={() => update({ enabled: !cfg.enabled })}
            className={`inline-flex items-center gap-1 px-3 py-2 rounded-md font-bold text-sm uppercase tracking-wide ${cfg.enabled ? "bg-emerald-700 text-white" : "bg-slate-300 text-slate-700"}`}
            data-testid="digest-enabled-toggle"
          >
            {cfg.enabled ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
            {cfg.enabled ? "On" : "Off"}
          </button>
        </div>

        {/* Recipients */}
        <div className="bg-white border border-slate-200 rounded-md p-4 mb-3">
          <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">
            Recipients (comma-separated)
          </Label>
          <Input
            className="mt-2 h-10 border-2 font-mono"
            value={(cfg.recipients || []).join(", ")}
            onChange={(e) => update({ recipients: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })}
            placeholder="alerts@yourcompany.com, ops@yourcompany.com"
            data-testid="digest-recipients"
          />
          <p className="text-[11px] text-slate-500 mt-1 font-mono">
            {(cfg.recipients || []).length} recipient(s) configured
          </p>
        </div>

        {/* Schedule */}
        <div className="bg-white border border-slate-200 rounded-md p-4 mb-3 grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Weekday</Label>
            <Select value={String(cfg.weekday)} onValueChange={(v) => update({ weekday: parseInt(v, 10) })}>
              <SelectTrigger className="h-10 mt-2 border-2" data-testid="digest-weekday">
                <SelectValue placeholder="Weekday" />
              </SelectTrigger>
              <SelectContent>
                {WEEKDAYS.map((w, i) => <SelectItem key={i} value={String(i)}>{w}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Hour (UTC · scheduler)</Label>
            <Input
              type="number"
              min={0}
              max={23}
              value={cfg.hour_utc}
              onChange={(e) => update({ hour_utc: Math.max(0, Math.min(23, parseInt(e.target.value || "0", 10))) })}
              className="h-10 mt-2 border-2"
              data-testid="digest-hour"
            />
            <p className="text-[10px] text-slate-500 mt-1 font-mono">
              {/* TRACK 27.03 · Render the scheduled wall-clock
                  in the current operator's local zone via the canonical
                  formatter — no hardcoded Florida timezone. `hour_utc`
                  is the backend cron field; the label above is the
                  API contract, the value below is the operator preview. */}
              Runs at{" "}
              {(() => {
                const d = new Date();
                d.setUTCHours(cfg.hour_utc || 0, 0, 0, 0);
                return `${formatPlatformTimeOnly(d)} ${getPlatformTimezone()}`;
              })()}
            </p>
          </div>
        </div>

        {/* Dashboard URL */}
        <div className="bg-white border border-slate-200 rounded-md p-4 mb-3">
          <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">Dashboard URL</Label>
          <Input
            className="mt-2 h-10 border-2 font-mono"
            value={cfg.dashboard_url || ""}
            onChange={(e) => update({ dashboard_url: e.target.value })}
            data-testid="digest-dashboard-url"
          />
        </div>

        {/* Last run */}
        {cfg.last_run && (
          <div className="bg-slate-50 border border-slate-200 rounded-md p-3 mb-3 text-xs font-mono">
            <strong className="uppercase tracking-[0.15em] text-slate-600">Last run</strong>:{" "}
            {formatPlatformTime(cfg.last_run.at)} ·{" "}
            <span className={cfg.last_run.sent_to?.length ? "text-emerald-700" : "text-amber-700"}>
              {cfg.last_run.sent_to?.length ? `sent to ${cfg.last_run.sent_to.length}` : "preview-only"}
            </span>
            {cfg.last_run.errors?.length > 0 && (
              <span className="text-red-700"> · {cfg.last_run.errors.length} error(s)</span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          <Button onClick={save} disabled={saving} className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="digest-save">
            {saving ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Save className="w-3.5 h-3.5 mr-1" />} Save
          </Button>
          <Button onClick={preview} variant="outline" data-testid="digest-preview">
            <Eye className="w-3.5 h-3.5 mr-1" /> Preview
          </Button>
          <Button onClick={sendNow} disabled={sending || !cfg.enabled} className="bg-cyan-700 hover:bg-cyan-800 text-white" data-testid="digest-send-now">
            {sending ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Send className="w-3.5 h-3.5 mr-1" />} Send Now
          </Button>
        </div>

        {showPreview && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowPreview(false)}>
            <div className="bg-white rounded-md max-w-2xl w-full max-h-[80vh] overflow-y-auto p-4" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-display font-black text-lg">Digest Preview</h2>
                <Button size="sm" variant="outline" onClick={() => setShowPreview(false)}>Close</Button>
              </div>
              <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
            </div>
          </div>
        )}
      </div>
    </LegacyAdminModernShell>
  );
}
