// test_opsCenterEscalations.cjs — Iter162 unit tests for the
// localStorage-backed escalation tracker. Pure Node script; no jest
// dependency needed. Run with: node test_opsCenterEscalations.cjs

// In-memory localStorage shim for Node.
const store = new Map();
global.localStorage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => { store.set(k, String(v)); },
  removeItem: (k) => { store.delete(k); },
  clear: () => { store.clear(); },
};

// ESM module import via dynamic import.
(async () => {
  // Use file:// path so Node treats it as a real ES module.
  const mod = await import("/app/frontend/src/lib/opsCenterEscalations.js");
  const {
    isEscalation, reconcileEscalations, clearEscalation, __internals,
  } = mod;

  let passed = 0, failed = 0;
  const tests = [];
  const t = (name, fn) => tests.push([name, fn]);

  const eq = (a, b, msg) => {
    if (JSON.stringify(a) !== JSON.stringify(b)) {
      throw new Error(`${msg || ""} expected ${JSON.stringify(b)} got ${JSON.stringify(a)}`);
    }
  };

  const reset = () => { store.clear(); };

  // ── isEscalation: pure detection ─────────────────────────────────
  t("isEscalation: Info→Warning is escalation", () => {
    eq(isEscalation("Info", "Warning"), true);
  });
  t("isEscalation: Info→Critical is escalation", () => {
    eq(isEscalation("Info", "Critical"), true);
  });
  t("isEscalation: Warning→Critical is escalation", () => {
    eq(isEscalation("Warning", "Critical"), true);
  });
  t("isEscalation: same severity is NOT escalation", () => {
    eq(isEscalation("Warning", "Warning"), false);
    eq(isEscalation("Critical", "Critical"), false);
    eq(isEscalation("Info", "Info"), false);
  });
  t("isEscalation: de-escalation is NOT escalation", () => {
    eq(isEscalation("Critical", "Warning"), false);
    eq(isEscalation("Critical", "Info"), false);
    eq(isEscalation("Warning", "Info"), false);
  });
  t("isEscalation: unknown prev is NOT escalation (first visit silent)", () => {
    eq(isEscalation(undefined, "Critical"), false);
    eq(isEscalation(undefined, "Warning"), false);
    eq(isEscalation(undefined, "Info"), false);
  });

  // ── reconcileEscalations: orchestration ──────────────────────────
  t("reconcileEscalations: first visit never pulses", () => {
    reset();
    const cards = [
      { key: "po_approval_p90", severity: "Critical" },
      { key: "repeat_equipment_failures", severity: "Warning" },
    ];
    const pulsing = reconcileEscalations("admin", cards);
    eq([...pulsing], []);
  });

  t("reconcileEscalations: second visit with escalation pulses", () => {
    reset();
    reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Info" },
    ], 1_000_000);
    const pulsing = reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Warning" },
    ], 2_000_000);
    eq([...pulsing], ["po_approval_p90"]);
  });

  t("reconcileEscalations: same severity on second visit does NOT pulse", () => {
    reset();
    reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Warning" },
    ], 1_000_000);
    const pulsing = reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Warning" },
    ], 2_000_000);
    eq([...pulsing], []);
  });

  t("reconcileEscalations: de-escalation does NOT pulse", () => {
    reset();
    reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Critical" },
    ], 1_000_000);
    const pulsing = reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Info" },
    ], 2_000_000);
    eq([...pulsing], []);
  });

  t("reconcileEscalations: 24h TTL clears old pulse", () => {
    reset();
    reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Info" },
    ], 1_000_000);
    // Visit 2 — escalation fires
    reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Critical" },
    ], 2_000_000);
    // Visit 3 — 25h later, escalation expired
    const later = 2_000_000 + (25 * 60 * 60 * 1000);
    const pulsing = reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Critical" },
    ], later);
    eq([...pulsing], []);
  });

  t("reconcileEscalations: persists pulse across visits within 24h", () => {
    reset();
    reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Info" },
    ], 1_000_000);
    reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Critical" },
    ], 2_000_000);
    // Visit 3 — 1h later, same severity, pulse persists.
    const later = 2_000_000 + (60 * 60 * 1000);
    const pulsing = reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Critical" },
    ], later);
    eq([...pulsing], ["po_approval_p90"]);
  });

  t("clearEscalation: removes pulse immediately", () => {
    reset();
    reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Info" },
    ], 1_000_000);
    reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Critical" },
    ], 2_000_000);
    clearEscalation("admin", "po_approval_p90");
    // Verify localStorage no longer carries the entry
    const esc = JSON.parse(localStorage.getItem(__internals.ESCALATIONS_KEY));
    eq(esc.admin.po_approval_p90, undefined);
  });

  t("reconcileEscalations: scoped per role (admin escalation ≠ pm)", () => {
    reset();
    reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Info" },
    ], 1_000_000);
    reconcileEscalations("pm", [
      { key: "po_approval_p90", severity: "Info" },
    ], 1_000_000);
    // Admin escalates
    const adminPulse = reconcileEscalations("admin", [
      { key: "po_approval_p90", severity: "Critical" },
    ], 2_000_000);
    eq([...adminPulse], ["po_approval_p90"]);
    // PM same severity → no pulse for PM
    const pmPulse = reconcileEscalations("pm", [
      { key: "po_approval_p90", severity: "Info" },
    ], 2_000_000);
    eq([...pmPulse], []);
  });

  t("reconcileEscalations: invalid input returns empty set", () => {
    reset();
    eq([...reconcileEscalations(null, null)], []);
    eq([...reconcileEscalations("admin", null)], []);
    eq([...reconcileEscalations("admin", undefined)], []);
  });

  // Run all tests
  for (const [name, fn] of tests) {
    try {
      fn();
      console.log("  ✓", name);
      passed++;
    } catch (e) {
      console.log("  ✗", name, "—", e.message);
      failed++;
    }
  }
  console.log(`\n${passed}/${passed + failed} passed`);
  process.exit(failed ? 1 : 0);
})();
