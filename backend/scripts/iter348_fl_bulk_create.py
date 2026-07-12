"""
iter348_fl_bulk_create.py — Bulk create native Field Leadership users.

Scope (per user spec):
  • Native FL users only — no unified-directory linking
  • NO welcome emails / NO temp-password emails / NO SMS
  • Active accounts, must_change_password=true
  • Temp passwords captured in a sidecar CSV for offline rollout
  • Skip duplicates (existing FL email), report
  • Skip rows with missing email
  • Do NOT log passwords

Output:
  /app/memory/iter348_fl_bulk_create_results.csv  (admin-only filesystem)
  STDOUT: aggregate summary only (no passwords)
"""
from __future__ import annotations
import asyncio
import csv
import os
import sys
import httpx

API_URL = os.environ.get(
    "API_URL",
    "https://backup-forensics.preview.emergentagent.com",
).rstrip("/")
SUPER_ADMIN_EMAIL = os.environ.get("MASCI_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
SUPER_ADMIN_PASSWORD = os.environ.get("MASCI_ADMIN_PASSWORD", "Maddix123!")
OUTPUT_CSV = os.environ.get(
    "OUTPUT_CSV",
    "/app/memory/iter348_fl_bulk_create_results.csv",
)

# Roster — verbatim from doc03667520260521092721.pdf
# Field is preserved exactly as-supplied; operator will correct typos later.
ROSTER = [
    ("ALLEN SMATHERS",          "allensmathers@masciae.com",       "SUPERVISOR"),
    ("ANTHONY GOES",            "anthonygoes.masci@yando.com",     "MILLING FOREMAN"),
    ("BRIAN HARDING",           "bhardin.masci@yahoo.com",         "SUPERVISOR"),
    ("CARLOS MEZA",             "cmeza-masci@yahoo.com",           "FOREMAN"),
    ("CHRISTOPHER GAINES",      "christophergaines.masci@yahoo.com","FOREMAN"),
    ("DANIEL TABORES",          "dtabores-masci@yahoo.com",        "FOREMAN"),
    ("DAVID HINSON",            "chinson_masci@yahoo.com",         "CONCRETE FINISHER"),
    ('DULIER "IVAN" LOPEZ',     "ivanlopez_masci@yahoo.com",       "FOREMAN"),
    ("HECTOR MEZA *",           "hector_meza-masci@yahoo.com",     "FOREMAN"),
    ('JAMES "TACO" OLORTEGUI',  "j.oloreque@yahoo.com",            "SUPERVISOR"),
    ("JASON CABRERA",           "icabrera.masci@yahoo.com",        "FOREMAN"),
    ("JESSIE ROBERTS",          "jroberts.masci@yahoo.com",        "SUPERVISOR"),
    ("JONATHAN MOLERO",         "jmolero_masci@yahoo.com",         "MILLING MACH"),
    ("JOSEPH ROTELLA",          "urotella-masci@yahoo.com",        "OP/FOREMAN"),
    ("LEANDRO JUAREZ",          "ijuarez@masciad.com",             "2ND MILL FOREMAN"),
    ("LEONARD WITKOWSKI",       "lennywitkowski@mascigc.com",      "SUPERVISOR"),
    ("LEONARDO CHAVEZ",         "chavez-masci@yahoo.com",          "FOREMAN"),
    ("MICHAEL TRAIL",           "mtrail-masci@yahoo.com",          "SUPERVISOR"),
    ("RAFAEL MEZA",             "rmeza_masci@yahoo.com",           "FOREMAN/EXC OP"),
    ("RICARDO MALDONADO",       "rmaldonado_masci@yahoo.com",      "SUPERVISOR"),
    ("RICH SANCHEZ",            "richsanchez@mascigc.com",         "SUPERVISOR"),
    ("ROBERT SCHUR",            "rschur_masci@yahoo.com",          "WORKING FOREMAN"),
    ("WILLIAM F MILLER",        "wmiller-masci@yahoo.com",         "FOREMAN"),
    ("rober",                   None,                              "PAVING FOREMAN"),  # incomplete row
]


def _role_for(title_hint: str) -> str:
    """Map roster title → closest allowed FL role. Operator will refine
    later — this is best-effort placeholder mapping per user spec."""
    if not title_hint:
        return "Foreman"
    t = title_hint.upper()
    if "SUPERVISOR" in t:
        return "Field Supervisor"
    if "SUPERINTENDENT" in t:
        return "Superintendent"
    if "TRUCK" in t:
        return "Truck Boss"
    if "WORKING" in t:
        return "Working Supervisor"
    # FOREMAN / OP/FOREMAN / MILLING / CONCRETE / PAVING → Foreman
    return "Foreman"


async def get_admin_token(client: httpx.AsyncClient) -> str:
    r = await client.post(
        f"{API_URL}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
    )
    r.raise_for_status()
    return r.json()["portal_tokens"]["admin"]


async def existing_emails(client: httpx.AsyncClient, token: str) -> set[str]:
    r = await client.get(
        f"{API_URL}/api/admin/field-leadership-users",
        headers={"X-Admin-Token": token},
    )
    r.raise_for_status()
    items = r.json().get("users", []) or r.json().get("items", []) or []
    return {(u.get("email") or "").strip().lower() for u in items}


async def main() -> int:
    created: list[dict] = []
    skipped_dup: list[dict] = []
    skipped_invalid: list[dict] = []
    errors: list[dict] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        token = await get_admin_token(client)
        existing = await existing_emails(client, token)
        existing_count_before = len(existing)
        print(f"[iter348] FL roster before: {existing_count_before} users")

        for name, email, original_title in ROSTER:
            row = {"name": name, "email": email, "title": original_title}
            if not email:
                skipped_invalid.append({**row, "reason": "missing email"})
                continue
            email_lower = email.strip().lower()
            if email_lower in existing:
                skipped_dup.append({**row, "reason": "email already in field_leadership_users"})
                continue

            role = _role_for(original_title)
            try:
                r = await client.post(
                    f"{API_URL}/api/admin/field-leadership-users",
                    headers={"X-Admin-Token": token},
                    json={
                        "name": name,
                        "email": email_lower,
                        "role": role,
                        "delivery": "screen",  # ← NO EMAIL SENT
                    },
                )
                if r.status_code != 200:
                    errors.append({**row, "status": r.status_code, "body": r.text[:200]})
                    continue
                data = r.json()
                user = data.get("user") or {}
                temp_pw = data.get("temp_password") or ""
                created.append({
                    "name": name,
                    "email": email_lower,
                    "original_title": original_title or "",
                    "assigned_role": role,
                    "user_id": user.get("id", ""),
                    "must_change_password": bool(user.get("must_change_password", True)),
                    "is_active": bool(user.get("is_active", True)),
                    "temp_password": temp_pw,
                })
                existing.add(email_lower)
            except Exception as e:  # noqa: BLE001
                errors.append({**row, "exception": repr(e)[:200]})

    # ── write the offline rollout CSV ───────────────────────────────
    with open(OUTPUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "name", "email", "original_title", "assigned_role",
            "user_id", "must_change_password", "is_active",
            "temp_password",
        ])
        for row in created:
            w.writerow([
                row["name"], row["email"], row["original_title"], row["assigned_role"],
                row["user_id"], row["must_change_password"], row["is_active"],
                row["temp_password"],
            ])

    # ── stdout summary (NO passwords) ───────────────────────────────
    print(f"\n[iter348] ── Bulk Create Results ──")
    print(f"  Total roster rows ………………… {len(ROSTER)}")
    print(f"  Created (native FL) …………… {len(created)}")
    print(f"  Duplicates skipped ………… {len(skipped_dup)}")
    print(f"  Invalid / missing email …… {len(skipped_invalid)}")
    print(f"  Errors ……………………………………… {len(errors)}")
    print(f"  FL count before / after …… {existing_count_before} → {existing_count_before + len(created)}")
    print(f"\n  Temp passwords written to:")
    print(f"    {OUTPUT_CSV}")
    print(f"  (filesystem-only · NOT emailed · NOT logged · NOT in API response)\n")

    if skipped_dup:
        print(f"  Duplicates ({len(skipped_dup)}):")
        for d in skipped_dup:
            print(f"    · {d['email']}  ({d['name']})")
    if skipped_invalid:
        print(f"\n  Invalid rows ({len(skipped_invalid)}):")
        for d in skipped_invalid:
            print(f"    · {d['name'] or '—'}  reason: {d['reason']}")
    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for e in errors:
            print(f"    · {e}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
