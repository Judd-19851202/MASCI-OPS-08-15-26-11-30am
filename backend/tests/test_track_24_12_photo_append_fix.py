"""TRACK 24.12 Phase A1 · Photo append regression lock.

Reproduces the "gallery reopens replaces prior photos" P0 by
inspecting the compiled PhotoUpload.jsx source. The fix contract
is:

  1. A `photosRef` is initialised from the incoming `photos` prop
     and kept current via `useEffect`.
  2. `handleFiles` reads `photosRef.current` (never the stale
     `photos` closure) as the base for the new batch.
  3. `photosRef.current` is advanced in-flight so a rapid second
     batch picked mid-flight appends instead of overwriting.
  4. `removeAt` also reads from the ref so it can't resurrect a
     photo a mid-flight batch just deleted.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHOTO_UPLOAD = ROOT.parent / "frontend" / "src" / "components" / "PhotoUpload.jsx"


def test_photo_upload_uses_ref_mirror_for_append():
    src = PHOTO_UPLOAD.read_text()
    for marker in [
        "photosRef = useRef(photos)",
        "photosRef.current = photos",
        "photosRef.current.length",   # startLen from ref
        "[...photosRef.current]",     # base list from ref
        "photosRef.current = [...next]",  # advance mid-flight
    ]:
        assert marker in src, (
            f"[Track 24.12 A1] PhotoUpload.jsx missing `{marker}` — "
            f"stale-closure regression WILL recur: users pick batch A "
            f"(3 photos), reopen picker mid-render, pick batch B "
            f"(2 photos), batch B overwrites batch A."
        )


def test_photo_upload_handle_files_reads_from_ref_not_prop():
    src = PHOTO_UPLOAD.read_text()
    # The old bug was `const next = [...photos];`. Ensure the fix
    # replaced it with the ref-based version and no residue remains.
    hf = src[src.find("const handleFiles"): src.find("const handleFiles") + 4000]
    assert "const next = [...photosRef.current]" in hf
    assert "const next = [...photos];" not in hf, (
        "[Track 24.12 A1] handleFiles still reads from the stale "
        "`photos` prop closure — the append fix regressed."
    )


def test_photo_upload_remove_at_uses_ref():
    src = PHOTO_UPLOAD.read_text()
    ra = src[src.find("const removeAt"): src.find("const removeAt") + 400]
    assert "photosRef.current" in ra, (
        "[Track 24.12 A1] removeAt must read from photosRef so it "
        "cannot resurrect a photo a mid-flight batch just deleted."
    )


def test_photo_upload_startlen_used_for_added_toast():
    src = PHOTO_UPLOAD.read_text()
    assert "startLen" in src, (
        "The `photos added` toast count must be measured against the "
        "ref-snapshot at start-of-batch (`startLen`), not the prop, "
        "otherwise a batch that arrives mid-flight prints a wrong count."
    )


def test_sections_pass_photos_prop_not_value():
    """TRACK 24.12 Phase A1 · wiring contract lock.

    PhotoUpload's controlled prop is `photos`, not `value`. Every
    call site in daily-report-v3/sections.jsx must use `photos={...}`.
    An earlier regression passed `value={photos}` which was
    silently ignored → the component always saw photos=[] → no
    thumbs rendered AND every batch overwrote parent state (the
    exact P0 the ref fix was meant to close, but rendered dead
    code by the wiring bug)."""
    sections = ROOT.parent / "frontend" / "src" / "components" / "daily-report-v3" / "sections.jsx"
    src = sections.read_text()
    import re
    # Every <PhotoUpload ...> must include a photos={...} prop.
    for match in re.finditer(r"<PhotoUpload\b([^>]*?)/>", src, re.DOTALL):
        block = match.group(1)
        assert "photos=" in block, (
            f"[Track 24.12 A1] a <PhotoUpload/> in sections.jsx does "
            f"NOT pass the `photos` prop. Full match: <PhotoUpload{block[:200]}/>."
        )
        assert "value=" not in block, (
            f"[Track 24.12 A1] a <PhotoUpload/> in sections.jsx is "
            f"still using the DEAD `value=` prop. Rename to `photos=`. "
            f"Full match: <PhotoUpload{block[:200]}/>"
        )
