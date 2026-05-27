# PM Governance Script Report — Phase IV-BETA.2

**Iteration:** iter437 · Phase IV-BETA.2 · 2026-02-27
**Status:** 🟢 3 GOVERNANCE INSTRUMENTS SHIPPED · INFORMATIONAL v1 · DEPLOY-GATE WIRING DEFERRED TO IV-BETA.4

## I. Scripts shipped

| Script | Path | Purpose | Mode |
|---|---|---|---|
| `verify_coaching_sublines.py` | `/app/scripts/verify_coaching_sublines.py` | Enforce 14-word budget · banned phrases · doctrine compliance on governed sidebar/section files | informational + exit-code |
| `verify_admin_copy.py` | `/app/scripts/verify_admin_copy.py` | Detect terminology drift / AI-tone / marketing-slop across all frontend JSX | informational + exit-code |
| `measure_visual_loudness.py` | `/app/scripts/measure_visual_loudness.py` | Playwright-driven per-surface loudness score across 3 viewports · trendline log | governance instrument |

## II. `verify_coaching_sublines.py`

### Scope (intentionally narrow this iteration)

Scans ONLY governance-critical files where sublines drive the operator's first-glance understanding:
- `frontend/src/components/admin/sidebar/domainMap.js`
- `frontend/src/components/pm/sidebar/domainMap.js`
- `frontend/src/pages/pm/PmSections.jsx`

### Rules enforced

1. ✅ Banned phrases (Welcome to · Easily · Simply · AI-powered · Empower · Seamless · Just submit/click/tap · Click here · Oops · etc. — 24 patterns total)
2. ✅ No emoji in coaching strings
3. ✅ No exclamation marks in subline/desc/intro fields
4. ✅ 14-word budget per `subline`, `desc`, `coaching_subline` field

### Current result

```
✅ verify_coaching_sublines: all governed sublines pass doctrine
```

### IV-BETA.4 deploy-gate plan

When wired into `scripts/pre_deploy_check.sh`, build fails on exit-code 1.

## III. `verify_admin_copy.py`

### Scope (broader · informational v1)

Scans ALL `frontend/src/**/*.{jsx,js,tsx}` excluding:
- `node_modules`
- Test files
- The two domainMap files (gate input, doctrine references quote forbidden words)
- Storybook

### Rules enforced (24 patterns)

Same banned-phrase catalog as the coaching gate, plus:
- Vague labels (`"Click here"`, `"Tap here"`, `"Manage X"`, `"More info"`)
- Non-canonical state names (`"In Review"`)
- Casual error tones (`Oops`, `Whoops`, `Uh oh`)
- Patronizing adverbs (`Simply`, `Easily`, `Just submit/click/tap/do`)

### Current run (v1 informational)

Surfaces ~30 violations · cataloged:

| Category | Count | Notes |
|---|---|---|
| `Unlock` button text (DevLogin · FieldLeadership · NewSafetyEquipmentIssuance) | 3 | Real UI · IV-BETA.3 cleanup |
| "Simply" / "simply" in source-code comments | ~10 | False positives · improve gate in v2 to skip `/* */` and `//` |
| Training-topic content (lab/milling/trucking) describing operator behavior | ~4 | Educational hazards content · IV-BETA.4 gate refinement to exclude `lib/topics/**` |
| "Just tap" in i18n strings (PassKey CTA) | 2 | Real copy · IV-BETA.3 |
| "seamlessly" in TrainingTrack comment | 1 | False positive · code comment |

### Known limitations (informational v1)

- No JSX-AST parsing yet — grep-based · catches false positives in code comments
- Does not parse JSX expression context (cannot distinguish a string literal that becomes a UI label vs. one that's a runtime constant)

### IV-BETA.4 refinement plan

- Switch to AST-based JSX scan (babel-parser)
- Whitelist `lib/topics/` (training-content corpus)
- Skip code comments
- Then wire into deploy gate

## IV. `measure_visual_loudness.py`

### Behavior

Runs Playwright across 3 viewports × N routes × per-route metrics capture:

1. Above-fold clickables count (target ≤ 14)
2. Badge density (target ≤ 6)
3. Typography combinations (target ≤ 4)
4. Animating elements (target ≤ 1 ambient)
5. Saturated red/amber bg-class elements (target ≤ 4)
6. Hue families present (target ≤ 3)

Aggregates per-route loudness score = sum(max(0, observed - target)) across the 6 dimensions.

### Outputs

- `/app/test_reports/visual_loudness_<iter>.json` — full detailed report
- `/app/memory/LOUDNESS_TRENDLINE.json` — append-only per-iteration log

### Sample invocation

```bash
python scripts/measure_visual_loudness.py \
  --base-url https://safety-audit-mobile-1.preview.emergentagent.com \
  --routes /admin /pm /pm/daily /pm/incidents \
  --iteration iter437-iv-beta-2
```

### Known limitations (v1)

- Pixel-counter for saturation is approximated by class scan (does not OCR rendered pixels)
- Authenticated routes require pre-seeded localStorage tokens (script accepts unauthenticated initial nav · token seeding via additional flag is IV-BETA.4)
- Trendline interpretation is qualitative — IV-BETA.4 will codify per-portal regression thresholds

### IV-BETA.4 deploy-gate plan

When wired:
- Compute portal-wide average loudness
- Compare to previous deploy's average (`LOUDNESS_TRENDLINE.json`)
- Fail deploy if portal average regresses by > 5%
- Pass with monotonic trendline · record new baseline

## V. Roadmap (post-IV-BETA.2)

| Sub-phase | Script work |
|---|---|
| IV-BETA.3 | Coaching/copy cleanup using `verify_admin_copy.py` violations as backlog (DevLogin Unlock · Passkey "Just tap" · etc.) |
| IV-BETA.4 | Wire all 3 scripts into `pre_deploy_check.sh` · refine `verify_admin_copy.py` with AST parsing · loudness regression threshold codified |
| IV-BETA.5 | Final cut · scripts continue running on each deploy |

## VI. Governance posture

These scripts establish **instrumentation before enforcement**. The platform observes its own state for one iteration, then begins enforcing thresholds in IV-BETA.4. This matches the discipline of Sigma operational hardening (verify_env_identity.sh · verify_no_contamination.py) — instrument first, gate second.

## Verdict

🟢 **3 GOVERNANCE INSTRUMENTS SHIPPED · COACHING GATE PASSING · COPY GATE INFORMATIONAL · LOUDNESS SCRIPT READY FOR TRENDLINE BASELINE.** The platform can now measure its own calmness. Deploy-gate wiring lands in IV-BETA.4.
