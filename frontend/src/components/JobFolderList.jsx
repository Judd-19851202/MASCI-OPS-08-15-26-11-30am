import React, { useMemo, useState } from "react";
import { ChevronRight, ChevronDown, FolderOpen, Folder, Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";
import { formatDateLong } from "@/lib/utils";
import { formatOperatorJobLabel, sanitizeOperatorProjectNumber } from "@/lib/operatorLanguage";

/**
 * <JobFolderList>
 *
 * Reusable accordion that groups any list of records by their MASCI job
 * (`project_number` / `project_name`) and renders one folder per job —
 * sorted by most-recent activity first, all collapsed by default.
 *
 * Used by every Records & Forms dashboard in admin + PM portals
 * (Daily Reports, Site Inspections, Meetings, Incidents, Pre-Op, QA/QC,
 * Safety Forms) so the 31-active-jobs flat list isn't a wall of dates.
 *
 * Required props:
 *   items       — array of records, each with project_number + project_name
 *                 + the date field named below
 *   dateField   — string, name of the date field on each record
 *                 (e.g. "report_date", "meeting_date", "incident_date",
 *                  "inspection_date", "issued_at")
 *   renderItem  — (item) => ReactNode, draws the existing per-row JSX so
 *                 every dashboard keeps its own style/badges/buttons
 *
 * Optional props:
 *   testIdPrefix — used for data-testid values (default "job-folder")
 *   emptyMsg     — shown when items is empty (string)
 */
export default function JobFolderList({
  items,
  dateField,
  renderItem,
  testIdPrefix = "job-folder",
  emptyMsg = null,
  jobsMaster = null,         // DR-JOB-002 · canonical { project_number → project_name } map (optional)
  showCert = false,          // DR-JOB-003 · admin opt-in for cert/test pollution tier
}) {
  const { t } = useT();
  const [search, setSearch] = useState("");
  const [openMap, setOpenMap] = useState({}); // { "25-03": true, ... }

  // DR-JOB-003 · conservative cert/test pollution matcher. Returns true when
  // the row appears to be a smoke/cert/test artefact that should NOT show
  // in the default operational hub.
  const isCertOrTest = (it) => {
    const blob = `${it.project_number || ""} ${it.project_name || ""}`.toUpperCase();
    if (!blob.trim()) return false;
    return (
      blob.includes("_PROD_CERT_DO_NOT_USE") ||
      blob.includes("PROD-POST-DEPLOY-CERT-SMOKE") ||
      blob.includes("PROD-ORPHAN-CORNER-VERIFY") ||
      /(^|[_\s-])(TEST|SMOKE|VERIFY|CERT|DEMO|SEED|SAMPLE|PREVIEW|QA-)([_\s-]|$)/.test(blob) ||
      /^ITER\d+/i.test(blob)
    );
  };

  // ── DR-JOB-002 · Group records by CANONICAL project_number ──────────
  const folders = useMemo(() => {
    const byKey = new Map();
    const ORPHAN = "__ORPHAN__";
    for (const it of items || []) {
      if (!showCert && isCertOrTest(it)) continue;
      const rawNum = (it.project_number || "").trim();
      const submittedName = (it.project_name || "").trim();
      // canonical number = jobs_master match (case-insensitive) → else raw → else orphan bucket
      const canonicalNum = rawNum || ORPHAN;
      // canonical display name preference:
      //   1. jobs_master canonical name when a row exists for this pn
      //   2. submitted project_name from this row
      //   3. fallback "Unmatched Project · {pn}" or "(No Job)"
      let canonicalName = "";
      if (jobsMaster && rawNum) {
        canonicalName = jobsMaster[rawNum] || jobsMaster[rawNum.toUpperCase()] || "";
      }
      if (!canonicalName) canonicalName = submittedName;
      if (!canonicalName) canonicalName = rawNum
        ? `${t("Unmatched Project")} · ${rawNum}`
        : t("Unmatched / Needs Project Review");

      const key = canonicalNum;  // KEY IS NOW PROJECT NUMBER ONLY
      if (!byKey.has(key)) {
        byKey.set(key, {
          key,
          number: rawNum || "—",
          name: canonicalName,
          isOrphan: !rawNum,
          submittedNames: new Set(),
          items: [],
          mostRecent: null,
        });
      }
      const folder = byKey.get(key);
      if (submittedName) folder.submittedNames.add(submittedName);
      folder.items.push(it);
      const d = it[dateField];
      if (d && (!folder.mostRecent || d > folder.mostRecent)) {
        folder.mostRecent = d;
      }
    }
    // Sort folders by most-recent activity DESC. Folders with no date
    // sink to the bottom, alphabetised by job name.
    const arr = Array.from(byKey.values());
    arr.sort((a, b) => {
      if (a.mostRecent && b.mostRecent) {
        return a.mostRecent < b.mostRecent ? 1 : a.mostRecent > b.mostRecent ? -1 : 0;
      }
      if (a.mostRecent) return -1;
      if (b.mostRecent) return 1;
      return a.name.localeCompare(b.name);
    });
    // Sort each folder's items most-recent first too
    for (const f of arr) {
      f.items.sort((a, b) => {
        const da = a[dateField] || "";
        const db = b[dateField] || "";
        return da < db ? 1 : da > db ? -1 : 0;
      });
    }
    return arr;
  }, [items, dateField, t, jobsMaster, showCert]);

  // ── Filter by search ─────────────────────────────────────────────────
  const visibleFolders = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return folders;
    return folders.filter(
      (f) =>
        f.name.toLowerCase().includes(q) || f.number.toLowerCase().includes(q)
    );
  }, [folders, search]);

  const toggleAll = (open) => {
    const next = {};
    visibleFolders.forEach((f) => {
      next[f.key] = open;
    });
    setOpenMap(next);
  };

  if (!items || items.length === 0) {
    return (
      <div className="p-10 sm:p-16 text-center text-slate-500" data-testid={`${testIdPrefix}-empty`}>
        {emptyMsg || t("No records yet.")}
      </div>
    );
  }

  return (
    <div data-testid={testIdPrefix}>
      {/* Toolbar: search + expand-all / collapse-all */}
      <div className="px-4 sm:px-5 py-3 border-b-2 border-slate-200 bg-slate-50 flex flex-col sm:flex-row gap-2 sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("Search jobs…")}
            className="pl-9 pr-9 h-10 border-2 border-slate-300"
            data-testid={`${testIdPrefix}-search`}
          />
          {search && (
            <button
              type="button"
              onClick={() => setSearch("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-700"
              data-testid={`${testIdPrefix}-search-clear`}
              aria-label={t("Clear search")}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => toggleAll(true)}
            className="px-3 h-10 rounded-md border-2 border-slate-300 hover:border-slate-500 text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700"
            data-testid={`${testIdPrefix}-expand-all`}
          >
            {t("Expand All")}
          </button>
          <button
            type="button"
            onClick={() => toggleAll(false)}
            className="px-3 h-10 rounded-md border-2 border-slate-300 hover:border-slate-500 text-xs font-mono uppercase tracking-[0.15em] font-bold text-slate-700"
            data-testid={`${testIdPrefix}-collapse-all`}
          >
            {t("Collapse All")}
          </button>
        </div>
      </div>

      {visibleFolders.length === 0 ? (
        <div className="p-8 text-center text-slate-500 text-sm" data-testid={`${testIdPrefix}-no-match`}>
          {t("No jobs match")} <span className="font-mono">&quot;{search}&quot;</span>
        </div>
      ) : (
        <ul className="divide-y-2 divide-slate-100">
          {visibleFolders.map((folder) => {
            const open = !!openMap[folder.key];
            return (
              <li key={folder.key}>
                {/* Folder header (clickable) */}
                <button
                  type="button"
                  onClick={() =>
                    setOpenMap((p) => ({ ...p, [folder.key]: !open }))
                  }
                  className="w-full px-4 sm:px-5 py-4 flex items-center gap-3 text-left hover:bg-red-50 transition-colors duration-150"
                  data-testid={`${testIdPrefix}-toggle-${folder.number}`}
                >
                  <span className="flex-shrink-0">
                    {open ? (
                      <ChevronDown className="w-5 h-5 text-red-700" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-slate-500" />
                    )}
                  </span>
                  <span className="flex-shrink-0">
                    {open ? (
                      <FolderOpen className="w-5 h-5 text-red-700" />
                    ) : (
                      <Folder className="w-5 h-5 text-slate-500" />
                    )}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      {folder.number !== "—" && (
                        <span className="inline-flex items-center px-2 py-0.5 bg-slate-800 text-white text-[10px] font-mono uppercase tracking-wider rounded font-bold">
                          #{sanitizeOperatorProjectNumber(folder.number, "Operations support")}
                        </span>
                      )}
                      <span className="font-display text-base sm:text-lg font-bold text-slate-900 truncate">
                        {formatOperatorJobLabel(folder.number, folder.name)}
                      </span>
                    </div>
                    {folder.mostRecent && (
                      <div className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mt-0.5">
                        {t("Last activity:")} {formatDateLong(folder.mostRecent)}
                      </div>
                    )}
                  </div>
                  <span
                    className="inline-flex items-center justify-center min-w-[2.5rem] h-7 px-2 rounded bg-red-700 text-white text-xs font-mono font-bold flex-shrink-0"
                    data-testid={`${testIdPrefix}-count-${folder.number}`}
                  >
                    {folder.items.length}
                  </span>
                </button>

                {/* Folder body — records inside */}
                {open && (
                  <ul
                    className="divide-y divide-slate-100 bg-slate-50/40 border-t border-slate-100"
                    data-testid={`${testIdPrefix}-body-${folder.number}`}
                  >
                    {folder.items.map((it) => (
                      <li key={it.id || JSON.stringify(it)}>{renderItem(it)}</li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
