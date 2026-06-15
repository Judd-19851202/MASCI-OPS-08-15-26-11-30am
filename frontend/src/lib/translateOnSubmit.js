// Auto-translate freeform user-typed Spanish back to English at submit time.
// All MASCI safety records must be stored & printed in English. Spanish UI is
// a fill-aid only — when the user hits Submit in ES mode, we send their
// payload to /api/translate which uses an LLM to translate string leaves.
//
// What we DO translate: prose strings the user typed (notes, descriptions,
// names of activities, purpose, etc).
// What we DO NOT translate:
//   - empty / whitespace-only strings
//   - data: URLs (photos, signatures)
//   - ISO dates (YYYY-MM-DD) and times (HH:MM, HH:MM:SS)
//   - pure numbers
//   - GPS coords / accuracy
//   - obvious identifiers (project_number, report_number, ids)
//   - signature_* / photo_* / *_signature fields by key
//
// The walker preserves the payload's exact shape — it only swaps string
// leaves where the LLM gave us a translation back.

import { api } from "@/lib/api";

const SKIP_KEY_RE =
  /signature|photo|^id$|created_at|gps_|accuracy|_lat$|_lng$|_url$|score|status|_count$|^date$|_date$|_time$|_number$|severity|incident_type|operation|topic_category/i;

const DATA_URL_RE = /^data:[a-z]+\/[a-z0-9.+-]+;base64,/i;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const TIME_RE = /^\d{1,2}:\d{2}(:\d{2})?$/;
const NUMERIC_RE = /^-?\d+(\.\d+)?$/;
const YESNO_RE = /^(yes|no|n\/a|true|false)$/i;

function shouldTranslate(key, value) {
  if (typeof value !== "string") return false;
  const v = value.trim();
  if (!v) return false;
  if (v.length < 2) return false;
  if (DATA_URL_RE.test(v)) return false;
  if (DATE_RE.test(v)) return false;
  if (TIME_RE.test(v)) return false;
  if (NUMERIC_RE.test(v)) return false;
  if (YESNO_RE.test(v)) return false;
  if (SKIP_KEY_RE.test(key)) return false;
  return true;
}

// Walk payload, collect translatable strings as { path, value }.
// Path is a JSON-pointer-ish string we use only for round-trip mapping.
function collect(node, path, out, parentKey = "") {
  if (Array.isArray(node)) {
    node.forEach((child, i) => collect(child, `${path}/${i}`, out, parentKey));
    return;
  }
  if (node && typeof node === "object") {
    for (const k of Object.keys(node)) {
      collect(node[k], `${path}/${k}`, out, k);
    }
    return;
  }
  if (shouldTranslate(parentKey, node)) {
    out.push({ path, value: node });
  }
}

function setByPath(root, path, value) {
  const parts = path.split("/").slice(1); // drop leading ""
  let cur = root;
  for (let i = 0; i < parts.length - 1; i++) {
    const k = parts[i];
    cur = Array.isArray(cur) ? cur[Number(k)] : cur[k];
    if (cur == null) return;
  }
  const last = parts[parts.length - 1];
  if (Array.isArray(cur)) cur[Number(last)] = value;
  else cur[last] = value;
}

