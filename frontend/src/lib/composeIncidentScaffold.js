// Shared helper: compose the discussion-notes scaffold for a topic that
// carries an `incident_pattern` field. Used both at template-load time
// (to render the scaffold into the textarea) and at submit time (to
// detect whether the user has edited the bilingual scaffold back to
// the English canonical form).
//
// Format:
//   <HEADER>
//   <incident_pattern paragraph>
//
//   <bullet discussion notes>

export const SCAFFOLD_HEADER_EN = "WHAT HAPPENS · real-world pattern";
export const SCAFFOLD_HEADER_ES = "PATRÓN REAL · lo que suele pasar";

/**
 * Compose discussion_notes with the optional incident_pattern header.
 * @param {string|undefined} pattern - the incident_pattern paragraph
 * @param {string|undefined} bullets - the bullet discussion notes
 * @param {boolean} isEs - true to use the Spanish header
 * @returns {string} composed notes (just bullets if pattern is empty)
 */
export function composeIncidentScaffold(pattern, bullets, isEs) {
  const body = bullets || "";
  if (!pattern) return body;
  const header = isEs ? SCAFFOLD_HEADER_ES : SCAFFOLD_HEADER_EN;
  return `${header}\n${pattern}\n\n${body}`;
}
