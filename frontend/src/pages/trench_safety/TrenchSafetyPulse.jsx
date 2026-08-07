// Trench Safety · Phase 8C · Operational Intelligence (Pulse)
// ─────────────────────────────────────────────────────────────────────
// Surfaces the weekly Trench Safety Pulse on the Safety + Admin Hub
// and provides a one-click "View Current Pulse" dialog that renders
// the same HTML email body that leadership receives.
//
// All data comes from /api/trench-safety/pulse/* — no new collection
// reads outside the certified `trench_safety_pulses` history surface.
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Loader2, Activity, Send, History, Eye, Mail,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

const RATING_STYLE = {
  "Excellent":       { bg: "bg-emerald-50",  border: "border-emerald-400", text: "text-emerald-900",  pill: "bg-emerald-600 text-white" },
  "Good":            { bg: "bg-blue-50",     border: "border-blue-400",    text: "text-blue-900",     pill: "bg-blue-600 text-white" },
  "Needs Attention": { bg: "bg-amber-50",    border: "border-amber-400",   text: "text-amber-900",    pill: "bg-amber-600 text-white" },
  "Critical":        { bg: "bg-red-50",      border: "border-red-400",     text: "text-red-900",      pill: "bg-red-700 text-white" },
};

function extractErr(e, fb) {
  return e?.response?.data?.detail || e?.message || fb;
}

