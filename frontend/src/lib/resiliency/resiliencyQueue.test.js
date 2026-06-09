/**
 * resiliencyQueue.test.js — DR-QUEUE-RETRY-001 · OMEGA DIRECTIVE.
 *
 * Pinned behavioural contract for the offline upload queue. Tests:
 *   1. Failed item stays failed during automatic drain (background path).
 *   2. retryAllFailed() resets failed item (status→pending, tries→0,
 *      lastError→null) and triggers a network attempt.
 *   3. Successful re-attempt removes the item from the queue.
 *   4. A re-armed item that fails again re-enters the normal retry
 *      lifecycle (tries increment from 0; eventually returns to failed
 *      after MAX_TRIES).
 *   5. Idempotency-Key is attached on every attempt → no duplicates.
 *   6. Manual Retry All is the ONLY path that re-arms failed items
 *      (drainQueue() alone is a no-op against a failed item).
 *
 * Runs with: cd /app/frontend && yarn test --watchAll=false src/lib/resiliency/resiliencyQueue.test.js
 */
/* eslint-env jest */
/* global jest, describe, test, expect, beforeEach, afterEach */

// ── Mocks ──────────────────────────────────────────────────────────
// idb-keyval is replaced by an in-memory store so the test does not
// touch IndexedDB. Variable must be `mock*` prefixed for jest.mock().
let mockIdb = {};
jest.mock("idb-keyval", () => ({
  get: jest.fn(async (k) => mockIdb[k]),
  set: jest.fn(async (k, v) => { mockIdb[k] = v; }),
  del: jest.fn(async (k) => { delete mockIdb[k]; }),
}));

// API mock — every test re-wires the implementation.
const mockRequest = jest.fn();
jest.mock("@/lib/api", () => ({
  api: { request: (...args) => mockRequest(...args) },
}), { virtual: true });

// Ensure navigator.onLine === true so drainQueue() doesn't bail early.
Object.defineProperty(global.navigator, "onLine", {
  configurable: true, get: () => true,
});

// Helper: reset queue + module state between tests.
async function freshModule() {
  jest.resetModules();
  mockIdb = {};
  mockRequest.mockReset();
  // Re-import after resetModules so internal `_queue` is null again.
  return require("./resiliencyQueue");
}

// Helper: drain timers used by the queue's _scheduleDrain backoff.
function flushBackoff() {
  jest.runOnlyPendingTimers();
}

