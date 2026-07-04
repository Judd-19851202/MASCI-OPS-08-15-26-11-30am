import React, { useEffect, useState } from "react";
import { useParams, useSearchParams, useLocation, Link, Navigate } from "react-router-dom";
import { ArrowLeft, Lock, Loader2, AlertCircle, Download } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { TRACKS } from "@/data/training";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { isShop } from "@/lib/shopAuth";

/**
 * TrainingPacketDownload — auth-aware packet downloader.
 *
 * Route: `/training/:track/packet?lang=en|es|bi`
 *
 * For the `field` track we immediately redirect to the public PDF URL
 * (same behavior as scanning the QR straight through).
 *
 * For Shop / PM / Admin tracks we force a login of the correct tier
 * before serving the PDF. Since `<iframe>` and direct `<a href>`
 * downloads can't attach the `X-*-Token` header the API expects, we use
 * `api.get(..., { responseType: 'blob' })` to authenticate the request
 * and trigger a local file download via Blob URL.
 */
export default function TrainingPacketDownload() {
  const { t, lang: uiLang } = useT();
  const { track: trackSlug } = useParams();
  const [params] = useSearchParams();
  const lang = params.get("lang") || "en";
  const location = useLocation();
  const track = TRACKS[trackSlug];

  const [state, setState] = useState("loading"); // loading | done | error
  const [err, setErr] = useState("");

  const requiredAudience = track?.audience;
  const isAuthed = (() => {
    if (!requiredAudience || requiredAudience === "public") return true;
    if (isAdmin()) return true;
    if (requiredAudience === "pm") return isPm();
    if (requiredAudience === "shop") return isShop() || isPm();
    return false;
  })();

  useEffect(() => {
    if (!track) return;
    let cancelled = false;
    (async () => {
      // Field is public → redirect to the PDF URL directly (opens inline).
      if (requiredAudience === "public") {
        const direct = `${process.env.REACT_APP_BACKEND_URL}/api/training/packet.pdf?track=${trackSlug}&lang=${encodeURIComponent(lang)}`;
        window.location.replace(direct);
        return;
      }
      if (!isAuthed) {
        // render the login CTA — don't attempt the download
        setState("login-required");
        return;
      }
      try {
        setState("loading");
        const res = await api.get(`/training/packet.pdf?track=${trackSlug}&lang=${encodeURIComponent(lang)}`, {
          responseType: "blob",
        });
        if (cancelled) return;
        const blob = new Blob([res.data], { type: "application/pdf" });
        const url = URL.createObjectURL(blob);
        // Open in a new tab so mobile users get a native PDF viewer.
        const w = window.open(url, "_blank");
        if (!w) {
          // Popup blocked — fall back to triggering a download.
          const a = document.createElement("a");
          a.href = url;
          a.download = `MASCI_training_${trackSlug}_${lang}.pdf`;
          document.body.appendChild(a);
          a.click();
          a.remove();
        }
        setTimeout(() => URL.revokeObjectURL(url), 60_000);
        setState("done");
      } catch (e) {
        if (cancelled) return;
        const status = e?.response?.status;
        if (status === 401) {
          setState("login-required");
        } else {
          setErr(e?.response?.data?.detail || e?.message || "Download failed");
          setState("error");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
     
  }, [trackSlug, lang]);

  if (!track) return <Navigate to="/training" replace />;

  // Public (field) → we already redirected; show a brief loading frame.
  if (requiredAudience === "public" || state === "loading") {
    return (
      <PageFrame>
        <div className="inline-flex items-center gap-2 text-slate-600">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="font-mono text-xs uppercase tracking-[0.25em]">{t("Opening packet…")}</span>
        </div>
      </PageFrame>
    );
  }

  if (state === "done") {
    return (
      <PageFrame>
        <div className="max-w-md text-center">
          <Download className="w-10 h-10 mx-auto text-emerald-700 mb-3" />
          <h2 className="font-display text-2xl font-black text-slate-900">{t("Your packet is ready")}</h2>
          <p className="text-slate-600 text-sm mt-2">
            {t("If it didn't open in a new tab, your browser may have blocked the pop-up — check your downloads folder.")}
          </p>
          <Link
            to={`/training/${trackSlug}`}
            className="inline-flex items-center justify-center h-11 px-5 mt-5 rounded bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
          >
            {t("Back to track")}
          </Link>
        </div>
      </PageFrame>
    );
  }

  if (state === "error") {
    return (
      <PageFrame>
        <div className="max-w-md text-center">
          <AlertCircle className="w-10 h-10 mx-auto text-red-700 mb-3" />
          <h2 className="font-display text-2xl font-black text-slate-900">{t("Couldn't open the packet")}</h2>
          <p className="text-slate-600 text-sm mt-2">{err}</p>
          <Link
            to={`/training`}
            className="inline-flex items-center justify-center h-11 px-5 mt-5 rounded border-2 border-slate-300 text-slate-700 hover:border-slate-500 font-bold uppercase tracking-wide text-sm"
          >
            {t("Back to Training Hub")}
          </Link>
        </div>
      </PageFrame>
    );
  }

  // login-required
  const loginPath =
    requiredAudience === "admin"
      ? "/admin/login"
      : requiredAudience === "pm"
      ? "/pm/login"
      : "/shop/login";
  const audienceLabel =
    uiLang === "es"
      ? requiredAudience === "admin"
        ? "Administrador"
        : requiredAudience === "pm"
        ? "Gerente de Proyecto"
        : "Taller"
      : requiredAudience === "admin"
      ? "Admin"
      : requiredAudience === "pm"
      ? "Project Manager"
      : "Shop";

  return (
    <PageFrame>
      <div className="max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-amber-100 text-amber-700 mb-3">
          <Lock className="w-7 h-7" />
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-red-700 font-bold">
          {t("Internal training · password required")}
        </div>
        <h2 className="font-display text-2xl sm:text-3xl font-black text-slate-900 mt-2">
          {uiLang === "es" && track.title_es ? track.title_es : track.title}
        </h2>
        <p className="text-slate-600 text-sm mt-3 leading-relaxed">
          {t("This packet covers internal MASCI workflows and is only shared with office staff.")}{" "}
          {uiLang === "es"
            ? `Inicie sesión como ${audienceLabel} para abrirlo.`
            : `Sign in as ${audienceLabel} to open it.`}
        </p>
        <div className="mt-6 flex flex-col gap-2">
          <Link
            to={loginPath}
            state={{ from: location.pathname + location.search }}
            className="inline-flex items-center justify-center h-11 px-5 rounded bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
            data-testid="packet-login-cta"
          >
            {uiLang === "es" ? `Iniciar Sesión · ${audienceLabel}` : `Sign In · ${audienceLabel}`}
          </Link>
          <Link
            to="/training"
            className="inline-flex items-center justify-center h-11 px-5 rounded border-2 border-slate-300 text-slate-700 hover:border-slate-500 font-bold uppercase tracking-wide text-sm"
          >
            {t("Back to Training Hub")}
          </Link>
        </div>
      </div>
    </PageFrame>
  );
}

function PageFrame({ children }) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4 border-red-700">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link to="/training" className="inline-flex items-center text-white hover:text-red-400 text-sm font-bold uppercase tracking-wide">
            <ArrowLeft className="w-4 h-4 mr-1" /> Training
          </Link>
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <LangToggle />
        </div>
      </header>
      <main className="flex-1 flex items-center justify-center px-5 py-14">
        <div className="bg-white border border-slate-200 rounded-md p-8 sm:p-10 w-full max-w-lg flex items-center justify-center">
          {children}
        </div>
      </main>
    </div>
  );
}
