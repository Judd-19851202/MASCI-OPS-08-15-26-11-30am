import { useEffect, useState, useCallback } from "react";
import { X, Info, AlertTriangle, AlertOctagon, OctagonAlert, CheckCircle2, Flag } from "lucide-react";
import { API } from "@/lib/api";
import { getDeviceId } from "@/lib/deviceId";
import { useT } from "@/lib/i18n";
import { SEVERITY_META } from "@/lib/hubBannerTemplates";
import { useCaptureMode } from "@/lib/captureMode";

/**
 * BannerStrip — top-of-page operational broadcast strip.
 *
 * iter328 · Banner Governance V2:
 *   • BILINGUAL BROADCAST — every banner renders EN and ES stacked,
 *     regardless of the user's language toggle. These are operational
 *     messages aimed at the entire workforce, not page-localized
 *     content.
 *   • CALM CHROME — left-edge severity stripe + soft fill instead of
 *     full-bleed bright bars. Cultural / holiday banners use a slate
 *     stripe and never visually compete with operational alerts.
 *   • STRICT PRIORITY — banners sort by SEVERITY_META[*].priority
 *     (lower = higher). Cultural is priority 9 and ALWAYS yields to
 *     hurricanes, heat warnings, lightning, stand-downs, etc.
 *   • Hard-gate modal still triggers for `require_ack`; cultural
 *     banners never require_ack by template design.
 *
 * Polling: refetch active banners every 60 seconds.
 */
const SEVERITY_ICON = {
  cultural: Flag,
  info: Info,
  advisory: AlertTriangle,
  warning: AlertOctagon,
  critical: OctagonAlert,
};

