# solidea-sizing-assistant

Self-service sizing tool that helps Solidea US customers find their correct compression garment size based on body measurements. Deployed as a Shopify widget with a FastAPI backend and n8n email automation.

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- n8n (for email automation -- optional for local API development)

### Installation

```bash
git clone <repo-url>
cd solidea-sizing-assistant
uv sync
cp .env.example .env
# Edit .env with your values
```

### Running

```bash
uv run uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000. Interactive API docs at http://localhost:8000/docs.

**Test a sizing request:**
```bash
curl -X POST http://localhost:8000/api/v1/size-recommendation \
  -H "Content-Type: application/json" \
  -d '{"product_type": "leggings", "measurements": {"height_cm": 170, "weight_kg": 65}}'
```

## Architecture

```
                solideaUS.com (Shopify)
                        |
                 [sizing-widget.js]
                        |
                   fetch() POST
                        |
                        v
            [FastAPI Backend (Railway/Render)]
           /            |              \
  /data/*.json    POST /api/v1/      GET /health
 (sizing charts)  size-recommendation
                        ^
                        |
                 [n8n Workflow]
                        |
               [Email Inbox (IMAP)]
```

### Key Components

| Component | Purpose | Location |
|---|---|---|
| FastAPI API | Accepts measurements, returns size recommendation | `app/` |
| Sizing Engine | Matches measurements to sizes from JSON data | `app/sizing/` |
| Sizing Data | JSON files with measurement ranges per product type | `data/` |
| Shopify Widget | JavaScript popup form for product pages | `widget/` |
| n8n Workflow | Email automation for sizing inquiries | External (n8n instance) |

### Data Flow

**Widget flow:**
1. Customer opens a product page on solideaUS.com
2. Widget detects product type, shows a measurement form
3. Customer enters measurements, clicks "Find My Size"
4. Widget sends POST to /api/v1/size-recommendation
5. API loads product-type JSON, matches measurements to size ranges
6. API returns recommended size (or "between sizes" with guidance)
7. Widget displays the result with a link to purchase

**Email flow:**
1. Customer emails a sizing question to the store inbox
2. n8n detects the email, parses measurements and product type
3. n8n calls the same API endpoint
4. n8n sends auto-reply with the recommendation and product link
5. If unparseable, the email is forwarded to the owner

## Development

### Setup

```bash
uv sync
cp .env.example .env
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_sizing_logic.py -v

# With coverage
uv run pytest --cov=app
```

### Code Style

This project uses Ruff for linting and formatting. Run before committing:

```bash
uv run ruff check . && uv run ruff format .
```

### Project Structure

```
solidea-sizing-assistant/
  app/
    __init__.py
    main.py                  # FastAPI app, CORS, startup validation
    models.py                # Pydantic request/response models
    sizing/
      __init__.py
      engine.py              # Core sizing logic
      loader.py              # JSON data loading and validation
  data/
    arm-sleeves.json         # Arm sleeve sizing chart
    leggings.json            # Legging sizing chart
    capris.json              # Capri sizing chart
    socks.json               # Knee-high sock sizing chart
    bras.json                # Bra sizing chart
    schema.json              # JSON schema for sizing data validation
  tests/
    __init__.py
    conftest.py
    test_sizing_logic.py     # Unit tests for sizing engine
    test_api.py              # Integration tests for API endpoints
  widget/
    sizing-widget.js         # Shopify embed script
    sizing-widget.css        # Widget styles
    test-page.html           # Local test page for widget development
  docs/
    decisions/               # Architecture Decision Records
    runbooks/                # Operational guides
  .env.example
  .gitignore
  pyproject.toml
  CLAUDE.md
  README.md
  PROJECT_CHARTER.md
  TASKS.md
```

## Deployment

### Environment Variables

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

See `.env.example` for all required variables.

### Deploy

Push to the main branch. Railway/Render auto-deploys from GitHub.

The production API URL must be configured in:
1. The Shopify widget script (API endpoint URL)
2. The n8n workflow (HTTP Request node URL)

## Contributing

1. Create a feature branch from `main`
2. Make changes and add tests
3. Ensure all tests pass: `uv run pytest`
4. Ensure linter passes: `uv run ruff check . && uv run ruff format .`
5. Submit a pull request
