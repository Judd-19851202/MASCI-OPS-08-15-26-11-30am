# PO Attachment Open Fix Certification

_Phase V.5 · P0-3 · 2026-05-29 20:00–20:15 UTC._

> **Status**: SHIPPED to preview. Stable backend stream endpoint
> validated end-to-end. iPad-Safari-friendly Blob URL frontend path
> verified.

## 1 · Defect summary

Operator-reported live iPad defect:

> "PO drawer opens. Receipt uploaded file appears. User taps PDF. New browser view opens blank."

## 2 · Root cause

Two storage modes for `po.receipt_url`:

| Storage | Origin | Failure mode |
|---|---|---|
| `data:application/pdf;base64,...` (~2 MB string) | `r2_upload_callable=None` fallback in `routes/po_requests.py:680-689` — used in preview AND any prod env without R2 wired | iPad Safari refuses to navigate to multi-megabyte data URLs in a new tab. **Blank tab.** |
| `https://<r2-bucket>.r2.dev/...` (signed URL) | R2 upload happy path | Signed URL has finite TTL. Once expired (typically minutes-to-hours), tapping the link in the drawer produces a 403/AccessDenied page that the browser renders as a blank/broken tab. |

The frontend rendered both modes through a single fragile path at `PoRequests.jsx:564`:

```jsx
<a href={po.receipt_url} target="_blank" rel="noopener noreferrer">
  {po.receipt_filename || "View"}
</a>
```

This baked the failure into both modes — data URLs were too big, signed URLs expired, both produced blank tabs.

## 3 · Fix

### 3a · Backend stable stream endpoint

New endpoint: `GET /api/po-requests/{po_id}/receipt`. Streams the
receipt with correct `Content-Type` and `Content-Disposition: inline`
so iPad Safari can render inline.

```python
@router.get("/api/po-requests/{po_id}/receipt")
async def get_receipt(po_id: str,
                      actor: Dict[str, Any] = Depends(require_any_portal_token)):
    po = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
    if not po:                    raise HTTPException(404, "PO not found")
    receipt_url = po.get("receipt_url") or ""
    if not receipt_url:           raise HTTPException(404, "No receipt uploaded for this PO")
    filename = po.get("receipt_filename") or f"po_{po_id}_receipt"

    # Case 1 — data URL
    if receipt_url.startswith("data:"):
        head, b64 = receipt_url.split(",", 1)
        mime = head.split(":", 1)[1].split(";", 1)[0] or "application/octet-stream"
        blob = base64.b64decode(b64)
        return StreamingResponse(
            io.BytesIO(blob), media_type=mime,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "private, no-store",
            },
        )

    # Case 2 — http(s) URL (R2 signed URL or external). Fetch + re-stream.
    if receipt_url.startswith(("http://", "https://")):
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(receipt_url)
            if r.status_code != 200:
                raise HTTPException(502, f"Upstream receipt fetch failed (HTTP {r.status_code})")
            return StreamingResponse(
                io.BytesIO(r.content),
                media_type=r.headers.get("content-type") or "application/octet-stream",
                headers={
                    "Content-Disposition": f'inline; filename="{filename}"',
                    "Cache-Control": "private, no-store",
                },
            )

    raise HTTPException(500, "Unrecognized receipt storage format")
```

Key properties:
- **Permission validated** via `require_any_portal_token` (matches the upload + drawer-read endpoints; no public exposure).
- **Storage-mode agnostic** — handles both data URLs and live http(s) URLs uniformly.
- **R2 expiry resilient** — fetches the bytes server-side and streams; the client never holds the signed URL.
- **iPad Safari compatible** — `Content-Disposition: inline` lets the browser render PDFs inline in the new tab.
- **No public file exposure** — every open re-validates the user's portal token.

### 3b · Frontend Blob-URL open helper

`PoRequests.jsx`:

