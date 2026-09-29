# syntax=docker/dockerfile:1.7

# Stage 1: build the Vue application.
FROM node:20-alpine AS frontend-builder

WORKDIR /build/web
COPY web/package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --prefer-offline --no-audit --no-fund
COPY web/ ./
RUN npm run build

# Stage 2: run FastAPI and serve the built Vue application.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi "uvicorn[standard]"

COPY main.py ./
COPY --from=frontend-builder /build/web/dist ./web/dist

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
