"""Publish only verified synthetic capture: lossless screenshots, WebM, VTT and provenance.

Requires Pillow and a local FFmpeg executable, without adding application dependencies.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".local/final-case/capture"
TARGET = ROOT / "docs/case/media/final"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    return f"{milliseconds // 3600000:02}:{milliseconds // 60000 % 60:02}:{milliseconds // 1000 % 60:02}.{milliseconds % 1000:03}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads((SOURCE / "capture-raw.json").read_text(encoding="utf-8"))
    script = ROOT / "apps/web/scripts/capture-final-portfolio.mjs"
    if (
        not manifest["passed"]
        or not manifest["synthetic"]
        or manifest["fake_clock"]
        or manifest["project"] != "petlandfinalcase"
        or manifest["capture_script_sha256"] != digest(script)
        or manifest["errors"]
    ):
        raise SystemExit("Only verified synthetic final capture with matching source is allowed")
    video = SOURCE / "petland-final-demo.webm"
    probe = subprocess.run(
        [str(args.ffmpeg), "-hide_banner", "-i", str(video)],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stderr
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", probe)
    if not match or "Audio:" in probe or "1280x900" not in probe or "Video: vp8" not in probe:
        raise SystemExit("Final media duration/codec/viewport/audio could not be verified")
    h, m, s = map(float, match.groups())
    duration = h * 3600 + m * 60 + s
    if not 180 <= duration <= 300 or abs(duration - manifest["duration_seconds"]) >= 1:
        raise SystemExit("Container duration disagrees with continuous recording")
    TARGET.mkdir(parents=True, exist_ok=True)
    screenshots = []
    for check in manifest["checks"]:
        name = check.get("screenshot")
        if not name:
            continue
        if Path(name).name != name or not name.startswith("final-"):
            raise SystemExit("Unsafe screenshot path")
        if check["violations"] or not check["reflow"]:
            raise SystemExit("Screenshot did not pass declared checks")
        source = SOURCE / name
        with Image.open(source) as original:
            target = TARGET / (Path(name).stem + ".webp")
            original.save(target, "WEBP", lossless=True, method=6)
            with Image.open(target) as encoded:
                if original.convert("RGBA").tobytes() != encoded.convert("RGBA").tobytes():
                    raise SystemExit("Lossless encoding changed screenshot pixels")
            screenshots.append(
                {
                    **check,
                    "png_sha256": digest(source),
                    "image": target.name,
                    "image_sha256": digest(target),
                    "width": original.width,
                    "height": original.height,
                    "pixels_preserved": True,
                }
            )
    shutil.copyfile(video, TARGET / video.name)
    chapters = manifest["chapters"]
    cues = ["WEBVTT", ""]
    transcript = [
        "# PetLand 3.0 — transcrição final",
        "",
        "Vídeo contínuo sem áudio. Legendas descritivas em português; os tempos vêm da gravação real.",
        "Dados fictícios, ambiente HTTPS local e Mailpit sem entrega externa. Conta/contato preparados; serviço de cinco minutos, relógio real.",
        "",
        "[Player final](index.html#demo) · [Roteiro](presentation-script.md) · [Proveniência](media/final/capture.json).",
        "",
    ]
    for i, chapter in enumerate(chapters):
        begin = chapter["at_seconds"] if i else 0
        end = chapters[i + 1]["at_seconds"] - 0.001 if i + 1 < len(chapters) else duration
        if begin >= end or end > duration:
            raise SystemExit("Invalid chronological chapter")
        chapter["screenshot"] = Path(chapter["screenshot"]).stem + ".webp"
        cues.extend(
            [
                str(i + 1),
                f"{timestamp(begin)} --> {timestamp(end)}",
                chapter["caption"],
                "",
            ]
        )
        transcript.extend(
            [
                f"## {timestamp(chapter['at_seconds'])} — {chapter['title']}",
                "",
                chapter["caption"],
                "",
            ]
        )
    subtitles = TARGET / "petland-final-demo.vtt"
    subtitles.write_text("\n".join(cues), encoding="utf-8", newline="\n")
    manifest["recording_wall_seconds"] = manifest["duration_seconds"]
    manifest["duration_seconds"] = duration
    manifest["version"] = "3.0.0-rc.1"
    manifest["screenshots"] = screenshots
    manifest["video"] = {
        "file": video.name,
        "sha256": digest(TARGET / video.name),
        "bytes": video.stat().st_size,
        "container": "WebM",
        "codec": "VP8",
        "fps": 25,
        "audio": "none",
        "editing": "none; continuous Playwright viewport recording, copied byte-for-byte",
        "duration_verified": "FFmpeg container metadata; independently checked in browser player",
    }
    manifest["captions"] = {
        "file": subtitles.name,
        "sha256": digest(subtitles),
        "cues": len(chapters),
    }
    manifest["conversion"] = "Pillow lossless WebP; decoded RGBA pixels equal to original PNG"
    manifest["limitations"] = [
        "No human product/screen-reader acceptance or external SMTP/production deployment",
        "First attempt failed application reflow at 320px: long synthetic pet name expanded the customer detail to 334px. Product source unchanged; final fixture uses Nala. Long-name layout remains a known limitation.",
    ]
    (TARGET / "capture.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (ROOT / "docs/case/final-transcript.md").write_text("\n".join(transcript), encoding="utf-8")
    (TARGET / "chapters.json").write_text(
        json.dumps(
            {"duration_seconds": duration, "chapters": chapters},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Final capture encoded: {len(screenshots)} lossless screenshots; {duration}s continuous video."
    )


if __name__ == "__main__":
    main()
