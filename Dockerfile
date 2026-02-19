FROM python:3.12-slim

WORKDIR /app

# Install production dependencies directly into system Python (no venv)
COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic

# Copy application code and data
COPY app/ app/
COPY data/ data/
COPY widget/ widget/

# Railway/Render inject PORT; default to 8000
ENV PORT=8000

EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
