import React from "react";
import { CalendarRange } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export const ScheduleDailyWorkPlanPanel = ({
  t,
  planDraft,
  onPlanDraft,
  onPlanItemChange,
  onSavePlan,
  working = false,
}) => {
  const items = planDraft?.items || [];
  return (
    <section className="rounded-[1.75rem] border border-white/30 bg-white/85 p-5 shadow-sm" data-testid="pm-project-schedule-daily-plan-section">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-black text-slate-900">{t("Daily work plan")}</h2>
          <p className="mt-1 text-sm text-slate-600">{t("Built from the approved schedule and rolling lookahead. Publishing today's plan does not change baseline or current schedule history.")}</p>
        </div>
        <Button type="button" onClick={onSavePlan} disabled={working} data-testid="pm-project-schedule-save-daily-plan-button">
          <CalendarRange className="mr-2 h-4 w-4" /> {working ? t("Working…") : t("Save day plan")}
        </Button>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="pm-daily-plan-date">{t("Work date")}</label>
          <Input id="pm-daily-plan-date" type="date" value={planDraft?.work_date || ""} onChange={(event) => onPlanDraft("work_date", event.target.value)} data-testid="pm-project-schedule-daily-plan-date-input" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="pm-daily-plan-status">{t("Plan status")}</label>
          <select id="pm-daily-plan-status" className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm" value={planDraft?.status || "draft"} onChange={(event) => onPlanDraft("status", event.target.value)} data-testid="pm-project-schedule-daily-plan-status-select">
            <option value="draft">{t("Draft")}</option>
            <option value="published">{t("Published")}</option>
            <option value="archived">{t("Archived")}</option>
          </select>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">{t("Planned activities")}</div>
          <div className="mt-2 text-2xl font-black text-slate-900" data-testid="pm-project-schedule-daily-plan-item-count">{items.length}</div>
        </div>
      </div>

      <Textarea className="mt-4" value={planDraft?.notes || ""} onChange={(event) => onPlanDraft("notes", event.target.value)} placeholder={t("What changed between the two-week lookahead and today's plan?")} data-testid="pm-project-schedule-daily-plan-notes-input" />

      <div className="mt-4 space-y-3">
        {items.map((item, index) => (
          <div key={item.plan_item_id || `${item.activity_id}-${index}`} className="rounded-[1.35rem] border border-slate-200 bg-slate-50 p-4" data-testid={`pm-project-schedule-daily-plan-row-${index}`}>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="font-semibold text-slate-900">{item.activity_id || "—"} · {item.activity_name || t("Planned activity")}</div>
                <div className="mt-1 text-xs text-slate-500">{item.work_package_id || "—"} · {item.project_cost_code || "—"}</div>
              </div>
              <Badge variant="secondary" data-testid={`pm-project-schedule-daily-plan-status-${index}`}>{item.actual_status || "not_started"}</Badge>
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <Input type="number" step="0.01" value={item.planned_quantity ?? 0} onChange={(event) => onPlanItemChange(index, "planned_quantity", event.target.value)} placeholder={t("Planned quantity")} data-testid={`pm-project-schedule-daily-plan-quantity-${index}`} />
              <Input type="number" step="0.01" value={item.planned_hours ?? 0} onChange={(event) => onPlanItemChange(index, "planned_hours", event.target.value)} placeholder={t("Planned hours")} data-testid={`pm-project-schedule-daily-plan-hours-${index}`} />
              <Input value={(item.planned_crews || []).map((row) => row.label || row.crew_id || "").filter(Boolean).join(", ")} disabled data-testid={`pm-project-schedule-daily-plan-crews-${index}`} />
              <Input value={(item.planned_equipment || []).map((row) => row.label || row.equipment_id || "").filter(Boolean).join(", ")} disabled data-testid={`pm-project-schedule-daily-plan-equipment-${index}`} />
            </div>

            <Textarea className="mt-3" value={item.daily_goal_note || ""} onChange={(event) => onPlanItemChange(index, "daily_goal_note", event.target.value)} placeholder={t("Daily execution goal, sequence note, or handoff reminder")} data-testid={`pm-project-schedule-daily-plan-goal-${index}`} />
          </div>
        ))}
        {items.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500" data-testid="pm-project-schedule-daily-plan-empty-state">{t("No day-plan items are ready for this date yet.")}</div> : null}
      </div>
    </section>
  );
};
