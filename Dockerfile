FROM python:3.11

# Install Node.js 18
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl \
  && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
  && apt-get install -y --no-install-recommends nodejs \
  && rm -rf /var/lib/apt/lists/*

# Copy uv from the official uv image
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Copy dependency descriptor files first to leverage cache
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml backend/uv.lock ./backend/

# Install dependencies (Node + Python)
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && uv sync --frozen

# Copy project source code
COPY . .

# Build frontend for production
RUN cd frontend && npm run build

# Railway assigns PORT dynamically; default to 5001
ENV FLASK_PORT=${PORT:-5001}
ENV FLASK_DEBUG=false

EXPOSE ${PORT:-5001}

# Run Flask backend (serves both API and built frontend)
CMD cd backend && uv run python run.py
