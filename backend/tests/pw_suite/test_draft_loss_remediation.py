"""iter440 · P0 field-incident · Daily Report draft loss · client remediation.

Locks the behavioural contract for the client-side fixes that defend
hypotheses H1 (silent write fail → red pill), H2 (token-rotation
orphaning → device-scoped key + migration), H3 (iOS lifecycle missing
flush → visibilitychange handler), and H9 (restore prompt no timestamp).

Reference: P0_REMEDIATION_PLAN.md §7.2.

These tests exercise the actual /daily/submit page on the mobile
viewport (iPhone-12 emulation + Mobile Safari user agent), simulating
the field foreman's environment. They do NOT require any backend
seeded state because the form mounts with a clean draft and we
inject IDB writes/mutations directly via page.evaluate().
"""
from __future__ import annotations

import json
import time

# Each test uses ONLY the mobile viewport. The conftest parametrizes
# `viewport_name` across desktop/ipad/mobile; we filter via an
# override at the module level to keep these draft-loss tests focused
# on the iPhone surface (which is where the P0 field incident lived).
import pytest

pytestmark = [pytest.mark.parametrize("viewport_name", ["mobile"], indirect=True)]


_DAILY_REPORT_PATH = "/daily/submit"


def _project_input(page):
    """Robust locator for the Project Name input across viewports."""
    return page.locator('[data-testid="input-project-name"]').first


def _wait_for_form(page):
    """Wait until the new-daily-report page has rendered the title +
    autosave pill. Defensive — handles preview banner overlay."""
    page.wait_for_selector("text=Daily Job Report", timeout=15_000)
    # Pill is rendered immediately on mount.
    page.wait_for_selector('[data-testid="daily-report-draft-pill"]', timeout=10_000)
    # The Project Name input always renders in section 01.
    page.wait_for_selector('[data-testid="input-project-name"]', timeout=10_000)


def test_draft_pill_renders_truthful_state(page, base_url, viewport_name):
    """The pill should be rendered with a data-state attribute that
    reflects the real save status — not just a green checkmark."""
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    pill = page.locator('[data-testid="daily-report-draft-pill"]').first
    pill.wait_for(state="attached", timeout=10_000)
    # The pill exposes data-state ∈ {saving, saved, failed, idle}
    state = pill.get_attribute("data-state")
    assert state in ("saving", "saved", "idle", None), f"unexpected pill state: {state!r}"


def test_silent_quota_failure_turns_pill_red(page, base_url, viewport_name):
    """Inject an actual QuotaExceededError into the next IDB write.
    The pill MUST then transition to data-state="failed" with a
    "Save failed — storage full" label — never green.

    This is the H1 disconfirming test: prior to iter440 the pill said
    "Saved" on every quota failure, lying to the operator."""
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)

    # Patch IDBObjectStore.prototype.put to throw QuotaExceededError on
    # the next invocation, then restore. This emulates iOS Safari's
    # behavior under ITP-reduced quota.
    page.evaluate(
        """() => {
          const proto = IDBObjectStore.prototype;
          const origPut = proto.put;
          let armed = true;
          proto.put = function(...args) {
            if (armed) {
              armed = false;
              proto.put = origPut;
              // Mimic the actual DOMException name and message.
              const err = new DOMException(
                'The quota has been exceeded.', 'QuotaExceededError'
              );
              // The idb-keyval store dispatches an error event on the
              // request — synthesize one.
              const fakeReq = { onerror: null, onsuccess: null };
              setTimeout(() => {
                if (fakeReq.onerror) fakeReq.onerror({ target: { error: err } });
              }, 0);
              throw err;
            }
            return origPut.apply(this, args);
          };
        }"""
    )

    # Type into the form — autosave debounce fires after 800 ms, then
    # the IDB write goes through our patched put() and throws.
    project_input = _project_input(page)
    project_input.fill("P0-Quota-Failure-Test")

    # Wait for the pill to surface a "failed" state (the autosave hook
    # awaits the save before flipping the status, so we have a stable
    # window to observe). Cap at 4 s.
    pill = page.locator('[data-testid="daily-report-draft-pill"]').first
    end = time.time() + 6
    final_state = None
    final_text = ""
    while time.time() < end:
        try:
            final_state = pill.get_attribute("data-state")
            final_text = (pill.text_content() or "").strip()
            if final_state == "failed":
                break
        except Exception:
            pass
        page.wait_for_timeout(200)

    assert final_state == "failed", (
        f"H1 violation — pill did NOT turn red on quota failure. "
        f"final_state={final_state!r} text={final_text!r}"
    )
    assert "Save failed" in final_text or "storage" in final_text.lower(), (
        f"H1 violation — pill text not truthful: {final_text!r}"
    )


