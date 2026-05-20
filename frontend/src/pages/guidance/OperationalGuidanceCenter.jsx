// OperationalGuidanceCenter — the top-level shell for MASCI's
// Training / Help / Operational Guidance system.
//
// Phase A + B + C scope:
//   • RBAC-aware section + article rendering, driven entirely by the
//     server (/api/guidance/*). Frontend trusts the server's visibility
//     decisions; never displays a title the server didn't return.
//   • Single-page Operational Guidance Center with: portal-first track
//     grid (Safety + Dispatch surfaced as first-class) · cross-cutting
//     section grid · search · article reader.
//   • Plain content blocks (p / steps / bullets / why / next / warn /
//     tip / mistakes). One renderer for everything.
//   • iter195: the legacy /ops-training surface is retired. /ops-training
//     now redirects here. No unrestricted side door into operator training.
//
// Style: matches MASCI's existing card/typography conventions.
// Mobile-first; section grids collapse to a single column under md.

import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  BookOpen, Search, Loader2, ChevronLeft, UserCog, Zap, LayoutGrid,
  LifeBuoy, Lightbulb, Shield, UserPlus, AlertTriangle, Lightbulb as TipIcon,
  AlertCircle, ArrowRightCircle, Home, LogIn,
} from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";

const SECTION_ICONS = {
  "user-cog": UserCog,
  "zap": Zap,
  "layout-grid": LayoutGrid,
  "life-buoy": LifeBuoy,
  "lightbulb": Lightbulb,
  "shield": Shield,
  "user-plus": UserPlus,
};

// ─────────────────────────────────────────────────────────────────────
// Block renderer — turns body[].type into JSX
// ─────────────────────────────────────────────────────────────────────
//
// iter199 — Pass 3 translation: callout headers ("Why this matters",
// "What happens next", "Common mistakes") are now translation-aware
// via useT(). Article body strings (block.text / block.items) come
// already-localized from the server because the article reader picks
// body_es vs body before rendering.
function Block({ block }) {
  const { t } = useT();
  if (!block || typeof block !== "object") return null;
  switch (block.type) {
    case "p":
      return <p className="text-[15px] leading-relaxed text-slate-800">{block.text}</p>;
    case "steps":
      return (
        <ol className="list-decimal list-inside space-y-1 text-[15px] text-slate-800">
          {(block.items || []).map((it, i) => <li key={i}>{it}</li>)}
        </ol>
      );
    case "bullets":
      return (
        <ul className="list-disc list-inside space-y-1 text-[15px] text-slate-800">
          {(block.items || []).map((it, i) => <li key={i}>{it}</li>)}
        </ul>
      );
    case "why":
      return (
        <div className="border-l-4 border-amber-500 bg-amber-50 p-3 rounded-r flex gap-3 items-start">
          <Lightbulb className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="flex-1 text-sm text-slate-800 leading-relaxed">
            <strong className="block text-[11px] uppercase tracking-wider text-amber-700 mb-1">
              {t("Why this matters")}
            </strong>
            {block.text}
          </div>
        </div>
      );
    case "next":
      return (
        <div className="border border-emerald-200 bg-emerald-50 rounded p-3">
          <strong className="text-[11px] uppercase tracking-wider text-emerald-700 block mb-1">
            {t("What happens next")}
          </strong>
          <ul className="space-y-1 text-sm text-slate-800">
            {(block.items || []).map((it, i) => (
              <li key={i} className="flex gap-2">
                <ArrowRightCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span>{it}</span>
              </li>
            ))}
          </ul>
        </div>
      );
    case "warn":
      return (
        <div className="border-l-4 border-red-500 bg-red-50 p-3 rounded-r flex gap-3 items-start">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="text-sm text-slate-800 leading-relaxed">{block.text}</div>
        </div>
      );
    case "tip":
      return (
        <div className="border-l-4 border-sky-500 bg-sky-50 p-3 rounded-r flex gap-3 items-start">
          <TipIcon className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
          <div className="text-sm text-slate-800 leading-relaxed">{block.text}</div>
        </div>
      );
    case "mistakes":
      return (
        <div className="border border-orange-200 bg-orange-50 rounded p-3">
          <strong className="text-[11px] uppercase tracking-wider text-orange-700 block mb-1">
            {t("Common mistakes")}
          </strong>
          <ul className="space-y-1 text-sm text-slate-800">
            {(block.items || []).map((it, i) => (
              <li key={i} className="flex gap-2">
                <AlertCircle className="w-4 h-4 text-orange-600 shrink-0 mt-0.5" />
                <span>{it}</span>
              </li>
            ))}
          </ul>
        </div>
      );
    default:
      return null;
  }
}

