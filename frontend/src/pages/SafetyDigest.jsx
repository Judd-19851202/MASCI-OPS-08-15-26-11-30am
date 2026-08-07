// SafetyDigestPanel — preview + manually send the weekly Monday digest.
// The cron also runs automatically, but Safety can hit "Send now" to
// trigger a fresh send at any time, or just review what the digest
// would contain right now (KPIs + top open CAs).
import React, { useEffect, useState } from "react";
import axios from "axios";
import { Mail, Loader2, RefreshCcw, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import SafetyShell from "@/components/SafetyShell";
import { EmptyState, LoadingState } from "@/components/ui/PortalStates";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: buildScopedPortalAuthHeaders(["safety"]) });

export default function SafetyDigest() {
  const { t } = useT();
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [toEmail, setToEmail] = useState("safety@mascigc.com");

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/safety/digest/preview`, auth());
      setPreview(r.data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load digest");
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { refresh(); }, []);

  const send = async () => {
    if (!toEmail.trim()) { toast.error("Enter a recipient email"); return; }
    setSending(true);
    try {
      const r = await axios.post(
        `${API}/safety/digest/send?to_email=${encodeURIComponent(toEmail.trim())}`,
        {},
        auth(),
      );
      if (r.data?.sent) {
        toast.success(`Digest sent to ${toEmail}`);
      } else {
        toast.warning("Digest computed — email delivery is disabled in this environment. Contact your administrator if you need the digest emailed.");
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Send failed");
    } finally {
      setSending(false);
    }
  };

  const k = preview?.payload?.kpis || {};

  return (
    <SafetyShell title="Weekly Safety Digest" kicker="SAFETY · WEEKLY DIGEST">
      <div className="flex flex-col sm:flex-row gap-3 mb-5 items-start sm:items-center justify-between">
        <p className="text-slate-600 text-sm max-w-2xl leading-relaxed">
          {t("Weekly Monday-morning digest emailed to safety@mascigc.com (configurable). KPIs cover open CAs, overdue CAs, 7-day incident + meeting counts, fire-extinguisher overdue counts, training expirations, and the top 5 oldest open corrective actions.")}
        </p>
        <Button onClick={refresh} variant="outline" disabled={loading} className="h-10" data-testid="safety-digest-refresh">
          {loading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <RefreshCcw className="w-4 h-4 mr-1" />}
          {t("Refresh")}
        </Button>
      </div>

      <div className="bg-white border border-slate-200 rounded-md p-5 mb-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-cyan-700 font-bold mb-3">
          {t("Send a digest now")}
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[260px]">
            <Label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">{t("Recipient")}</Label>
            <Input type="email" value={toEmail} onChange={(e) => setToEmail(e.target.value)} className="h-10 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-cyan-700 mt-1" data-testid="safety-digest-to" />
          </div>
          <Button onClick={send} disabled={sending} className="bg-cyan-700 hover:bg-cyan-800 text-white border-b-2 border-cyan-900 font-bold uppercase tracking-wide h-10" data-testid="safety-digest-send">
            {sending ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <Send className="w-4 h-4 mr-1" />}
            {t("Send now")}
          </Button>
        </div>
      </div>

      <h2 className="font-display text-xl font-black mb-3">{t("This week's update")}</h2>
      {loading ? (
        <LoadingState label={t("Loading…")} testId="safety-digest-loading" />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mb-6">
            <KPI testId="digest-kpi-open-cas" label="Open CAs" value={k.open_corrective_actions ?? 0} accent="cyan" />
            <KPI testId="digest-kpi-overdue-cas" label="Overdue CAs" value={k.overdue_corrective_actions ?? 0} accent="red" />
            <KPI testId="digest-kpi-incidents-7d" label="Incidents · 7d" value={k.incidents_last_7d ?? 0} accent="amber" />
            <KPI testId="digest-kpi-meetings-7d" label="Meetings · 7d" value={k.meetings_last_7d ?? 0} accent="emerald" />
            <KPI testId="digest-kpi-fe-overdue" label="Fire Ext · Overdue" value={k.fire_extinguishers_overdue ?? 0} accent="red" />
            <KPI testId="digest-kpi-training-expired" label="Training Expired" value={k.training_expired ?? 0} accent="red" />
            <KPI testId="digest-kpi-training-expiring" label="Expiring 30d" value={k.training_expiring_30d ?? 0} accent="amber" />
          </div>

          <h3 className="font-display text-lg font-black mb-2">{t("Top open corrective actions")}</h3>
          {!preview?.payload?.top_open_corrective_actions?.length ? (
            <EmptyState
              icon={Mail}
              title={t("Inbox zero")}
              body={t("No open corrective actions right now.")}
              testId="safety-digest-empty"
            />
          ) : (
            <div className="overflow-x-auto" data-testid="safety-digest-top-list">
              <table className="w-full text-sm">
                <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
                  <tr>
                    <th className="text-left px-3 py-2">Title</th>
                    <th className="text-left px-3 py-2">Status</th>
                    <th className="text-left px-3 py-2">Priority</th>
                    <th className="text-left px-3 py-2">Project</th>
                    <th className="text-left px-3 py-2">Due</th>
                    <th className="text-left px-3 py-2">Assignee</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.payload.top_open_corrective_actions.map((ca, i) => (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="px-3 py-2 font-semibold">{ca.title}</td>
                      <td className="px-3 py-2">{ca.status}</td>
                      <td className="px-3 py-2">{ca.priority || "—"}</td>
                      <td className="px-3 py-2">{ca.project_number || "—"}</td>
                      <td className="px-3 py-2">{ca.due_date || "—"}</td>
                      <td className="px-3 py-2">{ca.assigned_to_name || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </SafetyShell>
  );
}

function KPI({ label, value, accent = "cyan", testId }) {
  const cls = {
    cyan: "border-cyan-700 text-cyan-900",
    red: "border-red-700 text-red-900",
    amber: "border-amber-600 text-amber-900",
    emerald: "border-emerald-700 text-emerald-900",
  }[accent];
  return (
    <div className={`bg-white border-2 ${cls} rounded-md p-4`} data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">{label}</div>
      <div className="font-display text-3xl font-black mt-1 leading-none">{value}</div>
    </div>
  );
}
