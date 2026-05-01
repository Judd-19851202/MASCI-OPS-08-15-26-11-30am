import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { TrendingUp, TrendingDown, Minus, GraduationCap, ExternalLink } from "lucide-react";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";

/**
 * Training Scan Stats Stripe — compact panel for the PM Hub & Admin Hub.
 * Pulls /api/admin/training/stats (accepts Admin or PM token) and shows:
 *   - This-week total + week-over-week delta
 *   - Per-track bars (Field / Shop / PM / Admin)
 *   - Per-language chips (EN / ES / EN+ES)
 *   - 14-day sparkline of daily scans
 *
 * Zero PII — the backend only logs track/lang/date/device-family/source.
 */
const TRACK_LABELS = {
  field: { en: "Field", es: "Campo", color: "bg-amber-500" },
  shop: { en: "Shop", es: "Taller", color: "bg-slate-700" },
  pm: { en: "PM", es: "Gerente", color: "bg-amber-600" },
  admin: { en: "Admin", es: "Admin", color: "bg-red-700" },
};

const LANG_LABELS = {
  en: { label: "EN", color: "bg-slate-900" },
  es: { label: "ES", color: "bg-amber-600" },
  bi: { label: "EN+ES", color: "bg-red-700" },
};

export default function TrainingStatsStripe() {
  const { t, lang } = useT();
  const [stats, setStats] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await api.get("/admin/training/stats");
        if (mounted) setStats(res?.data || null);
      } catch (e) {
        if (mounted) setErr(e?.response?.status || "error");
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  if (err || !stats) {
    return null; // silent fail — no stripe is better than a broken one
  }

  const thisWeek = stats.this_week || 0;
  const lastWeek = stats.last_week || 0;
  const delta = thisWeek - lastWeek;
  const deltaPct = lastWeek > 0 ? Math.round((delta / lastWeek) * 100) : null;
  const TrendIcon = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus;
  const trendClass = delta > 0 ? "text-emerald-700" : delta < 0 ? "text-red-700" : "text-slate-500";

  const byTrack = stats.by_track || {};
  const byLang = stats.by_lang || {};
  const trend = stats.trend || [];
  const maxTrend = Math.max(1, ...trend.map((d) => d.n));

  // Build the full 14-day window so missing days show as zero bars.
  const days = [];
  const today = new Date();
  for (let i = 13; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    const hit = trend.find((x) => x.date === key);
    days.push({ key, n: hit ? hit.n : 0 });
  }

  const maxTrackVal = Math.max(1, ...Object.values(byTrack));
  const tracks = ["field", "shop", "pm", "admin"];

  return (
    <section
      className="bg-white border-2 border-slate-300 rounded-md p-5 sm:p-6 mb-6"
      data-testid="training-stats-stripe"
    >
      <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-red-700 text-white shrink-0">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
              {t("Training scans · last 7 days")}
            </div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900" data-testid="stats-this-week">
                {thisWeek}
              </span>
              <span className={`inline-flex items-center gap-1 text-xs font-mono font-bold uppercase tracking-[0.15em] ${trendClass}`}>
                <TrendIcon className="w-3.5 h-3.5" />
                {delta > 0 ? "+" : ""}{delta}
                {deltaPct !== null && ` (${deltaPct > 0 ? "+" : ""}${deltaPct}%)`}
              </span>
              <span className="text-xs text-slate-500 font-mono uppercase tracking-[0.15em]">
                {t("vs prior week")}
              </span>
            </div>
          </div>
        </div>
        <Link
          to="/training"
          className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] font-bold text-slate-700 hover:text-red-700"
          data-testid="stats-open-hub"
        >
          <ExternalLink className="w-3.5 h-3.5" /> {t("Training Hub")}
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Per-track bars */}
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-slate-500 font-bold mb-2">
            {t("By track")}
          </div>
          <div className="space-y-1.5">
            {tracks.map((tr) => {
              const n = byTrack[tr] || 0;
              const pct = (n / maxTrackVal) * 100;
              const label = TRACK_LABELS[tr]?.[lang] || TRACK_LABELS[tr]?.en || tr;
              return (
                <div key={tr} className="flex items-center gap-2 text-xs" data-testid={`stats-track-${tr}`}>
                  <span className="w-14 font-bold text-slate-800 shrink-0">{label}</span>
                  <div className="flex-1 h-4 bg-slate-100 rounded overflow-hidden">
                    <div
                      className={`h-full ${TRACK_LABELS[tr]?.color || "bg-slate-600"} transition-all duration-300`}
                      style={{ width: `${Math.max(pct, n > 0 ? 4 : 0)}%` }}
                    />
                  </div>
                  <span className="w-6 text-right font-mono font-bold text-slate-700 shrink-0">{n}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Per-language chips */}
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-slate-500 font-bold mb-2">
            {t("By language")}
          </div>
          <div className="flex flex-wrap gap-2">
            {["en", "es", "bi"].map((lk) => {
              const n = byLang[lk] || 0;
              const meta = LANG_LABELS[lk];
              return (
                <div
                  key={lk}
                  className={`flex items-center gap-2 px-3 py-2 rounded ${meta.color} text-white`}
                  data-testid={`stats-lang-${lk}`}
                >
                  <span className="font-mono text-xs font-bold tracking-wide">{meta.label}</span>
                  <span className="font-display text-xl font-black leading-none">{n}</span>
                </div>
              );
            })}
          </div>
          <div className="mt-3 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500">
            {t("All-time total")}: <span className="font-bold text-slate-800">{stats.total || 0}</span>
          </div>
        </div>

        {/* 14-day sparkline */}
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-slate-500 font-bold mb-2">
            {t("14-day trend")}
          </div>
          <div className="flex items-end gap-0.5 h-16" data-testid="stats-trend-bars">
            {days.map((d, i) => {
              const h = d.n > 0 ? Math.max(6, (d.n / Math.max(maxTrend, 1)) * 100) : 2;
              return (
                <div
                  key={d.key}
                  className={`flex-1 rounded-t-sm transition-colors ${d.n > 0 ? "bg-red-700" : "bg-slate-200"}`}
                  style={{ height: `${h}%` }}
                  title={`${d.key}: ${d.n}`}
                />
              );
            })}
          </div>
          <div className="mt-1 flex items-center justify-between text-[9px] font-mono uppercase tracking-[0.15em] text-slate-500">
            <span>{days[0].key.slice(5)}</span>
            <span>{t("today")}</span>
          </div>
        </div>
      </div>
    </section>
  );
}
