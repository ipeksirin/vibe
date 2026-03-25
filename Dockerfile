# ── Stage 1: Build React frontend ──────────────────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python backend + built frontend ────────────────────────────────
FROM python:3.11-slim
WORKDIR /app/backend

COPY backend/requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y gcc python3-dev && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY backend/ .
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
