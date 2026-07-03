// iter353c · Unified Employee Accountability Timeline page.
// Aggregated read-only view of an employee's full operational record:
// training · PPE · incidents · CDL/medical · Field Leadership · HR
// lifecycle history. NOT a new source of truth — purely aggregation
// of `safety_training_records`, `training_track_records`,
// `safety_equipment_issuances`, `safety_equipment_trainings`,
// `incidents`, `field_leadership_records`, and `employees`.
// Route: /hr/employees/:id/accountability
// RBAC: HR + Safety + Admin can view (operator policy: shared
// accountability between HR + Safety, iter353a).
import React, { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useParams, Link } from "react-router-dom";
import {
  Download, FileText, ShieldCheck, AlertTriangle,
  Calendar, Truck, HardHat, Activity, History, FileCheck2,
  CircleSlash, RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { PortalShell } from "@/design-system";
import HrSideNavV2 from "@/components/hr/sidebar/HrSideNavV2";
import AccessDenied from "@/pages/AccessDenied";
import { isHr } from "@/lib/hrAuth";
import { isSafety } from "@/lib/safetyAuth";
import { isAdmin } from "@/lib/adminAuth";
import { getHrToken } from "@/lib/hrAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";
import { useT } from "@/lib/i18n";
import { formatUtcForAudit } from "@/lib/dateUtils";
import { LifecycleGuide } from "@/components/LifecycleGuide";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  const h = {};
  const a = getAdminToken(); if (a) h["X-Admin-Token"] = a;
  const hr = getHrToken(); if (hr) h["X-HR-Token"] = hr;
  const sf = getSafetyToken(); if (sf) h["X-Safety-Token"] = sf;
  return h;
}

const ROLE_PILL = {
  hr:     "bg-purple-100 text-purple-900 border-purple-200",
  safety: "bg-cyan-100 text-cyan-900 border-cyan-200",
  admin:  "bg-slate-200 text-slate-900 border-slate-300",
  pm:     "bg-indigo-100 text-indigo-900 border-indigo-200",
  fl:     "bg-red-100 text-red-900 border-red-200",
  dispatch: "bg-amber-100 text-amber-900 border-amber-200",
  shop:   "bg-orange-100 text-orange-900 border-orange-200",
  legacy: "bg-slate-100 text-slate-600 border-slate-200",
};

const CATEGORY_ICONS = {
  "Training":            Activity,
  "PPE & Equipment":     HardHat,
  "Incidents":           AlertTriangle,
  "Field Leadership":    ShieldCheck,
  "HR Lifecycle":        History,
  "Driver Qualification": Truck,
};

