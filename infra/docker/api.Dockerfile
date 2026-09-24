FROM python:3.13-slim@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0
COPY --from=ghcr.io/astral-sh/uv:0.12.18@sha256:3adc3706091ce7c2fe595e669628caedd6d951551b92b258b7e7dbe06d9440bc /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY apps/api/src ./src
COPY apps/api/alembic.ini ./
COPY apps/api/migrations ./migrations
RUN uv sync --frozen --no-dev && useradd --uid 10001 --create-home petland && chown -R petland:petland /app
USER petland
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "petland.bootstrap.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
