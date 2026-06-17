/**
 * sentryInit.beforeSend.test.js — Track 15.13A · network-error suppression.
 *
 * Verifies that transient AxiosError "Network Error" / ERR_NETWORK /
 * cancellation / timeout events are dropped at the gateway so they
 * never reach Sentry. The in-app session-status bus already shows the
 * user a calm banner for these conditions; a Sentry alert on top is
 * pure noise. Real 5xx / 4xx with `err.response.status` continue to
 * flow through untouched (their drop branch requires `noResponse`).
 *
 * Run with: cd /app/frontend && CI=true yarn test --watchAll=false src/lib/sentryInit.beforeSend.test.js
 */
/* eslint-env jest */
/* global describe, test, expect */

import fs from "fs";
import path from "path";

const SRC = fs.readFileSync(
  path.resolve(__dirname, "sentryInit.js"),
  "utf8",
);

// Slice out the _beforeSend function body without importing the module
// (importing pulls in @sentry/react which is not test-safe).
function _extractBeforeSend() {
  const start = SRC.indexOf("function _beforeSend(");
  expect(start).toBeGreaterThan(-1);
  const next = SRC.indexOf("\nfunction ", start + 10);
  return SRC.slice(start, next > 0 ? next : SRC.length);
}

const BODY = _extractBeforeSend();

describe("Sentry _beforeSend · 15.13A network-error suppression", () => {
  test("AxiosError with ERR_NETWORK is dropped (returns null)", () => {
    expect(BODY).toContain('code === "ERR_NETWORK"');
    expect(BODY).toContain("return null;");
    expect(BODY).toMatch(/isAxios\s*&&\s*noResponse\s*&&\s*\(/);
  });

  test("ERR_CANCELED / CanceledError / AbortError are dropped", () => {
    expect(BODY).toContain('code === "ERR_CANCELED"');
    expect(BODY).toContain('name === "CanceledError"');
    expect(BODY).toContain('name === "AbortError"');
  });

  test("ECONNABORTED / ETIMEDOUT / /timeout/i are dropped", () => {
    expect(BODY).toContain('code === "ECONNABORTED"');
    expect(BODY).toContain('code === "ETIMEDOUT"');
    expect(BODY).toMatch(/\/timeout\/i\.test/);
  });

  test("Backend 5xx (response.status present) is NOT dropped", () => {
    // The drop branch is gated on `noResponse` — a real 5xx has a
    // response object and falls through to the scrubber + event return.
    expect(BODY).toMatch(/const noResponse = !origErr\.response/);
  });

  test("Non-axios errors fall through to the scrubber + return", () => {
    expect(BODY).toMatch(
      /origErr\.isAxiosError === true \|\| name === "AxiosError"/,
    );
  });

  test("Existing PII scrub still runs (headers / cookies / data / message)", () => {
    expect(BODY).toContain("***SCRUBBED***");
    expect(BODY).toContain("event.request.headers");
    expect(BODY).toContain("event.request.cookies");
    expect(BODY).toContain("event.request.data");
    expect(BODY).toMatch(/event\.message\.replace\(\/\[a-f0-9\]\{40,\}\/g/);
  });

  test("Scrubber failures never crash the event pipeline", () => {
    expect(BODY).toContain("try {");
    expect(BODY).toContain("} catch {");
  });
});
