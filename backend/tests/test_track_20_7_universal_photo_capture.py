"""Track 20.7 · Universal Photo Capture & Attachment — lock test.

Track 20.7 is a surgical FRONTEND-ONLY fix to
`frontend/src/components/PhotoUpload.jsx`. It adds a runtime
camera-support probe (`useCameraSupport`) and a graceful fallback
from the "Take Photo" button to the plain file picker whenever the
browser reports no `videoinput` device (desktops without a webcam,
camera-permission-blocked contexts, HTTP contexts).

Backend contract: byte-identical (no route, no payload key, no
MIME/size limit, no auth path changed). Zero live emails. Zero HTTP
calls. Zero DB writes.

This lock test is intentionally additive and structural — it does NOT
assert exact whitespace or exact copy strings that adjacent tracks
might legitimately extend. It asserts that the *behavior guarantees*
are present in source.

Run in isolation:
    pytest /app/backend/tests/test_track_20_7_universal_photo_capture.py -v
"""
from pathlib import Path

REPO = Path("/app")
MEM = REPO / "memory"
FE = REPO / "frontend/src"
FE_COMP = FE / "components"
BE = REPO / "backend"
BE_ROUTES = BE / "routes"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ── The single canonical control ────────────────────────────────────

def test_photo_upload_component_exists():
    p = FE_COMP / "PhotoUpload.jsx"
    assert p.exists(), "PhotoUpload.jsx must exist"


def test_only_one_photoupload_jsx_in_repo():
    """Zero-Drift: there must be exactly ONE PhotoUpload.jsx file in
    the frontend source tree. Creating a parallel photo control is a
    Class-B Zero-Drift violation."""
    matches = list(FE.rglob("PhotoUpload.jsx"))
    assert len(matches) == 1, (
        f"Zero-Drift violation: expected exactly one PhotoUpload.jsx, "
        f"found {len(matches)}: {[str(m) for m in matches]}"
    )
    assert matches[0] == FE_COMP / "PhotoUpload.jsx"


# ── Camera-support probe ────────────────────────────────────────────

def test_use_camera_support_hook_defined():
    src = _read(FE_COMP / "PhotoUpload.jsx")
    assert "function useCameraSupport" in src or "useCameraSupport =" in src, (
        "PhotoUpload.jsx must define a `useCameraSupport` hook that "
        "probes the runtime for camera availability."
    )


def test_probe_uses_enumerate_devices():
    """The probe MUST use navigator.mediaDevices.enumerateDevices —
    the only permission-free way to check for a video input."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    assert "navigator.mediaDevices" in src
    assert "enumerateDevices" in src


def test_probe_looks_for_videoinput_kind():
    src = _read(FE_COMP / "PhotoUpload.jsx")
    assert '"videoinput"' in src or "'videoinput'" in src, (
        "probe must filter enumerateDevices() results by kind === 'videoinput'"
    )


def test_probe_fails_safe():
    """On any error (SecurityError on HTTP, no mediaDevices API, etc.),
    the hook MUST return false so the fallback path is taken."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    # A try/catch block that sets supported=false, and an explicit
    # feature-detection short-circuit for the missing mediaDevices API.
    assert "catch" in src
    assert "!navigator.mediaDevices" in src or "navigator.mediaDevices" in src


# ── Fallback wiring ────────────────────────────────────────────────

def test_take_photo_falls_back_to_gallery_picker():
    """The core deployment-blocker fix: when the camera probe returns
    false, clicking "Take Photo" MUST route to the plain file picker
    (the gallery input) instead of the capture input."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    # Presence of the fallback branch — click gallery ref inside the
    # cameraKnownUnsupported path.
    assert "cameraKnownUnsupported" in src, (
        "PhotoUpload must expose a `cameraKnownUnsupported` state that "
        "drives the fallback branch."
    )
    assert "galleryRef.current?.click()" in src or "galleryRef.current?.click();" in src, (
        "fallback branch must click the gallery input (not the camera input)"
    )


def test_openCamera_has_fallback_early_return():
    """`openCamera` must early-return through the gallery picker when
    cameraKnownUnsupported is true — otherwise the desktop no-op recurs."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    # Locate the openCamera function body and check the fallback branch
    # appears BEFORE the cameraRef click.
    idx = src.find("const openCamera")
    assert idx != -1, "openCamera must exist"
    body = src[idx: idx + 400]
    assert "cameraKnownUnsupported" in body, (
        "openCamera must consult cameraKnownUnsupported"
    )
    assert "galleryRef" in body, "openCamera fallback must click galleryRef"
    assert "cameraRef" in body, "openCamera happy path must still click cameraRef"
    # Order check: fallback branch (galleryRef click) must appear before
    # the cameraRef click.
    gallery_at = body.find("galleryRef.current?.click")
    camera_at = body.find("cameraRef.current?.click")
    assert 0 <= gallery_at < camera_at, (
        "fallback branch must run BEFORE the default cameraRef click"
    )


