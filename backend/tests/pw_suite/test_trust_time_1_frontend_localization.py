"""TRUST-TIME-1 · Frontend localization (Node-driven) · 2026-05-28.

Proves the new `dateUtils.js` helpers convert UTC and naive-ISO
timestamps to the operator's LOCAL browser time across the four
CONUS timezones. Uses Node's `TZ=` env var (which JavaScript honors
for `Intl.DateTimeFormat` / `toLocaleString`) — same code path as
the browser's `Intl` machinery, no Playwright dependency, ~1 s total.
"""
from __future__ import annotations

import pathlib
import subprocess
import json

import pytest


DATEUTILS = pathlib.Path("/app/frontend/src/lib/dateUtils.js")

# A tiny Node harness that imports the helpers via dynamic require.
# We translate the ES module syntax to CommonJS on-the-fly so we can
# eval it directly under Node without a bundler.
NODE_HARNESS = r"""
'use strict';
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync(process.argv[2], 'utf8');

// Strip ES export syntax so the result is plain top-level JS.
const stripped = src
  .replace(/^export\s+function\s+/gm, 'function ')
  .replace(/^export\s+const\s+/gm, 'const ');

// Run in this context so top-level function declarations land in
// the local scope (not the case with bare `eval()` for `function`).
const ctx = { console, Date, Intl };
vm.createContext(ctx);
vm.runInContext(stripped, ctx);

const utc = '2026-05-28T13:43:00Z';
const naive = '2026-05-28T13:43:00';
const probe = `JSON.stringify({
  utc_local:   formatLocalDateTime('${utc}'),
  naive_local: formatLocalDateTime('${naive}'),
  utc_time:    formatLocalTime('${utc}'),
  utc_short:   formatLocalShort('${utc}'),
  audit_utc:   formatUtcForAudit('${utc}'),
  audit_naive: formatUtcForAudit('${naive}'),
  rel_5m:      formatRelativeTime(new Date(Date.now() - 5*60*1000).toISOString()),
})`;
const out = vm.runInContext(probe, ctx);
console.log(out);
"""

HARNESS_PATH = pathlib.Path("/tmp/_trust_time_1_node_harness.js")


def _run_node(tz: str) -> dict:
    if not HARNESS_PATH.exists() or HARNESS_PATH.read_text() != NODE_HARNESS:
        HARNESS_PATH.write_text(NODE_HARNESS)
    proc = subprocess.run(
        ["node", str(HARNESS_PATH), str(DATEUTILS)],
        env={"TZ": tz, "PATH": "/usr/bin:/usr/local/bin:/root/.nvm/versions/node/v20.19.0/bin"},
        capture_output=True, text=True, timeout=20,
    )
    assert proc.returncode == 0, f"node failed: {proc.stderr}"
    return json.loads(proc.stdout.strip())


@pytest.mark.parametrize("tz,expected_hour", [
    ("America/New_York",    "9"),   # EDT in late May · UTC-4 → 09:43
    ("America/Chicago",     "8"),   # CDT · UTC-5            → 08:43
    ("America/Denver",      "7"),   # MDT · UTC-6            → 07:43
    ("America/Los_Angeles", "6"),   # PDT · UTC-7            → 06:43
])
def test_utc_timestamp_localizes_correctly(tz, expected_hour):
    r = _run_node(tz)
    assert expected_hour in r["utc_local"], (
        f"UTC 13:43 in {tz} should show hour '{expected_hour}', got: {r['utc_local']!r}"
    )
    # Naive ISO (the production bug source) must coerce to UTC then localize identically.
    assert expected_hour in r["naive_local"], (
        f"Naive '2026-05-28T13:43:00' in {tz} must coerce to UTC and show hour "
        f"'{expected_hour}'; got: {r['naive_local']!r}"
    )
    # The audit helper is tz-stable: ALWAYS shows 13:43 UTC.
    assert "13:43 UTC" in r["audit_utc"], r["audit_utc"]
    assert "13:43 UTC" in r["audit_naive"], r["audit_naive"]


def test_relative_time_is_minute_grained():
    """`formatRelativeTime` should return '5m ago' for a 5-min-old ts."""
    r = _run_node("America/New_York")
    assert r["rel_5m"] == "5m ago", r["rel_5m"]


def test_audit_helper_always_labels_utc():
    """No silent UTC display — every audit-helper output ends with 'UTC'."""
    r = _run_node("America/New_York")
    assert r["audit_utc"].endswith(" UTC"), r["audit_utc"]
    assert r["audit_naive"].endswith(" UTC"), r["audit_naive"]


def test_naive_iso_coerce_matches_utc_iso():
    """The whole point of the fix: naive ISO and `Z`-suffixed ISO must
    produce IDENTICAL localized renderings (within the same locale)."""
    for tz in ("America/New_York", "America/Chicago",
               "America/Denver", "America/Los_Angeles"):
        r = _run_node(tz)
        assert r["utc_local"] == r["naive_local"], (
            f"In {tz}: utc_local={r['utc_local']!r} vs "
            f"naive_local={r['naive_local']!r} — naive must coerce to UTC."
        )
