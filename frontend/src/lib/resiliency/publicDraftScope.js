function safeStorage() {
  try {
    if (typeof window !== "undefined" && window.localStorage) return window.localStorage;
  } catch {
    // ignore
  }
  return null;
}

function cleanBase(formKeyBase = "") {
  return String(formKeyBase || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function storageKey(formKeyBase = "") {
  return `masci.public-draft.active-session.${cleanBase(formKeyBase) || "unknown"}.v1`;
}

function mintSessionId() {
  const random = Math.random().toString(36).slice(2, 10);
  return `pds.${Date.now().toString(36)}.${random}`;
}

export function isPublicDraftSessionId(value = "") {
  return /^pds\.[a-z0-9]+\.[a-z0-9]+$/i.test(String(value || "").trim());
}

export function getActivePublicDraftSession(formKeyBase = "") {
  const storage = safeStorage();
  if (!storage) return "";
  try {
    const value = String(storage.getItem(storageKey(formKeyBase)) || "").trim();
    return isPublicDraftSessionId(value) ? value : "";
  } catch {
    return "";
  }
}

export function ensureActivePublicDraftSession(formKeyBase = "", existing = "") {
  const current = String(existing || "").trim();
  if (isPublicDraftSessionId(current)) return current;
  const storage = safeStorage();
  const fromStorage = getActivePublicDraftSession(formKeyBase);
  if (fromStorage) return fromStorage;
  const minted = mintSessionId();
  try { storage?.setItem(storageKey(formKeyBase), minted); } catch { /* ignore */ }
  return minted;
}

export function clearActivePublicDraftSession(formKeyBase = "", expected = "") {
  const storage = safeStorage();
  if (!storage) return;
  try {
    const current = String(storage.getItem(storageKey(formKeyBase)) || "").trim();
    if (!expected || !current || current === String(expected).trim()) {
      storage.removeItem(storageKey(formKeyBase));
    }
  } catch {
    // ignore
  }
}

export function buildPublicDraftSessionScope(sessionId = "") {
  const cleaned = String(sessionId || "").trim();
  return cleaned ? `session::${cleaned}` : "";
}

export function buildPublicDraftScopedFormKey(formKeyBase = "", sessionId = "") {
  const scope = buildPublicDraftSessionScope(sessionId);
  return scope ? `${formKeyBase}::${scope}` : formKeyBase;
}

function hasMeaningfulValue(value) {
  if (value == null) return false;
  if (typeof value === "string") return value.trim().length > 0;
  if (typeof value === "number") return Number.isFinite(value) && value !== 0;
  if (typeof value === "boolean") return value;
  if (Array.isArray(value)) return value.some((entry) => hasMeaningfulValue(entry));
  if (typeof value === "object") return Object.values(value).some((entry) => hasMeaningfulValue(entry));
  return false;
}

export function hasMeaningfulPublicDraft(payload = {}, ignoredKeys = []) {
  const ignore = new Set(ignoredKeys);
  return Object.entries(payload || {}).some(([key, value]) => !ignore.has(key) && hasMeaningfulValue(value));
}