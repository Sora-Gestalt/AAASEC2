# DAY 3 — read 04-docker.md before touching this file.
FROM python:3.12-slim

# uv, copied straight from the official distroless image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Dependency layer FIRST: this layer is rebuilt only when pyproject/lock
# change, not on every code edit. This ordering is the entire secret of
# fast Docker rebuilds — reorder it and watch your build times explode.
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev

# Code layer LAST (changes most often)
COPY src/ src/
COPY skills/ skills/

EXPOSE 8000
CMD ["uv", "run", "--no-dev", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
