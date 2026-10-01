FROM python:3.13-slim@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0
COPY --from=ghcr.io/astral-sh/uv:0.12.18@sha256:3adc3706091ce7c2fe595e669628caedd6d951551b92b258b7e7dbe06d9440bc /uv /bin/
WORKDIR /workspace
COPY apps/api/pyproject.toml apps/api/uv.lock ./apps/api/
RUN uv sync --project apps/api --frozen --no-install-project
COPY apps/api/src ./apps/api/src
COPY apps/api/migrations ./apps/api/migrations
COPY apps/api/alembic.ini ./apps/api/
COPY scripts/benchmark_api.py ./scripts/
RUN uv sync --project apps/api --frozen
CMD ["uv", "run", "--project", "apps/api", "--no-sync", "python", "scripts/benchmark_api.py", "--output", "/evidence/api-benchmark.json"]