export function TrenchSafetyPulseCard({ allowSend = true }) {
  const { t } = useT();
  const [pulse, setPulse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewOpen, setViewOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);

  const refresh = async () => {
    try {
      const r = await api.get("/trench-safety/pulse/current");
      setPulse(r.data || null);
    } catch (e) {
      // swallow — the card will gracefully show empty
    }
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await api.get("/trench-safety/pulse/current");
        if (!cancelled) setPulse(r.data || null);
      } catch { /* swallow */ }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, []);

  async function onGenerate(send) {
    setGenerating(true);
    try {
      const r = await api.post(`/trench-safety/pulse/generate?send=${send ? "true" : "false"}`);
      toast.success(send
        ? `${t("Pulse generated and dispatched")} · ${r.data?.delivery?.recipient_count ?? 0} ${t("recipient(s)")}`
        : t("Pulse generated."));
      await refresh();
    } catch (e) {
      toast.error(extractErr(e, t("Generate failed.")));
    } finally { setGenerating(false); }
  }

  if (loading) {
    return (
      <section className="bg-white border border-slate-200 rounded-md p-4" data-testid="pulse-card-loading">
        <Loader2 className="w-5 h-5 animate-spin text-cyan-700" />
      </section>
    );
  }

  const snap = pulse?.snapshot || {};
  const health = snap.health || {};
  const rating = health.rating || "—";
  const style = RATING_STYLE[rating] || { bg: "bg-slate-50", border: "border-slate-300", text: "text-slate-900", pill: "bg-slate-600 text-white" };
  const score = health.score ?? 0;
  const al = snap.alerts || {};
  const attentionCount = Object.values(al).reduce((acc, v) => acc + (typeof v === "number" && v > 0 ? v : 0), 0);
  const week = pulse?.week_of || snap.week_of || "—";
  const lastGen = pulse?.generated_at || snap.generated_at;
  const delivered = pulse?.delivery?.status === "sent";

  return (
    <section className={`border-2 ${style.border} ${style.bg} rounded-md p-4`} data-testid="pulse-card">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold">
            <Activity className="w-3.5 h-3.5" />
            {t("Trench Safety Pulse")}
          </div>
          <div className="font-display text-xl font-black text-slate-900 mt-1" data-testid="pulse-card-week">
            {t("Week of")} {week}
          </div>
          <div className="text-xs text-slate-600 mt-0.5">
            {t("Last generated")}: <span className="font-mono">{lastGen ? lastGen.slice(0, 16).replace("T", " ") : "—"}</span>
            {delivered && (
              <span className="ml-2 inline-flex items-center gap-1 text-emerald-700 font-bold">
                <Mail className="w-3 h-3" /> {t("Delivered")}
              </span>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-[0.12em] ${style.pill}`} data-testid="pulse-card-rating">
            {t(rating)}
          </div>
          <div className={`font-display text-4xl font-black mt-1 leading-none ${style.text}`} data-testid="pulse-card-score">
            {score}<span className="text-base opacity-60"> / 100</span>
          </div>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="pulse-card-stats">
        <Stat label={t("On Hold")}        value={al.on_hold ?? 0}             testId="pulse-stat-onhold" />
        <Stat label={t("Open Repairs")}   value={al.open_repairs ?? 0}        testId="pulse-stat-repairs" />
        <Stat label={t("Inspections Due")} value={al.inspections_due ?? 0}    testId="pulse-stat-inspdue" />
        <Stat label={t("Recent · 7d")}    value={snap.activity_7d_total ?? 0} testId="pulse-stat-recent" />
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <Button size="sm" variant="outline" onClick={() => setViewOpen(true)} data-testid="pulse-view-btn">
          <Eye className="w-3.5 h-3.5 mr-1" /> {t("View Current Pulse")}
        </Button>
        {allowSend && (
          <>
            <Button size="sm" onClick={() => onGenerate(false)} disabled={generating} className="bg-cyan-700 hover:bg-cyan-800" data-testid="pulse-generate-btn">
              {generating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : (<><Activity className="w-3.5 h-3.5 mr-1" /> {t("Generate Update")}</>)}
            </Button>
            <Button size="sm" onClick={() => onGenerate(true)} disabled={generating} variant="outline" data-testid="pulse-send-btn">
              <Send className="w-3.5 h-3.5 mr-1" /> {t("Generate + Send")}
            </Button>
          </>
        )}
        <Button size="sm" variant="outline" onClick={() => setHistoryOpen(true)} data-testid="pulse-history-btn">
          <History className="w-3.5 h-3.5 mr-1" /> {t("History")}
        </Button>
        <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-mono self-center ml-auto">
          {attentionCount} {t("items requiring attention")}
        </div>
      </div>

      <PulseViewerDialog open={viewOpen} onOpenChange={setViewOpen} pulseId={pulse?.id} liveSnapshot={pulse?.id ? null : snap} />
      <PulseHistoryDialog open={historyOpen} onOpenChange={setHistoryOpen} />
    </section>
  );
}

function Stat({ label, value, testId }) {
  return (
    <div className="bg-white/70 border border-white/40 rounded px-2 py-1" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className="font-display text-xl font-black text-slate-900">{value}</div>
    </div>
  );
}

function PulseViewerDialog({ open, onOpenChange, pulseId, liveSnapshot }) {
  const { t } = useT();
  const [html, setHtml] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        if (pulseId) {
          // We have a saved pulse — fetch its rendered HTML
          const apiBase = process.env.REACT_APP_BACKEND_URL;
          const url = `${apiBase}/api/trench-safety/pulse/${pulseId}/html`;
          const r = await fetch(url, { credentials: "include" });
          const txt = await r.text();
          if (!cancelled) setHtml(txt);
        } else if (liveSnapshot) {
          // No saved pulse yet — generate one (view-only update) to view
          const r = await api.post("/trench-safety/pulse/generate?send=false");
          if (!cancelled) {
            const apiBase = process.env.REACT_APP_BACKEND_URL;
            const url = `${apiBase}/api/trench-safety/pulse/${r.data.id}/html`;
            const rr = await fetch(url, { credentials: "include" });
            setHtml(await rr.text());
          }
        }
      } catch { /* swallow */ }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [open, pulseId, liveSnapshot]);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="pulse-viewer-dialog">
        <DialogHeader><DialogTitle>{t("Trench Safety Pulse")}</DialogTitle></DialogHeader>
        {loading ? (
          <div className="flex items-center gap-2 py-8 text-slate-500">
            <Loader2 className="w-5 h-5 animate-spin" /> {t("Rendering pulse…")}
          </div>
        ) : (
          <iframe
            title="pulse"
            srcDoc={html || "<p>No pulse available.</p>"}
            sandbox=""
            data-testid="pulse-viewer-iframe"
            style={{ width: "100%", height: "60vh", border: "1px solid #e2e8f0", borderRadius: 6 }}
          />
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>{t("Close")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function PulseHistoryDialog({ open, onOpenChange }) {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get("/trench-safety/pulse/history", { params: { limit: 52 } });
        if (!cancelled) setItems(r.data?.items || []);
      } catch { /* swallow */ }
      finally { if (!cancelled) setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [open]);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl" data-testid="pulse-history-dialog">
        <DialogHeader><DialogTitle>{t("Pulse History")}</DialogTitle></DialogHeader>
        {loading ? (
          <div className="flex items-center gap-2 py-8 text-slate-500"><Loader2 className="w-5 h-5 animate-spin" /></div>
        ) : items.length === 0 ? (
          <div className="text-sm text-slate-500" data-testid="pulse-history-empty">
            {t("No pulses generated yet. Press Generate Update to create the first.")}
          </div>
        ) : (
          <ul className="divide-y divide-slate-100 max-h-[60vh] overflow-y-auto">
            {items.map((p) => (
              <li key={p.id} className="py-2 flex items-center justify-between gap-3" data-testid={`pulse-history-row-${p.id}`}>
                <div className="flex-1">
                  <div className="font-bold text-slate-900">{t("Week of")} {p.week_of}</div>
                  <div className="text-xs text-slate-500 font-mono">{p.generated_at?.slice(0,16).replace("T"," ")} · {p.generated_by}</div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-black text-slate-900">{p.score}</div>
                  <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500">{t(p.rating || "—")}</div>
                </div>
                <div className={"text-[10px] uppercase tracking-[0.12em] font-bold px-2 py-0.5 rounded border " + (
                  (p.delivery?.status === "sent")
                    ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                    : "border-slate-300 bg-slate-50 text-slate-600"
                )}>
                  {t(p.delivery?.status || "not_sent")} · {p.delivery?.recipient_count ?? 0}
                </div>
              </li>
            ))}
          </ul>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>{t("Close")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
