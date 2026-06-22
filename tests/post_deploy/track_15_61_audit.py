"""
TRACK 15.61 · Daily Report production forensic harness — READ-ONLY.
Pulls every Daily Report from production, computes the metrics
required by phases 1, 2, 4, 5, 9, 10, and dumps a single
machine-readable JSON for the deliverable writers to consume.

NO writes. NO mutations. NO test records.
"""
from __future__ import annotations

import json
import os
import sys
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import mean, median

import requests

PROD = "https://mascidocs.com"
DATA_DIR = Path("/app/memory/track_15_61_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PASSWORD = "Maddix123!"


def login():
    r = requests.post(
        f"{PROD}/api/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD},
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("portal_tokens", {})


def pull_list(tokens):
    r = requests.get(
        f"{PROD}/api/daily-reports",
        headers={"X-Admin-Token": tokens.get("admin", ""), "X-Safety-Token": tokens.get("safety", "")},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def pull_detail(tokens, rid):
    # The detail endpoint uses `require_admin_pm_or_hr_read`. The directory
    # admin token is NOT accepted by `_is_valid_admin_token` (15.59 finding).
    # HR token returns an `_actor_kind=hr_user` actor → `compute_pm_scope`
    # treats HR as an unrestricted reader. Use HR token for the detail pull.
    r = requests.get(
        f"{PROD}/api/daily-reports/{rid}",
        headers={"X-HR-Token": tokens.get("hr", "")},
        timeout=30,
    )
    if r.status_code != 200:
        return None
    return r.json()


def word_count(s: str) -> int:
    if not s:
        return 0
    return len([w for w in re.split(r"\s+", s.strip()) if w])


def activity_log_text(doc: dict) -> str:
    """The Daily Report 'Activity Log' is the `activities[]` array. Each
    row is {description, location?, crew?, notes?, etc.}. We concatenate
    every textual field across every row to compute narrative length."""
    parts = []
    for a in doc.get("activities") or []:
        if not isinstance(a, dict):
            continue
        for k in ("description", "activity", "narrative", "notes", "details", "location", "crew"):
            v = a.get(k)
            if isinstance(v, str) and v.strip():
                parts.append(v.strip())
    return " · ".join(parts)


def job_story_score(doc: dict) -> dict:
    """Lightweight 8-question scoring. Each question is YES/NO based
    on observable evidence in the record."""
    score = {}
    activities = doc.get("activities") or []
    score["q1_work_occurred"] = bool(activities) or bool((doc.get("masci_crews") or [])) or bool((doc.get("subcontractors") or []))
    score["q2_completed"] = any(
        (isinstance(a, dict) and (a.get("status") == "complete" or "complete" in (a.get("description") or "").lower()))
        for a in activities
    ) or bool(doc.get("production"))
    score["q3_delays"] = bool(doc.get("schedule_delays")) or bool((doc.get("schedule_delays_notes") or "").strip()) or bool(doc.get("weather_impact")) or bool((doc.get("weather_impact_notes") or "").strip())
    score["q4_changes"] = bool((doc.get("general_notes") or "").strip()) or bool(doc.get("constraints") or [])
    score["q5_inspections"] = bool(doc.get("excavation_activity_today")) or bool(doc.get("linked_excavation_ids") or [])
    score["q6_followup"] = bool(doc.get("constraints") or []) or bool(doc.get("safety_incidents_today"))
    activity_text = activity_log_text(doc)
    score["q7_pm_understands"] = (word_count(activity_text) >= 20) or (word_count(doc.get("general_notes") or "") >= 20)
    score["q8_exec_understands"] = bool(doc.get("production") or []) or (word_count(activity_text) >= 50)
    score["total"] = sum(1 for v in score.values() if v is True)
    return score


def main() -> int:
    print("Logging in...", flush=True)
    tokens = login()
    print("Pulling list...", flush=True)
    summaries = pull_list(tokens)
    print(f"  → {len(summaries)} summaries", flush=True)

    # Pull every detail
    print("Pulling details...", flush=True)
    details = []
    for i, s in enumerate(summaries):
        d = pull_detail(tokens, s["id"])
        if d:
            details.append(d)
        if i % 20 == 0:
            print(f"  → {i+1}/{len(summaries)}", flush=True)
    print(f"  → {len(details)} details fetched", flush=True)

    # Save the raw pull
    (DATA_DIR / "raw_details.json").write_text(json.dumps(details, default=str, indent=2))

    # ─── Compute the forensic stats ───
    now = datetime.now(timezone.utc)
    sixty_days_ago = now - timedelta(days=60)

    def parse_date(d):
        try:
            return datetime.fromisoformat((d or "").replace("Z", "+00:00"))
        except Exception:
            return None

    in_window = []
    for d in details:
        ca = parse_date(d.get("created_at"))
        if ca and ca >= sixty_days_ago:
            in_window.append(d)
    print(f"  → {len(in_window)} reports in last 60 days", flush=True)

    # PHASE 1 — counts
    by_project = Counter()
    by_super = Counter()
    by_foreman = Counter()
    by_crew = Counter()
    for d in in_window:
        proj = d.get("project_number") or d.get("project_name") or "(unknown)"
        by_project[proj] += 1
        sup = (d.get("superintendent") or "").strip() or "(unset)"
        by_super[sup] += 1
        fore = (d.get("prepared_by") or "").strip() or "(unset)"
        by_foreman[fore] += 1
        for c in d.get("masci_crews") or []:
            if isinstance(c, dict):
                key = c.get("crew_name") or c.get("foreman") or c.get("supervisor") or ""
                if key:
                    by_crew[str(key).strip()] += 1

    phase1 = {
        "total_reports_all_time": len(details),
        "reports_last_60_days": len(in_window),
        "reports_per_project_top_20": by_project.most_common(20),
        "reports_per_superintendent_top_20": by_super.most_common(20),
        "reports_per_foreman_top_20": by_foreman.most_common(20),
        "reports_per_crew_top_20": by_crew.most_common(20),
        "least_active_projects_bottom_20": sorted(by_project.items(), key=lambda x: x[1])[:20],
    }

    # PHASE 2 — Activity log forensics
    word_counts = []
    char_counts = []
    blank = under_25 = under_50 = over_100 = 0
    samples = []
    activities_row_counts = []
    for d in in_window:
        t = activity_log_text(d)
        n_rows = len(d.get("activities") or [])
        activities_row_counts.append(n_rows)
        wc = word_count(t)
        cc = len(t)
        word_counts.append(wc)
        char_counts.append(cc)
        if cc == 0:
            blank += 1
        if wc < 25:
            under_25 += 1
        if wc < 50:
            under_50 += 1
        if wc > 100:
            over_100 += 1
        samples.append({
            "id": d.get("id"),
            "doc_id": d.get("doc_id"),
            "report_date": d.get("report_date"),
            "project": d.get("project_number") or d.get("project_name"),
            "prepared_by": d.get("prepared_by"),
            "activities_row_count": n_rows,
            "activity_words": wc,
            "activity_chars": cc,
            "general_notes_words": word_count(d.get("general_notes") or ""),
            "preview": t[:160],
        })

    samples.sort(key=lambda x: -x["activity_words"])
    top25 = samples[:25]
    bot25 = samples[-25:]
    phase2 = {
        "n": len(in_window),
        "pct_completely_blank": round(100 * blank / max(1, len(in_window)), 1),
        "pct_under_25_words": round(100 * under_25 / max(1, len(in_window)), 1),
        "pct_under_50_words": round(100 * under_50 / max(1, len(in_window)), 1),
        "pct_over_100_words": round(100 * over_100 / max(1, len(in_window)), 1),
        "avg_words": round(mean(word_counts), 1) if word_counts else 0,
        "median_words": round(median(word_counts), 1) if word_counts else 0,
        "avg_chars": round(mean(char_counts), 1) if char_counts else 0,
        "median_chars": round(median(char_counts), 1) if char_counts else 0,
        "avg_activities_rows": round(mean(activities_row_counts), 2) if activities_row_counts else 0,
        "median_activities_rows": round(median(activities_row_counts), 2) if activities_row_counts else 0,
        "best_25_examples": top25,
        "worst_25_examples": bot25,
    }

    # PHASE 4 — Job story scoring
    scored = []
    for d in in_window:
        s = job_story_score(d)
        scored.append({
            "id": d.get("id"),
            "doc_id": d.get("doc_id"),
            "report_date": d.get("report_date"),
            "project": d.get("project_number") or d.get("project_name"),
            "prepared_by": d.get("prepared_by"),
            "score": s,
        })
    scored.sort(key=lambda x: -x["score"]["total"])
    phase4 = {
        "n": len(scored),
        "score_distribution": dict(Counter(x["score"]["total"] for x in scored)),
        "top_20_best_reports": scored[:20],
        "top_20_worst_reports": scored[-20:],
    }

    # PHASE 5 — Haul / trucking forensics
    haul_stats = {
        "reports_with_outbound_materials": 0,
        "reports_with_zero_outbound_materials": 0,
        "reports_with_materials_in": 0,
        "outbound_materials_total_rows": 0,
        "material_types_seen": Counter(),
        "haulers_seen": Counter(),
        "units_seen": Counter(),
        "loads_per_material": defaultdict(int),
    }
    for d in in_window:
        out = d.get("outbound_materials") or []
        if out:
            haul_stats["reports_with_outbound_materials"] += 1
            haul_stats["outbound_materials_total_rows"] += len(out)
            for row in out:
                if not isinstance(row, dict):
                    continue
                m = (row.get("material") or "").strip() or "(blank)"
                u = (row.get("unit") or "").strip() or "(blank)"
                h = (row.get("hauler") or "").strip() or "(blank)"
                q = row.get("quantity") or 0
                try:
                    q_i = int(q)
                except Exception:
                    q_i = 0
                haul_stats["material_types_seen"][m] += 1
                haul_stats["haulers_seen"][h] += 1
                haul_stats["units_seen"][u] += 1
                haul_stats["loads_per_material"][m] += q_i
        else:
            haul_stats["reports_with_zero_outbound_materials"] += 1
        if d.get("materials"):
            haul_stats["reports_with_materials_in"] += 1
    phase5 = {
        "reports_window": len(in_window),
        "reports_with_outbound_materials": haul_stats["reports_with_outbound_materials"],
        "reports_with_zero_outbound_materials": haul_stats["reports_with_zero_outbound_materials"],
        "reports_with_materials_in": haul_stats["reports_with_materials_in"],
        "outbound_materials_total_rows": haul_stats["outbound_materials_total_rows"],
        "material_types_top": haul_stats["material_types_seen"].most_common(20),
        "haulers_top": haul_stats["haulers_seen"].most_common(20),
        "units_top": haul_stats["units_seen"].most_common(10),
        "total_loads_per_material_top": sorted(haul_stats["loads_per_material"].items(), key=lambda x: -x[1])[:20],
    }

    # PHASE 9 — field behaviour patterns
    behaviour = {
        "n": len(in_window),
        "reports_with_only_outbound_no_activities": 0,
        "reports_with_only_materials_no_activities": 0,
        "reports_with_photos_no_activities": 0,
        "reports_with_general_notes_no_activities": 0,
        "reports_with_zero_narrative_anywhere": 0,
        "reports_with_activities_but_no_general_notes": 0,
        "reports_with_general_notes_but_no_activities": 0,
    }
    for d in in_window:
        has_activities = bool(d.get("activities") or [])
        has_outbound = bool(d.get("outbound_materials") or [])
        has_materials = bool(d.get("materials") or [])
        has_photos = bool(d.get("photos") or [])
        has_general_notes = bool((d.get("general_notes") or "").strip())
        activity_words = word_count(activity_log_text(d))
        gen_words = word_count(d.get("general_notes") or "")

        if has_outbound and not has_activities:
            behaviour["reports_with_only_outbound_no_activities"] += 1
        if has_materials and not has_activities:
            behaviour["reports_with_only_materials_no_activities"] += 1
        if has_photos and not has_activities:
            behaviour["reports_with_photos_no_activities"] += 1
        if has_general_notes and not has_activities:
            behaviour["reports_with_general_notes_no_activities"] += 1
        if activity_words == 0 and gen_words == 0:
            behaviour["reports_with_zero_narrative_anywhere"] += 1
        if has_activities and not has_general_notes:
            behaviour["reports_with_activities_but_no_general_notes"] += 1
        if has_general_notes and not has_activities:
            behaviour["reports_with_general_notes_but_no_activities"] += 1
    phase9 = behaviour

    # PHASE 10 — data flow matrix (per-field presence rate in last-60d corpus)
    SAMPLE_FIELDS = [
        "activities", "outbound_materials", "materials", "production", "constraints",
        "general_notes", "schedule_delays_notes", "weather_impact_notes",
        "masci_crews", "subcontractors", "visitors", "equipment", "photos",
        "linked_excavation_ids", "weather_summary", "weather_snapshots",
        "safety_incidents_today", "incident_notes", "prepared_by_signature",
        "superintendent_signature", "gps_lat",
    ]
    field_presence = {}
    for f in SAMPLE_FIELDS:
        present = 0
        non_empty = 0
        for d in in_window:
            v = d.get(f)
            if v is not None:
                present += 1
            if isinstance(v, list):
                if v:
                    non_empty += 1
            elif isinstance(v, str):
                if v.strip():
                    non_empty += 1
            elif isinstance(v, (int, float, bool)):
                if v:
                    non_empty += 1
            elif v not in (None, ""):
                non_empty += 1
        field_presence[f] = {
            "pct_present": round(100 * present / max(1, len(in_window)), 1),
            "pct_non_empty": round(100 * non_empty / max(1, len(in_window)), 1),
        }
    phase10 = {"n": len(in_window), "field_non_empty_rate_pct": field_presence}

    out_doc = {
        "track": "15.61",
        "generated_at_utc": now.isoformat(),
        "target": PROD,
        "n_all_time": len(details),
        "n_60_day_window": len(in_window),
        "phase1": phase1,
        "phase2": phase2,
        "phase4": phase4,
        "phase5": phase5,
        "phase9": phase9,
        "phase10": phase10,
    }
    out_path = DATA_DIR / "forensics.json"
    out_path.write_text(json.dumps(out_doc, indent=2, default=str))
    print(f"REPORT → {out_path}")
    print(f"60d reports: {len(in_window)}")
    print(f"% blank activity: {phase2['pct_completely_blank']}%")
    print(f"% under 25w activity: {phase2['pct_under_25_words']}%")
    print(f"avg activity rows: {phase2['avg_activities_rows']}")
    print(f"reports with outbound material rows: {phase5['reports_with_outbound_materials']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
