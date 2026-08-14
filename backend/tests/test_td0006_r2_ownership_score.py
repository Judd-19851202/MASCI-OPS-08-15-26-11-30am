"""TD-0006 — R2 storage ownership score truth.

Root cause (live production evidence, mascidocs.com, read-only):
- /api/admin/r2/lifecycle/health sub_scores.ownership_score = 15.1.
- Formula was 100 * verified_owner / classification_total, where the denominator
  INCLUDED protected_or_exempt objects (SYSTEM_RESERVED / RETENTION_PROTECTED /
  BACKUP_PROTECTED / LEGAL_HOLD / HISTORICAL). Live counts: owned=1639,
  total=10821, protected=4916 (45.4%), ambiguous=4266, confirmed_orphan=0.
  Exempt objects can NEVER be VERIFIED_OWNER, so counting them falsely deflated
  ownership coverage to 15.1% even though confirmed-orphan risk was 0%.

Truth invariants:
- Ownership coverage is measured over ATTRIBUTABLE objects (total - protected).
- AMBIGUOUS/PENDING remain in the denominator (genuine resolution backlog).
- All-exempt population => 100 (nothing to attribute), never a false 0.
"""
from backend.services.r2_lifecycle.health import compute_ownership_score


def test_exempt_objects_excluded_from_denominator():
    # Live production shape.
    score = compute_ownership_score(owned=1639, total=10821, protected=4916)
    # attributable = 10821 - 4916 = 5905 ; 1639/5905 = 27.76%
    assert round(score, 1) == 27.8
    # And it is strictly higher than the old exempt-contaminated 15.1.
    assert score > 15.1


def test_ambiguous_still_penalizes_coverage():
    # 100 attributable objects, 40 owned, 60 ambiguous, 0 protected.
    score = compute_ownership_score(owned=40, total=100, protected=0)
    assert score == 40.0  # ambiguous backlog is NOT hidden


def test_all_exempt_is_not_a_deficiency():
    score = compute_ownership_score(owned=0, total=500, protected=500)
    assert score == 100.0  # nothing eligible to attribute -> honest 100, not 0


def test_fully_owned_attributable_is_100():
    score = compute_ownership_score(owned=300, total=800, protected=500)
    # attributable = 300 ; 300/300 = 100
    assert score == 100.0


def test_zero_total_is_safe():
    assert compute_ownership_score(owned=0, total=0, protected=0) == 100.0