// ─────────────────────────────────────────────────────────────────────
// Portal Training Directory (iter204)
// ─────────────────────────────────────────────────────────────────────
// Training-first portal cards inside the Operational Guidance Center.
//
// Operator-driven design correction (iter204 over iter203):
//   Guidance is a TRAINING / ONBOARDING ecosystem — NOT a duplicate
//   production navigation layer. Each card primarily opens portal
//   training, onboarding, and troubleshooting. The portal login link
//   is preserved but de-emphasized as a small secondary action.
//
// Per-card behavior:
//   PRIMARY action  → opens the portal's training/identity article
//                     (e.g., /guidance/portal-hr).
//   SECONDARY link  → small "Go to {Portal} sign-in →" text link.
//                     Operationally optional, intentionally subdued.
//
// Mental model:
//   "Operational Guidance teaches me how the portal works."
//   NOT: "Operational Guidance is another way into the production system."
const PORTAL_DIRECTORY = [
  {
    key: "leadership", label: "Field Leadership Training", labelEs: "Capacitación · Liderazgo de Campo",
    loginUrl: "/leadership/login", trainingArticle: "portal-leadership-identity",
    purpose: "Onboarding & operational identity for Superintendents, Foremen, and Field Leaders.",
    purposeEs: "Orientación e identidad operacional para Superintendentes, Capataces y Líderes de Campo.",
    accent: "bg-red-700", iconBg: "bg-red-50", iconColor: "text-red-700", border: "hover:border-red-700",
  },
  {
    key: "hr", label: "HR Portal Training", labelEs: "Capacitación · Portal de RH",
    loginUrl: "/hr/login", trainingArticle: "portal-hr-identity",
    purpose: "Onboarding, time verification, accountability, and HR workflow guidance.",
    purposeEs: "Orientación, verificación de tiempo, rendición de cuentas y flujos de RH.",
    accent: "bg-purple-700", iconBg: "bg-purple-50", iconColor: "text-purple-700", border: "hover:border-purple-700",
  },
  {
    key: "safety", label: "Safety Portal Training", labelEs: "Capacitación · Portal de Seguridad",
    loginUrl: "/safety-portal/login", trainingArticle: "portal-safety-identity",
    purpose: "Incident response, corrective actions, audits, and training compliance.",
    purposeEs: "Respuesta a incidentes, acciones correctivas, auditorías y cumplimiento.",
    accent: "bg-yellow-600", iconBg: "bg-yellow-50", iconColor: "text-yellow-700", border: "hover:border-yellow-600",
  },
  {
    key: "shop", label: "Shop / Fleet Training", labelEs: "Capacitación · Taller / Flota",
    loginUrl: "/shop/login", trainingArticle: "portal-shop-identity",
    purpose: "Pre-Op review, damage workflow, maintenance coordination, parts ordering.",
    purposeEs: "Revisión Pre-Op, daños, coordinación de mantenimiento y repuestos.",
    accent: "bg-orange-600", iconBg: "bg-orange-50", iconColor: "text-orange-700", border: "hover:border-orange-600",
  },
  {
    key: "dispatch", label: "Dispatch Portal Training", labelEs: "Capacitación · Portal de Despacho",
    loginUrl: "/dispatch-portal/login", trainingArticle: "portal-dispatch-identity",
    purpose: "Equipment movement, availability, holds, transfers, and dispatch workflows.",
    purposeEs: "Movimiento de equipo, disponibilidad, retenciones, transferencias y flujos.",
    accent: "bg-sky-700", iconBg: "bg-sky-50", iconColor: "text-sky-700", border: "hover:border-sky-700",
  },
  {
    key: "pm", label: "PM Portal Training", labelEs: "Capacitación · Portal de PM",
    loginUrl: "/pm/login", trainingArticle: "portal-pm-identity",
    purpose: "Project review cadence, labor documentation, cross-portal coordination.",
    purposeEs: "Revisión de proyecto, documentación laboral, coordinación entre portales.",
    accent: "bg-amber-600", iconBg: "bg-amber-50", iconColor: "text-amber-700", border: "hover:border-amber-600",
  },
  {
    key: "admin", label: "Admin Console Guidance", labelEs: "Guía · Consola de Admin",
    loginUrl: "/admin/login", trainingArticle: "portal-admin-identity",
    purpose: "Operator-level training — people, jobs, system, backups, governance.",
    purposeEs: "Capacitación de operador — personas, trabajos, sistema, respaldos, gobernanza.",
    accent: "bg-slate-900", iconBg: "bg-slate-100", iconColor: "text-slate-900", border: "hover:border-slate-900",
  },
];

