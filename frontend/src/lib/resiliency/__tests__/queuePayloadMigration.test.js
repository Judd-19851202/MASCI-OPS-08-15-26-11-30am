// P0-QUEUE-2026-08-13 — queue payload migration regressions.
import { migrateQueuedBody, QUEUE_SCHEMA_VERSION } from "../queuePayloadMigration";

describe("migrateQueuedBody — legacy submission-queue compatibility", () => {
  test("strips the client-only idempotency helper that caused extra_forbidden", () => {
    const original = {
      kind: "new_hire",
      name: "Field Worker",
      submitted_via: "employee_combo_inline",
      _track_15_60_client_idempotency_key: "idem-123",
    };
    const { body, stripped, changed } = migrateQueuedBody(original, "employee-request-inline");
    expect(stripped).toContain("_track_15_60_client_idempotency_key");
    expect(body._track_15_60_client_idempotency_key).toBeUndefined();
    // Business fields preserved.
    expect(body.kind).toBe("new_hire");
    expect(body.name).toBe("Field Worker");
    expect(body.submitted_via).toBe("employee_combo_inline");
    expect(changed).toBe(true);
  });

  test("NEVER mutates the persisted original body (recovery copy intact)", () => {
    const original = { name: "X", _track_15_60_client_idempotency_key: "k" };
    migrateQueuedBody(original, "employee-request-inline");
    // Original still has the field — only the SENT clone was stripped.
    expect(original._track_15_60_client_idempotency_key).toBe("k");
  });

  test("STRIP-ONLY: adds no new field to the outbound body", () => {
    const original = { name: "X", value: 5 };
    const { body, stripped } = migrateQueuedBody(original, "incident-new");
    expect(stripped).toEqual([]);
    // No queue_schema_version (or anything) injected — must not create a new
    // extra_forbidden on endpoints whose model still forbids unknown fields.
    expect(Object.keys(body).sort()).toEqual(["name", "value"]);
    expect(body.queue_schema_version).toBeUndefined();
  });

  test("preserves UNKNOWN non-allowlisted business fields (no silent discard)", () => {
    const original = { name: "X", operator_note: "poured 40yd", weird_field: "keep me" };
    const { body } = migrateQueuedBody(original, "incident-new");
    expect(body.operator_note).toBe("poured 40yd");
    expect(body.weird_field).toBe("keep me");
  });

  test("is idempotent — running twice yields the same result", () => {
    const original = { name: "X", _track_15_60_client_idempotency_key: "k" };
    const once = migrateQueuedBody(original, "x").body;
    const twice = migrateQueuedBody(once, "x").body;
    expect(twice).toEqual(once);
  });

  test("does not strip business fields that merely contain an underscore", () => {
    const original = { employee_id: "E1", last_day_worked: "2026-08-01", crew: "C3" };
    const { body, stripped } = migrateQueuedBody(original, "employee-request-inline");
    expect(stripped).toEqual([]);
    expect(body.employee_id).toBe("E1");
    expect(body.last_day_worked).toBe("2026-08-01");
  });

  test("non-object bodies pass through untouched", () => {
    expect(migrateQueuedBody(null).body).toBeNull();
    expect(migrateQueuedBody("string-body").body).toBe("string-body");
    expect(QUEUE_SCHEMA_VERSION).toBeGreaterThanOrEqual(1);
  });
});
