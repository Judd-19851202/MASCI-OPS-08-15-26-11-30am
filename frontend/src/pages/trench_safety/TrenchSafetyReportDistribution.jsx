// Trench Safety · Phase 9B · Report Distribution UI
// ─────────────────────────────────────────────────────────────────────
// Subscription manager + Road Plate package installer + Leadership
// digest viewer — all driven by /api/trench-safety/reports/* endpoints
// added in Phase 9B.
import React, { useEffect, useState } from "react";
import {
  Mail, Plus, Trash2, Play, Loader2, Package, FileText, Eye, Send,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

const REPORT_OPTIONS = [
  { id: "executive",             label: "Executive Asset Health" },
  { id: "road-plate",            label: "Road Plate Command" },
  { id: "inspection-compliance", label: "Inspection Compliance" },
  { id: "repair-backlog",        label: "Repair Backlog" },
  { id: "holds",                 label: "Hold Management" },
  { id: "utilization",           label: "Asset Utilization" },
  { id: "missing-data",          label: "Missing Data" },
  { id: "project-assets",        label: "Project Asset" },
  { id: "activity",              label: "Activity & Audit" },
];

function extractErr(e, fb) {
  return e?.response?.data?.detail || e?.message || fb;
}

export function SubscriptionManagerDialog({ open, onOpenChange }) {
  const { t } = useT();
  if (!open) return null;
  return <Inner onOpenChange={onOpenChange} t={t} />;
}

function Inner({ onOpenChange, t }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newForm, setNewForm] = useState({
    name: "", report_id: "executive", frequency: "weekly",
    format: "pdf", recipients: "",
  });
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    try {
      const r = await api.get("/trench-safety/reports/subscriptions");
      setItems(r.data?.items || []);
    } catch { /* swallow */ }
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get("/trench-safety/reports/subscriptions");
        if (!cancelled) setItems(r.data?.items || []);
      } catch { /* swallow */ }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, []);

  async function createSub() {
    if (!newForm.name.trim()) {
      toast.error(t("Subscription name is required."));
      return;
    }
    setBusy(true);
    try {
      const payload = {
        name: newForm.name.trim(),
        report_id: newForm.report_id,
        frequency: newForm.frequency,
        format: newForm.format,
        recipients: newForm.recipients
          .split(/[,\n]/).map((s) => s.trim()).filter(Boolean),
        filters: {},
        enabled: true,
      };
      await api.post("/trench-safety/reports/subscriptions", payload);
      toast.success(t("Subscription created."));
      setNewForm({ name: "", report_id: "executive", frequency: "weekly", format: "pdf", recipients: "" });
      await refresh();
    } catch (e) {
      toast.error(extractErr(e, t("Create failed.")));
    } finally { setBusy(false); }
  }

  async function toggleEnabled(sub) {
    try {
      await api.put(`/trench-safety/reports/subscriptions/${sub.id}`, { enabled: !sub.enabled });
      await refresh();
    } catch (e) { toast.error(extractErr(e, t("Update failed."))); }
  }

  async function runNow(sub) {
    setBusy(true);
    try {
      const r = await api.post(`/trench-safety/reports/subscriptions/${sub.id}/run`);
      const st = r.data?.delivery?.status;
      const n = r.data?.delivery?.recipient_count ?? 0;
      toast.success(`${t("Run complete")} · ${st} · ${n} ${t("recipient(s)")}`);
      await refresh();
    } catch (e) { toast.error(extractErr(e, t("Run failed."))); }
    finally { setBusy(false); }
  }

  async function deleteSub(sub) {
    try {
      await api.delete(`/trench-safety/reports/subscriptions/${sub.id}`);
      toast.success(t("Subscription deleted."));
      await refresh();
    } catch (e) { toast.error(extractErr(e, t("Delete failed."))); }
  }

  async function installRoadPlatePackage() {
    setBusy(true);
    try {
      const r = await api.post("/trench-safety/reports/subscriptions/install-road-plate-package");
      const c = r.data?.created_count ?? 0;
      const s = r.data?.skipped_count ?? 0;
      toast.success(`${t("Road Plate Leadership Package")} · ${c} ${t("installed")} · ${s} ${t("already present")}`);
      await refresh();
    } catch (e) { toast.error(extractErr(e, t("Install failed."))); }
    finally { setBusy(false); }
  }

  return (
    <Dialog open={true} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" data-testid="subscription-manager-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-cyan-700" />
            {t("Report Subscriptions")}
          </DialogTitle>
        </DialogHeader>

        <div className="text-xs text-slate-600 -mt-2">
          {t("Scheduled email delivery of Trench Safety reports through the certified Resend pipeline. Weekly or monthly cadence. CSV / XLSX / PDF format. Manage recipients and filters per subscription.")}
        </div>

        <div className="flex flex-wrap gap-2 mt-2">
          <Button size="sm" variant="outline" onClick={installRoadPlatePackage} disabled={busy} data-testid="install-road-plate-package">
            <Package className="w-3.5 h-3.5 mr-1" /> {t("Install Road Plate Leadership Package")}
          </Button>
        </div>

        {/* New subscription form */}
        <div className="bg-white border border-slate-200 rounded p-3 mt-2" data-testid="sub-new-form">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
            {t("Create Subscription")}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
            <div>
              <Label className="text-[10px] uppercase font-bold">{t("Name")}</Label>
              <Input value={newForm.name} onChange={(e) => setNewForm({ ...newForm, name: e.target.value })} placeholder={t("Weekly Executive · Safety")} data-testid="sub-new-name" />
            </div>
            <div>
              <Label className="text-[10px] uppercase font-bold">{t("Report")}</Label>
              <Select value={newForm.report_id} onValueChange={(v) => setNewForm({ ...newForm, report_id: v })}>
                <SelectTrigger data-testid="sub-new-report"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {REPORT_OPTIONS.map((r) => <SelectItem key={r.id} value={r.id}>{t(r.label)}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-[10px] uppercase font-bold">{t("Frequency")}</Label>
              <Select value={newForm.frequency} onValueChange={(v) => setNewForm({ ...newForm, frequency: v })}>
                <SelectTrigger data-testid="sub-new-frequency"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="weekly">{t("Weekly")}</SelectItem>
                  <SelectItem value="monthly">{t("Monthly")}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-[10px] uppercase font-bold">{t("Format")}</Label>
              <Select value={newForm.format} onValueChange={(v) => setNewForm({ ...newForm, format: v })}>
                <SelectTrigger data-testid="sub-new-format"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="xlsx">XLSX</SelectItem>
                  <SelectItem value="csv">CSV</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-[10px] uppercase font-bold">{t("Recipients (comma)")}</Label>
              <Input value={newForm.recipients} onChange={(e) => setNewForm({ ...newForm, recipients: e.target.value })} placeholder="lead@masci.com, ops@masci.com" data-testid="sub-new-recipients" />
            </div>
          </div>
          <div className="mt-2 flex justify-end">
            <Button onClick={createSub} disabled={busy} className="bg-cyan-700 hover:bg-cyan-800" data-testid="sub-new-save">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : (<><Plus className="w-4 h-4 mr-1" /> {t("Create Subscription")}</>)}
            </Button>
          </div>
        </div>

        {/* Existing subscriptions list */}
        <div className="mt-3" data-testid="sub-list">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold mb-2">
            {t("Active Subscriptions")} · {items.length}
          </div>
          {loading ? (
            <div className="flex items-center gap-2 text-slate-500"><Loader2 className="w-4 h-4 animate-spin" /></div>
          ) : items.length === 0 ? (
            <div className="text-sm italic text-slate-500" data-testid="sub-list-empty">— {t("no subscriptions yet")} —</div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {items.map((s) => (
                <li key={s.id} className="py-2 flex flex-wrap items-center gap-3" data-testid={`sub-row-${s.id}`}>
                  <div className="flex-1 min-w-[200px]">
                    <div className="font-bold text-slate-900">{s.name}</div>
                    <div className="text-xs font-mono text-slate-500">
                      {s.report_id} · {s.frequency} · {s.format.toUpperCase()} · {s.recipients?.length ?? 0} {t("recipient(s)")}
                    </div>
                    <div className="text-[10px] uppercase tracking-[0.12em] text-slate-400 font-mono">
                      {t("Last run")}: {s.last_run_at ? s.last_run_at.slice(0, 16).replace("T", " ") : "—"} · {t("Next due")}: {s.next_due_at?.slice(0, 16).replace("T", " ") || "—"}
                    </div>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => toggleEnabled(s)} data-testid={`sub-toggle-${s.id}`}>
                    {s.enabled ? t("Disable") : t("Enable")}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => runNow(s)} data-testid={`sub-run-${s.id}`}>
                    <Play className="w-3.5 h-3.5 mr-1" /> {t("Run Now")}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => deleteSub(s)} data-testid={`sub-delete-${s.id}`}>
                    <Trash2 className="w-3.5 h-3.5 text-red-700" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} data-testid="sub-close">{t("Close")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function LeadershipDigestButton() {
  const { t } = useT();
  const [open, setOpen] = useState(false);
  const [html, setHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);

  async function loadCurrent() {
    setLoading(true);
    try {
      const r = await api.get("/trench-safety/reports/digest/current");
      const id = r.data?.id;
      if (id) {
        const apiBase = process.env.REACT_APP_BACKEND_URL;
        const url = `${apiBase}/api/trench-safety/reports/digest/${id}/html`;
        const rr = await fetch(url, { credentials: "include" });
        setHtml(await rr.text());
      } else {
        // No history yet — generate one to preview
        const g = await api.post("/trench-safety/reports/digest/generate?send=false");
        const apiBase = process.env.REACT_APP_BACKEND_URL;
        const url = `${apiBase}/api/trench-safety/reports/digest/${g.data.id}/html`;
        const rr = await fetch(url, { credentials: "include" });
        setHtml(await rr.text());
      }
    } catch { /* swallow */ }
    finally { setLoading(false); }
  }

  async function sendNow() {
    setBusy(true);
    try {
      const r = await api.post("/trench-safety/reports/digest/generate?send=true");
      const st = r.data?.delivery?.status;
      const n = r.data?.delivery?.recipient_count ?? 0;
      toast.success(`${t("Digest dispatched")} · ${st} · ${n} ${t("recipient(s)")}`);
    } catch (e) { toast.error(extractErr(e, t("Send failed."))); }
    finally { setBusy(false); }
  }

  return (
    <>
      <Button size="sm" variant="outline" onClick={() => { setOpen(true); loadCurrent(); }} data-testid="open-leadership-digest">
        <FileText className="w-3.5 h-3.5 mr-1" /> {t("Leadership Digest")}
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="digest-viewer-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-cyan-700" />
              {t("Trench Safety Leadership Digest")}
            </DialogTitle>
          </DialogHeader>
          {loading ? (
            <div className="flex items-center gap-2 py-8 text-slate-500"><Loader2 className="w-5 h-5 animate-spin" /></div>
          ) : (
            <iframe
              title="leadership-digest"
              srcDoc={html || "<p>No digest available.</p>"}
              sandbox=""
              data-testid="digest-iframe"
              style={{ width: "100%", height: "60vh", border: "1px solid #e2e8f0", borderRadius: 6 }}
            />
          )}
          <DialogFooter>
            <Button onClick={sendNow} disabled={busy} className="bg-cyan-700 hover:bg-cyan-800" data-testid="digest-send-now">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : (<><Send className="w-4 h-4 mr-1" /> {t("Generate + Send")}</>)}
            </Button>
            <Button variant="outline" onClick={() => setOpen(false)}>{t("Close")}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
