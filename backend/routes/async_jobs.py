from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response

from lib.async_jobs import (
    get_async_job,
    get_async_job_binary_result,
    serialize_async_job_status,
)


def register_async_job_routes(api_router: APIRouter) -> None:
    @api_router.get("/jobs/{job_id}/status")
    async def async_job_status(job_id: str):
        meta = await get_async_job(job_id)
        if not meta:
            raise HTTPException(status_code=404, detail="job not found")
        return serialize_async_job_status(meta)

    @api_router.get("/jobs/{job_id}/result")
    async def async_job_result(job_id: str, token: str = Query(..., min_length=8)):
        resolved = await get_async_job_binary_result(job_id, token)
        if not resolved:
            raise HTTPException(status_code=404, detail="job result not found")
        _, stored = resolved
        filename = str(stored.get("filename") or f"job-{job_id}.bin")
        return Response(
            content=stored.get("content") or b"",
            media_type=str(stored.get("media_type") or "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-store",
                "X-Async-Job-Id": job_id,
            },
        )


__all__ = ["register_async_job_routes"]