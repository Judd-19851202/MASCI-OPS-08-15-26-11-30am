from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Dict, Optional

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None  # type: ignore

try:
    import resource
except Exception:  # pragma: no cover
    resource = None  # type: ignore

logger = logging.getLogger(__name__)

INCIDENT_COLLECTION = "runtime_incident_forensics"
BOOT_COLLECTION = "runtime_boot_markers"
INCIDENT_DIR = Path("/app/memory/runtime_incidents")
INCIDENT_RETENTION_DAYS = 14
INCIDENT_FILE_LIMIT = 50
INCIDENT_MONGO_LIMIT = 200
MONITOR_INTERVAL_SECONDS = 5.0
EVENT_LOOP_LAG_WARN_MS = 500
EVENT_LOOP_LAG_FAIL_MS = 2000
MONGO_WARN_MS = 750
MONGO_FAIL_MS = 2000
REQUEST_FAILURE_TRIGGER = 3
SNAPSHOT_COOLDOWN_SECONDS = 300
DISK_WARN_PERCENT = 85.0
DISK_FAIL_PERCENT = 92.0
RSS_WARN_MB = 900
RSS_FAIL_MB = 1200
CPU_WARN_PERCENT = 85.0
CPU_FAIL_PERCENT = 95.0
FD_WARN_RATIO = 0.80
FD_FAIL_RATIO = 0.92

_SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[A-Za-z0-9._\-]+"),
    re.compile(r"(?i)(x-[a-z-]*token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(password\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"mongodb(\+srv)?://[^:@/\s]+:[^@/\s]+@"),
]

RUNTIME_STATE: Dict[str, Any] = {
    "configured": False,
    "process_started_at": datetime.now(timezone.utc),
    "startup_complete": False,
    "ready": False,
    "readiness_reason": "startup_incomplete",
    "last_readiness_change_at": datetime.now(timezone.utc).isoformat(),
    "event_loop": {
        "lag_ms": 0.0,
        "max_lag_ms": 0.0,
        "last_checked_at": None,
    },
    "mongo": {
        "ok": False,
        "latency_ms": None,
        "last_checked_at": None,
        "last_success_at": None,
    },
    "resources": {},
    "release": {},
    "health": {},
    "request_failures": {
        "consecutive": 0,
        "last_failure": None,
        "recent": deque(maxlen=12),
    },
    "last_successful_health_at": None,
    "restart_count": 0,
    "shutdown_requested": False,
}

BACKGROUND_TASKS: Dict[str, Dict[str, Any]] = {}
_INCIDENT_COOLDOWNS: Dict[str, float] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: Optional[datetime] = None) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _clip(value: Any, limit: int = 240) -> str:
    return str(value or "")[:limit]


def redact_text(text: str) -> str:
    if not text:
        return ""
    out = str(text)
    for pattern in _SECRET_PATTERNS:
        if pattern.pattern.startswith("mongodb"):
            out = pattern.sub("mongodb://***:***@", out)
        else:
            out = pattern.sub(r"\1***", out)
    return out


def classify_public_failure(*, status_code: int, headers: Dict[str, str], body_excerpt: str, curl_exit_code: Optional[int] = None) -> str:
    lowered = {str(k).lower(): str(v).lower() for k, v in (headers or {}).items()}
    server = lowered.get("server", "")
    via = lowered.get("via", "")
    body = (body_excerpt or "").lower()
    if curl_exit_code not in (None, 0) or status_code == 0:
        return "network_transport_failure"
    if status_code == 520 and "cloudflare" in server:
        return "cloudflare_edge_origin_error"
    if status_code in (502, 503, 504):
        if via:
            return "ingress_or_upstream_unavailable"
        return "origin_unavailable"
    if status_code >= 500:
        if "internal_server_error" in body or "service_starting" in body:
            return "application_runtime_failure"
        return "application_or_origin_failure"
    if 400 <= status_code < 500:
        return "application_route_or_auth_response"
    return "healthy"


def configure_runtime(app: Any, *, release_identity: Dict[str, Any]) -> None:
    if psutil is not None:
        try:
            psutil.Process(os.getpid()).cpu_percent(None)
        except Exception:
            pass
    RUNTIME_STATE["configured"] = True
    RUNTIME_STATE["process_started_at"] = _now()
    RUNTIME_STATE["release"] = dict(release_identity or {})
    app.state.runtime_reliability = RUNTIME_STATE
    app.state.runtime_background_tasks = BACKGROUND_TASKS


