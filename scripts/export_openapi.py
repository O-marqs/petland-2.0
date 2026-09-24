"""Export real routes only, without opening a database connection."""

import argparse
import json
from pathlib import Path

from petland.bootstrap.app import create_app
from petland.bootstrap.settings import Settings

parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
settings = Settings(
    _env_file=None,
    app_env="test",
    database_url="postgresql+psycopg://unused@localhost/unused",
)
schema = create_app(settings).openapi()
target = Path(__file__).resolve().parents[1] / "packages/api-contract/openapi.json"
output = json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
if args.check:
    if not target.exists() or target.read_text(encoding="utf-8") != output:
        raise SystemExit("OpenAPI is stale. Run pnpm contracts:generate.")
    print("OpenAPI matches the running application factory.")
else:
    target.write_text(output, encoding="utf-8", newline="\n")
