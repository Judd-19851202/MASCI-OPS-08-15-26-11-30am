// iter288 · HR · Driver Qualification Dashboard.
// Read-only operational visibility surface. Filterable list of drivers
// + 5 tiny summary cards. NOT a dispatch system, NOT a compliance
// platform — read the coaching family for the boundary discipline.
import React, { useCallback, useEffect, useState } from "react";
import { Loader2, Search, Truck, AlertTriangle, Clock, Ban, ShieldX, Download, Upload } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import HrPageShell from "@/components/HrPageShell";
import { HelpTipBlock } from "@/components/HelpTip";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";

const inputCls = "h-9 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-purple-600";

const DRIVER_STATUSES = ["active", "suspended", "restricted", "inactive"];
const ENDORSEMENT_CODES = [
  { code: "N", label: "Tanker (N)" },
  { code: "H", label: "Hazmat (H)" },
  { code: "X", label: "Tanker + Hazmat (X)" },
  { code: "T", label: "Doubles/Triples (T)" },
  { code: "P", label: "Passenger (P)" },
  { code: "S", label: "School Bus (S)" },
];

function StatusChip({ status, t }) {
  if (!status) return <span className="text-slate-400">—</span>;
  const map = {
    active: "bg-emerald-100 text-emerald-800 border-emerald-300",
    suspended: "bg-red-100 text-red-800 border-red-300",
    restricted: "bg-amber-100 text-amber-800 border-amber-300",
    inactive: "bg-slate-100 text-slate-700 border-slate-300",
  };
  return (
    <Badge variant="outline" className={`${map[status] || "bg-slate-100"} text-[10px] uppercase font-mono`} data-testid={`dq-status-chip-${status}`}>
      {t(status)}
    </Badge>
  );
}

function DateChip({ date, t }) {
  if (!date) return <span className="text-slate-400">—</span>;
  // Lightweight expiring-soon visual cue (no full alert system, just a hint).
  const today = new Date().toISOString().slice(0, 10);
  const in30 = new Date(Date.now() + 30 * 86400_000).toISOString().slice(0, 10);
  const expired = date < today;
  const soon = !expired && date <= in30;
  const cls = expired
    ? "text-red-700 font-bold"
    : soon
      ? "text-amber-700 font-bold"
      : "text-slate-700";
  return <span className={cls} title={expired ? t("Expired") : soon ? t("Expiring soon") : ""}>{date}</span>;
}

