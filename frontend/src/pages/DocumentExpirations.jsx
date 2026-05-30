// DocumentExpirations.jsx — Iter151 (Phase B). Universal document
// expiration page at /document-expirations. Role-aware scoping is
// done server-side (HR sees employee + training certs, Safety sees
// safety + training + employee, Shop sees equipment, Admin sees all).
//
// Includes:
//   * 4 summary tiles (Current / Expiring Soon / Expired / Archived)
//   * Filters: status, category, free-text search (remembered)
//   * Add-doc dialog
//   * Status badges with traffic-light colors
//   * Admin-only scanner controls ("Preview" + "Run Scan Now")

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  CalendarClock, AlertOctagon, CheckCircle2, Archive,
  Plus, Search, ArrowLeft, Home, Play, Eye, RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { MasciLogo } from "@/components/MasciLogo";
import NotificationBell from "@/components/NotificationBell";
import {
  listExpirations, summary, createExpiration,
  adminScan, adminScanPreview,
} from "@/lib/docExpirationsApi";
import { isSignedInAnywhere } from "@/lib/permissions";
import { useRememberedFilter } from "@/lib/useRememberedFilter";
import { friendlyError } from "@/lib/friendlyErrors";
import { isAdmin } from "@/lib/adminAuth";
import AccessDenied from "@/pages/AccessDenied";
import { toast } from "sonner";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import GlobalSearch from "@/components/GlobalSearch";
import { DOC_EXP_STATUS_TINTS } from "@/lib/statusBadges";
import { HelpTipBlock } from "@/components/HelpTip";
import { useT } from "@/lib/i18n";

const STATUS_COLORS = DOC_EXP_STATUS_TINTS;

const CATEGORIES = [
  { value: "employee", labelKey: "Employee documents" },
  { value: "training_cert", labelKey: "Training certifications" },
  { value: "safety", labelKey: "Safety compliance" },
  { value: "equipment", labelKey: "Equipment / asset" },
  { value: "company", labelKey: "Company / admin" },
  { value: "project", labelKey: "Project / job" },
];

