"""Check active tracked files; historical baseline is intentionally preserved."""

import subprocess
from pathlib import Path

from repository_hygiene import check_public_file

root = Path(__file__).resolve().parents[1]
files = (
    subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
    )
    .decode()
    .split("\0")
)
errors = []
for name in set(files):
    path = root / name
    if not name or not path.is_file():
        continue
    try:
        check_public_file(name, path.read_bytes())
    except ValueError as exc:
        errors.append(str(exc))
if errors:
    raise SystemExit("\n".join(errors))
print("Active source scan passed. This is not a historical credential audit.")