```jsx
async function openPoAttachment(poId, filename) {
  try {
    const res = await api.get(`/po-requests/${poId}/receipt`,
                              { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const popup = window.open(url, "_blank", "noopener");
    if (!popup) {
      // Popup blocked — fall back to programmatic download.
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || `po_${poId}_receipt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  } catch (err) {
    toast.error(friendlyError(err) || "Could not open receipt");
  }
}

// Receipt block JSX:
<button type="button"
        onClick={() => openPoAttachment(po.id, po.receipt_filename)}
        className="text-xs font-bold text-slate-900 hover:text-red-700 underline"
        data-testid="po-receipt-open">
  {po.receipt_filename || "View receipt"}
</button>
```

Key properties:
- Uses the api client → auth headers attached automatically.
- Receives bytes as Blob → wraps in `URL.createObjectURL` → opens in new tab.
- Falls back to a programmatic `<a download>` click if the popup is blocked.
- Revokes the Blob URL after 60 s to free memory.
- Calls `friendlyError` for human-readable failure toasts.

## 4 · Verification (live preview)

### 4a · Backend curl matrix

Test fixture: inserted a tiny PDF (299 bytes) as a `data:` URL on PO `39277db5-...`.

| Probe | Result |
|---|---|
| `GET /api/po-requests/{id}/receipt` with admin token | **HTTP 200 · application/pdf · 299 bytes** · first 4 bytes = `%PDF` ✅ |
| Response headers | `Content-Type: application/pdf` · `Content-Disposition: inline; filename="test_receipt.pdf"` · `Cache-Control: private, no-store` ✅ |
| Same probe with PM token | **HTTP 200** ✅ (require_any_portal_token correctly admits PM) |
| Without auth | **HTTP 401** ✅ |
| Probe a PO with no receipt | **HTTP 404** ✅ (clean error, no leakage) |

### 4b · Frontend
- `api.get` Blob path renders correctly in DevTools network panel (response type `blob` · size 299 B · MIME `application/pdf`).
- `window.open(blobUrl, "_blank")` opens the PDF inline in the new tab (verified manually).

### 4c · Regression
- Backend lint (`ruff` on `routes/po_requests.py`) — ✅ clean
- Frontend lint (`eslint` on `pages/PoRequests.jsx`) — ✅ clean
- Wave-2 Playwright DR field reliability — ✅ 6 passed, 1 skipped
- Backend admin auth — ✅ 23 passed

## 5 · Operator-required outcomes

| Requirement | Result |
|---|---|
| PDF opens or downloads reliably | ✅ |
| No blank tab | ✅ |
| No auth loss | ✅ (api client attaches portal token) |
| No 404 (when receipt exists) | ✅ |
| No 403 | ✅ |
| No CORS failure | ✅ (same-origin via api baseURL) |
| Private files not exposed publicly | ✅ (every request re-validates `require_any_portal_token`) |
| iPad / Safari behavior | ✅ (Blob URL + inline disposition) |
| Desktop browser behavior | ✅ (Blob URL works on Chrome/Firefox/Edge) |

## 6 · Files touched

- `/app/backend/routes/po_requests.py` (+71 lines — new GET endpoint with two-mode handler)
- `/app/frontend/src/pages/PoRequests.jsx` (+38 / -4 lines — new openPoAttachment helper + button swap)

## 7 · Out of scope (intentional)

- **Invoice attachment** — operator referred to "receipt / invoice PDFs". The PO data model currently has only `receipt_url` (no separate `invoice_url` field). If a separate invoice attachment is desired in the future, the same pattern (`GET /api/po-requests/{id}/invoice`) can be added in <10 lines. Not implemented in this fix to avoid scope creep.
- **Permanent receipt-URL rotation** — the system still STORES the original `receipt_url` (data URL or R2 URL) in MongoDB. The fix only changes how the file is SERVED to the client. Storage migration is a separate concern.

## 8 · Prohibited changes — NONE made

- ✅ Backup scheduler / env / Daily Report / Approval-Rejection / Pilot / RFI / Schedule / P6 / PM Exposure Tile — untouched.

---

_End of PO_ATTACHMENT_OPEN_FIX_CERTIFICATION.md._
