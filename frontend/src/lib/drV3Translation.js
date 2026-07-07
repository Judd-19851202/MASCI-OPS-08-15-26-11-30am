// TRACK 24.3 · Daily Report V3 · ES → EN submit-time translation client.
//
// When the operator submits DR V3 in Spanish, this module collects every
// natural-language free-text field on the payload, POSTs to
// `/api/translate/dr-v3-freetext`, and returns a NEW payload with those
// same field paths overwritten by the canonical English translation +
// `translation_metadata` attached for audit.
//
// Fail-closed: on ANY error the caller receives `{ok: false}` and MUST
// block submit. Never falls back to Spanish canonical storage.
import { api } from "@/lib/api";

// Canonical list of free-text field paths that must translate on submit.
// Paths using `[]` marker denote array-item fields whose `notes`/`description`
// child value should be translated per row.
const FREE_TEXT_PATHS = [
  { path: "general_notes", scalar: true },
  { path: "weather_summary", scalar: true },
  { path: "safety_narrative", scalar: true },
  { path: "tomorrow_plan", scalar: true },
  { path: "pm_attention_notes", scalar: true },
  { path: "ai_edit_narrative", scalar: true },
  { path: "ai_accepted_summary", scalar: true },
  { path: "incident_notes", scalar: true },
  { path: "schedule_delays_notes", scalar: true },
  { path: "weather_impact_notes", scalar: true },
  // Row-scoped free-text (per-element)
  { array: "activities", field: "notes" },
  { array: "activities", field: "description" },
  { array: "production", field: "notes" },
  { array: "production", field: "description" },
  { array: "constraints", field: "notes" },
  { array: "equipment", field: "notes" },
  { array: "subcontractors", field: "notes" },
  { array: "materials", field: "notes" },
  { array: "outbound_materials", field: "notes" },
  { array: "visitors", field: "purpose" },
  { array: "photo_captions", scalar_array: true },
];

// Excavation free-text sub-fields.
const EXCAVATION_TEXT_FIELDS = [
  "location_notes",
  "protective_system_notes",
  "soil_notes",
  "utilities_notes",
  "corrective_actions",
  "work_stop_reason",
  "atmosphere_readings",
  "water_mitigation",
];

// Preserve-token regex — anything matching one of these patterns must
// pass through the translator verbatim.
const _RE_UPPER_ID = /\b[A-Z0-9]{2,}(?:-[A-Z0-9]+)+\b/g; // e.g. DR-2026-00001, 24-12
const _RE_STATION = /\bSta\s*\d+\+\d+\b/gi;              // e.g. Sta 12+50
const _RE_NUMBER = /\b\d+(?:\.\d+)?\b/g;

function _collectPreserveTokens(payload) {
  const set = new Set();
  const add = (v) => {
    if (typeof v !== "string") return;
    const t = v.trim();
    if (t) set.add(t);
  };
  add(payload.project_number);
  add(payload.project_name);
  add(payload.report_number);
  add(payload.doc_id);
  add(payload.prepared_by);
  add(payload.superintendent);
  add(payload.safety_contact_person);

  (payload.masci_crews || []).forEach((row) => {
    add(row?.crew_name);
    add(row?.foreman);
    (row?.members || []).forEach((m) => {
      add(m?.name); add(m?.employee_id); add(m?.trade);
    });
  });
  (payload.equipment || []).forEach((e) => {
    add(e?.unit); add(e?.unit_number); add(e?.asset_id); add(e?.description);
  });
  (payload.subcontractors || []).forEach((s) => {
    add(s?.company); add(s?.name); add(s?.foreman); add(s?.contact);
  });
  (payload.materials || []).concat(payload.outbound_materials || []).forEach((m) => {
    add(m?.material); add(m?.carrier); add(m?.hauler);
    add(m?.ticket_number); add(m?.manifest_number); add(m?.destination);
    add(m?.unit); add(m?.unit_snapshot);
  });
  (payload.visitors || []).forEach((v) => {
    add(v?.name); add(v?.company);
  });
  const exc = payload.excavation || {};
  add(exc.project_area); add(exc.station_from); add(exc.station_to);
  add(exc.competent_person_name_snapshot);
  add(exc.competent_person_trade_snapshot);

  // Sweep every free-text value for embedded IDs/stations/numbers.
  const sweep = (text) => {
    if (typeof text !== "string") return;
    for (const rx of [_RE_UPPER_ID, _RE_STATION]) {
      const matches = text.match(rx) || [];
      matches.forEach(add);
    }
    // Number-only tokens ≥ 3 digits (station numbers, ticket refs).
    const nums = text.match(_RE_NUMBER) || [];
    nums.forEach((n) => { if (n.length >= 3) add(n); });
  };

  const walkFor = (obj, keys) => {
    keys.forEach((k) => sweep(obj?.[k]));
  };
  walkFor(payload, [
    "general_notes", "weather_summary", "safety_narrative",
    "tomorrow_plan", "pm_attention_notes", "incident_notes",
    "schedule_delays_notes", "weather_impact_notes",
    "ai_accepted_summary", "ai_edit_narrative",
  ]);
  (payload.masci_crews || []).forEach((row) => {
    (row?.members || []).forEach((m) => sweep(m?.notes));
  });
  ["activities", "production", "constraints", "equipment",
   "subcontractors", "materials", "outbound_materials"].forEach((arrKey) => {
    (payload[arrKey] || []).forEach((row) => {
      sweep(row?.notes); sweep(row?.description);
    });
  });
  (payload.visitors || []).forEach((v) => sweep(v?.purpose));
  EXCAVATION_TEXT_FIELDS.forEach((k) => sweep(exc[k]));

  return Array.from(set);
}

