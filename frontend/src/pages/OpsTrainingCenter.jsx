// OpsTrainingCenter — Iter134. System-wide operator training & guides.
// Distinct from /training (field-worker tracks). This is the "how to use
// each portal of the platform" reference for operators + admins.
//
// Public-read: no auth required to view guides. Admin-edit happens in
// a separate Admin page; this page is the consumer view.
import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import {
  GraduationCap, ArrowLeft, Home, BookOpen, Loader2, ShieldAlert,
  Briefcase, HardHat, Wrench, Truck, ShieldCheck, Cog, LifeBuoy,
  Search, ChevronRight, FileDown,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { EmptyState, LoadingState } from "@/components/ui/PortalStates";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PORTAL_META = {
  admin:       { Icon: ShieldAlert, accent: "border-red-700 bg-red-700",       text: "text-red-700" },
  safety:      { Icon: ShieldCheck, accent: "border-cyan-700 bg-cyan-700",     text: "text-cyan-700" },
  hr:          { Icon: Briefcase,   accent: "border-purple-700 bg-purple-700", text: "text-purple-700" },
  dispatch:    { Icon: Truck,       accent: "border-amber-600 bg-amber-600",   text: "text-amber-700" },
  shop:        { Icon: Wrench,      accent: "border-orange-700 bg-orange-700", text: "text-orange-700" },
  pm:          { Icon: HardHat,     accent: "border-emerald-700 bg-emerald-700", text: "text-emerald-700" },
  field:       { Icon: HardHat,     accent: "border-slate-700 bg-slate-700",   text: "text-slate-700" },
  integration: { Icon: Cog,         accent: "border-indigo-700 bg-indigo-700", text: "text-indigo-700" },
  reliability: { Icon: LifeBuoy,    accent: "border-rose-700 bg-rose-700",     text: "text-rose-700" },
};

function HeaderBar() {
  const nav = useNavigate();
  return (
    <header className="bg-slate-900 border-b-4 border-indigo-600">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-4 flex items-center gap-3 flex-wrap">
        <Link to="/" className="inline-flex items-center text-white hover:text-indigo-300 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="ops-training-nav-home">
          <Home className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Home</span>
        </Link>
        <button onClick={() => nav(-1)} className="inline-flex items-center text-white hover:text-indigo-300 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="ops-training-nav-back">
          <ArrowLeft className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Back</span>
        </button>
        <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
        <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
        <div className="flex-1" />
        <LangToggle />
      </div>
    </header>
  );
}

export default function OpsTrainingCenter() {
  const { t } = useT();
  const [searchParams, setSearchParams] = useSearchParams();
  const portalParam = searchParams.get("portal") || "";
  const [portals, setPortals] = useState([]);
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        const [pRes, gRes] = await Promise.all([
          axios.get(`${API}/training-center/portals`),
          axios.get(`${API}/training-center/guides`),
        ]);
        if (!alive) return;
        setPortals(pRes.data?.portals || []);
        setGuides(gRes.data?.guides || []);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const filtered = useMemo(() => {
    let list = guides;
    if (portalParam) list = list.filter((g) => g.portal === portalParam);
    if (search.trim()) {
      const s = search.trim().toLowerCase();
      list = list.filter((g) =>
        (g.title || "").toLowerCase().includes(s)
        || (g.summary || "").toLowerCase().includes(s)
        || (g.kicker || "").toLowerCase().includes(s),
      );
    }
    return list;
  }, [guides, portalParam, search]);

  const setPortal = (key) => {
    if (!key || key === portalParam) {
      searchParams.delete("portal");
    } else {
      searchParams.set("portal", key);
    }
    setSearchParams(searchParams, { replace: true });
  };

  return (
    <div className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <HeaderBar />

      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-6">
        <div className="flex items-start gap-3 mb-1">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-indigo-700 text-white shrink-0">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
              OPERATIONS · TRAINING CENTER
            </div>
            <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 tracking-tight leading-tight">
              {t("MASCI Training Center & Operator Guides")}
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl leading-relaxed">
              {t("Step-by-step guides for every portal, every integration, and platform reliability. Download any guide as PDF for offline reference, classroom training, or new-hire packets.")}
            </p>
          </div>
        </div>

        {/* Search bar */}
        <div className="mt-5 mb-5 relative max-w-xl">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <Input
            placeholder={t("Search guides by title or topic…")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-11 pl-9 text-sm border-2 border-slate-300 focus-visible:ring-2 focus-visible:ring-indigo-600"
            data-testid="ops-training-search"
          />
        </div>

        {/* Portal filters */}
        <div className="flex flex-wrap gap-2 mb-6">
          <button
            onClick={() => setPortal("")}
            className={`px-3 py-1.5 rounded-md text-xs font-mono uppercase tracking-[0.15em] font-bold border-2 ${
              !portalParam ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-200"
            }`}
            data-testid="ops-training-portal-all"
          >
            All <span className="opacity-70">({guides.length})</span>
          </button>
          {portals.filter((p) => p.count > 0).map((p) => {
            const meta = PORTAL_META[p.key] || PORTAL_META.admin;
            const Icon = meta.Icon;
            const active = portalParam === p.key;
            return (
              <button
                key={p.key}
                onClick={() => setPortal(p.key)}
                className={`px-3 py-1.5 rounded-md text-xs font-mono uppercase tracking-[0.15em] font-bold border-2 flex items-center gap-1.5 ${
                  active ? `${meta.accent} text-white` : "bg-white text-slate-700 border-slate-200"
                }`}
                data-testid={`ops-training-portal-${p.key}`}
              >
                <Icon className="w-3.5 h-3.5" /> {p.label} <span className="opacity-70">({p.count})</span>
              </button>
            );
          })}
        </div>

        {/* Guide grid */}
        {loading ? (
          <LoadingState label={t("Loading guides…")} testId="ops-training-loading" />
        ) : filtered.length === 0 ? (
          <EmptyState
            title={t("No guides match your filter")}
            body={t("Try clearing the search or selecting a different portal. The Training Center is admin-editable — new guides can be added at any time.")}
            testId="ops-training-empty"
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((g) => {
              const meta = PORTAL_META[g.portal] || PORTAL_META.admin;
              const Icon = meta.Icon;
              return (
                <Link
                  key={g.slug}
                  to={`/ops-training/${g.slug}`}
                  className="group bg-white border border-slate-200 border-l-4 border-l-indigo-600 hover:shadow-md hover:border-slate-300 rounded-md p-5 transition-all duration-150 hover:-translate-y-0.5 flex flex-col"
                  data-testid={`ops-training-guide-${g.slug}`}
                >
                  <div className="flex items-start gap-3 mb-2">
                    <div className={`inline-flex items-center justify-center w-10 h-10 rounded-md ${meta.accent} text-white shrink-0`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className={`font-mono text-[9px] uppercase tracking-[0.18em] ${meta.text}`}>
                        {g.kicker}
                      </div>
                      <h3 className="font-display text-base font-black tracking-tight text-slate-900 leading-tight mt-0.5">
                        {g.title}
                      </h3>
                    </div>
                  </div>
                  <p className="text-slate-600 text-xs leading-relaxed flex-1 line-clamp-4">
                    {g.summary}
                  </p>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                      v{g.version || "1.0"}
                    </span>
                    <span className="text-xs font-bold uppercase tracking-wide text-indigo-700 group-hover:translate-x-0.5 transition-transform flex items-center">
                      <BookOpen className="w-3.5 h-3.5 mr-1" /> Read <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
