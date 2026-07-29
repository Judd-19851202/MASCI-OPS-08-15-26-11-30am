import React, { useEffect, useState } from "react";
import { Calculator, Loader2, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

/**
 * CalculatorUsageCard — admin-facing analytic card showing how the
 * /field/calculators Material Calculators page is being used.
 *
 * Backed by `GET /api/admin/calculators/stats`. The CSV export goes to
 * `/api/admin/calculators/export.csv` — we do a token-aware fetch +
 * blob download so the JWT header is actually sent (direct <a href>
 * would miss the X-Admin-Token header and 401).
 */
export default function CalculatorUsageCard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    let mounted = true;
    api
      .get("/admin/calculators/stats")
      .then((r) => mounted && setStats(r.data))
      .catch((e) =>
        mounted &&
        setErr(e?.response?.data?.detail || "Failed to load calculator stats"),
      )
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  async function onExport() {
    setExporting(true);
    try {
      const res = await api.get("/admin/calculators/export.csv", {
        responseType: "blob",
        headers: buildScopedPortalAuthHeaders(["admin"]),
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "masci-calculator-runs.csv";
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-5 sm:p-7 mb-6"
      data-testid="calculator-usage-card"
    >
      <header className="flex items-start gap-3 mb-4">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-amber-600 text-white shrink-0">
          <Calculator className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-800 font-bold">
            Material Calculator Usage
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            Calculator runs
          </h2>
          <p className="text-sm text-slate-600 mt-1.5">
            Every time a field user hits <strong>Save Calculation</strong> on
            Field → Material Calculators, the inputs and results land here.
          </p>
        </div>
        <Button
          onClick={onExport}
          variant="outline"
          disabled={exporting || !stats?.totals?.total}
          className="shrink-0"
          data-testid="calc-export-csv"
        >
          {exporting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Download className="w-4 h-4" />
          )}
          <span className="ml-2">Export CSV</span>
        </Button>
      </header>

      {loading && (
        <div className="flex items-center gap-2 text-slate-500 text-sm py-3">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading…
        </div>
      )}

      {err && (
        <div className="bg-red-50 border border-red-300 text-red-900 text-sm rounded p-3">
          {err}
        </div>
      )}

      {stats && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 mb-4">
            <BigStat label="Total runs" value={stats.totals.total} testid="calc-total" />
            <BigStat label="English" value={stats.totals.en} tone="blue" testid="calc-en" />
            <BigStat label="Spanish" value={stats.totals.es} tone="amber" testid="calc-es" />
            <BigStat
              label="Most used"
              value={stats.most_used?.label || "—"}
              small
              testid="calc-most"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-slate-200 text-left">
                  <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                    Calculator
                  </th>
                  <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 text-right">
                    Total
                  </th>
                  <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-blue-700 text-right">
                    EN
                  </th>
                  <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-amber-700 text-right">
                    ES
                  </th>
                </tr>
              </thead>
              <tbody>
                {stats.by_type.map((row) => (
                  <tr
                    key={row.calculator_type}
                    className="border-b border-slate-100"
                    data-testid={`calc-row-${row.calculator_type}`}
                  >
                    <td className="py-2 pr-3 font-medium text-slate-900">
                      {row.label}
                    </td>
                    <td className="py-2 pr-3 text-right tabular-nums">
                      {row.total}
                    </td>
                    <td className="py-2 pr-3 text-right tabular-nums text-blue-700">
                      {row.en}
                    </td>
                    <td className="py-2 pr-3 text-right tabular-nums text-amber-700 font-bold">
                      {row.es}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {stats.last_used && (
            <p className="text-[11px] text-slate-500 mt-3">
              Last run:{" "}
              <span className="font-mono">
                {formatPlatformTime(stats.last_used.created_at)}
              </span>{" "}
              · {stats.last_used.calculator_type} · {stats.last_used.language.toUpperCase()}
            </p>
          )}
        </>
      )}
    </section>
  );
}

function BigStat({ label, value, tone, testid, small }) {
  const toneMap = {
    slate: "border-slate-300 bg-slate-50 text-slate-900",
    blue: "border-blue-300 bg-blue-50 text-blue-900",
    amber: "border-amber-400 bg-amber-50 text-amber-900",
  };
  return (
    <div
      className={`border-2 rounded px-3 py-3 ${toneMap[tone] || toneMap.slate}`}
      data-testid={testid}
    >
      <div className="font-mono text-[9px] uppercase tracking-[0.25em] opacity-70 font-bold">
        {label}
      </div>
      <div
        className={
          "font-display font-black leading-tight tabular-nums mt-0.5 " +
          (small ? "text-base" : "text-2xl sm:text-3xl")
        }
      >
        {value}
      </div>
    </div>
  );
}
