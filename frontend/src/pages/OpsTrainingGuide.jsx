// OpsTrainingGuide — Iter134. Single guide viewer + PDF download.
// Renders the structured sections with a minimal markdown subset that
// matches the backend renderer (**bold**, *italic*, `code`).
import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import {
  ArrowLeft, Home, BookOpen, FileDown, Loader2, GraduationCap,
  Lightbulb, AlertTriangle, ChevronLeft, Printer,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Tiny markdown subset matching the backend
function renderInline(text) {
  if (!text) return null;
  // Escape HTML, then replace markers — done with React nodes to be safe
  const parts = [];
  let remaining = text;
  let key = 0;
  while (remaining.length > 0) {
    const matches = [
      { re: /\*\*(.+?)\*\*/, tag: "strong" },
      { re: /\*(.+?)\*/,     tag: "em" },
      { re: /`(.+?)`/,       tag: "code" },
    ];
    let earliest = null;
    matches.forEach((m) => {
      const r = remaining.match(m.re);
      if (r && (earliest === null || r.index < earliest.idx)) {
        earliest = { idx: r.index, len: r[0].length, text: r[1], tag: m.tag };
      }
    });
    if (!earliest) {
      parts.push(remaining);
      break;
    }
    if (earliest.idx > 0) parts.push(remaining.slice(0, earliest.idx));
    const Tag = earliest.tag;
    if (Tag === "code") {
      parts.push(<code key={`c-${key++}`} className="bg-slate-100 px-1.5 py-0.5 rounded text-[0.9em] font-mono">{earliest.text}</code>);
    } else if (Tag === "strong") {
      parts.push(<strong key={`s-${key++}`}>{earliest.text}</strong>);
    } else {
      parts.push(<em key={`e-${key++}`}>{earliest.text}</em>);
    }
    remaining = remaining.slice(earliest.idx + earliest.len);
  }
  return parts;
}

function renderBody(md) {
  if (!md) return null;
  const paragraphs = md.split(/\n\s*\n/).filter((p) => p.trim());
  return paragraphs.map((p, i) => (
    <p key={i} className="text-slate-700 leading-relaxed mb-3">
      {p.split("\n").map((line, j) => (
        <React.Fragment key={j}>
          {j > 0 && <br />}
          {renderInline(line)}
        </React.Fragment>
      ))}
    </p>
  ));
}

function HeaderBar() {
  const nav = useNavigate();
  return (
    <header className="bg-slate-900 border-b-4 border-indigo-600">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-4 flex items-center gap-3 flex-wrap">
        <Link to="/" className="inline-flex items-center text-white hover:text-indigo-300 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="ops-training-nav-home">
          <Home className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Home</span>
        </Link>
        <button onClick={() => nav(-1)} className="inline-flex items-center text-white hover:text-indigo-300 text-xs sm:text-sm font-bold uppercase tracking-wide" data-testid="ops-training-nav-back">
          <ArrowLeft className="w-4 h-4 sm:mr-1" /><span className="hidden sm:inline">Back</span>
        </button>
        <MasciLogo variant="mark" size="xl" className="hidden sm:block" homeLink="/" />
        <MasciLogo variant="mark" size="md" className="sm:hidden" homeLink="/" />
        <div className="flex-1" />
        <LangToggle />
      </div>
    </header>
  );
}

export default function OpsTrainingGuide() {
  const { t } = useT();
  const { slug } = useParams();
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        const r = await axios.get(`${API}/training-center/guide/${slug}`);
        if (alive) setGuide(r.data);
      } catch (err) {
        if (alive) {
          toast.error(err?.response?.data?.detail || "Guide not found");
        }
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [slug]);

  const downloadPdf = async () => {
    setDownloading(true);
    try {
      const r = await axios.get(`${API}/training-center/guide/${slug}/pdf`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([r.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `${slug}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      toast.error("PDF download failed");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="min-h-screen blueprint-bg pb-16">
      <div className="caution-stripe" />
      <HeaderBar />

      <div className="max-w-4xl mx-auto px-5 sm:px-8 py-6">
        <Link
          to="/ops-training"
          className="inline-flex items-center text-xs font-bold uppercase tracking-[0.15em] text-indigo-700 hover:text-indigo-900 mb-4"
          data-testid="ops-training-guide-back"
        >
          <ChevronLeft className="w-4 h-4 mr-1" /> {t("All Guides")}
        </Link>

        {loading ? (
          <div className="text-center py-16 text-slate-500 bg-white border border-slate-200 rounded-md">
            <Loader2 className="w-7 h-7 animate-spin mx-auto" /> {t("Loading…")}
          </div>
        ) : !guide ? (
          <div className="text-center py-16 text-slate-500 bg-white border-2 border-dashed border-slate-300 rounded-md">
            {t("Guide not found.")}
          </div>
        ) : (
          <article className="bg-white border border-slate-200 rounded-md p-6 sm:p-8" data-testid="ops-training-guide-article">
            <div className="flex items-start gap-3 mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-indigo-700 text-white shrink-0">
                <GraduationCap className="w-6 h-6" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
                  {guide.kicker}
                </div>
                <h1 className="font-display text-2xl sm:text-3xl font-black text-slate-900 tracking-tight leading-tight">
                  {guide.title}
                </h1>
              </div>
              <Button
                onClick={downloadPdf}
                disabled={downloading}
                className="bg-slate-900 hover:bg-indigo-700 text-white border-b-2 border-black font-bold uppercase tracking-wide h-9 shrink-0"
                data-testid="ops-training-guide-pdf"
              >
                {downloading
                  ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> {t("Building…")}</>
                  : <><FileDown className="w-4 h-4 mr-2" /> PDF</>}
              </Button>
            </div>

            {guide.summary && (
              <p className="text-sm text-slate-600 italic leading-relaxed border-l-4 border-indigo-200 pl-3 mb-4">
                {guide.summary}
              </p>
            )}

            <div className="text-xs text-slate-500 font-mono uppercase tracking-wider mb-6 border-b border-slate-200 pb-3">
              <span>Audience: <strong className="text-slate-700 normal-case font-sans">{guide.audience || "—"}</strong></span>
              <span className="mx-3 text-slate-300">·</span>
              <span>v{guide.version || "1.0"}</span>
              {guide.updated_at && (
                <>
                  <span className="mx-3 text-slate-300">·</span>
                  <span>Updated {String(guide.updated_at).slice(0, 10)}</span>
                </>
              )}
            </div>

            {(guide.sections || []).map((s, i) => (
              <section key={i} className="mb-6">
                <h2 className="font-display text-lg sm:text-xl font-black text-slate-900 mb-2 border-b-2 border-slate-200 pb-1">
                  {s.heading}
                </h2>
                <div className="text-sm">
                  {renderBody(s.body_md)}
                </div>
                {(s.callouts || []).map((c, j) => {
                  const isWarn = (c.kind || "").toLowerCase() === "warn";
                  const Icon = isWarn ? AlertTriangle : Lightbulb;
                  const cls = isWarn
                    ? "bg-amber-50 border-amber-400 text-amber-900"
                    : "bg-cyan-50 border-cyan-400 text-cyan-900";
                  return (
                    <div key={j} className={`mt-3 border-l-4 ${cls} rounded-r p-3 text-sm flex gap-2 items-start`}>
                      <Icon className="w-4 h-4 mt-0.5 shrink-0" />
                      <div>
                        <strong className="uppercase text-[10px] tracking-wider mr-1">{(c.kind || "tip").toUpperCase()}:</strong>
                        {renderInline(c.text || "")}
                      </div>
                    </div>
                  );
                })}
              </section>
            ))}

            <div className="mt-8 pt-5 border-t-2 border-slate-200 flex items-center justify-between gap-2 flex-wrap">
              <Link
                to="/ops-training"
                className="inline-flex items-center text-xs font-bold uppercase tracking-[0.15em] text-indigo-700 hover:text-indigo-900"
                data-testid="ops-training-guide-back-bottom"
              >
                <ChevronLeft className="w-4 h-4 mr-1" /> {t("More Guides")}
              </Link>
              <Button
                onClick={downloadPdf}
                disabled={downloading}
                variant="outline"
                className="border-2 border-slate-300 font-bold uppercase tracking-wide h-9"
                data-testid="ops-training-guide-pdf-bottom"
              >
                <Printer className="w-4 h-4 mr-2" /> {t("Download as PDF")}
              </Button>
            </div>
          </article>
        )}
      </div>
    </div>
  );
}
