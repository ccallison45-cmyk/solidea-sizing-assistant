# Local Development

## Prerequisites

- **Python 3.12+**: [Download](https://www.python.org/downloads/) or install via your system package manager
- **uv**: Install with `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or `pip install uv` (Windows)
- **Git**: For version control

Optional:
- **n8n**: Only needed if developing/testing the email automation locally. Install via `npm install -g n8n` or use n8n cloud.

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd solidea-sizing-assistant

# Install all dependencies (including dev dependencies)
uv sync

# Create your local environment file
cp .env.example .env

# Edit .env: confirm APP_ENV=development and APP_PORT=8000
```

## Running the Application

```bash
# Start the FastAPI development server with auto-reload
uv run uvicorn app.main:app --reload --port 8000
```

**Verify it's running:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

**Open the interactive API docs:**

Navigate to http://localhost:8000/docs in your browser. You can test the sizing endpoint directly from this page.

**Test a sizing request from the command line:**
```bash
curl -X POST http://localhost:8000/api/v1/size-recommendation \
  -H "Content-Type: application/json" \
  -d '{"product_type": "leggings", "measurements": {"height_cm": 170, "weight_kg": 65}}'
```

## Testing the Widget Locally

```bash
# Open the test page in your browser
# On macOS:
open widget/test-page.html

# On Windows:
start widget/test-page.html

# On Linux:
xdg-open widget/test-page.html
```

The test page is pre-configured to call `http://localhost:8000`. Make sure the API server is running first.

## Running Tests

```bash
# All tests
uv run pytest

# Verbose output
uv run pytest -v

# Specific test file
uv run pytest tests/test_sizing_logic.py

# With coverage report
uv run pytest --cov=app

# Run only tests matching a keyword
uv run pytest -k "test_legging"
```

## Linting and Formatting

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

## Common Issues

| Issue | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError` | Dependencies not installed | Run `uv sync` |
| CORS error in browser console | API not allowing the requesting origin | Check `ALLOWED_ORIGINS` in .env; add `http://localhost:*` for dev |
| JSON validation error on startup | Malformed sizing data file | Check the specific file mentioned in the error against `data/schema.json` |
| Port 8000 already in use | Another process on that port | Change `APP_PORT` in .env or stop the other process |
| Widget not loading on test page | API not running | Start the API server first; check browser console for fetch errors |
| `uv: command not found` | uv not installed or not in PATH | Install uv: `pip install uv` or see https://docs.astral.sh/uv/ |