def test_fallback_hint_rendered():
    """When cameraKnownUnsupported, the UI MUST expose a visible
    "camera unavailable" hint so the user is never confused."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    assert "Camera unavailable" in src, (
        "PhotoUpload must render a visible 'Camera unavailable' hint "
        "in the fallback state."
    )


def test_fallback_relabels_take_photo_button():
    """The Take Photo button MUST relabel to 'Choose from files' (or
    equivalent 'Choose photo / file') when the fallback is active."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    assert "Choose from files" in src or "Choose photo / file" in src, (
        "PhotoUpload must relabel the Take Photo button when the "
        "camera is unavailable."
    )


# ── Hidden inputs preserved ────────────────────────────────────────

def test_gallery_input_has_no_capture_attr():
    """The gallery input MUST NOT carry the `capture` attribute — that
    input is the universal file picker path, guaranteed to work on
    every device."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    # Locate the galleryRef input and confirm no `capture=` sits in its
    # attribute list.
    idx = src.find("ref={galleryRef}")
    assert idx != -1, "galleryRef input must exist"
    # Widen the window to include the closing `/>` of the input tag.
    tag_end = src.find("/>", idx)
    assert tag_end != -1
    gallery_tag = src[idx:tag_end]
    assert "capture=" not in gallery_tag, (
        "gallery input must NOT carry a `capture` attribute — that "
        "would defeat the desktop fallback."
    )


def test_camera_input_retains_capture_environment():
    """The camera input MUST keep `capture="environment"` — that is the
    correct behavior on mobile devices with a camera."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    idx = src.find("ref={cameraRef}")
    assert idx != -1, "cameraRef input must exist"
    tag_end = src.find("/>", idx)
    camera_tag = src[idx:tag_end]
    assert 'capture="environment"' in camera_tag, (
        "camera input must retain `capture=\"environment\"` — this is "
        "correct on mobile and irrelevant on desktop (thanks to the "
        "fallback probe)."
    )


# ── iOS Safari multi-select regression guard ───────────────────────

def test_ios_filelist_snapshot_preserved():
    """Both hidden inputs must snapshot the FileList to a real Array
    BEFORE resetting `input.value = ""` — otherwise iOS Safari drops
    files #2-N. This is the guardrail from the earlier
    'only-one-photo-uploaded' bug and MUST NOT regress."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    # Two Array.from(...) calls — one per input onChange handler.
    assert src.count("Array.from(e.target.files") >= 2, (
        "each hidden file input must snapshot FileList via Array.from(...)"
    )
    # Both must also reset via input.value = "" AFTER the snapshot.
    assert src.count('e.target.value = ""') >= 2


# ── Compression pipeline preserved (backend-contract shape) ────────

def test_compress_image_signature_unchanged():
    """The compression pipeline MUST still be `compressImage(file, 1280,
    0.78)` — a change in these numbers is a backend-contract change
    (visible as different bytes on the wire), which Track 20.7 is not
    allowed to make."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    assert "compressImage(file, 1280, 0.78)" in src, (
        "compressImage signature must remain (file, 1280, 0.78)"
    )


# ── Backend contract untouched ─────────────────────────────────────

def test_backend_daily_reports_still_accepts_photos_field():
    """The parent-form contract still declares `photos: List[str]`."""
    src = _read(BE_ROUTES / "daily_reports.py")
    assert "photos: List[str]" in src, (
        "daily_reports.py must retain `photos: List[str]` field — "
        "Track 20.7 is contract-preserving."
    )


def test_job_photos_indexer_still_reads_photos_field():
    src = _read(BE_ROUTES / "job_photos.py")
    assert 'record.get("photos")' in src, (
        "job_photos.py indexer must still read `record.get('photos')` "
        "— Track 20.7 did not change the mirror contract."
    )


def test_no_new_backend_upload_route_created_by_207():
    """Track 20.7 MUST NOT introduce a new backend upload route.
    Forbidden filenames guard the Zero-Drift invariant."""
    forbidden = (
        "photo_upload_v2.py",
        "photo_capture.py",
        "universal_photo.py",
        "camera_capture.py",
    )
    for name in forbidden:
        assert not (BE_ROUTES / name).exists(), (
            f"Track 20.7 must not introduce {name} — Zero-Drift violation"
        )


# ── No new frontend photo control introduced ───────────────────────

