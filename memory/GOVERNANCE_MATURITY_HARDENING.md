# Governance Maturity Hardening — Phase IV-BETA.5A-P1D

*iter437 · 2026-02-27*
*Status: 🟢 INSTRUMENTS EXTENDED · WARNING-ONLY CONTRACT PRESERVED*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Mandate

Expand the doctrine governance instrument set with **three new
aggregates** — calmness ranking, hierarchy consistency, escalation-noise
scoring — without escalating any of them to deploy-blocking. Operator
trust depends on instruments that **inform**, not gate.

## II. New aggregates (🟢 IMPLEMENTED)

All three are produced by:

```
python3 /app/scripts/diff_doctrine_baseline.py --summary
```

Wired into `pre_deploy_check.sh` as a new warning-only stage:

```
Governance · doctrine maturity aggregates (warning-only)
```

### Aggregate 1 — Portal calmness ranking

Sort governed portals by **desktop loudness composite**, ascending.

Sample output (post iter437 IV-BETA.5A):

```
governance maturity · calmness ranking (desktop, ascending loudness)
  · pm      26.86 / 100   stable
  · admin   36.15 / 100   stable
  · hr      64.71 / 100   monitor
  · safety  66.78 / 100   monitor
```

Calibrated bands:

| Band | Range | Read |
|---|---|---|
| stable | ≤ 45 | Within doctrine calm band |
| monitor | 45–75 | Elevated, often by data-bound badge density (not decorative loudness) |
| drift | > 75 | Review recommended |

### Aggregate 2 — Hierarchy consistency scoring

For each portal, count distinct `hierarchy_hash` values across the
three viewports (desktop · iPad · mobile). A portal with **one** hash
across all three has a stable hierarchy; two or more = split (potential
responsive-design drift).

Sample output:

```
governance maturity · hierarchy consistency (desktop / ipad / mobile)
  · admin  consistent   (1 distinct hierarchy hash(es))
  · hr     consistent   (1 distinct hierarchy hash(es))
  · pm     consistent   (1 distinct hierarchy hash(es))
  · safety consistent   (1 distinct hierarchy hash(es))
```

Every portal is currently **consistent** across viewports — a strong
trust signal that the hierarchy is responsive, not fragmented.

### Aggregate 3 — Escalation-noise composite

For each portal, compute:

```
composite = hue_family_count * 4  +  badge_density
```

Lower = calmer. The formula intentionally weights hue families more
than badges because hues fragment the eye while badges (when
data-bound) are doctrine-preserved true signal.

Sample output:

```
governance maturity · escalation noise composite (lower = calmer)
  · admin  hues=5 · badge_density= 2.15 · composite= 22.1
  · hr     hues=2 · badge_density=14.71 · composite= 22.7
  · pm     hues=3 · badge_density= 2.86 · composite= 14.9
  · safety hues=2 · badge_density=12.78 · composite= 20.8
```

PM has the lowest composite (14.9). HR is the highest (22.7) but only
because it surfaces the most data-bound operational badges (overdue,
expirations). Safety is **lower** than HR even though both have only
2 hue families — Safety's badge density is slightly lower.

## III. What stayed WARNING-ONLY (🟢)

All P1D instruments are **non-blocking**:

| Stage | Mode |
|---|---|
| `stage_governance_coaching_sublines` | warning-only (existing) |
| `stage_governance_admin_copy` | warning-only (existing) |
| `stage_governance_visual_loudness` | warning-only (existing) |
| `stage_governance_doctrine_drift` | warning-only (existing) |
| `stage_governance_doctrine_maturity` (NEW) | **warning-only** |

The deploy gate still only blocks on the original P0 classes:
- Admin-token leaks (Playwright)
- Preview contamination
- Env identity mismatch
- Broken auth routing

This preserves the operator's contract: *governance instruments inform,
they do not gate*.

## IV. Trend-data plan (🟢)

Per the existing doctrine, none of these aggregates are calibrated
into block-deploy thresholds until **3+ iterations of trend data**
have been observed. With the iter437 IV-BETA.5A run, we are at
**iteration 1** of the per-portal aggregate set. Earliest gate
escalation: iter437 IV-BETA.5C (3 iterations from now).

## V. What was deliberately NOT done (🟢)

Per the directive:

- ❌ NO dashboard surface for these aggregates
- ❌ NO chart
- ❌ NO emoji severity icons
- ❌ NO change in the deploy-gate posture (still warning-only)
- ❌ NO new collection in MongoDB
- ❌ NO new permission scope
- ❌ NO change to the `pre_deploy_check.sh` failure logic

## VI. How operator uses these (🟢)

Two surfaces:

1. **`pre_deploy_check.sh` stdout** during any deploy — the new stage
   prints three small tables (≤ 10 lines each).
2. **`python3 scripts/diff_doctrine_baseline.py --summary`** locally.

Plus the existing operator-facing `GovernanceHealthChip` (P1A) which
surfaces the single most-important signal — the portal's drift state —
on every Hub V2 in a single quiet line of text.

## VII. Doctrine reaffirmed

- ✅ All P1D aggregates are warning-only
- ✅ No deploy gate posture change
- ✅ No new dashboard surface
- ✅ No DB writes · no new collections
- ✅ Operator can audit aggregates locally any time
- ✅ Preview only · no production deploy
