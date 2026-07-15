from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path

from PIL import Image
import pillow_heif


pillow_heif.register_heif_opener()


ROOT = Path("/app/tmp_photo_fixture")
OUT = ROOT / "dr03_nine_photo_fixture.json"


def _jpg_data_url(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    img.thumbnail((1280, 1280))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    base = [p for p in sorted(ROOT.iterdir()) if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    photos = [{"name": p.name, "data_url": _jpg_data_url(p)} for p in base]

    zip_path = ROOT / "y6ei59r7_Photos_%283%29.zip"
    extract = ROOT / "extracted_fixture"
    extract.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract)
    heic = extract / "IMG_5050.heic"
    if heic.exists():
        photos.append({"name": heic.name, "data_url": _jpg_data_url(heic)})

    OUT.write_text(__import__("json").dumps({"count": len(photos), "photos": photos}, indent=2))
    print(OUT)
    print(len(photos))


if __name__ == "__main__":
    main()