function _flattenFreeText(payload) {
  // Returns { fields: {path: text}, setters: [(newTextByPath) => void] }
  const fields = {};
  const setters = [];

  const putScalar = (path) => {
    const v = payload[path];
    if (typeof v === "string" && v.trim()) {
      fields[path] = v;
      setters.push((byPath) => {
        if (byPath[path] !== undefined) payload[path] = byPath[path];
      });
    }
  };

  FREE_TEXT_PATHS.forEach((spec) => {
    if (spec.scalar) {
      putScalar(spec.path);
    } else if (spec.scalar_array) {
      const arr = payload[spec.array];
      if (Array.isArray(arr)) {
        arr.forEach((v, i) => {
          if (typeof v === "string" && v.trim()) {
            const path = `${spec.array}[${i}]`;
            fields[path] = v;
            setters.push((byPath) => {
              if (byPath[path] !== undefined) payload[spec.array][i] = byPath[path];
            });
          }
        });
      }
    } else if (spec.array && spec.field) {
      const arr = payload[spec.array];
      if (Array.isArray(arr)) {
        arr.forEach((row, i) => {
          if (row && typeof row[spec.field] === "string" && row[spec.field].trim()) {
            const path = `${spec.array}[${i}].${spec.field}`;
            fields[path] = row[spec.field];
            setters.push((byPath) => {
              if (byPath[path] !== undefined) payload[spec.array][i][spec.field] = byPath[path];
            });
          }
        });
      }
    }
  });

  // Crew member notes
  (payload.masci_crews || []).forEach((row, ci) => {
    (row?.members || []).forEach((m, mi) => {
      if (m && typeof m.notes === "string" && m.notes.trim()) {
        const path = `masci_crews[${ci}].members[${mi}].notes`;
        fields[path] = m.notes;
        setters.push((byPath) => {
          if (byPath[path] !== undefined) {
            payload.masci_crews[ci].members[mi].notes = byPath[path];
          }
        });
      }
    });
  });

  // Excavation nested block
  const exc = payload.excavation;
  if (exc && typeof exc === "object") {
    EXCAVATION_TEXT_FIELDS.forEach((k) => {
      if (typeof exc[k] === "string" && exc[k].trim()) {
        const path = `excavation.${k}`;
        fields[path] = exc[k];
        setters.push((byPath) => {
          if (byPath[path] !== undefined) payload.excavation[k] = byPath[path];
        });
      }
    });
  }

  return { fields, setters };
}

/**
 * Translate every Spanish free-text field on a DR V3 payload to English.
 * Returns { ok, payload, error }. On failure the caller MUST NOT submit.
 *
 * The returned payload is a NEW deep-cloned object with:
 *   * canonical text fields overwritten in English
 *   * `translation_metadata` attached (audit sub-doc)
 *   * `submit_language` remains as-is (the operator's UI language)
 */
export async function translateDrV3PayloadEsToEn(payload) {
  // Deep clone so we never mutate the caller's live state.
  const clone = JSON.parse(JSON.stringify(payload || {}));
  const { fields, setters } = _flattenFreeText(clone);

  if (Object.keys(fields).length === 0) {
    return { ok: true, payload: clone };
  }

  const preserveTokens = _collectPreserveTokens(clone);

  // Snapshot the original Spanish for audit metadata (per Track 24.3
  // blueprint · audit sub-doc, never consumed by AI/PDF/email/ODS).
  const originalSpanishSnapshot = { ...fields };

  let resp;
  try {
    const { data } = await api.post("/translate/dr-v3-freetext", {
      fields,
      preserve_tokens: preserveTokens,
      dr_id: clone.report_number || clone.id || "",
    });
    resp = data;
  } catch (e) {
    const err = e?.response?.data?.detail?.error
      || e?.response?.data?.error
      || "translation_service_unavailable";
    return { ok: false, error: err };
  }

  if (!resp?.ok) {
    return { ok: false, error: resp?.error || "translation_service_unavailable" };
  }

  // Apply translations back onto the cloned payload.
  const translated = resp.translations || {};
  setters.forEach((setFn) => setFn(translated));

  // Attach audit metadata.
  clone.translation_metadata = {
    ...(resp.translation_metadata || {}),
    original_spanish_snapshot: originalSpanishSnapshot,
  };

  return { ok: true, payload: clone };
}

export const __TESTING__ = {
  _flattenFreeText,
  _collectPreserveTokens,
  FREE_TEXT_PATHS,
  EXCAVATION_TEXT_FIELDS,
};