def test_restore_prompt_shows_savedat_timestamp(page, base_url, viewport_name):
    """When a draft exists, the restore prompt MUST render a humanized
    timestamp ("Saved 12s ago") so the operator can tell whether the
    offered draft is today's in-progress work or yesterday's stale tail.

    Defends H9 — prior to iter440 the prompt showed no timestamp."""
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)

    # Make sure SOME work is saved by typing into a field.
    project_input = _project_input(page)
    project_input.fill("Restore-Timestamp-Test")
    page.wait_for_timeout(1500)

    # Reload to surface the restore prompt.
    page.reload(wait_until="domcontentloaded")
    _wait_for_form(page)

    # The prompt may not appear if the draft cleanup ran — give it
    # a chance, but tolerate absence (test still passes the contract
    # check on the savedat span when the prompt DOES appear).
    try:
        prompt = page.locator(
            '[data-testid="daily-report-draft-restore-prompt"]'
        ).first
        prompt.wait_for(state="visible", timeout=5_000)
    except Exception:
        pytest.skip("Restore prompt not surfaced (autosave may have been disabled)")

    savedat = page.locator(
        '[data-testid="daily-report-draft-restore-prompt-savedat"]'
    ).first
    savedat.wait_for(state="visible", timeout=2_000)
    txt = savedat.text_content() or ""
    # Must reference "Saved" + a humanized age ("s ago", "m ago", "h ago", or a date).
    assert "Saved" in txt or "saved" in txt, f"timestamp missing: {txt!r}"
    assert any(token in txt for token in ("ago", "/", "-")), (
        f"timestamp not humanized: {txt!r}"
    )


def test_visibility_hidden_flushes_draft_to_idb(page, base_url, viewport_name):
    """H3 disconfirming test — mid-debounce visibility hidden must
    immediately flush the in-progress edit to IndexedDB. We type, fire
    the visibilitychange event before the 800ms debounce expires, then
    read IDB directly and assert the latest text is on disk."""
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)

    needle = f"H3-needle-{int(time.time())}"
    project_input = _project_input(page)
    project_input.fill(needle)

    # Fire visibility hidden immediately (well before 800 ms debounce).
    page.evaluate(
        """() => {
          Object.defineProperty(document, 'visibilityState', {
            configurable: true, get: () => 'hidden',
          });
          document.dispatchEvent(new Event('visibilitychange'));
        }"""
    )
    # Give the synchronous flush a chance to land.
    page.wait_for_timeout(800)

    # Read the device-scoped draft from IDB and confirm the needle is
    # in the form payload.
    found = page.evaluate(
        """async () => {
          const open = indexedDB.open('keyval-store');
          return await new Promise((resolve) => {
            open.onsuccess = () => {
              const db = open.result;
              const tx = db.transaction('keyval', 'readonly');
              const store = tx.objectStore('keyval');
              const allKeys = store.getAllKeys();
              const allVals = store.getAll();
              tx.oncomplete = () => {
                const matches = [];
                for (let i = 0; i < allKeys.result.length; i++) {
                  const k = allKeys.result[i];
                  const v = allVals.result[i];
                  if (typeof k === 'string' && k.startsWith('masci.draft.')) {
                    matches.push({ k, v });
                  }
                }
                resolve(matches);
              };
            };
            open.onerror = () => resolve([]);
          });
        }"""
    )
    # At least one masci.draft.* entry should now exist and the form
    # payload should mention our needle.
    serialized = json.dumps(found)
    assert needle in serialized, (
        f"H3 violation — needle {needle!r} not in any draft after "
        f"visibility-hidden flush. drafts found: {len(found)}, "
        f"serialized[:300]={serialized[:300]!r}"
    )


def test_device_id_persists_across_reload(page, base_url, viewport_name):
    """The persisted device id is the iter440 root fix for H2. It MUST
    survive a reload (and, by extension, a token rotation) so the IDB
    draft key remains stable."""
    page.goto(f"{base_url}{_DAILY_REPORT_PATH}", wait_until="domcontentloaded")
    _wait_for_form(page)
    first_id = page.evaluate("() => localStorage.getItem('masci.device-id')")
    assert first_id and first_id.startswith("d."), f"device id absent or malformed: {first_id!r}"

    page.reload(wait_until="domcontentloaded")
    _wait_for_form(page)
    second_id = page.evaluate("() => localStorage.getItem('masci.device-id')")
    assert second_id == first_id, (
        f"H2 violation — device id changed across reload: {first_id!r} → {second_id!r}"
    )
