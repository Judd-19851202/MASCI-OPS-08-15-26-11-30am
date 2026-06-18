"""TRACK 15.13F · Seed runtime certification accounts (preview-only).

Creates 2 shop users + 1 mechanic + idempotency. Refuses if APP_ENV=production
or DB_NAME=masci_safety.
"""
import os
import sys
import asyncio
from datetime import datetime, timezone

from dotenv import load_dotenv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from pymongo import MongoClient
from pm_auth import hash_password  # type: ignore

APP_ENV = (os.environ.get("APP_ENV") or "").lower()
DB_NAME = os.environ.get("DB_NAME") or ""
if APP_ENV == "production" or DB_NAME == "masci_safety":
    print(f"REFUSE: APP_ENV={APP_ENV} DB_NAME={DB_NAME} — preview only")
    sys.exit(1)

PW = "CertProof2026!"
NOW = datetime.now(timezone.utc).isoformat()
client = MongoClient(os.environ["MONGO_URL"])
db = client[DB_NAME]

ACCOUNTS = [
    # (email, role, is_asset_admin_dir, friendly_name)
    ("cert.assetadmin.directory@mascicert.local", "Equipment Manager", True,
     "Cert Asset Admin (directory_flag)"),
    ("cert.assetadmin.legacy@mascicert.local", "Asset Administrator", False,
     "Cert Asset Admin (legacy_shop_role)"),
    ("cert.mechanic@mascicert.local", "Mechanic", False,
     "Cert Mechanic (negative control)"),
]

for email, role, is_dir, name in ACCOUNTS:
    import uuid
    pw_hash = hash_password(PW)
    # UUID-shaped id; cert prefix kept for traceable rollback filter.
    uid = f"cert15-13f-{uuid.uuid4().hex[:18]}"
    db.shop_users.delete_many({"email": email})
    db.user_directory.delete_many({"email": email})
    db.shop_users.insert_one({
        "id": uid, "name": name, "email": email, "phone": "",
        "role": role, "is_active": True, "disabled": False,
        "password_hash": pw_hash, "must_change_password": False,
        "created_at": NOW, "updated_at": NOW,
        "cert_track": "TRACK15_13F",
    })
    if is_dir:
        db.user_directory.insert_one({
            "id": f"dir-{uid}", "email": email, "name": name,
            "portals": [], "disabled": False, "must_change_password": False,
            "password_hash": None, "is_asset_admin": True,
            "created_at": NOW, "updated_at": NOW,
            "cert_track": "TRACK15_13F",
        })
    print(f"✓ Seeded: {email} ({role}) is_asset_admin_dir={is_dir}")

print()
print(f"Password for all cert accounts: {PW}")
print("Login at: /shop/login")
