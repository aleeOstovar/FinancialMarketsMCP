# Stage 1: Builder (Compiles dependencies)
FROM python:3.12-slim as builder

WORKDIR /app

# Install system build tools (needed for some python packages)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Runtime (Minimal image)
FROM python:3.12-slim

WORKDIR /app

# Create a non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp mcp

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache /wheels/*

# Copy Application Code
# We copy the 'src' folder into /app/src
COPY src /app/src
COPY deployments/env /app/deployments/env

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Change ownership to non-root user
RUN chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Expose the port
EXPOSE 8000

# Healthcheck (Docker will auto-restart if this fails)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start the server
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]