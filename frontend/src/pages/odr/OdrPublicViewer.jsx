// OdrPublicViewer.jsx — Phase V.1 · M0.3 · Public ODR Viewer.
//
// Audience: DOT, FAA, CEI, Owners, Consultants.
// NO portal token. NO interior data. NO coaching, NO readiness,
// NO chronology notes, NO completion telemetry.
//
// Doctrine:
//   /app/memory/ODR_PUBLIC_LINK_DEVICE_CONTINUITY_ADDENDUM.md
//   /app/memory/M0_2_CONTINUITY_ENGINE_CERTIFICATION.md
//   /app/memory/M0_2_PDF_ENGINE_CERTIFICATION.md
//
// Resolution path:
//   /odr/public/:doc_id?link=...
//     → GET /api/odr/public/:doc_id?link_id=…
//     → render facts + photos + production + conditions + signature + attachments

import React from "react";
import { useParams, useSearchParams } from "react-router-dom";
import axios from "axios";

const RAW_BACKEND = process.env.REACT_APP_BACKEND_URL || "";
const API = `${RAW_BACKEND.replace(/\/$/, "")}/api`;

async function logPublicObservation(kind, doc_id) {
  // Cannot use portal-token api (this is no-auth). Skip backend log;
  // the GET resolve call already produces a preload_attempt audit row.
  return Promise.resolve({ kind, doc_id });
}

export default function OdrPublicViewer() {
  const { doc_id } = useParams();
  const [params] = useSearchParams();
  const link_id = params.get("link") || params.get("link_id") || "";
  const [data, setData] = React.useState(null);
  const [err, setErr] = React.useState("");

  React.useEffect(() => {
    let live = true;
    setErr(""); setData(null);
    const q = link_id ? `?link_id=${encodeURIComponent(link_id)}` : "";
    axios.get(`${API}/odr/public/${encodeURIComponent(doc_id)}${q}`)
      .then(r => { if (live) setData(r.data); })
      .catch(e => {
        if (live) {
          const detail = e?.response?.data?.detail || e?.message;
          setErr(typeof detail === "string" ? detail : "This record is not available.");
        }
      });
    return () => { live = false; };
  }, [doc_id, link_id]);

  React.useEffect(() => {
    logPublicObservation("public_viewer_opened", doc_id);
  }, [doc_id]);

  if (err) return <Shell><Error message={err} doc_id={doc_id} /></Shell>;
  if (!data) return <Shell><Loading /></Shell>;

  const proj = data.project || {};
  const crew = data.crew_profile || {};

  return (
    <Shell>
      <header className="border-b border-slate-200 pb-4 mb-4" data-testid="public-odr-header">
        <div className="text-[11px] uppercase tracking-widest text-slate-500">
          Operational Daily Record · Official Record
        </div>
        <h1 className="text-2xl font-semibold text-slate-900 mt-1">
          {data.doc_id}
        </h1>
        <div className="text-sm text-slate-600 mt-1">
          {proj.project_number} — {proj.project_name}
        </div>
        <div className="text-xs text-slate-500 mt-1">
          Report Date: <strong>{proj.report_date}</strong>
          {" · "}
          Status: <strong className="capitalize">{data.status}</strong>
        </div>
      </header>

      <Section label="Crew" testid="public-odr-crew">
        <KV k="Crew Name" v={crew.crew_name} />
        <KV k="Crew Type" v={crew.crew_type} />
        <KV k="Primary Operation" v={crew.primary_operation} />
      </Section>

      <Section label="Production" testid="public-odr-production">
        {(data.production_segments || []).length === 0
          ? <Empty label="No production segments recorded." />
          : (data.production_segments || []).map((s, i) => (
              <div key={i} className="border-l-2 border-slate-200 pl-3 mb-3">
                <div className="text-sm font-medium text-slate-800">
                  Segment {i + 1} · {s.crew_type} · {s.primary_operation}
                </div>
                {s.work_area_id && <div className="text-xs text-slate-500">Area: {s.work_area_id}</div>}
              </div>
            ))}
      </Section>

      <Section label="Delays" testid="public-odr-delays">
        {!(data.delays || {}).any_delays
          ? <Empty label="No delays recorded." />
          : (
            <>
              <KV k="Total Hours Lost" v={(data.delays || {}).total_hours_lost ?? 0} />
              {((data.delays || {}).entries || []).map((e, i) => (
                <div key={i} className="mt-2 text-sm text-slate-700">
                  · {e.delay_type} — {e.hours_lost ?? 0}h —{" "}
                  <span className="text-slate-500">{(e.description || {}).text || "—"}</span>
                </div>
              ))}
            </>
          )}
      </Section>

      <Section label="Safety" testid="public-odr-safety">
        {(data.safety || {}).any_event
          ? <KV k="Safety Event" v="Recorded" />
          : <Empty label="No safety events recorded." />}
      </Section>

      <Section label="Weather Impact" testid="public-odr-weather">
        {!(data.weather_impact || {}).weather_impacted_work
          ? <Empty label="No weather impact." />
          : (
            <>
              <KV k="Hours Lost" v={(data.weather_impact || {}).hours_lost ?? "—"} />
              <KV k="Description" v={((data.weather_impact || {}).description || {}).text || "—"} />
            </>
          )}
      </Section>

      <Section label="Signature" testid="public-odr-signature">
        <KV
          k="Foreman Acknowledged"
          v={((data.signature || {}).foreman_acknowledgement || {}).acknowledged ? "Yes" : "No"}
        />
        <KV
          k="Acknowledged At UTC"
          v={((data.signature || {}).foreman_acknowledgement || {}).acknowledged_at_utc || "—"}
        />
        <KV
          k="Statement"
          v={((data.signature || {}).foreman_acknowledgement || {}).text || "—"}
        />
      </Section>

      <footer className="text-[10px] text-slate-400 border-t border-slate-200 pt-3 mt-6">
        Official Record · {data.doc_id} · Operational continuity tracked.
        Document integrity is anchored at the platform — independent verification
        available on request.
      </footer>
    </Shell>
  );
}

function Shell({ children }) {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-5 sm:px-8 py-8 print:py-0" data-testid="public-odr-viewer">
        {children}
      </div>
    </div>
  );
}

function Section({ label, testid, children }) {
  return (
    <section className="mb-5" data-testid={testid}>
      <h2 className="text-[11px] uppercase tracking-widest text-slate-500 mb-1">{label}</h2>
      <div className="text-sm text-slate-800 space-y-0.5">{children}</div>
    </section>
  );
}
function KV({ k, v }) {
  return (
    <div className="flex text-sm">
      <span className="w-44 text-slate-500">{k}</span>
      <span className="flex-1 text-slate-800">{String(v ?? "—")}</span>
    </div>
  );
}
function Empty({ label }) { return <div className="text-sm text-slate-500">{label}</div>; }
function Loading() { return <div className="py-20 text-center text-slate-500">Loading…</div>; }
function Error({ message, doc_id }) {
  return (
    <div className="py-20 text-center">
      <div className="text-sm text-slate-700 font-medium">This record is not available.</div>
      <div className="text-xs text-slate-500 mt-2">
        {doc_id}{message ? ` · ${message}` : ""}
      </div>
    </div>
  );
}
