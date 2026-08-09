// Track 19.36 · Executive Case Report — boardroom-grade single-screen view
// consuming the same unified Executive Intelligence Model that powers the
// server-rendered PDF. Zero-drift: reads only, never writes.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { useT } from "@/lib/i18n";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import {
  AlertTriangle, ChevronLeft, Download, FileText, Lock, ScrollText,
  ShieldCheck, TrendingUp, Users,
} from "lucide-react";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const requestConfig = () => ({
  headers: buildScopedPortalAuthHeaders(["safety", "admin", "pm"], { "Content-Type": "application/json" }),
  timeout: 20000,
});

async function downloadPdfBlob(url, fallbackName) {
  const res = await fetch(url, {
    headers: buildScopedPortalAuthHeaders(["safety", "admin", "pm"]),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const blob = await res.blob();
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const cd = res.headers.get("content-disposition") || "";
  const match = /filename="?([^";]+)"?/i.exec(cd);
  link.href = href;
  link.download = match ? match[1] : fallbackName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(href);
}

function _fmt(v) {
  if (v === null || v === undefined || v === "") return "";
  try { return formatPlatformTime(v); } catch { return String(v); }
}

function NotDocumented() {
  const { t } = useT();
  return <span className="italic text-slate-400">{t("Not documented yet.")}</span>;
}

function Field({ label, value, testId, mono }) {
  const has = value !== undefined && value !== null && String(value).trim() !== "";
  return (
    <div className="grid grid-cols-3 gap-3 py-1.5 border-b border-slate-100 last:border-0" data-testid={testId}>
      <dt className="col-span-1 text-[10px] uppercase tracking-[0.14em] font-mono text-slate-500">{label}</dt>
      <dd className={`col-span-2 text-sm ${mono ? "font-mono" : ""} ${has ? "text-slate-900" : ""}`}>
        {has ? String(value) : <NotDocumented />}
      </dd>
    </div>
  );
}

