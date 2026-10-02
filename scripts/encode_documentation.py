"""Lossless WebP encoding of real documentation screenshots; requires Pillow."""

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".local/docs-capture"
TARGET = ROOT / "docs/ux/media/current"


def main():
    manifest = json.loads((SOURCE / "capture-raw.json").read_text())
    if not manifest["passed"] or not manifest["synthetic"] or manifest["project"] != "petlanddocs":
        raise SystemExit("Only verified synthetic documentation screenshots may be encoded")
    TARGET.mkdir(parents=True, exist_ok=True)
    for check in manifest["checks"]:
        if "png" not in check:
            continue
        name = check["png"]
        if Path(name).name != name:
            raise SystemExit("Unsafe screenshot path")
        source = SOURCE / "screenshots" / name
        if hashlib.sha256(source.read_bytes()).hexdigest() != check["sha256"]:
            raise SystemExit("Source screenshot hash differs")
        with Image.open(source) as original:
            target = TARGET / (Path(name).stem + ".webp")
            original.save(target, "WEBP", lossless=True, method=6)
            with Image.open(target) as encoded:
                if original.convert("RGBA").tobytes() != encoded.convert("RGBA").tobytes():
                    raise SystemExit("Lossless encoding changed screenshot pixels")
            check["image"] = target.name
            check["image_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
            check["width"], check["height"] = original.size
    manifest["conversion"] = (
        "Pillow lossless WebP; decoded RGBA pixels verified equal to original PNG"
    )
    (TARGET / "capture.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("Eight real screenshots encoded losslessly; provenance preserved.")


if __name__ == "__main__":
    main()
