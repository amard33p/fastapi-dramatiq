FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv, a fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/

# Create a virtual environment location (uv will create it)
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Set the Python path so imports from /app work correctly
ENV PYTHONPATH=/app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Copy application code
COPY app/ ./app/

# Install Python dependencies system-wide with uv
RUN uv sync --no-cache-dir