function Section({ title, icon: Icon, testId, children, tone = "default" }) {
  const border = tone === "hero" ? "border-slate-900" : "border-slate-200";
  return (
    <section
      className={`rounded-xl border-2 ${border} bg-white p-4 sm:p-5`}
      data-testid={`exec-report-section-${testId}`}
    >
      <div className="flex items-center gap-2 mb-3">
        {Icon && <Icon className="w-4 h-4 text-slate-700" aria-hidden />}
        <h2 className="font-display text-lg font-black tracking-tight text-slate-900">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function SeverityChip({ band }) {
  const tone =
    band === "high" ? "bg-red-100 text-red-900 border-red-300" :
    band === "elevated" ? "bg-amber-100 text-amber-900 border-amber-300" :
    band === "moderate" ? "bg-orange-100 text-orange-900 border-orange-300" :
    "bg-cyan-100 text-cyan-900 border-cyan-300";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-0.5 font-mono text-[10px] uppercase tracking-[0.14em] ${tone}`}
      data-testid="exec-report-severity-chip"
    >
      {band || "unrated"}
    </span>
  );
}

export default function ExecutiveCaseReport() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const { t } = useT();
  const [model, setModel] = useState(null);
  const [err, setErr] = useState("");
  const [downloading, setDownloading] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await axios.get(
        `${API}/incident-cases/${caseId}/executive-intelligence`,
        requestConfig(),
      );
      setModel(data);
    } catch (e) {
      setErr(e?.response?.data?.detail?.detail || e.response?.data?.detail || e.message || "load_failed");
    }
  }, [caseId]);

  useEffect(() => { load(); }, [load]);

  const downloadPdf = async () => {
    if (downloading) return;
    setDownloading(true);
    try {
      await downloadPdfBlob(
        `${API}/incident-cases/${caseId}/executive-report.pdf`,
        `executive_report_${caseId}.pdf`,
      );
    } catch (e) {
      setErr(e?.message || String(e));
    } finally {
      setDownloading(false);
    }
  };

  const noReportReady = /404|not found|case not found/i.test(String(err || ""));

  if (err) {
    return (
      <div className="min-h-screen bg-slate-50 p-6" data-testid={noReportReady ? "exec-report-empty" : "exec-report-error"}>
        <div className={`max-w-md mx-auto rounded-xl border-2 bg-white p-6 ${noReportReady ? "border-amber-300" : "border-red-300"}`}>
          <div className={`font-mono text-[10px] uppercase tracking-widest ${noReportReady ? "text-amber-800" : "text-red-800"}`}>
            {noReportReady ? t("Executive report") : t("Error")}
          </div>
          <div className="font-display text-xl font-black text-slate-900 mt-1">
            {noReportReady ? t("Executive report not ready yet") : t("Could not load executive report")}
          </div>
          <p className="mt-2 text-sm text-slate-700">
            {noReportReady
              ? t("This case does not have an executive report in the current preview data yet. Safety can prepare the case package first, then reopen this page.")
              : String(err)}
          </p>
          <button
            className="mt-4 h-10 px-4 rounded-md bg-slate-900 text-white"
            onClick={() => navigate(-1)}
            data-testid="exec-report-back"
          >
            {t("Back")}
          </button>
        </div>
      </div>
    );
  }

  if (!model) {
    return (
      <div className="min-h-screen bg-slate-50 p-6" data-testid="exec-report-loading">
        {t("Loading executive report…")}
      </div>
    );
  }

  const cr = model.case_ref || {};
  const s = model.executive_summary || {};
  const why = model.why_it_matters || {};
  const timeline = model.timeline || [];
  const evidence = model.evidence_chain || [];
  const capa = model.corrective_actions || { items: [], totals: {} };
  const reg = model.regulatory_review || {};
  const readiness = model.readiness || { sub_scores: [] };
  const decisions = model.decision_records || [];
  const ops = model.operational_intelligence || {};
  const attention = model.attention_signals || null;

  return (
    <div className="min-h-screen bg-slate-100" data-testid="exec-report">
      <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3 print:hidden">
        <button
          onClick={() => navigate(-1)}
          className="h-9 w-9 rounded-md border border-slate-300 hover:bg-slate-100 flex items-center justify-center"
          aria-label={t("Back")}
          data-testid="exec-report-back"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            {t("Executive Case Report")}
          </div>
          <div className="font-display text-base font-black text-slate-900">
            {t("Case")} #{cr.case_number || (cr.case_id || "").slice(0, 8) || "—"}
          </div>
        </div>
        <button
          onClick={downloadPdf}
          className="inline-flex items-center gap-1.5 h-9 px-3 rounded-md bg-slate-900 text-white text-sm font-bold hover:bg-slate-800"
          data-testid="exec-report-download-pdf"
        >
          <Download className="w-4 h-4" aria-hidden /> {downloading ? t("Downloading…") : t("PDF")}
        </button>
      </header>

      <main className="max-w-5xl mx-auto p-4 sm:p-6 space-y-4">
        {/* Hero */}
        <Section title={s.headline || t("Incident")} icon={AlertTriangle} testId="hero" tone="hero">
          <div className="flex flex-wrap gap-2 mb-3" data-testid="exec-report-hero-meta">
            <SeverityChip band={s.severity_band} />
            <span className="inline-flex items-center rounded-full border border-slate-300 bg-slate-50 px-3 py-0.5 font-mono text-[10px] uppercase tracking-[0.14em] text-slate-700">
              {t("State")} · {cr.state || "—"}
            </span>
            <span className="inline-flex items-center rounded-full border border-slate-300 bg-slate-50 px-3 py-0.5 font-mono text-[10px] uppercase tracking-[0.14em] text-slate-700">
              {t("Readiness")} · {readiness.overall_pct ?? 0}%
            </span>
          </div>
          <p className="text-sm text-slate-700 leading-relaxed border-l-4 border-slate-300 pl-3">
            {s.one_paragraph || <NotDocumented />}
          </p>
        </Section>

        {/* Why It Matters */}
        <Section title={t("Why It Matters — Executive Briefing")} icon={TrendingUp} testId="why">
          <dl>
            <Field label={t("What happened")} value={why.what_happened} testId="why-what" />
            <Field label={t("Why leadership should care")} value={why.why_leadership_should_care} testId="why-care" />
            <Field label={t("Current risk if no action")} value={why.current_risk_if_no_action} testId="why-risk" />
            <Field label={t("Recommended executive decision")} value={why.recommended_executive_decision} testId="why-decision" />
            <Field label={t("Expected outcome if implemented")} value={why.expected_outcome_if_implemented} testId="why-outcome" />
          </dl>
          <p className="mt-2 text-[11px] italic text-slate-500 border-l-2 border-slate-200 pl-2">
            {why.source_note || ""}
          </p>
        </Section>

        {/* Timeline */}
        <Section title={t("Timeline (traceable)")} icon={ScrollText} testId="timeline">
          {timeline.length === 0 ? <NotDocumented /> : (
            <ol className="space-y-2" data-testid="exec-report-timeline-list">
              {timeline.map((e) => (
                <li key={e.id || `${e.at}-${e.event_type}`} className="rounded-md border border-slate-200 bg-slate-50 p-2" data-testid={`exec-report-timeline-${e.id || e.event_type}`}>
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                    <span>{_fmt(e.at) || e.at}</span>
                    <span>{e.actor_name || e.actor_role || "—"}</span>
                  </div>
                  <div className="text-sm text-slate-900">{e.summary}</div>
                </li>
              ))}
            </ol>
          )}
        </Section>

        {/* Evidence chain */}
        <Section title={t("Evidence Chain")} icon={Lock} testId="evidence">
          {evidence.length === 0 ? <NotDocumented /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="exec-report-evidence-table">
                <thead className="text-[10px] uppercase tracking-widest text-slate-500 font-mono">
                  <tr>
                    <th className="text-left py-1 pr-3">{t("Item")}</th>
                    <th className="text-left py-1 pr-3">{t("Type")}</th>
                    <th className="text-left py-1 pr-3">{t("Uploaded by")}</th>
                    <th className="text-left py-1 pr-3">{t("Uploaded at")}</th>
                    <th className="text-left py-1">{t("Status")}</th>
                  </tr>
                </thead>
                <tbody>
                  {evidence.map((e) => (
                    <tr key={e.id} className="border-t border-slate-100" data-testid={`exec-report-evidence-${e.id}`}>
                      <td className="py-1.5 pr-3">{e.label || e.evidence_type}</td>
                      <td className="py-1.5 pr-3 font-mono text-xs">{e.evidence_type}</td>
                      <td className="py-1.5 pr-3">{e.added_by || "—"}</td>
                      <td className="py-1.5 pr-3 font-mono text-xs">{_fmt(e.added_at)}</td>
                      <td className={`py-1.5 ${e.withdrawn ? "text-red-700" : "text-emerald-700"}`}>
                        {e.withdrawn ? t("Withdrawn") : t("Active")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        {/* CAPA */}
        <Section title={t("Corrective Actions")} icon={ShieldCheck} testId="capa">
          {(capa.items || []).length === 0 ? <NotDocumented /> : (
            <>
              <ul className="space-y-1.5" data-testid="exec-report-capa-list">
                {capa.items.map((a) => (
                  <li key={a.id} className="flex items-center justify-between rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
                    <div>
                      <div className="font-semibold text-slate-900 text-sm">{a.title}</div>
                      <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500">
                        {a.action_class} · {a.state} {a.assigned_to_name ? `· ${a.assigned_to_name}` : ""}
                      </div>
                    </div>
                    {a.due_at && <div className="font-mono text-xs text-slate-600">{t("Due")}: {_fmt(a.due_at)}</div>}
                  </li>
                ))}
              </ul>
              <div className="mt-2 text-xs text-slate-600" data-testid="exec-report-capa-totals">
                {t("Total")} {capa.totals.total || 0} · {t("Open")} {capa.totals.open || 0} · {t("Verified")} {capa.totals.verified || 0}
              </div>
            </>
          )}
        </Section>

        {/* Regulatory bucket */}
        <Section title={t("Regulatory · Insurance · Legal Review")} icon={FileText} testId="regulatory">
          <h3 className="text-[11px] uppercase tracking-widest font-mono text-slate-500 mt-2 mb-1">{t("OSHA")}</h3>
          <dl>
            <Field
              label={t("Recordable")}
              value={
                reg.osha_review?.osha_recordable === true ? t("Yes")
                : reg.osha_review?.osha_recordable === false ? t("No")
                : ""
              }
              testId="reg-osha-recordable"
            />
            <Field label={t("Case number")} value={reg.osha_review?.osha_case_number} testId="reg-osha-case" mono />
            <Field label={t("Reason")} value={reg.osha_review?.recordability_reason} testId="reg-osha-reason" />
          </dl>
          <h3 className="text-[11px] uppercase tracking-widest font-mono text-slate-500 mt-3 mb-1">{t("Insurance / Workers Comp")}</h3>
          <dl>
            <Field label={t("Days lost")} value={reg.insurance_review?.workers_comp_days_lost} testId="reg-wc-lost" />
            <Field label={t("Days restricted")} value={reg.insurance_review?.workers_comp_days_restricted} testId="reg-wc-restricted" />
            <Field label={t("Medical summary")} value={reg.insurance_review?.medical_summary} testId="reg-wc-med" />
          </dl>
          <h3 className="text-[11px] uppercase tracking-widest font-mono text-slate-500 mt-3 mb-1">{t("Legal / Agency")}</h3>
          <dl>
            <Field label={t("Police case number")} value={reg.legal_review?.police_case_number} testId="reg-legal-case" mono />
          </dl>
          <h3 className="text-[11px] uppercase tracking-widest font-mono text-slate-500 mt-3 mb-1">{t("Executive")}</h3>
          <dl>
            <Field label={t("Reviewer")} value={reg.executive_review?.reviewer} testId="reg-exec-reviewer" />
            <Field label={t("Notes")} value={reg.executive_review?.notes} testId="reg-exec-notes" />
          </dl>
        </Section>

        {/* Track 19.37 · Attention Signals — attention-only. Not a decision. */}
        {attention && (
          <Section title={t("Attention Signals")} icon={AlertTriangle} testId="attention">
            <div className="mb-3 flex flex-wrap gap-2 items-center" data-testid="exec-report-attention-header">
              <span className="font-display text-2xl font-black text-slate-900" data-testid="exec-report-attention-score">
                {attention.overall_attention_score ?? 0}
              </span>
              <span className={`font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full border ${
                attention.attention_level === "high" ? "border-red-300 bg-red-50 text-red-800" :
                attention.attention_level === "medium" ? "border-amber-300 bg-amber-50 text-amber-800" :
                "border-slate-300 bg-slate-50 text-slate-700"
              }`} data-testid="exec-report-attention-level">
                {t("Review Priority")} · {(attention.attention_level || "low").toUpperCase()}
              </span>
              <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">
                {t("Needs Safety Review")}
              </span>
            </div>
            <ul className="space-y-1.5" data-testid="exec-report-attention-list">
              {(attention.signals || []).filter(s => (s.score || 0) > 0).map((s) => (
                <li key={s.signal_key} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm" data-testid={`exec-report-attention-signal-${s.signal_key}`}>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-slate-900">{t(s.label)}</span>
                    <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">
                      {t("confidence")} · {s.confidence}
                    </span>
                    <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">
                      {t("owner")} · {s.recommended_review_owner}
                    </span>
                  </div>
                  <div className="text-xs text-slate-700 mt-1">{s.rationale}</div>
                  {(s.source_fields || []).length > 0 && (
                    <div className="text-[10px] font-mono text-slate-500 mt-1" data-testid={`exec-report-attention-source-${s.signal_key}`}>
                      {t("Source fields")}: {s.source_fields.join(" · ")}
                    </div>
                  )}
                </li>
              ))}
              {(attention.signals || []).filter(s => (s.score || 0) > 0).length === 0 && (
                <li className="text-sm italic text-slate-500" data-testid="exec-report-attention-none">
                  {t("No attention signals detected on this case.")}
                </li>
              )}
            </ul>
            {(attention.missing_inputs || []).length > 0 && (
              <div className="mt-3 text-[11px] font-mono text-slate-500" data-testid="exec-report-attention-missing">
                {t("Missing inputs")}: {attention.missing_inputs.join(" · ")}
              </div>
            )}
            <p className="mt-3 text-[11px] italic text-slate-500 border-l-2 border-slate-300 pl-2" data-testid="exec-report-attention-notice">
              {attention.no_auto_decision_notice}
            </p>
          </Section>
        )}

        {/* Operational Intelligence */}
        <Section title={t("Operational Intelligence")} icon={TrendingUp} testId="ops">
          <dl>
            <Field label={t("Days open")} value={ops.days_open} testId="ops-days-open" />
            <Field label={t("Time to intake (days)")} value={ops.time_to_intake_days} testId="ops-tt-intake" />
            <Field label={t("Time to corrective action (days)")} value={ops.time_to_capa_days} testId="ops-tt-capa" />
            <Field label={t("Time to closure (days)")} value={ops.time_to_closure_days} testId="ops-tt-close" />
          </dl>
        </Section>

        {/* Readiness */}
        <Section title={t("Readiness Score (explainable)")} icon={ShieldCheck} testId="readiness">
          <div className="mb-3">
            <span className="font-display text-2xl font-black text-slate-900" data-testid="exec-report-readiness-pct">
              {readiness.overall_pct ?? 0}%
            </span>
            <span className="ml-2 font-mono text-[11px] uppercase tracking-widest text-slate-500">
              {readiness.band || "low"}
            </span>
          </div>
          <ul className="space-y-1" data-testid="exec-report-readiness-list">
            {(readiness.sub_scores || []).map((sub) => (
              <li key={sub.key} className="text-sm" data-testid={`exec-report-readiness-sub-${sub.key}`}>
                <span className="font-mono text-[11px] uppercase tracking-widest text-slate-500 mr-2">{sub.key}</span>
                <span className="font-semibold text-slate-900">{sub.num}/{sub.den} · {sub.pct}%</span>
                <span className="text-slate-600"> — {sub.rationale}</span>
              </li>
            ))}
          </ul>
        </Section>

        {/* Decisions */}
        <Section title={t("Decision Records")} icon={Users} testId="decisions">
          {decisions.length === 0 ? <NotDocumented /> : (
            <ul className="space-y-1.5" data-testid="exec-report-decisions-list">
              {decisions.map((d) => (
                <li key={d.id} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                  <div className="flex justify-between text-[11px] font-mono text-slate-500">
                    <span>{_fmt(d.at)}</span>
                    <span>{d.actor_name || d.actor_role || "—"}</span>
                  </div>
                  <div className="font-semibold text-slate-900">{d.decision}</div>
                  {(d.from_state || d.to_state) && (
                    <div className="text-xs text-slate-600 font-mono">{d.from_state} → {d.to_state}</div>
                  )}
                  {d.reason && <div className="text-xs text-slate-700 mt-1">{t("Reason")}: {d.reason}</div>}
                </li>
              ))}
            </ul>
          )}
        </Section>

        {(model.missing_fields || []).length > 0 && (
          <Section title={t("Documentation gaps")} icon={AlertTriangle} testId="gaps">
            <ul className="text-sm text-slate-700 list-disc pl-5" data-testid="exec-report-missing-list">
              {model.missing_fields.map((k) => (
                <li key={k} className="font-mono text-xs">{k}</li>
              ))}
            </ul>
          </Section>
        )}

        <p className="text-[11px] text-slate-500 font-mono uppercase tracking-widest" data-testid="exec-report-model-version">
            {t("Prepared")} · {_fmt(model.generated_at)}
        </p>
      </main>
    </div>
  );
}
