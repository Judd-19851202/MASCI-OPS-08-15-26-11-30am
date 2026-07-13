import { getDeviceId } from "./deviceId";

export const DAILY_REPORT_FORM_BASE = "daily-report-new";

function clean(value, fallback) {
  const out = String(value || "").trim();
  return out || fallback;
}

export function buildDailyReportInstanceScope(data = {}) {
  const project = clean(data.project_number, "unassigned");
  const reportDate = clean(data.report_date, "undated");
  const reportNumber = clean(data.report_number, "default");
  return `${project}::${reportDate}::${reportNumber}`;
}

export function buildDailyReportScopedFormKey(data = {}) {
  return `${DAILY_REPORT_FORM_BASE}::${buildDailyReportInstanceScope(data)}`;
}

export function buildDailyReportTelemetryContext(data = {}, actorId = "") {
  return {
    formKey: buildDailyReportScopedFormKey(data),
    scope: buildDailyReportInstanceScope(data),
    actorId: actorId || "",
    deviceId: getDeviceId(),
  };
}
