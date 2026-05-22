// AdminReferenceLookup — iter338 · Admin-only canonical reference resolver.
//
// Tiny operational utility. Admin pastes a canonical Ref
// (e.g., "INC-2026-0517-002") and is taken directly to the matching
// detail page. NOT a global search. NOT public. NOT fuzzy. Exact-match
// across the 9 canonical number fields (incidents, daily_reports,
// inspections, equipment_inspections, meetings, jhas,
// safety_equipment_issuances, safety_training_records,
// field_leadership_records) + UUID fallback. Resolves via
// GET /api/admin/lookup?ref=<ID>.

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

export default function AdminReferenceLookup() {
  const { t } = useT();
  const navigate = useNavigate();
  const [ref, setRef] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e?.preventDefault?.();
    const needle = (ref || "").trim();
    if (!needle) return;
    setBusy(true);
    setError("");
    try {
      const r = await api.get("/admin/lookup", { params: { ref: needle } });
      if (r.data?.found && r.data?.path) {
        navigate(r.data.path);
        return;
      }
      setError(`${t("No active record matches Ref")} · ${needle}`);
    } catch (err) {
      setError(t("Lookup unavailable. Try again in a moment."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section
      data-testid="admin-reference-lookup"
      className="bg-white border border-slate-200 border-l-4 border-l-slate-700 rounded-md p-5"
    >
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-md bg-slate-900 text-white flex items-center justify-center shrink-0">
          <Search className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[11px] uppercase tracking-[0.22em] text-slate-500 font-semibold">
            {t("Admin Utility")}
          </div>
          <h2 className="text-base sm:text-lg font-bold text-slate-900 mt-0.5">
            {t("Find Record by Ref")}
          </h2>
          <p className="text-sm text-slate-600 mt-1 max-w-2xl leading-snug">
            {t("Paste a canonical reference to jump straight to the record.")}
          </p>

          <form onSubmit={onSubmit} className="mt-3 flex flex-col sm:flex-row gap-2 max-w-2xl">
            <input
              type="text"
              data-testid="admin-lookup-input"
              value={ref}
              onChange={(e) => { setRef(e.target.value); setError(""); }}
              placeholder={t("Paste Ref · INC-2026-0517-002")}
              autoComplete="off"
              spellCheck={false}
              className="flex-1 font-mono text-sm tracking-wide border border-slate-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
            />
            <button
              type="submit"
              data-testid="admin-lookup-submit"
              disabled={busy || !ref.trim()}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-slate-900 text-white text-sm font-semibold uppercase tracking-[0.14em] hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              {t("Find")}
            </button>
          </form>

          {error ? (
            <div
              data-testid="admin-lookup-error"
              className="mt-3 text-sm font-mono text-slate-700 bg-slate-50 border border-slate-200 rounded px-3 py-2"
            >
              {error}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
