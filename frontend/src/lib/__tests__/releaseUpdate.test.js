/* eslint-env jest */
/* global describe, test, expect, beforeEach, afterEach, jest */

import {
  RELEASE_STATES,
  getReleaseState,
  checkNow,
  applyUpdateNow,
  onClientUpdateRequired,
  _resetReleaseUpdate,
  _setBootFingerprintForTest,
} from "@/lib/releaseUpdate";
import { markDirty, markClean, _resetDirtyWork, isAnyDirty } from "@/lib/dirtyWork";

function mockVersion(fp) {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ deployable_release_provenance: { build_deployable_fingerprint: fp } }),
    })
  );
}

describe("Zero-Stale-Client release controller", () => {
  const origReload = window.location.reload;
  let reloadSpy;
  beforeEach(() => {
    _resetReleaseUpdate();
    _resetDirtyWork();
    Object.defineProperty(navigator, "onLine", { value: true, configurable: true });
    reloadSpy = jest.fn();
    Object.defineProperty(window, "location", {
      value: { ...window.location, reload: reloadSpy },
      configurable: true,
    });
    jest.useFakeTimers();
  });
  afterEach(() => {
    jest.useRealTimers();
    window.location.reload = origReload;
    try { sessionStorage.clear(); } catch { /* noop */ }
  });

  test("first check anchors boot fingerprint and reports CURRENT (no reload)", async () => {
    mockVersion("dcf-A");
    await checkNow("startup");
    expect(getReleaseState().state).toBe(RELEASE_STATES.CURRENT);
    expect(getReleaseState().boot).toBe("dcf-A");
    expect(reloadSpy).not.toHaveBeenCalled();
  });

  test("clean client auto-reloads when a newer release appears", async () => {
    _setBootFingerprintForTest("dcf-A");
    mockVersion("dcf-B");
    await checkNow("force");
    // UPDATE_AVAILABLE → UPDATING → reload scheduled
    jest.advanceTimersByTime(100);
    expect(reloadSpy).toHaveBeenCalledTimes(1);
  });

  test("dirty work defers the reload (UPDATE_PENDING_DIRTY_WORK) and applies at safe boundary", async () => {
    _setBootFingerprintForTest("dcf-A");
    markDirty("daily-report");
    expect(isAnyDirty()).toBe(true);
    mockVersion("dcf-B");
    await checkNow("force");
    expect(getReleaseState().state).toBe(RELEASE_STATES.UPDATE_PENDING_DIRTY_WORK);
    expect(reloadSpy).not.toHaveBeenCalled();
    // Operator saves/submits → dirty clears → deferred update applies.
    markClean("daily-report");
    jest.advanceTimersByTime(100);
    expect(reloadSpy).toHaveBeenCalledTimes(1);
  });

  test("offline is reported and never reloads", async () => {
    _setBootFingerprintForTest("dcf-A");
    Object.defineProperty(navigator, "onLine", { value: false, configurable: true });
    await checkNow("force");
    expect(getReleaseState().state).toBe(RELEASE_STATES.OFFLINE);
    expect(reloadSpy).not.toHaveBeenCalled();
  });

  test("reload-loop guard stops after repeated non-sticky reloads", async () => {
    _setBootFingerprintForTest("dcf-A");
    mockVersion("dcf-B");
    // Simulate reloads that never change the served fingerprint (stale CDN).
    await checkNow("force"); jest.advanceTimersByTime(100); // 1
    await checkNow("force"); jest.advanceTimersByTime(100); // 2
    await checkNow("force"); jest.advanceTimersByTime(100); // blocked → UPDATE_FAILED
    expect(getReleaseState().state).toBe(RELEASE_STATES.UPDATE_FAILED);
    expect(reloadSpy).toHaveBeenCalledTimes(2);
  });

  test("endpoint failure never claims CURRENT (fails safe to UNKNOWN)", async () => {
    _setBootFingerprintForTest("dcf-A");
    global.fetch = jest.fn(() => Promise.reject(new Error("network")));
    await checkNow("force");
    expect(getReleaseState().state).toBe(RELEASE_STATES.UNKNOWN);
    expect(reloadSpy).not.toHaveBeenCalled();
  });

  test("CLIENT_UPDATE_REQUIRED (clean) → transitions to UPDATING and reloads", () => {
    _setBootFingerprintForTest("dcf-A");
    onClientUpdateRequired();
    expect(getReleaseState().state).toBe(RELEASE_STATES.UPDATING);
    jest.advanceTimersByTime(100);
    expect(reloadSpy).toHaveBeenCalledTimes(1);
  });

  test("CLIENT_UPDATE_REQUIRED (dirty) protects work, reloads only at safe boundary", () => {
    _setBootFingerprintForTest("dcf-A");
    markDirty("safety-form");
    onClientUpdateRequired();
    expect(getReleaseState().state).toBe(RELEASE_STATES.UPDATE_REQUIRED);
    expect(reloadSpy).not.toHaveBeenCalled(); // dirty work never destroyed
    markClean("safety-form");
    jest.advanceTimersByTime(100);
    expect(reloadSpy).toHaveBeenCalledTimes(1);
  });
});
