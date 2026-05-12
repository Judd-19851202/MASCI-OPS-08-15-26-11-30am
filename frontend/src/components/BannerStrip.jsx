import { useEffect, useState, useCallback } from "react";
import { X, Info, AlertTriangle, AlertOctagon, OctagonAlert, CheckCircle2 } from "lucide-react";
import { API } from "@/lib/api";
import { getDeviceId } from "@/lib/deviceId";
import { useT } from "@/lib/i18n";
import { SEVERITY_META } from "@/lib/hubBannerTemplates";

/**
 * BannerStrip — sticky top-of-page strip showing the highest-severity
 * active hub banner. Two display modes:
 *
 *  1. require_ack === false:
 *     Renders as a thin colored strip with title + body + Dismiss
 *     button. Dismissing hides the banner for this device (admin still
 *     sees impression + dismiss count in the audit panel) but the
 *     dismissal does NOT count as an acknowledgment.
 *
 *  2. require_ack === true:
 *     Renders the strip + a full-screen modal that blocks every other
 *     interaction until the user clicks "I acknowledge". This is the
 *     hard gate used for CRITICAL stand-downs and OSHA / Hurricane
 *     situations where MASCI needs proof the crew saw the message.
 *
 * Polling: refetch active banners every 60 seconds so a banner posted
 * mid-shift shows up on field devices without a page reload.
 *
 * Bilingual: each banner has English + Spanish copy generated server-
 * side via Claude. We pick whichever matches the global LangToggle
 * setting via the `useT` hook.
 */
const SEVERITY_ICON = {
  info: Info,
  advisory: AlertTriangle,
  warning: AlertOctagon,
  critical: OctagonAlert,
};

export default function BannerStrip() {
  const { lang } = useT();
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

  // Pick the highest-severity un-dismissed un-acked banner to show as
  // the visible strip. Required-ack banners always win over soft ones.
  const visible = banners.filter((b) => !b.dismissed && !b.acknowledged);
  const requiredAck = visible.find((b) => b.require_ack);
  const softTop = visible.find((b) => !b.require_ack);
  const top = requiredAck || softTop;

  if (!top) return null;

  const meta = SEVERITY_META[top.severity] || SEVERITY_META.advisory;
  const Icon = SEVERITY_ICON[top.severity] || AlertTriangle;
  const title = lang === "es" ? top.title_es || top.title_en : top.title_en;
  const body = lang === "es" ? top.body_es || top.body_en : top.body_en;

  const acknowledge = async () => {
    try {
      await fetch(`${API}/banners/${top.id}/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId }),
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
        body: JSON.stringify({ device_id: deviceId }),
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
          className={`max-w-2xl w-full rounded-lg border-4 ${meta.cls_bar} shadow-2xl ${
            meta.pulse ? "animate-pulse-slow" : ""
          }`}
          data-testid={`hub-banner-${top.severity}`}
        >
          <div className="p-6 sm:p-8">
            <div className="flex items-start gap-4">
              <Icon className="w-10 h-10 sm:w-12 sm:h-12 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="font-mono text-[10px] sm:text-xs uppercase tracking-[0.25em] opacity-75 mb-1">
                  {meta.label}
                </div>
                <h2 className="font-display text-xl sm:text-3xl font-black leading-tight break-words">
                  {title}
                </h2>
                {body && (
                  <p className="mt-3 text-sm sm:text-base leading-relaxed whitespace-pre-wrap">
                    {body}
                  </p>
                )}
              </div>
            </div>

            <button
              onClick={acknowledge}
              className={`mt-6 w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-md font-bold uppercase tracking-wider text-sm border-b-2 border-black/40 ${meta.cls_btn}`}
              data-testid="hub-banner-ack-btn"
            >
              <CheckCircle2 className="w-4 h-4" />
              {lang === "es" ? "RECONOZCO" : "I Acknowledge"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Soft sticky strip ─────────────────────────────────────────
  return (
    <div
      className={`sticky top-0 z-[80] border-b-2 ${meta.cls_bar} print:hidden`}
      data-testid={`hub-banner-strip-${top.severity}`}
      role="status"
    >
      <div className="max-w-6xl mx-auto px-3 sm:px-4 py-2.5 flex items-start gap-3">
        <Icon className="w-5 h-5 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-sm sm:text-base font-bold leading-tight break-words">
            {title}
          </div>
          {body && (
            <div className="text-xs sm:text-sm opacity-95 leading-snug mt-0.5 line-clamp-2 sm:line-clamp-none">
              {body}
            </div>
          )}
        </div>
        <button
          onClick={dismiss}
          className="shrink-0 inline-flex items-center justify-center w-7 h-7 rounded-full hover:bg-black/15 transition-colors"
          aria-label={lang === "es" ? "Cerrar aviso" : "Dismiss banner"}
          data-testid="hub-banner-dismiss-btn"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
