"""TRACK 15.13A · Asset Care Routing Recovery — safety tests.

Static-source assertions on the shop-side asset-admin mirror logic.
No DB writes. No network. Pure regex / AST-style assertions over the
canonical server.py + ShopLogin.jsx + welcome-email branch.
"""
from pathlib import Path

SERVER_PY = Path(__file__).resolve().parents[1] / "server.py"
SHOP_LOGIN = (
    Path(__file__).resolve().parents[2] / "frontend" / "src" / "pages" / "ShopLogin.jsx"
)
SHOP_HUB = (
    Path(__file__).resolve().parents[2] / "frontend" / "src" / "pages" / "ShopHubV2.jsx"
)


class TestAssetAdminRoleLabels:
    """The set of role labels that should set `is_asset_admin=true` on
    the directory mirror must be explicit and small."""

    def test_role_label_set_present(self):
        src = SERVER_PY.read_text()
        assert "_ASSET_ADMIN_ROLE_LABELS" in src
        for label in (
            "Asset Administrator",
            "Asset Manager",
            "Equipment Manager",
            "Fleet Coordinator",
        ):
            assert f'"{label}"' in src, label

    def test_role_implies_helper_signature(self):
        src = SERVER_PY.read_text()
        assert "def _role_implies_asset_admin" in src
        assert "_ASSET_ADMIN_ROLE_LABELS" in src


class TestDirectoryMirrorContract:
    """`_mirror_asset_admin_flag` must:
    * never delete a directory row,
    * never grant a portal,
    * never set a password,
    * only flip the `is_asset_admin` boolean (and stub a row when needed)."""

    def test_mirror_helper_present(self):
        src = SERVER_PY.read_text()
        assert "async def _mirror_asset_admin_flag" in src

    def test_mirror_helper_never_deletes(self):
        src = SERVER_PY.read_text()
        # Locate the helper body roughly between its `async def` line and
        # the next `async def` declaration.
        start = src.index("async def _mirror_asset_admin_flag")
        body = src[start:src.index("\nasync def ", start + 30)]
        for forbidden in ("delete_one", "delete_many", "drop(", "drop_collection"):
            assert forbidden not in body, forbidden

    def test_mirror_helper_never_sets_password_or_portal(self):
        src = SERVER_PY.read_text()
        start = src.index("async def _mirror_asset_admin_flag")
        body = src[start:src.index("\nasync def ", start + 30)]
        # We DO set `password_hash: None` on the stub row, which is the
        # explicit "no password" sentinel. We must NOT introduce any
        # hashed password into the stub.
        assert "hash_password(" not in body
        assert "bcrypt" not in body.lower()
        # `portals: []` on the stub is intentional — no portal grants.
        assert '"portals": []' in body

    def test_mirror_helper_idempotent_on_existing_rows(self):
        src = SERVER_PY.read_text()
        start = src.index("async def _mirror_asset_admin_flag")
        body = src[start:src.index("\nasync def ", start + 30)]
        # When the directory row exists, we $set is_asset_admin to the
        # current desired value (True or False) and do nothing else
        # structural.
        assert "$set" in body
        assert "is_asset_admin" in body


class TestShopLoginMirrorsFlag:
    """`shop_login` must emit `is_asset_admin` in its response payload
    so the SPA can route to /shop/asset-care without an extra round-trip."""

    def test_shop_login_response_includes_is_asset_admin_key(self):
        src = SERVER_PY.read_text()
        # The literal key must appear inside the shop_login function
        # response block (the only "kind": "shop" return in server.py).
        idx = src.index('"kind": "shop"')
        block = src[max(0, idx - 1000): idx + 1000]
        assert '"is_asset_admin"' in block

    def test_shop_login_reads_directory_row_by_email(self):
        src = SERVER_PY.read_text()
        assert "db.user_directory.find_one(" in src
        # And the lookup uses the lowercased email.
        assert '"email": (user.get("email") or "").strip().lower()' in src


class TestWelcomeEmailBranching:
    """`admin_shop_user_email_welcome` must branch by role:
    * asset-admin role → "Welcome to MASCI Asset Care" headline
    * non-asset role  → "Welcome to the MASCI Shop Portal" headline (unchanged)
    """

    def test_asset_care_headline_present(self):
        src = SERVER_PY.read_text()
        assert '"Welcome to MASCI Asset Care"' in src

    def test_branch_predicate_uses_role_helper(self):
        src = SERVER_PY.read_text()
        # The branch must be driven by `_role_implies_asset_admin`, not
        # by an ad-hoc string match — keeps the role catalog in one place.
        idx = src.index("is_asset_admin_role = _role_implies_asset_admin")
        assert idx > 0

    def test_existing_shop_portal_headline_preserved(self):
        """Non-asset shop users must still receive the legacy headline
        verbatim — no regression for Mechanic / Shop Manager onboarding."""
        src = SERVER_PY.read_text()
        assert '"Welcome to the MASCI Shop Portal"' in src

    def test_render_portal_email_branch_selects_asset_care_portal(self):
        src = SERVER_PY.read_text()
        # Verify the render_portal_email call uses the branched portal
        # label so the email chrome (logo / footer) matches Asset Care.
        assert 'portal="Asset Care" if is_asset_admin_role else "Shop"' in src


class TestShopLoginSpaCallsLandingFor:
    """ShopLogin.jsx must honor the mirrored flag and route asset admins
    to /shop/asset-care instead of always /shop."""

    def test_spa_reads_is_asset_admin_from_response(self):
        src = SHOP_LOGIN.read_text()
        assert "is_asset_admin" in src
        assert "/shop/asset-care" in src

    def test_spa_writes_local_storage_flag(self):
        src = SHOP_LOGIN.read_text()
        assert 'localStorage.setItem("masci.is_asset_admin", "true")' in src

    def test_non_asset_user_still_lands_on_shop(self):
        src = SHOP_LOGIN.read_text()
        # The ternary preserves the legacy /shop landing for non-asset
        # shop users (`isAssetAdmin ? "/shop/asset-care" : "/shop"`).
        assert '"/shop/asset-care" : "/shop"' in src


class TestShopHubV2AssetCareTile:
    """Asset Care must be reachable from /shop via a primary-action link
    (so users who navigate to /shop manually can find the workspace)."""

    def test_asset_care_link_present(self):
        src = SHOP_HUB.read_text()
        assert 'to="/shop/asset-care"' in src
        assert 'shop-hub-v2-action-asset-care' in src

    def test_asset_care_link_uses_design_system(self):
        src = SHOP_HUB.read_text()
        # The link must reuse the existing CSS variables / radius — no
        # one-off styling. Spot-check the CSS variable usage.
        idx = src.index('shop-hub-v2-action-asset-care')
        block = src[idx:idx + 600]
        assert "var(--paper-card)" in block
        assert "var(--radius-card)" in block
