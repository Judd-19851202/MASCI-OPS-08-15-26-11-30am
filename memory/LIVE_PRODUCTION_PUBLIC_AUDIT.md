# LIVE PRODUCTION PUBLIC AUDIT — mascidocs.com

**Audit date:** 2026-06-04
**Audit window:** ~20:42 UTC
**Target:** `https://mascidocs.com`
**Mode:** VERIFY-ONLY · NO CODE CHANGES · NO WRITES
**Classification:** PASS WITH ADVISORIES

---

## 1. Reachability

| Probe | Result |
|---|---|
| HTTPS root `GET /` | `200 OK`, 8.3 KB SPA shell, TTFB 314 ms |
| `GET /api/health` | `200 OK` · body `{"ok":true,"service":"masci-hub","ts":"…"}` · TTFB 137 ms |
| Edge | Cloudflare (`server: cloudflare`, `cf-ray` present) |
| TLS | HTTP/2 over TLS, valid cert (cf-managed) |

## 2. Security headers on HTML root

```
strict-transport-security: max-age=63072000; includeSubDomains; preload
x-content-type-options: nosniff
referrer-policy: strict-origin-when-cross-origin
cache-control: public, max-age=300
access-control-allow-origin: *      ← static HTML edge cache, NOT API
```

✓ HSTS at 2 years + preload + subdomains.
✓ `nosniff` enforced.
✓ Referrer Policy is sane (`strict-origin-when-cross-origin`).
ℹ The `Access-Control-Allow-Origin: *` here is the **Cloudflare edge** serving the static SPA — confirmed not present on `/api/*`. See `LIVE_PRODUCTION_AUTH_AUDIT.md` for the API-side CORS verification.

## 3. SPA shell sanity

- Title: `MASCI Operations Platform`
- Branded favicon set (multiple sizes) + Apple touch icons + manifest.
- OpenGraph/Twitter card metadata correct (`og:url=https://mascidocs.com/`, `og:image=/og-image.png`).
- PostHog analytics initialised under `phc_yJW…OTFE` (existing telemetry — no change).
- Emergent runtime script `https://assets.emergent.sh/scripts/emergent-main.js` present (deploy artefact, expected).
- ⚠️ **No preview banner** on production root — confirms `APP_ENV` is **not** `preview` (correct).

## 4. Static asset surface

Hashed bundles served from `/static/`:
- `/static/js/main.1d116d9b.js` → `200`, `cache-control: public, max-age=300, immutable`
- `/static/css/main.9ddceae9.css` → `200`, `cache-control: public, max-age=300, immutable`

ADVISORY → `max-age=300` on **immutable** hashed bundles is extremely conservative. Browsers will revalidate every 5 minutes despite the immutable directive helping. A pure-static asset hashed by Webpack is safe to cache for 1 year (`max-age=31536000`). Recommend raising on the next deploy.

## 5. robots / sitemap discoverability

| Path | HTTP | Body |
|---|---|---|
| `/robots.txt` | `200` | SPA `index.html` shell (fallback) |
| `/sitemap.xml` | `200` | SPA `index.html` shell (fallback) |

ADVISORY → No real `robots.txt` or `sitemap.xml` is served. Crawlers will index this as a JS SPA with no directives. Acceptable for a private operations platform but recommend adding a `Disallow: /` `robots.txt` if you want to prevent indexing entirely.

## 6. Public-marketing surfaces (no auth)

- `/sign-in` — public multi-portal sign-in (email + master password, "Remember Me", direct portal links).
- `/cheatsheet` — public printable foreman cheat sheet (per `test_credentials.md` line 346 — not re-probed; not change-relevant).
- Hub home `/` — branded marketing-style landing with three primary tiles (Field, QA/QC, Safety) and a sign-in CTA top-right.

Visual smoke screenshot captured at `/tmp/prod_home.png` and `/tmp/prod_signin.png` for record.

## 7. Public POST hardening (verified via routes)

Per server config, the following public POSTs are rate-limited at `PUBLIC_POST_LIMIT_PER_HOUR` per IP, magic-byte validated on PDF, and forced to `application/pdf` + `X-Content-Type-Options: nosniff` on download:
- `/api/inspections`, `/api/meetings`, `/api/jhas`, `/api/incidents`, `/api/daily-reports`, `/api/equipment-inspections`, `/api/equipment-units`, `/api/translate`.

Not flood-tested live (per OMEGA — no writes). Header behaviour verified on the static layer.

## 8. Verdict

**PASS.** Public surface is HTTPS-only, edge-cached, HSTS-preloaded, branded, with correct env (no preview banner). Two minor advisories above (cache TTL, robots/sitemap) — non-blocking.