export default function DocumentExpirations() {
  const nav = useNavigate();
  const { t } = useT();
  const [status, setStatus] = useRememberedFilter("docexp.status", "all");
  const [category, setCategory] = useRememberedFilter("docexp.category", "all");
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [summ, setSumm] = useState({});
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const signedIn = isSignedInAnywhere();
  const admin = isAdmin();

  const fetchAll = useCallback(async () => {
    if (!signedIn) { setLoading(false); return; }
    setLoading(true);
    try {
      const r = await listExpirations({
        limit: 300,
        ...(status !== "all" ? { status } : {}),
        ...(category !== "all" ? { category } : {}),
        ...(q ? { q } : {}),
      });
      let visible = r.items || [];
      // Default view hides Archived rows — they're noisy and rarely actionable.
      // Only show them when the user explicitly filters status='Archived'.
      if (status !== "Archived") {
        visible = visible.filter((d) => d.status !== "Archived");
      }
      setItems(visible);
      const s = await summary().catch(() => ({}));
      setSumm(s);
    } catch (e) {
      toast.error(friendlyError(e, t("Could not load expirations")));
    } finally { setLoading(false); }
  }, [status, category, q, signedIn, t]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (!signedIn) return <AccessDenied attemptedPortal="document-expirations" />;

  const onCreate = async (payload) => {
    try {
      await createExpiration(payload);
      toast.success(t("Expiration record added"));
      setAddOpen(false);
      fetchAll();
    } catch (e) {
      toast.error(friendlyError(e, t("Could not save expiration")));
    }
  };

  const onScan = async (preview = false) => {
    try {
      const fn = preview ? adminScanPreview : adminScan;
      const r = await fn();
      const data = r.data ?? r;
      const fired = data?.fired?.length ?? 0;
      toast.success(
        preview
          ? `${t("Preview")}: ${fired} ${t("threshold(s) would fire")}`
          : `${t("Scan complete")}: ${fired} ${t("threshold(s) fired")}`,
      );
      if (!preview) fetchAll();
    } catch (e) {
      toast.error(friendlyError(e, t("Scan failed")));
    }
  };

  return (
    <div className="min-h-screen bg-slate-50" data-testid="document-expirations-page">
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center gap-3 flex-wrap">
          <Link to="/" className="inline-flex items-center text-white hover:text-amber-400 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="docexp-nav-home">
            <Home className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Home</span>
          </Link>
          <button onClick={() => nav(-1)} className="inline-flex items-center text-white hover:text-amber-400 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="docexp-nav-back">
            <ArrowLeft className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">{t("Back")}</span>
          </button>
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <div className="flex-1 min-w-0">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-amber-400 font-bold">{t("Document Expirations")}</div>
            <div className="font-display text-lg sm:text-xl font-black text-white leading-tight">{t("Compliance Tracker")}</div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <GlobalSearch accent="dark" />
            <NotificationBell accent="white" />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-6 sm:py-8">
        {/* iter225 · operational outreach coaching for the
            document-expirations surface. Anchor: "Phone call beats
            email blast." Tier-2: hr + safety + admin. */}
        <HelpTipBlock formKey="document-expirations" showCounter />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mb-6">
          <SummaryTile label={t("Current")} value={summ.by_status?.Current ?? 0} icon={CheckCircle2} accent="emerald" testIdSuffix="current" />
          <SummaryTile label={t("Expiring Soon")} value={summ.expiring_30d ?? 0} icon={CalendarClock} accent="amber" testIdSuffix="expiring-soon" />
          <SummaryTile label={t("Expired")} value={summ.expired ?? 0} icon={AlertOctagon} accent="red" testIdSuffix="expired" />
          <SummaryTile label={t("Archived")} value={summ.by_status?.Archived ?? 0} icon={Archive} accent="slate" testIdSuffix="archived" />
        </div>

        <div className="bg-white border border-slate-200 rounded-md p-3 sm:p-4 mb-4 flex flex-wrap items-center gap-2.5">
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-[150px] h-9 text-xs" data-testid="docexp-status-filter">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("All statuses")}</SelectItem>
              <SelectItem value="Current">{t("Current")}</SelectItem>
              <SelectItem value="Expiring Soon">{t("Expiring Soon")}</SelectItem>
              <SelectItem value="Expired">{t("Expired")}</SelectItem>
              <SelectItem value="Archived">{t("Archived")}</SelectItem>
            </SelectContent>
          </Select>
          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger className="w-[200px] h-9 text-xs" data-testid="docexp-category-filter">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("All categories")}</SelectItem>
              {CATEGORIES.map((c) => (
                <SelectItem key={c.value} value={c.value}>{t(c.labelKey)}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <Input
              value={q} onChange={(e) => setQ(e.target.value)}
              placeholder={t("Search document type or title…")}
              className="pl-8 h-9 text-xs"
              data-testid="docexp-search-input"
            />
          </div>
          {admin && (
            <>
              <Button variant="outline" size="sm" onClick={() => onScan(true)} className="text-xs" data-testid="docexp-scan-preview">
                <Eye className="w-3.5 h-3.5 mr-1" /> {t("Preview Scan")}
              </Button>
              <Button variant="outline" size="sm" onClick={() => onScan(false)} className="text-xs" data-testid="docexp-scan-run">
                <Play className="w-3.5 h-3.5 mr-1" /> {t("Run Scan")}
              </Button>
            </>
          )}
          <Button variant="outline" size="sm" onClick={fetchAll} className="text-xs" data-testid="docexp-refresh">
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
          <AddDialog open={addOpen} setOpen={setAddOpen} onSubmit={onCreate} />
        </div>

        {loading ? (
          <div className="bg-white border border-slate-200 rounded-md py-10 text-center text-slate-500 text-sm">{t("Loading…")}</div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={CalendarClock}
            title={t("No expiration records")}
            hint={t("Documents you upload with an expiration date will appear here. Try clearing filters.")}
            testId="docexp-empty"
          />
        ) : (
          <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr className="text-left text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                  <th className="px-4 py-2.5">{t("Status")}</th>
                  <th className="px-4 py-2.5">{t("Document")}</th>
                  <th className="px-4 py-2.5">{t("Category")}</th>
                  <th className="px-4 py-2.5">{t("Linked To")}</th>
                  <th className="px-4 py-2.5">{t("Expires")}</th>
                  <th className="px-4 py-2.5">{t("Days")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((d) => (
                  <DocRow key={d.id} doc={d} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}

function SummaryTile({ label, value, icon: Icon, accent, testIdSuffix }) {
  const palette = {
    emerald: "border-emerald-300 text-emerald-900",
    amber: "border-amber-300 text-amber-900",
    red: "border-red-400 text-red-900",
    slate: "border-slate-300 text-slate-700",
  }[accent] || "border-slate-300 text-slate-900";
  return (
    <div className={`bg-white border-2 ${palette} rounded-md p-3`} data-testid={`docexp-summary-${testIdSuffix || label.toLowerCase().replace(/\s/g,'-')}`}>
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 opacity-70" />
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-80 font-bold">{label}</span>
      </div>
      <div className="font-display text-2xl font-black mt-1 leading-none">{value}</div>
    </div>
  );
}

function DocRow({ doc }) {
  const expIso = doc.expiration_date;
  const days = useMemo(() => {
    if (!expIso) return null;
    try {
      const exp = new Date(expIso + "T00:00:00");
      const now = new Date();
      return Math.ceil((exp - now) / 86400000);
    } catch { return null; }
  }, [expIso]);
  const linked = doc.linked_employee_id || doc.linked_equipment_id || doc.linked_project_number || "—";
  return (
    <tr className="hover:bg-slate-50" data-testid={`docexp-row-${doc.id}`}>
      <td className="px-4 py-2.5">
        <StatusBadge kind="doc_exp" value={doc.status} size="sm" />
      </td>
      <td className="px-4 py-2.5">
        <div className="font-bold text-slate-900 text-sm">{doc.document_type}</div>
        {doc.title && <div className="text-[11px] text-slate-500">{doc.title}</div>}
      </td>
      <td className="px-4 py-2.5 text-slate-600 text-xs font-mono">{doc.category}</td>
      <td className="px-4 py-2.5 text-slate-700 text-xs font-mono">{linked}</td>
      <td className="px-4 py-2.5 text-slate-700 text-xs">{expIso || "—"}</td>
      <td className="px-4 py-2.5 text-xs font-mono">
        {days === null ? "—" : days < 0 ? <span className="text-red-700 font-bold">{days}d</span> : <span className={days <= 14 ? "text-amber-700 font-bold" : "text-slate-600"}>{days}d</span>}
      </td>
    </tr>
  );
}

function AddDialog({ open, setOpen, onSubmit }) {
  const { t } = useT();
  const [form, setForm] = useState({
    document_type: "", category: "employee", title: "",
    linked_employee_id: "", linked_equipment_id: "",
    expiration_date: "", issue_date: "", notes: "",
  });
  const submit = (e) => {
    e.preventDefault();
    const payload = { ...form };
    Object.keys(payload).forEach((k) => { if (payload[k] === "") payload[k] = null; });
    if (!payload.document_type || !payload.expiration_date) {
      toast.error(t("Document type and expiration date are required"));
      return;
    }
    onSubmit(payload);
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" className="text-xs" data-testid="docexp-add-trigger">
          <Plus className="w-3.5 h-3.5 mr-1" /> {t("Add")}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md" data-testid="docexp-add-dialog">
        <DialogHeader>
          <DialogTitle>{t("Add Expiration Record")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <Label htmlFor="dt">{t("Document type *")}</Label>
            <Input id="dt" value={form.document_type} onChange={(e) => setForm({ ...form, document_type: e.target.value })} placeholder={t("e.g. OSHA 30, TWIC, CDL Medical")} data-testid="docexp-add-type" />
          </div>
          <div>
            <Label>{t("Category *")}</Label>
            <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
              <SelectTrigger data-testid="docexp-add-category"><SelectValue /></SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((c) => (<SelectItem key={c.value} value={c.value}>{t(c.labelKey)}</SelectItem>))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="title">{t("Title / Reference")}</Label>
            <Input id="title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder={t("e.g. John Doe — Driver License")} data-testid="docexp-add-title" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label htmlFor="issue">{t("Issue date")}</Label>
              <Input id="issue" type="date" value={form.issue_date} onChange={(e) => setForm({ ...form, issue_date: e.target.value })} data-testid="docexp-add-issue" />
            </div>
            <div>
              <Label htmlFor="exp">{t("Expiration date *")}</Label>
              <Input id="exp" type="date" value={form.expiration_date} onChange={(e) => setForm({ ...form, expiration_date: e.target.value })} data-testid="docexp-add-exp" />
            </div>
          </div>
          <div>
            <Label htmlFor="emp">{t("Linked employee ID")}</Label>
            <Input id="emp" value={form.linked_employee_id} onChange={(e) => setForm({ ...form, linked_employee_id: e.target.value })} placeholder={t("Optional")} data-testid="docexp-add-emp" />
          </div>
          <div>
            <Label htmlFor="eqp">{t("Linked equipment ID")}</Label>
            <Input id="eqp" value={form.linked_equipment_id} onChange={(e) => setForm({ ...form, linked_equipment_id: e.target.value })} placeholder={t("Optional")} data-testid="docexp-add-eqp" />
          </div>
          <DialogFooter>
            <Button type="submit" data-testid="docexp-add-submit">{t("Save")}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
