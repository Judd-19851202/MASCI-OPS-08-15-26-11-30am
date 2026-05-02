import React, { useEffect } from "react";
import { useParams, useLocation, useSearchParams, Link, Navigate } from "react-router-dom";
import { ArrowLeft, Printer, ClipboardCheck, Lock } from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { TRACKS, lessonsForTrack } from "@/data/training";
import { isAdmin } from "@/lib/adminAuth";
import { isPm } from "@/lib/pmAuth";
import { isShop } from "@/lib/shopAuth";

// NOTE: no useT() on this page — the poster itself is intentionally bilingual
// so a single print works for any trailer regardless of which crew shows up.

const ACCENTS = {
  red: { bar: "#B91C1C", chip: "#FEF2F2" },
  amber: { bar: "#D97706", chip: "#FFFBEB" },
  slate: { bar: "#0F172A", chip: "#F1F5F9" },
};

/**
 * Scan-&-Go QR poster — one print-ready 1-page letter poster per training
 * track. Three QR codes (EN, ES, EN+ES) point at the PDF packet so crews
 * can pull any language right from a printed poster in the trailer.
 *
 * Route: `/training/:track/poster` (+ optional `?autoprint=1` for one-click)
 * Public — no auth — so it's safe to print and hand out.
 */
export default function TrainingQrPoster() {
  const { track: trackSlug } = useParams();
  const location = useLocation();
  const [params] = useSearchParams();
  const track = TRACKS[trackSlug];

  useEffect(() => {
    if (params.get("autoprint") === "1") {
      const t = setTimeout(() => window.print(), 700);
      return () => clearTimeout(t);
    }
  }, [params]);

  if (!track) return <Navigate to="/training" replace />;

  // Gate non-public tracks the same way TrainingTrack does. We do NOT
  // redirect; a friendly card is shown so office staff who are logged
  // out know why they can't see the poster.
  const audience = track.audience;
  const allowed =
    audience === "public" ||
    isAdmin() ||
    (audience === "pm" && isPm()) ||
    (audience === "shop" && (isShop() || isPm()));
  if (!allowed) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <div className="caution-stripe" />
        <header className="bg-slate-900 border-b-4 border-red-700">
          <div className="max-w-4xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
            <Link to="/training" className="inline-flex items-center text-white hover:text-red-400 text-sm font-bold uppercase tracking-wide">
              <ArrowLeft className="w-4 h-4 mr-1" /> Training
            </Link>
            <MasciLogo variant="mark" size="md" homeLink="/" />
            <span />
          </div>
        </header>
        <main className="flex-1 flex items-center justify-center px-5 py-14">
          <div className="bg-white border-2 border-slate-300 rounded-md p-8 max-w-md w-full text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-amber-100 text-amber-700 mb-3">
              <Lock className="w-7 h-7" />
            </div>
            <h2 className="font-display text-2xl font-black text-slate-900">Internal poster · password required</h2>
            <p className="text-slate-600 text-sm mt-3">
              This trailer poster is for {audience === "admin" ? "Admin" : audience === "pm" ? "PM" : "Shop"} staff only. Sign in to preview and print.
            </p>
            <div className="mt-5 flex flex-col gap-2">
              <Link
                to={audience === "admin" ? "/admin/login" : audience === "pm" ? "/pm/login" : "/shop/login"}
                state={{ from: location.pathname + location.search }}
                className="inline-flex items-center justify-center h-11 rounded bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              >
                Sign In
              </Link>
              <Link
                to="/training"
                className="inline-flex items-center justify-center h-11 rounded border-2 border-slate-300 text-slate-700 hover:border-slate-500 font-bold uppercase tracking-wide text-sm"
              >
                Back to Training Hub
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const api = process.env.REACT_APP_BACKEND_URL;
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const lessons = lessonsForTrack(trackSlug);
  const accent = ACCENTS[track.accent] || ACCENTS.red;

  // The URL encoded inside each QR. For the PUBLIC `field` track the QR
  // points straight at the PDF endpoint (no auth needed). For gated
  // tracks it points at the frontend packet-download route, which forces
  // a login and then streams the PDF — so a photographed poster can't be
  // used by an outsider to pull internal documents.
  const mkUrl = (lang) =>
    audience === "public"
      ? `${api}/api/training/packet.pdf?track=${trackSlug}&lang=${lang}`
      : `${origin}/training/${trackSlug}/packet?lang=${lang}`;
  const qr = (lang) =>
    `${api}/api/qr.svg?scale=9&data=${encodeURIComponent(mkUrl(lang))}`;

  return (
    <>
      {/* Screen chrome — hidden on print. Lets an admin preview + print. */}
      <div className="min-h-screen bg-slate-50 print:hidden">
        <div className="caution-stripe" />
        <header className="bg-slate-900 border-b-4 border-red-700">
          <div className="max-w-4xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
            <Link
              to="/training"
              state={location.state}
              className="inline-flex items-center text-white hover:text-red-400 text-sm font-bold uppercase tracking-wide"
              data-testid="qr-poster-back"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> Training
            </Link>
            <MasciLogo variant="mark" size="md" homeLink="/" />
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-red-700 hover:bg-red-800 text-white font-bold uppercase text-xs tracking-wide border-b-2 border-red-900"
              data-testid="qr-poster-print"
            >
              <Printer className="w-3.5 h-3.5" /> Print Poster
            </button>
          </div>
        </header>
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-5 text-xs text-slate-500 font-mono uppercase tracking-[0.2em]">
          Scan-&-Go QR Poster · {trackSlug} · preview — click Print to output a single letter-size page
        </div>
      </div>

      {/* Poster body — identical to what prints. Single letter-size page. */}
      <div className="qr-poster-page print:block">
        <div className="qr-poster" data-testid={`qr-poster-${trackSlug}`}>
          {/* Top accent bar */}
          <div className="qp-bar" style={{ background: accent.bar }} />

          {/* Header */}
          <header className="qp-hdr">
            <div>
              <div className="qp-eyebrow" style={{ color: accent.bar }}>
                MASCI Training · Scan-&-Go
              </div>
              <h1 className="qp-title">
                {track.title}
                <br />
                <span className="qp-title-es" style={{ color: accent.bar }}>
                  {track.title_es}
                </span>
              </h1>
            </div>
            <MasciLogo variant="mark" size="lg" className="qp-logo" />
          </header>

          <p className="qp-blurb">
            <strong>EN:</strong> Scan any code below to get the full training
            packet on your phone. No login, no app to install.
            <br />
            <strong>ES:</strong> Escanee cualquier código para obtener el
            paquete completo de capacitación en su teléfono. Sin inicio de
            sesión, sin aplicación que instalar.
          </p>

          {/* 3 QR tiles */}
          <div className="qp-grid">
            <QrTile
              label="English"
              flag="EN"
              sub={`${lessons.length} lessons · printable`}
              qrSrc={qr("en")}
              color={accent.bar}
            />
            <QrTile
              label="Español"
              flag="ES"
              sub={`${lessons.length} lecciones · imprimible`}
              qrSrc={qr("es")}
              color={accent.bar}
              highlight
            />
            <QrTile
              label="Bilingual · Bilingüe"
              flag="EN+ES"
              sub="Side-by-side · lado a lado"
              qrSrc={qr("bi")}
              color={accent.bar}
            />
          </div>

          {/* Direct URL fallback */}
          <div className="qp-fallback">
            <div className="qp-fallback-l">
              Direct URL · URL directa
            </div>
            <div className="qp-fallback-url">
              {origin}/training/{trackSlug}
            </div>
          </div>

          {/* Footer */}
          <footer className="qp-foot">
            <div>
              <strong>ACCOUNTABILITY · ADAPT · OVERCOME</strong>
              <br />
              {track.blurb}
            </div>
            <div style={{ textAlign: "right" }}>
              <strong>RESPONSABILIDAD · ADAPTACIÓN · SUPERACIÓN</strong>
              <br />
              {track.blurb_es}
            </div>
          </footer>
          <div className="qp-legal">
            © {new Date().getFullYear()} MASCI · Powered by The Judd Group LLC · Post inside
            every site trailer / Pegue dentro de cada tráiler
          </div>
        </div>
      </div>

      {/* Inline print CSS — kept local to this component so it doesn't leak
          into the rest of the app. */}
      <style>{`
        .qr-poster-page { padding: 24px; display: flex; justify-content: center; }
        .qr-poster {
          width: 8.5in; min-height: 11in; background: white; color: #0F172A;
          font-family: 'Helvetica Neue', Arial, sans-serif;
          padding: 0.5in 0.55in 0.45in 0.55in; box-sizing: border-box;
          border: 1px solid #CBD5E1;
          display: flex; flex-direction: column; position: relative;
        }
        .qp-bar { position: absolute; top: 0; left: 0; right: 0; height: 12pt; }
        .qp-hdr { display: flex; justify-content: space-between; align-items: flex-start; gap: 14pt; margin-top: 14pt; }
        .qp-eyebrow { font-family: 'Courier New', monospace; font-size: 9pt; letter-spacing: 3pt; font-weight: 800; text-transform: uppercase; }
        .qp-title { font-size: 26pt; font-weight: 900; letter-spacing: -0.5pt; line-height: 1.08; margin: 4pt 0 0 0; }
        .qp-title-es { font-size: 20pt; font-weight: 700; }
        .qp-logo { width: 80pt !important; height: auto !important; }
        .qp-blurb { font-size: 10pt; line-height: 1.45; margin: 14pt 0 18pt 0; color: #334155; border-top: 1pt solid #E2E8F0; border-bottom: 1pt solid #E2E8F0; padding: 10pt 0; }
        .qp-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14pt; flex: 1; align-items: stretch; }
        .qp-tile { border: 2pt solid #0F172A; padding: 14pt 10pt; display: flex; flex-direction: column; align-items: center; text-align: center; border-radius: 3pt; }
        .qp-tile.hi { background: #FEF3C7; border-color: #D97706; }
        .qp-tile .qp-flag { font-family: 'Courier New', monospace; font-size: 11pt; letter-spacing: 3pt; font-weight: 900; color: white; background: #0F172A; padding: 4pt 10pt; border-radius: 2pt; }
        .qp-tile.hi .qp-flag { background: #D97706; }
        .qp-tile .qp-label { font-size: 15pt; font-weight: 900; margin-top: 8pt; }
        .qp-tile img, .qp-tile .qp-qr { width: 100%; max-width: 180pt; aspect-ratio: 1/1; margin: 10pt 0; }
        .qp-tile .qp-sub { font-size: 8pt; color: #64748B; font-family: 'Courier New', monospace; letter-spacing: 1pt; text-transform: uppercase; margin-top: 4pt; }
        .qp-fallback { margin-top: 12pt; padding: 8pt 10pt; background: #F1F5F9; border-left: 3pt solid #64748B; font-size: 9pt; }
        .qp-fallback-l { font-family: 'Courier New', monospace; font-size: 7.5pt; letter-spacing: 2pt; color: #64748B; font-weight: 800; text-transform: uppercase; margin-bottom: 2pt; }
        .qp-fallback-url { font-family: 'Courier New', monospace; font-weight: 700; color: #0F172A; }
        .qp-foot { display: flex; justify-content: space-between; gap: 16pt; margin-top: 14pt; border-top: 2pt solid #0F172A; padding-top: 10pt; font-size: 8.5pt; color: #334155; line-height: 1.35; }
        .qp-legal { margin-top: 8pt; text-align: center; font-size: 7.5pt; color: #64748B; font-family: 'Courier New', monospace; letter-spacing: 1pt; text-transform: uppercase; }

        @media print {
          @page { size: letter; margin: 0; }
          html, body { margin: 0; padding: 0; background: white; }
          body > *:not(.qr-poster-page) { display: none !important; }
          .qr-poster-page { padding: 0; }
          .qr-poster { border: none; width: 100%; min-height: auto; page-break-after: avoid; }
        }
      `}</style>
    </>
  );
}

function QrTile({ label, flag, sub, qrSrc, color, highlight }) {
  return (
    <div className={`qp-tile ${highlight ? "hi" : ""}`} style={highlight ? { borderColor: color } : {}}>
      <div className="qp-flag" style={highlight ? { background: color } : {}}>
        {flag}
      </div>
      <div className="qp-label">{label}</div>
      {/* Image tag loads the SVG QR from the backend. Use <img> so the
          print renderer handles it like any other asset. */}
      <img src={qrSrc} alt={`${label} QR`} className="qp-qr" />
      <div className="qp-sub">{sub}</div>
      <div style={{ marginTop: 6, fontSize: 7, color: "#94A3B8", display: "flex", alignItems: "center", gap: 4 }}>
        <ClipboardCheck style={{ width: 9, height: 9 }} />
        mascidocs.com
      </div>
    </div>
  );
}