describe("resiliencyQueue · DR-QUEUE-RETRY-001 contract", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });
  afterEach(() => {
    jest.useRealTimers();
  });

  // ── 1. Background drain must skip failed items ────────────────────
  test("automatic drainQueue() does NOT retry items in failed state", async () => {
    const mod = await freshModule();

    // Seed a failed item directly via IDB so we can exercise drainQueue
    // without going through enqueueUpload's "first attempt" path.
    mockIdb["masci.resiliency.queue.v1"] = [{
      id: "fail-1",
      method: "POST",
      url: "/api/daily_reports",
      headers: {},
      body: { project_number: "26-01 - CP" },
      idempotencyKey: "idem-fail-1",
      formKey: "daily-report-new",
      tries: 5,
      status: "failed",
      enqueuedAt: Date.now(),
      lastError: "boom",
    }];

    mockRequest.mockResolvedValue({ data: { ok: true } });
    await mod.drainQueue();

    expect(mockRequest).not.toHaveBeenCalled();
    const items = mod.getQueueItems();
    expect(items).toHaveLength(1);
    expect(items[0].status).toBe("failed");
    expect(items[0].tries).toBe(5);
  });

  // ── 2. retryAllFailed() resets failed item ────────────────────────
  test("retryAllFailed() resets status, tries, lastError; then attempts", async () => {
    const mod = await freshModule();

    mockIdb["masci.resiliency.queue.v1"] = [{
      id: "fail-2",
      method: "POST",
      url: "/api/daily_reports",
      headers: {},
      body: { project_number: "26-01 - CP" },
      idempotencyKey: "idem-fail-2",
      formKey: "daily-report-new",
      tries: 5,
      status: "failed",
      enqueuedAt: Date.now(),
      lastError: "previous failure",
    }];

    mockRequest.mockResolvedValue({ data: { ok: true, id: "dr-9" } });
    const result = await mod.retryAllFailed();

    expect(result.reset).toBe(1);
    expect(result.drained).toBe(true);
    // The re-armed item was successfully attempted, so the queue is
    // empty.
    expect(mod.getQueueItems()).toHaveLength(0);
    expect(mockRequest).toHaveBeenCalledTimes(1);
    // Idempotency key MUST be attached → server can dedupe.
    expect(mockRequest.mock.calls[0][0].headers["Idempotency-Key"])
      .toBe("idem-fail-2");
  });

  // ── 3. Successful re-attempt removes item ─────────────────────────
  test("successful retry submission removes the item from queue", async () => {
    const mod = await freshModule();

    mockIdb["masci.resiliency.queue.v1"] = [{
      id: "fail-3",
      method: "POST",
      url: "/api/incidents",
      headers: {},
      body: { kind: "near-miss" },
      idempotencyKey: "idem-fail-3",
      formKey: "incident-new",
      tries: 5,
      status: "failed",
      enqueuedAt: Date.now(),
      lastError: "network",
    }];

    mockRequest.mockResolvedValue({ data: { id: "inc-1" } });
    await mod.retryAllFailed();

    expect(mod.getQueueDepth()).toBe(0);
    expect(mod.getQueueItems()).toHaveLength(0);
  });

  // ── 4. Re-armed item that fails again returns to normal lifecycle ─
  test("re-armed item failing again increments tries from 0 → MAX_TRIES", async () => {
    const mod = await freshModule();

    mockIdb["masci.resiliency.queue.v1"] = [{
      id: "fail-4",
      method: "POST",
      url: "/api/inspections",
      headers: {},
      body: { kind: "weekly" },
      idempotencyKey: "idem-fail-4",
      formKey: "inspection-new",
      tries: 5,
      status: "failed",
      enqueuedAt: Date.now(),
      lastError: "old",
    }];

    // Make every attempt fail.
    mockRequest.mockRejectedValue(new Error("still down"));

    await mod.retryAllFailed();
    // After re-arm + first attempt failure, tries should be 1, status pending.
    let items = mod.getQueueItems();
    expect(items).toHaveLength(1);
    expect(items[0].status).toBe("pending");
    expect(items[0].tries).toBe(1);
    expect(items[0].lastError).toMatch(/still down/);

    // Subsequent automatic drains progress tries from 0 lifecycle until
    // MAX_TRIES is reached again. We just call drainQueue() repeatedly
    // (background-style) and confirm the item ends in failed state with
    // tries === 5.
    for (let i = 0; i < 5; i += 1) {
      flushBackoff();
      
      await mod.drainQueue();
    }
    items = mod.getQueueItems();
    expect(items).toHaveLength(1);
    expect(items[0].status).toBe("failed");
    expect(items[0].tries).toBe(5);
  });

  // ── 5. Idempotency-Key is attached on every attempt ───────────────
  test("Idempotency-Key header attached on every retry (no duplicates)", async () => {
    const mod = await freshModule();

    mockIdb["masci.resiliency.queue.v1"] = [{
      id: "fail-5",
      method: "POST",
      url: "/api/meetings",
      headers: {},
      body: { topic: "TBT" },
      idempotencyKey: "idem-fail-5",
      formKey: "meeting-new",
      tries: 5,
      status: "failed",
      enqueuedAt: Date.now(),
      lastError: "old",
    }];

    // First call fails, second call succeeds.
    mockRequest
      .mockRejectedValueOnce(new Error("flaky"))
      .mockResolvedValueOnce({ data: { id: "mtg-1" } });

    await mod.retryAllFailed();
    flushBackoff();
    await mod.drainQueue();

    // The queue may auto-schedule extra drain attempts after a failure.
    // The contract we are asserting is: EVERY attempt — however many
    // there are — must carry the same Idempotency-Key so the backend
    // can deduplicate.
    expect(mockRequest.mock.calls.length).toBeGreaterThanOrEqual(2);
    for (const call of mockRequest.mock.calls) {
      expect(call[0].headers["Idempotency-Key"]).toBe("idem-fail-5");
    }
  });

  // ── 6. Manual Retry All is the ONLY re-arm path ───────────────────
  test("drainQueue alone never re-arms; retryAllFailed is required", async () => {
    const mod = await freshModule();

    mockIdb["masci.resiliency.queue.v1"] = [{
      id: "fail-6",
      method: "POST",
      url: "/api/daily_reports",
      headers: {},
      body: {},
      idempotencyKey: "idem-fail-6",
      formKey: "daily-report-new",
      tries: 5,
      status: "failed",
      enqueuedAt: Date.now(),
      lastError: "permanent",
    }];

    mockRequest.mockResolvedValue({ data: { ok: true } });

    // Many background drains — must NOT touch the failed item.
    for (let i = 0; i < 10; i += 1) {
      flushBackoff();
      
      await mod.drainQueue();
    }
    expect(mockRequest).not.toHaveBeenCalled();
    expect(mod.getQueueItems()[0].status).toBe("failed");

    // Only the explicit operator action recovers it.
    await mod.retryAllFailed();
    expect(mockRequest).toHaveBeenCalledTimes(1);
    expect(mod.getQueueItems()).toHaveLength(0);
  });

  // ── 7. Production-equivalent recovery scenario ────────────────────
  test("recovers a real-world stuck Daily Report item", async () => {
    const mod = await freshModule();
    // Mirror the production user's reported scenario: a Daily Report
    // queued offline, exhausted retries, currently `failed`.
    mockIdb["masci.resiliency.queue.v1"] = [{
      id: "dr-stuck",
      method: "POST",
      url: "/api/daily_reports",
      headers: { "X-Actor-Id": "operator-1" },
      body: {
        project_number: "24-12",
        project_name: "CC5744 - OXFORD RD Improvements (OXFORD)",
        date: "2026-06-09",
      },
      idempotencyKey: "idem-dr-stuck",
      formKey: "daily-report-new",
      tries: 5,
      status: "failed",
      enqueuedAt: Date.now() - 60_000,
      lastError: "Network Error",
    }];

    mockRequest.mockResolvedValue({ data: { id: "dr-created-once" } });
    const out = await mod.retryAllFailed();

    expect(out.reset).toBe(1);
    expect(mod.getQueueItems()).toHaveLength(0);
    // Backend received the Idempotency-Key, so even if the original
    // attempt did land server-side, the server would deduplicate.
    expect(mockRequest.mock.calls[0][0].headers["Idempotency-Key"])
      .toBe("idem-dr-stuck");
    // Original Daily Report body preserved verbatim — no payload mutation.
    expect(mockRequest.mock.calls[0][0].data).toEqual({
      project_number: "24-12",
      project_name: "CC5744 - OXFORD RD Improvements (OXFORD)",
      date: "2026-06-09",
    });
  });
});