function RolePill({ role }) {
  const r = (role || "legacy").toLowerCase();
  const cls = ROLE_PILL[r] || ROLE_PILL.legacy;
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 border rounded text-[10px] font-mono uppercase tracking-wider ${cls}`}
      data-testid={`role-pill-${r}`}
    >
      {r}
    </span>
  );
}

function StatusTile({ icon: Icon, label, value, tint = "slate", testid }) {
  const tints = {
    slate:   "border-slate-200 bg-white text-slate-900",
    purple:  "border-purple-300 bg-purple-50 text-purple-900",
    cyan:    "border-cyan-300 bg-cyan-50 text-cyan-900",
    amber:   "border-amber-300 bg-amber-50 text-amber-900",
    rose:    "border-rose-300 bg-rose-50 text-rose-900",
    emerald: "border-emerald-300 bg-emerald-50 text-emerald-900",
  };
  return (
    <div
      className={`border-2 rounded-md p-3 ${tints[tint]}`}
      data-testid={testid}
    >
      <div className="flex items-start gap-2">
        <Icon className="w-4 h-4 mt-0.5 opacity-70" />
        <div className="min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-70 truncate">{label}</div>
          <div className="font-display text-lg font-black leading-tight mt-0.5 break-words">{value}</div>
        </div>
      </div>
    </div>
  );
}

export default function HrEmployeeAccountabilityTimeline() {
  const { id } = useParams();
  const { t } = useT();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState("all");
  const [downloading, setDownloading] = useState(false);

  // Auth: any of HR / Safety / Admin can view.
  const allowed = isHr() || isSafety() || isAdmin();

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try {
      const r = await axios.get(
        `${API}/hr/employees/${id}/accountability/timeline`,
        { headers: authHeaders() },
      );
      setData(r.data);
    } catch (e) {
      setErr(operationalError(e, t("Could not load accountability timeline.")));
    } finally {
      setLoading(false);
    }
  }, [id, t]);

  useEffect(() => { if (allowed) load(); }, [allowed, load]);

  const downloadPdf = async () => {
    setDownloading(true);
    try {
      const r = await axios.get(
        `${API}/hr/employees/${id}/accountability/brief.pdf`,
        { headers: authHeaders(), responseType: "blob" },
      );
      const url = window.URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `HR_Compliance_Brief_${(data?.employee?.name || id).replace(/\s+/g, "_")}.pdf`;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(t("Compliance brief downloaded"));
    } catch (e) {
      toast.error(operationalError(e, t("Could not download PDF.")));
    } finally {
      setDownloading(false);
    }
  };

  const filtered = useMemo(() => {
    const events = data?.events || [];
    if (tab === "all") return events;
    const tabMap = {
      training:  ["Training"],
      ppe:       ["PPE & Equipment"],
      incidents: ["Incidents"],
      fl:        ["Field Leadership"],
      lifecycle: ["HR Lifecycle"],
      driver:    ["Driver Qualification"],
    };
    const cats = tabMap[tab] || [];
    return events.filter((e) => cats.includes(e.category));
  }, [data, tab]);

  if (!allowed) return <AccessDenied attemptedPortal="hr" />;

  const emp = data?.employee || {};
  const cs = data?.current_state || {};
  const counts = data?.category_counts || {};

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="HR Portal · Accountability"
      pageTitle={t("Accountability Timeline")}
      subtitle={t("Aggregated read-only view of an employee's training, PPE, incidents, and lifecycle history.")}
      sideNav={<HrSideNavV2 />}
      primaryActions={
        <div className="flex items-center gap-2" data-testid="acct-header-actions">
          {/* Track 19.56 · promote to Universal Thread view. Same
             payload, presented through the shared shell. */}
          <Link
            to={`/hr/employees/${encodeURIComponent(id)}/thread`}
            data-testid="acct-open-thread-link"
            className="inline-flex items-center px-3 py-1.5 text-xs font-mono font-bold uppercase tracking-widest border-2 border-slate-300 hover:border-slate-900 text-slate-900 rounded"
          >
            Universal Thread
          </Link>
          <Button
            variant="outline" size="sm" onClick={load} disabled={loading}
            data-testid="acct-refresh-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${loading ? "animate-spin" : ""}`} />
            {t("Refresh")}
          </Button>
          <Button
            size="sm" onClick={downloadPdf}
            disabled={downloading || loading || !data}
            className="bg-purple-700 hover:bg-purple-800 text-white"
            data-testid="acct-download-pdf-btn"
          >
            <Download className="w-4 h-4 mr-1" />
            {downloading ? t("Generating…") : t("Compliance Brief PDF")}
          </Button>
        </div>
      }
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-5 space-y-5" data-testid="hr-accountability-page">
        {/* iter365 · operational coaching uniformity — short, field-direct. */}
        <LifecycleGuide
          id="employee-accountability-timeline"
          icon={History}
          accent="indigo"
          title={t("How this timeline works")}
          summary={t("One employee · every operational record from every portal · read-only.")}
          sections={[
            { label: t("Why this matters"), body: t("If a CAPA, training, PPE, incident, or CDL/medical event touches this person, it shows up here. This is how the platform builds trust in the roster.") },
            { label: t("Source of truth"), body: t("Corrections happen in the original portal — this view aggregates, it doesn't edit. The role pill on each row shows where the record was written.") },
          ]}
        />

        {/* iter366 · legacy "Shared-authority intro" purple band removed —
            the LifecycleGuide above is now the single operational coaching
            surface on this page (no duplicated messaging). */}

        {/* Employee header card */}
        {loading && !data ? (
          <div className="bg-white border border-slate-200 rounded-md p-6 text-sm text-slate-500" data-testid="acct-loading">
            {t("Loading employee accountability…")}
          </div>
        ) : err ? (
          <div className="bg-rose-50 border border-rose-300 rounded-md p-4 text-sm text-rose-900" data-testid="acct-error">
            {err}
          </div>
        ) : (
          <>
            <div
              className="bg-white border border-slate-200 rounded-md p-5"
              data-testid="acct-employee-header"
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-purple-700 font-bold">{t("Employee")}</div>
              <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 mt-1" data-testid="acct-employee-name">
                {emp.name || "—"}
              </h1>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600 mt-2">
                {emp.trade && <span><strong>{t("Trade")}:</strong> {emp.trade}</span>}
                {emp.crew && <span><strong>{t("Crew")}:</strong> {emp.crew}</span>}
                {emp.supervisor && <span><strong>{t("Supervisor")}:</strong> {emp.supervisor}</span>}
                {emp.employee_id && <span className="font-mono text-[11px]">#{emp.employee_id}</span>}
                {emp.lifecycle_status && (
                  <span className="font-mono text-[11px] uppercase px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded">
                    {emp.lifecycle_status}
                  </span>
                )}
              </div>
            </div>

            {/* Current state tiles */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3" data-testid="acct-state-tiles">
              <StatusTile
                icon={Truck} label={t("CDL Holder")}
                value={cs.cdl_holder ? t("Yes") : t("No")}
                tint={cs.cdl_holder ? "cyan" : "slate"}
                testid="acct-tile-cdl"
              />
              <StatusTile
                icon={Truck} label={t("Approved Driver")}
                value={cs.approved_company_driver ? t("Yes") : t("No")}
                tint={cs.approved_company_driver ? "cyan" : "slate"}
                testid="acct-tile-approved"
              />
              <StatusTile
                icon={Calendar} label={t("CDL Expires")}
                value={cs.cdl_expiration_date || "—"}
                tint={cs.cdl_expiration_date ? "slate" : "slate"}
                testid="acct-tile-cdl-exp"
              />
              <StatusTile
                icon={FileCheck2} label={t("Medical Card")}
                value={cs.medical_card_expiration_date || "—"}
                tint="slate"
                testid="acct-tile-medical"
              />
              <StatusTile
                icon={AlertTriangle} label={t("Expiring ≤90d")}
                value={cs.expiring_within_90d ?? 0}
                tint={cs.expiring_within_90d ? "amber" : "slate"}
                testid="acct-tile-expiring"
              />
              <StatusTile
                icon={CircleSlash} label={t("Expired")}
                value={cs.expired ?? 0}
                tint={cs.expired ? "rose" : "slate"}
                testid="acct-tile-expired"
              />
            </div>

            {/* Expiration watch strip */}
            {(data?.expiring_within_90d?.length || data?.expired_items?.length) ? (
              <div
                className="bg-amber-50 border-l-4 border-amber-500 rounded-md p-3 text-sm text-amber-900"
                data-testid="acct-expiry-strip"
              >
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold mb-1">
                  {t("Expiration Watch")}
                </div>
                <ul className="space-y-0.5 text-xs">
                  {[...(data?.expired_items || []), ...(data?.expiring_within_90d || [])].slice(0, 6).map((e, i) => (
                    <li key={i} data-testid="acct-expiry-row">
                      <span className="font-mono mr-2">{e.expiration_date}</span>
                      <strong>{e.title}</strong>
                      <span className="ml-2 text-amber-700">({e.category})</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {/* Tabbed timeline */}
            <Tabs value={tab} onValueChange={setTab} data-testid="acct-tabs">
              <TabsList className="flex-wrap h-auto">
                <TabsTrigger value="all" data-testid="acct-tab-all">
                  {t("All")} <span className="ml-1.5 text-[10px] font-mono opacity-60">{data?.total_events || 0}</span>
                </TabsTrigger>
                <TabsTrigger value="training" data-testid="acct-tab-training">
                  {t("Training")} <span className="ml-1.5 text-[10px] font-mono opacity-60">{counts["Training"] || 0}</span>
                </TabsTrigger>
                <TabsTrigger value="ppe" data-testid="acct-tab-ppe">
                  {t("PPE")} <span className="ml-1.5 text-[10px] font-mono opacity-60">{counts["PPE & Equipment"] || 0}</span>
                </TabsTrigger>
                <TabsTrigger value="incidents" data-testid="acct-tab-incidents">
                  {t("Incidents")} <span className="ml-1.5 text-[10px] font-mono opacity-60">{counts["Incidents"] || 0}</span>
                </TabsTrigger>
                <TabsTrigger value="fl" data-testid="acct-tab-fl">
                  {t("FL Records")} <span className="ml-1.5 text-[10px] font-mono opacity-60">{counts["Field Leadership"] || 0}</span>
                </TabsTrigger>
                <TabsTrigger value="driver" data-testid="acct-tab-driver">
                  {t("Driver Qual")} <span className="ml-1.5 text-[10px] font-mono opacity-60">{counts["Driver Qualification"] || 0}</span>
                </TabsTrigger>
                <TabsTrigger value="lifecycle" data-testid="acct-tab-lifecycle">
                  {t("HR Lifecycle")} <span className="ml-1.5 text-[10px] font-mono opacity-60">{counts["HR Lifecycle"] || 0}</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value={tab} className="mt-3">
                {filtered.length === 0 ? (
                  <div
                    className="bg-white border-2 border-dashed border-slate-200 rounded-md p-8 text-center text-sm text-slate-500"
                    data-testid="acct-empty"
                  >
                    {t("No events in this category yet.")}
                  </div>
                ) : (
                  <>
                    {/* Desktop table */}
                    <div className="hidden sm:block overflow-x-auto bg-white border border-slate-200 rounded-md" data-testid="acct-table-desktop">
                      <table className="w-full text-sm min-w-[800px]">
                        <thead className="bg-slate-50">
                          <tr className="text-left text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
                            <th className="px-3 py-2 w-24">{t("Date")}</th>
                            <th className="px-3 py-2 w-32">{t("Category")}</th>
                            <th className="px-3 py-2">{t("Event")}</th>
                            <th className="px-3 py-2 w-32">{t("Expires")}</th>
                            <th className="px-3 py-2 w-32">{t("Source")}</th>
                            <th className="px-3 py-2 w-20">{t("By")}</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {filtered.map((e) => {
                            const Icon = CATEGORY_ICONS[e.category] || Activity;
                            return (
                              <tr
                                key={e.id}
                                className={e.archived ? "opacity-60" : ""}
                                data-testid={`acct-row-${e.kind}`}
                              >
                                <td className="px-3 py-2 font-mono text-[11px] text-slate-600 whitespace-nowrap">
                                  {(e.ts || "").slice(0, 10) || "—"}
                                </td>
                                <td className="px-3 py-2 text-xs text-slate-600">
                                  <span className="inline-flex items-center gap-1">
                                    <Icon className="w-3 h-3" /> {e.category}
                                  </span>
                                </td>
                                <td className="px-3 py-2">
                                  <div className="font-semibold text-slate-900">
                                    {e.title}
                                    {e.archived && (
                                      <span className="ml-2 inline-block px-1 py-0.5 text-[9px] font-mono bg-slate-200 text-slate-700 border border-slate-300 rounded uppercase">
                                        {t("Archived")}
                                      </span>
                                    )}
                                  </div>
                                  {e.description && <div className="text-xs text-slate-600 mt-0.5">{e.description}</div>}
                                </td>
                                <td className="px-3 py-2 text-xs font-mono text-slate-600">{e.expiration_date || "—"}</td>
                                <td className="px-3 py-2 text-[10px] font-mono text-slate-500" data-testid="acct-source-label">
                                  {e.source}
                                </td>
                                <td className="px-3 py-2">
                                  <RolePill role={e.created_by_role} />
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* Mobile card layout */}
                    <div className="sm:hidden space-y-2" data-testid="acct-cards-mobile">
                      {filtered.map((e) => {
                        const Icon = CATEGORY_ICONS[e.category] || Activity;
                        return (
                          <div
                            key={e.id}
                            className={`bg-white border border-slate-200 rounded-md p-3 ${e.archived ? "opacity-60" : ""}`}
                            data-testid={`acct-card-${e.kind}`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-1 text-xs text-slate-600">
                                <Icon className="w-3 h-3" /> {e.category}
                              </div>
                              <RolePill role={e.created_by_role} />
                            </div>
                            <div className="font-semibold text-slate-900 mt-1.5">
                              {e.title}
                              {e.archived && (
                                <span className="ml-2 inline-block px-1 py-0.5 text-[9px] font-mono bg-slate-200 text-slate-700 border border-slate-300 rounded uppercase">
                                  {t("Archived")}
                                </span>
                              )}
                            </div>
                            {e.description && <div className="text-xs text-slate-600 mt-0.5">{e.description}</div>}
                            <div className="flex items-center gap-3 mt-2 text-[10px] font-mono text-slate-500">
                              <span>{(e.ts || "").slice(0, 10) || "—"}</span>
                              {e.expiration_date && <span>{t("exp")}: {e.expiration_date}</span>}
                              <span className="ml-auto">{e.source}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </>
                )}
              </TabsContent>
            </Tabs>

            <div className="text-[11px] text-slate-500 font-mono flex items-center gap-2 pt-2 border-t border-slate-200" data-testid="acct-footer">
              <FileText className="w-3 h-3" />
              {t("Aggregated view · source records remain authoritative · generated")}{" "}
              {formatUtcForAudit(data?.generated_at)}
            </div>
          </>
        )}
      </div>
    </PortalShell>
  );
}
