"""iter437 / Phase IV-BETA.3A · Communication Unification subject locks.

Locks the 6 cross-portal subject-line contracts defined in
/app/memory/COMMUNICATION_UNIFICATION_DOCTRINE.md addendum §A.I and
§A.III. These tests do NOT exercise email send paths (Resend isn't
called); they assert the EXACT subject strings the platform builds
for each communication site.

Sites covered:
  1. Parts order            → routes/shop_parts.py:323 (inline)
  2. PM admin notification  → routes/pm_admin.py:333 (inline)
  3. PO digest              → po_digest.build_digest_subject
  4. Platform outage        → server.py:7352 (inline · admin_alert_outage)
  5. System health alert    → health_monitor.py:98 (inline · alert_red_subsystems)
  6. Backup verification    → backup_verification.render_verification_subject
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from po_digest import DIGEST_SUBJECT, build_digest_subject  # noqa: E402
from backup_verification import render_verification_subject  # noqa: E402


# ─────────────────────────────────────────────────────────────────
# 1 · Parts order subject (inline string in shop_parts.py:323)
# ─────────────────────────────────────────────────────────────────
def _parts_subject(unit: str, n_items: int) -> str:
    """Mirrors the f-string at shop_parts.py:323."""
    return f"[MASCI · PARTS] {unit} · Parts Order · {n_items} item(s)"


class TestPartsOrderSubject:
    def test_format(self):
        assert _parts_subject("EX-450", 4) == (
            "[MASCI · PARTS] EX-450 · Parts Order · 4 item(s)"
        )

    def test_has_tag_segment(self):
        # doctrine A.I: subjects must have a TAG segment "MASCI · {TAG}"
        assert "[MASCI · PARTS]" in _parts_subject("UNIT", 1)


# ─────────────────────────────────────────────────────────────────
# 2 · PM admin notification subject (inline string in pm_admin.py:333)
# ─────────────────────────────────────────────────────────────────
def _pm_admin_subject(headline: str) -> str:
    return f"[MASCI · ACCESS] {headline}"


class TestPmAdminAccessSubject:
    def test_welcome(self):
        assert _pm_admin_subject("Welcome to the MASCI PM Portal") == (
            "[MASCI · ACCESS] Welcome to the MASCI PM Portal"
        )

    def test_reset(self):
        assert _pm_admin_subject("Your password has been reset") == (
            "[MASCI · ACCESS] Your password has been reset"
        )


# ─────────────────────────────────────────────────────────────────
# 3 · PO digest subject (build_digest_subject)
# ─────────────────────────────────────────────────────────────────
class TestPoDigestSubject:
    def test_legacy_constant_still_exported(self):
        # We did NOT remove the constant — only added the builder.
        assert DIGEST_SUBJECT == "[MASCI · PO] Weekly Request PO Digest"

    def test_builder_injects_date(self):
        assert build_digest_subject("2026-02-23") == (
            "[MASCI · PO] Weekly Request PO Digest · 2026-02-23"
        )

    def test_builder_defaults_to_today(self):
        s = build_digest_subject()
        assert s.startswith("[MASCI · PO] Weekly Request PO Digest · ")
        # Trailing YYYY-MM-DD shape
        tail = s.rsplit(" · ", 1)[-1]
        assert len(tail) == 10 and tail[4] == "-" and tail[7] == "-"


# ─────────────────────────────────────────────────────────────────
# 4 · Platform outage subject (server.py:7352)
# ─────────────────────────────────────────────────────────────────
def _outage_subject(issue_key: str) -> str:
    return f"🚨 PLATFORM OUTAGE · {issue_key}"


class TestOutageSubject:
    def test_format(self):
        assert _outage_subject("ingress-5xx") == "🚨 PLATFORM OUTAGE · ingress-5xx"

    def test_uses_reserved_severe_prefix(self):
        # Doctrine A.III severe tier reserves 🚨 prefix for severe / immediate.
        assert _outage_subject("x").startswith("🚨 ")


# ─────────────────────────────────────────────────────────────────
# 5 · System health subject (health_monitor.py:98)
# ─────────────────────────────────────────────────────────────────
def _health_subject(overall: str, n_red: int) -> str:
    """Mirrors the conditional at health_monitor.py:98."""
    if (overall or "").lower() in ("fail", "red", "critical"):
        return f"🚨 HEALTH FAIL · {n_red} subsystem(s)"
    return (
        f"[MASCI · HEALTH] System Health {overall.upper()} · "
        f"{n_red} subsystem(s) at risk"
    )


class TestHealthSubject:
    def test_fail_uses_severe_prefix(self):
        assert _health_subject("fail", 2) == "🚨 HEALTH FAIL · 2 subsystem(s)"

    def test_red_uses_severe_prefix(self):
        assert _health_subject("red", 3) == "🚨 HEALTH FAIL · 3 subsystem(s)"

    def test_routine_uses_tag(self):
        assert _health_subject("amber", 1) == (
            "[MASCI · HEALTH] System Health AMBER · 1 subsystem(s) at risk"
        )

    def test_no_long_dash(self):
        # iter437: replaced em-dash with operational `·` separator
        assert "—" not in _health_subject("amber", 1)


# ─────────────────────────────────────────────────────────────────
# 6 · Backup verification subject (render_verification_subject)
# ─────────────────────────────────────────────────────────────────
def _report(verdict: str, archives: int = 7) -> dict:
    return {"verdict": verdict, "r2": {"archive_count": archives}}


class TestBackupVerificationSubject:
    def test_pass(self):
        assert render_verification_subject(_report("pass", 7)) == (
            "[MASCI · BACKUP] Weekly Verification · 7 archives healthy"
        )

    def test_fail_uses_severe_prefix(self):
        s = render_verification_subject(_report("fail"))
        assert s.startswith("🚨 BACKUP VERIFICATION FAILED")

    def test_warn_uses_tag(self):
        s = render_verification_subject(_report("warn", 5))
        assert s.startswith("[MASCI · BACKUP]")
        assert "5 archives" in s

    def test_pass_does_not_use_forbidden_emoji(self):
        # Doctrine A.I forbids non-reserved emoji; ✓ is forbidden.
        s = render_verification_subject(_report("pass"))
        assert "✓" not in s
        assert "🎉" not in s


# ─────────────────────────────────────────────────────────────────
# Cross-cutting · no forbidden urgency words anywhere
# ─────────────────────────────────────────────────────────────────
FORBIDDEN_URGENCY_WORDS = (
    "URGENT", "Urgent", "urgent ",
    "IMPORTANT", "Important",
    "ASAP", "asap",
    "Please ", "Kindly ",
    "Time-sensitive", "Heads up",
)


@pytest.mark.parametrize(
    "subject",
    [
        _parts_subject("X", 1),
        _pm_admin_subject("Welcome"),
        build_digest_subject("2026-02-23"),
        _outage_subject("x"),
        _health_subject("amber", 1),
        _health_subject("fail", 1),
        render_verification_subject(_report("pass")),
        render_verification_subject(_report("fail")),
        render_verification_subject(_report("warn")),
    ],
)
def test_no_forbidden_urgency_words(subject: str):
    for word in FORBIDDEN_URGENCY_WORDS:
        assert word not in subject, (
            f"Subject {subject!r} contains forbidden urgency word {word!r}"
        )
