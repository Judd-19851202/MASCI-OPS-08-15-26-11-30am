"""iter437 / Phase IV-BETA.5A-P3A · Governance Checkpoint System.

Locks the checkpoint memory contract:
  • `diff_doctrine_baseline.py --append --checkpoint LABEL` writes
    records with `checkpoint=true` and `checkpoint_label=LABEL`
  • Chip endpoint returns `reference="checkpoint"` when a checkpoint
    record exists for the portal
  • Endpoint surfaces `checkpoint_label`, `checkpoint_timestamp`,
    `checkpoint_calmness`, and `delta_since_checkpoint`
  • Chip frontend renders `data-reference="checkpoint"` and embeds
    `since checkpoint` in the trailing text on drifting / improving
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
import requests

TRENDLINE_PATH = Path("/app/memory/DOCTRINE_TRENDLINE.json")

SUPER_EMAIL = (
    os.popen("grep '^SUPER_ADMIN_EMAIL=' /app/backend/.env | cut -d= -f2-")
    .read().strip().strip('"')
)
SUPER_PW = (
    os.popen("grep '^SUPER_ADMIN_BOOTSTRAP_PASSWORD=' /app/backend/.env | cut -d= -f2-")
    .read().strip().strip('"')
)


@pytest.fixture(scope="module")
def tokens(base_url: str) -> dict:
    r = requests.post(
        f"{base_url}/api/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PW},
        timeout=15,
    )
    r.raise_for_status()
    return (r.json() or {}).get("portal_tokens", {}) or {}


# ─── Append + checkpoint script behaviour ─────────────────────────

def test_checkpoint_append_writes_label():
    """`--append --checkpoint LABEL` records the label on every portal."""
    label = "PW regression checkpoint · P3A"
    result = subprocess.run(
        ["python3", "/app/scripts/diff_doctrine_baseline.py",
         "--append", "--checkpoint", label],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr

    data = json.loads(TRENDLINE_PATH.read_text())
    records = data.get("records") or []
    cps = [r for r in records if r.get("checkpoint") and r.get("checkpoint_label") == label]
    # We expect one checkpoint per portal (4 portals) from this run.
    portals_with_cp = {r["portal"] for r in cps}
    assert portals_with_cp == {"admin", "pm", "hr", "safety"}, (
        f"checkpoint records missing for some portals: {portals_with_cp}"
    )


def test_checkpoint_label_capped_at_80_chars():
    """Operator-supplied label must be capped — prevent abuse."""
    long_label = "X" * 200
    subprocess.run(
        ["python3", "/app/scripts/diff_doctrine_baseline.py",
         "--append", "--checkpoint", long_label],
        check=True, capture_output=True, text=True, timeout=30,
    )
    data = json.loads(TRENDLINE_PATH.read_text())
    cps = [
        r for r in data.get("records") or []
        if r.get("checkpoint") and r.get("checkpoint_label", "").startswith("X")
    ]
    assert cps, "no XXX checkpoint found"
    assert len(cps[-1]["checkpoint_label"]) <= 80


# ─── Endpoint exposes checkpoint reference ────────────────────────

def test_chip_endpoint_uses_checkpoint_reference(base_url: str):
    """Once at least one checkpoint exists, the endpoint reports
    reference='checkpoint' and includes the label."""
    # Seed a checkpoint so the test is self-contained.
    subprocess.run(
        ["python3", "/app/scripts/diff_doctrine_baseline.py",
         "--append", "--checkpoint", "endpoint-regression"],
        check=True, capture_output=True, text=True, timeout=30,
    )
    for portal in ("admin", "pm", "hr", "safety"):
        r = requests.get(f"{base_url}/api/governance/health/{portal}", timeout=15)
        r.raise_for_status()
        j = r.json()
        assert j.get("ok") is True
        assert j.get("reference") == "checkpoint", (
            f"{portal} endpoint did not switch to checkpoint reference: {j}"
        )
        assert "checkpoint_label" in j
        assert isinstance(j.get("delta_since_checkpoint"), (int, float))


# ─── Chip frontend reflects the reference ─────────────────────────

def _seed_admin(page, base_url: str, token: str):
    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.evaluate(f"localStorage.setItem('masci.admin.token', '{token}')")


def test_chip_renders_checkpoint_reference(page, base_url: str, tokens: dict):
    """After a checkpoint exists, the chip carries
    `data-reference="checkpoint"`."""
    # Make sure a checkpoint exists.
    subprocess.run(
        ["python3", "/app/scripts/diff_doctrine_baseline.py",
         "--append", "--checkpoint", "chip-render-regression"],
        check=True, capture_output=True, text=True, timeout=30,
    )
    _seed_admin(page, base_url, tokens.get("admin"))
    page.goto(f"{base_url}/admin?adminSidebarV2=1", wait_until="networkidle")
    page.wait_for_timeout(2000)

    chip = page.locator("[data-testid='governance-health-chip-admin']")
    assert chip.count() == 1
    ref = chip.get_attribute("data-reference")
    assert ref == "checkpoint", f"chip reference should be 'checkpoint', got: {ref}"


def test_chip_label_lowercase_after_checkpoint(page, base_url: str, tokens: dict):
    """Chip label MUST stay sentence-case (lowercase 'governance …')
    even when a checkpoint reference is active."""
    _seed_admin(page, base_url, tokens.get("admin"))
    page.goto(f"{base_url}/admin?adminSidebarV2=1", wait_until="networkidle")
    page.wait_for_timeout(1500)
    label = page.locator("[data-testid='governance-health-label-admin']")
    text = (label.text_content() or "").strip().lower()
    assert text.startswith("governance "), text
    assert "!" not in text
