# M0.2A · ODR Bilingual Probe Report

_Generated 2026-05-29 · env=preview · db=masci_safety_preview._

This is the human-readable companion to the probe-generated
`/app/memory/ODR_BILINGUAL_PROBE_REPORT.md` (auto-refreshed on every
probe run).

## Probe purpose

Defend the **bilingual + coaching coverage contract** for the OGC
catalog so the M0.3 frontend can rely on every prompt_key resolving
to ≥4 EN + ≥4 ES bullets, with crew overlays where declared.

## Probe surface

Seven invariants over the live catalog + live ODR data:

| ID | Invariant |
|---|---|
| B1 | ≥ 1 prompt_key per ODR section |
| B2 | ≥ 4 EN bullets AND ≥ 4 ES bullets per prompt_key |
| B3 | Crew overlays (if declared) carry ≥ 4 bullets per language |
| B4 | No empty / whitespace-only bullets |
| B5 | Crew universe coverage — every `enum.CrewType` resolves (overlay or fallback) |
| B6 | Every live `odr.readiness.coaching_prompts[*].prompt_key` exists in catalog (orphan-key guard) |
| B7 | LocalizedString shape integrity in live ODR data (`original` requires `original_lang`) |

## Live result (M0.2A ship)

```
odr_bilingual_probe · env=preview · db=masci_safety_preview
  prompt_keys=14  EN_min4=14  ES_min4=14
  ODRs scanned=5  failures=0  warnings=1
  ✅ all checks passed
```

The single warning is the cosmetic `subcontractors` / `review`
section soft-warn — neither has a coaching prompt yet because there
is no surface-driven hard stop on either. Adding either is purely
optional and only triggers a B1 warning.

## Gate integration

Wired into `/app/scripts/pre_deploy_check.sh` as a hard-blocking stage:

```
run_stage "Phase V.1 · ODR bilingual probe" stage_odr_bilingual
```

Sub-second probe.

## Failure response (operator playbook)

| Failure | Most likely cause | Remediation |
|---|---|---|
| B1 hard-missing section | new ODR section shipped without coaching | add ≥1 prompt_key in `guidance_catalog.py` |
| B2 EN/ES floor breach | bullet list edited in error | restore the missing bullet(s) · re-run probe |
| B3 crew overlay below floor | new overlay shipped with < 4 bullets | fill the overlay; do not ship partial overlays |
| B4 empty bullet | accidental empty-string commit | replace or remove |
| B5 enum crew not in catalog universe | new CrewType added to enums.py without updating catalog | add the crew to `CATALOG_CREW_TYPES` |
| B6 orphan prompt_key in live data | readiness emitted a prompt_key that no longer exists in catalog | rename catalog key OR fix the readiness emit site |
| B7 LocalizedString shape | translation pipeline wrote `original` without `original_lang` | fix the translator; warning-only at M0.2A |

## Status

🟢 **GREEN.** Bilingual + crew-aware coaching surface is operationally
trustworthy. Probe ready for production.
