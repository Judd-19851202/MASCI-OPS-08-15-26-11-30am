/**
 * TRACK 15.13H · Error classification + operationalError + Axios interceptor
 *               regression tests.
 *
 * Each test maps to a specific production failure mode the user reported:
 *
 *  1. False "Session Expired" modal on 5xx / Cloudflare 520 / network blip.
 *  2. False "Your HR session expired" toast on a 403 from a feature endpoint.
 *  3. HR Daily Reports list collapsing to 0 reports when one request blips.
 *  4. Active-portal 401 on a peripheral endpoint (e.g. /lifecycle for HR)
 *     bouncing the user out of a still-valid session.
 *
 * These are unit-level checks against the pure helpers; the live browser
 * cert lives in TRACK_15_13H_PRODUCTION_STABILITY_RECOVERY.md.
 */

import { classifyApiError, ERROR_KINDS } from "../errorClassification";
import { operationalError } from "../errors";

// Helper to construct an axios-shaped error.
function axiosErr({ status, detail, code, message, noResponse } = {}) {
  if (noResponse) {
    const e = new Error(message || "Network Error");
    e.code = code;
    return e;
  }
  return {
    response: {
      status,
      data: detail !== undefined ? { detail } : undefined,
    },
    code,
    message: message || "",
  };
}

describe("TRACK 15.13H · classifyApiError contract", () => {
  it("401 → session_expired", () => {
    const c = classifyApiError(axiosErr({ status: 401 }));
    expect(c.kind).toBe(ERROR_KINDS.SESSION_EXPIRED);
    expect(c.title).toBe("Session Expired");
  });

  it("403 → access_restricted (NOT session_expired)", () => {
    const c = classifyApiError(axiosErr({ status: 403 }));
    expect(c.kind).toBe(ERROR_KINDS.ACCESS_RESTRICTED);
    expect(c.title).not.toBe("Session Expired");
  });

  it("500 → backend_unavailable (NOT session_expired)", () => {
    const c = classifyApiError(axiosErr({ status: 500 }));
    expect(c.kind).toBe(ERROR_KINDS.BACKEND_UNAVAILABLE);
    expect(c.title).not.toBe("Session Expired");
  });

  it("502/503/504 → backend_unavailable", () => {
    for (const s of [502, 503, 504]) {
      const c = classifyApiError(axiosErr({ status: s }));
      expect(c.kind).toBe(ERROR_KINDS.BACKEND_UNAVAILABLE);
    }
  });

  it("520 (Cloudflare origin unreachable) → backend_unavailable", () => {
    const c = classifyApiError(axiosErr({ status: 520 }));
    expect(c.kind).toBe(ERROR_KINDS.BACKEND_UNAVAILABLE);
    expect(c.title).toBe("MASCI Services Temporarily Unavailable");
  });

  it("Network timeout (ECONNABORTED, no response) → network_unreachable", () => {
    const c = classifyApiError(axiosErr({ noResponse: true, code: "ECONNABORTED", message: "timeout of 0ms exceeded" }));
    expect(c.kind).toBe(ERROR_KINDS.NETWORK_UNREACHABLE);
  });

  it("ERR_NETWORK (no response) → network_unreachable", () => {
    const c = classifyApiError(axiosErr({ noResponse: true, code: "ERR_NETWORK", message: "Network Error" }));
    expect(c.kind).toBe(ERROR_KINDS.NETWORK_UNREACHABLE);
  });

  it("Canceled / aborted request → null (silent, no modal)", () => {
    const c = classifyApiError(axiosErr({ noResponse: true, code: "ERR_CANCELED", message: "canceled" }));
    expect(c.kind).toBeNull();
  });

  it("404 → kind null (per-call client error, no global modal)", () => {
    const c = classifyApiError(axiosErr({ status: 404 }));
    expect(c.kind).toBeNull();
  });

  it("405 → kind null", () => {
    const c = classifyApiError(axiosErr({ status: 405 }));
    expect(c.kind).toBeNull();
  });

  it("422 → kind null (validation error, per-call only)", () => {
    const c = classifyApiError(axiosErr({ status: 422, detail: "Field required" }));
    expect(c.kind).toBeNull();
  });
});

describe("TRACK 15.13H · operationalError contract", () => {
  const fallback = "Daily Reports temporarily unavailable. Try again in a moment.";
  const expired = "Your HR session expired. Please sign in again.";

  it("401 → expiredMsg (session boundary)", () => {
    expect(operationalError(axiosErr({ status: 401 }), fallback, expired)).toBe(expired);
  });

  it("403 → fallback (NOT expiredMsg)", () => {
    // This is the BUG the user reported: 403 was being routed to
    // "Your HR session expired" which logged users out of valid
    // sessions.
    expect(operationalError(axiosErr({ status: 403 }), fallback, expired)).toBe(fallback);
  });

  it("403 with operator-authored detail → that detail (not session expired)", () => {
    const detail = "Asset Administrator access required.";
    expect(operationalError(axiosErr({ status: 403, detail }), fallback, expired)).toBe(detail);
  });

  it("404 → fallback", () => {
    expect(operationalError(axiosErr({ status: 404 }), fallback, expired)).toBe(fallback);
  });

  it("500/502/503/504/520 → fallback (NOT session expired)", () => {
    for (const s of [500, 502, 503, 504, 520]) {
      expect(operationalError(axiosErr({ status: s }), fallback, expired)).toBe(fallback);
    }
  });

  it("Network/no-response → fallback (NOT session expired)", () => {
    expect(operationalError(axiosErr({ noResponse: true, code: "ERR_NETWORK" }), fallback, expired)).toBe(fallback);
  });

  it("Raw FastAPI defaults (Not Found / Method Not Allowed / Internal Server Error) → fallback", () => {
    for (const detail of ["Not Found", "Method Not Allowed", "Internal Server Error", "Service Unavailable", "Bad Gateway", "Gateway Timeout"]) {
      expect(operationalError(axiosErr({ status: 500, detail }), fallback, expired)).toBe(fallback);
    }
  });

  it("422 with field validation detail → keeps the operator-authored message", () => {
    expect(operationalError(axiosErr({ status: 422, detail: "project_number is required" }), fallback, expired)).toBe("project_number is required");
  });
});

describe("TRACK 15.13H · api.js interceptor contract (smoke / source check)", () => {
  it("active-portal branch absorbs 401 without clearing any token", () => {
    // Static smoke — verifies the 15.13H fix is in the source.
    // The active-portal branch must NOT clear any token (a single
    // 401 on a feature endpoint is not proof of session expiry)
    // and must set `_namespacedHandled = true` so the global modal
    // is suppressed.
    const fs = require("node:fs");
    const path = require("node:path");
    const src = fs.readFileSync(path.resolve(__dirname, "../api.js"), "utf-8");
    expect(src).toMatch(/TRACK 15\.13H/);

    // Pull just the `if (activePortal) { … } else {` block.
    const activeBlock = src.match(/if \(activePortal\) \{[\s\S]*?\n        \} else \{/);
    expect(activeBlock).toBeTruthy();
    const text = activeBlock[0];

    // Must set namespace-handled flag.
    expect(text).toContain("_namespacedHandled = true");
    // Must NOT call any clearXToken() inside the active branch (the
    // legacy fallback below is allowed to wipe everything when there
    // is NO active portal, but the active branch must be soft).
    expect(text).not.toMatch(/clearHrToken\(\)/);
    expect(text).not.toMatch(/clearShopToken\(\)/);
    expect(text).not.toMatch(/clearAdminToken\(\)/);
    expect(text).not.toMatch(/clearPmToken\(\)/);
  });
});
