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
// Search
// ─────────────────────────────────────────────────────────────────────
function SearchBox({ onResults, query, setQuery }) {
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
        placeholder="Search guidance — by role, task, or keyword"
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
  const { lang } = useT();  // iter199 — Pass 3 translation toggle
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
      <Shell title="Search results">
        <button
          onClick={() => { setSearchResults(null); setQuery(""); }}
          className="inline-flex items-center gap-1 text-[12px] font-bold uppercase tracking-wider text-amber-700 hover:underline mb-3"
          data-testid="guidance-search-back"
        >
          <ChevronLeft className="w-4 h-4" /> All guidance
        </button>
        <SearchBox onResults={setSearchResults} query={query} setQuery={setQuery} />
        {searchResults.length === 0 ? (
          <div className="text-center text-slate-500 py-10" data-testid="guidance-search-empty">
            No matching guidance available for your access level.
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
        <Shell title="Not available">
          <div className="text-center text-slate-500 py-10" data-testid="guidance-article-not-found">
            This guidance isn't available for your access level.
            <div className="mt-4">
              <Link to="/guidance" className="text-amber-700 hover:underline">Back to Guidance</Link>
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
          <ChevronLeft className="w-4 h-4" /> Back
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
              Related guidance
            </strong>
            <ul className="space-y-1">
              {article.related.map((r) => (
                <li key={r.id}>
                  <Link
                    to={`/guidance/${r.id}`}
                    className="text-amber-700 hover:text-amber-900 hover:underline inline-flex items-center gap-1 text-sm"
                    data-testid={`guidance-related-${r.id}`}
                  >
                    <ArrowRightCircle className="w-3.5 h-3.5" />
                    {r.title}
                  </Link>
                </li>
              ))}
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
      <Shell title={sec?.title || "Section"}>
        <button
          type="button"
          onClick={() => navigate("/guidance")}
          className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900 mb-3"
          data-testid="guidance-back-to-home"
        >
          <ChevronLeft className="w-4 h-4" /> All guidance
        </button>
        <SearchBox onResults={setSearchResults} query={query} setQuery={setQuery} />
        {loading ? (
          <Loader2 className="w-6 h-6 animate-spin mx-auto my-12 text-slate-400" />
        ) : articles.length === 0 ? (
          <div className="text-center text-slate-500 py-10">No articles in this section for your access level.</div>
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
  const PUBLIC_TRACKS = [
    { id: "public-tools-map",         icon: LayoutGrid, label: "All Public Field Tools",   blurb: "Index of every no-login tool on the platform." },
    { id: "role-new-employee",        icon: UserPlus,   label: "New Employee Basics",       blurb: "First-week orientation for any role." },
    { id: "public-mobile-qr",         icon: Zap,        label: "Scan-and-Go (QR Codes)",    blurb: "Open MASCI on your phone in seconds." },
    { id: "onboard-mobile",           icon: BookOpen,   label: "Using MASCI on a Phone",    blurb: "Mobile-first tips that save your work." },
    { id: "public-photos",            icon: Lightbulb,  label: "Photos That Actually Help", blurb: "Wide shot · close-up · clear." },
    { id: "public-daily-report-basics", icon: LayoutGrid, label: "Daily Report Basics",    blurb: "What it is, why yours matters." },
    { id: "public-preop-basics",      icon: Shield,     label: "Equipment Pre-Op Basics",   blurb: "Walk it. Sign it. Flag what's broken." },
    { id: "public-toolbox-talks",     icon: UserCog,    label: "Toolbox Talks / Safety Meetings", blurb: "Sign in. Listen. The record is your signature." },
    { id: "public-qaqc-basics",       icon: LifeBuoy,   label: "QA / QC for Field Crews",   blurb: "Photo before you cover it. Sign-offs that matter." },
    { id: "public-material-calculator", icon: Lightbulb, label: "Material Calculator",     blurb: "Concrete · gravel · asphalt quick math." },
    { id: "public-incident-basics",   icon: AlertTriangle, label: "If Something Happens",  blurb: "First steps after injury, near-miss, or damage." },
    { id: "public-cant-login",        icon: LifeBuoy,   label: "I Can't Log In",            blurb: "Common login problems & fixes." },
    { id: "public-who-to-ask",        icon: UserCog,    label: "Who Do I Ask for Help?",    blurb: "A quick map of who handles what." },
    { id: "public-why-documentation", icon: Shield,     label: "Why This Paperwork Matters", blurb: "Field crew's version of 'why'." },
    { id: "onboard-login",            icon: LogIn,      label: "How to Log In",             blurb: "First-time login basics." },
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
              MASCI Operations Platform · Operational Guidance Center
            </div>
            <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight leading-tight">
              How and why to run<br className="hidden sm:block" /> MASCI operations.
            </h1>
            <p className="mt-3 text-sm sm:text-base text-slate-300 max-w-xl leading-relaxed">
              {isAuthenticated
                ? "Portal-specific training, role-based help, troubleshooting, and operational knowledge. Filtered by your portal access."
                : "Public field-crew training is open below. Portal-specific training (HR · Safety · Shop · Dispatch · PM · Field Leadership · Admin) appears when you sign in."}
            </p>
            {!isAuthenticated && (
              <Link
                to="/sign-in"
                className="inline-flex items-center mt-4 h-10 px-4 rounded-md bg-red-700 hover:bg-red-800 text-white text-xs font-bold uppercase tracking-wider transition-colors"
                data-testid="guidance-signin-cta"
              >
                <LogIn className="w-4 h-4 mr-2" />
                Sign in for portal training
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
                Public · No Sign-In Required
              </div>
              <h2 className="font-display text-xl font-black tracking-tight">
                Field Crew Training
              </h2>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {visiblePublicTracks.map((t) => {
              const Icon = t.icon;
              return (
                <Link
                  key={t.id}
                  to={`/guidance/${t.id}`}
                  className="group relative bg-white border-2 border-slate-300 rounded-md p-4 hover:border-red-700 hover:shadow-md transition-all"
                  data-testid={`guidance-public-track-${t.id}`}
                >
                  <div className="absolute inset-y-0 left-0 w-1 bg-red-700 rounded-l-sm" />
                  <div className="flex items-start gap-3">
                    <div className="inline-flex items-center justify-center w-10 h-10 rounded bg-red-50 text-red-700 shrink-0 group-hover:bg-red-100 transition-colors">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-display text-base font-bold text-slate-900 leading-tight">
                        {t.label}
                      </div>
                      <div className="text-[12px] text-slate-600 mt-1 leading-snug">
                        {t.blurb}
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* Portal Training — first-class portal tracks for authenticated
          users. Safety + Dispatch are always surfaced when authorized. */}
      {visibleTracks.length > 0 && (
        <section className="mt-8" data-testid="guidance-portal-tracks">
          <div className="flex items-baseline justify-between mb-3">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-700 font-bold">
                Sign-In Required · Your Portals
              </div>
              <h2 className="font-display text-xl font-black tracking-tight">
                Portal Training
              </h2>
            </div>
            <Link
              to="/guidance/section/portals"
              className="text-[12px] font-bold uppercase tracking-wider text-amber-700 hover:underline"
              data-testid="guidance-portal-tracks-all"
            >
              All portal articles →
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {visibleTracks.map((t) => (
              <Link
                key={t.key}
                to="/guidance/section/portals"
                className="group relative bg-white border-2 border-slate-300 rounded-md p-4 hover:border-amber-500 hover:shadow-md transition-all overflow-hidden"
                data-testid={`guidance-portal-track-${t.key}`}
              >
                <div className={`absolute inset-y-0 left-0 w-1 ${ACCENT_BAND[t.accent] || "bg-slate-700"}`} />
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
                  {t.key}
                </div>
                <div className="font-display text-base font-bold text-slate-900 mt-1 leading-tight">
                  {t.label}
                </div>
                <div className="text-[12px] text-slate-500 mt-1">
                  {portalCounts[t.key]} {portalCounts[t.key] === 1 ? "article" : "articles"}
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Browse by topic — tertiary navigation for power users */}
      <section className="mt-8">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 font-bold">
          By Topic
        </div>
        <h2 className="font-display text-xl font-black tracking-tight mb-3">
          Browse all guidance
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
                    <div className="font-semibold text-slate-900">{s.title}</div>
                    <div className="text-[12px] text-slate-500 mt-0.5">
                      {s.count} {s.count === 1 ? "article" : "articles"}
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
          No guidance is available for your access level yet.
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
              Home
            </Link>
            <Link
              to="/sign-in"
              className="hidden sm:inline-flex items-center h-9 px-3 rounded-md bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs font-bold uppercase tracking-wide transition-colors"
              data-testid="guidance-signin-link"
            >
              Sign in
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