export default function BannerStrip() {
  const { lang } = useT();
  const captureMode = useCaptureMode();
  const [banners, setBanners] = useState([]);
  const deviceId = getDeviceId();

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/banners/active?device_id=${encodeURIComponent(deviceId)}`);
      if (!r.ok) return;
      const j = await r.json();
      setBanners(Array.isArray(j?.banners) ? j.banners : []);
    } catch {
      // Network errors are non-fatal — keep whatever we last had.
    }
  }, [deviceId]);

  useEffect(() => {
    load();
    const t = setInterval(load, 60000);
    return () => clearInterval(t);
  }, [load]);

  // iter328 · pick the highest-priority un-dismissed un-acked banner
  // using SEVERITY_META priority (lower = higher). Required-ack
  // banners still win over soft ones at the same severity tier so
  // hurricanes never get buried by an advisory.
  const visible = banners.filter((b) => !b.dismissed && !b.acknowledged);
  const byPriority = [...visible].sort((a, b) => {
    const ap = (SEVERITY_META[a.severity] || {}).priority ?? 99;
    const bp = (SEVERITY_META[b.severity] || {}).priority ?? 99;
    if (ap !== bp) return ap - bp;
    // Same priority — required-ack wins.
    if (a.require_ack !== b.require_ack) return a.require_ack ? -1 : 1;
    return 0;
  });
  const top = byPriority[0];

  // iter347 · `?capture=1` capture-mode hides operational banners so
  // platform clips for the promo film stay clean. The data still polls
  // (so toggling capture off reveals the latest active banner instantly)
  // — we just don't render. Zero footprint when capture mode is off.
  if (captureMode) return null;
  if (!top) return null;

  const meta = SEVERITY_META[top.severity] || SEVERITY_META.advisory;
  const Icon = SEVERITY_ICON[top.severity] || AlertTriangle;
  const titleEn = top.title_en || "";
  const titleEs = top.title_es || titleEn;
  const bodyEn = top.body_en || "";
  const bodyEs = top.body_es || bodyEn;

  // iter328 · BILINGUAL BROADCAST — never collapse to a single language.
  // Single-language banners (titleEs missing/blank/identical to titleEn)
  // fall back to showing only the English line so we don't render an
  // empty ES stub.
  const showBilingual = (esText, enText) => Boolean(esText) && esText !== enText;

  const acknowledge = async () => {
    try {
      await fetch(`${API}/banners/${top.id}/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: deviceId,
          path: typeof window !== "undefined" ? window.location.pathname : null,
          lang,
        }),
      });
      await load();
    } catch {
      /* ignore — next poll will retry */
    }
  };

  const dismiss = async () => {
    try {
      await fetch(`${API}/banners/${top.id}/dismiss`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: deviceId,
          path: typeof window !== "undefined" ? window.location.pathname : null,
          lang,
        }),
      });
      await load();
    } catch {
      /* ignore */
    }
  };

  // ── Hard-gate modal for require_ack banners ───────────────────
  if (top.require_ack) {
    return (
      <div
        className="fixed inset-0 z-[9999] bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 print:hidden"
        data-testid="hub-banner-gate"
        role="alertdialog"
        aria-modal="true"
      >
        <div
          className={`max-w-2xl w-full rounded-md border ${meta.cls_bar} bg-white shadow-2xl ${
            meta.pulse ? "animate-pulse-slow" : ""
          }`}
          data-testid={`hub-banner-${top.severity}`}
        >
          <div className="p-6 sm:p-8">
            <div className="flex items-start gap-4">
              <Icon className="w-9 h-9 sm:w-10 sm:h-10 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="font-mono text-[10px] sm:text-xs uppercase tracking-[0.25em] opacity-75 mb-1">
                  {meta.label}
                </div>
                <h2 className="font-display text-xl sm:text-2xl font-black leading-tight break-words">
                  {titleEn}
                </h2>
                {showBilingual(titleEs, titleEn) && (
                  <h3 className="font-display text-lg sm:text-xl font-bold leading-tight break-words opacity-90 mt-1">
                    {titleEs}
                  </h3>
                )}
                {bodyEn && (
                  <p className="mt-3 text-sm sm:text-base leading-relaxed whitespace-pre-wrap">
                    {bodyEn}
                  </p>
                )}
                {showBilingual(bodyEs, bodyEn) && (
                  <p className="mt-2 text-sm sm:text-base leading-relaxed whitespace-pre-wrap italic opacity-90">
                    {bodyEs}
                  </p>
                )}
              </div>
            </div>

            <button
              onClick={acknowledge}
              className={`mt-6 w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-md font-bold uppercase tracking-wider text-sm ${meta.cls_btn}`}
              data-testid="hub-banner-ack-btn"
            >
              <CheckCircle2 className="w-4 h-4" />
              I Acknowledge · Reconozco
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Soft sticky strip ─────────────────────────────────────────
  return (
    <div
      className={`sticky top-0 z-[80] border-b ${meta.cls_bar} print:hidden`}
      data-testid={`hub-banner-strip-${top.severity}`}
      role="status"
    >
      <div className="max-w-6xl mx-auto px-3 sm:px-4 py-2.5 flex items-start gap-3">
        <Icon className="w-5 h-5 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-mono text-[9px] sm:text-[10px] uppercase tracking-[0.22em] opacity-70 font-bold leading-none mb-1">
            {meta.label}
          </div>
          <div className="text-sm sm:text-base font-bold leading-tight break-words">
            {titleEn}
          </div>
          {showBilingual(titleEs, titleEn) && (
            <div className="text-xs sm:text-sm font-semibold leading-tight break-words opacity-85 mt-0.5">
              {titleEs}
            </div>
          )}
          {bodyEn && (
            <div className="text-xs sm:text-sm opacity-95 leading-snug mt-1 line-clamp-3 sm:line-clamp-none">
              {bodyEn}
            </div>
          )}
          {showBilingual(bodyEs, bodyEn) && (
            <div className="text-xs sm:text-sm opacity-80 italic leading-snug mt-0.5 line-clamp-3 sm:line-clamp-none">
              {bodyEs}
            </div>
          )}
        </div>
        <button
          onClick={dismiss}
          className="shrink-0 inline-flex items-center justify-center w-7 h-7 rounded-full hover:bg-black/10 transition-colors"
          aria-label="Dismiss / Cerrar"
          data-testid="hub-banner-dismiss-btn"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
