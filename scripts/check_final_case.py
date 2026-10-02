"""Validate public final capture provenance, hashes and chapter/caption relationships."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "docs/case/media/final/"


def validate_final(read):
    manifest = json.loads(read(PREFIX + "capture.json"))
    if (
        manifest["status"] != "FINAL_CURRENT_SNAPSHOT"
        or not manifest["passed"]
        or not manifest["synthetic"]
        or manifest["fake_clock"]
        or not manifest["source_equality_checked"]
        or manifest["project"] != "petlandfinalcase"
        or manifest["origin"] != "https://localhost:8445"
        or manifest["schema_revision"] != "0007_product_operations"
        or manifest["application_commit"] != "f3d70a2cce07d587351eadaa66864b7c1ae4444a"
        or manifest["errors"]
        or not 180 <= manifest["duration_seconds"] <= 300
    ):
        raise ValueError("Final capture origin/state is incompatible")
    script = read("apps/web/scripts/capture-final-portfolio.mjs")
    if hashlib.sha256(script).hexdigest() != manifest["capture_script_sha256"]:
        raise ValueError("Final capture automation differs from recorded source")
    for kind in ["video", "captions"]:
        item = manifest[kind]
        if Path(item["file"]).name != item["file"]:
            raise ValueError("Unsafe final media path")
        data = read(PREFIX + item["file"])
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("Final media hash differs")
        if kind == "video" and (
            not data.startswith(bytes.fromhex("1a45dfa3"))
            or len(data) != item["bytes"]
            or item["audio"] != "none"
        ):
            raise ValueError("Final WebM differs")
    chapters = manifest["chapters"]
    if len(chapters) != 19 or manifest["captions"]["cues"] != len(chapters):
        raise ValueError("Final journey chapters are incomplete")
    previous = -1
    for chapter in chapters:
        if not previous < chapter["at_seconds"] < manifest["duration_seconds"]:
            raise ValueError("Final chapter chronology differs")
        previous = chapter["at_seconds"]
    if json.loads(read(PREFIX + "chapters.json")) != {
        "duration_seconds": manifest["duration_seconds"],
        "chapters": chapters,
    }:
        raise ValueError("Standalone chapters differ from capture")
    subtitles = read(PREFIX + manifest["captions"]["file"]).decode("utf-8").replace("\r\n", "\n")
    if not subtitles.startswith("WEBVTT\n") or len(
        re.findall(r"^\d+\n.* --> .*", subtitles, re.MULTILINE)
    ) != len(chapters):
        raise ValueError("Final captions are incomplete")
    screenshots = manifest["screenshots"]
    required = {
        "final-home.webp",
        "final-customer-dashboard.webp",
        "final-booking.webp",
        "final-operations-dashboard.webp",
        "final-roster.webp",
        "final-capacity.webp",
        "final-attendance.webp",
        "final-management.webp",
    }
    if len(screenshots) != 22 or not required <= {s["image"] for s in screenshots}:
        raise ValueError("Final screenshot inventory is incomplete")
    for shot in screenshots:
        if Path(shot["image"]).name != shot["image"]:
            raise ValueError("Unsafe final screenshot path")
        data = read(PREFIX + shot["image"])
        if (
            hashlib.sha256(data).hexdigest() != shot["image_sha256"]
            or data[:4] != b"RIFF"
            or data[8:12] != b"WEBP"
            or shot["violations"]
            or not shot["reflow"]
            or not shot["pixels_preserved"]
            or shot["viewport"]["width"] not in {1280, 320}
        ):
            raise ValueError("Final screenshot hash/format/checks differ")
    for check in manifest["checks"]:
        if check.get("actual_mailpit") and check["external_delivery"]:
            raise ValueError("Local SMTP cannot establish external delivery")
    return manifest


if __name__ == "__main__":
    result = validate_final(lambda name: (ROOT / name).read_bytes())
    print(
        f"Final presentation verified: {len(result['screenshots'])} screenshots, 19 chapters; synthetic only."
    )
