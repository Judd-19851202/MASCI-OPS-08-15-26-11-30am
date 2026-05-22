"""
iter331 · Live Production Hot-Fix · PDF Endpoints Non-Blocking

Anti-drift regression: the synchronous PDF render calls inside async
FastAPI handlers in `hr_portal.py` and `field_leadership.py` blocked the
event loop for 15-20s on production hardware. While blocked, every other
/api/* request on the same worker timed out at Cloudflare's origin
threshold, returning HTTP 520. The fix wraps each render in
`asyncio.to_thread(...)` to offload to the default executor pool —
matching the pattern already used by `safety_forms.py` and the
email-report path in `server.py`.

This regression locks the fix in place so a future refactor can't
re-introduce the blocking call.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_hr_portal_fl_pdf_uses_to_thread():
    src = (ROOT / "backend" / "routes" / "hr_portal.py").read_text(encoding="utf-8")
    # The FL PDF render must run in a thread.
    assert "asyncio.to_thread(render_field_leadership_pdf" in src, (
        "hr_portal.py FL PDF endpoint must offload render via asyncio.to_thread"
    )
    # The blocking sync call must be absent.
    assert "pdf = render_field_leadership_pdf(d)" not in src, (
        "hr_portal.py still calls render_field_leadership_pdf synchronously"
    )


def test_field_leadership_pdf_uses_to_thread():
    src = (ROOT / "backend" / "routes" / "field_leadership.py").read_text(encoding="utf-8")
    assert "asyncio.to_thread(render_pdf_bytes" in src, (
        "field_leadership.py PDF endpoint must offload render via asyncio.to_thread"
    )
    assert "pdf_bytes = render_pdf_bytes(rec)" not in src, (
        "field_leadership.py still calls render_pdf_bytes synchronously"
    )


def test_safety_forms_pdf_endpoints_remain_non_blocking():
    """Safety forms PDF endpoints were already correct — make sure the
    iter331 sweep didn't accidentally regress them."""
    src = (ROOT / "backend" / "routes" / "safety_forms.py").read_text(encoding="utf-8")
    # All three rendered shapes still use to_thread.
    assert "asyncio.to_thread(render_issuance_pdf" in src
    assert "asyncio.to_thread(render_return_pdf" in src
    assert "asyncio.to_thread(render_training_pdf" in src


def test_hr_portal_imports_asyncio():
    src = (ROOT / "backend" / "routes" / "hr_portal.py").read_text(encoding="utf-8")
    assert "import asyncio" in src, "hr_portal.py must import asyncio for to_thread"


def test_field_leadership_imports_asyncio():
    src = (ROOT / "backend" / "routes" / "field_leadership.py").read_text(encoding="utf-8")
    assert "import asyncio" in src, "field_leadership.py must import asyncio for to_thread"
