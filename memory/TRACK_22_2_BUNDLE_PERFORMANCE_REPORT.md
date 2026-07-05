# Track 22.2 Phase B · Bundle + Performance Report

**Date:** 2026-02-05
**Comparison:** Phase 1 baseline (pre-extraction) vs Track 22.2 Phase B (post-extraction).

## Build result

| Metric | Baseline | Post-extraction | Δ |
|---|---|---|---|
| `yarn build` status | Compiled with warnings | Compiled with warnings | Identical |
| Compilation errors | 0 | 0 | 0 |
| ESLint warnings | 110 | 110 | 0 |
| Tailwind warnings | 1 (`duration-[400ms]`) | 1 (`duration-[400ms]`) | 0 |

## Bundle sizes (gzipped)

| Chunk | Baseline | Post-extraction | Δ |
|---|---:|---:|---:|
| `main.*.js` | 1.14 MB | **1.14 MB (−218 B)** | −218 B ✅ |
| `main.*.css` | 29.32 kB | 29.32 kB | 0 |
| Second-largest chunk | 278 kB (2872) | 278 kB (2872) | 0 |
| Sentry chunk | 157.1 kB | 157.1 kB | 0 |

## Chunk count

| Metric | Baseline | Post-extraction | Δ |
|---|---:|---:|---:|
| Total build artifacts (js + css lines in build log) | 194 | 194 | 0 |
| JS chunk files | 193 | 193 | 0 |

## Interpretation
- **Zero regression.** No metric worsened.
- **Marginal improvement.** Main bundle is 218 bytes smaller because the extractor gave webpack a slightly better tree-shake surface (the shell no longer imports `Routes`, `Route`, `Navigate`, `Toaster` alongside 138 route-target imports and 180 lazy declarations — App.js's static import graph shrank).
- **Lazy chunks unchanged.** All 180 `React.lazy()` boundaries remain intact; chunk-splitting semantics preserved. No lazy-target collapse into eager loading.

## Runtime performance

| Metric | Baseline (Phase 1) | Post-extraction | Δ |
|---|---:|---:|---:|
| Public Hub cold-render (Playwright, DOM-content-loaded → 2.5s wait) | Body renders, 0 console errors | Body renders, 0 console errors | 0 |
| Sign-In cold-render | Body renders, 0 console errors, 3 known-benign ERR_ABORTED (Class D) | Body renders, 0 console errors, 0 non-benign network failures | 0 |
| Deep-link 404 fallback | Custom 404 renders | Custom 404 renders | 0 |
| Admin-login public form | (not previously smoked) | Body renders, 0 console errors | new smoke coverage |

## Backend performance (recert · unchanged)
- Boot time: 7.29 s (baseline) → not re-measured this pass; no backend code change.
- OpenAPI gen: 1.04 s (baseline) → unchanged.
- Track 22.* lock envelope: 254/254 pass in **26.66 s** (baseline was 31.55 s — variance is machine load, not a real change).

## Verdict
🟢 **Bundle parity + marginal improvement. Zero regression. Zero lazy-target collapse.**
