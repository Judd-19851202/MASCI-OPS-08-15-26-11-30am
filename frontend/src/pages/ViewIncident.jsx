import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { Printer, Loader2, Trash2, MapPin, Mail, ClipboardCheck, CheckCircle2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { RefKicker } from "@/components/RefKicker";
import BackLink from "@/components/BackLink";
import { useHubHome } from "@/components/HubBackLink";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { formatDateLong } from "@/lib/utils";
import { getCompanyInfo } from "@/lib/companyInfo";
import { formatCoords } from "@/lib/geolocation";
import { MapThumbnail } from "@/components/MapThumbnail";
import { printReport, maybeAutoPrint } from "@/lib/printReport";
import { PrintWatermark } from "@/components/PrintWatermark";
import { PhotoLightbox } from "@/components/PhotoLightbox";
import { PhotoZipDownload } from "@/components/PhotoZipDownload";
import { resolvePhotoSrc } from "@/lib/photoSrc";
import { EmailReportDialog } from "@/components/EmailReportDialog";
import { EditProjectDialog } from "@/components/EditProjectDialog";
import { SubmitLangBadge } from "@/components/SubmitLangBadge";
import { useT } from "@/lib/i18n";
import { LifecycleGuide } from "@/components/LifecycleGuide";
import { AlertOctagon } from "lucide-react";
import {
  SEVERITY_LEVELS,
  ROOT_CAUSE_CATEGORIES,
} from "@/lib/incidentSchema";

const ReportSection = ({ number, title, children }) => (
  <section className="bg-white border border-slate-200 rounded-md p-5 sm:p-7 print-section">
    <div className="flex items-baseline gap-3 mb-4 pb-2 border-b-2 border-slate-200">
      <span className="font-mono text-xs uppercase tracking-[0.2em] text-red-700">
        Section {number}
      </span>
      <h2 className="font-display text-xl sm:text-2xl font-bold text-slate-900">
        {title}
      </h2>
    </div>
    {children}
  </section>
);

const KV = ({ label, value, full = false }) => (
  <div className={full ? "sm:col-span-2" : ""}>
    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
      {label}
    </div>
    <div className="text-base text-slate-900 mt-1 whitespace-pre-wrap">
      {value || "—"}
    </div>
  </div>
);

const severityOf = (key) =>
  SEVERITY_LEVELS.find((s) => s.key === key) || SEVERITY_LEVELS[0];

// Phase 5D · P1 — Tier-2 follow-up awareness
// Derives a quiet operational status from severity + linked CAPAs.
// Never stored, never cached — computed live on every render.
// Returns null when the incident is low-severity AND has no CAPAs
// (no follow-up needed, no banner shown).
const SERIOUS_SEVERITIES = new Set(["medical", "restricted", "lost_time", "fatality"]);
const OPEN_CAPA_STATES = new Set(["Open", "In Progress", "Pending Review"]);

function computeFollowUpStatus(incident, capas) {
  const sev = (incident?.severity || "").toLowerCase();
  const oshaRecordable = incident?.osha_recordable === "Yes";
  const requiresFollowUp = SERIOUS_SEVERITIES.has(sev) || oshaRecordable;
  const capaCount = capas.length;
  const openCount = capas.filter((c) => OPEN_CAPA_STATES.has(c.status || "Open")).length;
  const verifiedCount = capas.filter((c) => c.status === "Verified" || c.status === "Closed").length;

  if (capaCount === 0 && requiresFollowUp) {
    return {
      kind: "required",
      tone: "rose",
      glossaryAnchor: "follow_up_required",
      titleKey: "Follow-Up Required",
      summaryKey: "Tier-1 report is in. No CAPA has been opened yet. Open one to track the corrective work.",
      ctaKey: "Open Follow-Up CAPA",
    };
  }
  if (capaCount > 0 && openCount > 0) {
    return {
      kind: "open",
      tone: "amber",
      glossaryAnchor: "investigation_open",
      titleKey: "Investigation Open",
      // Counts surface as numbers; surrounding label translates via t().
      counts: { verified: verifiedCount, total: capaCount, open: openCount },
      summaryTemplate: "open",
      ctaKey: null,
    };
  }
  if (capaCount > 0 && openCount === 0) {
    return {
      kind: "complete",
      tone: "emerald",
      glossaryAnchor: "operationally_complete",
      titleKey: "Operationally Complete",
      counts: { verified: verifiedCount, total: capaCount, open: openCount },
      summaryTemplate: "complete",
      ctaKey: null,
    };
  }
  return null; // low severity, no CAPAs → quiet
}

const TONE_STYLES = {
  rose: {
    wrap: "bg-rose-50 border-rose-300",
    pill: "bg-rose-700 text-white",
    label: "text-rose-700",
    icon: "text-rose-700",
    iconCmp: AlertTriangle,
    cta: "bg-rose-700 hover:bg-rose-800 text-white border-rose-900",
  },
  amber: {
    wrap: "bg-amber-50 border-amber-300",
    pill: "bg-amber-600 text-white",
    label: "text-amber-700",
    icon: "text-amber-700",
    iconCmp: ClipboardCheck,
    cta: "",
  },
  emerald: {
    wrap: "bg-emerald-50 border-emerald-300",
    pill: "bg-emerald-700 text-white",
    label: "text-emerald-700",
    icon: "text-emerald-700",
    iconCmp: CheckCircle2,
    cta: "",
  },
};

export default function ViewIncident() {
  const { t } = useT();
  const hubHome = useHubHome();
  const { id } = useParams();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const listUrl = pathname.replace(/\/[^/]+$/, "") || "/admin/incidents";
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [emailOpen, setEmailOpen] = useState(false);
  // iter368 · reverse-link from incident → CAPAs that cite it as source.
  // Closes the operational convergence gap where the incident detail
  // page never surfaced which CAPAs were tracking its follow-up.
  const [linkedCapas, setLinkedCapas] = useState([]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await api.get(`/incidents/${id}`);
        if (alive) setData(res.data);
      } catch {
        toast.error(t("Incident not found"));
        navigate(listUrl);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [id, navigate, listUrl, t]);

  // iter368 · Fetch linked CAPAs in parallel. Non-blocking; tolerates
  // permission errors so subcontractor / public-form viewers don't see
  // a noisy failure.
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get(`/safety/corrective-actions?source_kind=incident&source_id=${id}`);
        if (alive) setLinkedCapas(Array.isArray(r.data) ? r.data : []);
      } catch {
        if (alive) setLinkedCapas([]);
      }
    })();
    return () => { alive = false; };
  }, [id]);

  // Auto-print after the page renders if we landed here via ?autoprint=1
  useEffect(() => {
    if (!loading && data) maybeAutoPrint();
  }, [loading, data]);

  const handleDelete = async () => {
    if (!window.confirm(t("Delete this incident report? This cannot be undone.")))
      return;
    try {
      await api.delete(`/incidents/${id}`);
      toast.success(t("Deleted"));
      navigate(listUrl);
    } catch {
      toast.error(t("Delete failed"));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-500">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> {t("Loading…")}
      </div>
    );
  }
  if (!data) return null;

  const sev = severityOf(data.severity);
  const company = getCompanyInfo();
  const checkedRootCauses = ROOT_CAUSE_CATEGORIES.filter(
    (c) => data.root_causes && data.root_causes[c.key]
  );
  // Phase 5D · P1 — quiet follow-up awareness
  const followUpStatus = computeFollowUpStatus(data, linkedCapas);
  const followUpTone = followUpStatus ? TONE_STYLES[followUpStatus.tone] : null;
  const FollowUpIcon = followUpTone?.iconCmp;
  const capaCtaHref =
    `/safety-portal/corrective-actions?source_kind=incident&source_id=${data.id}` +
    `&title=${encodeURIComponent(`Incident follow-up — ${data.incident_type || "Incident"}`)}`;

  return (
    <div className="min-h-screen bg-slate-50">
      <PrintWatermark />
      <div className="caution-stripe no-print" />
      <header className="bg-slate-900 border-b-4 border-red-700 sticky top-0 z-10 no-print">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
          <BackLink to={listUrl} label={t("Incidents")} variant="header" testId="back-link" />
          <MasciLogo variant="mark" size="md" homeLink={hubHome} />
          <div className="flex gap-2">
            <EditProjectDialog
              kind="incidents"
              recordId={data.id}
              current={data}
              onSaved={(rec) => rec && setData(rec)}
            />
            <Button
              variant="outline"
              size="icon"
              onClick={handleDelete}
              className="h-11 w-11 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:text-red-400"
              data-testid="delete-btn"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              onClick={() => setEmailOpen(true)}
              className="h-11 px-4 border-2 border-slate-600 bg-slate-800 text-white hover:border-red-500 hover:bg-slate-700 font-bold uppercase tracking-wide text-sm"
              data-testid="email-btn"
            >
              <Mail className="w-4 h-4 mr-1" /> {t("Email")}
            </Button>
            <Button
              onClick={printReport}
              className="h-11 px-4 bg-red-700 hover:bg-red-800 text-white font-bold uppercase tracking-wide text-sm border-b-2 border-red-900"
              data-testid="print-btn"
            >
              <Printer className="w-4 h-4 mr-1" /> {t("Print / PDF")}
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6 print-page">
        {/* iter365 · operational coaching uniformity — short, field-direct.
            Hidden on print so the official report PDF stays clean. */}
        <div className="print:hidden">
          <LifecycleGuide
            id="incident-detail"
            icon={AlertOctagon}
            accent="rose"
            title={t("Incident lifecycle")}
            summary={t("Reported → Linked CAPA(s) → Verified → Closed. Closing without a verified CAPA is blocked.")}
            sections={[
              { label: t("Why this matters"), body: t("Every incident is tied to corrective actions. Closing the loop is how the crew learns and the next shift stays safe.") },
              { label: t("Downstream"), body: t("Safety, the PM, HR (for OSHA recordables), and the involved employee's accountability timeline all see this record.") },
            ]}
          />
        </div>

        {/* Phase 5D · P1 — Tier-2 follow-up awareness banner.
            Quiet operational status derived live from severity + linked
            CAPAs. Hidden on print so the official report PDF stays clean. */}
        {followUpStatus && followUpTone ? (
          <div
            className={`print:hidden border-2 ${followUpTone.wrap} rounded-md px-4 py-3 flex items-start gap-3`}
            data-testid={`followup-status-${followUpStatus.kind}`}
          >
            <FollowUpIcon className={`w-5 h-5 shrink-0 mt-0.5 ${followUpTone.icon}`} aria-hidden />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className={`inline-flex items-center px-2 py-0.5 text-[10px] font-mono uppercase tracking-[0.18em] rounded font-bold ${followUpTone.pill}`}
                >
                  {t(followUpStatus.titleKey)}
                </span>
                <Link
                  to={`/admin/operational-language#${followUpStatus.glossaryAnchor}`}
                  className={`text-[10px] font-mono uppercase tracking-[0.18em] ${followUpTone.label} hover:underline`}
                  data-testid="followup-glossary-link"
                >
                  {t("What this means")}
                </Link>
              </div>
              <p className="text-sm text-slate-800 mt-1 leading-snug">
                {followUpStatus.summaryKey ? (
                  t(followUpStatus.summaryKey)
                ) : followUpStatus.summaryTemplate === "open" ? (
                  <>
                    {followUpStatus.counts.verified}
                    {" "}
                    {t("of")}
                    {" "}
                    {followUpStatus.counts.total}
                    {" "}
                    {t("CAPA(s) verified ·")}
                    {" "}
                    {followUpStatus.counts.open}
                    {" "}
                    {t("still in motion.")}
                  </>
                ) : (
                  <>
                    {t("All")}
                    {" "}
                    {followUpStatus.counts.total}
                    {" "}
                    {t("linked CAPA(s) verified or closed. Audit trail preserved.")}
                  </>
                )}
              </p>
            </div>
            {followUpStatus.ctaKey ? (
              <Link to={capaCtaHref} className="shrink-0" data-testid="followup-cta">
                <Button
                  size="sm"
                  className={`h-9 px-3 font-bold uppercase tracking-wide text-xs border-b-2 ${followUpTone.cta}`}
                >
                  <ClipboardCheck className="w-4 h-4 mr-1" />
                  {t(followUpStatus.ctaKey)}
                </Button>
              </Link>
            ) : null}
          </div>
        ) : null}
        <div className="flex items-start justify-between border-b-4 border-red-700 pb-4 gap-4">
          <div className="flex-1">
            <MasciLogo
              variant="mark"
              size="2xl"
              className="hidden sm:block max-w-[420px]"
              onLight
            homeLink={hubHome} />
            <MasciLogo variant="mark" size="xl" className="sm:hidden" homeLink={hubHome} />
            {/* iter336 · review-side reference continuity · same canonical
                ID surfaced on the /thank-you submission page so reviewers
                can spot-match a record from a field crew's verbal/
                screenshot reference. */}
            <RefKicker
              recordId={data.incident_number || data.report_number || data.id}
              testId="view-incident-ref"
              className="mt-4"
            />
            <h1 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">
              {t("Accident / Incident Report")}
            </h1>
            <div className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 mt-1 flex items-center gap-2 flex-wrap">
              {data.doc_id && (
                <span
                  className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-red-50 border border-red-300 text-red-800 font-bold tabular-nums tracking-wide"
                  data-testid="record-doc-id-badge"
                >
                  <span className="text-[9px] uppercase tracking-[0.22em] text-red-700">{t("Doc ID")}</span>
                  {data.doc_id}
                </span>
              )}
              <span>{t("Report ID")} · {data.id?.slice(0, 8).toUpperCase()}</span>
            </div>
            {data.submit_language === "es" && (
              <div className="mt-2">
                <SubmitLangBadge lang={data.submit_language} />
              </div>
            )}
            <div className="mt-2 flex items-center gap-2 flex-wrap">
              <span
                className={`inline-flex items-center px-2.5 py-1 ${sev.color} text-white text-[11px] font-mono uppercase tracking-wider rounded font-bold`}
                data-testid="severity-badge"
              >
                {sev.label}
              </span>
              {data.osha_recordable === "Yes" && (
                <span className="inline-flex items-center px-2.5 py-1 bg-red-900 text-white text-[11px] font-mono uppercase tracking-wider rounded font-bold">
                  {t("OSHA Recordable")}
                </span>
              )}
              <span className="inline-flex items-center px-2.5 py-1 bg-slate-800 text-white text-[11px] font-mono uppercase tracking-wider rounded">
                {data.incident_type}
              </span>
            </div>
          </div>
        </div>

        <ReportSection number="01" title={t("Report Information")}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <KV label={t("Project Name")} value={data.project_name} />
            <KV label={t("Project Number")} value={data.project_number} />
            <div className="sm:col-span-2">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                {t("Location")}
              </div>
              <div className="text-base text-slate-900 mt-1 whitespace-pre-wrap">
                {data.location || "—"}
              </div>
              {data.gps_lat != null && (
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-1 flex items-center gap-1 flex-wrap">
                  <MapPin className="w-3 h-3 text-red-700" />
                  <span>
                    GPS · {formatCoords(data.gps_lat, data.gps_lng, data.gps_accuracy)}
                  </span>
                  <a
                    href={`https://www.google.com/maps?q=${data.gps_lat},${data.gps_lng}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-red-700 hover:text-red-800 font-bold no-print"
                  >
                    · {t("Open in Maps")}
                  </a>
                </div>
              )}
              {data.gps_lat != null && (
                <MapThumbnail
                  lat={data.gps_lat}
                  lng={data.gps_lng}
                  className="mt-2"
                />
              )}
            </div>
            <KV
              label={t("Incident Date")}
              value={formatDateLong(data.incident_date)}
            />
            <KV label={t("Incident Time")} value={data.incident_time} />
            <KV
              label={t("Reported Date")}
              value={formatDateLong(data.reported_date)}
            />
            <KV label={t("Reported By")} value={data.reported_by} />
            <KV label={t("Supervisor")} value={data.supervisor_name} />
          </div>
        </ReportSection>

        <ReportSection number="02" title={t("Classification")}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <KV label={t("Incident Type")} value={data.incident_type} />
            <KV label={t("Severity")} value={sev.label} />
            <KV label={t("OSHA Recordable")} value={data.osha_recordable} />
            <KV label={t("Work Stopped")} value={data.work_stopped} />
          </div>
        </ReportSection>

        {(data.person_name || data.body_part || data.injury_nature) && (
          <ReportSection number="03" title={t("Person Involved")}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <KV label={t("Name")} value={data.person_name} />
              <KV label={t("Role / Trade")} value={data.person_role} />
              <KV label={t("Employer")} value={data.person_employer} />
              <KV
                label={t("Years Experience")}
                value={data.person_years_experience}
              />
              <KV label={t("Body Part")} value={data.body_part} />
              <KV label={t("Injury Nature")} value={data.injury_nature} />
              <KV
                label={t("Treatment Provided")}
                value={data.treatment_provided}
                full
              />
              <KV label={t("Medical Facility")} value={data.medical_facility} />
              <KV label={t("Sent Home / Off Site")} value={data.sent_home} />
            </div>
          </ReportSection>
        )}

        <ReportSection number="04" title={t("What Happened")}>
          <div className="space-y-4">
            <KV label={t("Description")} value={data.description} full />
            <KV label={t("Immediate Cause")} value={data.immediate_cause} full />
            <KV
              label={t("Contributing Factors")}
              value={data.contributing_factors}
              full
            />
          </div>
        </ReportSection>

        <ReportSection number="05" title={t("Root Cause Analysis")}>
          {checkedRootCauses.length === 0 ? (
            <div className="text-slate-500 text-sm">
              {t("No root cause categories selected.")}
            </div>
          ) : (
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {checkedRootCauses.map((c) => (
                <li
                  key={c.key}
                  className="flex items-center gap-2 p-2 border border-red-200 rounded bg-red-50"
                >
                  <span className="inline-flex w-1.5 h-1.5 rounded-full bg-red-700 shrink-0" />
                  <span className="text-sm text-slate-900">{c.label}</span>
                </li>
              ))}
            </ul>
          )}
          {data.root_cause_notes && (
            <div className="mt-4">
              <KV label={t("Notes")} value={data.root_cause_notes} full />
            </div>
          )}
        </ReportSection>

        <ReportSection
          number="06"
          title={`${t("Witnesses")} (${data.witnesses?.length || 0})`}
        >
          {data.witnesses?.length === 0 ? (
            <div className="text-slate-500 text-sm">{t("No witnesses listed.")}</div>
          ) : (
            <div className="space-y-3">
              {(data.witnesses || []).map((w, i) => (
                <div
                  key={i}
                  className="border border-slate-200 rounded-md p-3 print-row"
                >
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                    {t("Witness")} {i + 1}
                  </div>
                  <div className="font-bold text-slate-900 mt-1">
                    {w.name || "—"}
                  </div>
                  {w.statement && (
                    <div className="text-sm text-slate-700 mt-2 whitespace-pre-wrap">
                      {w.statement}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </ReportSection>

        <ReportSection number="07" title={t("Corrective Actions & Follow-Up")}>
          <div className="space-y-4">
            <KV
              label={t("Immediate Actions Taken")}
              value={data.immediate_actions_taken}
              full
            />
            <KV
              label={t("Long-Term Corrective Actions")}
              value={data.corrective_actions}
              full
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <KV label={t("Responsible Party")} value={data.responsible_party} />
              <KV
                label={t("Target Completion")}
                value={
                  data.target_completion_date
                    ? formatDateLong(data.target_completion_date)
                    : "—"
                }
              />
            </div>

            {/* iter368 · Linked CAPAs (reverse-lookup) — closes the
                operational convergence gap where the incident detail
                page never surfaced which CAPAs were tracking it.
                Hidden in print so the official report stays unchanged. */}
            {linkedCapas.length > 0 && (
              <div className="print:hidden border-t border-slate-200 pt-4 mt-4" data-testid="incident-linked-capas">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-rose-700 font-bold mb-2">
                  {t("Linked CAPAs")} · {linkedCapas.length}
                </div>
                <div className="space-y-2">
                  {linkedCapas.map((c) => (
                    <div
                      key={c.id}
                      className="border border-slate-200 rounded-md px-3 py-2 text-sm hover:bg-slate-50"
                      data-testid={`linked-capa-${c.id}`}
                    >
                      <div className="flex items-baseline justify-between gap-3 flex-wrap">
                        <div className="font-semibold text-slate-900">{c.title || "—"}</div>
                        <span className="font-mono text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border bg-slate-50">
                          {c.status || "Open"}
                        </span>
                      </div>
                      {c.assigned_to_name ? (
                        <div className="text-xs text-slate-600 mt-1">
                          {t("Owner")}: {c.assigned_to_name}
                          {c.due_date ? ` · ${t("Due")} ${c.due_date}` : ""}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </ReportSection>

        <ReportSection number="08" title={t("Notifications")}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <KV label={t("Safety Manager")} value={data.notified_safety_manager} />
            <KV label={t("Project Manager")} value={data.notified_pm} />
            <KV label={t("General Contractor")} value={data.notified_gc} />
            <KV label={t("Owner / Agency")} value={data.notified_owner} />
            <KV label={t("OSHA")} value={data.notified_osha} />
            <KV label={t("Other")} value={data.notified_other} />
          </div>
        </ReportSection>

        {data.photos?.length > 0 && (
          <ReportSection number="09" title={`${t("Photos")} (${data.photos.length})`}>
            <div className="flex justify-end mb-2 print:hidden">
              <PhotoZipDownload
                photos={data.photos}
                prefix={`MASCI_Incident_${(data.id || "").slice(0, 8)}_photos`}
                testId="incident-photos-zip"
              />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {data.photos.map((p, i) => (
                <PhotoLightbox
                  key={i}
                  src={p}
                  alt={`Incident Photo ${i + 1}`}
                  filename={`MASCI_Incident_${(data.id || "").slice(0, 8)}_photo${i + 1}.jpg`}
                  className="relative w-full aspect-square rounded-md overflow-hidden border border-slate-200 bg-white"
                  testId={`view-photo-${i}`}
                >
                  <img
                    src={resolvePhotoSrc(p)}
                    alt={`Photo ${i + 1}`}
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                </PhotoLightbox>
              ))}
            </div>
          </ReportSection>
        )}

        <ReportSection number="10" title={t("Signatures")}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
                {t("Reporter")}
              </div>
              <div className="text-base font-bold text-slate-900 mb-2">
                {data.reported_by || "—"}
              </div>
              <div className="border border-slate-200 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center">
                {data.reporter_signature ? (
                  <img
                    src={data.reporter_signature}
                    alt="Reporter signature"
                    className="max-h-[120px]"
                  />
                ) : (
                  <span className="text-slate-400 text-sm">{t("No signature")}</span>
                )}
              </div>
            </div>
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
                {t("Supervisor")}
              </div>
              <div className="text-base font-bold text-slate-900 mb-2">
                {data.supervisor_name || "—"}
              </div>
              <div className="border border-slate-200 rounded-md bg-white p-2 min-h-[120px] flex items-center justify-center">
                {data.supervisor_signature ? (
                  <img
                    src={data.supervisor_signature}
                    alt="Supervisor signature"
                    className="max-h-[120px]"
                  />
                ) : (
                  <span className="text-slate-400 text-sm">{t("No signature")}</span>
                )}
              </div>
            </div>
          </div>
        </ReportSection>

        <div className="text-center font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500 pt-4 pb-8 print-section">
          {t("Generated")}{" "}
          {data.created_at ? new Date(data.created_at).toLocaleString() : ""} ·{" "}
          {company.company_name || "MASCI"} {t("Incident Report")}
        </div>
        {(company.address ||
          company.phone ||
          company.email) && (
          <div className="print-only border-t-2 border-black pt-3 mt-2 text-[9pt] leading-snug print-section">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-display font-black text-[11pt] text-black">
                  {company.company_name || "MASCI"}
                </div>
                {company.tagline && (
                  <div className="font-mono text-[8pt] uppercase tracking-[0.2em] text-black">
                    {company.tagline}
                  </div>
                )}
              </div>
              <div className="text-right text-black">
                {company.address && <div>{company.address}</div>}
                {company.city_state_zip && <div>{company.city_state_zip}</div>}
                {(company.phone || company.email) && (
                  <div>
                    {company.phone}
                    {company.phone && company.email ? " · " : ""}
                    {company.email}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
      <EmailReportDialog open={emailOpen} onOpenChange={setEmailOpen} kind="incident" record={data} />
    </div>
  );
}
