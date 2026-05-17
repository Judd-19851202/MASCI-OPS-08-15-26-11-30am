// OperationalGuidanceCenter — the new top-level shell for MASCI's
// Training / Help / Operational Guidance system.
//
// Phase A scope (preview only):
//   • RBAC-aware section + article rendering, driven entirely by the
//     server (/api/guidance/*). Frontend trusts the server's visibility
//     decisions; never displays a title the server didn't return.
//   • Single-page hub with: sections grid · search · article reader.
//   • Plain content blocks (p / steps / bullets / why / next / warn /
//     tip / mistakes). One renderer for everything.
//   • Wraps and absorbs the existing /training and /ops-training
//     entry points — those routes remain reachable as legacy deep
//     links, but the home hub directs new traffic here.
//
// Style: matches MASCI's existing card/typography conventions.
// Mobile-first; the section grid collapses to a single column under md.

import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  BookOpen, Search, Loader2, ChevronLeft, UserCog, Zap, LayoutGrid,
  LifeBuoy, Lightbulb, Shield, UserPlus, AlertTriangle, Lightbulb as TipIcon,
  AlertCircle, ArrowRightCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

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
function Block({ block }) {
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
              Why this matters
            </strong>
            {block.text}
          </div>
        </div>
      );
    case "next":
      return (
        <div className="border border-emerald-200 bg-emerald-50 rounded p-3">
          <strong className="text-[11px] uppercase tracking-wider text-emerald-700 block mb-1">
            What happens next
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
            Common mistakes
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
  const [sections, setSections] = useState([]);
  const [articles, setArticles] = useState([]);
  const [article, setArticle] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  // Load section catalog on mount
  useEffect(() => {
    (async () => {
      try {
        const r = await api.get("/guidance/sections");
        setSections(r?.data?.sections || []);
      } catch { /* render nothing */ }
    })();
  }, []);

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
          {article.title}
        </h1>
        {article.summary && (
          <p className="text-slate-600 mt-1 text-[15px]">{article.summary}</p>
        )}
        <div className="mt-6 space-y-4" data-testid="guidance-article-body">
          {(article.body || []).map((b, i) => <Block key={i} block={b} />)}
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
          data-testid="guidance-back-to-hub"
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

  // ── Render: hub home ──────────────────────────────────────────────
  return (
    <Shell>
      <div className="bg-white border-2 border-slate-300 rounded-md p-5 mb-4 flex items-start gap-3" data-testid="guidance-hub-header">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-amber-600 text-white shrink-0">
          <BookOpen className="w-6 h-6" />
        </div>
        <div className="flex-1">
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
            Operational Guidance Center
          </span>
          <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
            How and why to run MASCI operations
          </h1>
          <p className="text-sm text-slate-600 mt-1 leading-relaxed">
            Role-based training · task-based help · troubleshooting · operational knowledge.
            What you see here is filtered by your portal access.
          </p>
        </div>
      </div>

      <SearchBox onResults={setSearchResults} query={query} setQuery={setQuery} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-5">
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

      {sections.length === 0 && (
        <div className="text-center text-slate-500 py-10" data-testid="guidance-hub-empty">
          No guidance is available for your access level yet.
        </div>
      )}

      <div className="mt-8 pt-4 border-t border-slate-200">
        <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-2 font-bold">
          Legacy training pages
        </div>
        <div className="flex flex-wrap gap-2 text-[13px]">
          <Link to="/training" className="text-amber-700 hover:underline" data-testid="legacy-training-link">
            Training Hub
          </Link>
          <span className="text-slate-400">·</span>
          <Link to="/ops-training" className="text-amber-700 hover:underline" data-testid="legacy-ops-training-link">
            Ops Training Center
          </Link>
        </div>
      </div>
    </Shell>
  );
}

function Shell({ title, children }) {
  return (
    <div className="min-h-screen bg-slate-50 py-6 px-4">
      <div className="max-w-5xl mx-auto">
        {title && (
          <h1 className="font-display text-2xl font-black tracking-tight text-slate-900 mb-4">
            {title}
          </h1>
        )}
        {children}
      </div>
    </div>
  );
}
