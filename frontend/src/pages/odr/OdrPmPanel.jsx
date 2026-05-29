// OdrPmPanel.jsx — Phase V.1 · M0.3 · PM Consumption Panel.
//
// PMs are CONSUMERS, not authors. This surface answers:
//   "What project risk exists today?" within seconds.
//
// Hides: crew noise, low-level activity spam, per-foreman attribution,
//        completion telemetry, coaching prompts.
//
// Surfaces: production summary, open blockers (delays + constraints),
//           chronology of submitted ODRs, readiness flags (counts only),
//           contractual exposure (extra work + amendments).
//
// Doctrine:
//   /app/memory/FIELD_LEADERSHIP_VISIBILITY_DOCTRINE.md (FLL-5)
//   /app/memory/M0_2_PDF_ENGINE_CERTIFICATION.md (PM audience)

import React from "react";
import { Link } from "react-router-dom";
import { listOdrs, logObservation, pdfUrl } from "@/lib/odrApi";
import OdrTrustBanner from "@/components/odr/OdrTrustBanner";

export default function OdrPmPanel() {
  const [data, setData] = React.useState({ items: [], fll: "", verb: "" });
  const [err, setErr] = React.useState("");
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    logObservation({ surface: "pm_panel", kind: "pm_panel_opened" });
  }, []);

  React.useEffect(() => {
    let live = true;
    listOdrs({ status: "submitted" })
      .then(d => { if (live) { setData(d); setLoading(false); } })
      .catch(e => { if (live) { setErr(e.message); setLoading(false); } });
    return () => { live = false; };
  }, []);

  // Aggregate metrics PMs care about.
  const metrics = React.useMemo(() => {
    const items = data.items || [];
    let totalHoursLost = 0;
    let openDelays = 0;
    let extraWork = 0;
    let safetyEvents = 0;
    let amendments = 0;
    for (const o of items) {
      const d = o.delays || {};
      totalHoursLost += Number(d.total_hours_lost || 0);
      if (d.any_delays) openDelays += 1;
      const x = o.extra_work || {};
      if (x.any_extra_work) extraWork += 1;
      if ((o.safety || {}).any_event) safetyEvents += 1;
      amendments += Number(o.amendment_count || 0);
    }
    return { totalHoursLost, openDelays, extraWork, safetyEvents, amendments, count: items.length };
  }, [data]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6" data-testid="pm-odr-panel">
        <header className="mb-4">
          <h1 className="text-2xl font-semibold text-slate-800">PM · ODR Consumption</h1>
          <p className="text-xs text-slate-500 mt-1">
            Read-only consumer lens · {data.fll || "—"} / {data.verb || "—"}
          </p>
        </header>

        <OdrTrustBanner />

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-x-6 gap-y-3 mt-4" data-testid="pm-odr-metrics">
          <Metric label="Submitted (7d)" value={metrics.count} />
          <Metric label="Open Delays" value={metrics.openDelays} accent={metrics.openDelays > 0} />
          <Metric label="Hours Lost" value={metrics.totalHoursLost.toFixed(1)} />
          <Metric label="Extra Work" value={metrics.extraWork} accent={metrics.extraWork > 0} />
          <Metric label="Safety Events" value={metrics.safetyEvents} accent={metrics.safetyEvents > 0} />
        </div>

        <section className="mt-6 bg-white border border-slate-200 rounded-lg" data-testid="pm-odr-list">
          <div className="px-4 py-3 border-b border-slate-100 text-xs uppercase tracking-wider text-slate-500">
            Recent Submitted Records
          </div>
          {loading && <Empty label="Loading…" />}
          {!loading && err && <Empty label={err} />}
          {!loading && !err && (data.items || []).length === 0 && (
            <Empty label="No submitted ODRs in scope. Quiet day." />
          )}
          <ul className="divide-y divide-slate-100">
            {(data.items || []).slice(0, 50).map(o => (
              <li key={o.id} className="px-4 py-3 hover:bg-slate-50" data-testid={`pm-odr-row-${o.doc_id}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <Link
                      to={`/odr/${encodeURIComponent(o.id)}`}
                      onClick={() => logObservation({
                        surface: "pm_panel", kind: "pm_project_opened",
                        odr_id: o.id, doc_id: o.doc_id,
                      })}
                      className="text-sm font-medium text-slate-800 hover:underline"
                    >
                      {o.doc_id}
                    </Link>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {(o.project || {}).project_number} · {(o.project || {}).report_date}
                      {" · "}
                      {(o.crew_profile || {}).crew_type}
                      {(o.delays || {}).any_delays && (
                        <span className="ml-2 text-amber-700">· delays</span>
                      )}
                      {(o.safety || {}).any_event && (
                        <span className="ml-2 text-rose-700">· safety</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <a
                      href={pdfUrl(o.id, "pm")}
                      target="_blank"
                      rel="noopener noreferrer"
                      data-testid={`pm-odr-pdf-${o.doc_id}`}
                      onClick={() => logObservation({
                        surface: "pm_panel", kind: "pm_pdf_downloaded",
                        odr_id: o.id, doc_id: o.doc_id,
                        context: { audience: "pm" },
                      })}
                      className="text-[11px] px-2 py-1 rounded border border-slate-300 text-slate-700 hover:bg-slate-100"
                    >
                      PDF
                    </a>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}

function Metric({ label, value, accent = false }) {
  return (
    <div
      data-testid={`pm-metric-${label.toLowerCase().replace(/\s+/g, "-")}`}
      className={`rounded-lg border px-3 py-3 bg-white ${
        accent ? "border-amber-200" : "border-slate-200"
      }`}
    >
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className={`text-xl font-semibold mt-1 ${accent ? "text-amber-700" : "text-slate-800"}`}>
        {value}
      </div>
    </div>
  );
}

function Empty({ label }) {
  return <div className="px-4 py-10 text-center text-sm text-slate-500">{label}</div>;
}
