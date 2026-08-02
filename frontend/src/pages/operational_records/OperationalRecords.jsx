// OperationalRecords.jsx — Phase V.1 · M1 · Option C.
//
// Unified operational records dashboard. One search · one timeline ·
// one list across two substrates (ODR + frozen Daily Reports).
//
// The user does not need to know which substrate owns a record. The
// archive badge explains why legacy entries look different.
//
// Doctrine:
//   /app/memory/M1_OPTION_C_IMPLEMENTATION_PLAN.md
//   /app/memory/UNIFIED_RECORDS_PROJECTOR_CERTIFICATION.md
//   /app/memory/ARCHIVE_VISUAL_TREATMENT_STANDARD.md
//   /app/memory/ODR_PLATFORM_INHERITANCE_DOCTRINE.md (one MASCI Ops feel)

import React from "react";
import { Link } from "react-router-dom";
import { listOperationalRecords } from "@/lib/odrApi";
import { useT } from "@/lib/i18n";
import ArchiveBadge, {
  ArchiveExplainerCard,
} from "@/components/odr/ArchiveBadge";

const KIND_FILTERS = [
  { value: "", label: "All records" },
  { value: "odr", label: "ODR only" },
  { value: "legacy_daily_report", label: "Archive only" },
];

export default function OperationalRecords() {
  const { t } = useT();
  const [items, setItems] = React.useState([]);
  const [counts, setCounts] = React.useState({ total: 0, odr: 0, legacy_daily_report: 0 });
  const [kind, setKind] = React.useState("");
  const [project, setProject] = React.useState("");
  const [search, setSearch] = React.useState("");
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState("");

  const refresh = React.useCallback(() => {
    setLoading(true);
    const params = { limit: 200 };
    if (kind) params.kind = kind;
    if (project) params.project_number = project;
    listOperationalRecords(params)
      .then((d) => {
        setItems(d.items || []);
        setCounts(d.counts || { total: 0, odr: 0, legacy_daily_report: 0 });
        setErr("");
      })
      .catch((e) => setErr(e.message || "Load failed"))
      .finally(() => setLoading(false));
  }, [kind, project]);

  React.useEffect(() => {
    refresh();
  }, [refresh]);

  const visibleItems = React.useMemo(() => {
    if (!search) return items;
    const q = search.toLowerCase();
    return items.filter(
      (r) =>
        (r.doc_id || "").toLowerCase().includes(q) ||
        (r.project_name || "").toLowerCase().includes(q) ||
        (r.project_number || "").toLowerCase().includes(q) ||
        (r.foreman_name || "").toLowerCase().includes(q)
    );
  }, [items, search]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-6xl px-4 py-6">
        <header className="mb-6">
          <div className="text-xs uppercase tracking-wider text-slate-500">
            {t("MASCI Operational Records")}
          </div>
          <h1 className="text-2xl font-semibold text-slate-900 mt-1">
            {t("Operational Records")}
          </h1>
          <p className="mt-1 text-sm text-slate-600 max-w-2xl">
            {t("Every project record across MASCI Ops in one place. New entries are filed as Operational Daily Records (ODR). Historical Daily Reports remain available, byte-identical to the day they were signed.")}
          </p>
        </header>

        <ArchiveExplainerCard className="mb-6" />

        {/* Filter row */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <input
            data-testid="op-records-search"
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("Search doc id, project, foreman…")}
            className="w-64 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-300"
          />
          <input
            data-testid="op-records-project-filter"
            type="text"
            value={project}
            onChange={(e) => setProject(e.target.value)}
            placeholder={t("Project number")}
            className="w-44 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-300"
          />
          <select
            data-testid="op-records-kind-filter"
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-300"
          >
            {KIND_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
          <button
            data-testid="op-records-refresh"
            onClick={refresh}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
          >
            {t("Refresh")}
          </button>
          <div className="ml-auto text-xs text-slate-500" data-testid="op-records-counts">
            {counts.total} {t("record(s)")} · {counts.odr} ODR · {counts.legacy_daily_report} {t("archived")}
          </div>
        </div>

        {err ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            {err}
          </div>
        ) : null}

        {loading ? (
          <div className="rounded-md border border-slate-200 bg-white p-6 text-sm text-slate-500" data-testid="op-records-loading">
            {t("Loading records…")}
          </div>
        ) : (
          <ul
            className="space-y-2"
            data-testid="op-records-list"
          >
            {visibleItems.length === 0 ? (
              <li className="rounded-md border border-slate-200 bg-white p-6 text-sm text-slate-500">
                {t("No records matched.")}
              </li>
            ) : null}
            {visibleItems.map((r) => (
              <li
                key={`${r.record_kind}:${r.id}`}
                data-testid={`op-record-${r.record_kind}-${r.id}`}
                className={
                  "rounded-md border bg-white p-4 transition-shadow hover:shadow-sm " +
                  (r.archive
                    ? "border-slate-200"
                    : "border-slate-200")
                }
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Link
                    to={r.viewer_route}
                    className="text-sm font-mono text-slate-900 hover:underline"
                    data-testid={`op-record-doc-id-${r.doc_id}`}
                  >
                    {r.doc_id || "—"}
                  </Link>
                  {r.archive ? <ArchiveBadge size="sm" /> : null}
                  <div className="ml-auto text-xs text-slate-500">
                    {r.report_date || ""}
                  </div>
                </div>
                <div className="mt-1 text-sm text-slate-800">
                  {r.project_name || "—"}{" "}
                  <span className="text-slate-500 text-xs">
                    {r.project_number ? `· ${r.project_number}` : ""}
                  </span>
                </div>
                <div className="mt-1 text-xs text-slate-500 flex flex-wrap gap-x-4 gap-y-1">
                  <span>{t("Foreman")}: {r.foreman_name || "—"}</span>
                  {r.superintendent_name ? (
                    <span>{t("Super")}: {r.superintendent_name}</span>
                  ) : null}
                  <span>{t("Photos")}: {r.photo_count}</span>
                  {r.has_foreman_signature ? (
                    <span>{t("Foreman signed")}</span>
                  ) : null}
                  {r.has_superintendent_signature ? (
                    <span>{t("Super signed")}</span>
                  ) : null}
                  {r.archive ? (
                    <span className="text-slate-500">
                      {t("Original format preserved")}
                    </span>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
