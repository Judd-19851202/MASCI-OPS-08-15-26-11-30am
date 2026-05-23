// iter353e-UI · PM Crew Compliance Lens (read-only).
// Route: /pm/crew-compliance
// Surfaces the iter353e backend `/api/pm/crew/*` endpoints as a
// dedicated PM-facing operational awareness page. STRICTLY read-only —
// no edit, no CAPA closure, no certification administration. Scope:
// every employee whose name has appeared on a daily report under a
// PM-assigned project in the last 180 days.
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle, CircleSlash, Users, Activity, ShieldCheck, ClipboardCheck,
  ArrowRight, RefreshCw, Search,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import PmShell from "@/components/PmShell";
import { api } from "@/lib/api";
import { operationalError } from "@/lib/errors";
import { useT } from "@/lib/i18n";
import { usePageTitle } from "@/lib/usePageTitle";
import { LifecycleGuide } from "@/components/LifecycleGuide";
import { Users as UsersIcon } from "lucide-react";

function SeverityPill({ value, kind = "info" }) {
  const tints = {
    info:    "bg-slate-100 text-slate-700 border-slate-200",
    amber:   "bg-amber-100 text-amber-900 border-amber-300",
    rose:    "bg-rose-100 text-rose-900 border-rose-300",
    emerald: "bg-emerald-100 text-emerald-900 border-emerald-300",
  };
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 border rounded text-[10px] font-mono uppercase tracking-wider ${tints[kind]}`}>
      {value}
    </span>
  );
}

function SummaryTile({ icon: Icon, label, value, tint = "slate", testid, onClick }) {
  const tints = {
    slate:   "border-slate-300 bg-white text-slate-900",
    amber:   "border-amber-400 bg-amber-50 text-amber-900",
    rose:    "border-rose-400 bg-rose-50 text-rose-900",
    emerald: "border-emerald-400 bg-emerald-50 text-emerald-900",
  };
  const C = onClick ? "button" : "div";
  return (
    <C
      type={onClick ? "button" : undefined}
      onClick={onClick}
      className={`border-2 ${tints[tint]} rounded-md p-3 text-left ${onClick ? "hover:shadow-md cursor-pointer transition-shadow" : ""}`}
      data-testid={testid}
    >
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 opacity-70" />
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-70">{label}</div>
      </div>
      <div className="font-display text-2xl font-black mt-1 leading-none">{value}</div>
    </C>
  );
}

function DateCell({ value }) {
  if (!value) return <span className="text-slate-400">—</span>;
  const today = new Date().toISOString().slice(0, 10);
  const cutoff30 = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
  let tint = "text-slate-700";
  if (value < today) tint = "text-rose-700 font-semibold";
  else if (value <= cutoff30) tint = "text-amber-700 font-semibold";
  return <span className={`font-mono text-xs ${tint}`}>{value}</span>;
}

export default function PmCrewCompliance() {
  const { t } = useT();
  usePageTitle("PM · Crew Compliance");
  const [summary, setSummary] = useState({});
  const [training, setTraining] = useState([]);
  const [ppe, setPpe] = useState([]);
  const [capas, setCapas] = useState([]);
  const [tab, setTab] = useState("training");
  const [filterMode, setFilterMode] = useState("all"); // all | expiring | expired
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try {
      const [s, tr, pp, ca] = await Promise.all([
        api.get("/pm/crew/summary"),
        api.get("/pm/crew/training-records"),
        api.get("/pm/crew/ppe"),
        api.get("/pm/crew/capas"),
      ]);
      setSummary(s.data || {});
      setTraining(tr.data?.items || []);
      setPpe(pp.data?.items || []);
      setCapas(ca.data?.items || []);
    } catch (e) {
      setErr(operationalError(e, t("Could not load crew compliance.")));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { load(); }, [load]);

  const today = new Date().toISOString().slice(0, 10);
  const cutoff30 = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);

  const trainingFiltered = useMemo(() => {
    let rows = training;
    if (filterMode === "expired") {
      rows = rows.filter((r) => r.expiration_date && r.expiration_date < today);
    } else if (filterMode === "expiring") {
      rows = rows.filter((r) => r.expiration_date && r.expiration_date >= today && r.expiration_date <= cutoff30);
    }
    if (q.trim()) {
      const qq = q.trim().toLowerCase();
      rows = rows.filter((r) =>
        (r.employee_name || "").toLowerCase().includes(qq)
        || (r.training_name || "").toLowerCase().includes(qq)
        || (r.certification_type || "").toLowerCase().includes(qq)
      );
    }
    return rows;
  }, [training, filterMode, q, today, cutoff30]);

  const ppeFiltered = useMemo(() => {
    if (!q.trim()) return ppe;
    const qq = q.trim().toLowerCase();
    return ppe.filter((r) =>
      (r.employee_name || "").toLowerCase().includes(qq)
      || (r.equipment_type || "").toLowerCase().includes(qq)
    );
  }, [ppe, q]);

  const capasFiltered = useMemo(() => {
    if (!q.trim()) return capas;
    const qq = q.trim().toLowerCase();
    return capas.filter((r) =>
      (r.employee_name || r.linked_employee_name || "").toLowerCase().includes(qq)
      || (r.title || r.description || "").toLowerCase().includes(qq)
    );
  }, [capas, q]);

  const crewSize = summary.crew_size ?? 0;
  const scope = summary.scope || "—";

  return (
    <PmShell
      title={t("My Crew Compliance")}
      section="overview"
      intro={
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-600 text-white shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="text-sm text-slate-700 leading-relaxed">
            {t("Read-only operational awareness for the crews on your projects. Scope: every employee on a daily report under your projects in the last 180 days. For corrections, contact HR or Safety — this view is read-only.")}
          </div>
        </div>
      }
    >
      <div className="space-y-4 mt-5" data-testid="pm-crew-compliance">
        {/* iter365 · operational coaching uniformity — short, field-direct. */}
        <LifecycleGuide
          id="pm-crew-compliance"
          icon={UsersIcon}
          accent="amber"
          title={t("How your crew compliance view works")}
          summary={t("Read-only roll-up of everyone on your projects' daily reports in the last 180 days.")}
          sections={[
            { label: t("Why this matters"), body: t("If someone on your crew has an expired training or missing PPE, you see it before the field does. Corrections happen in HR / Safety — not here.") },
          ]}
        />

        {/* Summary tiles */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3" data-testid="pm-crew-summary">
          <SummaryTile
            icon={Users}
            label={t("Crew size (180d)")}
            value={crewSize}
            testid="pm-crew-tile-size"
          />
          <SummaryTile
            icon={AlertTriangle}
            label={t("Training expiring ≤30d")}
            value={summary.expiring_30d ?? 0}
            tint={summary.expiring_30d ? "amber" : "slate"}
            onClick={() => { setTab("training"); setFilterMode("expiring"); }}
            testid="pm-crew-tile-expiring"
          />
          <SummaryTile
            icon={CircleSlash}
            label={t("Training expired")}
            value={summary.expired ?? 0}
            tint={summary.expired ? "rose" : "slate"}
            onClick={() => { setTab("training"); setFilterMode("expired"); }}
            testid="pm-crew-tile-expired"
          />
          <SummaryTile
            icon={ClipboardCheck}
            label={t("Open CAPAs")}
            value={summary.open_capas ?? 0}
            tint={summary.open_capas ? "amber" : "slate"}
            onClick={() => setTab("capas")}
            testid="pm-crew-tile-capas"
          />
          <SummaryTile
            icon={ShieldCheck}
            label={t("PPE records")}
            value={summary.ppe_records ?? 0}
            tint="slate"
            onClick={() => setTab("ppe")}
            testid="pm-crew-tile-ppe"
          />
        </div>

        {/* Read-only banner + scope indicator */}
        <div className="bg-white border border-slate-200 border-l-4 border-l-amber-600 rounded-md p-3 text-xs text-slate-700 flex items-center gap-3 flex-wrap" data-testid="pm-crew-banner">
          <ShieldCheck className="w-4 h-4 text-amber-700" />
          <span>{t("Read-only PM operational awareness.")}</span>
          <SeverityPill value={scope === "pm_crew_180d" ? t("My crew · 180d") : t("Admin all")} kind="info" />
          {!loading && (
            <span className="ml-auto text-[10px] font-mono text-slate-400">
              {t("Updated")}: <DateCell value={today} />
            </span>
          )}
        </div>

        {err ? (
          <div className="bg-rose-50 border border-rose-300 rounded-md p-3 text-sm text-rose-900" data-testid="pm-crew-error">{err}</div>
        ) : null}

        {/* Filter bar */}
        <div className="bg-white border border-slate-200 rounded-md p-3 flex flex-wrap items-end gap-2" data-testid="pm-crew-filters">
          <div className="flex-1 min-w-[200px]">
            <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold flex items-center gap-1.5 mb-1">
              <Search className="w-3 h-3" /> {t("Search")}
            </label>
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("Employee · training · equipment · CAPA")}
              className="h-9 text-sm"
              data-testid="pm-crew-search"
            />
          </div>
          <Button variant="outline" size="sm" onClick={load} disabled={loading} data-testid="pm-crew-refresh">
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? "animate-spin" : ""}`} /> {t("Refresh")}
          </Button>
        </div>

        {/* Tabs */}
        <Tabs value={tab} onValueChange={setTab} data-testid="pm-crew-tabs">
          <TabsList>
            <TabsTrigger value="training" data-testid="pm-crew-tab-training">
              {t("Training")} <span className="ml-1.5 text-[10px] font-mono opacity-60">{training.length}</span>
            </TabsTrigger>
            <TabsTrigger value="ppe" data-testid="pm-crew-tab-ppe">
              {t("PPE")} <span className="ml-1.5 text-[10px] font-mono opacity-60">{ppe.length}</span>
            </TabsTrigger>
            <TabsTrigger value="capas" data-testid="pm-crew-tab-capas">
              {t("CAPAs")} <span className="ml-1.5 text-[10px] font-mono opacity-60">{capas.length}</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="training" className="mt-3">
            {tab === "training" && filterMode !== "all" ? (
              <div className="mb-2 flex items-center gap-2 text-xs">
                <SeverityPill
                  value={filterMode === "expired" ? t("Showing expired only") : t("Showing expiring ≤30d")}
                  kind={filterMode === "expired" ? "rose" : "amber"}
                />
                <button type="button" onClick={() => setFilterMode("all")} className="text-slate-600 hover:text-slate-900 underline underline-offset-2" data-testid="pm-crew-filter-clear">
                  {t("Clear filter")}
                </button>
              </div>
            ) : null}
            <CrewTrainingTable
              items={trainingFiltered}
              today={today}
              cutoff30={cutoff30}
              empty={t("No training records match the current filter.")}
            />
          </TabsContent>

          <TabsContent value="ppe" className="mt-3">
            <CrewPpeTable items={ppeFiltered} empty={t("No PPE issuance records yet.")} />
          </TabsContent>

          <TabsContent value="capas" className="mt-3">
            <CrewCapasTable items={capasFiltered} empty={t("No open CAPAs involving crew.")} />
          </TabsContent>
        </Tabs>
      </div>
    </PmShell>
  );
}