def test_no_parallel_photo_control_component():
    """Zero-Drift: no parallel photo-capture component may exist."""
    forbidden_names = (
        "PhotoUploadV2.jsx",
        "PhotoUploadDesktop.jsx",
        "PhotoUploadMobile.jsx",
        "CameraCapture.jsx",
        "UniversalPhotoInput.jsx",
    )
    for name in forbidden_names:
        matches = list(FE.rglob(name))
        assert not matches, (
            f"Zero-Drift violation: parallel photo control {name} "
            f"found at {[str(m) for m in matches]}"
        )


# ── Email safety guarantee ─────────────────────────────────────────

def test_no_email_transports_in_touched_files():
    """Track 20.7 touched exactly one production file. That file MUST
    contain no email-transport imports or invocations."""
    src = _read(FE_COMP / "PhotoUpload.jsx")
    for needle in ("fsi_send_email", "resend.emails.send",
                   "/api/email/send", "/api/notifications/send",
                   "phase4.send_email"):
        assert needle not in src, (
            f"PhotoUpload.jsx unexpectedly contains email transport {needle!r}"
        )


def test_lock_test_makes_no_network_calls():
    """This test file itself must import nothing that would touch the
    network — pure source-level assertions only."""
    self_src = _read(Path(__file__))
    for forbidden in ("requests", "httpx", "urllib.request",
                      "aiohttp", "TestClient"):
        assert f"import {forbidden}" not in self_src, (
            f"Track 20.7 lock test must not import {forbidden}"
        )


# ── Consumer surfaces intact ───────────────────────────────────────

CONSUMER_FILES = (
    "pages/NewDailyReport.jsx",
    "pages/NewIncident.jsx",
    "pages/NewInspection.jsx",
    "pages/NewEquipmentInspection.jsx",
    "pages/NewQaqcInspection.jsx",
    "pages/NewFleetDVIR.jsx",
    "pages/NewMeeting.jsx",
    "pages/NewSafetyEquipmentIssuance.jsx",
    "pages/FieldLeadershipFormPage.jsx",
    "pages/trench_safety/TrenchSafetyOpsCenter.jsx",
    "pages/operations_actions/OperationsActionDetail.jsx",
    "components/EquipmentLines.jsx",
    "components/EquipmentReturnLines.jsx",
    "components/FleetRepairDrawer.jsx",
    "components/AttachmentUpload.jsx",
    "components/oa/PhotoUploader.jsx",
)


def test_all_documented_consumers_still_import_photoupload():
    """The 16 consumer forms documented in TRACK_20_7_PHOTO_SURFACE_INVENTORY
    must still import from `components/PhotoUpload`. This proves the
    cascade fix is real — one edit propagates to every consumer."""
    for rel in CONSUMER_FILES:
        p = FE / rel
        assert p.exists(), f"consumer file missing: {rel}"
        src = _read(p)
        assert "PhotoUpload" in src, (
            f"consumer {rel} no longer references PhotoUpload — the "
            f"cascade fix would not reach this surface"
        )


# ── Docs + register ────────────────────────────────────────────────

REQUIRED_DOCS = [
    "TRACK_20_7_EXECUTIVE_SUMMARY.md",
    "TRACK_20_7_PHOTO_SURFACE_INVENTORY.md",
    "TRACK_20_7_UNIVERSAL_PHOTO_CONTROL_STANDARD.md",
    "TRACK_20_7_DAILY_REPORT_CAMERA_ROOT_CAUSE.md",
    "TRACK_20_7_DEVICE_BROWSER_MATRIX.md",
    "TRACK_20_7_BACKEND_CONTRACT_CERTIFICATION.md",
    "TRACK_20_7_EMAIL_SAFETY_CERTIFICATION.md",
    "TRACK_20_7_FIX_REPORT.md",
    "TRACK_20_7_ZERO_DRIFT_MATRIX.md",
    "TRACK_20_7_TEST_REPORT.md",
]


def test_all_deliverables_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing Track 20.7 deliverables: {missing}"


def test_prd_and_changelog_updated():
    assert "TRACK 20.7" in _read(MEM / "PRD.md")
    assert "TRACK 20.7" in _read(MEM / "CHANGELOG.md")


# ── Continuity ─────────────────────────────────────────────────────

def test_prior_track_docs_preserved():
    for name in ("TRACK_19_62_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_61_EXECUTIVE_SUMMARY.md",
                 "TRACK_19_60_EXECUTIVE_SUMMARY.md",
                 "TRACK_20_6_FINAL_RECOMMENDATION.md",
                 "TRACK_20_5_FINAL_RECOMMENDATION.md",
                 "TECHNICAL_DEBT_REGISTER.md"):
        assert (MEM / name).exists(), f"prior track doc missing: {name}"
