"""Validate repository Markdown links, current diagram XML and screenshot provenance."""

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

from render_architecture import DEST, PAGES, ROOT, render


def anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    result = set(re.findall(r'(?:id|name)=["\']([^"\']+)', text))
    occurrences: dict[str, int] = {}
    # Ignore code fences before deriving GitHub-style heading anchors.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE):
        heading = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", heading)
        slug = re.sub(r"[^\w\- ]", "", heading.lower(), flags=re.UNICODE).replace(" ", "-")
        count = occurrences.get(slug, 0)
        occurrences[slug] = count + 1
        result.add(slug + (f"-{count}" if count else ""))
    return result


def validate() -> list[str]:
    errors = []
    links = 0
    for path in [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        *sorted((ROOT / "docs").rglob("*.md")),
    ]:
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        for match in re.finditer(r"!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)", text):
            target = unquote(match[1].strip("<>"))
            if re.match(r"^[a-zA-Z]+:", target):
                continue
            name, _, fragment = target.partition("#")
            file = (path.parent / name).resolve() if name else path
            links += 1
            if not file.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing {target}")
            elif fragment and file.suffix in {".md", ".html"} and fragment not in anchors(file):
                errors.append(f"{path.relative_to(ROOT)}: missing anchor {target}")
    originals = {
        "docs/product/PetLand_3.0_Plano_Consolidado.md": "53b8496a4b1aa50ef2a6a26b86975c03c31729120b0521210148b44f0028f2c0",
        "docs/ux/PetLand_3.0_Caderno_UX.pdf": "7b9a78562b8d23e20c5979655e2a947a88700a151348fce418e89fff93d0f3b8",
    }
    for name, expected in originals.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            errors.append(f"Discovery original changed: {name}")
    doc = ET.parse(DEST / "PetLand_3.0_Architecture.drawio").getroot()
    if [d.attrib.get("name") for d in doc] != [p[0] for p in PAGES]:
        errors.append("Draw.io pages disagree with current model")
    for page in doc:
        cells = page.findall("./mxGraphModel/root/mxCell")
        ids = {c.attrib["id"] for c in cells}
        if len(ids) != len(cells):
            errors.append(f"Duplicate Draw.io IDs: {page.attrib['name']}")
        for cell in cells:
            if (
                cell.attrib.get("edge")
                and not {cell.attrib["source"], cell.attrib["target"]} <= ids
            ):
                errors.append("Draw.io edge refers to missing node")
    for name, expected in render().items():
        if (DEST / name).read_bytes() != expected:
            errors.append(f"Non-deterministic / outdated diagram: {name}")
        if name.endswith(".svg"):
            svg = ET.parse(DEST / name).getroot()
            if svg.find("{http://www.w3.org/2000/svg}title") is None:
                errors.append(f"SVG has no accessible title: {name}")
    media = ROOT / "docs/ux/media/current"
    capture = json.loads((media / "capture.json").read_text())
    if (
        not capture["passed"]
        or not capture["synthetic"]
        or capture["fake_clock"]
        or capture["javascript_errors"]
    ):
        errors.append("Current capture evidence is incompatible")
    images = [c for c in capture["checks"] if "image" in c]
    if len(images) != 8 or len(capture["checks"]) != 16:
        errors.append("Expected eight current screenshots and sixteen desktop/mobile checkpoints")
    for shot in images:
        path = media / shot["image"]
        data = path.read_bytes()
        if (
            hashlib.sha256(data).hexdigest() != shot["image_sha256"]
            or data[:4] != b"RIFF"
            or data[8:12] != b"WEBP"
        ):
            errors.append(f"Screenshot checksum / format differs: {shot['image']}")
        if shot["violations"] or not shot["reflow"] or shot["width"] < 320 or shot["height"] < 1:
            errors.append(f"Screenshot verification differs: {shot['image']}")
    print(
        f"Inspected {links} local links/anchors, discovery hashes, seven editable pages/SVGs and eight screenshot hashes."
    )
    return errors


if __name__ == "__main__":
    found = validate()
    if found:
        raise SystemExit("\n".join(found))
    from check_final_case import validate_final

    validate_final(lambda name: (ROOT / name).read_bytes())
    print(
        "Documentation references and provenance verified. Human product acceptance remains pending."
    )
