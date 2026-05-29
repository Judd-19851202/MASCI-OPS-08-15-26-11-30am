// OdrCenter.jsx — Phase V.1 · M0.3 · FL ODR Command Center.
//
// Doctrine:
//   /app/memory/FIELD_LEADERSHIP_VISIBILITY_DOCTRINE.md
//   /app/memory/ODR_FINAL_GOVERNANCE_ADDENDUM.md
//   /app/memory/M0_2_AMENDMENT_ENGINE_CERTIFICATION.md
//
// Calm, role-aware, NOT a dashboard. Surfaces seven calm tabs:
//   - Needs Attention (drafts + returned)
//   - Recently Submitted
//   - Recently Amended
//   - Ready for Review
//   - Constraint-Linked
//   - Chronology Events
//   - Readiness Signals
//
// FLL-1 (Foreman) sees own ODRs.
// FLL-2/3/4 (Super tier) sees crew/project/regional scope.
// FLL-5 (PM) hits the dedicated PM panel · not this one.
// FLL-6 (Admin) sees a SUMMARY · this view defaults to "all".

import React from "react";
import { Link } from "react-router-dom";
import { listOdrs, logObservation } from "@/lib/odrApi";
import OdrTrustBanner from "@/components/odr/OdrTrustBanner";

const TABS = [
  { key: "needs", label: "Needs Attention", description: "Drafts and returned records waiting on you." },
  { key: "submitted", label: "Recently Submitted", description: "What the field reported recently." },
  { key: "amended", label: "Recently Amended", description: "Records changed after submission." },
  { key: "review", label: "Ready for Review", description: "Submitted records awaiting your approval." },
  { key: "constraints", label: "Constraint-Linked", description: "ODRs tied to active constraints." },
  { key: "chronology", label: "Chronology", description: "Recent events across your scope." },
  { key: "readiness", label: "Readiness Signals", description: "Records with open hard stops or missing required items." },
];

export default function OdrCenter() {
  const [tab, setTab] = React.useState("needs");
  const [data, setData] = React.useState({ items: [], fll: "", verb: "", count: 0 });
  const [err, setErr] = React.useState("");
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    logObservation({ surface: "fl_center", kind: "fl_inbox_opened" });
  }, []);

  React.useEffect(() => {
    let live = true;
    setLoading(true);
    setErr("");
    const params = tabParams(tab);
    listOdrs(params)
      .then(d => { if (live) { setData(d); setLoading(false); } })
      .catch(e => { if (live) { setErr(e.message); setLoading(false); } });
    return () => { live = false; };
  }, [tab]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6" data-testid="fl-odr-center">
        <header className="mb-4">
          <h1 className="text-2xl font-semibold text-slate-800">Field Leadership · ODR Center</h1>
          <p className="text-xs text-slate-500 mt-1">
            {data.fll || "scope loading"} · {data.verb || "—"} verb
          </p>
        </header>

        <OdrTrustBanner />

        <nav className="mt-4 flex flex-wrap gap-2" data-testid="fl-odr-tabs">
          {TABS.map(t => (
            <button
              key={t.key}
              data-testid={`fl-odr-tab-${t.key}`}
              onClick={() => {
                setTab(t.key);
                logObservation({
                  surface: "fl_center",
                  kind: t.key === "chronology" ? "chronology_opened"
                    : t.key === "readiness" ? "readiness_signal_clicked"
                    : "fl_inbox_opened",
                  context: { tab: t.key },
                });
              }}
              className={`text-xs px-3 py-2 rounded-full border ${
                tab === t.key
                  ? "bg-slate-800 text-white border-slate-800"
                  : "bg-white text-slate-700 border-slate-300 hover:border-slate-400"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <p className="text-xs text-slate-500 mt-3" data-testid="fl-odr-tab-desc">
          {TABS.find(x => x.key === tab)?.description}
        </p>

        <section className="mt-4 bg-white border border-slate-200 rounded-lg" data-testid="fl-odr-list">
          {loading && <Empty label="Loading…" />}
          {!loading && err && <Empty label={err} />}
          {!loading && !err && (data.items || []).length === 0 && (
            <Empty label="Nothing here right now. That's good." />
          )}
          <ul className="divide-y divide-slate-100">
            {(data.items || []).map(o => (
              <li key={o.id} className="px-4 py-3 hover:bg-slate-50" data-testid={`fl-odr-row-${o.doc_id}`}>
                <Link
                  to={`/odr/${encodeURIComponent(o.id)}`}
                  onClick={() => logObservation({
                    surface: "fl_center", kind: "fl_record_opened",
                    odr_id: o.id, doc_id: o.doc_id,
                  })}
                  className="flex items-center justify-between"
                >
                  <div>
                    <div className="text-sm font-medium text-slate-800">{o.doc_id}</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {(o.project || {}).project_number} · {(o.project || {}).report_date}
                      {" · "}
                      <span className="capitalize">{(o.crew_profile || {}).crew_type}</span>
                      {" · "}
                      {(o.crew_profile || {}).crew_name}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full ${
                      o.status === "submitted" ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      : o.status === "draft" ? "bg-slate-50 text-slate-600 border border-slate-200"
                      : "bg-amber-50 text-amber-700 border border-amber-200"
                    }`}>
                      {o.status}
                    </span>
                    {(o.amendment_count || 0) > 0 && (
                      <span className="text-[10px] text-slate-500">
                        +{o.amendment_count} amend
                      </span>
                    )}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}

function tabParams(tab) {
  const now = new Date();
  const dWeekAgo = new Date(now.getTime() - 7 * 86400_000).toISOString().slice(0, 10);
  switch (tab) {
    case "needs": return { status: "draft" };
    case "submitted": return { status: "submitted", report_date_from: dWeekAgo };
    case "amended": return { report_date_from: dWeekAgo };  // we filter amendments downstream
    case "review": return { status: "submitted" };
    case "constraints": return { report_date_from: dWeekAgo };
    case "chronology": return { report_date_from: dWeekAgo };
    case "readiness": return { status: "draft" };
    default: return {};
  }
}

function Empty({ label }) {
  return <div className="px-4 py-10 text-center text-sm text-slate-500" data-testid="fl-odr-empty">{label}</div>;
}
