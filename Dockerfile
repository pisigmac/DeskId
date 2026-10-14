# ==============================================================================
# Stage 1: Build Vue 3 Frontend Single Page Application with pnpm
# ==============================================================================
FROM node:22-alpine AS frontend-builder
WORKDIR /build

# Enable corepack for pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy dependency manifests and install packages
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml frontend/.npmrc ./
RUN pnpm install --frozen-lockfile

# Copy frontend source and build production assets
COPY frontend/ ./
RUN pnpm run build

# ==============================================================================
# Stage 2: Runtime Container (Python 3.12 + FastAPI + Static SPA)
# ==============================================================================
FROM python:3.12-slim
WORKDIR /app

# Copy application files and build artifacts
COPY pyproject.toml README.md ./
COPY src ./src
COPY static ./static
COPY migrations ./migrations
COPY --from=frontend-builder /build/dist ./frontend/dist

# Install python package with PostgreSQL driver
RUN pip install --no-cache-dir -e ".[postgres]"

ENV AUTH_HOST=0.0.0.0
ENV AUTH_PORT=8090
EXPOSE 8090

CMD ["deskid"]
