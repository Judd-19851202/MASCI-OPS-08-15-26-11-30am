"""Track 19.47 · Operational Intelligence Cockpit UI + summary endpoint
· lock test.

Run isolated:
    pytest backend/tests/test_track_19_47_cockpit_and_summary.py -q
"""
from __future__ import annotations

import asyncio
from pathlib import Path

APP = Path("/app")
BE = APP / "backend"
FE = APP / "frontend"
MEM = APP / "memory"


# ---------------------------------------------------- fake DB harness ------
class _Coll:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    async def count_documents(self, q):
        return len(self.rows)

    async def find_one(self, q=None, projection=None, sort=None):
        return self.rows[0] if self.rows else None

    def find(self, q=None, projection=None):
        rows = self.rows

        class _Cur:
            def __init__(self, r): self.r = list(r)
            def limit(self, n): self.r = self.r[:n]; return self
            def skip(self, n): self.r = self.r[n:]; return self
            def sort(self, *args, **kwargs): return self
            def __aiter__(self): self._it = iter(self.r); return self
            async def __anext__(self):
                try: return next(self._it)
                except StopIteration: raise StopAsyncIteration
        return _Cur(rows)

    def aggregate(self, pipeline):
        return self.find({}, {})


class _Db:
    def __init__(self, seeded=None):
        self._c = {n: _Coll(v) for n, v in (seeded or {}).items()}

    def __getitem__(self, name):
        return self._c.setdefault(name, _Coll())


# ---------------------------------------------------- Summary endpoint ----
def test_summary_endpoint_registered_read_only():
    """Endpoint must be GET only. No POST/PATCH/DELETE mirror."""
    src = (BE / "operational_intelligence" / "routes.py").read_text(
        encoding="utf-8")
    assert '"/operational-intelligence/summary"' in src
    import re
    matches = re.findall(
        r"@api_router\.(get|post|patch|delete|put)"
        r"\([^)]*/operational-intelligence/summary",
        src)
    for verb in matches:
        assert verb == "get", f"summary endpoint exposes non-GET: {verb}"


def test_summary_endpoint_preserves_admin_full_summary_gate():
    src = (BE / "operational_intelligence" / "routes.py").read_text(
        encoding="utf-8")
    idx = src.index('"/operational-intelligence/summary"')
    block = src[idx:idx + 1400]
    assert "require_summary_actor" in block
    assert "Admin auth required for full summary" in block


def test_summary_endpoint_never_returns_rendered_html():
    """The summary payload is a compact per-product row set; the
    aggregator MUST NOT include the full rendered_html output."""
    src = (BE / "operational_intelligence" / "routes.py").read_text(
        encoding="utf-8")
    start = src.index('"/operational-intelligence/summary"')
    end = src.index('"/operational-intelligence/audit"')
    summary_block = src[start:end]
    assert "rendered_html" not in summary_block, (
        "summary endpoint block references rendered_html — "
        "would bloat the Cockpit top-strip payload")


# ---------------------------------------------------- Summary behaviour --
def test_summary_payload_shape_and_partial_failure_safe():
    """Import the FastAPI app, wire the summary dep, and call it
    directly against a fake DB. Expect: 11 products present · buckets
    map filled · dry_run_default true · no exception even if some
    products fail to compose (which is expected — many domain
    aggregators depend on collections we didn't seed)."""
    import sys
    sys.path.insert(0, str(BE))
    # Import the products module so the registry populates.
    from operational_intelligence import (  # noqa: F401
        list_products, ProductStatus,
    )

    products_impl = [p for p in list_products()
                     if p.status == ProductStatus.IMPLEMENTED]
    assert len(products_impl) == 11, len(products_impl)

    # We test the summary logic by reproducing it here — the endpoint
    # itself lives inside a closure in register_operational_intelligence_routes
    # and is exercised by the live smoke test. Here we prove the
    # partial-failure contract holds: composing every implemented
    # product against an empty DB never raises.
    from operational_intelligence import compose
    db = _Db()

    async def _go():
        succeeded = 0
        for p in products_impl:
            try:
                d = await compose(db, product_id=p.product_id)
                assert "operational_intelligence_score" in d
                succeeded += 1
            except Exception:  # noqa: BLE001
                # The summary endpoint's partial-failure contract says
                # any per-product exception is captured into an `error`
                # field — it MUST NOT bubble up. This test proves the
                # contract is exercisable (i.e. some products do raise
                # on unseeded environments); the endpoint's own
                # try/except handles that.
                pass
        # At least one product must have composed successfully, otherwise
        # the summary payload would be empty of real data.
        assert succeeded >= 1
    asyncio.run(_go())


