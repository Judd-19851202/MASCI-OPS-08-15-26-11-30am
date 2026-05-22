// SafetyFormsRecords — iter323 · Safety Portal review surface for the
// two Safety-owned forms collections:
//   • Equipment Issuance & Accountability (db.safety_equipment_issuances)
//   • Equipment Use & Care Training         (db.safety_equipment_trainings)
//
// Tabs switch between the two collections. Filters by employee, project,
// and date range. Drill-row opens the existing detail viewers under
// /safety/forms/equipment-{issuance,training}/:id — no duplicate detail
// page is built. Safety-owned, no PM access.
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import {
  HardHat, GraduationCap, Search, Loader2, ChevronRight, Filter,
  CheckCircle2, AlertTriangle, Package, Clock, Plus,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import SafetyShell from "@/components/SafetyShell";
import { getSafetyToken } from "@/lib/safetyAuth";
import { useT } from "@/lib/i18n";
import {
  isAgingAccountability,
  accountabilityClassLabels,
} from "@/lib/safetyAccountabilityClass";
import { operationalError } from "@/lib/errors";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const auth = () => ({ headers: { "X-Safety-Token": getSafetyToken() } });

const STATUS_PILL = {
  issued:   "bg-amber-100 text-amber-900 border-amber-300",
  returned: "bg-emerald-100 text-emerald-900 border-emerald-300",
  damaged:  "bg-red-100 text-red-900 border-red-300",
  lost:     "bg-red-200 text-red-950 border-red-400",
};

function issuanceStatus(rec) {
  const ret = rec?.return;
  if (!ret) return "issued";
  // Highest-severity item status wins for the row-level pill.
  const items = Array.isArray(ret.items) ? ret.items : [];
  const has = (s) => items.some((it) => (it.status || "").toLowerCase() === s);
  if (has("lost")) return "lost";
  if (has("damaged")) return "damaged";
  return "returned";
}

export default function SafetyFormsRecords() {
  const { t } = useT();
  const [tab, setTab] = useState("issuance"); // 'issuance' | 'training'
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [employee, setEmployee] = useState("");
  const [project, setProject] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        const path = tab === "issuance"
          ? "/safety-forms/equipment-issuances"
          : "/safety-forms/equipment-trainings";
        const r = await axios.get(`${API}${path}`, auth());
        if (!alive) return;
        const data = Array.isArray(r.data?.items) ? r.data.items : [];
        setItems(data);
      } catch (e) {
        if (alive) {
          toast.error(operationalError(e,
            t("Safety Forms records temporarily unavailable. Try again in a moment."),
            t("Your Safety session expired. Please sign in again.")));
          setItems([]);
        }
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [tab, t]);

  const filtered = useMemo(() => {
    return items.filter((i) => {
      if (employee && !(`${i.employee_name || ""}`.toLowerCase().includes(employee.toLowerCase()))) return false;
      const proj = `${i.project_name || ""} ${i.project_number || ""}`.toLowerCase();
      if (project && !proj.includes(project.toLowerCase())) return false;
      const d = tab === "issuance" ? (i.issued_date || "") : (i.training_date || "");
      if (from && d < from) return false;
      if (to && d > to) return false;
      if (q) {
        const blob = `${i.employee_name || ""} ${i.project_name || ""} ${i.project_number || ""} ${i.issued_by || i.instructor_name || ""}`.toLowerCase();
        if (!blob.includes(q.toLowerCase())) return false;
      }
      return true;
    });
  }, [items, q, employee, project, from, to, tab]);

  const totalsLine = useMemo(() => {
    if (tab === "issuance") {
      const issued = filtered.filter((r) => !r.return).length;
      const returned = filtered.filter((r) => r.return).length;
      // iter324 · aging signal — serialized/recoverable PPE out > 90 days.
      const aging = filtered.filter((r) => isAgingAccountability(r, 90)).length;
      return { primary: filtered.length, issued, returned, aging };
    }
    return { primary: filtered.length };
  }, [filtered, tab]);

  const TabButton = ({ value, icon: Icon, label, testId }) => (
    <button
      type="button"
      onClick={() => setTab(value)}
      data-testid={testId}
      className={
        "inline-flex items-center gap-2 px-4 h-10 rounded-md border-2 font-bold uppercase tracking-wide text-xs " +
        (tab === value
          ? "border-cyan-700 bg-cyan-700 text-white"
          : "border-slate-300 bg-white text-slate-700 hover:border-slate-400")
      }
    >
      <Icon className="w-4 h-4" />
      {label}
    </button>
  );

  return (
    <SafetyShell title={t("Equipment & PPE Accountability")} kicker={t("Safety Review")}>
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4" data-testid="safety-forms-records-page">
        <header className="bg-white border border-slate-200 border-l-4 border-l-cyan-700 rounded-md p-5">
          <div className="flex items-start gap-3">
            <Package className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
            <div className="min-w-0 flex-1">
              <span className="font-mono text-xs uppercase tracking-[0.22em] text-cyan-700 font-bold">
                {t("Safety Portal")}
              </span>
              <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight mt-0.5">
                {t("Equipment & PPE Accountability")}
              </h1>
              <p className="text-sm text-slate-600 mt-1">
                {t("Every Equipment Issuance and Use & Care Training record filed through Safety Forms. Filter by employee, project, or date — drill in for the full PDF and check-in/return status.")}
              </p>
            </div>
          </div>
        </header>

        {/* Tabs + Form-Entry CTAs · iter332 · Safety Portal can now
            START new forms directly from the review surface. The two
            entry routes already exist under /safety/forms/* — we just
            surface them prominently so the workflow loop closes
            (review → start → submit → return → see the new record). */}
        <div className="flex flex-wrap items-center gap-2" data-testid="safety-forms-records-tabs">
          <TabButton
            value="issuance"
            icon={HardHat}
            label={t("Equipment Issuance")}
            testId="tab-issuance"
          />
          <TabButton
            value="training"
            icon={GraduationCap}
            label={t("Use & Care Training")}
            testId="tab-training"
          />
          <div className="flex-1" />
          <Link
            to="/safety/forms/equipment-issuance/new?from=records"
            className="inline-flex items-center gap-2 h-10 px-4 rounded-md bg-cyan-700 text-white font-bold uppercase tracking-wide text-xs hover:bg-cyan-800 transition-colors"
            data-testid="new-issuance-btn"
          >
            <Plus className="w-4 h-4" />
            {t("NEW EQUIPMENT ISSUANCE")}
          </Link>
          <Link
            to="/safety/forms/equipment-training/new?from=records"
            className="inline-flex items-center gap-2 h-10 px-4 rounded-md bg-cyan-700 text-white font-bold uppercase tracking-wide text-xs hover:bg-cyan-800 transition-colors"
            data-testid="new-training-btn"
          >
            <Plus className="w-4 h-4" />
            {t("NEW USE & CARE TRAINING")}
          </Link>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <SummaryCard
            label={t("Records")}
            value={totalsLine.primary}
            icon={Package}
            accent="bg-slate-700"
            testId="forms-summary-total"
          />
          {tab === "issuance" && (
            <>
              <SummaryCard
                label={t("Currently Issued")}
                value={totalsLine.issued}
                icon={AlertTriangle}
                accent="bg-amber-600"
                testId="forms-summary-issued"
              />
              <SummaryCard
                label={t("Returned")}
                value={totalsLine.returned}
                icon={CheckCircle2}
                accent="bg-emerald-700"
                testId="forms-summary-returned"
              />
              {/* iter324 · accountability aging signal — subtle, quiet,
                  consumable-PPE-excluded. Renders even when 0 so the
                  contract is visible (the badge stays muted at 0). */}
              <SummaryCard
                label={t("Aging (>90d)")}
                value={totalsLine.aging || 0}
                icon={Clock}
                accent={(totalsLine.aging || 0) > 0 ? "bg-amber-500" : "bg-slate-400"}
                testId="forms-summary-aging"
                hint={t("Serialized PPE — consumables excluded")}
              />
            </>
          )}
        </div>

        {/* Filters */}
        <div className="bg-white border border-slate-200 rounded-md p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
          <div className="lg:col-span-2 relative">
            <Search className="absolute left-2 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <Input
              className="pl-7 h-9"
              placeholder={t("Search employee, project, instructor…")}
              value={q}
              onChange={(e) => setQ(e.target.value)}
              data-testid="forms-search"
            />
          </div>
          <Input
            className="h-9"
            placeholder={t("Employee filter")}
            value={employee}
            onChange={(e) => setEmployee(e.target.value)}
            data-testid="forms-employee-filter"
          />
          <Input
            type="date"
            className="h-9"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
            data-testid="forms-from"
          />
          <Input
            type="date"
            className="h-9"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            data-testid="forms-to"
          />
        </div>

        {/* Table */}
        <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
          {loading ? (
            <div className="text-center py-12 text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mx-auto" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-10 text-center text-slate-500" data-testid="forms-empty">
              <Filter className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="italic">{t("No records match these filters.")}</p>
            </div>
          ) : tab === "issuance" ? (
            <IssuanceTable rows={filtered} t={t} />
          ) : (
            <TrainingTable rows={filtered} t={t} />
          )}
        </div>

        <p className="text-xs text-slate-500 font-mono">
          {filtered.length} {t("of")} {items.length} {t("records shown")}
        </p>
      </div>
    </SafetyShell>
  );
}

