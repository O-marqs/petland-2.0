"""Shared public-source/archive guards; report paths, never secret values."""

import re
from pathlib import PurePosixPath

PRIVATE_PARTS = {
    ".git",
    ".local",
    ".tools",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "dist",
    "coverage",
    "htmlcov",
    "playwright-report",
    "test-results",
}
PRIVATE_SUFFIXES = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".dump",
    ".backup",
    ".plbackup",
    ".log",
    ".tsbuildinfo",
    ".pyc",
    ".pyo",
}
SECRET_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
]


def check_public_path(name: str) -> None:
    path = PurePosixPath(name)
    parts = tuple(part.casefold() for part in path.parts)
    if (
        not name
        or "\\" in name
        or ":" in name
        or any(ord(char) < 32 for char in name)
        or path.is_absolute()
        or ".." in parts
        or PRIVATE_PARTS.intersection(parts)
        or any(part.startswith(".local-") for part in parts)
        or any(part.startswith(".env") and part != ".env.example" for part in parts)
        or path.suffix.casefold() in PRIVATE_SUFFIXES
        or path.name.casefold() in {".coverage", "thumbs.db", ".ds_store"}
        or name.casefold().endswith((".sql.gz", ".sql.zip", ".sql.bz2"))
    ):
        raise ValueError(f"Private or unsafe public path: {name}")


def check_public_file(name: str, content: bytes) -> None:
    check_public_path(name)
    if any(pattern.search(content) for pattern in SECRET_PATTERNS):
        raise ValueError(f"Possible secret in {name} (value withheld)")
