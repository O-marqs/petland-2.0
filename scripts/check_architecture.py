"""Enforce inward imports, including relative imports and future domain modules."""

import ast
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "apps/api/src"
LAYERS = {"domain", "application", "infrastructure", "presentation"}


def violations(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*.py"):
        parts = path.relative_to(root).with_suffix("").parts
        package = ".".join(parts[:-1])
        source = ".".join(parts)
        layer = next((p for p in parts if p in LAYERS), None)
        module = ".".join(parts[:3]) if len(parts) > 3 and parts[1] == "modules" else None
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    base = importlib.util.resolve_name("." * node.level + base, package)
                imported = [base, *(f"{base}.{alias.name}" for alias in node.names)]
            for target in imported:
                forbidden = False
                if layer in {"domain", "application"}:
                    if target.split(".")[0] not in sys.stdlib_module_names:
                        allowed = [f"{module}.domain", "petland.shared.domain"]
                        if layer == "application":
                            allowed += [f"{module}.application"]
                        forbidden = not any(
                            target == p or target.startswith(p + ".") for p in allowed
                        )
                elif layer == "presentation":
                    forbidden = ".infrastructure" in target or target.startswith(
                        ("petland.bootstrap", "petland.shared.database")
                    )
                elif layer == "infrastructure":
                    forbidden = ".presentation" in target or target.startswith("petland.bootstrap")
                if (
                    module
                    and target.startswith("petland.modules.")
                    and not target.startswith(module + ".")
                ):
                    forbidden = ".public" not in target
                if source.startswith("petland.shared.") and target.startswith(
                    ("petland.modules", "petland.bootstrap")
                ):
                    forbidden = True
                if forbidden:
                    errors.append(
                        f"{path.relative_to(root)}:{node.lineno}: forbidden import {target}"
                    )
    return sorted(set(errors))


if __name__ == "__main__":
    found = violations(ROOT)
    if found:
        raise SystemExit("\n".join(found))
    print("Architecture boundaries verified (absolute and relative imports).")
