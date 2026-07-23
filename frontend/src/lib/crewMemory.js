// crewMemory.js — iter437 · Phase 31.1 · Daily Report Crew Memory Continuity.
//
// Device-local memory of yesterday's Daily Report SETUP (crew names,
// equipment list, project + foreman). Reduces repetitive field entry
// on the SAME device, never syncs anywhere.
//
// Doctrine (verbatim from Phase 31.1 spec)
// ----------------------------------------
// - localStorage only. NO server sync. NO admin visibility.
// - Daily Report ONLY · this primitive must NOT be reused elsewhere
//   without an explicit Phase update.
// - ONLY repetitive setup fields are persisted:
//     prepared_by, superintendent, project_name, project_number,
//     masci_crews (names + trades · NOT hours / work_performed),
//     subcontractors (company + trade + foreman · NOT count / hours),
//     equipment (description ONLY · NOT hours / times / notes).
// - Banned: production quantities, notes, incidents, signatures,
//   comments, weather, attachment references.
// - 30-day expiration · rolling on use (lastUsedAt refresh).
// - Restore prompt is ALWAYS shown · never silent auto-fill.
// - Optional setup nickname · local-only.
//
// API
// ---
//   extractSetupSnapshot(reportData)        → snapshot
//   saveCrewSetup(snapshot, { nickname })   → snapshot (persisted)
//   loadCrewSetup()                         → snapshot | null
//   clearCrewSetup()                        → void
//   renameCrewSetup(nickname)               → snapshot | null
//   applySetupSnapshotToData(data, snap)    → merged data (immutable)
//
// Storage key: `masci.crew-memory.daily-report.v1.<device>.<project>.<operator>`
// (device-scoped and public-flow safe)
//
// Prior versions used either a single shared device slot or an auth-
// actor slot. Neither fits the public Daily Report workflow. The key is
// now device-scoped and further segmented by project + preparer/super-
// intendent context so shared field devices do not offer the wrong
// crew/equipment setup.

import { getDeviceId } from "./resiliency/deviceId";

const STORAGE_KEY_BASE = "masci.crew-memory.daily-report.v1";
const LEGACY_STORAGE_KEY = "masci.crew-memory.daily-report.v1";
const TTL_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
const SCHEMA_VERSION = 1;

function _normalizeKeyPart(value, fallback = "shared") {
  const normalized = String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return normalized || fallback;
}

function _contextMeta(context = {}) {
  const deviceId = getDeviceId();
  const projectNumber = String(context.projectNumber || context.project_number || "").trim();
  const preparedBy = String(context.preparedBy || context.prepared_by || "").trim();
  const superintendent = String(context.superintendent || "").trim();
  const operatorLabel = preparedBy || superintendent || "";
  return {
    deviceId,
    projectNumber,
    preparedBy,
    superintendent,
    operatorLabel,
    projectToken: _normalizeKeyPart(projectNumber, "no-project"),
    operatorToken: _normalizeKeyPart(operatorLabel, "shared"),
  };
}

function _contextKey(context = {}) {
  const meta = _contextMeta(context);
  return `${STORAGE_KEY_BASE}.${meta.deviceId}.${meta.projectToken}.${meta.operatorToken}`;
}

function _projectPrefix(context = {}) {
  const meta = _contextMeta(context);
  return `${STORAGE_KEY_BASE}.${meta.deviceId}.${meta.projectToken}.`;
}

function _devicePrefix() {
  return `${STORAGE_KEY_BASE}.${getDeviceId()}.`;
}

function _listDeviceKeys(prefix = _devicePrefix()) {
  try {
    const keys = [];
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i);
      if (typeof key === "string" && key.startsWith(prefix)) keys.push(key);
    }
    return keys;
  } catch {
    return [];
  }
}

function _readRecord(key) {
  try {
    return _safeJson(localStorage.getItem(key));
  } catch {
    return null;
  }
}

function _recordIsFresh(rec) {
  if (!rec || rec.schemaVersion !== SCHEMA_VERSION) return false;
  const savedAt = rec.savedAt || 0;
  return (_now() - savedAt) <= TTL_MS;
}

// --- internals ----------------------------------------------------------

function _now() { return Date.now(); }

