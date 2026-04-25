import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ClipboardCheck,
  Users,
  AlertTriangle,
  AlertOctagon,
  ArrowRight,
  Plus,
  Loader2,
  ShieldCheck,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { CompanyInfoDialog } from "@/components/CompanyInfoDialog";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { formatDateLong } from "@/lib/utils";

const Tile = ({ to, icon: Icon, title, desc, count, sub, accent = "red" }) => {
  const accentCls =
    accent === "red"
      ? "border-red-700 bg-red-700"
      : accent === "amber"
      ? "border-amber-600 bg-amber-600"
      : accent === "redDeep"
      ? "border-red-900 bg-red-900"
      : "border-slate-800 bg-slate-800";
  return (
    <Link
      to={to}
      className="group relative bg-white border-2 border-slate-300 rounded-md p-6 sm:p-8 hover:border-red-700 hover:-translate-y-0.5 transition-all duration-150 flex flex-col"
      data-testid={`hub-tile-${to.replace("/", "")}`}
    >
      <div
        className={`inline-flex items-center justify-center w-14 h-14 rounded-md ${accentCls} text-white mb-4`}
      >
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="font-display text-2xl font-black tracking-tight text-slate-900">
        {title}
      </h3>
      <p className="text-slate-600 text-sm mt-2 flex-1 leading-relaxed">{desc}</p>

      <div className="mt-5 pt-4 border-t-2 border-slate-100 flex items-end justify-between">
        <div>
          <div className="font-display text-3xl font-black text-slate-900 leading-none">
            {count == null ? "—" : count}
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1">
            {sub}
          </div>
        </div>
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-red-700 font-bold flex items-center gap-1 group-hover:gap-2 transition-all">
          Open <ArrowRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </Link>
  );
};

const NewBtn = ({ to, label, testId }) => (
  <Link
    to={to}
    className="inline-flex items-center justify-center h-11 px-4 bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-xs rounded-md border-b-2 border-slate-700"
    onClick={(e) => e.stopPropagation()}
    data-testid={testId}
  >
    <Plus className="w-3.5 h-3.5 mr-1" /> {label}
  </Link>
);

