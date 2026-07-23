import { getDeviceId } from "./deviceId";

export const DAILY_REPORT_FORM_BASE = "daily-report";

function clean(value, fallback) {
  const out = String(value || "").trim();
  return out || fallback;
}

function cleanOperator(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

export function buildDailyReportInstanceScope(data = {}) {
  const project = clean(data.project_number, "unassigned");
  const reportDate = clean(data.report_date, "undated");
  const reportInstance = clean(data.report_instance, "primary");
  const operator = cleanOperator(data.prepared_by || data.superintendent || "") || "shared";
  return `${project}::${reportDate}::${reportInstance}::${operator}`;
}

export function buildDailyReportScopedFormKey(data = {}) {
  return `${DAILY_REPORT_FORM_BASE}::${buildDailyReportInstanceScope(data)}`;
}

export function buildDailyReportTelemetryContext(data = {}, actorId = "") {
  return {
    formKey: buildDailyReportScopedFormKey(data),
    scope: buildDailyReportInstanceScope(data),
    actorId: actorId || getDeviceId(),
    deviceId: getDeviceId(),
  };
}
