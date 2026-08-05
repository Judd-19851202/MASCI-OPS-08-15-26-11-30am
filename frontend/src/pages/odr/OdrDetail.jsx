// OdrDetail.jsx — Phase V.1 · M0.3 · read-only ODR detail.
//
// Minimal substrate read view used by FL Center and PM Panel deep-link.
// Honors role-aware projection (server already strips fields per FLL).

import React from "react";
import { useParams } from "react-router-dom";
import { getOdr, getVersionChain, pdfUrl, logObservation } from "@/lib/odrApi";
import OdrTrustBanner from "@/components/odr/OdrTrustBanner";
import OdrPageShell from "@/components/odr/OdrPageShell";

export default function OdrDetail() {
  const { id } = useParams();
  const [odr, setOdr] = React.useState(null);
  const [chain, setChain] = React.useState(null);
  const [err, setErr] = React.useState("");

  React.useEffect(() => {
    let live = true;
    Promise.all([getOdr(id), getVersionChain(id).catch(() => null)])
      .then(([o, c]) => { if (live) { setOdr(o); setChain(c); } })
      .catch(e => { if (live) setErr(e.message); });
    return () => { live = false; };
  }, [id]);

  if (err) return <OdrPageShell portalRole="Operations Platform" pageTitle="Daily work record" subtitle="Open the record details and the latest update trail."><div className="p-6 text-rose-700" data-testid="odr-detail-error">{err}</div></OdrPageShell>;
  if (!odr) return <OdrPageShell portalRole="Operations Platform" pageTitle="Daily work record" subtitle="Open the record details and the latest update trail."><div className="p-6 text-slate-500" data-testid="odr-detail-loading">Loading…</div></OdrPageShell>;

  const proj = odr.project || {};
  const crew = odr.crew_profile || {};

  return (
    <OdrPageShell portalRole="Operations Platform" pageTitle="Daily work record" subtitle="See the record details, production, delays, and updates after submission.">
      <div className="max-w-3xl mx-auto px-0 py-6" data-testid="odr-detail-page">
        <header className="mb-3">
          <div className="text-xs text-slate-500">{odr.doc_id} · {odr.status}</div>
          <h1 className="text-xl font-semibold text-slate-800">
            {proj.project_number} — {proj.project_name}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {proj.report_date} · {crew.crew_type} · {crew.crew_name}
          </p>
        </header>

        <OdrTrustBanner />

        <div className="mt-3 flex gap-2 flex-wrap" data-testid="odr-detail-pdf-actions">
          {["foreman", "superintendent", "pm", "executive", "external"].map(a => (
            <a
              key={a}
              href={pdfUrl(id, a)}
              target="_blank"
              rel="noopener noreferrer"
              data-testid={`odr-detail-pdf-${a}`}
              onClick={() => logObservation({
                surface: "fl_center", kind: "pdf_rendered",
                odr_id: id, doc_id: odr.doc_id, context: { audience: a },
              })}
              className="text-[11px] px-3 py-1.5 rounded-full border border-slate-300 text-slate-700 hover:bg-slate-100 capitalize"
            >
              {a} PDF
            </a>
          ))}
        </div>

        <section className="mt-4 bg-white border border-slate-200 rounded-lg p-4">
          <h2 className="text-xs uppercase tracking-wider text-slate-500 mb-2">Production</h2>
          {(odr.production_segments || []).length === 0
            ? <Empty label="No production segments recorded." />
            : (odr.production_segments || []).map((s, i) => (
              <div key={i} className="text-sm text-slate-700">
                · {s.crew_type} — {s.primary_operation}
              </div>
            ))}
        </section>

        <section className="mt-3 bg-white border border-slate-200 rounded-lg p-4">
          <h2 className="text-xs uppercase tracking-wider text-slate-500 mb-2">Delays</h2>
          {(odr.delays || {}).any_delays ? (
            <>
              <div className="text-sm text-slate-700">
                {(odr.delays || {}).total_hours_lost || 0}h lost
              </div>
              {((odr.delays || {}).entries || []).map((e, i) => (
                <div key={i} className="text-xs text-slate-500 mt-1">
                  · {e.delay_type} — {((e.description || {}).text) || "—"}
                </div>
              ))}
            </>
          ) : <Empty label="No delays recorded." />}
        </section>

        <section className="mt-3 bg-white border border-slate-200 rounded-lg p-4" data-testid="odr-detail-amendments">
          <h2 className="text-xs uppercase tracking-wider text-slate-500 mb-2">
            Updates after submission ({chain?.amendment_count ?? 0})
          </h2>
          {!chain || (chain.amendments || []).length === 0
            ? <Empty label="No updates after submission." />
            : (chain.amendments || []).map(a => (
              <div key={a.amendment_id} className="text-xs text-slate-600 border-l-2 border-slate-200 pl-3 py-1">
                <div className="font-medium text-slate-700">{a.field_path}</div>
                <div className="text-[10px] text-slate-400">{a.at_utc} · {a.actor_role}</div>
                <div className="text-slate-600 mt-0.5">{((a.reason || {}).text) || ""}</div>
              </div>
            ))}
        </section>
      </div>
    </OdrPageShell>
  );
}

function Empty({ label }) { return <div className="text-sm text-slate-500">{label}</div>; }