export default function Hub() {
  const { t } = useT();
  const [counts, setCounts] = useState({ inspections: null, meetings: null, jhas: null, incidents: null });
  const [loading, setLoading] = useState(true);
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [insp, mtgs, jhas, incs] = await Promise.all([
          api.get("/inspections").catch(() => ({ data: [] })),
          api.get("/meetings").catch(() => ({ data: [] })),
          api.get("/jhas").catch(() => ({ data: [] })),
          api.get("/incidents").catch(() => ({ data: [] })),
        ]);
        if (!alive) return;
        setCounts({
          inspections: insp.data?.length || 0,
          meetings: mtgs.data?.length || 0,
          jhas: jhas.data?.length || 0,
          incidents: incs.data?.length || 0,
        });
        const merged = [
          ...(insp.data || []).map((d) => ({ ...d, _kind: "inspection" })),
          ...(mtgs.data || []).map((d) => ({ ...d, _kind: "meeting" })),
          ...(jhas.data || []).map((d) => ({ ...d, _kind: "jha" })),
          ...(incs.data || []).map((d) => ({ ...d, _kind: "incident" })),
        ]
          .sort((a, b) =>
            String(b.created_at || "").localeCompare(String(a.created_at || ""))
          )
          .slice(0, 6);
        setRecent(merged);
      } catch {
        /* noop */
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const inspSub = counts.inspections === 1 ? t("report on file") : t("reports on file");
  const mtgSub = counts.meetings === 1 ? t("meeting logged") : t("meetings logged");
  const jhaSub = counts.jhas === 1 ? t("analysis on file") : t("analyses on file");
  const incSub = counts.incidents === 1 ? t("report on file") : t("reports on file");

  return (
    <div className="min-h-screen blueprint-bg">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <MasciLogo variant="lockup" size="2xl" className="hidden sm:block" />
          <MasciLogo variant="mark" size="lg" className="sm:hidden" />
          <div className="flex items-center gap-2">
            <LangToggle />
            <CompanyInfoDialog />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="mb-10 sm:mb-14">
          <span className="font-mono text-xs uppercase tracking-[0.25em] text-red-700">
            {t("MASCI Safety Hub")}
          </span>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 mt-2">
            {t("One front door for every safety form.")}
          </h1>
          <p className="text-slate-600 text-base sm:text-lg mt-3 max-w-2xl">
            {t("Document compliance, run toolbox talks, and analyze hazards before every task. Print or save any record as a branded PDF — works from any device.")}
          </p>
          <div className="mt-4 flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.25em]">
            <span className="text-red-700 font-bold">{t("No Shortcuts")}</span>
            <span className="w-1 h-1 rounded-full bg-red-700" />
            <span className="text-red-700 font-bold">{t("No Exceptions")}</span>
          </div>
        </div>

        {loading ? (
          <div className="py-16 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> {t("Loading...")}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5 mb-12">
              <div className="relative">
                <Tile
                  to="/inspections"
                  icon={ClipboardCheck}
                  title={t("Site Inspections")}
                  desc={t("Daily and weekly job-site safety inspections. PPE, MOT, fall protection, electrical, and more — graded automatically.")}
                  count={counts.inspections}
                  sub={inspSub}
                  accent="red"
                />
                <div className="absolute top-6 right-6 sm:top-8 sm:right-8">
                  <NewBtn to="/inspect/new" label={t("New")} testId="hub-new-inspection" />
                </div>
              </div>

              <div className="relative">
                <Tile
                  to="/meetings"
                  icon={Users}
                  title={t("Safety Meetings")}
                  desc={t("Toolbox talks and daily huddles. 80+ heavy-civil topics with prefilled hazards — every crew member signs in.")}
                  count={counts.meetings}
                  sub={mtgSub}
                  accent="slate"
                />
                <div className="absolute top-6 right-6 sm:top-8 sm:right-8">
                  <NewBtn to="/meetings/new" label={t("New")} testId="hub-new-meeting" />
                </div>
              </div>

              <div className="relative">
                <Tile
                  to="/jha"
                  icon={AlertTriangle}
                  title={t("Job Hazard Analysis")}
                  desc={t("Pre-task JHA / JSA. Walk every step, list hazards, document controls, and get the crew sign-off before work starts.")}
                  count={counts.jhas}
                  sub={jhaSub}
                  accent="amber"
                />
                <div className="absolute top-6 right-6 sm:top-8 sm:right-8">
                  <NewBtn to="/jha/new" label={t("New")} testId="hub-new-jha" />
                </div>
              </div>

              <div className="relative">
                <Tile
                  to="/incidents"
                  icon={AlertOctagon}
                  title={t("Incident Reports")}
                  desc={t("Document near misses, injuries, and damage. Severity tiers, root cause, witnesses, and follow-up — all in one record.")}
                  count={counts.incidents}
                  sub={incSub}
                  accent="redDeep"
                />
                <div className="absolute top-6 right-6 sm:top-8 sm:right-8">
                  <NewBtn to="/incidents/new" label={t("New")} testId="hub-new-incident" />
                </div>
              </div>
            </div>

            {recent.length > 0 && (
              <div
                className="bg-white border-2 border-slate-300 rounded-md overflow-hidden"
                data-testid="hub-recent"
              >
                <div className="px-5 py-4 border-b-2 border-slate-200 flex items-center justify-between">
                  <h2 className="font-display text-xl font-bold flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-red-700" /> {t("Recent Activity")}
                  </h2>
                  <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
                    Last {recent.length}
                  </span>
                </div>
                <ul className="divide-y-2 divide-slate-100">
                  {recent.map((r) => {
                    const cfg =
                      r._kind === "inspection"
                        ? { label: "Inspection", to: `/inspect/${r.id}`, color: "bg-red-700" }
                        : r._kind === "meeting"
                        ? { label: "Meeting", to: `/meetings/${r.id}`, color: "bg-slate-800" }
                        : r._kind === "incident"
                        ? { label: "Incident", to: `/incidents/${r.id}`, color: "bg-red-900" }
                        : { label: "JHA", to: `/jha/${r.id}`, color: "bg-amber-600" };
                    const dateStr =
                      r.inspection_date || r.meeting_date || r.jha_date || r.incident_date || r.created_at;
                    const title =
                      r.project_name || r.topic || r.job_title || r.incident_type || "Untitled";
                    return (
                      <li key={`${r._kind}-${r.id}`}>
                        <Link
                          to={cfg.to}
                          className="block p-4 sm:p-5 hover:bg-red-50 transition-colors duration-150 flex items-center gap-3"
                          data-testid={`hub-recent-${r.id}`}
                        >
                          <span
                            className={`shrink-0 inline-flex items-center px-2 py-1 ${cfg.color} text-white text-[10px] font-mono font-bold uppercase tracking-wider rounded`}
                          >
                            {cfg.label}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="font-display font-bold text-slate-900 truncate">
                              {title}
                            </div>
                            <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500 mt-0.5">
                              {formatDateLong(dateStr)}
                              {r.location ? ` · ${r.location}` : ""}
                            </div>
                          </div>
                          <ArrowRight className="w-4 h-4 text-slate-400" />
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </>
        )}
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-8 text-center font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
        {t("MASCI · Job Site Safety Program")}
      </footer>
    </div>
  );
}
