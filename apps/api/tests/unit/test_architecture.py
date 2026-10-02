import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from check_architecture import ROOT, violations  # noqa: E402


def test_current_boundaries():
    assert violations(ROOT) == []


def test_architecture_guard_rejects_real_forbidden_edges(tmp_path):
    samples = {
        "domain/model.py": "from sqlalchemy import Column\n",
        "application/use_case.py": "from ..infrastructure import repository\n",
        "presentation/http/router.py": "from ...infrastructure.repository import Repository\n",
        "infrastructure/repository.py": "from petland.modules.pets.infrastructure import private\n",
    }
    for relative, source in samples.items():
        path = tmp_path / "petland/modules/identity" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    found = violations(tmp_path)
    assert all(
        any(
            relative.replace("/", "\\") in violation or relative in violation for violation in found
        )
        for relative in samples
    )
