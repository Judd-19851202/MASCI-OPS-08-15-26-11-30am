// HR Time Off Requests dashboard (iter101)
//
// Lists every time_off_request from field_leadership_records — supervisor-filed
// OR public-link-filed by office staff. HR can approve / deny / mark "need info"
// and can generate a public form link for office staff who don't have a
// platform login.

import React from "react";
import { Link } from "react-router-dom";
import {
  CalendarOff, CheckCircle2, XCircle, AlertCircle, Send, Copy,
  FileText, Filter, Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import BackLink from "@/components/BackLink";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { getHrToken } from "@/lib/hrAuth";
import { HelpTipBlock } from "@/components/HelpTip";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_STYLES = {
  pending:   { bg: "bg-amber-100 text-amber-900 border-amber-400", label: "Pending HR" },
  approved:  { bg: "bg-emerald-100 text-emerald-900 border-emerald-500", label: "Approved" },
  denied:    { bg: "bg-red-100 text-red-900 border-red-500", label: "Denied" },
  need_info: { bg: "bg-orange-100 text-orange-900 border-orange-500", label: "Need Info" },
};

export default function HrTimeOff() {
  const { t } = useT();
  const [rows, setRows] = React.useState([]);
  const [stats, setStats] = React.useState({});
  const [statusFilter, setStatusFilter] = React.useState("all");
  const [employee, setEmployee] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [active, setActive] = React.useState(null); // record open in decision dialog

  const headers = React.useCallback(() => ({
    "X-HR-Token": getHrToken() || "",
    "Content-Type": "application/json",
  }), []);

  const refresh = React.useCallback(async () => {
    setBusy(true);
    try {
      const qs = new URLSearchParams();
      if (statusFilter !== "all") qs.set("status", statusFilter);
      if (employee.trim()) qs.set("employee", employee.trim());
      const [listResp, statsResp] = await Promise.all([
        fetch(`${API}/field-leadership/time-off?${qs.toString()}`, { headers: headers() }),
        fetch(`${API}/field-leadership/time-off/stats`, { headers: headers() }),
      ]);
      if (listResp.ok) {
        const d = await listResp.json();
        setRows(d.items || []);
      }
      if (statsResp.ok) setStats(await statsResp.json());
    } catch (e) {
      toast.error(t("Could not load time-off list. Try again."));
    } finally {
      setBusy(false);
    }
  }, [statusFilter, employee, headers, t]);

  React.useEffect(() => { refresh(); }, [refresh]);

  return (
    <div className="min-h-screen blueprint-bg pb-16" data-testid="hr-time-off-page">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-cyan-700">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <BackLink to="/hr" label={t("HR Hub")} testId="time-off-back" />
          <MasciLogo variant="mark" size="md" className="hidden sm:block" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-8 py-4 sm:py-6">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="min-w-0">
            <div className="font-mono text-[10px] sm:text-xs uppercase tracking-[0.2em] text-cyan-700 font-bold">
              <CalendarOff className="w-3.5 h-3.5 inline mr-1" /> {t("HR · Time Off Requests")}
            </div>
            <h1 className="font-display text-2xl sm:text-4xl font-black mt-1">
              {t("Time Off Requests")}
            </h1>
          </div>
          <PublicLinkDialog onCreated={refresh} headers={headers} t={t} />
        </div>

        <StatsStrip stats={stats} t={t} />

        {/* iter222 · operational leadership coaching for HR's
            highest-cultural-drift-risk decision moments. Anchor:
            "Bereavement is granted, never debated. A pattern is a
            conversation, not a denial. Vacation is a yes with timing." */}
        <div className="mt-5">
          <HelpTipBlock formKey="time-off-review" showCounter />
        </div>

        <Card className="p-3 sm:p-4 mt-5 sm:mt-6">
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[140px]">
              <Label className="font-mono text-[10px] sm:text-xs uppercase tracking-wider">{t("Search Employee")}</Label>
              <Input value={employee} onChange={(e) => setEmployee(e.target.value)}
                placeholder={t("Name contains…")}
                className="h-11"
                data-testid="time-off-search-employee" />
            </div>
            <div className="w-full sm:w-auto">
              <Label className="font-mono text-[10px] sm:text-xs uppercase tracking-wider">{t("Status")}</Label>
              <div className="flex gap-1.5 flex-wrap">
                {["all", "pending", "approved", "denied", "need_info"].map((s) => (
                  <button key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`h-11 px-3 rounded-md text-xs font-bold uppercase tracking-wide border-2 ${
                      statusFilter === s
                        ? "bg-slate-900 text-white border-slate-900"
                        : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"
                    }`}
                    data-testid={`time-off-filter-${s}`}
                  >
                    {s.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>
            <Button onClick={refresh} disabled={busy} className="h-11 bg-cyan-700 hover:bg-cyan-800 text-white">
              <Filter className="w-4 h-4 mr-1.5" /> {t("Apply")}
            </Button>
          </div>
        </Card>

        {/* MOBILE: stacked cards (sm:hidden). DESKTOP: data table (hidden sm:block). */}
        <div className="sm:hidden space-y-2 mt-4" data-testid="time-off-mobile-list">
          {rows.length === 0 ? (
            <Card className="p-8 text-center text-slate-500">
              <CalendarOff className="w-8 h-8 mx-auto mb-2 text-slate-400" />
              {busy ? t("Loading…") : t("No time off requests in this view yet.")}
            </Card>
          ) : rows.map((r) => {
            const d = r.details || {};
            const st = STATUS_STYLES[r.status || "pending"] || STATUS_STYLES.pending;
            return (
              <Card key={r.id} className="p-3" data-testid={`time-off-mob-${r.id}`}>
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="font-display text-lg font-black truncate">{r.employee_name || "—"}</div>
                  <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border whitespace-nowrap ${st.bg}`}>
                    {st.label}
                  </span>
                </div>
                <div className="font-mono text-[10px] text-slate-500">{r.doc_id || "—"} · {(r.created_at || "").slice(0,10)}</div>
                <div className="text-sm mt-2">{d.reason || "—"} <span className="text-slate-400">· {d.pay_type || "—"}</span></div>
                <div className="text-xs font-mono text-slate-600 mt-1">
                  {(d.start_date || "—")} → {(d.end_date || "—")} · <span className="font-bold">{d.total_days || 0} {t("days")}</span>
                </div>
                <Button size="sm" variant="outline" onClick={() => setActive(r)}
                  className="w-full mt-3 h-11" data-testid={`time-off-review-mob-${r.id}`}>
                  <FileText className="w-3.5 h-3.5 mr-1" /> {t("Review")}
                </Button>
              </Card>
            );
          })}
        </div>

        <Card className="mt-4 overflow-x-auto hidden sm:block" data-testid="time-off-table">
          {rows.length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <CalendarOff className="w-8 h-8 mx-auto mb-2 text-slate-400" />
              {busy ? t("Loading…") : t("No time off requests in this view yet.")}
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-slate-700 uppercase tracking-wider text-xs">
                <tr>
                  <th className="text-left px-3 py-2">{t("Submitted")}</th>
                  <th className="text-left px-3 py-2">{t("Doc ID")}</th>
                  <th className="text-left px-3 py-2">{t("Employee")}</th>
                  <th className="text-left px-3 py-2">{t("Reason")}</th>
                  <th className="text-left px-3 py-2">{t("Dates")}</th>
                  <th className="text-right px-3 py-2">{t("Days")}</th>
                  <th className="text-left px-3 py-2">{t("Pay")}</th>
                  <th className="text-left px-3 py-2">{t("Status")}</th>
                  <th className="text-right px-3 py-2">{t("Actions")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => {
                  const d = r.details || {};
                  const st = STATUS_STYLES[r.status || "pending"] || STATUS_STYLES.pending;
                  return (
                    <tr key={r.id} className="border-t border-slate-100 hover:bg-cyan-50/30">
                      <td className="px-3 py-2 font-mono text-xs">{(r.created_at || "").slice(0, 10)}</td>
                      <td className="px-3 py-2 font-mono text-xs">{r.doc_id || "—"}</td>
                      <td className="px-3 py-2 font-semibold">{r.employee_name || "—"}</td>
                      <td className="px-3 py-2">{d.reason || "—"}</td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {(d.start_date || "—")} → {(d.end_date || "—")}
                      </td>
                      <td className="px-3 py-2 text-right font-mono font-bold">{d.total_days || 0}</td>
                      <td className="px-3 py-2">{d.pay_type || "—"}</td>
                      <td className="px-3 py-2">
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold border ${st.bg}`}>
                          {st.label}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <Button size="sm" variant="outline"
                          onClick={() => setActive(r)}
                          data-testid={`time-off-review-${r.id}`}
                        >
                          <FileText className="w-3.5 h-3.5 mr-1" /> {t("Review")}
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </Card>
      </main>

      {active && (
        <ReviewDialog
          record={active}
          onClose={() => setActive(null)}
          onDecided={() => { setActive(null); refresh(); }}
          headers={headers}
          t={t}
        />
      )}
    </div>
  );
}

function StatsStrip({ stats, t }) {
  const tiles = [
    { key: "pending", label: t("Pending"), color: "bg-amber-100 text-amber-900 border-amber-400" },
    { key: "approved", label: t("Approved"), color: "bg-emerald-100 text-emerald-900 border-emerald-500" },
    { key: "denied", label: t("Denied"), color: "bg-red-100 text-red-900 border-red-500" },
    { key: "need_info", label: t("Need Info"), color: "bg-orange-100 text-orange-900 border-orange-500" },
    { key: "submitted_last_7d", label: t("Last 7 Days"), color: "bg-slate-100 text-slate-900 border-slate-400" },
  ];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mt-5" data-testid="time-off-stats">
      {tiles.map((t) => (
        <div key={t.key} className={`rounded-md p-3 border-2 ${t.color}`}>
          <div className="font-mono text-[10px] uppercase tracking-widest font-bold">{t.label}</div>
          <div className="font-display text-2xl font-black">{stats[t.key] ?? 0}</div>
        </div>
      ))}
    </div>
  );
}

function ReviewDialog({ record, onClose, onDecided, headers, t }) {
  const d = record.details || {};
  const dec = d.hr_decision || {};
  const [status, setStatus] = React.useState(dec.status || "approved");
  const [notes, setNotes] = React.useState(dec.notes || "");
  const [payCode, setPayCode] = React.useState(dec.pay_code || _suggestPayCode(d.reason));
  const [busy, setBusy] = React.useState(false);

  const submit = async () => {
    setBusy(true);
    try {
      const resp = await fetch(`${API}/field-leadership/time-off/${record.id}/decide`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ status, notes, pay_code: payCode }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      toast.success(t(`Decision saved — ${status.replace("_", " ").toUpperCase()}`));
      onDecided();
    } catch (e) {
      toast.error(t("Could not save decision. Try again."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl" data-testid="time-off-review-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-xl">
            {t("Review Time Off Request")}
            {record.doc_id && <span className="ml-2 font-mono text-xs text-slate-500">{record.doc_id}</span>}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-3 text-sm">
          <Row label={t("Employee")} value={record.employee_name} />
          <Row label={t("Position")} value={record.employee_position || "—"} />
          <Row label={t("Filed By")} value={record.supervisor_name || "—"} />
          <Row label={t("Reason")} value={d.reason + (d.reason_other ? ` (${d.reason_other})` : "")} />
          <Row label={t("Pay Type")} value={d.pay_type || "—"} />
          <Row label={t("Dates")} value={`${d.start_date || "—"} → ${d.end_date || "—"}`} />
          <Row label={t("Total Days")} value={d.total_days || 0} />
          <Row label={t("Return to Work")} value={d.return_to_work_date || "—"} />
          <Row label={t("Contact During Leave")} value={d.contact_phone || "—"} />
          {d.coverage_plan && <Row label={t("Coverage")} value={d.coverage_plan} />}
          {d.notes && <Row label={t("Notes")} value={d.notes} />}
        </div>

        <div className="border-t pt-4 mt-2 space-y-3">
          <div className="font-mono text-xs uppercase tracking-wider font-bold text-cyan-700">
            {t("HR Decision")}
          </div>
          <div className="flex gap-2 flex-wrap">
            {[
              { v: "approved", label: t("Approve"), icon: CheckCircle2, bg: "bg-emerald-700 hover:bg-emerald-800" },
              { v: "denied", label: t("Deny"), icon: XCircle, bg: "bg-red-700 hover:bg-red-800" },
              { v: "need_info", label: t("Need Info"), icon: AlertCircle, bg: "bg-orange-700 hover:bg-orange-800" },
            ].map((opt) => (
              <button key={opt.v}
                onClick={() => setStatus(opt.v)}
                className={`h-10 px-4 rounded-md text-sm font-bold text-white uppercase tracking-wide border-2 ${
                  status === opt.v ? opt.bg + " border-slate-900" : "bg-slate-400 border-slate-300 hover:bg-slate-500"
                }`}
                data-testid={`time-off-decide-${opt.v}`}
              >
                <opt.icon className="w-4 h-4 inline mr-1" /> {opt.label}
              </button>
            ))}
          </div>
          <div>
            <Label className="font-mono text-xs uppercase">{t("Pay Code (Exact)")}</Label>
            <Input value={payCode} onChange={(e) => setPayCode(e.target.value)}
              placeholder="VAC / SCK / PER / FMLA / BRV / JURY / MIL / UNP"
              data-testid="time-off-pay-code" />
          </div>
          <div>
            <Label className="font-mono text-xs uppercase">{t("HR Notes (optional)")}</Label>
            <Textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)}
              placeholder={t("Anything the employee + supervisor + PM should know…")}
              data-testid="time-off-decision-notes" />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>{t("Close")}</Button>
          <a
            href={`${API}/field-leadership/${record.id}/pdf`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center h-10 px-4 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-900 font-bold uppercase tracking-wide text-sm border-2 border-slate-300"
            data-testid="time-off-download-pdf"
          >
            <FileText className="w-4 h-4 mr-1" /> {t("PDF")}
          </a>
          <Button onClick={submit} disabled={busy} className="bg-cyan-700 hover:bg-cyan-800 text-white" data-testid="time-off-save-decision">
            {busy ? t("Saving…") : t("Save Decision & Email Employee")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex gap-3">
      <div className="w-44 shrink-0 font-mono text-xs uppercase tracking-wider text-slate-500 pt-0.5">{label}</div>
      <div className="flex-1 text-slate-900 whitespace-pre-wrap">{String(value ?? "—")}</div>
    </div>
  );
}

function PublicLinkDialog({ onCreated, headers, t }) {
  const [open, setOpen] = React.useState(false);
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [position, setPosition] = React.useState("");
  const [dept, setDept] = React.useState("");
  const [note, setNote] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [created, setCreated] = React.useState(null);

  const reset = () => {
    setName(""); setEmail(""); setPosition(""); setDept(""); setNote(""); setCreated(null);
  };

  const submit = async () => {
    if (!name.trim()) { toast.error(t("Employee name required")); return; }
    setBusy(true);
    try {
      const resp = await fetch(`${API}/field-leadership/time-off/public-link`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          employee_name: name.trim(),
          employee_email: email.trim(),
          employee_position: position.trim(),
          department: dept.trim(),
          note: note.trim(),
        }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      const d = await resp.json();
      const origin = window.location.origin;
      const fullUrl = `${origin}${d.url_path}`;
      setCreated({ ...d, fullUrl });
      toast.success(email ? t("Link created · email sent.") : t("Link created — copy and share."));
      onCreated && onCreated();
    } catch (e) {
      toast.error(t("Could not create link. Try again."));
    } finally {
      setBusy(false);
    }
  };

  const copyLink = () => {
    if (!created) return;
    navigator.clipboard.writeText(created.fullUrl).then(() => toast.success(t("Copied!")));
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button className="h-10 bg-cyan-700 hover:bg-cyan-800 text-white font-bold" data-testid="time-off-send-public-link">
          <Send className="w-4 h-4 mr-1.5" /> {t("Send to Office Employee")}
        </Button>
      </DialogTrigger>
      <DialogContent data-testid="time-off-public-link-dialog">
        <DialogHeader>
          <DialogTitle>{t("Send Time Off Form to an Office Employee")}</DialogTitle>
        </DialogHeader>
        {created ? (
          <div className="space-y-3">
            <p className="text-sm text-slate-700">
              {t("Public link created. Valid 7 days, one submission. Copy + share if the auto-email wasn't sent.")}
            </p>
            <div className="bg-slate-100 p-2 rounded font-mono text-xs break-all" data-testid="time-off-public-url">
              {created.fullUrl}
            </div>
            <Button onClick={copyLink} variant="outline" className="w-full">
              <Copy className="w-4 h-4 mr-1.5" /> {t("Copy URL")}
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-slate-600">
              {t("Use this for office employees who don't have a platform login. We generate a token-gated public URL valid 7 days.")}
            </p>
            <div>
              <Label className="font-mono text-xs uppercase">{t("Employee Name")} *</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} data-testid="time-off-public-name" />
            </div>
            <div>
              <Label className="font-mono text-xs uppercase">{t("Employee Email (sends auto-link)")}</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} data-testid="time-off-public-email" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
              <div>
                <Label className="font-mono text-xs uppercase">{t("Position")}</Label>
                <Input value={position} onChange={(e) => setPosition(e.target.value)} />
              </div>
              <div>
                <Label className="font-mono text-xs uppercase">{t("Department")}</Label>
                <Input value={dept} onChange={(e) => setDept(e.target.value)} />
              </div>
            </div>
            <div>
              <Label className="font-mono text-xs uppercase">{t("Note (shown to employee)")}</Label>
              <Textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
            </div>
          </div>
        )}
        <DialogFooter>
          {created ? (
            <Button onClick={() => { reset(); }}>{t("Send Another")}</Button>
          ) : (
            <Button onClick={submit} disabled={busy} className="bg-cyan-700 hover:bg-cyan-800 text-white" data-testid="time-off-create-link">
              {busy ? t("Creating…") : t("Create Link")}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function _suggestPayCode(reason) {
  if (!reason) return "";
  const map = {
    "Vacation": "VAC",
    "Sick Leave": "SCK",
    "Medical Appointment": "SCK",
    "Family Emergency": "FMLA",
    "Bereavement": "BRV",
    "Jury Duty": "JURY",
    "Military Leave": "MIL",
    "Personal": "PER",
    "Other": "",
  };
  return map[reason] || "";
}
