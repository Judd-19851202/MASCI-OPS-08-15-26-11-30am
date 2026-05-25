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
// Storage key: `masci.crew-memory.daily-report.v1`
// (single slot per device · matches Phase 31.1 spec example "yesterday's setup")

const STORAGE_KEY = "masci.crew-memory.daily-report.v1";
const TTL_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
const SCHEMA_VERSION = 1;

// --- internals ----------------------------------------------------------

function _now() { return Date.now(); }

function _safeJson(raw) {
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

function _writeRaw(snapshot) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
  } catch {
    /* localStorage unavailable — calm degrade */
  }
  return snapshot;
}

function _stripCrewRow(row) {
  if (!row || typeof row !== "object") return null;
  const name = (row.name || "").trim();
  const trade = (row.trade || "").trim();
  if (!name) return null;
  return { name, trade };
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
 * Returns the persisted record (with timestamps + nickname).
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
  const record = {
    ...clean,
    nickname: (nickname || "").trim().slice(0, 60),
    savedAt: _now(),
    lastUsedAt: _now(),
  };
  return _writeRaw(record);
}

/**
 * Returns the persisted snapshot if present + not expired, else null.
 * Reads are silent — they never mutate the entry.
 */
export function loadCrewSetup() {
  const rec = _safeJson(
    typeof localStorage !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null
  );
  if (!rec) return null;
  if (rec.schemaVersion !== SCHEMA_VERSION) {
    // Old shape · drop it silently so the user starts blank.
    clearCrewSetup();
    return null;
  }
  const savedAt = rec.savedAt || 0;
  if (_now() - savedAt > TTL_MS) {
    clearCrewSetup();
    return null;
  }
  return rec;
}

/** Explicit operator action · matches "Clear Saved Setup" prompt button. */
export function clearCrewSetup() {
  try { localStorage.removeItem(STORAGE_KEY); } catch { /* noop */ }
}

/** Optional nickname rename · returns the updated record or null. */
export function renameCrewSetup(nickname) {
  const rec = loadCrewSetup();
  if (!rec) return null;
  rec.nickname = (nickname || "").trim().slice(0, 60);
  return _writeRaw(rec);
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
  const rec = loadCrewSetup();
  if (rec) {
    rec.lastUsedAt = _now();
    _writeRaw(rec);
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
export const __TESTING__ = { STORAGE_KEY, TTL_MS, SCHEMA_VERSION };
