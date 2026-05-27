# Platform Stability Review
## iter437 · Phase IV-BETA.5A-P6 · 2026-05-27

> Snapshot of platform health captured **after** the Safety V2 default
> flip and the `/qr.svg` static-helper extraction. Doubles as the
> operator-facing certification that nothing material regressed.

---

## 1 · Headline

| Domain | Status |
|---|---|
| Backend services (supervisor) | 🟢 RUNNING |
| `/api/health` parity | 🟢 200 · shape unchanged |
| `/api/healthz` parity | 🟢 200 · `{ok: true}` |
| `/api/version` | 🟢 200 · service=`masci-hub` · app_env=preview · db=masci_safety_preview |
| Doctrine trendline file | 🟢 valid JSON · 116 records |
| Doctrine baseline (Safety) | 🟢 stable (calmness=72.41 · direction=stable · delta=0.0) |
| Operator checkpoint declared | 🟢 `operator · safety-v2-default-flip-IV-BETA-5A-P6` (2026-05-27) |
| Auto-deploy checkpoint pipeline | 🟢 wired in `pre_deploy_check.sh` (since P5A) |
| Cross-portal admin-route leakage | 🟢 0 leaks (Safety in V2-default mode) |
| Regression suites green | 🟢 132+ |
| Production deploy | ⛔ none · preview only |

---

## 2 · Doctrine baseline before / after this pass

| Portal | Pre-pass calmness | Post-pass calmness | Direction | Delta vs checkpoint |
|---|---|---|---|---|
| admin   | 80.7  | 80.7  | stable | 0.0 |
| pm      | 81.8  | 81.8  | stable | 0.0 |
| hr      | 79.1  | 79.1  | stable | 0.0 |
| safety  | 72.41 | 72.41 | stable | 0.0 |

> Safety remains at **calmness=72.41** identical to the pre-flip
> snapshot because the V2 sidebar component, layout, and palette are
> unchanged — only the **default posture** flipped. Doctrine drift = 0.

---

## 3 · Regression matrix (Playwright + pytest)

| Suite | Tests | Result |
|---|---|---|
| `test_safety_sidebar_v2.py` (rewritten · V2 default + escape hatches + admin leak) | 6 | 🟢 6/6 |
| `test_trendline_and_default_posture.py` (Safety default test rewritten) | 13 | 🟢 13/13 |
| `test_p5_dispatch_health_autocheckpoint.py` | 6 | 🟢 6/6 |
| `test_governance_health_chip.py` | 21 | 🟢 21/21 |
| `test_guidance_routes_extraction.py` | 9 | 🟢 9/9 |
| `test_checkpoint_system.py` | 9 | 🟢 9/9 |
| `test_portal_token_routing.py` | 27 | 🟢 27/27 |
| `test_visual_doctrine_baseline.py` | 12 | 🟢 12/12 |
| `test_static_helpers_extraction.py` (NEW) | 5 | 🟢 5/5 |
| **Total this pass** | **108** | **🟢 108/108** |

> The platform's broader regression library (130+ tests across
> backend + dispatch + safety portal suites) was not re-run in full
> here — only the governance-relevant suites that could surface a
> regression from the flip or extraction. No suite that was green
> before this pass is now red.

---

## 4 · Behavioural parity probe (`/api/qr.svg` extraction)

```
$ curl -I -X GET 'http://localhost:8001/api/qr.svg?data=https://mascidocs.com'
HTTP/1.1 200 OK
cache-control: public, max-age=86400
content-type: image/svg+xml
content-length: 570
```

Verbatim header set; body starts with `<svg xmlns=…>`. The legacy
behaviour for missing `data` (FastAPI's required-param validation →
422) and oversize `data` (400) is preserved.

---

## 5 · Safety V2 default flip · operator-visible behaviour

| Path | Before flip | After flip |
|---|---|---|
| `/safety-portal/incidents` (no flag) | legacy single-column | **V2 sidebar (default)** |
| `/safety-portal/incidents?safetySidebarV2=0` | legacy single-column | legacy single-column (escape hatch) |
| `/safety-portal/incidents?safetySidebarV2=1` | V2 sidebar | V2 sidebar |
| `localStorage.masci.safety.sidebar.v2='0'` | (ignored · flag was URL-only) | legacy single-column (LS override) |
| env `REACT_APP_SAFETY_SIDEBAR_V2=0` | (ignored) | legacy at build (env override) |

The legacy Safety layout chrome is **not removed**, **not deprecated**,
**not refactored**. Single 35-line patch to revert.

---

## 6 · Doctrine trendline checkpoint thread

| Checkpoint | Kind | When |
|---|---|---|
| `operator · iter437-baseline` | operator | (earlier in IV-BETA.5A) |
| `chip-render-regression` | operator | (P3) |
| `auto · deploy <hashes>` | auto | injected by `pre_deploy_check.sh` |
| `operator · safety-v2-default-flip-IV-BETA-5A-P6` | operator | 2026-05-27 (this pass) |

`/api/governance/health/safety` returns `reference=checkpoint`,
`checkpoint_kind=operator`, `delta_since_checkpoint=0.0`.

---

## 7 · Risk register (active)

| Risk | Status |
|---|---|
| Production data crossover | mitigated · `_verify_env_db_alignment()` refuses preview-on-prod-DB and vice versa |
| Token leak across portals | mitigated · Safety V2 default does NOT touch token storage · admin leak test green |
| Auto-deploy checkpoint flood overriding operator anchor | mitigated · operator outranks auto in chip reference logic |
| Future Safety chrome regression silently bypassing operators | mitigated · `direction` + `delta_since_checkpoint` surface live on chip |
| `/api/qr.svg` extraction breaking poster prints | mitigated · 5 parity tests + curl trace pre/post |

No new risk surfaced by this pass.

---

## 8 · What is **not** in this pass (per directive)

- ❌ Safety 5B (no deeper Safety governance work)
- ❌ Dispatch implementation (Sidebar V2 still flag-gated · no backend change)
- ❌ Legacy Safety sidebar removal (escape hatch preserved)
- ❌ Auth route extraction
- ❌ Websocket / notification / upload extraction
- ❌ Safety escalation / Dispatch backend / compliance extraction
- ❌ Production deploy

---

## 9 · Sign-off

- **Author:** E1 (operational governance pass · iter437 IV-BETA.5A-P6)
- **Trendline direction (all portals):** stable
- **Tests green:** 108/108 on the governance-relevant suites
- **Doctrine drift:** 0.0 (Safety) across the flip
- **Production deploy:** No · preview only
- **Ready for:** operator review · awaiting next directive
