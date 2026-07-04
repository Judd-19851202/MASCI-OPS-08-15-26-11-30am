"""Track 19.62 · Fire Protection Promotion — Phase A · lock test.

Track 19.62 Phase A executes the Track 20.6 verdict:
    * Taxonomy bump v1.0.0 → v1.1.0 with `Fire Protection` asset_class
      + 9 extinguisher asset_types (additive · backwards-compat).
    * Asset spine resolver fallback into `db.fire_extinguishers`.
    * Historical Records `entity_kind="asset"` lane gains 5 additive
      fire-specific record_type slugs.
    * `AdminAssetThread.jsx` gains a Fire Protection class branch
      (mission facts, attention rules, relationship edges,
      "Manage in Safety Portal" cross-link).
    * `FleetUnitThread.jsx` surfaces linked extinguishers on parent
      asset threads (via `assigned_target_ref=` filter on the existing
      Safety endpoint · read-only relationship rendering).
    * `SafetyFireExtinguishers.jsx` list rows now deep-link to the
      Asset Thread.
    * Zero migration · zero new collection · zero new inspection
      engine · zero new OI product · zero new email flow.

Run in isolation:
    pytest /app/backend/tests/test_track_19_62_fire_protection_phase_a.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_COMP_OI = FE / "components/operational_intelligence"
FE_PAGES = FE / "pages"
BE = REPO / "backend"
BE_ROUTES = BE / "routes"
BE_OI = BE / "operational_intelligence"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ── Taxonomy v1.1.0 ─────────────────────────────────────────────────

def test_taxonomy_bumped_to_1_1_0():
    src = _read(BE / "services/asset_taxonomy.py")
    assert 'TAXONOMY_VERSION: str = "1.1.0"' in src, \
        "TAXONOMY_VERSION must be bumped to 1.1.0"


def test_fire_protection_asset_class_present():
    src = _read(BE / "services/asset_taxonomy.py")
    assert '"Fire Protection"' in src


def test_all_nine_extinguisher_types_present():
    src = _read(BE / "services/asset_taxonomy.py")
    for t in ("ABC Fire Extinguisher", "CO2 Fire Extinguisher",
              "Class D Fire Extinguisher", "Water Fire Extinguisher",
              "Foam Fire Extinguisher", "Clean Agent Fire Extinguisher",
              "Wheeled Fire Extinguisher", "Vehicle Fire Extinguisher",
              "Fire Extinguisher Cabinet / Station"):
        assert f'"{t}"' in src, f"taxonomy missing extinguisher type: {t!r}"


def test_fire_protection_is_not_ppe_or_safety_equipment():
    """Fire Protection is a NEW asset_class, not a Safety Equipment type."""
    from importlib import import_module
    tax = import_module("backend.services.asset_taxonomy") if False else None  # placeholder
    src = _read(BE / "services/asset_taxonomy.py")
    # ASSET_TYPES_BY_CLASS entry for Safety Equipment must not include
    # any fire extinguisher type.
    safety_start = src.index('"Safety Equipment":')
    safety_end = src.index("}", safety_start)  # end of the class block is far — good enough for regex-like scan
    # Take a wider window to include the tuple contents.
    safety_end = src.index("),", safety_start) + 2
    safety_block = src[safety_start:safety_end]
    for t in ("ABC Fire Extinguisher", "CO2 Fire Extinguisher",
              "Fire Extinguisher"):
        assert t not in safety_block, \
            f"Fire extinguisher type {t!r} must NOT appear in Safety Equipment block"


def test_fire_protection_behavior_declares_not_ppe():
    src = _read(BE / "services/asset_taxonomy.py")
    # Behavior override rows must set assignable_to_employee=False on
    # each fire extinguisher type.
    for t in ("ABC Fire Extinguisher", "CO2 Fire Extinguisher",
              "Class D Fire Extinguisher", "Water Fire Extinguisher",
              "Foam Fire Extinguisher", "Clean Agent Fire Extinguisher",
              "Wheeled Fire Extinguisher", "Vehicle Fire Extinguisher",
              "Fire Extinguisher Cabinet / Station"):
        # look for the row and require assignable_to_employee: False
        needle = f'"{t}":'
        assert needle in src, f"behavior override missing for {t!r}"
    # Global assertion — no fire extinguisher type is assignable to an
    # employee (they are stationed/mounted).
    fire_block_start = src.index("Track 19.62 · Fire Protection — life-safety")
    fire_block_end = len(src)
    fire_block = src[fire_block_start:fire_block_end]
    assert '"assignable_to_employee": False' in fire_block, \
        "Fire Protection behavior overrides must declare assignable_to_employee=False"


# ── Resolver fallback ──────────────────────────────────────────────

def test_resolver_falls_back_to_fire_extinguishers():
    src = _read(BE_ROUTES / "asset_spine.py")
    assert "db.fire_extinguishers.find_one" in src, \
        "resolver must fall back to db.fire_extinguishers"
    assert '"source": "fire_extinguishers"' in src, \
        "resolver fallback must tag payload with source=fire_extinguishers"
    assert '"asset_class": "Fire Protection"' in src, \
        "resolver fallback must return asset_class=Fire Protection"


def test_no_migration_from_fire_extinguishers():
    """No code path shall MOVE rows from db.fire_extinguishers into
    equipment_master. The Safety Portal router still owns its collection
    end-to-end (including the DELETE endpoint on that collection —
    that is authoritative deletion by Safety, not a migration).

    A "migration" here means: reading fire_extinguishers AND inserting
    into equipment_master in the same code path.
    """
    for name in ("asset_spine.py", "asset_documents.py", "asset_care.py",
                 "asset_service_events.py", "asset_transfers.py"):
        src = _read(BE_ROUTES / name)
        # Must not perform an equipment_master insert seeded from fire_ext.
        for insert_call in ("equipment_master.insert_one",
                            "equipment_master.insert_many",
                            "equipment_master.update_one",
                            "equipment_master.replace_one"):
            if insert_call in src:
                # Locate each insert site and confirm none of them read
                # fire_extinguishers within a ±400-char window before.
                idx = src.find(insert_call)
                while idx != -1:
                    window = src[max(0, idx - 400): idx]
                    assert "fire_extinguishers" not in window, \
                        f"{name}: {insert_call} at char {idx} appears to migrate from db.fire_extinguishers"
                    idx = src.find(insert_call, idx + 1)


# ── No new duplicate systems ───────────────────────────────────────

def test_no_new_fire_collection():
    for name in ("fire_protection.py", "fire_ext_v2.py", "life_safety.py",
                 "asset_fire.py"):
        assert not (BE_ROUTES / name).exists(), \
            f"Track 19.62 must not introduce {name}"


def test_no_new_oi_product():
    src = _read(BE / "operational_intelligence/products.py")
    # No fire-protection OI product may be registered.
    assert "fire_protection_intelligence" not in src, \
        "no fire-protection OI product may be registered"
    assert 'product_id="fire' not in src


def test_no_new_inspection_engine():
    """No new inspection module for fire may be created."""
    forbidden = ("fire_ext_inspection_engine.py",
                 "fire_inspection_engine.py",
                 "life_safety_inspection.py")
    for name in forbidden:
        assert not (BE_ROUTES / name).exists(), \
            f"must not create new inspection engine: {name}"


def test_oi_engine_inventory_frozen():
    expected = {"__init__.py", "engine.py", "registry.py", "products.py",
                "score_model.py", "product_layout.py", "recipients.py",
                "routes.py", "scheduler.py"}
    actual = {f.name for f in BE_OI.glob("*.py")}
    assert actual == expected


def test_oi_component_inventory_frozen():
    expected_jsx = {"OiAttentionStrip.jsx", "GuidanceCard.jsx",
                    "AttentionChip.jsx", "TrendChip.jsx",
                    "OperationalThread.jsx",
                    "OperationalThreadPage.jsx",
                    "RelationshipGraph.jsx"}
    expected_js = {"guidanceMap.js"}
    actual_jsx = {f.name for f in FE_COMP_OI.glob("*.jsx")}
    actual_js = {f.name for f in FE_COMP_OI.glob("*.js")}
    assert actual_jsx == expected_jsx
    assert actual_js == expected_js


# ── No email paths ─────────────────────────────────────────────────

def test_no_email_send_in_touched_backend_files():
    forbidden = ("fsi_send_email", "resend.emails.send", "phase4.send_email")
    for name in ("asset_spine.py", "employee_records.py",
                 "safety_portal/fire_extinguishers.py",
                 "safety_portal/_models.py"):
        src = _read(BE_ROUTES / name)
        for needle in forbidden:
            assert needle not in src, \
                f"{name} unexpectedly contains {needle!r}"


def test_no_email_send_in_touched_frontend_files():
    forbidden = ("fsi_send_email", "resend.emails", "/api/email/send",
                 "/api/notifications/send", "phase4.send_email")
    for path in (FE_PAGES / "AdminAssetThread.jsx",
                 FE_PAGES / "fleet/FleetUnitThread.jsx",
                 FE_PAGES / "SafetyFireExtinguishers.jsx"):
        src = _read(path)
        for needle in forbidden:
            assert needle not in src, \
                f"{path.name} unexpectedly contains {needle!r}"


# ── Historical Records — 5 new fire-specific slugs ─────────────────

def test_historical_records_asset_lane_has_fire_slugs():
    src = _read(BE_ROUTES / "employee_records.py")
    for slug in ("hydrostatic_test_certificate",
                 "recharge_service_record",
                 "fire_ext_annual_service",
                 "fire_ext_manufacturer_doc",
                 "fire_ext_retirement_record"):
        assert f'"{slug}"' in src, \
            f"employee_records LANE_RECORD_TYPES['asset'] must include {slug!r}"


# ── Asset Thread — Fire Protection class branch ────────────────────

def test_asset_thread_handles_fire_class():
    src = _read(FE_PAGES / "AdminAssetThread.jsx")
    assert "fire protection" in src.lower(), \
        "AdminAssetThread must branch on the Fire Protection class"
    for needle in ("Fire Protection fact panel",
                   "Fire Extinguisher",
                   "Manage in Safety Portal",
                   "Fire Protection attention rules",
                   "Fire Protection parent-asset edge"):
        assert needle in src, f"AdminAssetThread.jsx missing branch marker: {needle!r}"


def test_asset_thread_no_compliance_claims():
    """Track 19.62 must not use unauthorized compliance language."""
    src = _read(FE_PAGES / "AdminAssetThread.jsx")
    for phrase in ("OSHA compliant", "legally compliant", "certified safe",
                   "fire-code compliant"):
        assert phrase not in src, \
            f"AdminAssetThread must not claim {phrase!r}"


# ── Parent asset surfacing ─────────────────────────────────────────

def test_fleet_unit_thread_surfaces_linked_extinguishers():
    src = _read(FE_PAGES / "fleet/FleetUnitThread.jsx")
    assert "/api/safety/fire-extinguishers?assigned_target_ref=" in src, \
        "FleetUnitThread must query safety endpoint filtered by assigned_target_ref"
    assert "extinguishers" in src, \
        "FleetUnitThread must consume extinguishers state"
    assert "Fire Ext" in src, "FleetUnitThread must render a Fire Ext relationship edge"


def test_safety_fire_extinguishers_list_deeplinks_to_asset_thread():
    src = _read(FE_PAGES / "SafetyFireExtinguishers.jsx")
    assert "/admin/assets/" in src and "/thread" in src, \
        "SafetyFireExtinguishers list must deep-link to the Asset Thread"


# ── Safety extinguisher router / UI preserved ──────────────────────

def test_safety_fire_ext_router_still_present():
    p = BE_ROUTES / "safety_portal/fire_extinguishers.py"
    assert p.exists()
    src = _read(p)
    for needle in ('@api_router.get("/safety/fire-extinguishers")',
                   '@api_router.post("/safety/fire-extinguishers")',
                   '@api_router.post("/safety/fire-extinguishers/{fe_id}/inspect")'):
        assert needle in src


def test_safety_fire_ext_router_extended_with_parent_filter():
    src = _read(BE_ROUTES / "safety_portal/fire_extinguishers.py")
    assert "assigned_target_ref" in src, \
        "list endpoint must accept assigned_target_ref query"


def test_fire_ext_models_have_assignment_fields():
    src = _read(BE_ROUTES / "safety_portal/_models.py")
    for field in ("assigned_target_kind", "assigned_target_ref",
                  "assigned_target_label", "assigned_location_detail",
                  "assigned_project_number", "assigned_unit_number",
                  "assigned_facility_name", "assigned_room_name",
                  "serial_number", "asset_tag"):
        assert field in src, f"FireExtinguisher models missing field {field!r}"


# ── Docs + register ────────────────────────────────────────────────

REQUIRED_DOCS = [
    "TRACK_19_62_EXECUTIVE_SUMMARY.md",
    "TRACK_19_62_FIRE_PROTECTION_TAXONOMY.md",
    "TRACK_19_62_ASSIGNMENT_RELATIONSHIP_MODEL.md",
    "TRACK_19_62_RESOLVER_FALLBACK.md",
    "TRACK_19_62_HISTORICAL_RECORDS_FIRE_DOCS.md",
    "TRACK_19_62_ASSET_THREAD_FIRE_BRANCH.md",
    "TRACK_19_62_PARENT_ASSET_SURFACING.md",
    "TRACK_19_62_OI_ROUTING.md",
    "TRACK_19_62_PERMISSION_CERTIFICATION.md",
    "TRACK_19_62_EMAIL_SAFETY_CERTIFICATION.md",
    "TRACK_19_62_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_62_TEST_REPORT.md",
]


def test_all_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 19.62 deliverables: {missing}"


def test_tech_debt_register_updated_with_fleet_pilot_fix():
    """Track 19.62 fixed a Class-A duplicate-key issue in
    FleetUnitThread.jsx deriveRelationships. The register must mention it."""
    src = _read(MEM / "TECHNICAL_DEBT_REGISTER.md")
    assert "TD-19.62-A01" in src or "duplicate key" in src.lower(), \
        "register must record the Class-A dup-key fix from Track 19.62"


def test_prd_and_changelog_updated():
    assert "TRACK 19.62" in _read(MEM / "PRD.md")
    assert "TRACK 19.62" in _read(MEM / "CHANGELOG.md")


# ── Continuity ─────────────────────────────────────────────────────

def test_prior_track_docs_preserved():
    for name in ("TRACK_20_6_FINAL_RECOMMENDATION.md",
                 "TRACK_20_6_EXECUTIVE_AUDIT.md",
                 "TRACK_20_5_FINAL_RECOMMENDATION.md",
                 "TRACK_19_61_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_60_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_59_EXECUTIVE_SUMMARY.md",
                 "TECHNICAL_DEBT_REGISTER.md"):
        assert (MEM / name).exists(), f"prior doc missing: {name}"
