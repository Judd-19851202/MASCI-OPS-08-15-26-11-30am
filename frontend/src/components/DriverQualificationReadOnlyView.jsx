// iter353b · Shared read-only Driver Qualification view.
// Used by both Dispatch (`/dispatch-portal/driver-qualification`)
// and Field Leadership (`/field-leadership/portal/driver-qualification`).
// Same backend payload shape — single component, two thin wrappers.
//
// STRICTLY READ-ONLY surface: no edit, no import, no upload, no PATCH.
// Search + filters + summary cards only. Highlights expiring/expired
// dates where data exists.
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Search, Filter, RefreshCw, AlertTriangle, ShieldCheck, Truck, FileX, Zap } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { operationalError } from "@/lib/errors";
import { useT } from "@/lib/i18n";
import { LifecycleGuide } from "@/components/LifecycleGuide";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function StatusPill({ value, type }) {
  if (!value) return <span className="text-slate-400">—</span>;
  const v = String(value).toLowerCase();
  const tints = {
    yes:        "bg-emerald-100 text-emerald-900 border-emerald-200",
    no:         "bg-slate-100 text-slate-600 border-slate-200",
    active:     "bg-emerald-100 text-emerald-900 border-emerald-200",
    restricted: "bg-amber-100 text-amber-900 border-amber-300",
    suspended:  "bg-rose-100 text-rose-900 border-rose-300",
    inactive:   "bg-slate-200 text-slate-700 border-slate-300",
  };
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 border rounded text-[10px] font-mono uppercase tracking-wider ${tints[v] || "bg-slate-100 text-slate-700 border-slate-200"}`}>
      {value}
    </span>
  );
}

function DateCell({ value }) {
  const { t } = useT();
  if (!value) return <span className="text-slate-400">—</span>;
  const today = new Date().toISOString().slice(0, 10);
  const cutoff30 = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
  let tint = "text-slate-700";
  let label = "";
  if (value < today) { tint = "text-rose-700 font-semibold"; label = t("expired"); }
  else if (value <= cutoff30) { tint = "text-amber-700 font-semibold"; label = t("≤30d"); }
  return (
    <span className={`font-mono text-xs ${tint}`}>
      {value}{label && <span className="ml-1 uppercase tracking-wider text-[10px]">· {label}</span>}
    </span>
  );
}

function SummaryCard({ icon: Icon, label, value, tint = "slate", testid }) {
  const tints = {
    slate:   "border-slate-300 bg-white text-slate-900",
    amber:   "border-amber-400 bg-amber-50 text-amber-900",
    rose:    "border-rose-400 bg-rose-50 text-rose-900",
    emerald: "border-emerald-400 bg-emerald-50 text-emerald-900",
  };
  return (
    <div className={`border-2 ${tints[tint]} rounded-md p-3`} data-testid={testid}>
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 opacity-70" />
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-70">{label}</div>
      </div>
      <div className="font-display text-2xl font-black mt-1 leading-none">{value}</div>
    </div>
  );
}

/**
 * DriverQualificationReadOnlyView
 *
 * Props:
 *   - endpoint:    e.g. "/dispatch/driver-qualification" or
 *                  "/field-leadership/portal/driver-qualification".
 *   - authHeaders: function returning the auth headers to attach
 *                  (varies by portal — Dispatch uses X-Dispatch-Token,
 *                  FL uses X-FL-Token).
 *   - accent:      Tailwind color name for portal accent
 *                  ("orange" for Dispatch, "red" for FL).
 *   - testidPrefix: e.g. "dq-disp" or "dq-fl".
 */
export default function DriverQualificationReadOnlyView({
  endpoint,
  authHeaders,
  accent = "slate",
  testidPrefix = "dq",
  onRowClick = null,
}) {
  const { t } = useT();
  const [data, setData] = useState({ items: [], count: 0, summary: {}, as_of: "" });
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  // Filters
  const [q, setQ] = useState("");
  const [cdl, setCdl] = useState("any");             // any|true|false
  const [approved, setApproved] = useState("any");   // any|true|false
  const [status, setStatus] = useState("any");       // any|active|restricted|suspended|inactive
  const [availableOnly, setAvailableOnly] = useState(false);  // iter353b-availability tile filter

  const params = useMemo(() => {
    const p = { limit: 500 };
    if (q.trim()) p.q = q.trim();
    if (cdl !== "any") p.cdl_holder = cdl;
    if (approved !== "any") p.approved = approved;
    if (status !== "any") p.driver_status = status;
    if (availableOnly) p.available_now = true;
    return p;
  }, [q, cdl, approved, status, availableOnly]);

  const load = async () => {
    setLoading(true); setErr("");
    try {
      const r = await axios.get(`${API}${endpoint}`, { headers: authHeaders(), params });
      setData(r.data || { items: [] });
    } catch (e) {
      setErr(operationalError(e, t("Could not load driver qualification.")));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [params]);

  const accentBar = {
    orange: "border-l-orange-500",
    red:    "border-l-red-700",
    slate:  "border-l-slate-500",
  }[accent] || "border-l-slate-500";

  return (
    <div className="space-y-4" data-testid={`${testidPrefix}-view`}>
      {/* iter365 · operational coaching uniformity — short, field-direct.
          Used by both Dispatch + FL portals via the shared component. */}
      <LifecycleGuide
        id={`driver-qualification-${testidPrefix || "view"}`}
        icon={ShieldCheck}
        accent="emerald"
        title={t("How driver readiness works")}
        summary={t("A driver is dispatchable only when active, approved, CDL valid (if CDL holder), and medical card valid.")}
        sections={[
          { label: t("Why this matters"), body: t("Sending an unqualified driver creates legal and safety exposure. The emerald tile above is your one-click 'who can I send right now' answer.") },
          { label: t("Read-only"), body: t("Status, CDL, and medical-card data are owned by HR. To correct anything, contact HR — this view never edits the source.") },
        ]}
      />

      {/* iter353b-availability · "Drivers Available Right Now" hero tile.
          The single most important operational question for Dispatch +
          FL — "who can I legally and operationally send out right now?"
          Click to filter the table down to currently-dispatchable
          drivers only. */}
      <button
        type="button"
        onClick={() => setAvailableOnly((v) => !v)}
        className={`w-full text-left border-2 rounded-md p-4 transition-colors group ${
          availableOnly
            ? "border-emerald-600 bg-emerald-600 text-white"
            : "border-emerald-500 bg-emerald-50 hover:bg-emerald-100 text-emerald-950"
        }`}
        data-testid={`${testidPrefix}-availability-tile`}
      >
        <div className="flex items-start gap-4">
          <Zap className={`w-7 h-7 mt-1 shrink-0 ${availableOnly ? "text-white" : "text-emerald-700"}`} />
          <div className="flex-1 min-w-0">
            <div className={`font-mono text-[10px] uppercase tracking-[0.22em] font-bold ${availableOnly ? "text-emerald-100" : "text-emerald-800"}`}>
              {t("Drivers Available Right Now")}
            </div>
            <div className="flex items-baseline gap-3 mt-1 flex-wrap">
              <div className="font-display text-4xl font-black leading-none" data-testid={`${testidPrefix}-availability-total`}>
                {data.summary?.available_now ?? 0}
              </div>
              <div className={`text-xs ${availableOnly ? "text-emerald-100" : "text-emerald-800"}`}>
                <span className="font-mono">
                  <strong data-testid={`${testidPrefix}-availability-cdl`}>{data.summary?.available_now_cdl ?? 0}</strong> {t("CDL")}
                  {" · "}
                  <strong data-testid={`${testidPrefix}-availability-non-cdl`}>{data.summary?.available_now_non_cdl ?? 0}</strong> {t("non-CDL approved")}
                </span>
              </div>
            </div>
            <div className={`text-xs mt-1.5 ${availableOnly ? "text-emerald-50" : "text-emerald-900"}`}>
              {t("Active · approved · CDL valid · medical valid")} ·{" "}
              <span className="underline underline-offset-2 group-hover:font-bold">
                {availableOnly ? t("Showing dispatchable only — click to clear") : t("Click to filter")}
              </span>
            </div>
          </div>
        </div>
      </button>

      {/* Read-only banner */}
      <div
        className={`bg-white border border-slate-200 border-l-4 ${accentBar} rounded-md p-4`}
        data-testid={`${testidPrefix}-banner`}
      >
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold flex items-center gap-1.5">
          <ShieldCheck className="w-3 h-3" /> {t("Read-only · Driver Qualification")}
        </div>
        <div className="text-sm text-slate-700 mt-1">
          {t("Verify approved-driver and CDL readiness before sending or assigning someone to work. Editing happens in HR — corrections are made there.")}
        </div>
      </div>

      {/* Summary tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3" data-testid={`${testidPrefix}-summary`}>
        <SummaryCard icon={Truck} label={t("Drivers in scope")} value={data.count ?? 0} tint="slate" testid={`${testidPrefix}-tile-count`} />
        <SummaryCard icon={AlertTriangle} label={t("CDL expiring ≤30d")} value={data.summary?.cdl_expiring_30d ?? 0} tint={data.summary?.cdl_expiring_30d ? "amber" : "slate"} testid={`${testidPrefix}-tile-cdl-30d`} />
        <SummaryCard icon={AlertTriangle} label={t("Medical ≤30d")} value={data.summary?.medical_card_expiring_30d ?? 0} tint={data.summary?.medical_card_expiring_30d ? "amber" : "slate"} testid={`${testidPrefix}-tile-med-30d`} />
        <SummaryCard icon={FileX} label={t("Restricted")} value={data.summary?.restricted ?? 0} tint={data.summary?.restricted ? "amber" : "slate"} testid={`${testidPrefix}-tile-restricted`} />
        <SummaryCard icon={FileX} label={t("Suspended")} value={data.summary?.suspended ?? 0} tint={data.summary?.suspended ? "rose" : "slate"} testid={`${testidPrefix}-tile-suspended`} />
      </div>

      {/* Filters */}
      <div className="bg-white border border-slate-200 rounded-md p-3 grid grid-cols-1 sm:grid-cols-5 gap-2 items-end" data-testid={`${testidPrefix}-filters`}>
        <div className="sm:col-span-2">
          <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold flex items-center gap-1.5 mb-1">
            <Search className="w-3 h-3" /> {t("Search")}
          </label>
          <Input
            value={q} onChange={(e) => setQ(e.target.value)}
            placeholder={t("Name · employee ID · CDL #")}
            className="h-9 text-sm"
            data-testid={`${testidPrefix}-search`}
          />
        </div>
        <div>
          <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">{t("CDL")}</label>
          <Select value={cdl} onValueChange={setCdl}>
            <SelectTrigger className="h-9 text-sm" data-testid={`${testidPrefix}-filter-cdl`}><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="any">{t("Any")}</SelectItem>
              <SelectItem value="true">{t("CDL holders only")}</SelectItem>
              <SelectItem value="false">{t("Non-CDL")}</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">{t("Approved Driver")}</label>
          <Select value={approved} onValueChange={setApproved}>
            <SelectTrigger className="h-9 text-sm" data-testid={`${testidPrefix}-filter-approved`}><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="any">{t("Any")}</SelectItem>
              <SelectItem value="true">{t("Approved only")}</SelectItem>
              <SelectItem value="false">{t("Not approved")}</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-1 block">{t("Status")}</label>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="h-9 text-sm" data-testid={`${testidPrefix}-filter-status`}><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="any">{t("Any")}</SelectItem>
              <SelectItem value="active">{t("Active")}</SelectItem>
              <SelectItem value="restricted">{t("Restricted")}</SelectItem>
              <SelectItem value="suspended">{t("Suspended")}</SelectItem>
              <SelectItem value="inactive">{t("Inactive")}</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="sm:col-span-5 flex justify-end">
          <Button variant="outline" size="sm" onClick={load} disabled={loading} data-testid={`${testidPrefix}-refresh`}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? "animate-spin" : ""}`} /> {t("Refresh")}
          </Button>
        </div>
      </div>

      {/* Error */}
      {err ? (
        <div className="bg-rose-50 border border-rose-300 rounded-md p-3 text-sm text-rose-900" data-testid={`${testidPrefix}-error`}>
          {err}
        </div>
      ) : null}

      {/* Empty state */}
      {!loading && !err && (data.items?.length ?? 0) === 0 ? (
        <div className="bg-white border-2 border-dashed border-slate-200 rounded-md p-8 text-center text-sm text-slate-500" data-testid={`${testidPrefix}-empty`}>
          {t("No driver-qualified employees match the current filter.")}
        </div>
      ) : null}

      {/* Desktop table */}
      {(data.items?.length ?? 0) > 0 ? (
        <>
          <div className="hidden sm:block bg-white border border-slate-200 rounded-md overflow-x-auto" data-testid={`${testidPrefix}-table`}>
            <table className="w-full text-sm min-w-[900px]">
              <thead className="bg-slate-50">
                <tr className="text-left text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                  <th className="px-3 py-2">{t("Name")}</th>
                  <th className="px-3 py-2">{t("Trade")}</th>
                  <th className="px-3 py-2">{t("CDL")}</th>
                  <th className="px-3 py-2">{t("Approved")}</th>
                  <th className="px-3 py-2">{t("Status")}</th>
                  <th className="px-3 py-2">{t("CDL Expires")}</th>
                  <th className="px-3 py-2">{t("Medical")}</th>
                  <th className="px-3 py-2">{t("Endorsements")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((e) => (
                  <tr key={e.id} data-testid={`${testidPrefix}-row-${e.id}`}
                      onClick={onRowClick ? () => onRowClick(e) : undefined}
                      className={onRowClick ? "cursor-pointer hover:bg-slate-50" : ""}>
                    <td className="px-3 py-2 font-semibold text-slate-900">
                      {e.name}
                      {e.employee_id ? <span className="ml-2 text-[10px] font-mono text-slate-400">#{e.employee_id}</span> : null}
                    </td>
                    <td className="px-3 py-2 text-slate-600 text-xs">{e.trade || "—"}</td>
                    <td className="px-3 py-2"><StatusPill value={e.cdl_holder ? "Yes" : "No"} /></td>
                    <td className="px-3 py-2"><StatusPill value={e.approved_company_driver ? "Yes" : "No"} /></td>
                    <td className="px-3 py-2"><StatusPill value={e.driver_status} /></td>
                    <td className="px-3 py-2"><DateCell value={e.cdl_expiration_date} /></td>
                    <td className="px-3 py-2"><DateCell value={e.medical_card_expiration_date} /></td>
                    <td className="px-3 py-2 text-slate-600 text-xs font-mono">
                      {(e.cdl_endorsements || []).join(", ") || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="sm:hidden space-y-2" data-testid={`${testidPrefix}-cards`}>
            {data.items.map((e) => (
              <div key={e.id}
                   className={`bg-white border border-slate-200 rounded-md p-3 ${onRowClick ? "cursor-pointer hover:border-slate-400" : ""}`}
                   onClick={onRowClick ? () => onRowClick(e) : undefined}
                   data-testid={`${testidPrefix}-card-${e.id}`}>
                <div className="flex items-start justify-between gap-2">
                  <div className="font-semibold text-slate-900">{e.name}</div>
                  <div className="flex flex-wrap gap-1">
                    <StatusPill value={e.cdl_holder ? "Yes" : "No"} />
                    <StatusPill value={e.approved_company_driver ? "Yes" : "No"} />
                  </div>
                </div>
                <div className="text-xs text-slate-600 mt-1">
                  {e.trade || "—"} {e.employee_id ? <span className="font-mono ml-1">#{e.employee_id}</span> : null}
                </div>
                <div className="flex items-center gap-3 mt-2 text-[11px]">
                  <StatusPill value={e.driver_status} />
                  <span className="text-slate-500"><Filter className="w-3 h-3 inline mr-1" />{(e.cdl_endorsements || []).join(",") || "—"}</span>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[11px] text-slate-600">
                  <span><strong>{t("CDL")}:</strong> <DateCell value={e.cdl_expiration_date} /></span>
                  <span><strong>{t("Medical")}:</strong> <DateCell value={e.medical_card_expiration_date} /></span>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : null}

      <div className="text-[11px] text-slate-500 font-mono pt-1 border-t border-slate-200" data-testid={`${testidPrefix}-footer`}>
        {t("Read-only · source roster owned by HR · last verified")} {data.as_of || "—"}
      </div>
    </div>
  );
}
