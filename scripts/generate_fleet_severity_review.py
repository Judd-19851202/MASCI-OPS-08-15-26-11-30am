#!/usr/bin/env python3
"""iter251 governance helper · regenerates the human-readable severity
review package from `fleet_defect_severity.py` for Safety / Shop / Ops /
Dispatch leadership redline before production reliance.

Run:  python3 /app/scripts/generate_fleet_severity_review.py
Out:  /app/FLEET_SEVERITY_REVIEW_PACKAGE_iter251.md

This is a one-shot author tool, NOT a production endpoint. The
companion read-only API endpoint
(/api/admin/fleet/severity-audit) gives the live validation view.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, "/app/backend")

import fleet_defect_severity as _sev  # noqa: E402
import checklists_fleet as _ck  # noqa: E402


# ─── Cross-reference: every checklist item across every kind ──────
def used_items_by_kind():
    out = {}
    for kind, defn in _ck.FLEET_INSPECTION_KINDS.items():
        truck = defn["truck_items"]() if defn["truck_items"] else []
        trailer = defn["trailer_items"]() if defn["trailer_items"] else []
        out[kind] = {"label": defn["label"], "truck": truck, "trailer": trailer}
    return out


def main() -> None:
    items_by_kind = used_items_by_kind()
    all_used_items: set = set()
    for k_data in items_by_kind.values():
        all_used_items.update(k_data["truck"])
        all_used_items.update(k_data["trailer"])

    sev_keys = set(_sev.FLEET_DEFECT_SEVERITY.keys())
    meta_keys = set(_sev.FLEET_DEFECT_SEVERITY_META.keys())

    missing_severity = sorted(all_used_items - sev_keys)
    orphan_severity = sorted(sev_keys - all_used_items)
    missing_metadata = sorted(sev_keys - meta_keys)
    uncertain_items = sorted([
        item for item, meta in _sev.FLEET_DEFECT_SEVERITY_META.items()
        if meta.get("uncertain")
    ])

    # Items grouped by category for readability
    by_category: dict = {}
    for item, (sev, cat) in _sev.FLEET_DEFECT_SEVERITY.items():
        by_category.setdefault(cat, []).append((item, sev))

    total_oos = sum(1 for s, _c in _sev.FLEET_DEFECT_SEVERITY.values() if s == "oos")
    total_mon = sum(1 for s, _c in _sev.FLEET_DEFECT_SEVERITY.values() if s == "monitor")

    out_lines: list = []
    a = out_lines.append

    # ─── Header ───────────────────────────────────────────────────
    a("# Fleet Defect Severity Review Package · iter251")
    a("")
    a("**Status:** v1-DRAFT-pending-safety-review")
    a("**Generated from:** `/app/backend/fleet_defect_severity.py` + `/app/backend/checklists_fleet.py`")
    a("**Audience:** Safety · Shop · Operations · Dispatch leadership")
    a("**Purpose:** Redline operational disagreements BEFORE production reliance.")
    a("")
    a("This document drives whether a failed DVIR / weekly inspection puts a truck/trailer "
      "**OUT OF SERVICE** (truck cannot operate until shop repair + dispatch re-clearance) or "
      "**MONITOR** (truck still operates · shop sees the defect · driver continues with caution).")
    a("")
    a("Drivers do NOT pick severity in the field — this table picks it for them, eliminating "
      "in-field judgement calls.")
    a("")
    a("---")
    a("")

    # ─── Summary ──────────────────────────────────────────────────
    a("## Summary")
    a("")
    a(f"- **Total classified items:** {len(sev_keys)}")
    a(f"- **OUT OF SERVICE classifications:** {total_oos}")
    a(f"- **MONITOR classifications:** {total_mon}")
    a(f"- **OOS-to-monitor ratio:** {round(total_oos / total_mon, 2) if total_mon else 'n/a'} "
      "(conservative bias toward OOS)")
    a(f"- **Items flagged UNCERTAIN pending Safety review:** {len(uncertain_items)}")
    a(f"- **Items missing severity classification:** {len(missing_severity)} (must be zero before deploy)")
    a(f"- **Orphan severity entries (not used by any checklist):** {len(orphan_severity)}")
    a(f"- **Items missing metadata (rationale / regulation_ref):** {len(missing_metadata)}")
    a("")

    if missing_severity:
        a("### ❌ HARD FAIL · missing severity classifications")
        a("Each of these would HTTP 400 a real DVIR submission in production.")
        a("")
        for item in missing_severity:
            a(f"- `{item}`")
        a("")

    if uncertain_items:
        a("### ⚠️ ITEMS PENDING SAFETY DECISION")
        a("These items are classified but Safety must confirm the classification before "
          "production reliance. Each carries an `uncertainty_note` describing the operational tension.")
        a("")
        for item in uncertain_items:
            meta = _sev.FLEET_DEFECT_SEVERITY_META[item]
            sev, cat = _sev.FLEET_DEFECT_SEVERITY[item]
            a(f"- **`{item}`** · current: **{sev.upper()}** ({cat}) · "
              f"ref: `{meta.get('regulation_ref','—')}`")
            note = meta.get("uncertainty_note") or "(no note)"
            a(f"  - *{note}*")
        a("")

    if missing_metadata:
        a("### ⚠️ MISSING METADATA")
        a("These severity entries have a classification but no rationale or regulation reference. "
          "Operator + Safety should add metadata so the reasoning survives the original author.")
        a("")
        for item in missing_metadata:
            a(f"- `{item}`")
        a("")

    if orphan_severity:
        a("### 🟡 ORPHAN SEVERITY ENTRIES")
        a("Classified but not currently referenced by any checklist. Operationally safe but "
          "indicates table drift · consider removing or wiring into a checklist.")
        a("")
        for item in orphan_severity:
            a(f"- `{item}`")
        a("")

    a("---")
    a("")

    # ─── Per-kind coverage ────────────────────────────────────────
    a("## Per-Kind Coverage")
    a("")
    a("| Inspection Kind | Truck Items | Trailer Items | Total | Classified | Coverage |")
    a("|---|---|---|---|---|---|")
    for kind, data in items_by_kind.items():
        truck_n = len(data["truck"])
        trailer_n = len(data["trailer"])
        total = truck_n + trailer_n
        classified = sum(1 for x in data["truck"] + data["trailer"] if x in sev_keys)
        pct = round(100.0 * classified / total, 1) if total else 0.0
        a(f"| `{kind}` ({data['label']}) | {truck_n} | {trailer_n} | {total} | "
          f"{classified} | {pct}% |")
    a("")
    a("---")
    a("")

    # ─── Full classified items by category ────────────────────────
    a("## Full Classification by Category")
    a("")
    a("**Legend:** 🛑 = OUT OF SERVICE · 👁 = MONITOR · ⚠️ = uncertain (Safety review)")
    a("")

    # Render in a sensible operational order
    ordered_cats = [
        "brakes", "tires", "wheels", "steering", "suspension", "structural",
        "air_system", "coupling", "landing_gear", "lights", "signals",
        "alarms", "horn", "mirrors", "glass", "wipers", "hydraulic",
        "pto", "fluids", "emergency_equipment", "reflectors", "tarp",
        "interior", "body",
    ]
    remaining = [c for c in by_category if c not in ordered_cats]
    for cat in ordered_cats + remaining:
        if cat not in by_category:
            continue
        items = sorted(by_category[cat], key=lambda x: (x[1] != "oos", x[0]))
        oos_in_cat = sum(1 for _i, s in items if s == "oos")
        mon_in_cat = sum(1 for _i, s in items if s == "monitor")
        a(f"### {cat.replace('_', ' ').title()} · {oos_in_cat} OOS · {mon_in_cat} MONITOR")
        a("")
        for item, sev in items:
            meta = _sev.FLEET_DEFECT_SEVERITY_META.get(item, {})
            badge = ("🛑" if sev == "oos" else "👁")
            warn = " ⚠️" if meta.get("uncertain") else ""
            a(f"#### {badge}{warn} `{item}`")
            a(f"- **Severity:** {sev.upper()}")
            ref = meta.get("regulation_ref") or "(no reference)"
            a(f"- **Reference:** {ref}")
            rat = meta.get("rationale") or "(no rationale captured · please add)"
            a(f"- **Rationale:** {rat}")
            if meta.get("uncertain"):
                a(f"- **Uncertainty note:** *{meta.get('uncertainty_note', '(none)')}*")
            a("")
        a("")

    # ─── Sign-off block ───────────────────────────────────────────
    a("---")
    a("")
    a("## Operational Sign-Off")
    a("")
    a("Before production reliance, each of the following must redline + sign:")
    a("")
    a("- [ ] **Safety** · approves overall OOS classifications · confirms uncertainty-flagged items")
    a("- [ ] **Shop** · confirms repair-routing accuracy · confirms ambiguity-threshold definitions (e.g. \"severe damage\", \"major leak\")")
    a("- [ ] **Operations** · confirms operational impact estimates (false-positive OOS productivity hit acceptable)")
    a("- [ ] **Dispatch leadership** · confirms re-clearance authority + workflow")
    a("")
    a("Once signed, update `severity_table_version` in `fleet_defect_severity.py` from `v1-DRAFT-pending-safety-review` to `v1-approved-YYYY-MM-DD` and re-run this generator + the audit endpoint.")
    a("")
    a("---")
    a("")
    a("## Editing Workflow")
    a("")
    a("1. Operator/Safety propose a change (severity flip, rationale edit, item add/remove).")
    a("2. Edit `/app/backend/fleet_defect_severity.py` (table) and the META block in the same file.")
    a("3. Run `python3 /app/scripts/generate_fleet_severity_review.py` to regenerate this document.")
    a("4. Run `python3 -m pytest /app/backend/tests/test_iter251_fleet_ops_foundation.py /app/backend/tests/test_iter251_severity_audit.py` to validate.")
    a("5. Hit `GET /api/admin/fleet/severity-audit` with admin token to confirm verdict.")
    a("6. Submit to the operator-side sign-off list above before deploying.")
    a("")
    a("---")
    a("")
    a("*This file is regenerated by `/app/scripts/generate_fleet_severity_review.py`. "
      "Do not edit directly — edit `fleet_defect_severity.py` and rerun the generator.*")

    out = Path("/app/FLEET_SEVERITY_REVIEW_PACKAGE_iter251.md")
    out.write_text("\n".join(out_lines))
    print(f"wrote {out} · {len(sev_keys)} items · {total_oos} OOS · "
          f"{total_mon} MONITOR · {len(uncertain_items)} uncertain")


if __name__ == "__main__":
    main()