def set_startup_complete(app: Any, *, ready: bool, reason: str) -> None:
    app.state.ready = ready
    RUNTIME_STATE["startup_complete"] = True
    RUNTIME_STATE["ready"] = ready
    RUNTIME_STATE["readiness_reason"] = reason
    RUNTIME_STATE["last_readiness_change_at"] = _iso(_now())


def set_readiness(app: Any, *, ready: bool, reason: str) -> None:
    if bool(RUNTIME_STATE.get("ready")) != bool(ready):
        RUNTIME_STATE["last_readiness_change_at"] = _iso(_now())
    app.state.ready = ready
    RUNTIME_STATE["ready"] = ready
    RUNTIME_STATE["readiness_reason"] = reason


def _task_meta(name: str) -> Dict[str, Any]:
    return BACKGROUND_TASKS.setdefault(name, {
        "name": name,
        "category": "background",
        "critical": False,
        "status": "pending",
        "started_at": None,
        "ended_at": None,
        "last_seen_at": None,
        "last_error": None,
        "long_running": True,
        "timeout_seconds": None,
    })


def heartbeat_background_task(name: str, *, note: Optional[str] = None) -> None:
    meta = _task_meta(name)
    meta["last_seen_at"] = _iso(_now())
    if note:
        meta["note"] = _clip(note, 240)


async def _periodic_task_watch(app: Any, name: str, task: asyncio.Task, timeout_seconds: Optional[int]) -> None:
    triggered_timeout = False
    while not task.done():
        heartbeat_background_task(name)
        if timeout_seconds and not triggered_timeout:
            started_at = _parse_dt(_task_meta(name).get("started_at"))
            if started_at and (_now() - started_at).total_seconds() > timeout_seconds:
                triggered_timeout = True
                await capture_incident_snapshot(
                    app,
                    trigger="background_task_runtime_exceeded",
                    details={"task": name, "timeout_seconds": timeout_seconds},
                )
        await asyncio.sleep(15)


def register_background_task(
    app: Any,
    *,
    name: str,
    coro: Awaitable[Any],
    category: str,
    critical: bool = False,
    long_running: bool = True,
    timeout_seconds: Optional[int] = None,
) -> asyncio.Task:
    meta = _task_meta(name)
    meta.update({
        "category": category,
        "critical": critical,
        "long_running": long_running,
        "timeout_seconds": timeout_seconds,
    })

    async def _runner() -> Any:
        meta["status"] = "running"
        meta["started_at"] = _iso(_now())
        meta["ended_at"] = None
        meta["last_error"] = None
        heartbeat_background_task(name)
        watch_task = asyncio.create_task(_periodic_task_watch(app, name, asyncio.current_task(), timeout_seconds))
        try:
            result = await coro
            meta["status"] = "completed"
            return result
        except asyncio.CancelledError:
            meta["status"] = "cancelled"
            raise
        except Exception as exc:  # noqa: BLE001
            meta["status"] = "failed"
            meta["last_error"] = _clip(repr(exc), 400)
            await capture_incident_snapshot(
                app,
                trigger="background_task_failed",
                details={"task": name, "category": category, "error": repr(exc)},
            )
            raise
        finally:
            meta["ended_at"] = _iso(_now())
            watch_task.cancel()
            try:
                await watch_task
            except BaseException:
                pass

    task = asyncio.create_task(_runner())
    meta["task"] = task
    return task


def track_existing_background_task(
    app: Any,
    *,
    name: str,
    task: asyncio.Task,
    category: str,
    critical: bool = False,
    long_running: bool = True,
    timeout_seconds: Optional[int] = None,
) -> asyncio.Task:
    meta = _task_meta(name)
    meta.update({
        "task": task,
        "category": category,
        "critical": critical,
        "long_running": long_running,
        "timeout_seconds": timeout_seconds,
        "status": "running",
        "started_at": _iso(_now()),
        "ended_at": None,
        "last_error": None,
    })
    heartbeat_background_task(name)

    async def _watch_existing() -> None:
        watch_task = asyncio.create_task(_periodic_task_watch(app, name, task, timeout_seconds))
        try:
            await task
            if meta.get("status") == "running":
                meta["status"] = "completed"
        except asyncio.CancelledError:
            meta["status"] = "cancelled"
            raise
        except Exception as exc:  # noqa: BLE001
            meta["status"] = "failed"
            meta["last_error"] = _clip(repr(exc), 400)
            await capture_incident_snapshot(
                app,
                trigger="background_task_failed",
                details={"task": name, "category": category, "error": repr(exc)},
            )
        finally:
            meta["ended_at"] = _iso(_now())
            watch_task.cancel()
            try:
                await watch_task
            except BaseException:
                pass

    asyncio.create_task(_watch_existing())
    return task


