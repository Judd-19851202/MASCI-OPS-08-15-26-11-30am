import { getDeviceId } from "./deviceId";

export const DAILY_REPORT_FORM_BASE = "daily-report";
const ACTIVE_DAILY_REPORT_SESSION_KEY = "masci.daily-report.active-session.v1";

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

function safeStorage() {
  try {
    if (typeof window !== "undefined" && window.localStorage) return window.localStorage;
  } catch {
    // ignore
  }
  return null;
}

function mintSessionId() {
  const random = Math.random().toString(36).slice(2, 10);
  return `drs.${Date.now().toString(36)}.${random}`;
}

export function getActiveDailyReportDraftSession() {
  const storage = safeStorage();
  if (!storage) return "";
  try {
    const value = String(storage.getItem(ACTIVE_DAILY_REPORT_SESSION_KEY) || "").trim();
    return /^drs\.[a-z0-9]+\.[a-z0-9]+$/i.test(value) ? value : "";
  } catch {
    return "";
  }
}

export function ensureActiveDailyReportDraftSession(existing = "") {
  const current = String(existing || "").trim();
  if (/^drs\.[a-z0-9]+\.[a-z0-9]+$/i.test(current)) return current;
  const storage = safeStorage();
  const fromStorage = getActiveDailyReportDraftSession();
  if (fromStorage) return fromStorage;
  const minted = mintSessionId();
  try { storage?.setItem(ACTIVE_DAILY_REPORT_SESSION_KEY, minted); } catch { /* ignore */ }
  return minted;
}

export function clearActiveDailyReportDraftSession(expected = "") {
  const storage = safeStorage();
  if (!storage) return;
  try {
    const current = String(storage.getItem(ACTIVE_DAILY_REPORT_SESSION_KEY) || "").trim();
    if (!expected || !current || current === String(expected).trim()) {
      storage.removeItem(ACTIVE_DAILY_REPORT_SESSION_KEY);
    }
  } catch {
    // ignore
  }
}

export function buildDailyReportSessionScope(sessionId = "") {
  return `session::${String(sessionId || "").trim()}`;
}

export function buildDailyReportInstanceScope(data = {}) {
  const draftSessionId = String(data.draft_session_id || "").trim();
  if (draftSessionId) return buildDailyReportSessionScope(draftSessionId);
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
