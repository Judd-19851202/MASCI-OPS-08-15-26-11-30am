"""
MASCI Safety Hub — Phase 1 projects (Basecamp-style per-job workspaces).

A "project" maps 1:1 to a MASCI job (seeded from JOB_LIBRARY) plus one
special company-wide "HQ" project that auto-includes every active user.

In Phase 1 we expose read-only list/get + membership management. The tool
surfaces (Message Board, To-dos, Schedule, Docs, Hill Charts) ship in
Phase 2/3 as separate routers that attach to a project_id.
"""
from __future__ import annotations

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

HQ_PROJECT_ID = "hq"

# MASCI active jobs — mirrors /app/frontend/src/lib/jobLibrary.js.
# Seeded into the projects collection on first boot.
MASCI_JOBS = [
    ("20-07", "T5686 SR 15/SR600 (SANFORD, 17/92, LAKE MARY)", "SANFORD, 17/92, LAKE MARY"),
    ("21-06", "T5736 Oveido - (426, BROADWAY)", "Oveido - (426, BROADWAY)"),
    ("22-08", "T5749 SR 436 (ALTAMONTE SPRINGS)", "ALTAMONTE SPRINGS"),
    ("24-06", "T5824 - SR 46 (W 1ST ST.)", "SR 46 (W 1ST ST.)"),
    ("24-08", "E57B2 - SR 46 (MELLONVILLE AVE)", "SR 46 (MELLONVILLE AVE)"),
    ("24-12", "CC5744 - OXFORD RD Improvements (OXFORD)", "OXFORD RD Improvements (OXFORD)"),
    ("24-13 - CP", "T5841 - SR 401 (Brevard Co, Cape Canaveral)", "SR 401 (Brevard Co, Cape Canaveral)"),
    ("25-01 - CP", "T5832 - SR 430 (Mason Ave)", "SR 430 (Mason Ave)"),
    ("25-02", "E53F5 - SR 5 (Titusville)", "SR 5 (Titusville)"),
    ("25-03", "Vol. Co Resurface", ""),
    ("25-04", "Oxford Rd Surcharge Utility", "Oxford Rd"),
    ("25-08", "T5838 SR 500 (US441) (Mt Dora)", "SR 500 (US441) (Mt Dora)"),
    ("25-10", "Pavement Management Services", ""),
    ("25-12", "N. Atlantic Ave - Drainage", "N. Atlantic Ave"),
    ("25-13", "N. Atlantic Ave - Watermain Replacement", "N. Atlantic Ave"),
    ("25-14", "E8V62 Resurf Seminole Expressway (SR 417)", "Seminole Expressway (SR 417)"),
    ("25-15", "E53F1 - SR 404, Brevard Co (Pineda)", "SR 404, Brevard Co (Pineda)"),
    ("25-16 - CP", "T5842 - SR 600 Volusia County (Orange City)", "SR 600 Volusia County (Orange City)"),
    ("25-21", "SJR2C - Loop Trail - Spruce Creek", "Loop Trail - Spruce Creek"),
    ("25-22 - CP", "T5860 SR 9 (I-95)", "SR 9 (I-95)"),
    ("25-23 - CP", "T5861 A1A - Jimmy Buffet Hwy", "A1A - Jimmy Buffet Hwy"),
    ("25-24 - CP", "G2 & G11 Canal St Improvement", "G2 & G11 Canal St"),
    ("26-01 - CP", "NSB Corbin Park Stormwater Improvements", "NSB Corbin Park"),
    ("26-02", "Resurfacing Phase I", ""),
    ("26-03 - CP", "T5874 - SR 426 Winterhaven / Aloma", "SR 426 Winterhaven / Aloma"),
    ("26-04", "E58F7 - SR 5", "SR 5"),
    ("26-05", "Fillmore Ave Reconstruction", "Fillmore Ave"),
    ("26-06", "Knox McRae Master Pump Station", "Knox McRae"),
    ("26-07", "University High Parent Loop Ext", "University High"),
    ("26-08 - CP", "T5877 - SR 44 (from I-95 to Walker Dr)", "SR 44 (from I-95 to Walker Dr)"),
    ("26-09 - CP", "T5871 Sub to CARR", ""),
]


class Project(BaseModel):
    id: str
    name: str
    project_number: Optional[str] = ""
    location: Optional[str] = ""
    is_hq: bool = False
    archived: bool = False
    created_at: str