function IssuanceTable({ rows, t }) {
  const lang = (typeof navigator !== "undefined" && navigator.language || "").startsWith("es") ? "es" : "en";
  return (
    <table className="w-full text-sm" data-testid="issuance-table">
      <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em] text-[10px]">
        <tr>
          <th className="text-left px-3 py-2">{t("Issued")}</th>
          <th className="text-left px-3 py-2">{t("Employee")}</th>
          <th className="text-left px-3 py-2">{t("Project / Job")}</th>
          <th className="text-left px-3 py-2">{t("Issued By")}</th>
          <th className="text-left px-3 py-2">{t("Items")}</th>
          <th className="text-left px-3 py-2">{t("Status")}</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, idx) => {
          const status = issuanceStatus(r);
          const itemCount = Array.isArray(r.items) ? r.items.length : 0;
          // iter324 · subtle per-row aging indicator. Only renders when
          // the row qualifies (serialized PPE, > 90d, no return). The
          // indicator is informational, not alarming.
          const isAging = isAgingAccountability(r, 90);
          const agingClasses = isAging ? accountabilityClassLabels(r, lang) : [];
          return (
            <tr key={r.id || idx} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`issuance-row-${idx}`}>
              <td className="px-3 py-2 font-mono text-xs text-slate-600 whitespace-nowrap">
                <div className="flex items-center gap-1.5">
                  <span>{r.issued_date || "—"}</span>
                  {isAging && (
                    <span
                      className="inline-flex items-center px-1.5 h-4 rounded-sm bg-amber-50 border border-amber-300 text-amber-900 text-[9px] font-mono tracking-wide uppercase"
                      title={`${t("Aging accountability item")}: ${agingClasses.join(", ")}`}
                      data-testid={`issuance-aging-${idx}`}
                    >
                      {t("90d+")}
                    </span>
                  )}
                </div>
              </td>
              <td className="px-3 py-2 font-bold truncate max-w-[12rem]">
                {r.employee_name || "—"}
              </td>
              <td className="px-3 py-2 text-slate-600 truncate max-w-[14rem]">
                {r.project_name || r.project_number || "—"}
              </td>
              <td className="px-3 py-2 text-slate-600 truncate max-w-[10rem]">
                {r.issued_by || "—"}
              </td>
              <td className="px-3 py-2 font-mono font-bold">{itemCount}</td>
              <td className="px-3 py-2">
                <span className={`px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${STATUS_PILL[status] || "bg-slate-100"}`}>
                  {t(status)}
                </span>
              </td>
              <td className="px-3 py-2 text-right">
                <Link
                  to={`/safety/forms/equipment-issuance/${r.id}`}
                  className="text-cyan-700 hover:underline font-bold inline-flex items-center"
                  data-testid={`issuance-open-${idx}`}
                >
                  {t("Open")} <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function TrainingTable({ rows, t }) {
  return (
    <table className="w-full text-sm" data-testid="training-table">
      <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em] text-[10px]">
        <tr>
          <th className="text-left px-3 py-2">{t("Date")}</th>
          <th className="text-left px-3 py-2">{t("Employee")}</th>
          <th className="text-left px-3 py-2">{t("Project / Job")}</th>
          <th className="text-left px-3 py-2">{t("Instructor")}</th>
          <th className="text-left px-3 py-2">{t("Training Type")}</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, idx) => (
          <tr key={r.id || idx} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`training-row-${idx}`}>
            <td className="px-3 py-2 font-mono text-xs text-slate-600 whitespace-nowrap">
              {r.training_date || "—"}
            </td>
            <td className="px-3 py-2 font-bold truncate max-w-[12rem]">
              {r.employee_name || "—"}
            </td>
            <td className="px-3 py-2 text-slate-600 truncate max-w-[14rem]">
              {r.project_name || r.project_number || "—"}
            </td>
            <td className="px-3 py-2 text-slate-600 truncate max-w-[10rem]">
              {r.instructor_name || "—"}
            </td>
            <td className="px-3 py-2 text-slate-600 truncate max-w-[10rem]">
              {r.training_type || r.training_kind || "—"}
            </td>
            <td className="px-3 py-2 text-right">
              <Link
                to={`/safety/forms/equipment-training/${r.id}`}
                className="text-cyan-700 hover:underline font-bold inline-flex items-center"
                data-testid={`training-open-${idx}`}
              >
                {t("Open")} <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SummaryCard({ label, value, icon: Icon, accent, testId, hint }) {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-3" data-testid={testId}>
      <div className="flex items-center gap-2">
        <div className={`inline-flex items-center justify-center w-8 h-8 rounded-md ${accent} text-white`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 font-bold">
          {label}
        </div>
      </div>
      <div className="font-display text-2xl font-black mt-1">{value}</div>
      {hint && (
        <div className="text-[10px] text-slate-500 italic mt-0.5">{hint}</div>
      )}
    </div>
  );
}
