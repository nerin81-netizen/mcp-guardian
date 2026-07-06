FROM python:3.11-slim

WORKDIR /app

# Install git since mcp-guardian queries git diff / commit status
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project configuration and sources
COPY pyproject.toml LICENSE README.md ./
COPY src/ ./src/

# Install dependencies and package itself
RUN pip install --no-cache-dir . uvicorn starlette sse-starlette

# Expose port for health checks and Streamable HTTP transport
EXPOSE 8000

# Run Streamable HTTP at /mcp by default on Kakao Cloud
CMD ["python", "-m", "mcp_guardian.server", "streamable-http"]
