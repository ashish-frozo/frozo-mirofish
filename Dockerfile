FROM python:3.11-slim

# Install Node.js 18 and system dependencies
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl gnupg libmagic1 \
  && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y --no-install-recommends nodejs \
  && rm -rf /var/lib/apt/lists/*

# Copy uv from the official uv image
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Copy dependency descriptor files first to leverage cache
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml backend/uv.lock ./backend/

# Install CPU-only PyTorch first (avoids ~3GB CUDA downloads)
RUN cd backend && uv venv && uv pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && uv sync --frozen

# Copy project source code
COPY . .

# Build frontend for production
RUN cd frontend && npm run build

# Production environment defaults
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Railway assigns PORT dynamically; default to 5001
ENV FLASK_DEBUG=false
ENV FLASK_PORT=5001

WORKDIR /app/backend

# Create non-root user (after all build steps that need root)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE ${PORT:-5001}

# Run Flask backend directly from venv (avoids uv run re-syncing)
CMD ["/app/backend/.venv/bin/python", "run.py"]
