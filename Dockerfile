FROM python:3.13-slim

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only (no dev)
RUN uv sync --no-dev --frozen

# Put the virtual environment on PATH so uvicorn is directly accessible
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code and data
COPY app/ app/
COPY data/ data/
COPY widget/ widget/

# Railway/Render inject PORT; default to 8000
ENV PORT=8000

EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