async def cancel_registered_background_tasks(app: Any, *, exclude: Optional[set[str]] = None) -> None:
    exclude = exclude or set()
    RUNTIME_STATE["shutdown_requested"] = True
    tasks = []
    for name, meta in BACKGROUND_TASKS.items():
        if name in exclude:
            continue
        task = meta.get("task")
        if task is None or task.done():
            continue
        meta["status"] = "cancelling"
        task.cancel()
        tasks.append(task)
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        raw = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _task_rows() -> list[Dict[str, Any]]:
    rows = []
    for name, meta in sorted(BACKGROUND_TASKS.items()):
        started_at = _parse_dt(meta.get("started_at"))
        runtime_s = None
        if started_at and meta.get("status") in {"running", "cancelling"}:
            runtime_s = int((_now() - started_at).total_seconds())
        rows.append({
            "name": name,
            "category": meta.get("category"),
            "critical": bool(meta.get("critical")),
            "status": meta.get("status"),
            "started_at": meta.get("started_at"),
            "ended_at": meta.get("ended_at"),
            "last_seen_at": meta.get("last_seen_at"),
            "runtime_s": runtime_s,
            "last_error": meta.get("last_error"),
            "long_running": bool(meta.get("long_running", True)),
        })
    return rows


def _resource_snapshot() -> Dict[str, Any]:
    process = psutil.Process(os.getpid()) if psutil is not None else None
    cpu_percent = None
    rss_mb = None
    fd_count = None
    fd_limit = None
    thread_count = threading.active_count()
    if process is not None:
        try:
            cpu_percent = round(float(process.cpu_percent(None)), 1)
        except Exception:
            cpu_percent = None
        try:
            rss_mb = round(float(process.memory_info().rss) / (1024 * 1024), 1)
        except Exception:
            rss_mb = None
        try:
            fd_count = process.num_fds()  # type: ignore[attr-defined]
        except Exception:
            fd_count = None
        try:
            thread_count = process.num_threads()
        except Exception:
            pass
    if resource is not None:
        try:
            fd_limit = int(resource.getrlimit(resource.RLIMIT_NOFILE)[0])
        except Exception:
            fd_limit = None
    disk = shutil.disk_usage("/app")
    disk_percent = round((disk.used / disk.total) * 100, 1)
    return {
        "cpu_percent": cpu_percent,
        "rss_mb": rss_mb,
        "disk_percent": disk_percent,
        "fd_count": fd_count,
        "fd_limit": fd_limit,
        "thread_count": thread_count,
        "active_asyncio_tasks": len(asyncio.all_tasks()),
    }