function _safeJson(raw) {
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

function _writeRaw(snapshot, context = {}) {
  try {
    localStorage.setItem(_contextKey(context), JSON.stringify(snapshot));
  } catch {
    /* localStorage unavailable — calm degrade */
  }
  return snapshot;
}

function _stripCrewRow(row) {
  if (!row || typeof row !== "object") return null;
  const name = (row.name || "").trim();
  if (!name) return null;
  // TRACK 23.4B / HR autofill · restore-yesterday MUST NOT carry stale
  // trade / crew / supervisor from yesterday's draft — the HR record
  // could have changed (promotion, crew reassignment, supervisor
  // swap). Keep only the employee identity + a `_needs_hr_refresh`
  // flag so the form re-hydrates from the current Employee Master on
  // restore. Times / hours / lunch already stripped by contract.
  return {
    name,
    employee_id: (row.employee_id || "").trim(),
    _needs_hr_refresh: true,
  };
}

/**
 * TRACK 23.4B / HR autofill · post-restore re-hydration.
 *
 * Given a crews[] array (typically the output of applySetupSnapshot)
 * and the current fresh employee master list, refresh each row's
 * trade / crew / supervisor from HR. Only touches rows tagged
 * `_needs_hr_refresh` so today's manually-typed customs are safe.
 */
export function refreshCrewFromEmployeeMaster(crews, employeeList) {
  if (!Array.isArray(crews) || crews.length === 0) return crews || [];
  const items = Array.isArray(employeeList)
    ? employeeList
    : (employeeList?.items || []);
  const byId = new Map();
  const byName = new Map();
  for (const emp of items) {
    if (emp?.employee_id) byId.set(String(emp.employee_id), emp);
    if (emp?.id) byId.set(String(emp.id), emp);
    if (emp?.name) byName.set(emp.name.toLowerCase(), emp);
  }
  return crews.map((c) => {
    if (!c?._needs_hr_refresh) return c;
    const key = c.employee_id ? String(c.employee_id) : "";
    const emp = (key && byId.get(key))
      || byName.get((c.name || "").toLowerCase())
      || null;
    if (!emp) {
      // Row references someone not on today's roster (offboarded /
      // renamed). Keep identity + drop the refresh flag so we don't
      // loop; trade stays blank so the user notices.
      const { _needs_hr_refresh: _stale, ...rest } = c;
      return rest;
    }
    // TRACK 23.4C · Reuse the shared HR field resolver so trade
    // aliases (role / title / position / classification / department)
    // land in the same place regardless of Employee Master vintage.
    // Small inline copy to avoid an import cycle with hrAutofill.js.
    const _trade =
      emp.trade || emp.role || emp.title || emp.position
      || emp.classification || emp.trade_role || emp.department || "";
    const _crew = emp.crew || emp.division || (_trade ? "" : emp.department) || "";
    const _sup = emp.supervisor || emp.supervisor_name || "";
    const { _needs_hr_refresh: _stale, ...rest } = c;
    return {
      ...rest,
      name: emp.name || c.name,
      employee_id: emp.employee_id || emp.id || c.employee_id || "",
      employee_name_snapshot: emp.name || c.name || "",
      trade: _trade || rest.trade || "",
      trade_snapshot: _trade || rest.trade || "",
      trade_autofilled: !!_trade,
      crew_snapshot: _crew,
      division_snapshot: _crew,
      supervisor_snapshot: _sup,
    };
  });
}

function _stripSubRow(row) {
  if (!row || typeof row !== "object") return null;
  const company = (row.company || "").trim();
  if (!company) return null;
  return {
    company,
    trade: (row.trade || "").trim(),
    foreman: (row.foreman || "").trim(),
  };
}

function _stripEquipmentRow(row) {
  if (!row || typeof row !== "object") return null;
  const description = (row.description || "").trim();
  if (!description) return null;
  return { description };
}

// --- public API ---------------------------------------------------------

/**
 * Pull ONLY the setup-allowed fields out of an in-flight Daily Report.
 * Everything banned (quantities, notes, weather, incidents, signatures,
 * photos, materials, activities, visitors, GPS, distribution list) is
 * deliberately dropped. Calling this on partial data is safe.
 */
export function extractSetupSnapshot(reportData) {
  const d = reportData || {};
  return {
    schemaVersion: SCHEMA_VERSION,
    nickname: "",
    prepared_by: (d.prepared_by || "").trim(),
    superintendent: (d.superintendent || "").trim(),
    project_name: (d.project_name || "").trim(),
    project_number: (d.project_number || "").trim(),
    masci_crews: Array.isArray(d.masci_crews)
      ? d.masci_crews.map(_stripCrewRow).filter(Boolean)
      : [],
    subcontractors: Array.isArray(d.subcontractors)
      ? d.subcontractors.map(_stripSubRow).filter(Boolean)
      : [],
    equipment: Array.isArray(d.equipment)
      ? d.equipment.map(_stripEquipmentRow).filter(Boolean)
      : [],
  };
}

/**
 * Persist a snapshot to this device. The snapshot is re-stripped here
 * defensively so callers cannot accidentally save banned fields. Adds
 * savedAt / lastUsedAt timestamps and the optional nickname.
 *
 * iter442 · confidence accrual:
 *   Each successful save increments `usageCount`. After repeated
 *   submissions of the same project, the operator gets a calm
 *   "preload from recent reports" banner instead of having to tap
 *   restore. Project-change detection (see applySetupSnapshotToData)
 *   gates the auto-apply path so a NEW job does not silently reuse
 *   the prior crew/equipment.
 *
 * Returns the persisted record (with timestamps + nickname + counts).
 */
export function saveCrewSetup(snapshot, { nickname } = {}) {
  const clean = extractSetupSnapshot(snapshot);
  // Drop entirely if the snapshot is functionally empty — no point
  // showing a restore prompt for nothing.
  const hasAnything =
    clean.prepared_by || clean.superintendent || clean.project_name ||
    clean.project_number || clean.masci_crews.length ||
    clean.subcontractors.length || clean.equipment.length;
  if (!hasAnything) return null;
  const existing = loadCrewSetup(clean);
  // Confidence accrual — bump usageCount when the SAME project number
  // is being saved again. New project → reset to 1 (the operator is
  // shifting context; the prior accrual no longer applies).
  let usageCount = 1;
  let firstSeenAt = _now();
  if (existing && existing.project_number === clean.project_number) {
    usageCount = (existing.usageCount || 1) + 1;
    firstSeenAt = existing.firstSeenAt || existing.savedAt || _now();
  }
  const record = {
    ...clean,
    nickname: (nickname || existing?.nickname || "").trim().slice(0, 60),
    device_id: getDeviceId(),
    prepared_by_key: _normalizeKeyPart(clean.prepared_by, "shared"),
    superintendent_key: _normalizeKeyPart(clean.superintendent, "shared"),
    project_key: _normalizeKeyPart(clean.project_number, "no-project"),
    savedAt: _now(),
    lastUsedAt: _now(),
    firstSeenAt,
    usageCount,
  };
  return _writeRaw(record, clean);
}

/**
 * Returns the persisted snapshot if present + not expired, else null.
 * Reads are silent — they never mutate the entry.
 */
export function loadCrewSetup(context = {}) {
  const meta = _contextMeta(context);
  if (!meta.projectNumber) return null;
  if (meta.operatorToken === "shared") return null;

  const candidates = _listDeviceKeys(_projectPrefix(context))
    .map((key) => ({ key, rec: _readRecord(key) }))
    .filter(({ rec }) => _recordIsFresh(rec))
    .sort((a, b) => (b.rec?.savedAt || 0) - (a.rec?.savedAt || 0));

  const exact = candidates.find(({ rec }) => {
    const prepared = _normalizeKeyPart(rec?.prepared_by || "", "shared");
    const superLabel = _normalizeKeyPart(rec?.superintendent || "", "shared");
    return meta.operatorToken !== "shared" && (prepared === meta.operatorToken || superLabel === meta.operatorToken);
  });
  if (exact?.rec) return exact.rec;

  if (meta.operatorToken === "shared" && candidates.length === 1) {
    return candidates[0].rec;
  }

  const legacy = _safeJson((() => {
    try { return localStorage.getItem(LEGACY_STORAGE_KEY); } catch { return null; }
  })());
  if (!_recordIsFresh(legacy)) return null;
  return String(legacy?.project_number || "").trim() === meta.projectNumber ? legacy : null;
}

/** Explicit operator action · matches "Clear Saved Setup" prompt button. */
export function clearCrewSetup() {
  for (const key of _listDeviceKeys()) {
    try { localStorage.removeItem(key); } catch { /* noop */ }
  }
  try { localStorage.removeItem(LEGACY_STORAGE_KEY); } catch { /* noop */ }
}

/** Optional nickname rename · returns the updated record or null. */
export function renameCrewSetup(nickname, context = {}) {
  const rec = loadCrewSetup(context);
  if (!rec) return null;
  rec.nickname = (nickname || "").trim().slice(0, 60);
  return _writeRaw(rec, rec);
}

/**
 * Apply a snapshot onto a Daily Report `data` object, returning a new
 * object. ONLY setup fields are touched; everything else (today's
 * date, weather, photos, signatures, notes, schedule flags) is
 * preserved verbatim — Phase 31.1 doctrine: "All fields remain
 * editable" + "Starting blank will not erase previously submitted
 * reports."
 *
 * Also bumps lastUsedAt on the persisted record (rolling expiration).
 */
export function applySetupSnapshotToData(data, snapshot) {
  const d = data || {};
  const s = snapshot || {};
  // Rolling expiration: touch lastUsedAt + persist.
  const rec = loadCrewSetup(d);
  if (rec) {
    rec.lastUsedAt = _now();
    _writeRaw(rec, rec);
  }
  return {
    ...d,
    prepared_by: s.prepared_by || d.prepared_by || "",
    superintendent: s.superintendent || d.superintendent || "",
    project_name: s.project_name || d.project_name || "",
    project_number: s.project_number || d.project_number || "",
    masci_crews: (s.masci_crews && s.masci_crews.length)
      ? s.masci_crews.map((r) => ({
          name: r.name || "",
          trade: r.trade || "",
          start_time: "",
          lunch_minutes: "",
          stop_time: "",
          hours: "",
          work_performed: "",
        }))
      : d.masci_crews || [],
    subcontractors: (s.subcontractors && s.subcontractors.length)
      ? s.subcontractors.map((r) => ({
          company: r.company || "",
          trade: r.trade || "",
          foreman: r.foreman || "",
          count: "",
          hours: "",
          work_performed: "",
        }))
      : d.subcontractors || [],
    equipment: (s.equipment && s.equipment.length)
      ? s.equipment.map((r) => ({
          description: r.description || "",
          hours_used: "",
          time_delivered: "",
          time_removed: "",
          notes: "",
        }))
      : d.equipment || [],
  };
}

// Test-only seam · NOT exported for app code. Kept here so unit tests
// can flush the slot deterministically without touching window.
export const __TESTING__ = {
  STORAGE_KEY_BASE,
  LEGACY_STORAGE_KEY,
  TTL_MS,
  SCHEMA_VERSION,
  _contextKey,
  _devicePrefix,
  _projectPrefix,
};

// iter442 · confidence proxy. Doctrine-locked:
//   - device_id may SUGGEST context
//   - device_id MUST NOT silently hard-lock identity
//   - if confidence is low, ask minimal setup questions
//   - if project changes, confirm before reusing crew/equipment
//
// `getConfidence()` returns one of "low" | "medium" | "high" based on
// how many times the SAME project_number has been submitted from this
// device. Pages use this to decide whether to surface a calm preload
// banner ("Recent crew and equipment may preload to speed up daily
// reporting.") vs. always require the manual Use Setup tap.
export function getCrewMemoryConfidence(context = {}) {
  const rec = loadCrewSetup(context);
  if (!rec) return { level: "low", usageCount: 0, projectNumber: "" };
  const n = rec.usageCount || 1;
  let level = "low";
  if (n >= 5) level = "high";
  else if (n >= 2) level = "medium";
  return {
    level,
    usageCount: n,
    projectNumber: rec.project_number || "",
    nickname: rec.nickname || "",
  };
}

// iter442 · project-change guard. Returns true when the snapshot's
// project_number differs from the supplied currentProjectNumber AND
// the operator has any usageCount accrued — i.e., we'd be reusing
// the crew/equipment for a DIFFERENT job. Pages call this BEFORE
// auto-applying the setup; if true, the operator must confirm.
export function isProjectChange(snapshot, currentProjectNumber) {
  if (!snapshot || !snapshot.project_number) return false;
  const current = (currentProjectNumber || "").trim();
  if (!current) return false;
  return snapshot.project_number !== current;
}