class ProjectMember(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    added_at: str


class AddMemberRequest(BaseModel):
    user_id: str


def _proj_doc_to_model(doc: dict) -> Project:
    return Project(
        id=doc["id"],
        name=doc.get("name", ""),
        project_number=doc.get("project_number", ""),
        location=doc.get("location", ""),
        is_hq=doc.get("is_hq", False),
        archived=doc.get("archived", False),
        created_at=doc.get("created_at", ""),
    )


def build_projects_router(db, get_current_user, require_admin_or_owner):
    router = APIRouter(prefix="/api")

    async def _is_member(project_id: str, user_id: str) -> bool:
        # HQ auto-includes everyone.
        if project_id == HQ_PROJECT_ID:
            return True
        m = await db.project_members.find_one(
            {"project_id": project_id, "user_id": user_id}, {"_id": 0}
        )
        return m is not None

    @router.get("/projects", response_model=List[Project])
    async def list_projects(user: dict = Depends(get_current_user)):
        # Collect projects user is a member of, plus HQ.
        mship = await db.project_members.find(
            {"user_id": user["id"]}, {"_id": 0, "project_id": 1}
        ).to_list(2000)
        ids = {m["project_id"] for m in mship}
        ids.add(HQ_PROJECT_ID)
        # Owners / admins see every project
        if user.get("role") in {"owner", "admin"}:
            cursor = db.projects.find({"archived": {"$ne": True}}, {"_id": 0})
        else:
            cursor = db.projects.find(
                {"id": {"$in": list(ids)}, "archived": {"$ne": True}}, {"_id": 0}
            )
        docs = await cursor.sort([("is_hq", -1), ("project_number", 1)]).to_list(2000)
        return [_proj_doc_to_model(d) for d in docs]

    @router.get("/projects/{project_id}", response_model=Project)
    async def get_project(project_id: str, user: dict = Depends(get_current_user)):
        doc = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Project not found")
        if user.get("role") not in {"owner", "admin"} and not await _is_member(project_id, user["id"]):
            raise HTTPException(status_code=403, detail="Not a member of this project")
        return _proj_doc_to_model(doc)

    @router.get("/projects/{project_id}/members", response_model=List[ProjectMember])
    async def list_members(project_id: str, user: dict = Depends(get_current_user)):
        doc = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Project not found")
        if user.get("role") not in {"owner", "admin"} and not await _is_member(project_id, user["id"]):
            raise HTTPException(status_code=403, detail="Not a member of this project")

        if project_id == HQ_PROJECT_ID:
            # HQ = every active user
            docs = await db.users.find(
                {"is_active": True}, {"_id": 0, "id": 1, "email": 1, "name": 1, "role": 1}
            ).sort("email", 1).to_list(500)
            return [
                ProjectMember(
                    user_id=u["id"], email=u["email"], name=u.get("name", ""),
                    role=u.get("role", "member"), added_at="",
                )
                for u in docs
            ]
        rows = await db.project_members.find(
            {"project_id": project_id}, {"_id": 0}
        ).to_list(500)
        members: List[ProjectMember] = []
        for r in rows:
            u = await db.users.find_one({"id": r["user_id"]}, {"_id": 0})
            if not u:
                continue
            members.append(ProjectMember(
                user_id=u["id"], email=u["email"], name=u.get("name", ""),
                role=u.get("role", "member"), added_at=r.get("added_at", ""),
            ))
        return members

    @router.post("/projects/{project_id}/members", response_model=ProjectMember)
    async def add_member(
        project_id: str,
        body: AddMemberRequest,
        _: dict = Depends(require_admin_or_owner),
    ):
        if project_id == HQ_PROJECT_ID:
            raise HTTPException(
                status_code=400,
                detail="HQ membership is automatic for every active user",
            )
        if not await db.projects.find_one({"id": project_id}):
            raise HTTPException(status_code=404, detail="Project not found")
        u = await db.users.find_one({"id": body.user_id}, {"_id": 0})
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        await db.project_members.update_one(
            {"project_id": project_id, "user_id": body.user_id},
            {"$set": {
                "project_id": project_id,
                "user_id": body.user_id,
                "added_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )
        return ProjectMember(
            user_id=u["id"], email=u["email"], name=u.get("name", ""),
            role=u.get("role", "member"),
            added_at=datetime.now(timezone.utc).isoformat(),
        )

    @router.delete("/projects/{project_id}/members/{user_id}")
    async def remove_member(
        project_id: str,
        user_id: str,
        _: dict = Depends(require_admin_or_owner),
    ):
        if project_id == HQ_PROJECT_ID:
            raise HTTPException(status_code=400, detail="Cannot remove from HQ")
        res = await db.project_members.delete_one(
            {"project_id": project_id, "user_id": user_id}
        )
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Membership not found")
        return {"ok": True}

    @router.get("/projects/{project_id}/scorecard")
    async def project_scorecard(project_id: str, user: dict = Depends(get_current_user)):
        """Aggregated snapshot of all 5 tool surfaces for the project home."""
        doc = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Project not found")
        if user.get("role") not in {"owner", "admin"} and not await _is_member(project_id, user["id"]):
            raise HTTPException(status_code=403, detail="Not a member of this project")
        from tools import get_scorecard as _gs  # lazy import to avoid cycle
        return await _gs(db, project_id)

    return router


async def seed_initial_projects(db) -> None:
    """Create HQ + one project per MASCI job (idempotent on project id)."""
    try:
        await db.projects.create_index("id", unique=True)
        await db.project_members.create_index(
            [("project_id", 1), ("user_id", 1)], unique=True
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"projects index: {e}")

    now = datetime.now(timezone.utc).isoformat()

    if not await db.projects.find_one({"id": HQ_PROJECT_ID}):
        await db.projects.insert_one({
            "id": HQ_PROJECT_ID,
            "name": "MASCI HQ",
            "project_number": "",
            "location": "Company-wide",
            "is_hq": True,
            "archived": False,
            "created_at": now,
        })
        logger.info("Seeded HQ project")

    for project_number, project_name, location in MASCI_JOBS:
        pid = project_number.replace(" ", "").lower()
        if await db.projects.find_one({"id": pid}):
            continue
        await db.projects.insert_one({
            "id": pid,
            "name": project_name,
            "project_number": project_number,
            "location": location,
            "is_hq": False,
            "archived": False,
            "created_at": now,
        })
    logger.info(f"Projects seed complete — {await db.projects.count_documents({})} total")