def runtime_health_snapshot(app: Any) -> Dict[str, Any]:
    lag_ms = float(RUNTIME_STATE["event_loop"].get("lag_ms") or 0.0)
    mongo_ok = bool(RUNTIME_STATE["mongo"].get("ok"))
    mongo_latency = RUNTIME_STATE["mongo"].get("latency_ms")
    resources = dict(RUNTIME_STATE.get("resources") or {})
    ready_flag = bool(getattr(app.state, "ready", False))
    failed_tasks = [t for t in _task_rows() if t.get("status") == "failed"]

    readiness_ok = (
        ready_flag
        and mongo_ok
        and lag_ms < EVENT_LOOP_LAG_FAIL_MS
        and not RUNTIME_STATE.get("shutdown_requested")
    )
    degraded = (
        lag_ms >= EVENT_LOOP_LAG_WARN_MS
        or (mongo_latency is not None and mongo_latency >= MONGO_WARN_MS)
        or bool(failed_tasks)
        or float(resources.get("disk_percent") or 0.0) >= DISK_WARN_PERCENT
        or float(resources.get("cpu_percent") or 0.0) >= CPU_WARN_PERCENT
        or float(resources.get("rss_mb") or 0.0) >= RSS_WARN_MB
    )

    if not readiness_ok:
        overall = "unavailable"
    elif degraded:
        overall = "degraded"
    else:
        overall = "healthy"

    reason_codes = []
    if not ready_flag:
        reason_codes.append("startup_not_ready")
    if not mongo_ok:
        reason_codes.append("mongo_unreachable")
    if lag_ms >= EVENT_LOOP_LAG_FAIL_MS:
        reason_codes.append("event_loop_starved")
    if failed_tasks:
        reason_codes.append("background_task_failure")
    if float(resources.get("disk_percent") or 0.0) >= DISK_FAIL_PERCENT:
        reason_codes.append("disk_pressure")

    return {
        "liveness": {"ok": True, "state": "alive"},
        "readiness": {
            "ok": readiness_ok,
            "state": "ready" if readiness_ok else "not_ready",
            "reason": RUNTIME_STATE.get("readiness_reason"),
        },
        "full_health": {
            "ok": overall == "healthy",
            "state": overall,
            "reason_codes": reason_codes,
        },
        "event_loop_lag_ms": round(lag_ms, 1),
        "mongo_latency_ms": mongo_latency,
        "mongo_ok": mongo_ok,
        "resources": resources,
        "background_tasks": _task_rows(),
        "release": dict(RUNTIME_STATE.get("release") or {}),
        "restart_count": int(RUNTIME_STATE.get("restart_count") or 0),
        "last_successful_health_at": RUNTIME_STATE.get("last_successful_health_at"),
        "last_successful_db_at": RUNTIME_STATE["mongo"].get("last_success_at"),
    }


def public_liveness_headers(app: Any) -> Dict[str, str]:
    health = runtime_health_snapshot(app)
    return {
        "X-MASCI-Liveness": health["liveness"]["state"],
        "X-MASCI-Readiness": health["readiness"]["state"],
        "X-MASCI-Full-Health": health["full_health"]["state"],
        "X-MASCI-Instance": _clip(RUNTIME_STATE.get("release", {}).get("instance_fingerprint"), 32),
    }


def public_readiness_payload(app: Any) -> Dict[str, Any]:
    health = runtime_health_snapshot(app)
    return {
        "ok": bool(health["readiness"]["ok"]),
        "state": health["readiness"]["state"],
        "reason": health["readiness"]["reason"],
        "event_loop_ok": health["event_loop_lag_ms"] < EVENT_LOOP_LAG_FAIL_MS,
        "mongo_ok": health["mongo_ok"],
        "startup_complete": bool(RUNTIME_STATE.get("startup_complete")),
    }


async def build_public_full_health_payload(app: Any, *, backup_recent: bool, scheduler_alive: bool) -> Dict[str, bool]:
    health = runtime_health_snapshot(app)
    mongo_ok = bool(health["mongo_ok"] and health["event_loop_lag_ms"] < EVENT_LOOP_LAG_FAIL_MS)
    ok = bool(health["readiness"]["ok"] and mongo_ok and scheduler_alive and backup_recent)
    if ok:
        RUNTIME_STATE["last_successful_health_at"] = _iso(_now())
    return {
        "ok": ok,
        "mongo": mongo_ok,
        "scheduler": bool(scheduler_alive),
        "backup_recent": bool(backup_recent),
    }


def _should_capture(trigger: str) -> bool:
    now_monotonic = time.monotonic()
    last = _INCIDENT_COOLDOWNS.get(trigger)
    if last is not None and (now_monotonic - last) < SNAPSHOT_COOLDOWN_SECONDS:
        return False
    _INCIDENT_COOLDOWNS[trigger] = now_monotonic
    return True


def _tail_backend_log() -> str:
    path = Path("/var/log/supervisor/backend.err.log")
    if not path.exists():
        return ""
    try:
        with path.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - 8192))
            raw = fh.read().decode("utf-8", errors="replace")
        return redact_text(raw[-6000:])
    except Exception:
        return ""