function EmployeeLink({ name, id }) {
  if (!id) return <span className="font-semibold text-slate-900">{name || "—"}</span>;
  return (
    <Link
      to={`/hr/employees/${id}/accountability`}
      className="font-semibold text-purple-800 hover:text-purple-900 hover:underline inline-flex items-center gap-1"
      data-testid="pm-crew-emp-link"
    >
      {name || "—"} <ArrowRight className="w-3 h-3 opacity-60" />
    </Link>
  );
}

function CrewTrainingTable({ items, today, cutoff30, empty }) {
  const { t } = useT();
  if (items.length === 0) {
    return <div className="bg-white border-2 border-dashed border-slate-200 rounded-md p-8 text-center text-sm text-slate-500" data-testid="pm-crew-training-empty">{empty}</div>;
  }
  return (
    <>
      <div className="hidden sm:block bg-white border border-slate-200 rounded-md overflow-x-auto" data-testid="pm-crew-training-table">
        <table className="w-full text-sm min-w-[800px]">
          <thead className="bg-slate-50">
            <tr className="text-left text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
              <th className="px-3 py-2">{t("Employee")}</th>
              <th className="px-3 py-2">{t("Training")}</th>
              <th className="px-3 py-2 w-32">{t("Completed")}</th>
              <th className="px-3 py-2 w-32">{t("Expires")}</th>
              <th className="px-3 py-2 w-24">{t("Severity")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((r) => {
              const exp = r.expiration_date;
              let sev = { v: t("Current"), k: "emerald" };
              if (exp && exp < today) sev = { v: t("Expired"), k: "rose" };
              else if (exp && exp <= cutoff30) sev = { v: t("≤30d"), k: "amber" };
              return (
                <tr key={r.id}>
                  <td className="px-3 py-2"><EmployeeLink name={r.employee_name} id={r.employee_id} /></td>
                  <td className="px-3 py-2 text-slate-700">{r.training_name || r.certification_type || "—"}</td>
                  <td className="px-3 py-2"><DateCell value={r.completed_date} /></td>
                  <td className="px-3 py-2"><DateCell value={r.expiration_date} /></td>
                  <td className="px-3 py-2"><SeverityPill value={sev.v} kind={sev.k} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="sm:hidden space-y-2" data-testid="pm-crew-training-cards">
        {items.map((r) => {
          const exp = r.expiration_date;
          let sev = { v: t("Current"), k: "emerald" };
          if (exp && exp < today) sev = { v: t("Expired"), k: "rose" };
          else if (exp && exp <= cutoff30) sev = { v: t("≤30d"), k: "amber" };
          return (
            <div key={r.id} className="bg-white border border-slate-200 rounded-md p-3">
              <div className="flex items-start justify-between gap-2">
                <EmployeeLink name={r.employee_name} id={r.employee_id} />
                <SeverityPill value={sev.v} kind={sev.k} />
              </div>
              <div className="text-xs text-slate-700 mt-1">{r.training_name || r.certification_type || "—"}</div>
              <div className="text-[11px] text-slate-500 font-mono mt-1.5 flex justify-between">
                <span>{t("Done")}: {r.completed_date || "—"}</span>
                <span>{t("Exp")}: <DateCell value={r.expiration_date} /></span>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}

function CrewPpeTable({ items, empty }) {
  const { t } = useT();
  if (items.length === 0) {
    return <div className="bg-white border-2 border-dashed border-slate-200 rounded-md p-8 text-center text-sm text-slate-500" data-testid="pm-crew-ppe-empty">{empty}</div>;
  }
  return (
    <div className="bg-white border border-slate-200 rounded-md overflow-x-auto" data-testid="pm-crew-ppe-table">
      <table className="w-full text-sm min-w-[600px]">
        <thead className="bg-slate-50">
          <tr className="text-left text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
            <th className="px-3 py-2">{t("Employee")}</th>
            <th className="px-3 py-2">{t("Equipment")}</th>
            <th className="px-3 py-2 w-32">{t("Issued")}</th>
            <th className="px-3 py-2 w-32">{t("Condition")}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((r) => (
            <tr key={r.id}>
              <td className="px-3 py-2 font-semibold text-slate-900">{r.employee_name || "—"}</td>
              <td className="px-3 py-2 text-slate-700 text-xs">{r.equipment_type || "—"}</td>
              <td className="px-3 py-2 text-xs"><DateCell value={r.issued_date} /></td>
              <td className="px-3 py-2 text-xs text-slate-600">{r.condition || r.size || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CrewCapasTable({ items, empty }) {
  const { t } = useT();
  if (items.length === 0) {
    return <div className="bg-white border-2 border-dashed border-slate-200 rounded-md p-8 text-center text-sm text-slate-500" data-testid="pm-crew-capas-empty">{empty}</div>;
  }
  return (
    <div className="bg-white border border-slate-200 rounded-md overflow-x-auto" data-testid="pm-crew-capas-table">
      <table className="w-full text-sm min-w-[700px]">
        <thead className="bg-slate-50">
          <tr className="text-left text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">
            <th className="px-3 py-2">{t("Employee")}</th>
            <th className="px-3 py-2">{t("CAPA")}</th>
            <th className="px-3 py-2 w-24">{t("Status")}</th>
            <th className="px-3 py-2 w-32">{t("Due")}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {items.map((r) => {
            const status = (r.status || "open").toLowerCase();
            const k = ["closed", "completed", "verified"].includes(status) ? "emerald" : "amber";
            return (
              <tr key={r.id}>
                <td className="px-3 py-2 font-semibold text-slate-900">{r.linked_employee_name || r.employee_name || "—"}</td>
                <td className="px-3 py-2 text-slate-700 text-xs">{r.title || r.description || "—"}</td>
                <td className="px-3 py-2"><SeverityPill value={r.status || "open"} kind={k} /></td>
                <td className="px-3 py-2 text-xs"><DateCell value={r.due_date} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
