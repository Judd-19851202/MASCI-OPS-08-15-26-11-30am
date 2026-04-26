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
 * English. Returns a NEW payload object — original is not mutated. If the
 * backend translate call fails for any reason, the original payload is
 * returned (we never block submit on a translation failure).
 */
export async function translateUserInput(payload, fromLang) {
  if (!fromLang || fromLang === "en") return payload;

  const items = [];
  collect(payload, "", items);

  if (items.length === 0) return payload;

  // Send the items as a flat dict { idx -> string }
  const dict = {};
  items.forEach((it, i) => {
    dict[String(i)] = it.value;
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
    return next;
  } catch (err) {
    console.warn("Auto-translate failed; submitting as-typed.", err);
    return payload;
  }
}
