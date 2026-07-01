// Track 19.16 · Phase E · Incident Report Viewer.
// Read-only print-friendly renderer for the 9 report packages.
// Consumes GET /api/incident-cases/:caseId/reports/:reportType.
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { useT } from "@/lib/i18n";
import {
  Printer, FileDown, Share2, ArrowLeft, ShieldCheck, Clock,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function _headers() {
  const h = { "Content-Type": "application/json" };
  try {
    const s = localStorage.getItem("safety_token");
    const a = localStorage.getItem("admin_token");
    const p = localStorage.getItem("pm_token");
    if (s) h["X-Safety-Token"] = s;
    if (a) h["X-Admin-Token"] = a;
    if (p) h["X-PM-Token"] = p;
  } catch (_err) { /* ignore */ }
  return h;
}
const cli = () => axios.create({ baseURL: API, headers: _headers(), timeout: 25000 });

const KV = ({ label, value, testId }) => (
  <div className="text-sm" data-testid={testId}>
    <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
      {label}
    </div>
    <div className="text-slate-900 mt-0.5">{value ?? "—"}</div>
  </div>
);

const SlaBadge = ({ status }) => {
  const s = String(status || "NONE").toUpperCase();
  const tones = {
    ON_PACE: "bg-emerald-100 text-emerald-900 border-emerald-300",
    WATCH: "bg-amber-100 text-amber-900 border-amber-300",
    BEHIND: "bg-orange-100 text-orange-900 border-orange-400",
    MISSED: "bg-red-100 text-red-900 border-red-500",
    NONE: "bg-slate-100 text-slate-700 border-slate-300",
  };
  return (
    <span
      className={`inline-block border rounded-full px-3 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] ${tones[s] || tones.NONE}`}
      data-testid="report-viewer-sla-badge"
    >SLA {s}</span>
  );
};

const Table = ({ head, rows, empty, testId }) => {
  if (!rows || rows.length === 0) {
    return <div className="text-sm italic text-slate-400 my-2">{empty}</div>;
  }
  return (
    <table className="w-full text-sm border-collapse my-2" data-testid={testId}>
      <thead>
        <tr>
          {head.map((h) => (
            <th key={h}
                className="bg-slate-900 text-slate-50 text-[10px] font-semibold uppercase tracking-[0.1em] px-2 py-1 text-left border border-slate-300">
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            {r.map((c, j) => (
              <td key={j}
                  className="px-2 py-1 border border-slate-200 align-top text-slate-800">
                {c ?? "—"}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

function SectionHeader({ section, payload }) {
  const d = section.data || {};
  const { t } = useT();
  return (
    <div className="border-b-2 border-slate-900 pb-3 mb-4"
         data-testid="report-viewer-section-header">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {payload.title} · {payload.audience}
          </div>
          <h1 className="text-3xl font-black tracking-tight">
            {t("Case")} {d.case_number || payload.case_number || "—"}
          </h1>
          <div className="text-sm text-slate-500 mt-1">
            {d.incident_type} · {d.location_label} · {t("Job")} {d.job_number || "—"}
          </div>
        </div>
        <SlaBadge status={d.sla_status} />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-3">
        <KV label={t("Occurred at")} value={d.occurred_at} testId="report-viewer-occurred-at" />
        <KV label={t("Reported at")} value={d.reported_at} />
        <KV label={t("Submitted at")} value={d.submitted_at} />
        <KV label={t("Reporter")} value={d.reporter_name} />
        <KV label={t("State")} value={d.state} />
      </div>
    </div>
  );
}

function SectionSummary({ section }) {
  const d = section.data || {}; const { t } = useT();
  return (
    <div data-testid="report-viewer-section-summary">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Summary")}</h2>
      <KV label={t("Observed conditions")} value={d.observed_conditions} />
      <div className="h-2" />
      <KV label={t("Immediate actions")} value={d.immediate_actions} />
    </div>
  );
}

function SectionExec({ section }) {
  const d = section.data || {}; const { t } = useT();
  return (
    <div data-testid="report-viewer-section-executive_summary">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Executive Summary")}</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        <KV label={t("Readiness")} value={`${d.readiness_pct ?? 0}%`} testId="report-viewer-readiness" />
        <KV label={t("State")} value={d.state} />
        <KV label={t("SLA")} value={d.sla_status} />
        <KV label={t("OSHA recordable")} value={String(d.osha_recordable ?? "—")} />
        <KV label={t("Root cause captured")} value={d.root_cause_present ? t("Yes") : t("No")} />
      </div>
      <div className="mt-3 p-3 bg-slate-50 border border-slate-200 rounded">
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 mb-1">{t("Blockers")}</div>
        {(d.blockers || []).length === 0
          ? <div className="italic text-slate-400 text-sm">{t("No blockers.")}</div>
          : <ul className="list-disc pl-5 text-sm">{d.blockers.map((b) => <li key={b}>{b}</li>)}</ul>}
      </div>
    </div>
  );
}

function SectionTimeline({ section }) {
  const { t } = useT();
  const rows = (section.data || []).map((e) => [
    e.at || "", e.event_type || "", e.actor_name || "",
    JSON.stringify(e.payload || {}),
  ]);
  return (
    <div data-testid="report-viewer-section-timeline">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Timeline")}</h2>
      <Table head={[t("When"), t("Event"), t("Actor"), t("Payload")]}
             rows={rows} empty={t("No events yet.")}
             testId="report-viewer-timeline-table" />
    </div>
  );
}

function SectionEvidence({ section }) {
  const { t } = useT();
  const rows = (section.data || []).map((i) => [
    i.id, i.evidence_type, i.label || "",
    i.added_at, `${i.chain_of_custody_length || 0} ${t("steps")}`,
  ]);
  return (
    <div data-testid="report-viewer-section-evidence">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Evidence Index")}</h2>
      <Table head={[t("ID"), t("Type"), t("Label"), t("Added"), t("Custody")]}
             rows={rows} empty={t("No evidence indexed.")}
             testId="report-viewer-evidence-table" />
    </div>
  );
}

function SectionWitnesses({ section }) {
  const { t } = useT();
  const rows = (section.data || []).map((w) => [
    w.name || "—", w.kind, w.status, w.contact || "",
    w.company || "", w.credibility_notes || "",
  ]);
  return (
    <div data-testid="report-viewer-section-witnesses">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Witnesses")}</h2>
      <Table head={[t("Name"), t("Kind"), t("Status"), t("Contact"),
                    t("Company"), t("Notes")]}
             rows={rows} empty={t("No witnesses recorded.")}
             testId="report-viewer-witnesses-table" />
    </div>
  );
}

function SectionMedical({ section }) {
  const { t } = useT();
  const d = section.data;
  if (d && typeof d === "object" && d.redacted) {
    return (
      <div data-testid="report-viewer-section-medical">
        <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Medical")}</h2>
        <div className="italic text-slate-400 text-sm">{t("Redacted for this audience.")}</div>
      </div>
    );
  }
  if (d && typeof d === "object" && "entries_count" in d) {
    return (
      <div data-testid="report-viewer-section-medical">
        <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Medical (aggregate)")}</h2>
        <div className="grid grid-cols-2 gap-2">
          <KV label={t("Entries")} value={d.entries_count} />
          <KV label={t("Total lost days")} value={d.total_lost_days} />
        </div>
      </div>
    );
  }
  const rows = (d || []).map((m) => [
    m.kind, m.provider || "", m.lost_days || 0, m.notes || "",
  ]);
  return (
    <div data-testid="report-viewer-section-medical">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Medical")}</h2>
      <Table head={[t("Kind"), t("Provider"), t("Lost days"), t("Notes")]}
             rows={rows} empty={t("No medical entries.")} />
    </div>
  );
}

function SectionAgency({ section }) {
  const { t } = useT();
  const rows = (section.data || []).map((a) => [
    a.agency_name || "", a.officer_name || "", a.report_number || "",
    a.case_status || "", a.contact_info || "",
  ]);
  return (
    <div data-testid="report-viewer-section-agency">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Police / Agency")}</h2>
      <Table head={[t("Agency"), t("Officer"), t("Report #"), t("Status"), t("Contact")]}
             rows={rows} empty={t("No agency contacts logged.")} />
    </div>
  );
}

function SectionComms({ section }) {
  const { t } = useT();
  const rows = (section.data || []).map((c) => [
    c.kind, c.contact_org || c.contact_name || "",
    c.subject || "", c.body || "", c.at || "",
  ]);
  return (
    <div data-testid="report-viewer-section-communications">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Communications")}</h2>
      <Table head={[t("Kind"), t("Party"), t("Subject"), t("Body"), t("When")]}
             rows={rows} empty={t("No communications logged.")} />
    </div>
  );
}

function SectionCapa({ section }) {
  const { t } = useT();
  const rows = (section.data || []).map((r) => [
    r.title, r.action_class, r.state,
    r.assigned_to_name || "", r.due_at || "",
  ]);
  return (
    <div data-testid="report-viewer-section-corrective_actions">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Corrective Actions")}</h2>
      <Table head={[t("Title"), t("Class"), t("State"),
                    t("Assigned to"), t("Due")]}
             rows={rows} empty={t("No corrective actions.")} />
    </div>
  );
}

function SectionRootCause({ section }) {
  const d = section.data || {}; const { t } = useT();
  return (
    <div data-testid="report-viewer-section-root_cause">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Root Cause")}</h2>
      <KV label={t("Summary")} value={d.summary} />
      <div className="h-2" />
      <KV label={t("Categories")} value={(d.categories || []).join(", ") || "—"} />
      <div className="h-2" />
      <KV label={t("Contributing factors")} value={(d.contributing_factors || []).join(", ") || "—"} />
    </div>
  );
}

function SectionKVGrid({ title, entries, testId }) {
  return (
    <div data-testid={testId}>
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{title}</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {entries.map(([k, v]) => <KV key={k} label={k} value={v} />)}
      </div>
    </div>
  );
}

function SectionVehicle({ section }) {
  const d = section.data || {}; const { t } = useT();
  return (
    <SectionKVGrid title={t("Vehicle Details")}
      testId="report-viewer-section-vehicle"
      entries={[
        [t("Vehicle IDs"), d.vehicle_ids],
        [t("Drivers"), d.drivers],
        [t("Passengers"), d.passengers],
        [t("Police response"), d.police_response],
        [t("Police case #"), d.police_case_number],
        [t("Tow required"), d.tow_required],
        [t("Traffic control"), d.traffic_control],
        [t("Third party involved"), d.third_party_involved],
        [t("Third-party info"), d.third_party_info],
      ]} />
  );
}

function SectionUtility({ section }) {
  const d = section.data || {}; const { t } = useT();
  return (
    <SectionKVGrid title={t("Utility Strike Details")}
      testId="report-viewer-section-utility"
      entries={[
        [t("Utility type"), d.utility_type],
        [t("Utility owner"), d.utility_owner],
        [t("Locate ticket #"), d.locate_ticket_number],
        [t("Locate valid"), d.locate_valid],
        [t("Service interrupted"), d.service_interrupted],
        [t("Emergency response called"), d.emergency_response_called],
        [t("ISP info"), d.isp_information],
      ]} />
  );
}

function SectionInjury({ section }) {
  const d = section.data || {}; const { t } = useT();
  return (
    <SectionKVGrid title={t("Injury Details")}
      testId="report-viewer-section-injury"
      entries={[
        [t("Injured employee"), d.injured_employee],
        [t("Body part"), d.injury_body_part],
        [t("Severity"), d.injury_severity],
        [t("First aid given"), d.first_aid_given],
        [t("EMS transported"), d.ems_transported],
        [t("Hospital"), d.hospital_name],
        [t("OSHA recordable"), String(d.osha_recordable ?? "—")],
        [t("Description"), d.injury_description],
      ]} />
  );
}

function SectionLinked({ section }) {
  const { t } = useT();
  const rows = (section.data || []).map((l) => [
    l.kind, l.target_id, l.target_label || "", l.added_at || "",
  ]);
  return (
    <div data-testid="report-viewer-section-linked">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Linked Records")}</h2>
      <Table head={[t("Kind"), t("Target ID"), t("Label"), t("Added")]}
             rows={rows} empty={t("No linked records.")} />
    </div>
  );
}

function SectionLessons({ section }) {
  const d = section.data || {}; const { t } = useT();
  return (
    <div data-testid="report-viewer-section-lessons_learned">
      <h2 className="text-lg font-bold mt-6 mb-2 pb-1 border-b border-slate-300">{t("Lessons Learned")}</h2>
      <KV label={t("Root cause")} value={d.root_cause_summary} />
      <div className="h-2" />
      <KV label={t("Contributing factors")}
          value={(d.contributing_factors || []).join(", ") || "—"} />
      {d.executive_review_notes ? (
        <>
          <div className="h-2" />
          <KV label={t("Executive review notes")} value={d.executive_review_notes} />
        </>
      ) : null}
    </div>
  );
}

const SECTION_RENDERERS = {
  header:             (s, p) => <SectionHeader key={s.code} section={s} payload={p} />,
  summary:            (s) => <SectionSummary key={s.code} section={s} />,
  executive_summary:  (s) => <SectionExec key={s.code} section={s} />,
  timeline:           (s) => <SectionTimeline key={s.code} section={s} />,
  evidence:           (s) => <SectionEvidence key={s.code} section={s} />,
  witnesses:          (s) => <SectionWitnesses key={s.code} section={s} />,
  medical:            (s) => <SectionMedical key={s.code} section={s} />,
  agency:             (s) => <SectionAgency key={s.code} section={s} />,
  communications:     (s) => <SectionComms key={s.code} section={s} />,
  corrective_actions: (s) => <SectionCapa key={s.code} section={s} />,
  root_cause:         (s) => <SectionRootCause key={s.code} section={s} />,
  vehicle:            (s) => <SectionVehicle key={s.code} section={s} />,
  utility:            (s) => <SectionUtility key={s.code} section={s} />,
  injury:             (s) => <SectionInjury key={s.code} section={s} />,
  linked:             (s) => <SectionLinked key={s.code} section={s} />,
  lessons_learned:    (s) => <SectionLessons key={s.code} section={s} />,
};

export default function IncidentReportViewer() {
  const { caseId, reportType } = useParams();
  const navigate = useNavigate();
  const { t } = useT();
  const [payload, setPayload] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let live = true;
    setLoading(true);
    cli()
      .get(`/incident-cases/${encodeURIComponent(caseId)}/reports/${encodeURIComponent(reportType)}`)
      .then((r) => { if (live) setPayload(r.data); })
      .catch((e) => { if (live) setErr(e?.response?.data?.detail || String(e)); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [caseId, reportType]);

  const pdfUrl = useMemo(
    () => `${API}/incident-cases/${encodeURIComponent(caseId)}/reports/${encodeURIComponent(reportType)}.pdf`,
    [caseId, reportType],
  );

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      alert(t("Report link copied."));
    } catch (_err) {
      window.prompt(t("Copy this link"), window.location.href);
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-4xl mx-auto" data-testid="report-viewer-loading">
        <div className="animate-pulse text-slate-500">{t("Loading report…")}</div>
      </div>
    );
  }

  if (err) {
    return (
      <div className="p-8 max-w-3xl mx-auto" data-testid="report-viewer-error">
        <div className="p-4 rounded-lg border border-red-300 bg-red-50 text-red-900">
          <div className="font-bold">{t("Could not load report")}</div>
          <div className="text-sm mt-1">
            {typeof err === "string" ? err : JSON.stringify(err)}
          </div>
          <button
            onClick={() => navigate(-1)}
            className="mt-3 px-3 py-1.5 rounded border border-red-400 bg-white text-red-900 text-sm"
            data-testid="report-viewer-back-btn"
          >
            <ArrowLeft className="inline w-3.5 h-3.5 mr-1" />{t("Back")}
          </button>
        </div>
      </div>
    );
  }

  const sections = payload?.sections || [];

  return (
    <div className="min-h-screen bg-slate-100 print:bg-white"
         data-testid="incident-report-viewer">
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { background: white !important; }
        }
        @page { size: Letter; margin: 0.6in; }
      `}</style>

      {/* Toolbar */}
      <div className="no-print sticky top-0 z-10 bg-slate-900 text-slate-50 px-4 py-2 flex flex-wrap items-center gap-2">
        <button
          onClick={() => navigate(`/safety/cases/${caseId}`)}
          className="inline-flex items-center gap-1 px-2 py-1 rounded hover:bg-slate-800 text-xs"
          data-testid="report-viewer-back-to-case"
        >
          <ArrowLeft className="w-3.5 h-3.5" />{t("Back to case")}
        </button>
        <div className="flex-1" />
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded bg-white text-slate-900 text-xs font-semibold hover:bg-slate-100"
          data-testid="report-viewer-print-btn"
        >
          <Printer className="w-3.5 h-3.5" />{t("Print")}
        </button>
        <a
          href={pdfUrl}
          target="_blank" rel="noopener noreferrer"
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded bg-emerald-500 text-white text-xs font-semibold hover:bg-emerald-400"
          data-testid="report-viewer-pdf-btn"
        >
          <FileDown className="w-3.5 h-3.5" />{t("Download PDF")}
        </a>
        <button
          onClick={handleShare}
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded bg-slate-700 text-slate-50 text-xs font-semibold hover:bg-slate-600"
          data-testid="report-viewer-share-btn"
        >
          <Share2 className="w-3.5 h-3.5" />{t("Share")}
        </button>
      </div>

      {/* Print header/banner (audience + branding) */}
      <div className="max-w-4xl mx-auto bg-white shadow-sm p-8 my-6 print:shadow-none print:m-0 print:p-6">
        {payload?.customer_facing ? (
          <div className="no-print mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-900"
               data-testid="report-viewer-customer-facing-badge">
            <ShieldCheck className="w-3.5 h-3.5" />
            {t("Customer-facing report")}
          </div>
        ) : null}

        {sections.map((s) => {
          const fn = SECTION_RENDERERS[s.code];
          if (!fn) return null;
          return fn(s, payload);
        })}

        <div className="mt-8 pt-4 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <div>{payload?.title} · {t("Case")} {payload?.case_number || payload?.case_id}</div>
          <div className="inline-flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {t("Generated")} {payload?.generated_at}
          </div>
        </div>
      </div>
    </div>
  );
}
