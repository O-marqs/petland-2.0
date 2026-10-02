"""Validate and package a review candidate locally; never create a tag, deploy or publish."""

import argparse
import hashlib
import json
import re
import subprocess
import tomllib
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from repository_hygiene import check_public_file, check_public_path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "docs/release/candidate.json"


def digest(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def validate(read):
    candidate = json.loads(read(CONFIG))
    version = candidate["version"]
    if not re.fullmatch(r"3\.0\.0-rc\.[1-9][0-9]*", version):
        raise ValueError("Only a review candidate is allowed")
    if candidate["production_ready"] or candidate["stable_release_published"]:
        raise ValueError("This tool cannot grant acceptance or publication")
    for name in ["package.json", "apps/web/package.json", "packages/api-contract/package.json"]:
        if json.loads(read(name))["version"] != version:
            raise ValueError("Package versions disagree")
    if (
        tomllib.loads(read("apps/api/pyproject.toml").decode())["project"]["version"]
        != candidate["python_version"]
    ):
        raise ValueError("Python candidate version disagrees")
    if json.loads(read("packages/api-contract/openapi.json"))["info"]["version"] != version:
        raise ValueError("OpenAPI version disagrees")
    factory = read("apps/api/src/petland/bootstrap/app.py").decode()
    if f'version="{version}"' not in factory:
        raise ValueError("Application version disagrees")
    schema = read("apps/api/src/petland/shared/database.py").decode()
    if f'SCHEMA_REVISION = "{candidate["schema_revision"]}"' not in schema:
        raise ValueError("Schema revision disagrees")
    for name in candidate["assets"]:
        if not read(name):
            raise ValueError("Empty required candidate asset")
    if not read("docs/case/media/petland-3.0-demo.webm").startswith(bytes.fromhex("1a45dfa3")):
        raise ValueError("Invalid WebM container")
    capture = json.loads(read("docs/case/media/capture.json"))
    if (
        not capture["passed"]
        or not capture["synthetic"]
        or capture["fake_clock"]
        or capture["version"] != version
        or not 180 <= capture["duration_seconds"] <= 300
    ):
        raise ValueError("Three-journey recording evidence is incompatible")
    return candidate


def check():
    candidate = validate(lambda name: (ROOT / name).read_bytes())
    print(f"Candidate {candidate['version']} consistent; media present, acceptance still pending.")
    return candidate


def safe_names(names):
    if len(names) != len(set(names)):
        raise ValueError("Duplicate candidate archive entries")
    for name in names:
        check_public_path(name)


def verify(folder: Path):
    manifest = json.loads((folder / "manifest.json").read_text())
    check_public_path(manifest["archive"])
    if Path(manifest["archive"]).name != manifest["archive"]:
        raise ValueError("Invalid archive name")
    archive = folder / manifest["archive"]
    if digest(archive) != manifest["archive_sha256"]:
        raise ValueError("Candidate archive checksum mismatch")
    with zipfile.ZipFile(archive) as file:
        if not re.fullmatch(r"[0-9a-f]{40}", manifest["commit"]) or file.comment != manifest[
            "commit"
        ].encode("ascii"):
            raise ValueError("Archive commit disagrees with manifest")
        safe_names(file.namelist())
        names = [name for name in file.namelist() if not name.endswith("/")]
        if set(names) != set(manifest["files"]):
            raise ValueError("Candidate file inventory mismatch")
        for name in names:
            data = file.read(name)
            check_public_file(name, data)
            if hashlib.sha256(data).hexdigest() != manifest["files"][name]:
                raise ValueError("Candidate asset checksum mismatch")
        candidate = validate(file.read)
        if candidate["version"] != manifest["version"]:
            raise ValueError("Archive candidate version mismatch")
    print(
        f"Local candidate archive verified: {len(names)} files; no acceptance or publication granted."
    )


def bundle():
    candidate = check()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT):
        raise ValueError("Commit the reviewed files before bundling")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    folder = ROOT / ".local/release" / candidate["version"] / commit
    if folder.exists():
        verify(folder)
        return
    tracked = (
        subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=ROOT)
        .decode()
        .splitlines()
    )
    safe_names(tracked)
    folder.mkdir(parents=True)
    archive = folder / f"petland-{candidate['version']}-{commit[:12]}.zip"
    subprocess.run(
        ["git", "archive", "--format=zip", "--output", str(archive), "HEAD"], cwd=ROOT, check=True
    )
    with zipfile.ZipFile(archive) as file:
        safe_names(file.namelist())
        files = {}
        for name in file.namelist():
            if name.endswith("/"):
                continue
            data = file.read(name)
            check_public_file(name, data)
            files[name] = hashlib.sha256(data).hexdigest()
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "version": candidate["version"],
                "commit": commit,
                "created_at": datetime.now(UTC).isoformat(),
                "archive": archive.name,
                "archive_sha256": digest(archive),
                "files": files,
                "gates": candidate["gates"],
                "publication": "not_performed",
                "includes_secrets_or_demo_database": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    verify(folder)
    print(folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "bundle", "verify"])
    parser.add_argument("--folder", type=Path)
    args = parser.parse_args()
    if args.command == "check":
        check()
    elif args.command == "bundle":
        bundle()
    elif args.folder:
        verify(args.folder.resolve())
    else:
        parser.error("verify requires --folder from bundle output")
