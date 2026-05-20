// iter269 · Sprint 2 · K4 helper · split a composed `discussion_notes`
// string into its incident_pattern context block and its action-bullet body.
//
// Why: the form scaffolds both into one textarea (so foremen can freely
// edit either part), and that storage shape is preserved. At render time
// (form, ViewMeeting, PDF) we want VISUAL separation between CONTEXT
// (the incident pattern paragraph) and ACTION (the bullets) so the
// operational teaching unit is unmistakable.
//
// Parses out the EN or ES scaffold header that `composeIncidentScaffold`
// emits and returns:
//   { header, pattern, bullets }
//
// If no header is found (e.g., user wrote freeform notes), returns
// { header: "", pattern: "", bullets: <original text> } so callers can
// fall back to single-block rendering.

import {
  SCAFFOLD_HEADER_EN,
  SCAFFOLD_HEADER_ES,
} from "@/lib/composeIncidentScaffold";

export function splitIncidentScaffold(notes) {
  const text = String(notes || "");
  if (!text) return { header: "", pattern: "", bullets: "" };

  let header = "";
  let rest = text;
  if (text.startsWith(SCAFFOLD_HEADER_EN)) {
    header = SCAFFOLD_HEADER_EN;
    rest = text.slice(SCAFFOLD_HEADER_EN.length);
  } else if (text.startsWith(SCAFFOLD_HEADER_ES)) {
    header = SCAFFOLD_HEADER_ES;
    rest = text.slice(SCAFFOLD_HEADER_ES.length);
  } else {
    return { header: "", pattern: "", bullets: text };
  }

  // After the header, composeIncidentScaffold puts: "\n<pattern>\n\n<bullets>"
  // Find the first blank line separating pattern from bullets.
  const trimmed = rest.replace(/^\n+/, "");
  const blankIdx = trimmed.indexOf("\n\n");
  if (blankIdx === -1) {
    return { header, pattern: trimmed.trim(), bullets: "" };
  }
  const pattern = trimmed.slice(0, blankIdx).trim();
  const bullets = trimmed.slice(blankIdx + 2).trim();
  return { header, pattern, bullets };
}
