import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { operatorConfidenceLabel, operatorStatusLabel } from "@/lib/operatorLanguage";

function registrySummary(rows, label, t) {
  if (!rows?.length) return `${t("No")} ${label.toLowerCase()}`;
  const resolved = rows.filter((row) => row.registry_status === "resolved").length;
  return `${resolved}/${rows.length} ${label.toLowerCase()} ${t("resolved")}`;
}

export const ScheduleActualsWorkspace = ({
  t,
  candidates = [],
  candidateDrafts = {},
  onCandidateDraft,
  onCandidateAction,
  working = false,
}) => {
  return (
    <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-schedule-actuals-section">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-black text-slate-900">{t("Progress update review")}</h2>
          <p className="mt-1 text-sm text-slate-600">{t("Daily Reports stay the field source. PM review decides what updates the current schedule and forecast.")}</p>
        </div>
        <Badge variant="secondary" data-testid="pm-project-schedule-actuals-count-badge">{candidates.length}</Badge>
      </div>

      <div className="mt-4 space-y-4">
        {candidates.map((candidate, index) => {
          const draft = candidateDrafts[candidate.candidate_id] || {};
          const approved = candidate.approved_actual || {};
          const materialFlow = candidate.material_flow || {};
          return (
            <div key={candidate.candidate_id} className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-schedule-actual-card-${candidate.candidate_id}`}>
              <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{t("Proposed update")}</div>
                  <div className="mt-1 text-lg font-black text-slate-900">{candidate.work_block_title || t("Work block")}</div>
                  <div className="mt-1 text-sm text-slate-600">
                    <a className="underline decoration-dotted underline-offset-2" href={`/pm/daily/${candidate.source_report_id}`} data-testid={`pm-project-schedule-actual-report-link-${index}`}>
                      {candidate.source_report_number || candidate.source_report_id}
                    </a>
                    {" · "}
                    {candidate.report_date || "—"}
                    {candidate.work_block_id ? ` · ${candidate.work_block_id}` : ""}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant={candidate.review_status === "approved" ? "default" : "secondary"} data-testid={`pm-project-schedule-actual-status-${candidate.candidate_id}`}>
                    {operatorStatusLabel(candidate.review_status, t)}
                  </Badge>
                  <Badge variant={(candidate.activity_resolution?.confidence || "").includes("review") ? "outline" : "secondary"}>
                    {operatorConfidenceLabel(candidate.activity_resolution?.confidence || "review_required", t)}
                  </Badge>
                </div>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4 text-sm text-slate-700">
                <div className="rounded-2xl border border-slate-200 bg-white p-3" data-testid={`pm-project-schedule-actual-resolution-${candidate.candidate_id}`}>
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Matched activity")}</div>
                  <div className="mt-2 font-semibold text-slate-900">{candidate.activity_resolution?.resolved_activity_id || t("Needs PM decision")}</div>
                  <div className="text-xs text-slate-500">{candidate.activity_resolution?.resolved_activity_name || t("No reliable activity match yet")}</div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white p-3">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Installed quantity")}</div>
                  <div className="mt-2 font-semibold text-slate-900">{Number(candidate.actual_facts?.installed_quantity || 0).toFixed(2)} {candidate.actual_facts?.unit || ""}</div>
                  <div className="text-xs text-slate-500">{t("Labor rows")}: {(candidate.actual_facts?.labor_entries || []).length}</div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white p-3">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Linked records")}</div>
                  <div className="mt-2 text-xs text-slate-600">{registrySummary(candidate.equipment_registry_links, t("Equipment"), t)}</div>
                  <div className="text-xs text-slate-600">{registrySummary(candidate.supplier_registry_links, t("Suppliers"), t)}</div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white p-3">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Material movement")}</div>
                  <div className="mt-2 text-xs text-slate-600">{t("Delivered")}: {(materialFlow.delivered || []).length}</div>
                  <div className="text-xs text-slate-600">{t("Installed")}: {(materialFlow.installed || []).length}</div>
                  <div className="text-xs text-slate-600">{t("Outbound rows needing review")}: {(materialFlow.outbound_unclassified || []).length}</div>
                </div>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <Input value={draft.activity_id ?? approved.activity_id ?? candidate.activity_resolution?.resolved_activity_id ?? ""} onChange={(event) => onCandidateDraft(candidate.candidate_id, "activity_id", event.target.value)} placeholder={t("Activity ID")} data-testid={`pm-project-schedule-actual-activity-id-${candidate.candidate_id}`} />
                <Input value={draft.activity_name ?? approved.activity_name ?? candidate.activity_resolution?.resolved_activity_name ?? ""} onChange={(event) => onCandidateDraft(candidate.candidate_id, "activity_name", event.target.value)} placeholder={t("Activity name")} data-testid={`pm-project-schedule-actual-activity-name-${candidate.candidate_id}`} />
                <Input type="number" step="0.01" value={draft.approved_percent_complete ?? approved.approved_percent_complete ?? 0} onChange={(event) => onCandidateDraft(candidate.candidate_id, "approved_percent_complete", event.target.value)} placeholder={t("Percent complete")} data-testid={`pm-project-schedule-actual-percent-${candidate.candidate_id}`} />
                <Input type="number" step="0.01" value={draft.approved_installed_quantity ?? approved.approved_installed_quantity ?? candidate.actual_facts?.installed_quantity ?? 0} onChange={(event) => onCandidateDraft(candidate.candidate_id, "approved_installed_quantity", event.target.value)} placeholder={t("Installed quantity")} data-testid={`pm-project-schedule-actual-quantity-${candidate.candidate_id}`} />
                <Input type="date" value={draft.actual_start_date ?? approved.actual_start_date ?? candidate.report_date ?? ""} onChange={(event) => onCandidateDraft(candidate.candidate_id, "actual_start_date", event.target.value)} data-testid={`pm-project-schedule-actual-start-${candidate.candidate_id}`} />
                <Input type="date" value={draft.actual_finish_date ?? approved.actual_finish_date ?? ""} onChange={(event) => onCandidateDraft(candidate.candidate_id, "actual_finish_date", event.target.value)} data-testid={`pm-project-schedule-actual-finish-${candidate.candidate_id}`} />
                <select className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={draft.schedule_progress_status ?? approved.schedule_progress_status ?? "in_progress"} onChange={(event) => onCandidateDraft(candidate.candidate_id, "schedule_progress_status", event.target.value)} data-testid={`pm-project-schedule-actual-progress-status-${candidate.candidate_id}`}>
                  <option value="not_started">{t("Not started")}</option>
                  <option value="in_progress">{t("In progress")}</option>
                  <option value="completed">{t("Completed")}</option>
                </select>
                <Input value={candidate.actual_facts?.location || ""} disabled data-testid={`pm-project-schedule-actual-location-${candidate.candidate_id}`} />
              </div>

              <Textarea className="mt-3" value={draft.review_note ?? candidate.review_note ?? ""} onChange={(event) => onCandidateDraft(candidate.candidate_id, "review_note", event.target.value)} placeholder={t("Explain the PM decision, supporting evidence, or why this stays deferred.")} data-testid={`pm-project-schedule-actual-note-${candidate.candidate_id}`} />

              <div className="mt-4 flex flex-wrap justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => onCandidateAction(candidate.candidate_id, "needs_review")} disabled={working} data-testid={`pm-project-schedule-actual-needs-review-${candidate.candidate_id}`}>{t("Needs review")}</Button>
                <Button type="button" variant="outline" onClick={() => onCandidateAction(candidate.candidate_id, "defer")} disabled={working} data-testid={`pm-project-schedule-actual-defer-${candidate.candidate_id}`}>{t("Defer")}</Button>
                <Button type="button" variant="ghost" onClick={() => onCandidateAction(candidate.candidate_id, "reject")} disabled={working} data-testid={`pm-project-schedule-actual-reject-${candidate.candidate_id}`}>{t("Reject")}</Button>
                <Button type="button" onClick={() => onCandidateAction(candidate.candidate_id, "approve")} disabled={working} data-testid={`pm-project-schedule-actual-approve-${candidate.candidate_id}`}>{t("Approve progress update")}</Button>
              </div>
            </div>
          );
        })}
        {candidates.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="pm-project-schedule-actuals-empty-state">{t("No proposed progress updates yet. Submit a Daily Report with work blocks to start review.")}</div> : null}
      </div>
    </section>
  );
};
