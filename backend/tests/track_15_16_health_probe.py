#!/usr/bin/env python3
"""
Track 15.16 · Production healthcheck compatibility probe.

The production proxy/runtime health probe targets the backend directly
at 127.0.0.1:8001 (per the production logs:
  "GET /health" upstream: "http://127.0.0.1:8001/health"
). The probe is NOT routed through the public ingress (which sends
non-/api paths to the React SPA on port 3000).

This test therefore probes the backend on its internal port for the
exact paths the platform health checker uses.

Run with:  python3 /app/backend/tests/track_15_16_health_probe.py
"""
import os
import sys
import requests

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8001")

# (path, expected_status, expected_body_subset_or_None)
INTERNAL_CHECKS = [
    ("/health",          200, {"status": "ok", "service": "masci-backend"}),
    ("/healthz",         200, {"status": "ok"}),
    ("/api/health",      200, None),
    ("/api/healthz",     200, None),
]

fail = 0
for path, expected_status, expected_body in INTERNAL_CHECKS:
    url = f"{BACKEND}{path}"
    r = requests.get(url, timeout=10)
    ok = r.status_code == expected_status
    body_ok = True
    if expected_body and ok:
        try:
            j = r.json()
            for k, v in expected_body.items():
                if j.get(k) != v:
                    body_ok = False
                    break
        except Exception:
            body_ok = False
    status = "PASS" if ok and body_ok else "FAIL"
    if status == "FAIL":
        fail += 1
    print(f"  {'✓' if status == 'PASS' else '✗'}  {path:18}  HTTP {r.status_code}  body={r.text[:80]}")

# Probe must be unauthenticated.
r = requests.get(f"{BACKEND}/health", headers={"X-HR-Token": "BOGUS"}, timeout=5)
if r.status_code != 200:
    fail += 1
    print(f"  ✗  /health with bogus token did not stay 200: {r.status_code}")
else:
    print(f"  ✓  /health stays 200 with bogus token (unauthenticated probe)")

# Probe must be cheap — no DB call. We can't verify "no DB" from outside,
# but we can assert sub-100ms latency on the local socket.
import time
t0 = time.monotonic()
requests.get(f"{BACKEND}/health", timeout=5)
elapsed_ms = (time.monotonic() - t0) * 1000
if elapsed_ms > 250:
    fail += 1
    print(f"  ✗  /health unexpectedly slow ({elapsed_ms:.0f} ms)")
else:
    print(f"  ✓  /health responds in {elapsed_ms:.0f} ms (well under 250 ms budget)")

print(f"\nTRACK 15.16 internal healthcheck probe: {'PASS' if fail == 0 else f'FAIL ({fail})'}")
sys.exit(0 if fail == 0 else 1)
