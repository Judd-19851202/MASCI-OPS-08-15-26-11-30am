// TRACK 23.4C · HR-autofill resolver for the Daily Report V3 crew row.
//
// EmployeeCombo fires `onPick` only when the user clicks a row in the
// dropdown. If the operator types the name and blurs (or presses
// Enter) without clicking, no HR record is ever passed back to the
// parent form. This helper closes that gap: given a typed name and
// the current HR roster, it resolves the best matching employee and
// returns the same {trade, crew, supervisor, employee_id, ...} shape
// the pick handler would receive.
//
// Also normalizes the many HR field aliases that different eras of
// the Employee Master shipped with: trade / role / title / position /
// classification / department for the Trade field; crew / division /
// department for the Crew field; supervisor / supervisor_name for
// the Supervisor field.

const _norm = (s) => (s || "").toString().trim().toLowerCase();

export function pickHrFields(emp) {
  if (!emp || typeof emp !== "object") {
    return { trade: "", crew: "", supervisor: "", employee_id: "" };
  }
  const trade =
    emp.trade
    || emp.role
    || emp.title
    || emp.position
    || emp.classification
    || emp.trade_role
    || emp.department
    || "";
  // Crew / division metadata. `department` acts as a fallback here
  // only when it wasn't consumed by the Trade branch above (rare —
  // typically HR uses either trade OR department, not both).
  const crew =
    emp.crew
    || emp.division
    || (trade ? "" : emp.department)
    || "";
  const supervisor = emp.supervisor || emp.supervisor_name || "";
  const employee_id = emp.employee_id || emp.id || "";
  const name = emp.name || emp.legal_name || emp.display_name || emp.preferred_name || "";
  return {
    name,
    employee_id,
    trade,
    crew,
    supervisor,
  };
}

export function resolveEmployeeByTypedName(typed, roster) {
  const q = _norm(typed);
  if (!q || q.length < 2) return null;
  const items = Array.isArray(roster)
    ? roster
    : (roster?.items || []);
  if (!items.length) return null;

  const candidateMatches = [];
  for (const it of items) {
    const name = _norm(it.name);
    const legal = _norm(it.legal_name);
    const pref = _norm(it.preferred_name);
    const display = _norm(it.display_name);
    const empId = _norm(it.employee_id);
    if (
      name === q
      || legal === q
      || pref === q
      || display === q
      || (empId && empId === q)
    ) {
      return it; // exact match wins immediately
    }
    if (name && name.includes(q)) candidateMatches.push([0, it]);
    else if (pref && pref.includes(q)) candidateMatches.push([1, it]);
    else if (legal && legal.includes(q)) candidateMatches.push([2, it]);
    else if (display && display.includes(q)) candidateMatches.push([3, it]);
  }
  // If exactly one partial match, take it. Otherwise return null so
  // the UI treats the typed value as a custom employee (safer than
  // guessing between multiple ambiguous partials).
  if (candidateMatches.length === 1) return candidateMatches[0][1];
  return null;
}
