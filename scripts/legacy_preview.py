"""Render two historical templates offline; never import or run the legacy application."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "3cc3f898cde896b80fed587bf8c06f4aa46742f6"
OUTPUT = ROOT / ".local/p08/legacy"


def historical(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    evidence = []
    for label, name in [("login", "telalogin_cliente.html"), ("booking", "telagendamento.html")]:
        original = historical("templates/" + name)
        rendered = original.decode("utf-8")
        # Deliberate, documented substitutions in these two fixed templates only.
        rendered = re.sub(r"{% with messages.*?{% endwith %}", "", rendered, flags=re.S)
        for variable, body in [
            ("pet", '<option value="synthetic-pet">Luna demo</option>'),
            ("servico", '<option value="synthetic-service">Banho demo</option>'),
        ]:
            rendered = re.sub(
                r"{% for " + variable + r" in .*?{% endfor %}", body, rendered, flags=re.S
            )
        rendered = rendered.replace("{{ today_date }}", "2026-10-01")
        for asset in re.findall(r"url_for\('static', filename='([^']+)'\)", rendered):
            if asset != "images/logo.jpeg.jpeg":
                raise ValueError("Unreviewed historical asset")
            destination = OUTPUT / "static" / asset
            destination.parent.mkdir(parents=True, exist_ok=True)
            data = historical("static/" + asset)
            destination.write_bytes(data)
            rendered = rendered.replace(
                "{{ url_for('static', filename='" + asset + "') }}", "/static/" + asset
            )
            evidence.append(
                {"source": "static/" + asset, "sha256": hashlib.sha256(data).hexdigest()}
            )
        rendered = re.sub(r"{{\s*url_for\([^}]+\)\s*}}", "#disabled", rendered)
        rendered = re.sub(r"<script\b.*?</script>", "", rendered, flags=re.S | re.I)
        rendered = re.sub(r"<link[^>]+(?:https?:)?//[^>]+>", "", rendered, flags=re.I)
        rendered = re.sub(r'\s+on\w+="[^"]*"', "", rendered)
        rendered = rendered.replace("<form ", '<form onsubmit="return false" ')
        if "{{" in rendered or "{%" in rendered:
            raise ValueError("Unreviewed historical template expression")
        notice = (
            '<aside style="position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#fff;'
            'color:#222;padding:8px;text-align:center;font:12px Arial;border-top:1px solid #aaa">'
            "2.0 · Template isolado do commit 3cc3f89 · Dados fictícios · Sem backend/SQL"
            "</aside>"
        )
        rendered = rendered.replace("</body>", notice + "</body>")
        (OUTPUT / f"{label}.html").write_text(rendered, encoding="utf-8")
        evidence.append(
            {"source": "templates/" + name, "sha256": hashlib.sha256(original).hexdigest()}
        )
    (OUTPUT / "provenance.json").write_text(
        json.dumps(
            {
                "commit": BASELINE,
                "mode": "isolated historical HTML, not a functional legacy flow",
                "adaptations": [
                    "fixed synthetic options/date and disabled links/forms",
                    "scripts and external stylesheets removed; system font fallback",
                    "empty flash messages and visible provenance label",
                    "only the historical static image is copied",
                ],
                "mysql_accessed": False,
                "legacy_application_executed": False,
                "sources": evidence,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Historical templates rendered in .local/p08/legacy; no legacy backend or database.")


if __name__ == "__main__":
    main()
