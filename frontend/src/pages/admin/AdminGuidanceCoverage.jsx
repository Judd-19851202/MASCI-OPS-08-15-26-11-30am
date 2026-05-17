// AdminGuidanceCoverage.jsx — iter193. Admin-only read-only Coverage
// Dashboard for the Operational Guidance Center. Two views in one page:
//   1) Structural coverage matrix (per-portal × per-section article counts)
//   2) Search-zero-results signal (recent + aggregated demand-driven gaps)
//
// This is operational governance infrastructure, not analytics. It tells
// admins where guidance content is missing (structural gaps) and where
// users are looking for content that doesn't exist (demand gaps).
//
// Scope discipline:
//   - admin-strict read-only (backend gate is canonical)
//   - no mutation surface
//   - no PII in displayed search-miss rows
import React, { useEffect, useState } from "react";
import {
  BookOpen, RefreshCcw, Loader2, AlertCircle, Search, CheckCircle2,
} from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

const REQUIRED_SECTIONS = ["roles", "portals", "troubleshooting", "knowledge"];

export default function AdminGuidanceCoverage() {
  const [coverage, setCoverage] = useState(null);
  const [misses, setMisses] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [c, m] = await Promise.all([
        api.get("/admin/guidance/coverage"),
        api.get("/admin/guidance/search-misses?limit=200"),
      ]);
      setCoverage(c.data);
      setMisses(m.data);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Failed to load guidance coverage";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <AdminShell title="Operational Guidance Coverage">
      <div className="space-y-8" data-testid="admin-guidance-coverage-panel">
        {/* Header */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="text-xs font-mono uppercase tracking-widest text-slate-500">
              Phase 3 · Operational Governance
            </div>
            <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
              <BookOpen className="h-7 w-7 text-amber-600" />
              Guidance Coverage Dashboard
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">
              Structural coverage per portal and recent search-zero-result signals.
              Use this to spot guidance gaps as the platform evolves. Read-only — no
              mutations from this panel.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={load}
            disabled={loading}
            data-testid="admin-guidance-coverage-refresh"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RefreshCcw className="h-4 w-4 mr-2" />
            )}
            Refresh
          </Button>
        </div>

        {error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-800">
            <AlertCircle className="inline h-4 w-4 mr-1" /> {error}
          </div>
        )}

        {/* Summary */}
        {coverage && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3" data-testid="coverage-summary">
            <SummaryTile label="Articles total" value={coverage.article_count} />
            <SummaryTile label="Portals tracked" value={coverage.portals.length} />
            <SummaryTile
              label="Portals mature"
              value={coverage.portals.filter((p) => p.mature).length}
              accent="emerald"
            />
            <SummaryTile
              label="Portals with gaps"
              value={coverage.portals.filter((p) => !p.mature).length}
              accent={coverage.portals.some((p) => !p.mature) ? "amber" : "slate"}
            />
          </div>
        )}

        {/* Coverage matrix */}
        {coverage && (
          <section data-testid="coverage-matrix-section">
            <h2 className="text-base font-semibold text-slate-800 mb-3">
              Structural Coverage Matrix
            </h2>
            <div className="overflow-x-auto rounded-md border border-slate-200">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-slate-700">
                      Portal
                    </th>
                    {REQUIRED_SECTIONS.map((s) => (
                      <th
                        key={s}
                        className="px-3 py-2 text-center font-medium text-slate-700"
                      >
                        {s}
                      </th>
                    ))}
                    <th className="px-3 py-2 text-center font-medium text-slate-700">
                      Total
                    </th>
                    <th className="px-3 py-2 text-center font-medium text-slate-700">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {coverage.portals.map((p) => (
                    <tr
                      key={p.portal}
                      className="border-t border-slate-100"
                      data-testid={`coverage-row-${p.portal}`}
                    >
                      <td className="px-3 py-2 font-mono text-slate-900">
                        {p.portal}
                      </td>
                      {REQUIRED_SECTIONS.map((s) => {
                        const n = p.sections?.[s] || 0;
                        const ok = n > 0;
                        return (
                          <td
                            key={s}
                            className={`px-3 py-2 text-center ${
                              ok ? "text-slate-900" : "text-amber-700 font-semibold"
                            }`}
                          >
                            {ok ? n : "—"}
                          </td>
                        );
                      })}
                      <td className="px-3 py-2 text-center text-slate-700">
                        {p.total}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {p.mature ? (
                          <span className="inline-flex items-center gap-1 text-emerald-700 text-xs font-medium">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Mature
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-amber-700 text-xs font-medium">
                            <AlertCircle className="h-3.5 w-3.5" />
                            Gaps: {p.gaps.join(", ")}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              "Mature" = at least one article in every required section
              ({REQUIRED_SECTIONS.join(" · ")}). Counts include articles
              scoped to that portal; admin-only articles are not credited to
              other portals.
            </p>
          </section>
        )}

        {/* Search misses */}
        {misses && (
          <section data-testid="search-misses-section">
            <h2 className="text-base font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <Search className="h-4 w-4" />
              Search Demand Signal · Recent Zero-Result Queries
            </h2>
            {misses.recent?.length ? (
              <div className="grid gap-6 lg:grid-cols-2">
                <div>
                  <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
                    Most-asked (last 200 misses, aggregated)
                  </div>
                  <ul className="space-y-1 text-sm" data-testid="search-misses-top">
                    {(misses.top || []).slice(0, 20).map((t) => (
                      <li
                        key={t.query}
                        className="flex items-center justify-between border-b border-slate-100 py-1"
                      >
                        <span className="font-mono text-slate-800 truncate pr-2">
                          {t.query}
                        </span>
                        <span className="text-xs text-slate-500">×{t.count}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
                    Most recent (chronological)
                  </div>
                  <ul className="space-y-1 text-xs" data-testid="search-misses-recent">
                    {misses.recent.slice(0, 25).map((r, i) => (
                      <li
                        key={`${r.ts}-${i}`}
                        className="flex items-baseline justify-between border-b border-slate-100 py-1"
                      >
                        <span className="font-mono text-slate-700 truncate pr-2">
                          {r.query}
                        </span>
                        <span className="text-slate-400">
                          {(r.scopes || []).join(",") || "—"}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                No zero-result searches yet. As users search, gaps will surface here.
              </p>
            )}
            <p className="mt-3 text-xs text-slate-500">
              Captured per zero-result search: query text, UTC timestamp, scope set.
              No IP, no user identifier, no payload. Operational gap-intelligence only.
            </p>
          </section>
        )}
      </div>
    </AdminShell>
  );
}

function SummaryTile({ label, value, accent = "slate" }) {
  const tone =
    accent === "emerald"
      ? "border-emerald-300 bg-emerald-50 text-emerald-900"
      : accent === "amber"
      ? "border-amber-300 bg-amber-50 text-amber-900"
      : "border-slate-200 bg-white text-slate-900";
  return (
    <div className={`rounded-md border p-3 ${tone}`}>
      <div className="text-xs uppercase tracking-wider opacity-75">{label}</div>
      <div className="mt-1 text-2xl font-bold">{value}</div>
    </div>
  );
}