function PortalSignInDirectory({ lang }) {
  const { t } = useT();
  return (
    <section className="mt-8" data-testid="guidance-portal-directory">
      <div className="mb-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-700 font-bold">
          {t("Training & Onboarding · By Portal")}
        </div>
        <h2 className="font-display text-xl font-black tracking-tight">
          {t("Portal Training")}
        </h2>
        <p className="text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
          {t("Open each portal's training to learn what it does, who uses it, and how to operate it. Sign-in links are available if you already know your portal.")}
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {PORTAL_DIRECTORY.map((p) => {
          const portalLabel = (lang === "es" && p.labelEs) ? p.labelEs : p.label;
          const portalPurpose = (lang === "es" && p.purposeEs) ? p.purposeEs : p.purpose;
          const trainingHref = `/guidance/${p.trainingArticle}`;
          return (
            <div
              key={p.key}
              className={`group relative bg-white border-2 border-slate-300 rounded-md p-4 ${p.border} hover:shadow-md transition-all`}
              data-testid={`guidance-portal-directory-${p.key}`}
            >
              <div className={`absolute inset-y-0 left-0 w-1.5 ${p.accent} rounded-l-sm`} />
              <div className={`inline-flex items-center justify-center w-10 h-10 rounded ${p.iconBg} ${p.iconColor} shrink-0 mb-2`}>
                <BookOpen className="w-5 h-5" />
              </div>
              <div className="font-display text-base font-bold text-slate-900 leading-tight">
                {portalLabel}
              </div>
              <div className="text-[12px] text-slate-600 mt-1 leading-snug min-h-[2.5rem]">
                {portalPurpose}
              </div>
              {/* PRIMARY — open training */}
              <div className="mt-3">
                <Link
                  to={trainingHref}
                  className={`inline-flex items-center h-9 px-3 rounded-md text-white text-[11px] font-bold uppercase tracking-wider transition-colors ${p.accent} hover:opacity-90`}
                  data-testid={`guidance-portal-directory-${p.key}-training`}
                >
                  <BookOpen className="w-3.5 h-3.5 mr-1.5" />
                  {t("Open Training")}
                </Link>
              </div>
              {/* SECONDARY — small de-emphasized sign-in link.
                  Intentionally subdued so the card never feels like
                  a primary production navigation entry. */}
              <div className="mt-2">
                <Link
                  to={p.loginUrl}
                  className="inline-flex items-center text-[11px] text-slate-500 hover:text-slate-800 hover:underline"
                  data-testid={`guidance-portal-directory-${p.key}-signin`}
                >
                  {t("Go to portal sign-in")} →
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Search
// ─────────────────────────────────────────────────────────────────────
function SearchBox({ onResults, query, setQuery }) {
  const { t } = useT();  // iter202 — translation fix: placeholder was hardcoded
  const [loading, setLoading] = useState(false);
  const run = async (q) => {
    setQuery(q);
    if (!q || q.trim().length < 2) { onResults(null); return; }
    setLoading(true);
    try {
      const r = await api.get(`/guidance/search?q=${encodeURIComponent(q)}`);
      onResults(r?.data?.results || []);
    } catch {
      onResults([]);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
      <Input
        type="search"
        placeholder={t("Search guidance — by role, task, or keyword")}
        className="pl-9 pr-9 h-11"
        value={query}
        onChange={(e) => run(e.target.value)}
        data-testid="guidance-search-input"
      />
      {loading && (
        <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 animate-spin" />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Main shell
// ─────────────────────────────────────────────────────────────────────
export default function OperationalGuidanceCenter() {
  const { articleId, sectionId } = useParams();
  const navigate = useNavigate();
  const { lang, t } = useT();  // iter202 — translation fix: also need t() not just lang
  const [sections, setSections] = useState([]);
  const [articles, setArticles] = useState([]);
  const [article, setArticle] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  // Iter195 — portal-first landing grid. Loaded for home view only.
  // Surfaces Safety + Dispatch + all other portals visually as first-class
  // tracks (operator directive: do not bury Safety / Dispatch behind a
  // generic "Portals" section).
  const [portalArticles, setPortalArticles] = useState([]);
  // iter196 — curated public-tracks tile data. Loaded for home view
  // only. These are the public field-crew training articles, surfaced
  // as first-class tiles so anon / no-login users have a useful entry
  // point (not just a bare "browse by topic" grid).
  const [publicTrackArticles, setPublicTrackArticles] = useState({});

  // Load section catalog on mount
  useEffect(() => {
    (async () => {
      try {
        const r = await api.get("/guidance/sections");
        setSections(r?.data?.sections || []);
      } catch { /* render nothing */ }
    })();
  }, []);

  // Home-page portal grid — load the portals section once
  useEffect(() => {
    if (articleId || sectionId) return;
    (async () => {
      try {
        const r = await api.get("/guidance/articles?section=portals");
        setPortalArticles(r?.data?.articles || []);
      } catch { /* render nothing */ }
    })();
  }, [articleId, sectionId]);

  // Home-page public-track tiles — load each curated public article
  // by id. Server filters by scope, so missing ones simply won't render.
  useEffect(() => {
    if (articleId || sectionId) return;
    const ids = [
      "public-tools-map",
      "role-new-employee", "onboard-login", "onboard-mobile",
      "public-mobile-qr", "public-photos", "public-daily-report-basics",
      "public-preop-basics", "public-toolbox-talks", "public-qaqc-basics",
      "public-material-calculator",
      "public-incident-basics", "public-cant-login", "public-who-to-ask",
      "public-why-documentation",
    ];
    (async () => {
      const results = {};
      await Promise.all(ids.map(async (id) => {
        try {
          const r = await api.get(`/guidance/articles/${id}`);
          if (r?.data?.id) {
            results[id] = { id: r.data.id, title: r.data.title, summary: r.data.summary };
          }
        } catch { /* not visible to this caller — skip */ }
      }));
      setPublicTrackArticles(results);
    })();
  }, [articleId, sectionId]);

  // Load article OR section listing when URL changes
  useEffect(() => {
    let active = true;
    setLoading(true);
    (async () => {
      try {
        if (articleId) {
          const r = await api.get(`/guidance/articles/${articleId}`);
          if (active) { setArticle(r.data); setArticles([]); }
        } else if (sectionId) {
          const r = await api.get(`/guidance/articles?section=${encodeURIComponent(sectionId)}`);
          if (active) { setArticles(r?.data?.articles || []); setArticle(null); }
        } else {
          if (active) { setArticle(null); setArticles([]); }
        }
      } catch {
        if (active) { setArticle(null); setArticles([]); }
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [articleId, sectionId]);

  // ── Render: searching ─────────────────────────────────────────────
  if (searchResults !== null) {
    return (
      <Shell title={t("Search results")}>
        <button
          onClick={() => { setSearchResults(null); setQuery(""); }}
          className="inline-flex items-center gap-1 text-[12px] font-bold uppercase tracking-wider text-amber-700 hover:underline mb-3"
          data-testid="guidance-search-back"
        >
          <ChevronLeft className="w-4 h-4" /> {t("All guidance")}
        </button>
        <SearchBox onResults={setSearchResults} query={query} setQuery={setQuery} />
        {searchResults.length === 0 ? (
          <div className="text-center text-slate-500 py-10" data-testid="guidance-search-empty">
            {t("No matching guidance available for your access level.")}
          </div>
        ) : (
          <ul className="mt-4 space-y-2">
            {searchResults.map((r) => (
              <li key={r.id}>
                <Link
                  to={`/guidance/${r.id}`}
                  onClick={() => { setSearchResults(null); setQuery(""); }}
                  className="block p-3 border border-slate-200 rounded hover:bg-slate-50 transition-colors"
                  data-testid={`guidance-search-result-${r.id}`}
                >
                  <div className="font-medium text-slate-900">{r.title}</div>
                  {r.summary && (
                    <div className="text-[13px] text-slate-600 mt-0.5">{r.summary}</div>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Shell>
    );
  }

  // ── Render: single article ────────────────────────────────────────
  if (articleId) {
    if (loading) return <Shell><Loader2 className="w-6 h-6 animate-spin mx-auto my-12 text-slate-400" /></Shell>;
    if (!article) {
      return (
        <Shell title={t("Not available")}>
          <div className="text-center text-slate-500 py-10" data-testid="guidance-article-not-found">
            {t("This guidance isn't available for your access level.")}
            <div className="mt-4">
              <Link to="/guidance" className="text-amber-700 hover:underline">{t("Back to Guidance")}</Link>
            </div>
          </div>
        </Shell>
      );
    }
    // iter199 — Pass 3 translation: pick *_es fields when caller is
    // viewing Spanish AND the article has a translation. Graceful
    // fallback to English on either field-by-field — a partially
    // translated article still renders cleanly (translated title,
    // English body for missing blocks).
    const displayTitle   = (lang === "es" && article.title_es)   ? article.title_es   : article.title;
    const displaySummary = (lang === "es" && article.summary_es) ? article.summary_es : article.summary;
    const displayBody    = (lang === "es" && Array.isArray(article.body_es) && article.body_es.length)
      ? article.body_es
      : (article.body || []);
    return (
      <Shell>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900 mb-3"
          data-testid="guidance-back-btn"
        >
          <ChevronLeft className="w-4 h-4" /> {t("Back")}
        </button>
        <h1 className="font-display text-3xl font-black tracking-tight text-slate-900" data-testid="guidance-article-title">
          {displayTitle}
        </h1>
        {displaySummary && (
          <p className="text-slate-600 mt-1 text-[15px]">{displaySummary}</p>
        )}
        <div className="mt-6 space-y-4" data-testid="guidance-article-body">
          {displayBody.map((b, i) => <Block key={i} block={b} />)}
        </div>
        {(article.related || []).length > 0 && (
          <div className="mt-8 border-t border-slate-200 pt-4">
            <strong className="block text-[11px] uppercase tracking-wider text-slate-600 mb-2">
              {t("Related guidance")}
            </strong>
            <ul className="space-y-1">
              {article.related.map((r) => {
                // iter200 polish — pick title_es when available + ES is selected
                const relTitle = (lang === "es" && r.title_es) ? r.title_es : r.title;
                return (
                  <li key={r.id}>
                    <Link
                      to={`/guidance/${r.id}`}
                      className="text-amber-700 hover:text-amber-900 hover:underline inline-flex items-center gap-1 text-sm"
                      data-testid={`guidance-related-${r.id}`}
                    >
                      <ArrowRightCircle className="w-3.5 h-3.5" />
                      {relTitle}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </Shell>
    );
  }

  // ── Render: section listing ───────────────────────────────────────
  if (sectionId) {
    const sec = sections.find((s) => s.id === sectionId);
    return (
      <Shell title={sec?.title ? t(sec.title) : t("Section")}>
        <button
          type="button"
          onClick={() => navigate("/guidance")}
          className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900 mb-3"
          data-testid="guidance-back-to-home"
        >
          <ChevronLeft className="w-4 h-4" /> {t("All guidance")}
        </button>
        <SearchBox onResults={setSearchResults} query={query} setQuery={setQuery} />
        {loading ? (
          <Loader2 className="w-6 h-6 animate-spin mx-auto my-12 text-slate-400" />
        ) : articles.length === 0 ? (
          <div className="text-center text-slate-500 py-10">{t("No articles in this section for your access level.")}</div>
        ) : (
          <ul className="mt-4 space-y-2" data-testid="guidance-section-list">
            {articles.map((a) => (
              <li key={a.id}>
                <Link
                  to={`/guidance/${a.id}`}
                  className="block p-3 border border-slate-200 rounded hover:bg-slate-50 transition-colors"
                  data-testid={`guidance-section-row-${a.id}`}
                >
                  <div className="font-medium text-slate-900">{a.title}</div>
                  {a.summary && <div className="text-[13px] text-slate-600 mt-0.5">{a.summary}</div>}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Shell>
    );
  }

  // ── Render: Operational Guidance Center · home ────────────────────
  // Two first-class tile groups: PUBLIC field-crew training (always
  // shown when its articles exist) + PORTAL training (gated by scope).
  // Then topic grid below. Operator directive: this page must teach
  // field crews + new hires too, not just authenticated portal users.
  const PORTAL_TRACKS = [
    { key: "hr",         label: "HR Portal",                  accent: "blue",   matchPrefix: ["portal-hr", "hr-"] },
    { key: "safety",     label: "Safety Portal",              accent: "red",    matchPrefix: ["portal-safety", "safety-"] },
    { key: "shop",       label: "Shop / Fleet Portal",        accent: "orange", matchPrefix: ["portal-shop", "shop-"] },
    { key: "dispatch",   label: "Dispatch Portal",            accent: "purple", matchPrefix: ["portal-dispatch", "dispatch-"] },
    { key: "pm",         label: "PM Portal",                  accent: "teal",   matchPrefix: ["portal-pm", "pm-"] },
    { key: "leadership", label: "Field Leadership Portal",    accent: "amber",  matchPrefix: ["portal-leadership", "field-"] },
    { key: "admin",      label: "Admin Console",              accent: "slate",  matchPrefix: ["portal-admin", "admin-"] },
  ];
  const ACCENT_BAND = {
    blue:   "bg-blue-600",
    red:    "bg-red-700",
    orange: "bg-orange-600",
    purple: "bg-purple-700",
    teal:   "bg-teal-600",
    amber:  "bg-amber-600",
    slate:  "bg-slate-700",
  };
  const portalCounts = {};
  for (const t of PORTAL_TRACKS) {
    portalCounts[t.key] = portalArticles.filter((a) =>
      t.matchPrefix.some((p) => a.id === p || a.id.startsWith(p))
    ).length;
  }
  const visibleTracks = PORTAL_TRACKS.filter((t) => portalCounts[t.key] > 0);

  // iter196-197 — curated Public Field Training tiles. Mapped to real
  // public/no-login surfaces in the platform (audited from App.js):
  //   /daily/submit, /incidents/submit, /equipment/submit,
  //   /meetings/submit, /qaqc, /field/calculators, etc.
  // Each tile maps to a single article; the article explains the
  // workflow + what happens after submission + who to ask for help.
  //
  // iter202 — added labelEs / blurbEs for Spanish toggle parity. Tile
  // labels are blurb-style summaries, slightly different from article
  // titles (which already have title_es). Render-time picks the lang.
  const PUBLIC_TRACKS = [
    { id: "public-tools-map",         icon: LayoutGrid, label: "All Public Field Tools",   labelEs: "Todas las Herramientas de Campo",   blurb: "Index of every no-login tool on the platform.",   blurbEs: "Índice de cada herramienta sin inicio de sesión." },
    { id: "role-new-employee",        icon: UserPlus,   label: "New Employee Basics",       labelEs: "Empleado Nuevo · Básico",            blurb: "First-week orientation for any role.",            blurbEs: "Orientación de primera semana para cualquier rol." },
    { id: "public-mobile-qr",         icon: Zap,        label: "Scan-and-Go (QR Codes)",    labelEs: "Escanear-y-Listo (QR)",              blurb: "Open MASCI on your phone in seconds.",            blurbEs: "Abra MASCI en su teléfono en segundos." },
    { id: "onboard-mobile",           icon: BookOpen,   label: "Using MASCI on a Phone",    labelEs: "Usando MASCI en el Teléfono",        blurb: "Mobile-first tips that save your work.",          blurbEs: "Consejos móviles que guardan su trabajo." },
    { id: "public-photos",            icon: Lightbulb,  label: "Photos That Actually Help", labelEs: "Fotos Que Sí Sirven",                blurb: "Wide shot · close-up · clear.",                   blurbEs: "Toma amplia · acercamiento · claras." },
    { id: "public-daily-report-basics", icon: LayoutGrid, label: "Daily Report Basics",    labelEs: "Reporte Diario · Básico",            blurb: "What it is, why yours matters.",                  blurbEs: "Qué es y por qué el suyo importa." },
    { id: "public-preop-basics",      icon: Shield,     label: "Equipment Pre-Op Basics",   labelEs: "Pre-Operación · Básico",             blurb: "Walk it. Sign it. Flag what's broken.",           blurbEs: "Recórralo. Fírmelo. Marque lo roto." },
    { id: "public-toolbox-talks",     icon: UserCog,    label: "Toolbox Talks / Safety Meetings", labelEs: "Charlas de Seguridad",         blurb: "Sign in. Listen. The record is your signature.",  blurbEs: "Firme. Escuche. El registro es su firma." },
    { id: "public-qaqc-basics",       icon: LifeBuoy,   label: "QA / QC for Field Crews",   labelEs: "QA / QC para Cuadrillas",            blurb: "Photo before you cover it. Sign-offs that matter.", blurbEs: "Foto antes de cubrir. Firmas que importan." },
    { id: "public-material-calculator", icon: Lightbulb, label: "Material Calculator",     labelEs: "Calculadora de Materiales",         blurb: "Concrete · gravel · asphalt quick math.",         blurbEs: "Concreto · grava · asfalto · matemática rápida." },
    { id: "public-incident-basics",   icon: AlertTriangle, label: "If Something Happens",  labelEs: "Si Pasa Algo",                       blurb: "First steps after injury, near-miss, or damage.", blurbEs: "Primeros pasos después de lesión o daño." },
    { id: "public-cant-login",        icon: LifeBuoy,   label: "I Can't Log In",            labelEs: "No Puedo Iniciar Sesión",            blurb: "Common login problems & fixes.",                  blurbEs: "Problemas comunes y soluciones." },
    { id: "public-who-to-ask",        icon: UserCog,    label: "Who Do I Ask for Help?",    labelEs: "¿A Quién Pregunto?",                 blurb: "A quick map of who handles what.",                blurbEs: "Mapa rápido de quién maneja qué." },
    { id: "public-why-documentation", icon: Shield,     label: "Why This Paperwork Matters", labelEs: "Por Qué Importa Este Papeleo",     blurb: "Field crew's version of 'why'.",                  blurbEs: "La versión de la cuadrilla del 'por qué'." },
    { id: "onboard-login",            icon: LogIn,      label: "How to Log In",             labelEs: "Cómo Iniciar Sesión",                blurb: "First-time login basics.",                        blurbEs: "Lo básico de la primera vez." },
  ];
  const visiblePublicTracks = PUBLIC_TRACKS.filter((t) => publicTrackArticles[t.id]);
  const isAuthenticated = visibleTracks.length > 0;

  return (
    <Shell>
      {/* Hero — strong MASCI visual identity */}
      <section className="relative overflow-hidden rounded-md border-2 border-slate-900 bg-slate-900 text-white mb-6" data-testid="guidance-hero">
        <div className="absolute inset-y-0 left-0 w-1.5 bg-red-700" />
        <div className="px-5 sm:px-8 py-6 sm:py-8 grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="md:col-span-2">
            <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-400 font-bold mb-2">
              {t("MASCI Operations Platform · Operational Guidance Center")}
            </div>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight leading-tight">
              {lang === "es"
                ? <>Cómo y por qué operar<br className="hidden sm:block" /> MASCI.</>
                : <>How and why to run<br className="hidden sm:block" /> MASCI operations.</>}
            </h1>
            <p className="mt-3 text-sm sm:text-base text-slate-300 max-w-xl leading-relaxed">
              {isAuthenticated
                ? t("Portal-specific training, role-based help, troubleshooting, and operational knowledge. Filtered by your portal access.")
                : t("Public field-crew training is open below. Portal-specific training (HR · Safety · Shop · Dispatch · PM · Field Leadership · Admin) appears when you sign in.")}
            </p>
            {!isAuthenticated && (
              <Link
                to="/sign-in"
                className="inline-flex items-center mt-4 h-10 px-4 rounded-md bg-red-700 hover:bg-red-800 text-white text-xs font-bold uppercase tracking-wider transition-colors"
                data-testid="guidance-signin-cta"
              >
                <LogIn className="w-4 h-4 mr-2" />
                {t("Sign in for portal training")}
              </Link>
            )}
          </div>
          <div className="hidden md:flex items-end justify-end">
            <BookOpen className="w-32 h-32 text-white/10" strokeWidth={1.2} />
          </div>
        </div>
      </section>

      <SearchBox onResults={setSearchResults} query={query} setQuery={setQuery} />

      {/* Public Field Crew Training — first-class tiles for anyone.
          These do not require login. RBAC-safe: every article shown is
          tagged `public` and contains no restricted operational intel. */}
      {visiblePublicTracks.length > 0 && (
        <section className="mt-6" data-testid="guidance-public-tracks">
          <div className="flex items-baseline justify-between mb-3">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
                {t("Public · No Sign-In Required")}
              </div>
              <h2 className="font-display text-xl font-black tracking-tight">
                {t("Field Crew Training")}
              </h2>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {visiblePublicTracks.map((tk) => {
              const Icon = tk.icon;
              const tileLabel = (lang === "es" && tk.labelEs) ? tk.labelEs : tk.label;
              const tileBlurb = (lang === "es" && tk.blurbEs) ? tk.blurbEs : tk.blurb;
              return (
                <Link
                  key={tk.id}
                  to={`/guidance/${tk.id}`}
                  className="group relative bg-white border-2 border-slate-300 rounded-md p-4 hover:border-red-700 hover:shadow-md transition-all"
                  data-testid={`guidance-public-track-${tk.id}`}
                >
                  <div className="absolute inset-y-0 left-0 w-1 bg-red-700 rounded-l-sm" />
                  <div className="flex items-start gap-3">
                    <div className="inline-flex items-center justify-center w-10 h-10 rounded bg-red-50 text-red-700 shrink-0 group-hover:bg-red-100 transition-colors">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-display text-base font-bold text-slate-900 leading-tight">
                        {tileLabel}
                      </div>
                      <div className="text-[12px] text-slate-600 mt-1 leading-snug">
                        {tileBlurb}
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* iter203 — Portal Sign-In Directory inside Operational Guidance.
          Always visible (anon + authenticated). Each card = one protected
          portal with: identity kicker · purpose · "Sign in" CTA (deep
          link to /<portal>/login) · "Learn about this portal" link to
          the guidance identity article (or /guidance fallback until
          Pass 5 saturates per-portal identity articles).

          This is the operational gateway pattern the operator surfaced:
          Guidance should be where users LEARN about a portal AND where
          they navigate to its login — not just a training catalog. */}
      <PortalSignInDirectory lang={lang} />

      {/* Portal Training — first-class portal tracks for authenticated
          users. Safety + Dispatch are always surfaced when authorized. */}
      {visibleTracks.length > 0 && (
        <section className="mt-8" data-testid="guidance-portal-tracks">
          <div className="flex items-baseline justify-between mb-3">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-700 font-bold">
                {t("Sign-In Required · Your Portals")}
              </div>
              <h2 className="font-display text-xl font-black tracking-tight">
                {t("Portal Training")}
              </h2>
            </div>
            <Link
              to="/guidance/section/portals"
              className="text-[12px] font-bold uppercase tracking-wider text-amber-700 hover:underline"
              data-testid="guidance-portal-tracks-all"
            >
              {t("All portal articles")} →
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {visibleTracks.map((tk) => (
              <Link
                key={tk.key}
                to="/guidance/section/portals"
                className="group relative bg-white border-2 border-slate-300 rounded-md p-4 hover:border-amber-500 hover:shadow-md transition-all overflow-hidden"
                data-testid={`guidance-portal-track-${tk.key}`}
              >
                <div className={`absolute inset-y-0 left-0 w-1 ${ACCENT_BAND[tk.accent] || "bg-slate-700"}`} />
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
                  {tk.key}
                </div>
                <div className="font-display text-base font-bold text-slate-900 mt-1 leading-tight">
                  {t(tk.label)}
                </div>
                <div className="text-[12px] text-slate-500 mt-1">
                  {portalCounts[tk.key]} {portalCounts[tk.key] === 1 ? t("article") : t("articles")}
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Browse by topic — tertiary navigation for power users */}
      <section className="mt-8">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 font-bold">
          {t("By Topic")}
        </div>
        <h2 className="font-display text-xl font-black tracking-tight mb-3">
          {t("Browse all guidance")}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {sections.map((s) => {
            const Icon = SECTION_ICONS[s.icon] || BookOpen;
            return (
              <Link
                key={s.id}
                to={`/guidance/section/${s.id}`}
                className="bg-white border-2 border-slate-300 rounded-md p-4 hover:border-amber-500 hover:shadow-md transition-all"
                data-testid={`guidance-section-card-${s.id}`}
              >
                <div className="flex items-start gap-3">
                  <div className="inline-flex items-center justify-center w-10 h-10 rounded bg-slate-100 text-slate-700 shrink-0">
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-slate-900">{t(s.title)}</div>
                    <div className="text-[12px] text-slate-500 mt-0.5">
                      {s.count} {s.count === 1 ? t("article") : t("articles")}
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {sections.length === 0 && visibleTracks.length === 0 && visiblePublicTracks.length === 0 && (
        <div className="text-center text-slate-500 py-10" data-testid="guidance-empty">
          {t("No guidance is available for your access level yet.")}
        </div>
      )}

      {/* Iter195: the legacy /ops-training link has been retired.
          That route now redirects into this Center. There is no longer
          an unrestricted side door into operator training. */}
    </Shell>
  );
}

function Shell({ title, children }) {
  // Iter195-fix: proper MASCI header + navigation. The Operational
  // Guidance Center is a destination page, not a floating shell —
  // users need branding, sign-in entry, and a clear way home.
  // iter202 — translation fix for header chrome.
  const { t } = useT();
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-6xl mx-auto px-4 sm:px-8 py-4 sm:py-5 flex items-center justify-between">
          <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
          <MasciLogo variant="mark" size="lg" className="sm:hidden" homeLink="/" />
          <div className="flex items-center gap-2">
            <Link
              to="/"
              className="inline-flex items-center h-9 px-3 rounded-md bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs font-bold uppercase tracking-wide transition-colors"
              data-testid="guidance-home-link"
            >
              <Home className="w-3.5 h-3.5 mr-1.5" />
              {t("Home")}
            </Link>
            <Link
              to="/sign-in"
              className="hidden sm:inline-flex items-center h-9 px-3 rounded-md bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs font-bold uppercase tracking-wide transition-colors"
              data-testid="guidance-signin-link"
            >
              {t("Sign in")}
            </Link>
            <LangToggle />
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-8 py-6 sm:py-8">
        {title && (
          <h1 className="font-display text-2xl font-black tracking-tight text-slate-900 mb-4">
            {title}
          </h1>
        )}
        {children}
      </main>
    </div>
  );
}