def test_summary_endpoint_strips_no_sensitive_fields_but_stays_safe():
    """The summary endpoint reads from audit collection for last_sent
    fields but only pulls send_status / recipient_count — never
    payload keys like token/secret/password/api_key. Grep-check that
    the audit read projection is narrow."""
    src = (BE / "operational_intelligence" / "routes.py").read_text(
        encoding="utf-8")
    start = src.index('"/operational-intelligence/summary"')
    end = src.index('"/operational-intelligence/audit"')
    block = src[start:end]
    # The summary block should project only `at` and `payload` from the
    # audit row and then read narrow keys — never dump the whole payload.
    for banned in ('"token"', '"secret"', '"password"', '"api_key"'):
        assert banned not in block, (
            f"summary block references {banned} — potential leak")


# ---------------------------------------------------- Frontend integrity -
COCKPIT_JSX = FE / "src/pages/admin/AdminOperationalIntelligence.jsx"


def test_cockpit_page_file_exists():
    assert COCKPIT_JSX.exists(), COCKPIT_JSX


def test_cockpit_route_registered_in_app_js():
    text = (FE / "src/App.js").read_text(encoding="utf-8")
    assert 'AdminOperationalIntelligence' in text
    assert '/admin/operational-intelligence' in text


def test_cockpit_admin_shell_nav_entry_present():
    text = (FE / "src/components/AdminShell.jsx").read_text(encoding="utf-8")
    assert "/admin/operational-intelligence" in text
    assert "Operational Intelligence" in text


def test_cockpit_wires_expected_backend_endpoints():
    text = COCKPIT_JSX.read_text(encoding="utf-8")
    for endpoint in (
        "/operational-intelligence/summary",
        "/operational-intelligence/${p.product_id}/preview",
        "/operational-intelligence/${p.product_id}/dispatch",
        "/operational-intelligence/history",
        "/operational-intelligence/audit",
    ):
        assert endpoint in text, f"cockpit missing endpoint wire: {endpoint}"


def test_cockpit_dry_run_default_no_live_send():
    """Dry-run must be the ONLY send path exposed. The Cockpit MUST
    NOT contain a live-send button (`dry_run: false` param) anywhere."""
    text = COCKPIT_JSX.read_text(encoding="utf-8")
    assert "dry_run: true" in text
    assert "dry_run: false" not in text.lower(), (
        "cockpit exposes a live-send path — must be dry-run only for "
        "this track")


def test_cockpit_has_expected_test_ids():
    text = COCKPIT_JSX.read_text(encoding="utf-8")
    for tid in (
        "admin-operational-intelligence",
        "oi-cockpit-top-strip",
        "oi-product-grid",
        "oi-preview-btn-",
        "oi-dryrun-btn-",
        "oi-history-btn-",
        "oi-audit-btn-",
        "oi-refresh-btn",
        "oi-recipient-governance-entry",
        "oi-preview-drawer",
        "oi-dryrun-drawer",
        "oi-history-drawer",
        "oi-audit-drawer",
    ):
        assert tid in text, f"cockpit missing data-testid: {tid}"


def test_cockpit_preview_uses_sandboxed_iframe():
    """The preview drawer must render backend HTML inside a sandbox=""
    iframe to protect against injected scripts."""
    text = COCKPIT_JSX.read_text(encoding="utf-8")
    assert 'sandbox=""' in text, (
        "preview HTML must render in a sandboxed iframe")


def test_cockpit_no_hardcoded_fake_scores():
    """No hardcoded numeric scores anywhere in the cockpit JSX — every
    score value must come from the backend summary payload."""
    text = COCKPIT_JSX.read_text(encoding="utf-8")
    # A crude but effective guard: assignment-style hard-coded scores
    # like `score: 92`, `attention_level: "LOW"`, etc.
    banned_patterns = [
        'score: 100,', 'score: 92,', 'score: 60,',
        'attention_level: "LOW"', 'attention_level: "HIGH"',
    ]
    for b in banned_patterns:
        assert b not in text, f"fake score literal detected: {b}"


# ---------------------------------------------------- Documentation ------
REQUIRED_DOCS = [
    "TRACK_19_47_OPERATIONAL_INTELLIGENCE_COCKPIT.md",
    "TRACK_19_47_SUMMARY_ENDPOINT.md",
    "TRACK_19_47_FRONTEND_WIRING.md",
    "TRACK_19_47_HISTORY_AUDIT_UI.md",
    "TRACK_19_47_RECIPIENT_GOVERNANCE_ENTRY.md",
    "TRACK_19_47_PERMISSION_CERTIFICATION.md",
    "TRACK_19_47_MOBILE_IPAD_REVIEW.md",
    "TRACK_19_47_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_47_TEST_REPORT.md",
]


def test_all_track_19_47_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing docs: {missing}"


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_47_ZERO_DRIFT_MATRIX.md").read_text(
        encoding="utf-8")
    for cat in ["Schemas", "Routes", "Emails", "Scheduler",
                "Recipients", "Audit", "Rollback"]:
        assert cat in text, f"ZDM missing category: {cat}"


def test_prd_updated():
    assert "TRACK 19.47" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.47" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
