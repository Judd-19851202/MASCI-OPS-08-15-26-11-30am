import React, { useEffect, useState } from "react";
import { Languages, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

/**
 * BilingualAdoptionCard — admin-facing analytic card that surfaces how
 * many records were originally filed in Spanish vs English across the
 * five field-facing submission types.
 *
 * Backed by `GET /api/admin/submit-language-stats` which counts the
 * `submit_language` field stamped onto every record by the submit flow
 * in `lib/translateOnSubmit.js`. Legacy records (filed before we started
 * stamping the language) appear as "unknown" — rendered faded to keep
 * the happy-path read clean.
 */
export default function BilingualAdoptionCard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let mounted = true;
    api
      .get("/admin/submit-language-stats")
      .then((r) => {
        if (mounted) setStats(r.data);
      })
      .catch((e) =>
        mounted &&
        setErr(e?.response?.data?.detail || "Failed to load language stats"),
      )
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-5 sm:p-7 mb-6"
      data-testid="bilingual-adoption-card"
    >
      <header className="flex items-start gap-3 mb-4">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-md bg-amber-500 text-white shrink-0">
          <Languages className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-amber-800 font-bold">
            Bilingual Adoption
          </div>
          <h2 className="font-display text-xl sm:text-2xl font-black text-slate-900 leading-none mt-1">
            Records filed in Spanish
          </h2>
          <p className="text-sm text-slate-600 mt-1.5">
            Counts of every field submission stamped with the language the
            crew member used at submit time. Spanish entries are
            auto-translated to English for the record itself — this card is
            the only view of the original language.
          </p>
        </div>
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
            <BigStat
              label="Total"
              value={stats.totals.total}
              tone="slate"
              testid="bilingual-total"
            />
            <BigStat
              label="English"
              value={stats.totals.en}
              tone="blue"
              testid="bilingual-en"
            />
            <BigStat
              label="Spanish"
              value={stats.totals.es}
              tone="amber"
              testid="bilingual-es"
            />
            <BigStat
              label="Spanish %"
              value={`${stats.totals.es_pct}%`}
              tone="amber"
              testid="bilingual-es-pct"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-slate-200 text-left">
                  <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                    Form
                  </th>
                  <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 text-right">
                    Total
                  </th>
                  <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 text-right">
                    EN
                  </th>
                  <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 text-right">
                    ES
                  </th>
                  <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-amber-700 text-right">
                    ES %
                  </th>
                  <th className="py-2 pr-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-400 text-right">
                    Legacy
                  </th>
                </tr>
              </thead>
              <tbody>
                {stats.by_collection.map((row) => (
                  <tr
                    key={row.collection}
                    className="border-b border-slate-100"
                    data-testid={`bilingual-row-${row.collection}`}
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
                    <td className="py-2 pr-3 text-right tabular-nums text-amber-700 font-bold">
                      {row.es_pct}%
                    </td>
                    <td className="py-2 pr-3 text-right tabular-nums text-slate-400">
                      {row.unknown}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {stats.totals.unknown > 0 && (
            <p className="text-[11px] text-slate-400 mt-3 italic">
              "Legacy" = records filed before the language stamp was added
              (ignored in the Spanish % calculation).
            </p>
          )}
        </>
      )}
    </section>
  );
}

function BigStat({ label, value, tone, testid }) {
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
      <div className="font-display text-2xl sm:text-3xl font-black leading-tight tabular-nums mt-0.5">
        {value}
      </div>
    </div>
  );
}