/**
 * Translate freeform user text in `payload` from `fromLang` (e.g. "es") into
 * English, and stamp the original submit language onto the returned payload
 * so admins can see which records were originally filed in Spanish.
 *
 * TRACK 14.0-S1 Amendment A — Original-text preservation:
 *   When a translation actually fires, the original strings are stored
 *   in a sidecar map ``_originals`` (keyed by the same path used for
 *   translation), plus ``_original_language`` ("es") on the payload.
 *   The translated EN content remains the canonical, searchable value
 *   stored at the original field path (preserves existing search /
 *   admin-view contracts); the sidecar is purely additive and lets
 *   bilingual views render BOTH languages. Backends that don't know
 *   about the sidecar simply ignore the extra keys (Pydantic extras
 *   policy = ignore on this codebase).
 *
 * - Returns a NEW payload object (original is never mutated).
 * - `submit_language` is ALWAYS set on the output ("en" | "es") regardless
 *   of whether any translation was actually needed. Downstream admin views
 *   + the /api/admin/submit-language-stats endpoint read this field.
 * - If the backend translate call fails for any reason, we still return a
 *   clone of the original payload with `submit_language` stamped — we never
 *   block submit on a translation failure. In that fallback case we ALSO
 *   stamp a sidecar copy of the originals so downstream consumers can
 *   surface a "translation pending" affordance instead of silently
 *   showing Spanish to an English audience.
 */
export async function translateUserInput(payload, fromLang) {
  // English — no LLM call needed, still stamp the language for audit.
  if (!fromLang || fromLang === "en") {
    return { ...payload, submit_language: "en" };
  }

  const items = [];
  collect(payload, "", items);

  if (items.length === 0) {
    return { ...payload, submit_language: fromLang };
  }

  // Send the items as a flat dict { idx -> string }
  const dict = {};
  items.forEach((it, i) => {
    dict[String(i)] = it.value;
  });

  // Pre-build the originals sidecar (path -> original string) up front so
  // it is available in both the success and failure branches.
  const originals = {};
  items.forEach((it) => {
    originals[it.path] = it.value;
  });

  try {
    const res = await api.post("/translate", {
      from_lang: fromLang,
      to_lang: "en",
      strings: dict,
    });
    const translated = res?.data?.strings || {};

    // Deep-clone the payload before mutation
    const next = JSON.parse(JSON.stringify(payload));
    items.forEach((it, i) => {
      const k = String(i);
      if (typeof translated[k] === "string" && translated[k].trim()) {
        setByPath(next, it.path, translated[k]);
      }
    });
    next.submit_language = fromLang;
    // TRACK 14.0-S1 Amendment A — preserve originals + source language.
    next._originals = originals;
    next._original_language = fromLang;
    next._translated_at = new Date().toISOString();
    next._translation_source = "llm";
    return next;
  } catch (err) {
    console.warn("Auto-translate failed; submitting as-typed.", err);
    return {
      ...payload,
      submit_language: fromLang,
      // Even on failure, stamp the originals sidecar so the eventual
      // record explicitly carries the source-language flag and lets a
      // background retranslation cron pick it up.
      _originals: originals,
      _original_language: fromLang,
      _translation_source: "pending",
    };
  }
}

/**
 * TRACK 14.0-S1 Amendment A · post-submit sidecar write.
 *
 * After a form is saved to its canonical collection, callers invoke this
 * helper with the form_type + form_id + the previously-prepared
 * translated payload so the original-language strings get persisted to
 * the `bilingual_records` sidecar collection. The canonical record
 * stays unchanged — backend-side schema changes are avoided.
 *
 * Returns ``{ok, stored, id?}``; never throws (a sidecar write failure
 * must not break the user's submission).
 */
export async function persistBilingualSidecar(formType, formId, translatedPayload) {
  try {
    if (!formType || !formId) return { ok: false, stored: false, reason: "missing_id" };
    const originals = translatedPayload?._originals;
    const lang = translatedPayload?._original_language;
    if (!originals || !lang || Object.keys(originals).length === 0) {
      return { ok: true, stored: false, reason: "no_originals" };
    }
    const r = await api.post("/bilingual-records", {
      form_type: String(formType).toLowerCase(),
      form_id: String(formId),
      original_language: lang,
      originals,
      translation_source: translatedPayload?._translation_source || "llm",
    });
    return r?.data || { ok: true, stored: true };
  } catch (err) {
    console.warn("Bilingual sidecar persist failed; continuing.", err);
    return { ok: false, stored: false, reason: "post_failed" };
  }
}

