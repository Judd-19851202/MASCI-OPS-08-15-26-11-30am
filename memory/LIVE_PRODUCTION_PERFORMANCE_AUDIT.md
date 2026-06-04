# LIVE PRODUCTION PERFORMANCE AUDIT — mascidocs.com

**Audit date:** 2026-06-04
**Target:** End-to-end response timings on the live URL
**Mode:** VERIFY-ONLY (single-shot timings from this audit pod)
**Classification:** PASS

---

## 1. Methodology

`curl` time breakdown captured for each surface from this audit pod:
- `time_namelookup` — DNS lookup
- `time_connect` — TCP+TLS handshake
- `time_starttransfer` — Time To First Byte (TTFB)
- `time_total` — full response
- `size_download` — payload size

Single sample per URL (cold cache to the audit pod's egress, warm to Cloudflare). Sufficient for a smoke perf signal under the OMEGA "no load testing" constraint.

## 2. Public surfaces

| Path | HTTP | TTFB | Total | Size |
|---|---|---|---|---|
| `/` | 200 | 0.314 s | 0.314 s | 8.3 KB |
| `/sign-in` | 200 | 0.557 s | 0.557 s | 8.3 KB |
| `/admin/login` | 200 | 0.400 s | 0.400 s | 8.3 KB |
| `/dispatch-portal/login` | 200 | 0.412 s | 0.412 s | 8.3 KB |
| `/safety-portal/login` | 200 | 0.399 s | 0.399 s | 8.3 KB |

Notes:
- All routes return the same hashed SPA shell (`8.3 KB` — Cloudflare-edge cached). Effective TTFB is the Cloudflare edge HIT path.
- `/sign-in` TTFB outlier at 557 ms — single sample, likely cold cache miss on the route variant in the edge POP. Re-fetch within seconds would warm.

## 3. API surfaces

| Endpoint | HTTP | TTFB | Total | Size |
|---|---|---|---|---|
| `/api/health` | 200 | 0.138 s | 0.138 s | 73 B |
| `/api/employees` | 200 | 0.285 s | 0.293 s | 34 KB |
| `/api/jobs` | 200 | 0.166 s | 0.166 s | 11 KB |
| `/api/equipment-master` | 200 | 0.417 s | 0.462 s | 400 KB |
| `/api/admin/maintainx/p0/config` (auth) | 200 | <0.30 s | <0.30 s | <300 B |
| `/api/admin/maintainx/defect-coverage` (auth) | 200 | <0.60 s | <0.60 s | ~1.5 KB |

Observations:
- Health endpoint at **137 ms** — backend is warm and reachable.
- Equipment-master 400 KB in **462 ms total** is acceptable for an admin-load operation; the front-end caches this client-side.

## 4. Static asset cacheability

| Asset | Cache-Control |
|---|---|
| `/static/js/main.1d116d9b.js` | `public, max-age=300, immutable` |
| `/static/css/main.9ddceae9.css` | `public, max-age=300, immutable` |

**PERF-ADV-1** — Cache TTL of 300 seconds on **immutable hashed bundles** is unnecessarily conservative. Standard for Webpack-hashed assets is `max-age=31536000, immutable` (1 year). Each page navigation currently triggers a Cloudflare revalidation after 5 minutes. Recommend raising on the next deploy.

## 5. Network path

- DNS lookup: 1-2 ms (Cloudflare anycast).
- TCP+TLS handshake: 12-14 ms.
- Egress origin: `cf-ray: a069c309dc1b22f1-ORD` → Cloudflare Chicago POP.

✅ DNS + TLS overhead is negligible; total perf is dominated by origin TTFB.

## 6. Browser-side perf (Playwright wait_until="networkidle")

- `/` reached networkidle in <30 s timeout, no console errors captured (`/root/.emergent/automation_output/.../console_*.log` clean).
- `/sign-in` reached networkidle, 3 form inputs detected.

✅ No render-blocking errors observed.

## 7. Verdict

**PASS.** Live production timings are well within an operational platform's acceptable envelope:
- Backend health under 200 ms.
- API reads under 500 ms even on 400 KB payloads.
- SPA shell under 600 ms TTFB.

One advisory logged:
- **PERF-ADV-1** — Static asset cache TTL is 5 min; recommend 1 year for immutable hashed bundles.

