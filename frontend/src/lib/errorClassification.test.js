/**
 * errorClassification.test.js — TRUST-DIAGNOSTICS-001 contract pinning.
 *
 * Run with: cd /app/frontend && CI=true yarn test --watchAll=false src/lib/errorClassification.test.js
 */
/* eslint-env jest */
/* global describe, test, expect, beforeEach, afterEach */

import { classifyApiError, ERROR_KINDS } from "./errorClassification";

const makeAxiosError = (status, data = {}) => ({
  isAxiosError: true,
  message: `Request failed with status code ${status}`,
  response: { status, data },
  config: {},
});

describe("classifyApiError · failure paths", () => {
  test("401 → session_expired", () => {
    const r = classifyApiError(makeAxiosError(401, { detail: "Admin login required" }));
    expect(r.kind).toBe(ERROR_KINDS.SESSION_EXPIRED);
    expect(r.status).toBe(401);
    expect(r.retryable).toBe(false);
    expect(r.title).toBe("Session Expired");
    expect(r.action).toBe("Log Back In");
  });

  test("403 → access_restricted", () => {
    const r = classifyApiError(makeAxiosError(403, { detail: "Forbidden" }));
    expect(r.kind).toBe(ERROR_KINDS.ACCESS_RESTRICTED);
    expect(r.status).toBe(403);
    expect(r.retryable).toBe(false);
    expect(r.title).toBe("Access Restricted");
  });

  test("500 → backend_unavailable", () => {
    const r = classifyApiError(makeAxiosError(500));
    expect(r.kind).toBe(ERROR_KINDS.BACKEND_UNAVAILABLE);
    expect(r.retryable).toBe(true);
    expect(r.title).toBe("MASCI Services Temporarily Unavailable");
  });

  test("502 / 503 / 504 → backend_unavailable", () => {
    [502, 503, 504].forEach((s) => {
      expect(classifyApiError(makeAxiosError(s)).kind).toBe(ERROR_KINDS.BACKEND_UNAVAILABLE);
    });
  });

  test("ECONNABORTED (timeout) → network_unreachable", () => {
    const err = { code: "ECONNABORTED", message: "timeout of 60000ms exceeded" };
    const r = classifyApiError(err);
    expect(r.kind).toBe(ERROR_KINDS.NETWORK_UNREACHABLE);
    expect(r.retryable).toBe(true);
    expect(r.title).toBe("Connection Problem");
  });

  test("ERR_NETWORK (no response) → network_unreachable", () => {
    const err = { code: "ERR_NETWORK", message: "Network Error" };
    const r = classifyApiError(err);
    expect(r.kind).toBe(ERROR_KINDS.NETWORK_UNREACHABLE);
  });

  test("offline (navigator.onLine=false) wins over status", () => {
    const err = makeAxiosError(500); // even with 500 response, offline takes precedence
    const r = classifyApiError(err, { offline: true });
    expect(r.kind).toBe(ERROR_KINDS.NETWORK_UNREACHABLE);
  });

  test("404 → kind:null (per-call client error, NOT global overlay)", () => {
    const r = classifyApiError(makeAxiosError(404));
    expect(r.kind).toBeNull();
    expect(r.status).toBe(404);
  });

  test("422 validation error → kind:null (per-call, not global)", () => {
    const r = classifyApiError(makeAxiosError(422, { detail: "Invalid input" }));
    expect(r.kind).toBeNull();
  });

  test("unknown error shape → network_unreachable (conservative)", () => {
    const r = classifyApiError(new Error("Something exploded"));
    expect(r.kind).toBe(ERROR_KINDS.NETWORK_UNREACHABLE);
  });
});

describe("classifyApiError · success paths", () => {
  test("2xx with array data → success_loaded", () => {
    const r = classifyApiError({ ok: true, status: 200, data: [1, 2, 3] });
    expect(r.kind).toBe(ERROR_KINDS.SUCCESS_LOADED);
  });

  test("2xx with empty array → success_empty", () => {
    const r = classifyApiError({ ok: true, status: 200, data: [] });
    expect(r.kind).toBe(ERROR_KINDS.SUCCESS_EMPTY);
  });

  test("2xx with empty object → success_empty", () => {
    const r = classifyApiError({ ok: true, status: 200, data: {} });
    expect(r.kind).toBe(ERROR_KINDS.SUCCESS_EMPTY);
  });

  test("custom isEmpty predicate honored", () => {
    const r = classifyApiError(
      { ok: true, status: 200, data: { count: 0, items: [] } },
      { isEmpty: (d) => d?.items?.length === 0 },
    );
    expect(r.kind).toBe(ERROR_KINDS.SUCCESS_EMPTY);
    const r2 = classifyApiError(
      { ok: true, status: 200, data: { count: 5, items: [1] } },
      { isEmpty: (d) => d?.items?.length === 0 },
    );
    expect(r2.kind).toBe(ERROR_KINDS.SUCCESS_LOADED);
  });
});
