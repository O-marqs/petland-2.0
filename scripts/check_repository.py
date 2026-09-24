"""Check active tracked files; historical baseline is intentionally preserved."""

import re
import subprocess
from pathlib import Path

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
patterns = [
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"gh[pousr]_[A-Za-z0-9]{36,}",
    r"AKIA[0-9A-Z]{16}",
]
for name in set(files):
    path = root / name
    if not name or not path.is_file():
        continue
    if (
        path.name == ".env"
        or ".venv" in path.parts
        or "node_modules" in path.parts
        or "__pycache__" in path.parts
    ):
        errors.append(f"Forbidden versioned artifact: {name}")
    if path.suffix not in {".png", ".pdf", ".woff2"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(re.search(pattern, text) for pattern in patterns):
            errors.append(f"Possible secret in {name} (value withheld)")
if errors:
    raise SystemExit("\n".join(errors))
print("Active source scan passed. This is not a historical credential audit.")
