// Trench Safety Repair Queue · Shop Portal · Phase 6
//
// Calm operational queue for trench safety repair work. Reads from the
// Phase 6 backend endpoint /api/trench-safety/shop/repairs which is
// already pre-sorted by severity then opened_at. Single-screen,
// no charts, no KPIs.
import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Loader2, Wrench, ArrowLeft, ChevronRight, ShieldAlert,
  AlertOctagon, Truck, PackageOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

const STATUS_BADGE = {
  "Open":                       "bg-amber-50 text-amber-900 border-amber-300",
  "In Progress":                "bg-blue-50 text-blue-900 border-blue-300",
  "Waiting on Parts":           "bg-orange-50 text-orange-900 border-orange-300",
  "Vendor Repair":              "bg-purple-50 text-purple-900 border-purple-300",
  "Completed":                  "bg-emerald-50 text-emerald-900 border-emerald-300",
  "Closed After Verification":  "bg-slate-100 text-slate-700 border-slate-300",
};

const SEVERITY_DOT = {
  "Critical": "bg-red-600",
  "Major":    "bg-orange-500",
  "Minor":    "bg-amber-400",
  "None":     "bg-slate-300",
};

const HOLD_BADGE = {
  "Safety Hold":        "bg-red-50 text-red-800 border-red-400",
  "Certification Hold": "bg-purple-50 text-purple-800 border-purple-400",
  "Maintenance Hold":   "bg-orange-50 text-orange-800 border-orange-400",
  "Inspection Hold":    "bg-amber-50 text-amber-800 border-amber-400",
};

function formatHoldLabel(value) {
  if (!value) return "—";
  return String(value).replace(/\bCertification Hold\b/gi, "Compliance Hold");
}

export default function ShopTrenchSafetyRepairs() {
  const { t } = useT();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const params = statusFilter ? { status: statusFilter } : {};
        const r = await api.get("/trench-safety/shop/repairs", { params });
        if (cancelled) return;
        setItems(r.data?.items || []);
        setCounts(r.data?.counts || {});
      } catch (e) {
        if (!cancelled) setErr(e?.response?.data?.detail || "Failed to load repair queue");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [statusFilter]);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-slate-900 text-white px-4 py-3 flex items-center gap-3" data-testid="shop-trench-repairs-header">
        <Button variant="ghost" size="sm" onClick={() => navigate("/shop")} className="text-white hover:bg-slate-800">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <Wrench className="w-5 h-5 text-cyan-300" />
        <h1 className="font-display font-black tracking-tight text-lg flex-1">
          {t("Trench Safety Repairs")}
        </h1>
        <span className="text-xs font-mono text-slate-300" data-testid="repair-queue-total">
          {items.length}
        </span>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-5">
        {/* Status filter chips */}
        <div className="flex gap-2 flex-wrap mb-4">
          <FilterChip label={t("All Active")} active={statusFilter === ""} onClick={() => setStatusFilter("")} testId="filter-all" />
          {["Open", "In Progress", "Waiting on Parts", "Vendor Repair", "Completed"].map((s) => (
            <FilterChip
              key={s}
              label={`${t(s)} ${counts[s] ? `(${counts[s]})` : ""}`}
              active={statusFilter === s}
              onClick={() => setStatusFilter(s === statusFilter ? "" : s)}
              testId={`filter-${s.replace(/\s+/g, "-").toLowerCase()}`}
            />
          ))}
        </div>

        {loading ? (
          <div className="flex items-center gap-2 text-slate-500 py-8 justify-center" data-testid="repair-queue-loading">
            <Loader2 className="w-4 h-4 animate-spin" /> {t("Loading…")}
          </div>
        ) : err ? (
          <div className="p-3 border border-red-300 bg-red-50 rounded text-red-900 text-sm" data-testid="repair-queue-error">{err}</div>
        ) : items.length === 0 ? (
          <div className="py-10 text-center text-sm text-slate-500 italic" data-testid="repair-queue-empty">
            {t("No active repairs in the queue.")}
          </div>
        ) : (
          <div className="space-y-2" data-testid="repair-queue-list">
            {items.map((r) => (
              <RepairRow key={r.id} repair={r} />
            ))}
          </div>
        )}

        <div className="mt-6 p-3 border border-amber-300 bg-amber-50 rounded text-sm text-amber-900" data-testid="repair-queue-coaching">
          <ShieldAlert className="w-4 h-4 inline mr-1.5 -mt-0.5" />
          <strong>{t("Coaching:")}</strong>{" "}
          {t("Completing a repair does not release a hold. Safety must verify before the asset returns to service.")}
        </div>
      </main>
    </div>
  );
}

function FilterChip({ label, active, onClick, testId }) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testId}
      className={
        "px-3 py-1.5 rounded-full border text-xs font-mono uppercase tracking-wider transition-colors " +
        (active
          ? "bg-cyan-700 border-cyan-700 text-white"
          : "bg-white border-slate-300 text-slate-700 hover:border-cyan-500 hover:text-cyan-800")
      }
    >
      {label}
    </button>
  );
}

function RepairRow({ repair: r }) {
  const { t } = useT();
  return (
    <Link
      to={`/safety/trench-safety/assets/${r.asset_id}`}
      className="block bg-white border border-slate-200 rounded-md hover:border-cyan-400 hover:shadow-sm transition-all"
      data-testid={`repair-row-${r.id}`}
    >
      <div className="p-3 flex items-start gap-3">
        <div className="flex flex-col items-center pt-1 shrink-0">
          <div
            className={"w-3 h-3 rounded-full " + (SEVERITY_DOT[r.severity_at_creation] || SEVERITY_DOT.None)}
            title={`${r.severity_at_creation || "None"} severity`}
            data-testid={`severity-dot-${r.severity_at_creation || "None"}`}
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center flex-wrap gap-2 mb-1">
            <span className="font-mono font-bold text-slate-900 text-sm" data-testid="repair-asset-id">{r.asset_id}</span>
            <span className="text-xs text-slate-500">·</span>
            <span className="text-xs text-slate-600">{r.asset_type} · {r.size}</span>
            <span
              className={"inline-block px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold " + (STATUS_BADGE[r.status] || "bg-slate-50 text-slate-700 border-slate-300")}
            >
              {t(r.status)}
            </span>
            {r.operational_status && HOLD_BADGE[r.operational_status] && (
              <span className={"inline-block px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold " + HOLD_BADGE[r.operational_status]}>
                {t(formatHoldLabel(r.operational_status))}
              </span>
            )}
            {r.requires_reinspection && (
              <span className="inline-block px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider font-bold bg-amber-50 text-amber-900 border-amber-400">
                {t("Reinspection Required")}
              </span>
            )}
          </div>
          <div className="text-sm text-slate-800 truncate">{r.issue_description || "—"}</div>
          <div className="text-[11px] text-slate-500 font-mono mt-1 flex flex-wrap gap-3">
            <span>{t("Severity")}: <span className="font-bold">{r.severity_at_creation || "None"}</span></span>
            {r.source && <span title={r.source}>src: {r.source.split(":")[0]}</span>}
            {r.opened_at && <span>{r.opened_at.slice(0, 10)}</span>}
            {r.opened_by && <span>by {r.opened_by}</span>}
            {r.repair_vendor && <span title="Vendor">{r.repair_vendor}</span>}
            {(r.current_project_name || r.current_location) && (
              <span>@ {r.current_project_name || r.current_location}</span>
            )}
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-slate-400 mt-2 shrink-0" />
      </div>
    </Link>
  );
}