export default function HrDriverQualificationDashboard() {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    cdl_holder: "",
    approved: "",
    driver_status: "",
    endorsement: "",
    expiring_cdl_30d: false,
    expiring_medical_30d: false,
    q: "",
  });

  const fetchRows = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 500 };
      if (filters.cdl_holder !== "") params.cdl_holder = filters.cdl_holder;
      if (filters.approved !== "") params.approved = filters.approved;
      if (filters.driver_status) params.driver_status = filters.driver_status;
      if (filters.endorsement) params.endorsement = filters.endorsement;
      if (filters.expiring_cdl_30d) params.expiring_cdl_30d = true;
      if (filters.expiring_medical_30d) params.expiring_medical_30d = true;
      if (filters.q.trim()) params.q = filters.q.trim();
      const r = await api.get("/hr/driver-qualification/dashboard", { params });
      setItems(r.data?.items || []);
      setSummary(r.data?.summary || null);
    } catch (err) {
      toast.error(err?.response?.data?.detail || t("Could not load driver qualification dashboard"));
    } finally {
      setLoading(false);
    }
  }, [filters, t]);

  useEffect(() => {
    fetchRows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleEndorsementFilter = (code) => {
    setFilters((f) => ({ ...f, endorsement: f.endorsement === code ? "" : code }));
  };
  const toggleStatusFilter = (s) => {
    setFilters((f) => ({ ...f, driver_status: f.driver_status === s ? "" : s }));
  };

  // iter313 · Export Current View → CSV.
  // Reuses the iter312 endpoint with the CURRENT filter state so the
  // exported file is EXACTLY what the user is looking at. No new
  // backend, no new query path, no analytics drift. The button stays
  // disabled while a fetch is in flight and surfaces failures via
  // toast (admin-visible discipline — HR knows when it doesn't work).
  const [exporting, setExporting] = useState(false);
  const exportCurrentView = async () => {
    setExporting(true);
    try {
      const params = { limit: 5000 };
      if (filters.cdl_holder !== "") params.cdl_holder = filters.cdl_holder;
      if (filters.approved !== "") params.approved = filters.approved;
      if (filters.driver_status) params.driver_status = filters.driver_status;
      if (filters.endorsement) params.endorsement = filters.endorsement;
      if (filters.expiring_cdl_30d) params.expiring_cdl_30d = true;
      if (filters.expiring_medical_30d) params.expiring_medical_30d = true;
      if (filters.q.trim()) params.q = filters.q.trim();
      const r = await api.get("/hr/driver-qualification/dashboard.csv", {
        params,
        responseType: "blob",
      });
      // Extract filename from Content-Disposition if present, else
      // fall back to a sensible client-side default.
      const cd = r.headers?.["content-disposition"] || r.headers?.["Content-Disposition"] || "";
      const match = /filename="?([^"]+)"?/i.exec(cd);
      const filename = match ? match[1] : `MASCI_driver_qualification_${new Date().toISOString().slice(0, 10)}.csv`;
      const blob = new Blob([r.data], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success(t("Driver qualification CSV downloaded"));
    } catch (err) {
      console.error("[hr/driver-qualification] csv export failed:", err);
      toast.error(err?.response?.data?.detail || t("Could not export driver qualification CSV"));
    } finally {
      setExporting(false);
    }
  };

  return (
    <HrPageShell title="Driver Qualification Dashboard" kicker="HR · Operational Visibility">
      <HelpTipBlock formKey="driver-qualification.dashboard" />

      {/* Tiny summary cards — operational gut-check */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 my-4" data-testid="dq-summary-cards">
          <SummaryCard testid="dq-card-cdl-expiring" icon={Clock} tint="border-amber-500 bg-amber-50" label={t("CDL Expiring 30d")} count={summary.cdl_expiring_30d} />
          <SummaryCard testid="dq-card-med-expiring" icon={Clock} tint="border-rose-500 bg-rose-50" label={t("Medical Card Expiring 30d")} count={summary.medical_card_expiring_30d} />
          <SummaryCard testid="dq-card-restricted" icon={AlertTriangle} tint="border-amber-600 bg-amber-100/60" label={t("Restricted")} count={summary.restricted} />
          <SummaryCard testid="dq-card-suspended" icon={Ban} tint="border-red-500 bg-red-50" label={t("Suspended")} count={summary.suspended} />
          <SummaryCard testid="dq-card-tanker-capable" icon={Truck} tint="border-emerald-500 bg-emerald-50" label={t("Tanker-Capable")} count={summary.tanker_capable} />
        </div>
      )}

      {/* Filters — lightweight, operational */}
      <Card className="p-3 mb-4 border-2 border-slate-200" data-testid="dq-filters">
        <div className="flex flex-wrap gap-2 items-end">
          <div className="flex-1 min-w-[160px]">
            <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Search")}</label>
            <Input value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} onKeyDown={(e) => e.key === "Enter" && fetchRows()} placeholder={t("Name · ID · CDL #")} className={inputCls} data-testid="dq-filter-q" />
          </div>
          <FilterTriToggle label={t("CDL Holder")} value={filters.cdl_holder} onChange={(v) => setFilters({ ...filters, cdl_holder: v })} testid="dq-filter-cdl-holder" t={t} />
          <FilterTriToggle label={t("Approved Company Driver")} value={filters.approved} onChange={(v) => setFilters({ ...filters, approved: v })} testid="dq-filter-approved" t={t} />
        </div>

        <div className="mt-2 flex flex-wrap gap-1.5 items-center">
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 mr-1">{t("Status")}:</span>
          {DRIVER_STATUSES.map((s) => (
            <Button
              key={s}
              variant={filters.driver_status === s ? "default" : "outline"}
              size="sm"
              className="h-7 text-xs"
              onClick={() => toggleStatusFilter(s)}
              data-testid={`dq-filter-status-${s}`}
            >
              {t(s)}
            </Button>
          ))}
        </div>

        <div className="mt-2 flex flex-wrap gap-1.5 items-center">
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 mr-1">{t("Endorsement")}:</span>
          {ENDORSEMENT_CODES.map(({ code, label }) => (
            <Button
              key={code}
              variant={filters.endorsement === code ? "default" : "outline"}
              size="sm"
              className="h-7 text-xs"
              onClick={() => toggleEndorsementFilter(code)}
              data-testid={`dq-filter-endorsement-${code}`}
            >
              {t(label)}
            </Button>
          ))}
        </div>

        <div className="mt-2 flex flex-wrap gap-2 items-center">
          <Button
            variant={filters.expiring_cdl_30d ? "default" : "outline"}
            size="sm"
            className="h-7 text-xs"
            onClick={() => setFilters({ ...filters, expiring_cdl_30d: !filters.expiring_cdl_30d })}
            data-testid="dq-filter-expiring-cdl"
          >
            {t("CDL Expiring 30d")}
          </Button>
          <Button
            variant={filters.expiring_medical_30d ? "default" : "outline"}
            size="sm"
            className="h-7 text-xs"
            onClick={() => setFilters({ ...filters, expiring_medical_30d: !filters.expiring_medical_30d })}
            data-testid="dq-filter-expiring-medical"
          >
            {t("Medical Card Expiring 30d")}
          </Button>
          <Button onClick={fetchRows} disabled={loading} className="h-7 text-xs bg-purple-700 hover:bg-purple-800 text-white ml-auto" data-testid="dq-apply">
            {loading ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Search className="w-3.5 h-3.5 mr-1" />}
            {t("Apply")}
          </Button>
          <Button
            onClick={exportCurrentView}
            disabled={exporting || loading || items.length === 0}
            variant="outline"
            className="h-7 text-xs border-purple-700 text-purple-700 hover:bg-purple-50"
            title={t("Export the current filtered view to CSV")}
            data-testid="dq-export-csv"
          >
            {exporting ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Download className="w-3.5 h-3.5 mr-1" />}
            {t("Export Current View → CSV")}
          </Button>
          {/* iter352 — self-service roster importer entry point. */}
          <Link to="/hr/driver-qualification/import" data-testid="dq-import-link">
            <Button
              variant="outline"
              className="h-7 text-xs border-emerald-700 text-emerald-700 hover:bg-emerald-50"
              title={t("Upload XLSX or CSV roster — preview matches, confirm, audit.")}
              data-testid="dq-import-btn"
            >
              <Upload className="w-3.5 h-3.5 mr-1" />
              {t("Import Roster")}
            </Button>
          </Link>
        </div>
      </Card>

      {/* Table — dense by design (operational surface) */}
      {loading ? (
        <Card className="p-10 text-center text-slate-500"><Loader2 className="w-6 h-6 mx-auto animate-spin" /></Card>
      ) : items.length === 0 ? (
        <Card className="p-10 text-center text-slate-500" data-testid="dq-empty">
          <ShieldX className="w-10 h-10 mx-auto text-slate-400 mb-3" />
          <div className="font-bold text-base text-slate-900">{t("No matching drivers")}</div>
          <p className="text-sm text-slate-600 mt-2 max-w-md mx-auto">
            {t("Adjust filters above, or add driver qualification data on an employee record in the HR portal.")}
          </p>
        </Card>
      ) : (
        <Card className="overflow-x-auto" data-testid="dq-table">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-[0.15em] font-mono">
              <tr>
                <th className="text-left px-3 py-2">{t("Driver")}</th>
                <th className="text-left px-3 py-2">{t("CDL")}</th>
                <th className="text-left px-3 py-2">{t("Approved")}</th>
                <th className="text-left px-3 py-2">{t("Status")}</th>
                <th className="text-left px-3 py-2">{t("Endorsements")}</th>
                <th className="text-left px-3 py-2">{t("Restrictions")}</th>
                <th className="text-left px-3 py-2">{t("CDL Exp")}</th>
                <th className="text-left px-3 py-2">{t("Medical Exp")}</th>
              </tr>
            </thead>
            <tbody data-testid="dq-table-body">
              {items.map((r) => (
                <tr key={r.id} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`dq-row-${r.id}`}>
                  <td className="px-3 py-2">
                    <div className="font-medium text-slate-900">{r.name}</div>
                    {(r.employee_id || r.trade) && (
                      <div className="text-xs text-slate-500">{r.employee_id}{r.employee_id && r.trade ? " · " : ""}{r.trade}</div>
                    )}
                  </td>
                  <td className="px-3 py-2">{r.cdl_holder ? <Badge variant="outline" className="bg-emerald-50 border-emerald-300 text-emerald-800 text-[10px]">{t("Yes")}</Badge> : <span className="text-slate-400">—</span>}</td>
                  <td className="px-3 py-2">{r.approved_company_driver ? <Badge variant="outline" className="bg-emerald-50 border-emerald-300 text-emerald-800 text-[10px]">{t("Yes")}</Badge> : <span className="text-slate-400">—</span>}</td>
                  <td className="px-3 py-2"><StatusChip status={r.driver_status} t={t} /></td>
                  <td className="px-3 py-2">
                    {Array.isArray(r.cdl_endorsements) && r.cdl_endorsements.length > 0
                      ? <div className="flex gap-1 flex-wrap">{r.cdl_endorsements.map((c) => <Badge key={c} variant="outline" className={`text-[10px] font-mono ${c === "N" || c === "X" ? "bg-emerald-50 border-emerald-400 text-emerald-800" : "bg-slate-50"}`}>{c}</Badge>)}</div>
                      : <span className="text-slate-400">—</span>}
                  </td>
                  <td className="px-3 py-2">
                    {Array.isArray(r.cdl_restrictions) && r.cdl_restrictions.length > 0
                      ? <div className="flex gap-1 flex-wrap">{r.cdl_restrictions.map((c) => <Badge key={c} variant="outline" className="text-[10px] font-mono bg-amber-50 border-amber-300 text-amber-800">{c === "air_brake" ? t("Air Brake") : c === "manual_transmission" ? t("Manual") : c}</Badge>)}</div>
                      : <span className="text-slate-400">—</span>}
                  </td>
                  <td className="px-3 py-2"><DateChip date={r.cdl_expiration_date} t={t} /></td>
                  <td className="px-3 py-2"><DateChip date={r.medical_card_expiration_date} t={t} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-3 py-2 text-xs text-slate-500 font-mono uppercase tracking-[0.15em] border-t" data-testid="dq-count">
            {t("Drivers")}: {items.length}
          </div>
        </Card>
      )}
    </HrPageShell>
  );
}

function SummaryCard({ icon: Icon, tint, label, count, testid }) {
  return (
    <Card className={`p-3 border-2 ${tint}`} data-testid={testid}>
      <div className="flex items-start gap-2">
        <Icon className="w-4 h-4 mt-0.5 text-slate-700" />
        <div className="min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 leading-tight">{label}</div>
          <div className="text-2xl font-bold text-slate-900 leading-none mt-1" data-testid={`${testid}-count`}>{count}</div>
        </div>
      </div>
    </Card>
  );
}

function FilterTriToggle({ label, value, onChange, testid, t }) {
  // value: "" (any) · "true" (yes) · "false" (no)
  const next = { "": "true", true: "false", false: "" };
  const display = value === "" ? t("Any") : value === true || value === "true" ? t("Yes") : t("No");
  return (
    <div>
      <label className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold block mb-0.5">{label}</label>
      <Button
        variant="outline"
        size="sm"
        className="h-9 text-xs min-w-[100px]"
        onClick={() => onChange(next[String(value)])}
        data-testid={testid}
      >
        {display}
      </Button>
    </div>
  );
}
