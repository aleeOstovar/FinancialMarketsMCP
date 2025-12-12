# Stage 1: Builder (Compiles dependencies via pyproject.toml)
FROM python:3.12-slim as builder

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy packaging files
COPY pyproject.toml .

# Generate wheels from pyproject.toml dependencies
# We use '.' to refer to the current directory (pyproject.toml)
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels .


# Stage 2: Runtime (Production Image)
FROM python:3.12-slim

WORKDIR /app

# 1. Install curl for Healthcheck (Critical Fix)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 2. Create non-root user
RUN groupadd -r mcp && useradd -r -g mcp mcp

# 3. Copy artifacts from Builder
COPY --from=builder /app/wheels /wheels

# 4. Install dependencies from wheels
RUN pip install --no-cache /wheels/*

# 5. Copy Application Source Code
COPY src /app/src
COPY deployments/env /app/deployments/env

# 6. Environment Config
# We add /app to PYTHONPATH so 'src.app.main' resolves correctly
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 7. Security: Permissions
RUN chown -R mcp:mcp /app

# 8. Switch User
USER mcp

# 9. Expose Port
EXPOSE 8000

# 10. Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 11. Start Command
# Using the module syntax standardizes the import path
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]