async def _scheduler_lock_snapshot(db: Any) -> list[Dict[str, Any]]:
    rows = []
    try:
        cursor = db.scheduler_locks.find({}, {"_id": 1, "owner_id": 1, "acquired_at": 1, "expires_at": 1}).limit(50)
        async for row in cursor:
            rows.append({
                "scheduler": row.get("_id"),
                "owner_id": row.get("owner_id"),
                "acquired_at": _iso(_parse_dt(row.get("acquired_at"))),
                "expires_at": _iso(_parse_dt(row.get("expires_at"))),
            })
    except Exception as exc:  # noqa: BLE001
        rows.append({"error": _clip(exc, 200)})
    return rows


def _backup_state_snapshot() -> Dict[str, Any]:
    try:
        from server import _BACKUP_SCHEDULER_STATE  # noqa: PLC0415
        state = dict(_BACKUP_SCHEDULER_STATE)
        state.pop("failed_attempts", None)
        state.pop("last_run_for_hour", None)
        return state
    except Exception:
        return {}


async def _public_health_correlation() -> Optional[Dict[str, Any]]:
    enabled = (os.environ.get("ENABLE_PUBLIC_HEALTH_CORRELATION") or "").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return None
    base = (os.environ.get("PROD_HEALTH_URL") or "").strip().rstrip("/")
    if not base:
        return None
    try:
        import httpx  # noqa: PLC0415
        async with httpx.AsyncClient(timeout=3.0, follow_redirects=False) as client:
            response = await client.get(f"{base}/api/health")
        headers = {k.lower(): v for k, v in response.headers.items() if k.lower() in {"server", "via", "cf-ray", "content-type"}}
        body_excerpt = redact_text(response.text[:200])
        return {
            "url": f"{base}/api/health",
            "status_code": response.status_code,
            "headers": headers,
            "classification": classify_public_failure(
                status_code=response.status_code,
                headers=headers,
                body_excerpt=body_excerpt,
            ),
            "body_excerpt": body_excerpt,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": _clip(repr(exc), 200)}


async def capture_incident_snapshot(app: Any, *, trigger: str, details: Dict[str, Any]) -> Optional[str]:
    if not _should_capture(trigger):
        return None
    health = runtime_health_snapshot(app)
    resources = dict(RUNTIME_STATE.get("resources") or _resource_snapshot())
    process_started = RUNTIME_STATE.get("process_started_at") or _now()
    uptime_s = int((_now() - process_started).total_seconds()) if isinstance(process_started, datetime) else None
    snapshot_id = f"incident-{uuid.uuid4().hex}"
    document = {
        "_id": snapshot_id,
        "id": snapshot_id,
        "captured_at": _iso(_now()),
        "captured_dt": _now(),
        "trigger": trigger,
        "details": {k: _clip(v, 240) for k, v in (details or {}).items()},
        "release": dict(RUNTIME_STATE.get("release") or {}),
        "instance_fingerprint": RUNTIME_STATE.get("release", {}).get("instance_fingerprint"),
        "process": {
            "pid": os.getpid(),
            "uptime_s": uptime_s,
            "restart_count": int(RUNTIME_STATE.get("restart_count") or 0),
            "thread_count": resources.get("thread_count"),
            "active_asyncio_tasks": resources.get("active_asyncio_tasks"),
        },
        "health": health,
        "event_loop_lag_ms": health.get("event_loop_lag_ms"),
        "mongo": {
            "ok": RUNTIME_STATE["mongo"].get("ok"),
            "latency_ms": RUNTIME_STATE["mongo"].get("latency_ms"),
            "last_success_at": RUNTIME_STATE["mongo"].get("last_success_at"),
        },
        "resources": resources,
        "scheduler_tasks": _task_rows(),
        "backup_state": _backup_state_snapshot(),
        "recent_errors": list(RUNTIME_STATE["request_failures"].get("recent") or []),
        "backend_log_excerpt": _tail_backend_log(),
        "storage": "pending",
    }

    db = getattr(app.state, "db", None)
    if db is not None:
        document["scheduler_locks"] = await _scheduler_lock_snapshot(db)
        public_probe = await _public_health_correlation()
        if public_probe is not None:
            document["public_health"] = public_probe
        try:
            await db[INCIDENT_COLLECTION].insert_one(document)
            document["storage"] = "mongo"
            try:
                total = await db[INCIDENT_COLLECTION].count_documents({})
                if total > INCIDENT_MONGO_LIMIT:
                    overflow = total - INCIDENT_MONGO_LIMIT
                    cursor = db[INCIDENT_COLLECTION].find({}, {"_id": 1}).sort("captured_dt", 1).limit(overflow)
                    ids = [row["_id"] async for row in cursor]
                    if ids:
                        await db[INCIDENT_COLLECTION].delete_many({"_id": {"$in": ids}})
            except Exception:
                pass
            return snapshot_id
        except Exception as exc:  # noqa: BLE001
            logger.warning("[runtime-reliability] mongo incident write failed: %s", exc)

    try:
        INCIDENT_DIR.mkdir(parents=True, exist_ok=True)
        path = INCIDENT_DIR / f"{document['captured_at'].replace(':', '-')}_{trigger}.json"
        document["storage"] = "file_fallback"
        path.write_text(redact_text(json.dumps(document, default=str, indent=2)), encoding="utf-8")
        files = sorted(INCIDENT_DIR.glob("*.json"))
        if len(files) > INCIDENT_FILE_LIMIT:
            for old in files[: len(files) - INCIDENT_FILE_LIMIT]:
                old.unlink(missing_ok=True)
        return snapshot_id
    except Exception as exc:  # noqa: BLE001
        logger.warning("[runtime-reliability] file incident write failed: %s", exc)
        return None


async def ensure_incident_indexes(db: Any) -> None:
    try:
        await db[INCIDENT_COLLECTION].create_index("captured_dt", expireAfterSeconds=INCIDENT_RETENTION_DAYS * 86400)
        await db[INCIDENT_COLLECTION].create_index([("trigger", 1), ("captured_dt", -1)])
        await db[INCIDENT_COLLECTION].create_index([("instance_fingerprint", 1), ("captured_dt", -1)])
    except Exception as exc:  # noqa: BLE001
        logger.warning("[runtime-reliability] incident index ensure failed: %s", exc)


async def record_worker_boot(app: Any, db: Any) -> None:
    await ensure_incident_indexes(db)
    now = _now()
    release = dict(RUNTIME_STATE.get("release") or {})
    current = {
        "_id": "latest",
        "started_at": _iso(now),
        "instance_fingerprint": release.get("instance_fingerprint"),
        "commit": release.get("commit"),
        "source_hash": release.get("source_hash"),
        "pid": os.getpid(),
    }
    previous = await db[BOOT_COLLECTION].find_one({"_id": "latest"}, {"_id": 0})
    if previous and previous.get("instance_fingerprint") != current["instance_fingerprint"]:
        RUNTIME_STATE["restart_count"] = int(previous.get("restart_count") or 0) + 1
        await capture_incident_snapshot(
            app,
            trigger="worker_restart_detected",
            details={
                "previous_instance": previous.get("instance_fingerprint"),
                "previous_started_at": previous.get("started_at"),
                "current_pid": os.getpid(),
            },
        )
    current["restart_count"] = int(RUNTIME_STATE.get("restart_count") or 0)
    await db[BOOT_COLLECTION].update_one({"_id": "latest"}, {"$set": current}, upsert=True)


async def observe_request_result(app: Any, *, path: str, status_code: int, exception: Optional[BaseException] = None) -> None:
    if not path.startswith("/api"):
        return
    failures = RUNTIME_STATE["request_failures"]
    if status_code >= 500 and not (status_code == 503 and not getattr(app.state, "ready", False)):
        failures["consecutive"] = int(failures.get("consecutive") or 0) + 1
        event = {
            "at": _iso(_now()),
            "path": path,
            "status_code": status_code,
            "error": _clip(repr(exception), 240) if exception else None,
        }
        failures["last_failure"] = event
        failures["recent"].append(event)
        if failures["consecutive"] >= REQUEST_FAILURE_TRIGGER:
            await capture_incident_snapshot(
                app,
                trigger="consecutive_internal_request_failures",
                details={
                    "path": path,
                    "status_code": status_code,
                    "consecutive": failures["consecutive"],
                },
            )
    else:
        failures["consecutive"] = 0


async def _monitor_tick(app: Any, db: Any) -> None:
    resources = _resource_snapshot()
    RUNTIME_STATE["resources"] = resources
    RUNTIME_STATE["event_loop"]["last_checked_at"] = _iso(_now())
    mongo_ok = False
    mongo_latency_ms = None
    started = time.perf_counter()
    try:
        await asyncio.wait_for(db.command("ping"), timeout=2.0)
        mongo_latency_ms = int((time.perf_counter() - started) * 1000)
        mongo_ok = True
        RUNTIME_STATE["mongo"]["last_success_at"] = _iso(_now())
    except Exception as exc:  # noqa: BLE001
        mongo_ok = False
        RUNTIME_STATE["request_failures"]["recent"].append({
            "at": _iso(_now()),
            "path": "mongo:ping",
            "status_code": 0,
            "error": _clip(repr(exc), 240),
        })
    RUNTIME_STATE["mongo"].update({
        "ok": mongo_ok,
        "latency_ms": mongo_latency_ms,
        "last_checked_at": _iso(_now()),
    })

    health = runtime_health_snapshot(app)
    RUNTIME_STATE["health"] = health
    if health["readiness"]["ok"]:
        RUNTIME_STATE["last_successful_health_at"] = _iso(_now())

    lag_ms = float(RUNTIME_STATE["event_loop"].get("lag_ms") or 0.0)
    if lag_ms >= EVENT_LOOP_LAG_FAIL_MS:
        await capture_incident_snapshot(app, trigger="event_loop_lag_exceeded", details={"lag_ms": lag_ms})
    if (not mongo_ok) or (mongo_latency_ms is not None and mongo_latency_ms >= MONGO_FAIL_MS):
        await capture_incident_snapshot(
            app,
            trigger="mongo_probe_distress",
            details={"mongo_ok": mongo_ok, "latency_ms": mongo_latency_ms},
        )
    if not health["readiness"]["ok"] and RUNTIME_STATE.get("startup_complete"):
        await capture_incident_snapshot(
            app,
            trigger="readiness_false",
            details={"reason": health["readiness"]["reason"]},
        )

    fd_count = resources.get("fd_count")
    fd_limit = resources.get("fd_limit")
    fd_ratio = (float(fd_count) / float(fd_limit)) if fd_count and fd_limit else 0.0
    if (
        float(resources.get("disk_percent") or 0.0) >= DISK_FAIL_PERCENT
        or float(resources.get("rss_mb") or 0.0) >= RSS_FAIL_MB
        or float(resources.get("cpu_percent") or 0.0) >= CPU_FAIL_PERCENT
        or fd_ratio >= FD_FAIL_RATIO
    ):
        await capture_incident_snapshot(
            app,
            trigger="resource_threshold_crossed",
            details={
                "disk_percent": resources.get("disk_percent"),
                "rss_mb": resources.get("rss_mb"),
                "cpu_percent": resources.get("cpu_percent"),
                "fd_ratio": round(fd_ratio, 3),
            },
        )


def start_runtime_monitor(app: Any, db: Any) -> asyncio.Task:
    async def _monitor() -> None:
        await record_worker_boot(app, db)
        last = time.monotonic()
        while True:
            await asyncio.sleep(MONITOR_INTERVAL_SECONDS)
            now_m = time.monotonic()
            lag_ms = max(0.0, (now_m - last - MONITOR_INTERVAL_SECONDS) * 1000.0)
            last = now_m
            RUNTIME_STATE["event_loop"]["lag_ms"] = lag_ms
            RUNTIME_STATE["event_loop"]["max_lag_ms"] = max(
                float(RUNTIME_STATE["event_loop"].get("max_lag_ms") or 0.0),
                lag_ms,
            )
            await _monitor_tick(app, db)

    return register_background_task(
        app,
        name="runtime-reliability-monitor",
        coro=_monitor(),
        category="runtime-monitor",
        critical=True,
        long_running=True,
    )


__all__ = [
    "BACKGROUND_TASKS",
    "BOOT_COLLECTION",
    "INCIDENT_COLLECTION",
    "RUNTIME_STATE",
    "build_public_full_health_payload",
    "cancel_registered_background_tasks",
    "capture_incident_snapshot",
    "classify_public_failure",
    "configure_runtime",
    "heartbeat_background_task",
    "observe_request_result",
    "public_liveness_headers",
    "public_readiness_payload",
    "record_worker_boot",
    "redact_text",
    "register_background_task",
    "runtime_health_snapshot",
    "set_readiness",
    "set_startup_complete",
    "start_runtime_monitor",
    "track_existing_background_task",
]