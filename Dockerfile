# syntax=docker/dockerfile:1.7

# Stage 1: build the Vue application.
FROM node:20-alpine AS frontend-builder

WORKDIR /build/web
COPY web/package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --prefer-offline --no-audit --no-fund
COPY web/ ./
RUN npm run build

# Stage 2: install locked Python dependencies and run FastAPI.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY main.py ./
COPY database.py ./
COPY --from=frontend-builder /build/web/dist ./web/dist

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
